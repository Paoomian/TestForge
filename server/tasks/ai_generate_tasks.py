import json
import re
import asyncio
import time
from datetime import datetime
from celery import shared_task

from database import SessionLocal
from models.ai_generate import AIGenerateTask, AIProviderConfig
from services.ai_service import AIServiceFactory
from services.prompt_engine import PromptEngine
from utils.crypto import decrypt_api_key


def run_async(coro):
    """在同步上下文中运行异步函数"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        # 取消所有待处理任务，避免关闭时的警告
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        if pending:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        loop.close()


def try_fix_truncated_json(json_str: str) -> list:
    """尝试修复被截断的 JSON 数组"""
    # 移除末尾的逗号和空白
    json_str = json_str.rstrip().rstrip(',')

    # 尝试直接解析
    try:
        result = json.loads(json_str)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # 尝试添加缺失的闭合括号
    # 计算需要多少个 ]
    open_brackets = json_str.count('[') - json_str.count(']')
    if open_brackets > 0:
        # 检查最后一个完整对象的位置
        last_complete = json_str.rfind('}')
        if last_complete > 0:
            truncated = json_str[:last_complete + 1]
            # 尝试逐个添加 ]
            for i in range(open_brackets):
                try:
                    test_json = truncated + ']' * (i + 1)
                    result = json.loads(test_json)
                    if isinstance(result, list):
                        return result
                except json.JSONDecodeError:
                    continue

    # 尝试找到最后一个完整的对象
    objects = []
    depth = 0
    start = -1
    for i, char in enumerate(json_str):
        if char == '{':
            if depth == 0:
                start = i
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0 and start >= 0:
                try:
                    obj = json.loads(json_str[start:i+1])
                    objects.append(obj)
                except json.JSONDecodeError:
                    pass
                start = -1

    if objects:
        return objects

    return None


def fix_json_quotes(s: str) -> str:
    """修复 AI 返回的 JSON 中未转义的 ASCII 双引号
    将字符串值内部的未转义 " 替换为中文引号
    """
    result = []
    in_string = False
    escape = False
    i = 0
    while i < len(s):
        ch = s[i]
        if escape:
            result.append(ch)
            escape = False
            i += 1
            continue
        if ch == '\\':
            result.append(ch)
            escape = True
            i += 1
            continue
        if ch == '"':
            if in_string:
                # 判断这个引号是字符串结束还是内部引号
                j = i + 1
                while j < len(s) and s[j] in ' \t\n':
                    j += 1
                next_ch = s[j] if j < len(s) else ''
                if next_ch in ',]}:':
                    in_string = False
                    result.append(ch)
                else:
                    result.append('“')  # 左中文引号 "
            else:
                in_string = True
                result.append(ch)
        else:
            result.append(ch)
        i += 1
    return ''.join(result)


def extract_json_from_response(response: str) -> list:
    """从 AI 响应中提取 JSON 数组"""
    # 清理响应文本
    response = response.strip()

    # 尝试直接解析（先不修复引号，避免破坏有效 JSON）
    try:
        result = json.loads(response)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # 尝试修复未转义的内部引号后再解析
    response_fixed = fix_json_quotes(response)
    try:
        result = json.loads(response_fixed)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # 尝试提取 ```json ... ``` 或 ``` ... ``` 代码块（非贪婪，可能截断）
    # 使用 response_fixed 来匹配，但解析时使用原始匹配内容
    patterns = [
        r'```json\s*\n?([\s\S]*?)\n?```',
        r'```\s*\n?([\s\S]*?)\n?```',
    ]
    for pattern in patterns:
        match = re.search(pattern, response_fixed)
        if match:
            content = match.group(1).strip()
            try:
                result = json.loads(content)
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                fixed = try_fix_truncated_json(content)
                if fixed:
                    return fixed

    # 代码块未闭合的情况：提取 ```json 之后的全部内容
    unclosed_match = re.search(r'```json\s*\n?([\s\S]*)', response_fixed)
    if unclosed_match:
        content = unclosed_match.group(1).strip()
        try:
            result = json.loads(content)
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            fixed = try_fix_truncated_json(content)
            if fixed:
                return fixed

    # 从第一个 [ 开始，通过括号配对找到正确的 JSON 数组结束位置
    start_idx = response_fixed.find('[')
    if start_idx >= 0:
        depth = 0
        in_string = False
        escape_next = False
        for i in range(start_idx, len(response)):
            ch = response[i]
            if escape_next:
                escape_next = False
                continue
            if ch == '\\' and in_string:
                escape_next = True
                continue
            if ch == '"' and not escape_next:
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == '[':
                depth += 1
            elif ch == ']':
                depth -= 1
                if depth == 0:
                    candidate = response_fixed[start_idx:i + 1]
                    try:
                        result = json.loads(candidate)
                        if isinstance(result, list):
                            return result
                    except json.JSONDecodeError:
                        fixed = try_fix_truncated_json(candidate)
                        if fixed:
                            return fixed
                    break

    # 尝试从整个响应中提取
    fixed = try_fix_truncated_json(response_fixed)
    if fixed:
        return fixed

    # 如果仍然失败，保存原始响应用于调试
    raise ValueError(f"无法从 AI 响应中提取有效的 JSON 数组。响应前 200 字符: {response[:200]}")


@shared_task(bind=True, max_retries=2)
def generate_test_cases(self, task_id: int, config_id: int):
    """生成测试用例的 Celery 任务

    Args:
        task_id: 任务 ID
        config_id: AI 配置 ID
    """
    db = SessionLocal()

    def update_progress(progress: int, stage: str):
        """更新进度和阶段"""
        task.progress = progress
        task.error_message = stage  # 临时存储阶段信息
        db.commit()

    try:
        # 获取任务
        task = db.query(AIGenerateTask).filter(AIGenerateTask.id == task_id).first()
        if not task:
            return

        # 检查任务状态
        if task.status == "cancelled":
            return

        # 更新任务状态
        task.status = "processing"
        update_progress(5, "正在初始化...")
        time.sleep(0.5)

        # 获取 AI 配置
        config = db.query(AIProviderConfig).filter(AIProviderConfig.id == config_id).first()
        if not config:
            task.status = "failed"
            task.error_message = "AI 配置不存在"
            db.commit()
            return

        # 创建 AI 服务
        update_progress(15, "正在连接 AI 服务...")
        time.sleep(0.8)
        api_key = decrypt_api_key(config.api_key)
        provider = AIServiceFactory.create_provider(
            config.provider,
            api_key,
            config.api_base_url
        )

        # 更新进度
        update_progress(25, "正在分析输入内容...")
        time.sleep(0.6)

        # 准备输入内容
        input_content = task.input_content
        if task.input_type == "swagger" and input_content:
            # 如果是 Swagger 文档，格式化为更易读的文本
            try:
                swagger_data = json.loads(input_content)
                from services.document_parser import DocumentParser
                input_content = DocumentParser.format_swagger_for_prompt(swagger_data)
            except (json.JSONDecodeError, Exception):
                pass  # 使用原始内容

        # 构建 Prompt
        update_progress(35, "正在构建 AI 提示词...")
        time.sleep(0.5)
        if task.skill_id:
            from models.ai_skill import AISkill
            skill = db.query(AISkill).filter(AISkill.id == task.skill_id).first()
            if skill:
                messages = PromptEngine.build_messages_from_skill(skill, input_content or "")
            else:
                messages = PromptEngine.build_messages(
                    generate_type=task.generate_type,
                    input_content=input_content or ""
                )
        else:
            messages = PromptEngine.build_messages(
                generate_type=task.generate_type,
                input_content=input_content or ""
            )

        # AI 调用前
        update_progress(45, "正在发送请求到 AI 服务...")
        time.sleep(0.5)

        # 调用 AI 生成
        update_progress(55, "AI 正在思考中...")
        response = run_async(provider.chat(messages, task.model_name))

        # AI 调用后
        update_progress(75, "AI 返回结果，正在解析...")
        time.sleep(0.3)

        # 解析结果
        try:
            generated_cases = extract_json_from_response(response)
        except ValueError as e:
            task.status = "failed"
            # 保存部分响应内容帮助调试
            debug_response = response[:300] if len(response) > 300 else response
            task.error_message = f"解析失败: {str(e)[:200]}"
            db.commit()
            return

        # 验证结果是列表
        if not isinstance(generated_cases, list):
            task.status = "failed"
            task.error_message = "AI 返回的结果不是数组格式"
            db.commit()
            return

        # 更新任务结果
        update_progress(85, "正在验证用例格式...")
        time.sleep(0.3)
        update_progress(95, "正在保存结果...")
        task.generated_cases = generated_cases
        task.cases_count = len(generated_cases)
        task.status = "completed"
        task.progress = 100
        task.error_message = None  # 清除阶段信息
        task.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        # 任务失败
        task = db.query(AIGenerateTask).filter(AIGenerateTask.id == task_id).first()
        if task:
            task.status = "failed"
            task.error_message = str(e)[:500]  # 限制错误消息长度
            db.commit()

        # 重试
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=5)

    finally:
        db.close()

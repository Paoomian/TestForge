from typing import List, Dict


# 功能测试自动附加的格式要求和示例
FUNCTIONAL_FORMAT_REQUIREMENTS = '''

=== 强制要求（不满足则输出无效） ===
1. 你的输出必须包含 combination 类型用例（≥8条），使用 Pairwise 成对测试方法，必须附带参数表和组合矩阵
2. 你的输出必须包含 backend_ui 类型用例（≥3条），步骤中必须写"打开浏览器开发者工具Network面板"，预期结果必须写明HTTP状态码
3. expected_results 必须是数组，与 steps 一一对应
4. 输出纯JSON数组，不要包含markdown代码块或其他文本

=== combination 用例格式（照此生成≥8条） ===

先输出参数表（从需求中提取4-6个关键参数）：
参数表：用户名类型(手机号/邮箱) × 密码(正确/错误) × 验证码(正确/错误) × 账户状态(正常/接近锁定/已锁定)

再输出Pairwise组合矩阵（每对取值至少出现一次）：
C1: 手机号+正确+正确+正常
C2: 手机号+错误+错误+接近锁定
C3: 手机号+正确+过期+已锁定
C4: 邮箱+正确+错误+正常
C5: 邮箱+错误+正确+接近锁定
C6: 邮箱+正确+正确+已锁定
C7: 手机号+错误+正确+正常
C8: 邮箱+错误+过期+已锁定

每条combination用例示例：
{
  "name": "组合C2-手机号+错误密码+错误验证码+接近锁定",
  "priority": "P1",
  "preconditions": "数据库存在手机号13800138000的用户，密码为Abc123；该用户连续登录失败次数为4（未锁定）；当前会话验证码为Xk9m",
  "steps": ["打开登录页面", "在用户名输入框输入13800138000", "在密码输入框输入WrongPwd", "在验证码输入框输入YYYY", "点击登录按钮"],
  "expected_results": ["登录页面正常显示", "用户名输入框显示13800138000", "密码输入框显示密文", "验证码输入框显示YYYY", "页面提示'验证码错误'，验证码图片刷新；数据库中该用户连续失败次数仍为4"],
  "test_type": "combination"
}

=== backend_ui 用例格式（照此生成≥3条） ===

{
  "name": "后端验证-锁定状态下直接调用登录API",
  "priority": "P1",
  "preconditions": "数据库存在手机号13800138000的用户，密码为Abc123；该用户连续失败5次，账户已锁定30分钟",
  "steps": ["打开浏览器开发者工具，切换到Network面板，清空已有请求记录", "在地址栏直接访问登录页面", "在用户名输入框输入13800138000", "在密码输入框输入Abc123（正确密码）", "在验证码输入框输入当前正确验证码", "点击登录按钮", "在Network面板中找到login请求，查看响应"],
  "expected_results": ["Network面板已清空，无残留请求", "登录页面正常加载", "用户名输入框显示13800138000", "密码输入框显示密文", "验证码输入框显示正确验证码", "页面提示'账户已锁定，请30分钟后再试'", "Network面板中POST /api/v1/auth/login请求的HTTP状态码为403，响应体包含message字段值为'账户已锁定'，响应体不包含密码明文或内部错误堆栈"],
  "test_type": "backend_ui"
}

=== 单条用例JSON结构 ===
{
  "name": "用例名称",
  "priority": "P0/P1/P2",
  "preconditions": "具体可验证的前置条件",
  "steps": ["步骤1", "步骤2"],
  "expected_results": ["预期1", "预期2"],
  "test_type": "normal/exception/boundary/combination/backend_ui"
}

=== 输出前自检 ===
□ combination 用例是否≥8条？（必须有参数表和组合矩阵）
□ backend_ui 用例是否是否≥3条？（步骤含Network面板，预期含HTTP状态码）
□ 每个边界参数是否有最小值-1/最小值/最大值/最大值+1（具体数值）？
□ expected_results 数组长度是否等于 steps 数组长度？'''


# 接口测试自动附加的格式要求
API_FORMAT_REQUIREMENTS = '''

【输出格式要求】
- 输出纯JSON数组，不要包含markdown代码块标记或其他文本
- 断言覆盖状态码、响应时间、关键字段

单条用例结构：
{
  "name": "用例名称",
  "method": "GET",
  "url": "/api/users",
  "headers": [{"key": "Content-Type", "value": "application/json"}],
  "query_params": [],
  "body_type": "none",
  "body_content": null,
  "priority": "P1",
  "assertions": [
    {
      "assertion_type": "status_code",
      "operator": "equals",
      "expected": "200"
    }
  ]
}'''


PROMPT_TEMPLATES = {
    "functional": {
        "system": """你是一个资深的测试工程师，擅长根据需求文档生成功能测试用例。

要求：
1. 根据需求的复杂度和覆盖度，自行决定生成用例的数量，确保全面覆盖
2. 用例必须覆盖以下测试方法：
   - 正常流程测试：验证主要功能的正常操作路径
   - 异常流程测试：验证错误处理和异常场景
   - 边界值测试：验证输入参数的边界条件（最小值、最大值、空值、特殊字符等）
   - 组合测试：验证多个参数组合的交互情况（使用 Pairwise 方法）
3. 每个用例包含：用例名称、前置条件、测试步骤、预期结果、优先级
4. 用例名称简洁明确，步骤可执行
5. 必须以 JSON 格式返回，不要包含其他内容""",

        "user": """请根据以下需求文档生成功能测试用例：

{input_content}

请根据需求的复杂度自行决定生成数量，确保全面覆盖以下测试方法：
- 正常流程测试（test_type: normal）
- 异常流程测试（test_type: exception）
- 边界值测试（test_type: boundary）：数值边界、字符串边界、日期边界等
- 组合测试（test_type: combination）：多参数组合场景

请严格以 JSON 数组格式返回，结构如下：
[
  {{
    "name": "用例名称",
    "priority": "P0/P1/P2/P3",
    "preconditions": "前置条件",
    "steps": ["步骤1", "步骤2"],
    "expected_result": "预期结果",
    "test_type": "normal/exception/boundary/combination"
  }}
]"""
    },

    "api": {
        "system": """你是一个接口测试专家，擅长根据接口文档生成接口测试用例。

要求：
1. 根据接口数量和复杂度，自行决定生成用例的数量
2. 每个接口生成：正向用例、参数校验用例、边界值用例
3. 输出格式为 JSON，包含完整的请求配置和断言
4. 断言覆盖状态码、响应时间、关键字段
5. 考虑认证、鉴权场景
6. 必须以 JSON 格式返回，不要包含其他内容""",

        "user": """请根据以下接口文档生成接口测试用例：

{input_content}

请为每个接口生成测试用例，包含：
- 请求方法、URL、Headers
- 请求体（如适用）
- 预期状态码和响应断言
- 数据提取规则（如需要）

请严格以 JSON 数组格式返回，结构如下：
[
  {{
    "name": "用例名称",
    "method": "GET",
    "url": "/api/users",
    "headers": [{{"key": "Content-Type", "value": "application/json"}}],
    "query_params": [],
    "body_type": "none",
    "body_content": null,
    "priority": "P1",
    "assertions": [
      {{
        "assertion_type": "status_code",
        "operator": "equals",
        "expected": "200"
      }}
    ]
  }}
]"""
    }
}


class PromptEngine:
    """Prompt 引擎"""

    @staticmethod
    def build_messages_from_skill(skill, input_content: str) -> List[Dict[str, str]]:
        """从数据库 Skill 构建 AI 对话消息

        支持两种模式：
        1. 新模式（user_prompt 为空）：system_prompt 作为 system 消息，自动生成 user 消息
        2. 旧模式（user_prompt 非空）：兼容旧格式，分别使用 system_prompt 和 user_prompt

        Args:
            skill: AISkill 数据库对象
            input_content: 输入内容

        Returns:
            消息列表，包含 system 和 user 消息
        """
        if skill.user_prompt and skill.user_prompt.strip():
            # 旧模式：user_prompt 由用户/前端生成，包含 {input_content} 占位符
            try:
                user_content = skill.user_prompt.format(input_content=input_content)
            except (KeyError, ValueError):
                user_content = skill.user_prompt.replace("{input_content}", input_content)

            return [
                {"role": "system", "content": skill.system_prompt},
                {"role": "user", "content": user_content}
            ]

        # 新模式：system_prompt 是用户写的 Prompt 模板，user 消息自动生成
        system_content = skill.system_prompt

        # 根据 generate_type 选择格式要求
        if skill.generate_type == 'functional':
            format_req = FUNCTIONAL_FORMAT_REQUIREMENTS
        elif skill.generate_type == 'api':
            format_req = API_FORMAT_REQUIREMENTS
        else:
            format_req = ''

        # 检查模板中是否包含 {input_content} 占位符
        if '{input_content}' in system_content:
            # 将模板中的 {input_content} 替换为实际内容
            try:
                system_content = system_content.format(input_content=input_content)
            except (KeyError, ValueError):
                system_content = system_content.replace("{input_content}", input_content)
            # user 消息只放格式要求
            user_content = format_req.strip()
        else:
            # 模板中没有占位符，user 消息包含输入内容 + 格式要求
            user_content = f'请根据以下内容生成测试用例：\n\n{input_content}{format_req}'

        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ]

    @staticmethod
    def build_messages(
        generate_type: str,
        input_content: str
    ) -> List[Dict[str, str]]:
        """构建 AI 对话消息（从硬编码模板，向后兼容）

        Args:
            generate_type: 生成类型 (functional/api)
            input_content: 输入内容

        Returns:
            消息列表，包含 system 和 user 消息
        """
        template = PROMPT_TEMPLATES.get(generate_type)
        if not template:
            raise ValueError(f"不支持的生成类型: {generate_type}，支持: {', '.join(PROMPT_TEMPLATES.keys())}")

        return [
            {"role": "system", "content": template["system"]},
            {"role": "user", "content": template["user"].format(
                input_content=input_content
            )}
        ]

    @staticmethod
    def get_supported_types() -> List[str]:
        """获取支持的生成类型"""
        return list(PROMPT_TEMPLATES.keys())

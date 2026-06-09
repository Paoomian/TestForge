"""
UI 批量执行引擎
串行执行每个 UI 用例，失败步骤和最后一步保存截图
"""
import asyncio
import base64
import logging
import platform
import time
from datetime import datetime, timezone
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from sqlalchemy.orm import Session
from models import TestRun, TestRunDetail, TestRunStatus, TestRunDetailStatus, UICase

logger = logging.getLogger(__name__)


class UIBatchRunner:
    """UI 批量执行引擎"""

    def __init__(
        self,
        db: Session,
        test_run_id: int,
        celery_task_id: Optional[str] = None,
        browser: str = "chrome",
        viewport_width: int = 1280,
        viewport_height: int = 720,
    ):
        self.db = db
        self.test_run_id = test_run_id
        self.celery_task_id = celery_task_id
        self.browser_type = browser
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height

        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    async def execute(self):
        """执行批量任务"""
        # 获取任务信息
        test_run = self.db.query(TestRun).filter(TestRun.id == self.test_run_id).first()
        if not test_run:
            logger.error(f"任务不存在: {self.test_run_id}")
            return

        # 更新任务状态为运行中
        test_run.status = TestRunStatus.RUNNING
        test_run.start_time = datetime.now(timezone.utc)
        if self.celery_task_id:
            test_run.celery_task_id = self.celery_task_id
        self.db.commit()

        try:
            # 启动浏览器
            await self._start_browser()

            # 获取所有待执行的明细
            details = self.db.query(TestRunDetail).filter(
                TestRunDetail.test_run_id == self.test_run_id
            ).order_by(TestRunDetail.execution_order).all()

            pass_count = 0
            fail_count = 0
            error_count = 0

            # 串行执行每个用例
            for i, detail in enumerate(details):
                # 检查是否已取消
                if self._is_cancelled():
                    detail.status = TestRunDetailStatus.SKIPPED
                    self.db.commit()
                    continue

                # 执行用例
                result = await self._execute_case(detail, is_last=(i == len(details) - 1))

                # 更新统计
                if result["status"] == "pass":
                    pass_count += 1
                elif result["status"] == "fail":
                    fail_count += 1
                else:
                    error_count += 1

                # 检查失败策略
                if test_run.failure_strategy == "stop" and result["status"] in ("fail", "error"):
                    # 将剩余用例标记为跳过
                    for remaining_detail in details[i + 1:]:
                        remaining_detail.status = TestRunDetailStatus.SKIPPED
                    self.db.commit()
                    break

            # 更新任务状态
            test_run.status = TestRunStatus.DONE
            test_run.pass_count = pass_count
            test_run.fail_count = fail_count
            test_run.error_count = error_count
            test_run.end_time = datetime.now(timezone.utc)
            # 计算耗时（处理时区问题）
            if test_run.start_time:
                start = test_run.start_time.replace(tzinfo=timezone.utc) if test_run.start_time.tzinfo is None else test_run.start_time
                test_run.duration = int((test_run.end_time - start).total_seconds() * 1000)
            else:
                test_run.duration = 0
            self.db.commit()

            logger.info(f"UI批量执行完成: 通过={pass_count}, 失败={fail_count}, 错误={error_count}")

        except Exception as e:
            logger.error(f"UI批量执行异常: {e}", exc_info=True)
            test_run.status = TestRunStatus.ERROR
            test_run.end_time = datetime.now(timezone.utc)
            self.db.commit()

        finally:
            await self._stop_browser()

    async def _start_browser(self):
        """启动浏览器"""
        self._playwright = await async_playwright().start()

        browser_type = getattr(self._playwright, self.browser_type, self._playwright.chromium)
        self._browser = await browser_type.launch(headless=True)
        self._context = await self._browser.new_context(
            viewport={"width": self.viewport_width, "height": self.viewport_height}
        )
        self._page = await self._context.new_page()
        logger.info(f"浏览器已启动: {self.browser_type}")

    async def _stop_browser(self):
        """关闭浏览器"""
        try:
            if self._page:
                await self._page.close()
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception as e:
            logger.warning(f"关闭浏览器异常: {e}")

    def _is_cancelled(self) -> bool:
        """检查任务是否已取消"""
        test_run = self.db.query(TestRun).filter(TestRun.id == self.test_run_id).first()
        return test_run and test_run.cancelled

    async def _execute_case(self, detail: TestRunDetail, is_last: bool = False) -> dict:
        """执行单个用例"""
        # 获取用例信息（UI用例的ID存储在case_number字段中）
        case_id = int(detail.case_number) if detail.case_number else detail.case_id
        logger.info(f"执行用例: case_id={case_id}, case_name={detail.case_name}")
        case = self.db.query(UICase).filter(UICase.id == case_id).first()
        if not case:
            detail.status = TestRunDetailStatus.ERROR
            detail.error_message = "用例不存在"
            self.db.commit()
            logger.error(f"用例不存在: case_id={case_id}")
            return {"status": "error", "message": "用例不存在"}

        logger.info(f"用例信息: name={case.name}, steps_count={len(case.steps or [])}")

        # 获取环境变量（用于变量替换）
        variables = {}
        test_run = self.db.query(TestRun).filter(TestRun.id == self.test_run_id).first()
        if test_run and test_run.environment_id:
            from models import Environment
            env = self.db.query(Environment).filter(Environment.id == test_run.environment_id).first()
            if env:
                variables["base_url"] = env.base_url or ""
                if env.variables:
                    variables.update(env.variables)
        logger.info(f"变量替换: variables={variables}")

        # 更新状态为执行中
        detail.status = TestRunStatus.RUNNING
        self.db.commit()

        start_time = time.time()
        steps_result = []
        has_failure = False

        try:
            steps = case.steps or []
            logger.info(f"总步骤数: {len(steps)}")
            for step_index, step in enumerate(steps):
                is_last_step = (step_index == len(steps) - 1)
                logger.info(f"步骤 {step_index + 1}/{len(steps)}, is_last_step={is_last_step}")
                # 替换步骤中的变量
                step = self._replace_variables(step, variables)
                step_result = await self._execute_step(step, step_index + 1)
                steps_result.append(step_result)

                if step_result["status"] in ("fail", "error"):
                    has_failure = True
                    # 失败步骤保存截图
                    if step_result.get("screenshot") is None:
                        screenshot = await self._take_screenshot()
                        step_result["screenshot"] = screenshot

                # 最后一步保存截图
                if is_last_step and not step_result.get("screenshot"):
                    screenshot = await self._take_screenshot()
                    step_result["screenshot"] = screenshot
                    logger.info(f"最后一步截图已保存, 截图长度: {len(screenshot) if screenshot else 0}")

                # 如果失败且策略是停止，则中断
                if has_failure:
                    break

            # 更新执行结果
            duration_ms = int((time.time() - start_time) * 1000)
            detail.duration_ms = duration_ms
            detail.status = TestRunDetailStatus.PASS if not has_failure else TestRunDetailStatus.FAIL

            # 保存步骤结果到 JSON 字段
            detail.script_output = {"steps": steps_result}

            self.db.commit()

            return {
                "status": detail.status,
                "duration_ms": duration_ms,
                "steps": steps_result,
            }

        except Exception as e:
            logger.error(f"执行用例异常: {e}", exc_info=True)
            detail.status = TestRunDetailStatus.ERROR
            detail.error_message = str(e)
            detail.duration_ms = int((time.time() - start_time) * 1000)
            self.db.commit()
            return {"status": "error", "message": str(e)}

    async def _execute_step(self, step: dict, step_order: int) -> dict:
        """执行单个步骤"""
        action = step.get("action", "")
        logger.info(f"执行步骤 {step_order}: action={action}")
        start_time = time.time()

        try:
            if action == "navigate":
                url = step.get("url", "")
                logger.info(f"导航到: {url}")
                await self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
                message = f"导航到 {url}"

            elif action == "click":
                selector = self._get_selector(step)
                if selector:
                    await self._page.click(selector, timeout=10000)
                    message = f"点击 {selector}"
                else:
                    raise Exception("未找到元素选择器")

            elif action == "type":
                selector = self._get_selector(step)
                value = step.get("value", "")
                if selector:
                    await self._page.fill(selector, value, timeout=10000)
                    message = f"输入 {value}"
                else:
                    raise Exception("未找到元素选择器")

            elif action == "press":
                key = step.get("key", "Enter")
                await self._page.keyboard.press(key)
                message = f"按下 {key}"

            elif action == "wait":
                wait_ms = step.get("waitMs", step.get("waitBefore", 1000))
                await self._page.wait_for_timeout(wait_ms)
                message = f"等待 {wait_ms}ms"

            elif action == "new_page":
                # 等待新页面打开
                async with self._page.context.expect_page() as new_page_info:
                    pass
                new_page = await new_page_info.value
                self._page = new_page
                message = "切换到新页面"

            elif action == "go_back":
                await self._page.go_back(wait_until="domcontentloaded")
                message = "返回上一页"

            else:
                message = f"未知操作: {action}"

            duration_ms = int((time.time() - start_time) * 1000)
            return {
                "step_order": step_order,
                "action": action,
                "status": "pass",
                "message": message,
                "duration_ms": duration_ms,
            }

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return {
                "step_order": step_order,
                "action": action,
                "status": "fail",
                "message": str(e),
                "duration_ms": duration_ms,
            }

    def _replace_variables(self, data: dict, variables: dict) -> dict:
        """替换数据中的变量"""
        import re
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                # 替换 {{variable}} 格式的变量
                def replace_var(match):
                    var_name = match.group(1).strip()
                    return variables.get(var_name, match.group(0))
                result[key] = re.sub(r'\{\{(\w+)\}\}', replace_var, value)
            elif isinstance(value, dict):
                result[key] = self._replace_variables(value, variables)
            else:
                result[key] = value
        return result

    def _get_selector(self, step: dict) -> Optional[str]:
        """从步骤中获取元素选择器"""
        target = step.get("target", {})
        if target:
            # 优先使用 CSS 选择器
            if target.get("selector"):
                return target["selector"]
            # 其次使用 XPath
            if target.get("xpath"):
                return f"xpath={target['xpath']}"
            # 尝试使用文本内容
            if target.get("text"):
                text = target["text"]
                return f"text={text}"
        return None

    async def _take_screenshot(self) -> str:
        """截图并返回 base64"""
        try:
            screenshot_bytes = await self._page.screenshot(type="jpeg", quality=75)
            return base64.b64encode(screenshot_bytes).decode("utf-8")
        except Exception as e:
            logger.warning(f"截图失败: {e}")
            return ""

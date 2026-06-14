"""
UI 用例执行服务
支持单用例调试执行，实时截图推送
"""
import asyncio
import base64
import platform
import threading
import time
from typing import Callable, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page


class UIExecutor:
    """UI 用例执行器"""

    def __init__(self, session_id: str = ""):
        self.session_id = session_id
        self.status = "idle"  # idle / running / completed / failed
        self.current_step = 0
        self.total_steps = 0
        self.results = []  # 执行结果
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._screenshot_callback: Optional[Callable] = None
        self._progress_callback: Optional[Callable] = None
        self._should_stop = False

    def start(
        self,
        steps: list[dict],
        base_url: str = "",
        variables: Optional[dict] = None,
        viewport_width: int = 1280,
        viewport_height: int = 720,
        screenshot_callback: Optional[Callable] = None,
        progress_callback: Optional[Callable] = None,
    ):
        """启动执行（同步方法，内部启动线程）"""
        self._screenshot_callback = screenshot_callback
        self._progress_callback = progress_callback
        self.status = "running"  # 提前设置状态

        # 在独立线程中执行
        self._thread = threading.Thread(
            target=self._run_in_thread,
            args=(steps, base_url, variables, viewport_width, viewport_height),
            daemon=True,
        )
        self._thread.start()

    def _run_in_thread(self, steps, base_url, variables, viewport_width, viewport_height):
        """在独立线程中运行"""
        if platform.system() == "Windows":
            self._loop = asyncio.ProactorEventLoop()
        else:
            self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            result = self._loop.run_until_complete(
                self.execute(steps, base_url, variables, viewport_width, viewport_height)
            )
            # 通知执行完成
            if self._progress_callback:
                try:
                    self._progress_callback({
                        "type": "completed",
                        "result": result,
                    })
                except Exception:
                    pass
        except Exception as e:
            print(f"[EXECUTOR] 执行异常: {e}")
        finally:
            self._loop.close()

    def stop(self):
        """停止执行"""
        self._should_stop = True

    async def execute(
        self,
        steps: list[dict],
        base_url: str = "",
        variables: Optional[dict] = None,
        viewport_width: int = 1280,
        viewport_height: int = 720,
        screenshot_callback: Optional[Callable] = None,
        progress_callback: Optional[Callable] = None,
    ) -> dict:
        """执行用例步骤"""
        if screenshot_callback:
            self._screenshot_callback = screenshot_callback
        if progress_callback:
            self._progress_callback = progress_callback
        self.total_steps = len(steps)
        self.current_step = 0
        self.results = []
        self.status = "running"
        self._should_stop = False

        # 合并变量：环境变量 + base_url
        self._variables = variables or {}
        if base_url:
            self._variables['base_url'] = base_url.rstrip('/')

        try:
            # 启动浏览器
            print("[EXECUTOR] 启动浏览器...")
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-gpu"]
            )
            self._context = await self._browser.new_context(
                viewport={"width": viewport_width, "height": viewport_height},
            )
            self._page = await self._context.new_page()
            print("[EXECUTOR] 浏览器启动成功")

            # 启动截图循环
            screenshot_task = asyncio.create_task(self._screenshot_loop())

            # 执行每个步骤
            for i, step in enumerate(steps):
                if self._should_stop:
                    break

                self.current_step = i + 1
                action = step.get("action", "")
                print(f"[EXECUTOR] 执行步骤 {self.current_step}/{self.total_steps}: {action}")

                # 通知步骤开始
                if self._progress_callback:
                    try:
                        self._progress_callback({
                            "type": "step_start",
                            "current": self.current_step,
                            "total": self.total_steps,
                            "step": step,
                        })
                    except Exception:
                        pass

                result = await self._execute_step(step, i + 1)
                self.results.append(result)
                print(f"[EXECUTOR] 步骤 {self.current_step} 完成: success={result['success']}, message={result['message']}")

                # 通知步骤完成
                if self._progress_callback:
                    try:
                        self._progress_callback({
                            "type": "step_end",
                            "current": self.current_step,
                            "total": self.total_steps,
                            "step": step,
                            "result": result,
                        })
                    except Exception:
                        pass

                # 如果步骤失败且是关键步骤，停止执行
                if not result["success"] and step.get("action") in ["navigate", "assert"]:
                    break

                # 步骤间等待一小段时间，方便观察
                await asyncio.sleep(0.5)

            # 停止截图循环
            screenshot_task.cancel()
            try:
                await screenshot_task
            except asyncio.CancelledError:
                pass

            # 计算执行结果
            passed = sum(1 for r in self.results if r["success"])
            failed = sum(1 for r in self.results if not r["success"])
            self.status = "completed" if failed == 0 else "failed"

            return {
                "status": self.status,
                "total": self.total_steps,
                "passed": passed,
                "failed": failed,
                "results": self.results,
            }

        except Exception as e:
            self.status = "failed"
            return {
                "status": "failed",
                "error": str(e),
                "results": self.results,
            }
        finally:
            await self._cleanup()

    async def _screenshot_loop(self):
        """定时截图循环"""
        try:
            while self.status == "running" and not self._should_stop:
                if self._page and self._screenshot_callback:
                    try:
                        # 检查页面是否还可用
                        if self._page.is_closed():
                            break
                        screenshot_bytes = await self._page.screenshot(type="jpeg", quality=60)
                        screenshot = base64.b64encode(screenshot_bytes).decode("utf-8")
                        if screenshot:
                            result = self._screenshot_callback(screenshot)
                            if asyncio.iscoroutine(result):
                                await result
                    except Exception as e:
                        # 如果是页面关闭错误，退出循环
                        if "closed" in str(e).lower():
                            break
                await asyncio.sleep(0.2)  # 200ms 截图一次
        except asyncio.CancelledError:
            pass

    def _replace_variables(self, text: str) -> str:
        """替换字符串中的 {{variable}} 变量"""
        if not text or not self._variables:
            return text
        import re
        def replace_match(match):
            var_name = match.group(1)
            return self._variables.get(var_name, match.group(0))
        return re.sub(r'\{\{(\w+)\}\}', replace_match, text)

    async def _execute_step(self, step: dict, step_num: int) -> dict:
        """执行单个步骤"""
        action = step.get("action")
        start_time = time.time()
        timeout = step.get("timeout", 10000)  # 默认 10 秒超时
        result = {
            "step": step_num,
            "action": action,
            "success": False,
            "message": "",
            "screenshot": None,
            "duration": 0,
        }

        # 变量替换：替换步骤中的 URL 和 value
        step = step.copy()
        if "url" in step:
            step["url"] = self._replace_variables(step["url"])
        if "value" in step:
            step["value"] = self._replace_variables(step["value"])

        try:
            if action == "navigate":
                url = step.get("url", "")
                await self._page.goto(url, wait_until="load", timeout=30000)
                result["success"] = True
                result["message"] = f"导航到 {url}"

            elif action == "click":
                target = step.get("target", {})
                selector = target.get("selector")
                if selector:
                    # 显式等待元素出现并可点击
                    element = await self._page.wait_for_selector(selector, state="visible", timeout=timeout)
                    if element:
                        await element.scroll_into_view_if_needed()
                        await element.click(timeout=5000)
                        result["success"] = True
                        result["message"] = f"点击 {target.get('text', selector)}"
                    else:
                        result["message"] = f"元素未找到: {selector}"
                else:
                    result["message"] = "缺少选择器"

            elif action == "type":
                target = step.get("target", {})
                value = step.get("value", "")
                selector = target.get("selector")
                if selector and value:
                    # 显式等待输入框出现
                    element = await self._page.wait_for_selector(selector, state="visible", timeout=timeout)
                    if element:
                        await element.scroll_into_view_if_needed()
                        await element.click()
                        await element.fill(value, timeout=5000)
                        result["success"] = True
                        result["message"] = f"输入 '{value}'"
                    else:
                        result["message"] = f"输入框未找到: {selector}"
                else:
                    result["message"] = "缺少选择器或值"

            elif action == "press":
                key = step.get("key", "")
                if key:
                    await self._page.keyboard.press(key)
                    result["success"] = True
                    result["message"] = f"按键 {key}"
                else:
                    result["message"] = "缺少按键"

            elif action == "new_page":
                # 新窗口已在 click 步骤中处理，等待新页面加载
                await asyncio.sleep(1)  # 等待新窗口打开
                await self._page.wait_for_load_state("domcontentloaded", timeout=10000)
                result["success"] = True
                result["message"] = "新窗口已打开"

            elif action == "go_back":
                await self._page.go_back()
                await self._page.wait_for_load_state("domcontentloaded", timeout=10000)
                result["success"] = True
                result["message"] = "返回上一页"

            elif action == "scroll":
                delta_x = step.get("deltaX", 0)
                delta_y = step.get("deltaY", 0)
                await self._page.mouse.wheel(delta_x, delta_y)
                await asyncio.sleep(0.5)  # 等待滚动完成
                result["success"] = True
                result["message"] = f"滚动 ({delta_x}, {delta_y})"

            elif action == "drag":
                # 拖拽操作
                from_point = step.get("from")
                to_point = step.get("to")
                if from_point and to_point:
                    # 执行拖拽：移动到起点 → 按下 → 移动到终点 → 释放
                    await self._page.mouse.move(from_point["x"], from_point["y"])
                    await self._page.mouse.down()
                    # 分步移动到终点，模拟真实拖拽
                    steps_count = 10
                    for i in range(steps_count + 1):
                        ratio = i / steps_count
                        x = from_point["x"] + (to_point["x"] - from_point["x"]) * ratio
                        y = from_point["y"] + (to_point["y"] - from_point["y"]) * ratio
                        await self._page.mouse.move(x, y)
                        await asyncio.sleep(0.02)  # 20ms 间隔
                    await self._page.mouse.up()
                    await asyncio.sleep(0.3)  # 等待拖拽完成
                    result["success"] = True
                    result["message"] = f"拖拽 ({from_point['x']},{from_point['y']}) → ({to_point['x']},{to_point['y']})"
                else:
                    result["message"] = "缺少拖拽坐标"

            elif action == "wait":
                wait_ms = step.get("waitMs", 1000)
                await asyncio.sleep(wait_ms / 1000)
                result["success"] = True
                result["message"] = f"等待 {wait_ms}ms"

            elif action == "assert":
                result = await self._execute_assert(step, step_num)

            else:
                result["message"] = f"未知操作: {action}"

        except Exception as e:
            result["message"] = str(e)

        # 计算耗时
        result["duration"] = int((time.time() - start_time) * 1000)

        # 截图
        try:
            screenshot_bytes = await self._page.screenshot(type="jpeg", quality=60)
            result["screenshot"] = base64.b64encode(screenshot_bytes).decode("utf-8")
        except Exception:
            pass

        return result

    async def _execute_assert(self, step: dict, step_num: int) -> dict:
        """执行断言"""
        assert_type = step.get("type")
        selector = step.get("selector")
        expected = step.get("expected", "").strip()  # 去除首尾空格
        timeout = step.get("timeout", 5000)

        result = {
            "step": step_num,
            "action": "assert",
            "success": False,
            "message": "",
            "screenshot": None,
            "duration": 0,
        }

        try:
            if assert_type == "element_exists":
                if selector:
                    element = await self._page.wait_for_selector(selector, timeout=timeout)
                    if element:
                        result["success"] = True
                        result["message"] = f"元素存在: {selector}"
                    else:
                        result["message"] = f"元素不存在: {selector}"

            elif assert_type == "element_not_exists":
                if selector:
                    try:
                        await self._page.wait_for_selector(selector, timeout=timeout)
                        result["message"] = f"元素不应存在: {selector}"
                    except Exception:
                        result["success"] = True
                        result["message"] = f"元素不存在: {selector}"

            elif assert_type == "text_equals":
                if selector:
                    element = await self._page.wait_for_selector(selector, timeout=timeout)
                    if element:
                        actual = await element.text_content()
                        if actual and actual.strip() == expected:
                            result["success"] = True
                            result["message"] = f"文本等于 '{expected}'"
                        else:
                            result["message"] = f"期望 '{expected}'，实际 '{actual}'"

            elif assert_type == "text_contains":
                if selector:
                    element = await self._page.wait_for_selector(selector, timeout=timeout)
                    if element:
                        actual = await element.text_content()
                        if actual and expected in actual:
                            result["success"] = True
                            result["message"] = f"文本包含 '{expected}'"
                        else:
                            result["message"] = f"期望包含 '{expected}'，实际 '{actual}'"

            elif assert_type == "value_equals":
                if selector:
                    element = await self._page.wait_for_selector(selector, timeout=timeout)
                    if element:
                        actual = await element.input_value()
                        if actual == expected:
                            result["success"] = True
                            result["message"] = f"值等于 '{expected}'"
                        else:
                            result["message"] = f"期望 '{expected}'，实际 '{actual}'"

            elif assert_type == "url_contains":
                current_url = self._page.url
                if expected in current_url:
                    result["success"] = True
                    result["message"] = f"URL 包含 '{expected}'"
                else:
                    result["message"] = f"URL 期望包含 '{expected}'，实际 '{current_url}'"

            elif assert_type == "title_contains":
                title = await self._page.title()
                if expected in title:
                    result["success"] = True
                    result["message"] = f"标题包含 '{expected}'"
                else:
                    result["message"] = f"标题期望包含 '{expected}'，实际 '{title}'"

            elif assert_type == "attribute_equals":
                if selector:
                    element = await self._page.wait_for_selector(selector, timeout=timeout)
                    if element:
                        attr_name = step.get("attributeName", "")
                        actual = await element.get_attribute(attr_name)
                        if actual == expected:
                            result["success"] = True
                            result["message"] = f"属性 {attr_name} 等于 '{expected}'"
                        else:
                            result["message"] = f"属性 {attr_name} 期望 '{expected}'，实际 '{actual}'"

            else:
                result["message"] = f"未知断言类型: {assert_type}"

        except Exception as e:
            result["message"] = f"断言失败: {str(e)}"

        return result

    async def _cleanup(self):
        """清理资源"""
        for resource in [self._page, self._context, self._browser]:
            if resource:
                try:
                    await resource.close()
                except Exception:
                    pass
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass


def execute_case_sync(
    steps: list[dict],
    base_url: str = "",
    viewport_width: int = 1280,
    viewport_height: int = 720,
) -> dict:
    """同步执行用例（用于 API 调用）"""
    # Windows 必须使用 ProactorEventLoop
    if platform.system() == "Windows":
        loop = asyncio.ProactorEventLoop()
    else:
        loop = asyncio.new_event_loop()

    asyncio.set_event_loop(loop)
    try:
        executor = UIExecutor()
        result = loop.run_until_complete(
            executor.execute(steps, base_url, viewport_width, viewport_height)
        )
        return result
    finally:
        loop.close()

"""
UI 录制核心服务
使用 Playwright 管理浏览器实例，通过 CDP 协议捕获用户操作

Windows 兼容性说明：
Playwright 需要 ProactorEventLoop 来支持子进程，但 uvicorn 默认使用 SelectorEventLoop。
解决方案：在独立线程中运行 Playwright，使用新的事件循环。
"""
import asyncio
import base64
import json
import logging
import platform
import threading
import time
import uuid
from typing import Callable, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

logger = logging.getLogger(__name__)


class UIRecorder:
    """UI 录制器：管理浏览器实例，捕获用户操作并推送截图"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.status = "idle"  # idle / connecting / recording / paused / stopped
        self.url = ""
        self.steps: list[dict] = []
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._screenshot_task: Optional[asyncio.Task] = None
        self._step_counter = 0
        self._pending_input_value = ""
        # 输入模式相关
        self._input_active = False
        self._input_target = None
        self._input_value = ""
        self._input_initial_value = ""  # 输入框的初始值
        # URL 参数化
        self._base_url: Optional[str] = None  # 环境的 base_url，用于变量替换
        # 回调函数
        self._screenshot_callback: Optional[Callable] = None
        self._step_callback: Optional[Callable] = None
        # 线程和事件循环
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None

    def start(
        self,
        url: str,
        base_url: Optional[str] = None,
        viewport_width: int = 1280,
        viewport_height: int = 720,
        user_agent: Optional[str] = None,
        screenshot_callback: Optional[Callable] = None,
        step_callback: Optional[Callable] = None,
    ):
        """启动录制会话（同步方法，内部启动线程）"""
        self.url = url
        self._base_url = base_url.rstrip('/') if base_url else None
        self.status = "connecting"
        self._screenshot_callback = screenshot_callback
        self._step_callback = step_callback

        # 在独立线程中启动 Playwright
        self._thread = threading.Thread(
            target=self._run_in_thread,
            args=(url, viewport_width, viewport_height, user_agent),
            daemon=True,
        )
        self._thread.start()

    def _run_in_thread(self, url, viewport_width, viewport_height, user_agent):
        """在独立线程中运行 Playwright 事件循环"""
        # Windows 必须使用 ProactorEventLoop 才能支持子进程（Playwright 需要）
        if platform.system() == "Windows":
            self._loop = asyncio.ProactorEventLoop()
        else:
            self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            # 启动 Playwright
            print(f"[RECORDER] 正在启动浏览器...")
            self._loop.run_until_complete(
                self._start_playwright(url, viewport_width, viewport_height, user_agent)
            )
            print(f"[RECORDER] 浏览器启动完成，状态: {self.status}")
            # 保持事件循环运行，直到录制停止
            if self.status != "stopped":
                self._loop.run_forever()
        except RuntimeError as e:
            # stop() 在启动阶段调用 loop.stop() 会触发此异常，属于预期行为
            if "Event loop stopped before Future completed" in str(e):
                print(f"[RECORDER] 启动过程中被停止，状态: {self.status}")
            else:
                print(f"[RECORDER] 录制线程异常: {e}")
                import traceback
                traceback.print_exc()
            self.status = "stopped"
        except Exception as e:
            print(f"[RECORDER] 录制线程异常: {e}")
            import traceback
            traceback.print_exc()
            self.status = "stopped"
        finally:
            if self._loop.is_closed():
                return
            # 启动被中断时，用已停止的 loop 清理 Playwright 资源
            # run_until_complete 可以在 stop() 后的 loop 上再次调用
            try:
                self._loop.run_until_complete(self._stop_playwright())
            except Exception as e:
                print(f"[RECORDER] 清理 Playwright 资源异常: {e}")
            # 清理事件循环中的所有任务
            try:
                pending = asyncio.all_tasks(self._loop)
                for task in pending:
                    task.cancel()
                if pending:
                    self._loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception as e:
                print(f"[RECORDER] 清理任务异常: {e}")
            try:
                if not self._loop.is_closed():
                    self._loop.close()
            except Exception as e:
                print(f"[RECORDER] 关闭事件循环异常: {e}")

    async def _start_playwright(self, url, viewport_width, viewport_height, user_agent):
        """启动 Playwright 浏览器"""
        try:
            print(f"[RECORDER] 启动 Playwright...")
            self._playwright = await async_playwright().start()
            if self.status == "stopped":
                return
            print(f"[RECORDER] 启动 Chromium 浏览器...")
            self._browser = await asyncio.wait_for(
                self._playwright.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-gpu",
                        "--disable-dev-shm-usage",
                        "--disable-extensions",
                        "--disable-background-timer-throttling",
                        "--disable-backgrounding-occluded-windows",
                        "--disable-renderer-backgrounding",
                    ]
                ),
                timeout=15,
            )
            if self.status == "stopped":
                return
            print(f"[RECORDER] 创建浏览器上下文...")
            self._context = await asyncio.wait_for(
                self._browser.new_context(
                    viewport={"width": viewport_width, "height": viewport_height},
                    user_agent=user_agent,
                ),
                timeout=10,
            )
            if self.status == "stopped":
                return
            # 检查浏览器是否仍然连接
            if not self._browser.is_connected():
                raise RuntimeError("Chromium 浏览器在创建上下文后断开连接，可能已崩溃")
            print(f"[RECORDER] 创建新页面...")
            self._page = await asyncio.wait_for(
                self._context.new_page(),
                timeout=25,
            )
            if self.status == "stopped":
                return

            # 监听新页面打开事件（target="_blank" 链接、window.open 等）
            self._context.on("page", lambda new_page: asyncio.ensure_future(
                self._on_new_page(new_page)
            ))

            # 监听当前页面导航事件
            self._setup_page_listeners(self._page)

            # 注入操作监听脚本
            print(f"[RECORDER] 注入事件监听脚本...")
            await self._inject_event_listeners()

            # 记录录制开始时间，用于忽略后续的自动重定向
            self._recording_start_time = time.time()

            # 导航到目标页面
            print(f"[RECORDER] 导航到 {url}...")
            try:
                await self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
            except Exception as e:
                # 某些页面会重定向导致 frame detached，忽略此错误
                print(f"[RECORDER] 导航警告（可能是重定向）: {e}")

            # 等待页面完全加载（包括重定向）
            print(f"[RECORDER] 等待页面稳定...")
            await asyncio.sleep(3)  # 等待 3 秒让所有重定向完成
            await self._page.wait_for_load_state("domcontentloaded", timeout=10000)

            # 记录最终的 URL 作为第一个导航步骤
            final_url = self._page.url
            print(f"[RECORDER] 页面最终 URL: {final_url}")

            self.status = "recording"

            # 清空之前自动记录的导航步骤，只保留最终的
            self.steps = []
            self._step_counter = 0
            await self._record_step({"action": "navigate", "url": final_url})

            # 重新设置录制开始时间，忽略后续 5 秒内的自动导航
            self._recording_start_time = time.time()

            print(f"[RECORDER] 浏览器启动成功，开始录制")

            # 启动截图循环
            self._screenshot_task = asyncio.create_task(self._screenshot_loop())

            print(f"[RECORDER] 录制会话 {self.session_id} 已启动: {url}")

        except asyncio.TimeoutError:
            # 诊断信息：判断卡在哪一步
            if not self._browser:
                msg = "Chromium 浏览器启动超时（15秒），请检查: 1) playwright install chromium  2) 杀毒软件是否拦截  3) 系统资源是否充足"
            elif not self._context:
                msg = "创建浏览器上下文超时（10秒）"
            elif not self._page:
                msg = "创建新页面超时（25秒），Chromium 可能已崩溃，请尝试 playwright install chromium 重新安装"
            else:
                msg = "浏览器启动超时"
            print(f"[RECORDER] {msg}")
            logger.error(msg)
            raise RuntimeError(msg)
        except Exception as e:
            self.status = "stopped"
            print(f"[RECORDER] 录制会话启动失败: {type(e).__name__}: {e}")
            logger.error(f"录制会话启动失败: {e}")
            raise

    def stop(self) -> list[dict]:
        """停止录制，返回录制的步骤（同步方法，幂等）"""
        # 幂等：已停止则直接返回
        if self.status == "stopped":
            return self.steps

        was_starting = self.status == "connecting"
        self.status = "stopped"

        if was_starting:
            # 还在启动阶段：只设标志，不干预事件循环
            # 避免取消 future 导致浏览器被 Playwright 关闭（TargetClosedError）
            # _start_playwright 会通过 asyncio.wait_for 超时后自然退出并清理资源
            print(f"[RECORDER] 启动阶段停止，后台线程将自行清理")
            return self.steps

        if self._loop and not self._loop.is_closed():
            if self._loop.is_running():
                # 录制阶段（run_forever 中），通过协程安全清理
                try:
                    future = asyncio.run_coroutine_threadsafe(self._stop_playwright(), self._loop)
                    future.result(timeout=5)
                except Exception as e:
                    print(f"[RECORDER] 停止 Playwright 异常: {e}")
                self._loop.call_soon_threadsafe(self._loop.stop)
            # 等待线程结束
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=10)
        return self.steps

    async def _stop_playwright(self):
        """停止 Playwright 浏览器"""
        try:
            if self._screenshot_task and not self._screenshot_task.done():
                self._screenshot_task.cancel()
                try:
                    await self._screenshot_task
                except asyncio.CancelledError:
                    pass

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
        except Exception as e:
            print(f"[RECORDER] 清理资源异常: {e}")

        print(f"[RECORDER] 录制会话 {self.session_id} 已停止，共 {len(self.steps)} 个步骤")

    def inject_event(self, event: dict):
        """接收前端事件并注入到浏览器（同步方法）"""
        if not self._page or self.status != "recording":
            return
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self._inject_event_async(event), self._loop)

    async def _on_frame_navigated(self, frame):
        """页面导航完成后的回调"""
        try:
            current_url = frame.url
            print(f"[FRAME_NAVIGATED] 触发: url={current_url[:50] if current_url else 'None'}, status={self.status}")

            # 跳过 about:blank
            if not current_url or current_url == "about:blank":
                print(f"[FRAME_NAVIGATED] 跳过: about:blank")
                return

            # 录制开始后的前 5 秒内，跳过自动重定向的导航
            if hasattr(self, '_recording_start_time'):
                elapsed = time.time() - self._recording_start_time
                if elapsed < 5:
                    print(f"[FRAME_NAVIGATED] 跳过: 录制开始后 {elapsed:.1f} 秒内的自动导航")
                    return

            # 如果最后一步是 click，跳过导航记录（Vue 路由跳转等）
            if self.steps:
                last_step = self.steps[-1]
                last_action = last_step.get("action")
                # 最后一步是 click，且时间在 2 秒内，跳过导航
                if last_action == "click":
                    last_time = last_step.get("timestamp", 0)
                    now = time.time() * 1000
                    if (now - last_time) < 2000:
                        print(f"[FRAME_NAVIGATED] 跳过: 点击后的导航 (last_action={last_action})")
                        return

            # 防重复：如果当前 URL 和最后一个 navigate 步骤的 URL 相同，跳过
            if self.steps:
                last_step = self.steps[-1]
                if last_step.get("action") == "navigate" and last_step.get("url") == current_url:
                    print(f"[FRAME_NAVIGATED] 跳过: 重复导航 {current_url[:50]}")
                    return
                # 如果最后一步是 new_page 且 URL 相同，也跳过
                if last_step.get("action") == "new_page" and last_step.get("url") == current_url:
                    print(f"[FRAME_NAVIGATED] 跳过: new_page 后的导航 {current_url[:50]}")
                    return

            # 等待页面加载
            await frame.wait_for_load_state("domcontentloaded", timeout=5000)

            # 重新注入事件监听
            await self._inject_event_listeners()

            # 记录导航步骤
            print(f"[FRAME_NAVIGATED] 记录 navigate 步骤: {current_url[:50]}")
            await self._record_step({"action": "navigate", "url": current_url})

            # 清除初始导航标记
            if hasattr(self, '_initial_navigation'):
                del self._initial_navigation
        except Exception as e:
            print(f"[FRAME_NAVIGATED] 异常: {e}")

    async def _inject_event_async(self, event: dict):
        """异步注入事件"""
        event_type = event.get("type")
        print(f"[EVENT] 收到事件: type={event_type}, action={event.get('action')}")
        try:
            if event_type == "mouse_event":
                await self._handle_mouse_event(event)
            elif event_type == "keyboard_event":
                await self._handle_keyboard_event(event)
            elif event_type == "input_event":
                if event.get("action") == "finish":
                    # 结束输入
                    await self._finish_input()
                else:
                    self._pending_input_value = event.get("value", "")
            elif event_type == "command":
                await self._handle_command(event)
        except Exception as e:
            print(f"[EVENT] 注入事件失败: {e}")
            import traceback
            traceback.print_exc()

    def _setup_page_listeners(self, page):
        """为页面设置导航监听器"""
        async def on_frame_navigated(frame):
            if frame == page.main_frame:
                await self._on_frame_navigated(frame)
        page.on("framenavigated", lambda frame: asyncio.ensure_future(on_frame_navigated(frame)))

    async def _on_new_page(self, new_page):
        """处理新打开的页面（target="_blank" 等）"""
        try:
            # 防重复：如果已经在处理新页面，跳过
            if hasattr(self, '_processing_new_page') and self._processing_new_page:
                print(f"[NEW_PAGE] 跳过: 正在处理另一个新页面")
                return
            self._processing_new_page = True
            print(f"[NEW_PAGE] 开始处理新页面")

            # 等待新页面加载
            await new_page.wait_for_load_state("domcontentloaded", timeout=10000)

            # 保存当前页面到历史栈
            if not hasattr(self, '_page_history'):
                self._page_history = []
            if self._page:
                self._page_history.append(self._page)

            # 切换到新页面
            old_url = self._page.url if self._page else ""
            self._page = new_page

            # 为新页面设置监听器
            self._setup_page_listeners(new_page)

            # 注入事件监听脚本
            await self._inject_event_listeners()

            # 记录页面切换步骤（_record_step 会自动调用 _step_callback）
            new_url = new_page.url
            print(f"[NEW_PAGE] 记录 new_page 步骤: {new_url[:50]}")
            await self._record_step({
                "action": "new_page",
                "url": new_url,
                "from_url": old_url,
            })

        except Exception as e:
            print(f"[NEW_PAGE] 异常: {e}")
        finally:
            self._processing_new_page = False

    async def _screenshot_loop(self):
        """定时截图循环"""
        try:
            while self.status == "recording":
                if self._page and self._screenshot_callback:
                    try:
                        screenshot_bytes = await self._page.screenshot(type="jpeg", quality=85)
                        screenshot = base64.b64encode(screenshot_bytes).decode("utf-8")
                        if screenshot:
                            # 回调可能是同步的
                            result = self._screenshot_callback(screenshot)
                            if asyncio.iscoroutine(result):
                                await result
                    except Exception as e:
                        logger.debug(f"截图推送异常: {e}")
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass

    async def _inject_event_listeners(self):
        """注入页面事件监听脚本"""
        await self._page.evaluate("""
            () => {
                window.addEventListener('beforeunload', () => {
                    window.__recorder_navigating = true;
                });
                document.addEventListener('input', (e) => {
                    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                        window.__last_input_value = e.target.value;
                    }
                }, true);
            }
        """)

    async def _handle_mouse_event(self, event: dict):
        """处理鼠标事件"""
        x = event.get("x", 0)
        y = event.get("y", 0)
        action = event.get("action")
        is_dragging = event.get("isDragging", False)
        is_click = event.get("isClick", False)

        print(f"[MOUSE_EVENT] action={action}, x={x}, y={y}, isClick={is_click}")

        if action == "scroll":
            # 处理滚轮事件
            delta_x = event.get("deltaX", 0)
            delta_y = event.get("deltaY", 0)
            await self._page.mouse.move(x, y)
            await self._page.mouse.wheel(delta_x, delta_y)
            await self._record_step({
                "action": "scroll",
                "deltaX": delta_x,
                "deltaY": delta_y,
            })
        elif action == "mousedown":
            print(f"[MOUSE_EVENT] 执行 mousedown at ({x}, {y})")
            await self._page.mouse.move(x, y)
            await self._page.mouse.down()
            # 记录拖拽起点
            self._drag_start = {"x": x, "y": y}
            self._drag_path = [{"x": x, "y": y}]
            print(f"[MOUSE_EVENT] mousedown 执行完成")
        elif action == "mousemove":
            await self._page.mouse.move(x, y)
            # 如果正在拖拽，记录拖拽路径点
            if is_dragging and hasattr(self, '_drag_path'):
                self._drag_path.append({"x": x, "y": y})
            elif is_dragging:
                self._drag_path = [{"x": self._drag_start.get("x", x), "y": self._drag_start.get("y", y)}, {"x": x, "y": y}]
        elif action == "mouseup":
            print(f"[MOUSE_EVENT] mouseup: isClick={is_click}, isDragging={is_dragging}, drag_path_len={len(self._drag_path) if hasattr(self, '_drag_path') else 0}")
            # 如果是拖拽操作结束
            if is_dragging and hasattr(self, '_drag_path') and len(self._drag_path) > 1:
                await self._page.mouse.up()
                start = self._drag_path[0]
                end = {"x": x, "y": y}
                element_info = await self._get_element_at_point(start["x"], start["y"])
                if element_info:
                    await self._record_step({
                        "action": "drag",
                        "target": element_info,
                        "from": start,
                        "to": end,
                    })
                self._drag_path = []
            elif is_click:
                # 先获取元素信息
                element_info = await self._get_element_at_point(x, y)
                print(f"[MOUSE_EVENT] element_info: {element_info is not None}")

                if element_info:
                    # 检查是否点击了输入框
                    tag = element_info.get("tagName", "")
                    is_input = tag in ["input", "textarea"] or tag == "select"

                    # 如果之前有输入在进行，先结束
                    if self._input_active:
                        await self._finish_input()

                    # 先记录点击步骤（在执行 up 之前，避免导航事件先触发）
                    await self._record_step({"action": "click", "target": element_info})

                    if is_input:
                        # 执行 up（mousedown 已经执行了 down）
                        await self._page.mouse.up()
                        # 发送输入框信息给前端，弹出输入弹窗
                        if self._step_callback:
                            try:
                                result = self._step_callback({
                                    "_msg_type": "input_target",
                                    "target": element_info,
                                })
                                if asyncio.iscoroutine(result):
                                    await result
                            except Exception:
                                pass
                        print(f"[INPUT] 检测到输入框，等待用户输入: {element_info.get('selector')}")
                    else:
                        # 执行 up（mousedown 已经执行了 down）
                        print(f"[MOUSE_EVENT] 执行 mouseup at ({x}, {y})")
                        await self._page.mouse.up()
                        print(f"[MOUSE_EVENT] mouseup 执行成功")
                        # 点击后短暂延迟，让页面有时间响应（如下拉框展开）
                        await asyncio.sleep(0.3)
                else:
                    # 没有获取到元素信息，直接执行 up
                    await self._page.mouse.up()
            else:
                # 普通 mouseup，清理拖拽路径
                if hasattr(self, '_drag_path'):
                    self._drag_path = []
        elif action == "dblclick":
            await self._page.mouse.dblclick(x, y)
            element_info = await self._get_element_at_point(x, y)
            if element_info:
                await self._flush_pending_input()
                await self._record_step({"action": "dblclick", "target": element_info})

    async def _check_and_wait_navigation(self, element_info: dict) -> bool:
        """检查元素是否是链接，如果是则等待页面导航"""
        tag = element_info.get("tagName", "")
        href = element_info.get("attributes", {}).get("href")
        if tag == "a" and href and not href.startswith("#") and not href.startswith("javascript:"):
            try:
                # 等待导航完成（最多 3 秒）
                await self._page.wait_for_load_state("domcontentloaded", timeout=3000)
                # 导航完成后重新注入事件监听
                await self._inject_event_listeners()
                return True
            except Exception:
                pass
        return False

    async def _handle_keyboard_event(self, event: dict):
        """处理键盘事件"""
        key = event.get("key")
        if not key:
            return
        special_keys = ["Enter", "Tab", "Escape", "Backspace", "Delete",
                        "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"]
        if key in special_keys:
            # 如果输入模式激活，先结束输入
            if self._input_active:
                await self._finish_input()
            await self._page.keyboard.press(key)
            # 只有在非输入框聚焦时才录制按键步骤
            if not self._input_active:
                await self._record_step({"action": "press", "key": key})

    async def _finish_input(self):
        """结束输入模式，记录输入步骤"""
        if not self._input_active:
            return

        # 获取输入框的当前值（使用保存的选择器）
        current_value = ""
        if self._input_target:
            try:
                selector = self._input_target.get("selector")
                if selector:
                    current_value = await self._page.evaluate(f"""
                        () => {{
                            const el = document.querySelector('{selector}');
                            return el ? (el.value || '') : '';
                        }}
                    """)
            except Exception as e:
                print(f"[INPUT] 获取输入值失败: {e}")

        # 计算新输入的值（当前值 - 初始值）
        new_input = current_value
        if self._input_initial_value and current_value.startswith(self._input_initial_value):
            new_input = current_value[len(self._input_initial_value):]

        # 只有当有新输入时才记录步骤
        if self._input_target and new_input:
            await self._record_step({
                "action": "type",
                "target": self._input_target,
                "value": new_input,
            })
            print(f"[INPUT] 输入完成: '{new_input[:50]}'")
        else:
            print(f"[INPUT] 无新输入，跳过记录")

        self._input_active = False
        self._input_target = None
        self._input_initial_value = ""

    async def _handle_command(self, event: dict):
        """处理控制命令"""
        action = event.get("action")
        if action == "pause":
            self.status = "paused"
        elif action == "resume":
            self.status = "recording"
        elif action == "go_back":
            # 返回上一个窗口
            if hasattr(self, '_page_history') and self._page_history:
                old_page = self._page
                self._page = self._page_history.pop()
                # 为旧页面重新设置监听器
                self._setup_page_listeners(self._page)
                await self._inject_event_listeners()
                await self._record_step({
                    "action": "go_back",
                    "url": self._page.url,
                })
                print(f"[COMMAND] 返回上一个窗口: {self._page.url[:50]}")
        elif action == "get_element":
            # 获取指定坐标的元素信息
            x = event.get("x", 0)
            y = event.get("y", 0)
            element_info = await self._get_element_at_point(x, y)
            if element_info:
                # 通过回调发送元素信息给前端
                if self._step_callback:
                    try:
                        result = self._step_callback({
                            "_msg_type": "element_info",
                            "element": element_info,
                        })
                        if asyncio.iscoroutine(result):
                            await result
                    except Exception:
                        pass
                print(f"[COMMAND] 获取元素信息: {element_info.get('tagName')}")
        elif action == "add_assert":
            # 添加断言步骤
            assertion = event.get("assertion", {})
            await self._record_step({
                "action": "assert",
                **assertion,
            })
        elif action == "input_text":
            # 输入文本到指定输入框
            target = event.get("target", {})
            value = event.get("value", "")
            selector = target.get("selector")
            if selector and value:
                try:
                    # 清空输入框并输入新值
                    await self._page.evaluate(f"""
                        () => {{
                            const el = document.querySelector('{selector}');
                            if (el) {{
                                el.value = '';
                                el.focus();
                            }}
                        }}
                    """)
                    await self._page.fill(selector, value)
                    # 记录输入步骤
                    await self._record_step({
                        "action": "type",
                        "target": target,
                        "value": value,
                    })
                    print(f"[INPUT] 输入完成: '{value[:50]}' -> {selector}")
                except Exception as e:
                    print(f"[INPUT] 输入失败: {e}")

    async def _flush_pending_input(self):
        """将待记录的输入操作刷出为步骤"""
        value = self._pending_input_value
        if value:
            try:
                focused = await self._page.evaluate("""
                    () => {
                        const el = document.activeElement;
                        if (!el) return null;
                        return {
                            selector: el.id ? '#' + el.id : null,
                            xpath: null,
                            text: el.textContent?.trim()?.substring(0, 50) || '',
                            tagName: el.tagName?.toLowerCase() || '',
                        };
                    }
                """)
                if focused:
                    await self._record_step({"action": "type", "target": focused, "value": value})
            except Exception:
                pass
            self._pending_input_value = ""

    async def _get_element_at_point(self, x: int, y: int) -> Optional[dict]:
        """获取指定坐标处的元素信息"""
        try:
            return await self._page.evaluate("""
                ([x, y]) => {
                    const el = document.elementFromPoint(x, y);
                    if (!el) return null;

                    // 动态 class 过滤列表
                    const dynamicClasses = [
                        'focus', 'active', 'hover', 'disabled', 'checked', 'selected',
                        'open', 'close', 'show', 'hide', 'visible', 'hidden',
                        'loading', 'error', 'success', 'warning', 'info'
                    ];

                    function isDynamicClass(cls) {
                        const lower = cls.toLowerCase();
                        return dynamicClasses.some(dc => lower.includes(dc)) ||
                               lower.startsWith('arco-') && lower.endsWith('-focus') ||
                               lower.startsWith('arco-') && lower.endsWith('-active') ||
                               lower.startsWith('arco-') && lower.endsWith('-hover') ||
                               lower.match(/^t-|^ant-|^el-|^arco-/);
                    }

                    function getSelector(el) {
                        if (el.id) return '#' + CSS.escape(el.id);
                        let path = [];
                        while (el && el.nodeType === 1) {
                            let selector = el.tagName.toLowerCase();
                            if (el.id) { path.unshift('#' + CSS.escape(el.id)); break; }
                            if (el.className && typeof el.className === 'string') {
                                const classes = el.className.trim().split(/\\s+/)
                                    .filter(c => c && !c.startsWith('__') && !isDynamicClass(c))
                                    .map(c => '.' + CSS.escape(c));
                                if (classes.length > 0) selector += classes.slice(0, 2).join('');
                            }
                            const parent = el.parentElement;
                            if (parent) {
                                const siblings = Array.from(parent.children).filter(s => s.tagName === el.tagName);
                                if (siblings.length > 1) selector += ':nth-of-type(' + (siblings.indexOf(el) + 1) + ')';
                            }
                            path.unshift(selector);
                            el = el.parentElement;
                        }
                        return path.join(' > ');
                    }

                    function getXPath(el) {
                        if (el.id) return '//*[@id="' + el.id + '"]';
                        const parts = [];
                        while (el && el.nodeType === 1) {
                            let index = 1, sibling = el.previousSibling;
                            while (sibling) {
                                if (sibling.nodeType === 1 && sibling.tagName === el.tagName) index++;
                                sibling = sibling.previousSibling;
                            }
                            parts.unshift(el.tagName.toLowerCase() + '[' + index + ']');
                            el = el.parentElement;
                        }
                        return '/' + parts.join('/');
                    }

                    return {
                        selector: getSelector(el),
                        xpath: getXPath(el),
                        text: (el.textContent || '').trim().substring(0, 100),
                        tagName: el.tagName.toLowerCase(),
                        rect: el.getBoundingClientRect().toJSON(),
                        attributes: {
                            id: el.id || undefined,
                            name: el.getAttribute('name') || undefined,
                            type: el.getAttribute('type') || undefined,
                            placeholder: el.getAttribute('placeholder') || undefined,
                        }
                    };
                }
            """, [x, y])
        except Exception as e:
            logger.debug(f"获取元素信息失败: {e}")
            return None

    def _parameterize_url(self, url: str) -> str:
        """将 URL 中的 base_url 部分替换为 {{base_url}} 变量"""
        if not self._base_url or not url:
            return url
        # 如果 URL 以 base_url 开头，替换为变量
        if url.startswith(self._base_url):
            path = url[len(self._base_url):]
            if not path.startswith('/'):
                path = '/' + path
            return '{{base_url}}' + path
        return url

    async def _record_step(self, step_data: dict):
        """记录一个操作步骤"""
        action = step_data.get("action")
        now = time.time() * 1000

        # URL 参数化：将 base_url 替换为变量
        if "url" in step_data and step_data["url"]:
            step_data["url"] = self._parameterize_url(step_data["url"])

        print(f"[RECORD_STEP] 被调用: step_data={step_data}, 当前步骤数={len(self.steps)}")

        if not action:
            print(f"[RECORD_STEP] 警告: action 为空，跳过记录")
            return

        # 去重逻辑
        if action == "navigate":
            # 跳过重复导航（1秒内相同URL）
            if hasattr(self, '_last_navigate'):
                last_url, last_time = self._last_navigate
                if step_data.get("url") == last_url and (now - last_time) < 1000:
                    logger.info(f"[_record_step] 跳过: 1秒内重复导航 {step_data.get('url', '')[:50]}")
                    return
            # 跳过紧跟在 new_page 后的导航
            if self.steps and self.steps[-1].get("action") == "new_page":
                logger.info(f"[_record_step] 跳过: new_page 后的导航")
                return
            self._last_navigate = (step_data.get("url"), now)

        elif action == "new_page":
            # 如果刚记录了 click，把 click 和 new_page 合并
            if self.steps and self.steps[-1].get("action") == "click":
                last_step = self.steps[-1]
                last_step["action"] = "new_page"
                last_step["url"] = step_data.get("url")
                last_step["from_url"] = step_data.get("from_url")
                print(f"[RECORD_STEP] 合并 click + new_page: {step_data.get('url', '')[:50]}")
                # 直接发送更新后的步骤数据
                if self._step_callback:
                    try:
                        result = self._step_callback(last_step)
                        if asyncio.iscoroutine(result):
                            await result
                    except Exception:
                        pass
                return

        self._last_step_time = now
        self._step_counter += 1

        # 构建步骤数据，确保 action 字段存在
        step = {
            "id": f"step_{self._step_counter}",
            "order": self._step_counter,
            "timestamp": int(now),
            "action": action,  # 显式设置 action
            **{k: v for k, v in step_data.items() if k != "action"},  # 避免覆盖
        }

        print(f"[RECORD_STEP] 记录步骤 #{self._step_counter}: action={step.get('action')}, id={step.get('id')}")

        # 不保存截图到数据库，只在实时显示时使用
        self.steps.append(step)

        if self._step_callback:
            try:
                result = self._step_callback(step)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.info(f"[_record_step] 步骤回调异常: {e}")


# ========== 全局会话管理 ==========

class RecordingSessionManager:
    """录制会话管理器"""

    def __init__(self):
        self._sessions: dict[str, UIRecorder] = {}

    def create_session(self) -> UIRecorder:
        """创建新的录制会话"""
        session_id = str(uuid.uuid4())[:8]
        recorder = UIRecorder(session_id)
        self._sessions[session_id] = recorder
        return recorder

    def get_session(self, session_id: str) -> Optional[UIRecorder]:
        """获取录制会话"""
        return self._sessions.get(session_id)

    def remove_session(self, session_id: str):
        """移除录制会话"""
        recorder = self._sessions.pop(session_id, None)
        if recorder and recorder.status != "stopped":
            recorder.stop()

    def stop_all(self):
        """停止所有录制会话"""
        for session_id in list(self._sessions.keys()):
            self.remove_session(session_id)


# 全局单例
recording_manager = RecordingSessionManager()

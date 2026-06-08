"""
ADB 服务
管理 Android 设备连接和 Monkey 测试执行
"""
import logging
import re
import subprocess
import threading
import uuid
from dataclasses import dataclass, field
from typing import Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class DeviceInfo:
    """设备信息"""
    serial: str
    status: str  # device / offline / unauthorized
    model: str = ""


@dataclass
class MonkeyTask:
    """Monkey 测试任务"""
    task_id: str
    device_serial: str
    process: Optional[subprocess.Popen] = None
    status: str = "running"  # running / completed / stopped / failed
    output_lines: list[str] = field(default_factory=list)
    _log_callback: Optional[Callable] = field(default=None, repr=False)


class ADBService:
    """ADB 设备管理服务"""

    def __init__(self):
        self._monkey_tasks: dict[str, MonkeyTask] = {}

    def list_devices(self) -> list[DeviceInfo]:
        """获取已连接的 Android 设备列表"""
        try:
            result = subprocess.run(
                ["adb", "devices", "-l"],
                capture_output=True, text=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
            )
            if result.returncode != 0:
                raise RuntimeError(f"adb 命令执行失败: {result.stderr}")

            devices = []
            for line in result.stdout.strip().splitlines()[1:]:  # 跳过第一行标题
                line = line.strip()
                if not line:
                    continue
                # 格式: SERIAL  STATUS  [key:value...]
                parts = line.split()
                if len(parts) < 2:
                    continue
                serial, status = parts[0], parts[1]
                # 提取 model
                model = ""
                for part in parts[2:]:
                    if part.startswith("model:"):
                        model = part.split(":", 1)[1]
                        break
                devices.append(DeviceInfo(serial=serial, status=status, model=model))
            return devices

        except FileNotFoundError:
            raise RuntimeError("未找到 adb 命令，请确认已安装 Android SDK Platform Tools 并添加到 PATH")
        except subprocess.TimeoutExpired:
            raise RuntimeError("adb 命令超时，请检查设备连接")

    def get_device_model(self, serial: str) -> str:
        """获取设备型号"""
        try:
            result = subprocess.run(
                ["adb", "-s", serial, "shell", "getprop", "ro.product.model"],
                capture_output=True, text=True, timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
            )
            return result.stdout.strip()
        except Exception:
            return ""

    def start_monkey(
        self,
        device_serial: str,
        event_count: int = 1000,
        interval: int = 300,
        seed: Optional[int] = None,
        package: Optional[str] = None,
        pct_touch: int = 15,
        pct_motion: int = 10,
        pct_trackball: int = 15,
        pct_nav: int = 20,
        pct_majornav: int = 15,
        pct_syskeys: int = 5,
        pct_appswitch: int = 2,
        pct_anyevent: int = 18,
        log_callback: Optional[Callable] = None,
    ) -> str:
        """启动 Monkey 测试，返回 task_id"""
        task_id = str(uuid.uuid4())[:8]

        # 构建 monkey 命令
        cmd = [
            "adb", "-s", device_serial, "shell",
            "monkey",
            "-v",
            "--pct-touch", str(pct_touch),
            "--pct-motion", str(pct_motion),
            "--pct-trackball", str(pct_trackball),
            "--pct-nav", str(pct_nav),
            "--pct-majornav", str(pct_majornav),
            "--pct-syskeys", str(pct_syskeys),
            "--pct-appswitch", str(pct_appswitch),
            "--pct-anyevent", str(pct_anyevent),
            "--throttle", str(interval),
        ]

        if seed is not None:
            cmd.extend(["-s", str(seed)])
        if package:
            cmd.extend(["-p", package])

        cmd.append(str(event_count))

        logger.info(f"[MONKEY] 启动命令: {' '.join(cmd)}")
        print(f"[MONKEY] 启动命令: {' '.join(cmd)}")

        task = MonkeyTask(
            task_id=task_id,
            device_serial=device_serial,
            _log_callback=log_callback,
        )

        # 在线程中启动进程并读取输出
        def _run():
            try:
                flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    creationflags=flags,
                )
                task.process = proc

                for line in proc.stdout:
                    line = line.rstrip("\n")
                    task.output_lines.append(line)
                    if task._log_callback:
                        try:
                            task._log_callback(task_id, line)
                        except Exception:
                            pass

                proc.wait()
                if task.status == "running":
                    task.status = "completed"
                    if task._log_callback:
                        try:
                            task._log_callback(task_id, f"[MONKEY] 测试完成，退出码: {proc.returncode}")
                        except Exception:
                            pass

            except Exception as e:
                task.status = "failed"
                logger.error(f"[MONKEY] 任务 {task_id} 异常: {e}")
                if task._log_callback:
                    try:
                        task._log_callback(task_id, f"[MONKEY] 错误: {e}")
                    except Exception:
                        pass

        self._monkey_tasks[task_id] = task
        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

        return task_id

    def stop_monkey(self, task_id: str) -> bool:
        """停止 Monkey 测试"""
        task = self._monkey_tasks.get(task_id)
        if not task or task.status != "running":
            return False

        task.status = "stopped"

        # 通过 adb shell kill 终止设备上的 monkey 进程
        try:
            subprocess.run(
                ["adb", "-s", task.device_serial, "shell", "pkill", "-f", "com.android.commands.monkey"],
                capture_output=True, timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
            )
        except Exception as e:
            logger.warning(f"[MONKEY] 终止 monkey 进程失败: {e}")

        # 同时终止本地 adb 进程
        if task.process:
            try:
                task.process.terminate()
            except Exception:
                pass

        return True

    def get_task(self, task_id: str) -> Optional[MonkeyTask]:
        """获取任务信息"""
        return self._monkey_tasks.get(task_id)

    def get_task_logs(self, task_id: str, offset: int = 0) -> list[str]:
        """获取任务日志（从 offset 开始）"""
        task = self._monkey_tasks.get(task_id)
        if not task:
            return []
        return task.output_lines[offset:]


# 全局单例
adb_service = ADBService()

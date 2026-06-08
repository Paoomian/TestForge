"""Monkey 测试 API"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from core.deps import check_permission
from schemas.monkey import MonkeyConfig, MonkeyTaskResponse, DeviceInfoSchema
from services.adb_service import adb_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/devices", response_model=list[DeviceInfoSchema])
def list_devices(
    current_user=Depends(check_permission("ui_test:read")),
):
    """获取已连接的 Android 设备列表"""
    try:
        devices = adb_service.list_devices()
        return [DeviceInfoSchema(serial=d.serial, status=d.status, model=d.model) for d in devices]
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start", response_model=MonkeyTaskResponse)
def start_monkey(
    config: MonkeyConfig,
    current_user=Depends(check_permission("ui_test:write")),
):
    """启动 Monkey 测试"""
    # 校验设备是否存在
    devices = adb_service.list_devices()
    device_map = {d.serial: d for d in devices}
    if config.device_serial not in device_map:
        raise HTTPException(status_code=400, detail=f"设备 {config.device_serial} 未连接")
    if device_map[config.device_serial].status != "device":
        raise HTTPException(status_code=400, detail=f"设备 {config.device_serial} 状态异常: {device_map[config.device_serial].status}")

    task_id = adb_service.start_monkey(
        device_serial=config.device_serial,
        event_count=config.event_count,
        interval=config.interval,
        seed=config.seed,
        package=config.package,
        pct_touch=config.pct_touch,
        pct_motion=config.pct_motion,
        pct_trackball=config.pct_trackball,
        pct_nav=config.pct_nav,
        pct_majornav=config.pct_majornav,
        pct_syskeys=config.pct_syskeys,
        pct_appswitch=config.pct_appswitch,
        pct_anyevent=config.pct_anyevent,
    )

    return MonkeyTaskResponse(
        task_id=task_id,
        device_serial=config.device_serial,
        status="running",
    )


@router.post("/stop")
def stop_monkey(
    task_id: str,
    current_user=Depends(check_permission("ui_test:write")),
):
    """停止 Monkey 测试"""
    success = adb_service.stop_monkey(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在或已结束")
    return {"message": "已发送停止命令", "task_id": task_id}


@router.get("/status/{task_id}")
def get_task_status(
    task_id: str,
    current_user=Depends(check_permission("ui_test:read")),
):
    """获取 Monkey 任务状态"""
    task = adb_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {
        "task_id": task.task_id,
        "device_serial": task.device_serial,
        "status": task.status,
        "lines_count": len(task.output_lines),
    }

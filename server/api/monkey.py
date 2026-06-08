"""Monkey 测试 API"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.deps import check_permission, get_current_user
from database import get_db
from models.monkey import MonkeyPreset
from schemas.monkey import (
    MonkeyConfig, MonkeyTaskResponse, DeviceInfoSchema,
    MonkeyPresetCreate, MonkeyPresetUpdate, MonkeyPresetOut,
)
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


# ==================== 预设配置 CRUD ====================

# 默认预设模板（单一App Monkey测试热门配置）
DEFAULT_PRESETS = [
    {
        "id": -1,
        "name": "标准测试 - 均衡分布",
        "pct_touch": 25,
        "pct_motion": 15,
        "pct_trackball": 0,
        "pct_nav": 25,
        "pct_majornav": 10,
        "pct_syskeys": 5,
        "pct_appswitch": 0,
        "pct_anyevent": 20,
        "event_count": 5000,
        "interval": 300,
    },
    {
        "id": -2,
        "name": "UI密集型 - 触摸为主",
        "pct_touch": 40,
        "pct_motion": 25,
        "pct_trackball": 0,
        "pct_nav": 15,
        "pct_majornav": 5,
        "pct_syskeys": 5,
        "pct_appswitch": 0,
        "pct_anyevent": 10,
        "event_count": 10000,
        "interval": 200,
    },
    {
        "id": -3,
        "name": "导航密集型 - 页面跳转",
        "pct_touch": 15,
        "pct_motion": 10,
        "pct_trackball": 0,
        "pct_nav": 30,
        "pct_majornav": 25,
        "pct_syskeys": 10,
        "pct_appswitch": 0,
        "pct_anyevent": 10,
        "event_count": 8000,
        "interval": 350,
    },
    {
        "id": -4,
        "name": "快速冒烟 - 短时验证",
        "pct_touch": 30,
        "pct_motion": 15,
        "pct_trackball": 0,
        "pct_nav": 25,
        "pct_majornav": 10,
        "pct_syskeys": 5,
        "pct_appswitch": 0,
        "pct_anyevent": 15,
        "event_count": 1000,
        "interval": 200,
    },
]


@router.get("/presets/default")
def list_default_presets():
    """获取默认预设模板"""
    return DEFAULT_PRESETS


@router.get("/presets", response_model=list[MonkeyPresetOut])
def list_presets(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取当前用户的所有预设"""
    return db.query(MonkeyPreset).filter(
        MonkeyPreset.user_id == current_user.id
    ).order_by(MonkeyPreset.updated_at.desc()).all()


@router.post("/presets", response_model=MonkeyPresetOut)
def create_preset(
    data: MonkeyPresetCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """创建预设"""
    preset = MonkeyPreset(
        **data.model_dump(),
        user_id=current_user.id,
    )
    db.add(preset)
    db.commit()
    db.refresh(preset)
    return preset


@router.put("/presets/{preset_id}", response_model=MonkeyPresetOut)
def update_preset(
    preset_id: int,
    data: MonkeyPresetUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """更新预设"""
    preset = db.query(MonkeyPreset).filter(
        MonkeyPreset.id == preset_id,
        MonkeyPreset.user_id == current_user.id,
    ).first()
    if not preset:
        raise HTTPException(status_code=404, detail="预设不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(preset, key, value)

    db.commit()
    db.refresh(preset)
    return preset


@router.delete("/presets/{preset_id}")
def delete_preset(
    preset_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """删除预设"""
    preset = db.query(MonkeyPreset).filter(
        MonkeyPreset.id == preset_id,
        MonkeyPreset.user_id == current_user.id,
    ).first()
    if not preset:
        raise HTTPException(status_code=404, detail="预设不存在")

    db.delete(preset)
    db.commit()
    return {"message": "已删除"}

"""
UI 录制 API
管理录制会话的启动、停止和状态查询
"""
import logging
import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas.ui_case import RecordingStartRequest, RecordingStopRequest, RecordingSession, UICaseInDB
from models import UICase, User
from core.deps import get_current_user, check_permission
from services.ui_recorder import recording_manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/start", response_model=RecordingSession)
def start_recording(
    request: RecordingStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("ui_test:write"))
):
    """启动录制会话"""
    recorder = recording_manager.create_session()

    # 获取环境的 base_url
    base_url = request.base_url
    if request.environment_id and not base_url:
        from models import Environment
        env = db.query(Environment).filter(Environment.id == request.environment_id).first()
        if env and env.base_url:
            base_url = env.base_url

    try:
        # 启动浏览器并导航到目标URL（同步方法，内部启动线程）
        recorder.start(
            url=request.url,
            base_url=base_url,
            viewport_width=request.viewport_width,
            viewport_height=request.viewport_height,
            user_agent=request.user_agent,
        )

        # 等待浏览器启动完成（首次启动可能需要更长时间）
        for _ in range(200):  # 最多等待20秒
            if recorder.status in ["recording", "stopped"]:
                break
            time.sleep(0.1)

        if recorder.status != "recording":
            error_msg = f"启动录制超时，当前状态: {recorder.status}"
            print(f"[RECORDER] {error_msg}")
            # 先停止录制，再删除会话
            recorder.stop()
            recording_manager.remove_session(recorder.session_id)
            raise HTTPException(status_code=500, detail=error_msg)

        return RecordingSession(
            session_id=recorder.session_id,
            status=recorder.status,
            url=recorder.url,
            websocket_url=f"/ws/ui-record/{recorder.session_id}",
        )
    except HTTPException:
        raise
    except Exception as e:
        recording_manager.remove_session(recorder.session_id)
        raise HTTPException(status_code=500, detail=f"启动录制失败: {str(e)}")


@router.post("/stop")
def stop_recording(
    session_id: str,
    request: RecordingStopRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("ui_test:write"))
):
    """停止录制并保存用例"""
    recorder = recording_manager.get_session(session_id)
    if not recorder:
        raise HTTPException(status_code=404, detail="录制会话不存在")

    # 停止录制，获取步骤
    recorder.stop()

    # 优先使用前端传入的步骤，否则使用录制器中的步骤
    steps = request.steps if request.steps else recorder.steps

    # 保存到数据库
    saved_case = None
    if request.save_to_project and steps:
        case = UICase(
            name=request.name,
            description=request.description or "",
            steps=steps,
            base_url=recorder.url,
            browser_config={"viewport_width": 1280, "viewport_height": 720},
            project_id=request.project_id,
        )
        db.add(case)
        db.commit()
        db.refresh(case)
        saved_case = UICaseInDB.model_validate(case)

    # 清理会话
    recording_manager.remove_session(session_id)

    return {
        "message": "录制已停止",
        "steps_count": len(steps),
        "steps": steps,
        "saved_case": saved_case,
    }


@router.get("/status/{session_id}")
def get_recording_status(
    session_id: str,
    current_user: User = Depends(check_permission("ui_test:read"))
):
    """获取录制会话状态"""
    recorder = recording_manager.get_session(session_id)
    if not recorder:
        raise HTTPException(status_code=404, detail="录制会话不存在")

    return {
        "session_id": session_id,
        "status": recorder.status,
        "url": recorder.url,
        "steps_count": len(recorder.steps),
    }


@router.delete("/{session_id}")
def delete_recording_session(
    session_id: str,
    current_user: User = Depends(check_permission("ui_test:write"))
):
    """删除录制会话（不保存）"""
    recorder = recording_manager.get_session(session_id)
    if recorder:
        recording_manager.remove_session(session_id)
    return {"message": "录制会话已删除"}


@router.post("/save")
def save_recording_as_case(
    session_id: str,
    name: str,
    project_id: int,
    description: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("ui_test:write"))
):
    """将录制的步骤保存为 UI 用例"""
    recorder = recording_manager.get_session(session_id)
    if not recorder:
        raise HTTPException(status_code=404, detail="录制会话不存在")

    if not recorder.steps:
        raise HTTPException(status_code=400, detail="没有录制到任何步骤")

    case = UICase(
        name=name,
        description=description,
        steps=recorder.steps,
        base_url=recorder.url,
        browser_config={"viewport_width": 1280, "viewport_height": 720},
        project_id=project_id,
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    return {
        "message": "用例保存成功",
        "case": UICaseInDB.model_validate(case),
    }

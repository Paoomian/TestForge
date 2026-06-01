"""
UI 用例执行 API
支持单用例调试执行
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import UICase, User
from core.deps import get_current_user, check_permission
from services.ui_executor import execute_case_sync

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/run/{case_id}")
def run_ui_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("ui_test:write"))
):
    """执行单个 UI 用例"""
    # 获取用例
    case = db.query(UICase).filter(UICase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="UI 用例不存在")

    if not case.steps:
        raise HTTPException(status_code=400, detail="用例没有步骤")

    # 执行用例
    try:
        result = execute_case_sync(
            steps=case.steps,
            base_url=case.base_url or "",
            viewport_width=1280,
            viewport_height=720,
        )
        return {
            "case_id": case_id,
            "case_name": case.name,
            **result,
        }
    except Exception as e:
        logger.error(f"执行用例失败: {e}")
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")


@router.post("/run-steps")
def run_custom_steps(
    request: dict,
    current_user: User = Depends(check_permission("ui_test:write"))
):
    """执行自定义步骤（用于调试）"""
    steps = request.get("steps", [])
    base_url = request.get("base_url", "")

    if not steps:
        raise HTTPException(status_code=400, detail="没有步骤")

    try:
        result = execute_case_sync(
            steps=steps,
            base_url=base_url,
            viewport_width=1280,
            viewport_height=720,
        )
        return result
    except Exception as e:
        logger.error(f"执行步骤失败: {e}")
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")

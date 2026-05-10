from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, APITestCase
from schemas.test_run import RunRequest, RunResult
from core.deps import get_current_user, check_permission
from services.api_test_runner.runner import TestRunner

router = APIRouter()


@router.post("/{case_id}/run", response_model=RunResult)
async def run_test_case(
    case_id: int,
    req: RunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:execute")),
):
    """执行单个用例"""
    # 检查用例是否存在
    case = db.query(APITestCase).filter(APITestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")

    runner = TestRunner(db)
    result = await runner.run_case(
        case_id=case_id,
        environment_id=req.environment_id,
        temp_variables=req.variables,
    )
    return result

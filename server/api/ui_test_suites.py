"""UI 任务配置 API"""
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import User, UITestSuite, UICase, Environment, TestRun, TestRunStatus, TestRunDetail, TestRunDetailStatus
from schemas.ui_test_suite import UITestSuiteCreate, UITestSuiteUpdate, UITestSuiteOut
from core.deps import get_current_user, check_permission

router = APIRouter()


class BatchDeleteRequest(BaseModel):
    suite_ids: List[int]


@router.get("", response_model=dict)
async def list_ui_test_suites(
    project_id: int = Query(None),
    keyword: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询 UI 任务配置列表"""
    query = db.query(UITestSuite)

    # 项目筛选
    if project_id:
        query = query.filter(UITestSuite.project_id == project_id)

    # 关键字搜索
    if keyword:
        query = query.filter(UITestSuite.name.contains(keyword))

    # 总数
    total = query.count()

    # 分页
    suites = query.order_by(UITestSuite.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for suite in suites:
        # 获取项目名称
        project_name = None
        if suite.project_id:
            from models import Project
            project = db.query(Project).filter(Project.id == suite.project_id).first()
            project_name = project.name if project else None

        # 获取环境名称
        environment_name = None
        if suite.environment_id:
            env = db.query(Environment).filter(Environment.id == suite.environment_id).first()
            environment_name = env.name if env else None

        items.append(UITestSuiteOut(
            id=suite.id,
            project_id=suite.project_id,
            project_name=project_name,
            name=suite.name,
            description=suite.description,
            case_ids=suite.case_ids or [],
            case_count=len(suite.case_ids or []),
            environment_id=suite.environment_id,
            environment_name=environment_name,
            failure_strategy=suite.failure_strategy,
            browser=suite.browser,
            viewport_width=suite.viewport_width,
            viewport_height=suite.viewport_height,
            tags=suite.tags or [],
            creator_id=suite.creator_id,
            created_at=suite.created_at,
            updated_at=suite.updated_at,
        ))

    return {"items": items, "total": total}


@router.get("/{suite_id}", response_model=UITestSuiteOut)
async def get_ui_test_suite(
    suite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取 UI 任务配置详情"""
    suite = db.query(UITestSuite).filter(UITestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="任务配置不存在")

    # 获取项目名称
    project_name = None
    if suite.project_id:
        from models import Project
        project = db.query(Project).filter(Project.id == suite.project_id).first()
        project_name = project.name if project else None

    # 获取环境名称
    environment_name = None
    if suite.environment_id:
        env = db.query(Environment).filter(Environment.id == suite.environment_id).first()
        environment_name = env.name if env else None

    return UITestSuiteOut(
        id=suite.id,
        project_id=suite.project_id,
        project_name=project_name,
        name=suite.name,
        description=suite.description,
        case_ids=suite.case_ids or [],
        case_count=len(suite.case_ids or []),
        environment_id=suite.environment_id,
        environment_name=environment_name,
        failure_strategy=suite.failure_strategy,
        browser=suite.browser,
        viewport_width=suite.viewport_width,
        viewport_height=suite.viewport_height,
        tags=suite.tags or [],
        creator_id=suite.creator_id,
        created_at=suite.created_at,
        updated_at=suite.updated_at,
    )


@router.post("", response_model=UITestSuiteOut)
async def create_ui_test_suite(
    req: UITestSuiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("ui_test:write")),
):
    """创建 UI 任务配置"""
    # 验证用例存在
    if req.case_ids:
        cases = db.query(UICase).filter(UICase.id.in_(req.case_ids)).all()
        if len(cases) != len(req.case_ids):
            found_ids = {c.id for c in cases}
            missing = [cid for cid in req.case_ids if cid not in found_ids]
            raise HTTPException(status_code=400, detail=f"用例不存在: {missing}")

    suite = UITestSuite(
        project_id=req.project_id,
        name=req.name,
        description=req.description,
        case_ids=req.case_ids,
        environment_id=req.environment_id,
        failure_strategy=req.failure_strategy,
        browser=req.browser,
        viewport_width=req.viewport_width,
        viewport_height=req.viewport_height,
        tags=req.tags,
        creator_id=current_user.id,
    )
    db.add(suite)
    db.commit()
    db.refresh(suite)

    return UITestSuiteOut(
        id=suite.id,
        project_id=suite.project_id,
        name=suite.name,
        description=suite.description,
        case_ids=suite.case_ids or [],
        case_count=len(suite.case_ids or []),
        environment_id=suite.environment_id,
        failure_strategy=suite.failure_strategy,
        browser=suite.browser,
        viewport_width=suite.viewport_width,
        viewport_height=suite.viewport_height,
        tags=suite.tags or [],
        creator_id=suite.creator_id,
        created_at=suite.created_at,
        updated_at=suite.updated_at,
    )


@router.put("/{suite_id}", response_model=UITestSuiteOut)
async def update_ui_test_suite(
    suite_id: int,
    req: UITestSuiteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("ui_test:write")),
):
    """更新 UI 任务配置"""
    suite = db.query(UITestSuite).filter(UITestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="任务配置不存在")

    # 过滤掉已删除的用例ID
    if req.case_ids is not None:
        cases = db.query(UICase).filter(UICase.id.in_(req.case_ids)).all()
        valid_ids = {c.id for c in cases}
        req.case_ids = [cid for cid in req.case_ids if cid in valid_ids]

    # 更新字段
    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(suite, key, value)

    db.commit()
    db.refresh(suite)

    # 获取项目名称
    project_name = None
    if suite.project_id:
        from models import Project
        project = db.query(Project).filter(Project.id == suite.project_id).first()
        project_name = project.name if project else None

    # 获取环境名称
    environment_name = None
    if suite.environment_id:
        env = db.query(Environment).filter(Environment.id == suite.environment_id).first()
        environment_name = env.name if env else None

    return UITestSuiteOut(
        id=suite.id,
        project_id=suite.project_id,
        project_name=project_name,
        name=suite.name,
        description=suite.description,
        case_ids=suite.case_ids or [],
        case_count=len(suite.case_ids or []),
        environment_id=suite.environment_id,
        environment_name=environment_name,
        failure_strategy=suite.failure_strategy,
        browser=suite.browser,
        viewport_width=suite.viewport_width,
        viewport_height=suite.viewport_height,
        tags=suite.tags or [],
        creator_id=suite.creator_id,
        created_at=suite.created_at,
        updated_at=suite.updated_at,
    )


@router.delete("/{suite_id}")
async def delete_ui_test_suite(
    suite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("ui_test:write")),
):
    """删除 UI 任务配置"""
    suite = db.query(UITestSuite).filter(UITestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="任务配置不存在")

    db.delete(suite)
    db.commit()

    return {"message": "删除成功"}


@router.post("/batch-delete")
async def batch_delete_ui_test_suites(
    req: BatchDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("ui_test:write")),
):
    """批量删除 UI 任务配置"""
    if not req.suite_ids:
        raise HTTPException(status_code=400, detail="请选择要删除的任务配置")

    suites = db.query(UITestSuite).filter(UITestSuite.id.in_(req.suite_ids)).all()
    if len(suites) != len(req.suite_ids):
        found_ids = {s.id for s in suites}
        missing = [sid for sid in req.suite_ids if sid not in found_ids]
        raise HTTPException(status_code=404, detail=f"任务配置不存在: {missing}")

    for suite in suites:
        db.delete(suite)

    db.commit()

    return {"message": f"成功删除 {len(suites)} 个任务配置"}


@router.post("/{suite_id}/run")
async def run_ui_test_suite(
    suite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("ui_test:execute")),
):
    """执行 UI 任务配置"""
    suite = db.query(UITestSuite).filter(UITestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="任务配置不存在")

    # 验证用例存在
    if not suite.case_ids:
        raise HTTPException(status_code=400, detail="任务配置中没有用例，请编辑任务配置添加用例")

    cases = db.query(UICase).filter(UICase.id.in_(suite.case_ids)).all()
    if len(cases) != len(suite.case_ids):
        found_ids = {c.id for c in cases}
        missing_count = len(suite.case_ids) - len(found_ids)
        raise HTTPException(status_code=400, detail=f"有 {missing_count} 个用例已被删除，请删除该任务配置后重新创建")

    # 生成任务名称
    now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    task_name = f"UI批量执行-{now}"

    # 创建执行任务
    test_run = TestRun(
        project_id=suite.project_id,
        name=task_name,
        test_type="ui_batch",
        case_ids=suite.case_ids,
        environment_id=suite.environment_id,
        failure_strategy=suite.failure_strategy,
        status=TestRunStatus.PENDING,
        total_count=len(suite.case_ids),
        creator_id=current_user.id,
    )
    db.add(test_run)
    db.flush()

    # 创建用例执行明细
    case_snapshot = {c.id: c for c in cases}
    for order, case_id in enumerate(suite.case_ids, start=1):
        case = case_snapshot.get(case_id)
        detail = TestRunDetail(
            test_run_id=test_run.id,
            case_id=None,
            case_number=str(case_id),
            case_name=case.name if case else None,
            execution_order=order,
            status=TestRunDetailStatus.PENDING,
            node_type="ui_case",
        )
        db.add(detail)

    db.commit()
    db.refresh(test_run)

    # 启动 Celery 任务
    from tasks.ui_batch_run_task import ui_batch_run_task
    task = ui_batch_run_task.delay(
        test_run.id,
        suite.browser,
        suite.viewport_width,
        suite.viewport_height,
    )

    return {"id": test_run.id, "name": task_name}

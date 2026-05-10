from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import User, TestSuite, APITestCase, Environment, Project
from schemas.test_suite import (
    TestSuiteCreate, TestSuiteUpdate, TestSuiteInfo, TestSuiteList, TestSuiteRunRequest
)
from core.deps import get_current_user, check_permission

router = APIRouter()


@router.post("", response_model=TestSuiteInfo)
async def create_suite(
    req: TestSuiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:execute")),
):
    """创建任务配置"""
    # 验证用例存在
    if req.case_ids:
        cases = db.query(APITestCase).filter(APITestCase.id.in_(req.case_ids)).all()
        if len(cases) != len(req.case_ids):
            found_ids = {c.id for c in cases}
            missing = [cid for cid in req.case_ids if cid not in found_ids]
            raise HTTPException(status_code=400, detail=f"用例不存在: {missing}")

    suite = TestSuite(
        project_id=req.project_id,
        name=req.name,
        description=req.description,
        case_ids=req.case_ids,
        environment_id=req.environment_id,
        concurrency=req.concurrency,
        failure_strategy=req.failure_strategy,
        variables=req.variables,
        tags=req.tags,
        creator_id=current_user.id,
    )
    db.add(suite)
    db.commit()
    db.refresh(suite)

    return _build_suite_info(suite, db)


@router.get("", response_model=dict)
async def list_suites(
    project_id: int = Query(None),
    keyword: str = Query(None),
    tag: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """任务配置列表"""
    query = db.query(TestSuite)

    if project_id:
        query = query.filter(TestSuite.project_id == project_id)
    if keyword:
        query = query.filter(TestSuite.name.contains(keyword))
    if tag:
        query = query.filter(TestSuite.tags.contains([tag]))

    total = query.count()
    suites = query.order_by(TestSuite.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    # 批量查询项目和环境名称
    project_ids = list(set(s.project_id for s in suites))
    projects = db.query(Project).filter(Project.id.in_(project_ids)).all()
    project_map = {p.id: p.name for p in projects}

    env_ids = list(set(s.environment_id for s in suites if s.environment_id))
    envs = db.query(Environment).filter(Environment.id.in_(env_ids)).all() if env_ids else []
    env_map = {e.id: e.name for e in envs}

    items = []
    for s in suites:
        items.append(TestSuiteList(
            id=s.id,
            project_id=s.project_id,
            project_name=project_map.get(s.project_id),
            name=s.name,
            description=s.description,
            case_count=len(s.case_ids or []),
            environment_name=env_map.get(s.environment_id),
            concurrency=s.concurrency,
            failure_strategy=s.failure_strategy,
            tags=s.tags or [],
            creator_id=s.creator_id,
            created_at=s.created_at,
        ))

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [item.model_dump() for item in items],
    }


@router.get("/{suite_id}", response_model=TestSuiteInfo)
async def get_suite(
    suite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取任务配置详情"""
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="任务配置不存在")

    return _build_suite_info(suite, db)


@router.put("/{suite_id}", response_model=TestSuiteInfo)
async def update_suite(
    suite_id: int,
    req: TestSuiteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:execute")),
):
    """更新任务配置"""
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="任务配置不存在")

    # 验证用例存在
    if req.case_ids is not None:
        if req.case_ids:
            cases = db.query(APITestCase).filter(APITestCase.id.in_(req.case_ids)).all()
            if len(cases) != len(req.case_ids):
                found_ids = {c.id for c in cases}
                missing = [cid for cid in req.case_ids if cid not in found_ids]
                raise HTTPException(status_code=400, detail=f"用例不存在: {missing}")

    # 更新字段
    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(suite, key, value)

    db.commit()
    db.refresh(suite)

    return _build_suite_info(suite, db)


@router.delete("/{suite_id}")
async def delete_suite(
    suite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:execute")),
):
    """删除任务配置"""
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="任务配置不存在")

    db.delete(suite)
    db.commit()

    return {"message": "删除成功"}


@router.post("/{suite_id}/copy", response_model=TestSuiteInfo)
async def copy_suite(
    suite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:execute")),
):
    """复制任务配置"""
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="任务配置不存在")

    new_suite = TestSuite(
        project_id=suite.project_id,
        name=f"{suite.name} (副本)",
        description=suite.description,
        case_ids=suite.case_ids,
        environment_id=suite.environment_id,
        concurrency=suite.concurrency,
        failure_strategy=suite.failure_strategy,
        variables=suite.variables,
        tags=suite.tags,
        creator_id=current_user.id,
    )
    db.add(new_suite)
    db.commit()
    db.refresh(new_suite)

    return _build_suite_info(new_suite, db)


@router.post("/{suite_id}/run")
async def run_suite(
    suite_id: int,
    req: TestSuiteRunRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:execute")),
):
    """执行任务配置（复用批量执行）"""
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="任务配置不存在")

    if not suite.case_ids:
        raise HTTPException(status_code=400, detail="任务配置中没有用例")

    # 合并配置（请求参数覆盖默认配置）
    environment_id = (req.environment_id if req and req.environment_id else suite.environment_id)
    concurrency = (req.concurrency if req and req.concurrency else suite.concurrency)
    failure_strategy = (req.failure_strategy if req and req.failure_strategy else suite.failure_strategy)
    variables = {**(suite.variables or {}), **((req.variables if req and req.variables else {}))}

    # 复用批量执行逻辑
    from datetime import datetime, timezone
    from models import TestRun, TestRunDetail, TestRunStatus, TestRunDetailStatus

    now = datetime.now(timezone.utc)
    task_name = f"{suite.name}-{now.strftime('%Y%m%d%H%M%S')}"

    # 创建执行任务
    test_run = TestRun(
        project_id=suite.project_id,
        name=task_name,
        test_type="api_batch",
        case_ids=suite.case_ids,
        environment_id=environment_id,
        concurrency=concurrency,
        failure_strategy=failure_strategy,
        variables=variables,
        status=TestRunStatus.PENDING.value,
        total_count=len(suite.case_ids),
        creator_id=current_user.id,
    )
    db.add(test_run)
    db.flush()

    # 创建执行明细
    for order, case_id in enumerate(suite.case_ids, start=1):
        detail = TestRunDetail(
            test_run_id=test_run.id,
            case_id=case_id,
            execution_order=order,
            status=TestRunDetailStatus.PENDING.value,
        )
        db.add(detail)

    db.commit()

    # 发送 Celery 任务
    from tasks.batch_run_task import batch_run_task
    batch_run_task.delay(test_run.id)

    return {"id": test_run.id, "message": "执行任务已创建"}


def _build_suite_info(suite: TestSuite, db: Session) -> TestSuiteInfo:
    """构建任务配置详情"""
    env_name = None
    if suite.environment_id:
        env = db.query(Environment).filter(Environment.id == suite.environment_id).first()
        env_name = env.name if env else None

    return TestSuiteInfo(
        id=suite.id,
        project_id=suite.project_id,
        name=suite.name,
        description=suite.description,
        case_ids=suite.case_ids or [],
        case_count=len(suite.case_ids or []),
        environment_id=suite.environment_id,
        environment_name=env_name,
        concurrency=suite.concurrency,
        failure_strategy=suite.failure_strategy,
        variables=suite.variables or {},
        tags=suite.tags or [],
        creator_id=suite.creator_id,
        created_at=suite.created_at,
        updated_at=suite.updated_at,
    )

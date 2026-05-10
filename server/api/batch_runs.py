from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import User, TestRun, TestRunDetail, TestRunStatus, TestRunDetailStatus, APITestCase
from schemas.test_run import BatchRunCreate, BatchRunList, BatchRunInfo, BatchRunDetailSummary, BatchRunDetailFull
from core.deps import get_current_user, check_permission

router = APIRouter()


@router.post("", response_model=BatchRunInfo)
async def create_batch_run(
    req: BatchRunCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:execute")),
):
    """创建批量执行任务"""
    # 验证用例存在
    cases = db.query(APITestCase).filter(APITestCase.id.in_(req.case_ids)).all()
    if len(cases) != len(req.case_ids):
        found_ids = {c.id for c in cases}
        missing = [cid for cid in req.case_ids if cid not in found_ids]
        raise HTTPException(status_code=400, detail=f"用例不存在: {missing}")

    # 验证并发数
    if req.concurrency not in (1, 3, 5, 10):
        raise HTTPException(status_code=400, detail="并发数必须是 1/3/5/10")

    # 验证失败策略
    if req.failure_strategy not in ("continue", "stop"):
        raise HTTPException(status_code=400, detail="失败策略必须是 continue/stop")

    # 生成任务名称
    project_id = cases[0].project_id if cases else 0
    now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    task_name = f"批量执行-{now}"

    # 创建任务
    test_run = TestRun(
        project_id=project_id,
        name=task_name,
        test_type="api_batch",
        case_ids=req.case_ids,
        environment_id=req.environment_id,
        concurrency=req.concurrency,
        failure_strategy=req.failure_strategy,
        variables=req.variables,
        status=TestRunStatus.PENDING,
        total_count=len(req.case_ids),
        creator_id=current_user.id,
    )
    db.add(test_run)
    db.flush()

    # 创建用例执行明细
    for order, case_id in enumerate(req.case_ids, start=1):
        detail = TestRunDetail(
            test_run_id=test_run.id,
            case_id=case_id,
            execution_order=order,
            status=TestRunDetailStatus.PENDING,
        )
        db.add(detail)

    db.commit()
    db.refresh(test_run)

    # 延迟导入避免循环依赖
    from tasks.batch_run_task import batch_run_task
    task = batch_run_task.delay(test_run.id)

    return _build_run_info(test_run, db)


@router.get("", response_model=dict)
async def list_batch_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询任务列表"""
    query = db.query(TestRun).filter(TestRun.test_type == "api_batch")

    # 状态筛选
    if status:
        query = query.filter(TestRun.status == status)

    # 总数
    total = query.count()

    # 分页
    runs = query.order_by(TestRun.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for run in runs:
        progress = 0
        if run.total_count > 0:
            completed = run.pass_count + run.fail_count + run.error_count
            progress = round(completed / run.total_count * 100, 1)

        items.append(BatchRunList(
            id=run.id,
            name=run.name,
            status=run.status or "pending",
            concurrency=run.concurrency,
            failure_strategy=run.failure_strategy,
            total_count=run.total_count,
            pass_count=run.pass_count,
            fail_count=run.fail_count,
            error_count=run.error_count,
            progress=progress,
            start_time=run.start_time,
            end_time=run.end_time,
            duration=run.duration,
            creator_id=run.creator_id,
            created_at=run.created_at,
        ))

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [item.model_dump() for item in items],
    }


@router.get("/{run_id}", response_model=BatchRunInfo)
async def get_batch_run(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询任务详情"""
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="任务不存在")

    return _build_run_info(run, db)


@router.get("/{run_id}/details/{detail_id}", response_model=BatchRunDetailFull)
async def get_detail(
    run_id: int,
    detail_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询单条用例执行详情"""
    detail = db.query(TestRunDetail).filter(
        TestRunDetail.id == detail_id,
        TestRunDetail.test_run_id == run_id,
    ).first()
    if not detail:
        raise HTTPException(status_code=404, detail="执行记录不存在")

    case = db.query(APITestCase).filter(APITestCase.id == detail.case_id).first()

    return BatchRunDetailFull(
        id=detail.id,
        test_run_id=detail.test_run_id,
        case_id=detail.case_id,
        case_name=case.name if case else None,
        case_number=case.case_number if case else None,
        execution_order=detail.execution_order,
        status=detail.status or "pending",
        request_snapshot=detail.request_snapshot,
        response_info=detail.response_info,
        assertions=detail.assertions or [],
        extracted_vars=detail.extracted_vars or {},
        script_output=detail.script_output or {},
        error_message=detail.error_message,
        duration_ms=detail.duration_ms,
        started_at=detail.started_at,
        finished_at=detail.finished_at,
    )


@router.post("/{run_id}/cancel")
async def cancel_batch_run(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:execute")),
):
    """取消任务"""
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="任务不存在")

    if run.status not in (TestRunStatus.PENDING, TestRunStatus.RUNNING):
        raise HTTPException(status_code=400, detail="任务已结束，无法取消")

    # 设置取消标志
    run.cancelled = True
    db.commit()

    # 尝试撤销 Celery 任务
    if run.celery_task_id:
        from celery_app import celery_app as app
        app.control.revoke(run.celery_task_id, terminate=True)

    return {"message": "取消请求已提交"}


@router.delete("/{run_id}")
async def delete_batch_run(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:execute")),
):
    """删除任务"""
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="任务不存在")

    if run.status == TestRunStatus.RUNNING:
        raise HTTPException(status_code=400, detail="运行中的任务无法删除")

    # 删除明细（级联）
    db.query(TestRunDetail).filter(TestRunDetail.test_run_id == run_id).delete()
    db.delete(run)
    db.commit()

    return {"message": "删除成功"}


def _build_run_info(run: TestRun, db: Session) -> BatchRunInfo:
    """构建任务详情响应"""
    # 查询明细
    details = db.query(TestRunDetail).filter(
        TestRunDetail.test_run_id == run.id
    ).order_by(TestRunDetail.execution_order).all()

    # 获取用例名称
    case_ids = [d.case_id for d in details]
    cases = db.query(APITestCase).filter(APITestCase.id.in_(case_ids)).all()
    case_map = {c.id: c for c in cases}

    detail_summaries = []
    # 实时统计
    pass_count = 0
    fail_count = 0
    error_count = 0

    for d in details:
        case = case_map.get(d.case_id)
        # 从 response_info 中提取接口响应时间和状态码
        api_duration_ms = None
        status_code = None
        if d.response_info:
            api_duration_ms = d.response_info.get('elapsed_ms')
            status_code = d.response_info.get('status_code')

        # 统计
        if d.status == 'pass':
            pass_count += 1
        elif d.status == 'fail':
            fail_count += 1
        elif d.status == 'error':
            error_count += 1

        detail_summaries.append(BatchRunDetailSummary(
            id=d.id,
            case_id=d.case_id,
            case_name=case.name if case else None,
            case_number=case.case_number if case else None,
            execution_order=d.execution_order,
            status=d.status or "pending",
            duration_ms=d.duration_ms,
            api_duration_ms=api_duration_ms,
            status_code=status_code,
            error_message=d.error_message,
        ))

    # 实时计算进度
    total_count = len(details)
    completed = pass_count + fail_count + error_count
    progress = round(completed / total_count * 100, 1) if total_count > 0 else 0

    return BatchRunInfo(
        id=run.id,
        project_id=run.project_id,
        name=run.name,
        status=run.status or "pending",
        case_ids=run.case_ids or [],
        environment_id=run.environment_id,
        concurrency=run.concurrency,
        failure_strategy=run.failure_strategy,
        variables=run.variables or {},
        total_count=total_count,
        pass_count=pass_count,
        fail_count=fail_count,
        error_count=error_count,
        progress=progress,
        celery_task_id=run.celery_task_id,
        start_time=run.start_time,
        end_time=run.end_time,
        duration=run.duration,
        creator_id=run.creator_id,
        created_at=run.created_at,
        details=detail_summaries,
    )

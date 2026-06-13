from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import User, TestRun, TestRunDetail, TestRunStatus, TestRunDetailStatus, APITestCase, UICase, Environment, SceneNode
from schemas.test_run import (
    BatchRunCreate, BatchRunList, BatchRunInfo, BatchRunDetailSummary, BatchRunDetailFull,
    BatchRunReport, TestSummary, PerformanceStats, FailureAnalysis, FailureCategory, APICallStat,
    NodeTreeItem
)
from core.deps import get_current_user, check_permission

router = APIRouter()


class BatchDeleteRequest(BaseModel):
    run_ids: List[int]


@router.post("", response_model=BatchRunInfo)
async def create_batch_run(
    req: BatchRunCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:execute")),
):
    """创建批量执行任务"""
    # 根据 test_type 验证用例存在
    if req.test_type == "ui_batch":
        cases = db.query(UICase).filter(UICase.id.in_(req.case_ids)).all()
        if len(cases) != len(req.case_ids):
            found_ids = {c.id for c in cases}
            missing = [cid for cid in req.case_ids if cid not in found_ids]
            raise HTTPException(status_code=400, detail=f"UI用例不存在: {missing}")
    else:
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
    prefix = "UI批量执行" if req.test_type == "ui_batch" else "批量执行"
    task_name = f"{prefix}-{now}"

    # 创建任务
    test_run = TestRun(
        project_id=project_id,
        name=task_name,
        test_type=req.test_type,
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

    # 创建用例执行明细（附带用例快照）
    if req.test_type == "ui_batch":
        case_snapshot = {c.id: c for c in db.query(UICase).filter(UICase.id.in_(req.case_ids)).all()}
        for order, case_id in enumerate(req.case_ids, start=1):
            case = case_snapshot.get(case_id)
            detail = TestRunDetail(
                test_run_id=test_run.id,
                case_id=None,  # UI用例不设置case_id，避免外键冲突
                case_number=str(case_id),  # 用case_number字段存储UI用例ID
                case_name=case.name if case else None,
                execution_order=order,
                status=TestRunDetailStatus.PENDING,
                node_type="ui_case",  # 标记为UI用例
            )
            db.add(detail)
    else:
        case_snapshot = {c.id: c for c in db.query(APITestCase).filter(APITestCase.id.in_(req.case_ids)).all()}
        for order, case_id in enumerate(req.case_ids, start=1):
            case = case_snapshot.get(case_id)
            detail = TestRunDetail(
                test_run_id=test_run.id,
                case_id=case_id,
                case_name=case.name if case else None,
                case_number=case.case_number if case else None,
                execution_order=order,
                status=TestRunDetailStatus.PENDING,
            )
            db.add(detail)

    db.commit()
    db.refresh(test_run)

    # 根据 test_type 调用不同的 Celery 任务
    if req.test_type == "ui_batch":
        from tasks.ui_batch_run_task import ui_batch_run_task
        task = ui_batch_run_task.delay(test_run.id, req.browser, req.viewport_width, req.viewport_height)
    else:
        from tasks.batch_run_task import batch_run_task
        task = batch_run_task.delay(test_run.id)

    return _build_run_info(test_run, db)


@router.post("/batch-delete")
async def batch_delete_runs(
    req: BatchDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:execute")),
):
    """批量删除任务"""
    if not req.run_ids:
        raise HTTPException(status_code=400, detail="请选择要删除的任务")

    # 查询所有要删除的任务
    runs = db.query(TestRun).filter(TestRun.id.in_(req.run_ids)).all()
    if len(runs) != len(req.run_ids):
        found_ids = {r.id for r in runs}
        missing = [rid for rid in req.run_ids if rid not in found_ids]
        raise HTTPException(status_code=404, detail=f"任务不存在: {missing}")

    # 过滤掉运行中的任务
    running = [r for r in runs if r.status == TestRunStatus.RUNNING]
    if running:
        raise HTTPException(status_code=400, detail=f"无法删除运行中的任务: {[r.id for r in running]}")

    # 删除关联的详情记录
    db.query(TestRunDetail).filter(TestRunDetail.test_run_id.in_(req.run_ids)).delete()
    # 删除任务
    db.query(TestRun).filter(TestRun.id.in_(req.run_ids)).delete()
    db.commit()

    return {"message": f"成功删除 {len(req.run_ids)} 条记录", "deleted": len(req.run_ids)}


@router.get("", response_model=dict)
async def list_batch_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    status: str = Query(None),
    config_mode: str = Query(None),
    test_type: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询任务列表"""
    if test_type:
        query = db.query(TestRun).filter(TestRun.test_type == test_type)
    else:
        query = db.query(TestRun)  # 返回所有类型

    # 状态筛选
    if status:
        query = query.filter(TestRun.status == status)

    # 模式筛选
    if config_mode:
        query = query.filter(TestRun.config_mode == config_mode)

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
            test_type=run.test_type or "api_batch",
            config_mode=run.config_mode or "simple",
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
        node_id=detail.node_id,
        node_type=detail.node_type or "api_call",
        case_id=detail.case_id,
        case_name=detail.case_name or (case.name if case else None),
        case_number=detail.case_number or (case.case_number if case else None),
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


def _build_node_tree(run: TestRun, details: list[TestRunDetail], db: Session) -> list[NodeTreeItem]:
    """构建编排节点树"""
    # 通过 detail 的 node_id 反查 suite_id
    node_ids = [d.node_id for d in details if d.node_id]
    if not node_ids:
        return []

    sample_node = db.query(SceneNode).filter(SceneNode.id == node_ids[0]).first()
    if not sample_node:
        return []

    suite_id = sample_node.suite_id

    # 加载该套件的所有场景节点
    all_nodes = db.query(SceneNode).filter(
        SceneNode.suite_id == suite_id
    ).order_by(SceneNode.sort_order).all()
    node_map = {n.id: n for n in all_nodes}

    # 构建 node_id -> detail 映射
    detail_map = {d.node_id: d for d in details if d.node_id}

    # 找出主流程节点（非 branch 内的节点，按 sort_order 排序）
    # 主流程 = sort_order 排序的所有顶层节点
    branch_node_ids: set[int] = set()
    for n in all_nodes:
        if n.node_type == "condition":
            branch_node_ids.update(n.true_branch or [])
            branch_node_ids.update(n.false_branch or [])
    top_level_nodes = [n for n in all_nodes if n.id not in branch_node_ids]

    def build_tree_item(node_id: int) -> NodeTreeItem | None:
        node = node_map.get(node_id)
        if not node:
            return None
        detail = detail_map.get(node_id)
        status = detail.status if detail else "pending"
        detail_id = detail.id if detail else None

        item = NodeTreeItem(
            node_id=node.id,
            node_type=node.node_type,
            name=node.name,
            status=status,
            detail_id=detail_id,
        )

        # 条件节点：构建分支子树，推导活跃分支
        if node.node_type == "condition":
            true_ids = node.true_branch or []
            false_ids = node.false_branch or []

            item.true_branch = [t for nid in true_ids if (t := build_tree_item(nid))]
            item.false_branch = [t for nid in false_ids if (t := build_tree_item(nid))]

            # 优先从 request_snapshot.result 读取条件结果
            if detail and detail.request_snapshot and "result" in detail.request_snapshot:
                item.active_branch = "true" if detail.request_snapshot["result"] else "false"
            else:
                # 兜底：通过分支执行状态推导
                true_executed = any(
                    detail_map.get(nid) and detail_map[nid].status not in ("pending", "skipped")
                    for nid in true_ids
                )
                false_executed = any(
                    detail_map.get(nid) and detail_map[nid].status not in ("pending", "skipped")
                    for nid in false_ids
                )
                if true_executed:
                    item.active_branch = "true"
                elif false_executed:
                    item.active_branch = "false"

        return item

    tree = []
    for n in top_level_nodes:
        item = build_tree_item(n.id)
        if item:
            tree.append(item)

    return tree


def _build_run_info(run: TestRun, db: Session) -> BatchRunInfo:
    """构建任务详情响应"""
    # 查询明细
    details = db.query(TestRunDetail).filter(
        TestRunDetail.test_run_id == run.id
    ).order_by(TestRunDetail.execution_order).all()

    # 获取用例名称（过滤掉 None）
    case_ids = [d.case_id for d in details if d.case_id]
    cases = db.query(APITestCase).filter(APITestCase.id.in_(case_ids)).all() if case_ids else []
    case_map = {c.id: c for c in cases}

    # 获取环境名称
    environment_name = None
    if run.environment_id:
        env = db.query(Environment).filter(Environment.id == run.environment_id).first()
        if env:
            environment_name = env.name

    detail_summaries = []
    # 实时统计
    pass_count = 0
    fail_count = 0
    error_count = 0

    for d in details:
        case = case_map.get(d.case_id) if d.case_id else None
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
            node_id=d.node_id,
            node_type=d.node_type or "api_call",
            case_id=d.case_id,
            case_name=d.case_name or (case.name if case else None),
            case_number=d.case_number or (case.case_number if case else None),
            execution_order=d.execution_order,
            status=d.status or "pending",
            duration_ms=d.duration_ms,
            api_duration_ms=api_duration_ms,
            status_code=status_code,
            error_message=d.error_message,
        ))

    # 计算进度：编排模式 skipped 不计入分母
    total_count = len(details)
    config_mode = run.config_mode or "simple"
    if config_mode == "orchestration":
        executed = pass_count + fail_count + error_count
        progress = round(pass_count / executed * 100, 1) if executed > 0 else 0
    else:
        completed = pass_count + fail_count + error_count
        progress = round(completed / total_count * 100, 1) if total_count > 0 else 0

    # 编排模式构建节点树
    node_tree = []
    if config_mode == "orchestration":
        node_tree = _build_node_tree(run, details, db)

    return BatchRunInfo(
        id=run.id,
        project_id=run.project_id,
        name=run.name,
        status=run.status or "pending",
        config_mode=config_mode,
        case_ids=run.case_ids or [],
        environment_id=run.environment_id,
        environment_name=environment_name,
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
        node_tree=node_tree,
    )


@router.get("/{run_id}/report", response_model=BatchRunReport)
async def get_batch_run_report(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询任务测试报告"""
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="任务不存在")
    return _build_run_report(run, db)


def _percentile(sorted_values: list[int], p: float) -> int:
    """计算百分位数 (nearest-rank method)"""
    if not sorted_values:
        return 0
    k = max(0, min(int(len(sorted_values) * p / 100) - 1, len(sorted_values) - 1))
    return sorted_values[k]


def _categorize_failure(detail: TestRunDetail) -> str:
    """根据用例执行详情对失败原因分类"""
    if detail.status == 'error':
        msg = (detail.error_message or '').lower()
        if 'timeout' in msg or '超时' in msg:
            return '请求超时'
        if 'connection' in msg or '连接' in msg:
            return '连接失败'
        return '执行异常'

    # status == 'fail' 表示断言失败
    if detail.assertions:
        failed_assertions = [a for a in detail.assertions if not a.get('passed', True)]
        if failed_assertions:
            types = set(a.get('assertion_type', 'unknown') for a in failed_assertions)
            type_names = {
                'status_code': '状态码', 'jsonpath': 'JSONPath',
                'response_time': '响应时间', 'header': '响应头',
                'body_contains': 'Body包含',
            }
            label = '/'.join(type_names.get(t, t) for t in types)
            return f'断言失败({label})'
    return '断言失败'


def _build_run_report(run: TestRun, db: Session) -> BatchRunReport:
    """构建测试报告"""
    # 1. 查询所有明细
    details = db.query(TestRunDetail).filter(
        TestRunDetail.test_run_id == run.id
    ).all()

    # 2. 加载用例名称映射
    case_ids = [d.case_id for d in details if d.case_id]
    cases = db.query(APITestCase).filter(APITestCase.id.in_(case_ids)).all()
    case_map = {c.id: c for c in cases}

    # 3. 统计状态
    pass_count = sum(1 for d in details if d.status == 'pass')
    fail_count = sum(1 for d in details if d.status == 'fail')
    error_count = sum(1 for d in details if d.status == 'error')
    skipped_count = sum(1 for d in details if d.status == 'skipped')
    total = len(details)
    pass_rate = round(pass_count / total * 100, 1) if total > 0 else 0.0

    # 4. 加载创建者名称
    creator_name = None
    if run.creator_id:
        user = db.query(User).filter(User.id == run.creator_id).first()
        if user:
            creator_name = user.username

    # 5. 构建摘要
    summary = TestSummary(
        total_count=total,
        pass_count=pass_count,
        fail_count=fail_count,
        error_count=error_count,
        skipped_count=skipped_count,
        pass_rate=pass_rate,
        start_time=run.start_time,
        end_time=run.end_time,
        duration_ms=run.duration,
        creator_id=run.creator_id,
        creator_name=creator_name,
    )

    # 6. 收集响应时间用于性能统计
    response_times = []  # [(case_id, elapsed_ms, detail)]
    for d in details:
        if d.response_info and d.response_info.get('elapsed_ms') is not None:
            response_times.append((d.case_id, d.response_info['elapsed_ms'], d))

    sorted_times = sorted(response_times, key=lambda x: x[1])
    time_values = [t[1] for t in sorted_times]

    # 构建 Top5 列表
    def _make_api_stat(case_id, ms, detail=None):
        case = case_map.get(case_id) if case_id else None
        return APICallStat(
            case_id=case_id,
            case_name=(detail.case_name if detail and detail.case_name else (case.name if case else None)),
            case_number=(detail.case_number if detail and detail.case_number else (case.case_number if case else None)),
            api_duration_ms=ms,
        )

    slowest_top5 = [_make_api_stat(cid, ms, d) for cid, ms, d in sorted_times[-5:][::-1]]
    fastest_top5 = [_make_api_stat(cid, ms, d) for cid, ms, d in sorted_times[:5]]

    performance = PerformanceStats(
        avg_response_ms=round(sum(time_values) / len(time_values), 1) if time_values else 0,
        min_response_ms=time_values[0] if time_values else 0,
        max_response_ms=time_values[-1] if time_values else 0,
        p50_response_ms=_percentile(time_values, 50),
        p90_response_ms=_percentile(time_values, 90),
        p95_response_ms=_percentile(time_values, 95),
        total_requests=len(time_values),
        slowest_top5=slowest_top5,
        fastest_top5=fastest_top5,
    )

    # 7. 失败分析
    failed_details = [d for d in details if d.status in ('fail', 'error')]
    # 分类失败原因
    categories_map = {}  # category_name -> list of dict
    for d in failed_details:
        category = _categorize_failure(d)
        if category not in categories_map:
            categories_map[category] = []
        case = case_map.get(d.case_id) if d.case_id else None
        # 构建断言详情
        assertion_details = []
        if d.assertions:
            for a in d.assertions:
                if not a.get('passed', True):
                    assertion_details.append({
                        "assertion_type": a.get('assertion_type', ''),
                        "field": a.get('field', ''),
                        "operator": a.get('operator', ''),
                        "expected": a.get('expected', ''),
                        "actual": a.get('actual', ''),
                    })
        categories_map[category].append({
            "detail_id": d.id,
            "case_id": d.case_id,
            "case_name": d.case_name or (case.name if case else None),
            "error_message": d.error_message or "",
            "assertions": assertion_details,
        })

    total_fail = len(failed_details)
    failure_categories = []
    for cat_name, cat_cases in categories_map.items():
        failure_categories.append(FailureCategory(
            category=cat_name,
            count=len(cat_cases),
            percentage=round(len(cat_cases) / total_fail * 100, 1) if total_fail > 0 else 0,
            cases=cat_cases,
        ))
    # 按数量降序排序
    failure_categories.sort(key=lambda x: x.count, reverse=True)

    failure_analysis = FailureAnalysis(
        total_fail_count=total_fail,
        categories=failure_categories,
    )

    return BatchRunReport(
        summary=summary,
        performance=performance,
        failure_analysis=failure_analysis,
    )

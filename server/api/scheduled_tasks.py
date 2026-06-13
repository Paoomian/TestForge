"""定时任务 API"""
from datetime import datetime, timedelta, timezone
from croniter import croniter
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from core.deps import get_current_user
from models import ScheduledTask, TestSuite, UITestSuite, Environment, User
from schemas.scheduled_task import ScheduledTaskCreate, ScheduledTaskUpdate, ScheduledTaskOut

router = APIRouter()


def calc_next_run(cron_expr: str, base_time: datetime = None) -> datetime:
    """根据 Cron 表达式计算下次执行时间"""
    if base_time is None:
        base_time = datetime.now(timezone.utc)
    cron = croniter(cron_expr, base_time)
    return cron.get_next(datetime)


def get_suite_info(db: Session, task_type: str, suite_id: int) -> dict:
    """获取套件名称和用例 ID"""
    if task_type == "ui_batch":
        suite = db.query(UITestSuite).filter(UITestSuite.id == suite_id).first()
    else:
        suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        return {"name": None, "case_ids": []}
    return {"name": suite.name, "case_ids": suite.case_ids or []}


@router.get("", response_model=dict)
def list_scheduled_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    enabled: bool = Query(None),
    task_type: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询定时任务列表"""
    query = db.query(ScheduledTask)
    if enabled is not None:
        query = query.filter(ScheduledTask.enabled == enabled)
    if task_type:
        query = query.filter(ScheduledTask.task_type == task_type)

    total = query.count()
    tasks = query.order_by(ScheduledTask.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    items = []
    for t in tasks:
        suite_info = get_suite_info(db, t.task_type, t.suite_id)
        env_name = None
        if t.environment_id:
            env = db.query(Environment).filter(Environment.id == t.environment_id).first()
            env_name = env.name if env else None

        items.append(ScheduledTaskOut(
            id=t.id,
            name=t.name,
            task_type=t.task_type,
            suite_id=t.suite_id,
            suite_name=suite_info["name"],
            environment_id=t.environment_id,
            environment_name=env_name,
            concurrency=t.concurrency,
            failure_strategy=t.failure_strategy,
            variables=t.variables or {},
            cron_expression=t.cron_expression,
            enabled=t.enabled,
            last_run_at=t.last_run_at,
            next_run_at=t.next_run_at,
            creator_id=t.creator_id,
            created_at=t.created_at,
            updated_at=t.updated_at,
        ))

    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.post("", response_model=ScheduledTaskOut)
def create_scheduled_task(
    data: ScheduledTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建定时任务"""
    # 验证 Cron 表达式
    if not croniter.is_valid(data.cron_expression):
        raise HTTPException(status_code=400, detail="无效的 Cron 表达式")

    # 验证套件存在
    if data.task_type == "ui_batch":
        suite = db.query(UITestSuite).filter(UITestSuite.id == data.suite_id).first()
    else:
        suite = db.query(TestSuite).filter(TestSuite.id == data.suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="测试套件不存在")

    next_run = calc_next_run(data.cron_expression)

    task = ScheduledTask(
        name=data.name,
        task_type=data.task_type,
        suite_id=data.suite_id,
        environment_id=data.environment_id,
        concurrency=data.concurrency,
        failure_strategy=data.failure_strategy,
        variables=data.variables,
        cron_expression=data.cron_expression,
        enabled=data.enabled,
        next_run_at=next_run,
        creator_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    return ScheduledTaskOut(
        id=task.id,
        name=task.name,
        task_type=task.task_type,
        suite_id=task.suite_id,
        suite_name=suite.name,
        environment_id=task.environment_id,
        concurrency=task.concurrency,
        failure_strategy=task.failure_strategy,
        variables=task.variables or {},
        cron_expression=task.cron_expression,
        enabled=task.enabled,
        next_run_at=task.next_run_at,
        creator_id=task.creator_id,
        created_at=task.created_at,
    )


@router.put("/{task_id}", response_model=ScheduledTaskOut)
def update_scheduled_task(
    task_id: int,
    data: ScheduledTaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新定时任务"""
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="定时任务不存在")

    update_data = data.dict(exclude_unset=True)

    # 验证 Cron 表达式
    if "cron_expression" in update_data:
        if not croniter.is_valid(update_data["cron_expression"]):
            raise HTTPException(status_code=400, detail="无效的 Cron 表达式")

    for key, value in update_data.items():
        setattr(task, key, value)

    # 重新计算下次执行时间
    task.next_run_at = calc_next_run(task.cron_expression)

    db.commit()
    db.refresh(task)

    suite_info = get_suite_info(db, task.task_type, task.suite_id)
    return ScheduledTaskOut(
        id=task.id,
        name=task.name,
        task_type=task.task_type,
        suite_id=task.suite_id,
        suite_name=suite_info["name"],
        environment_id=task.environment_id,
        concurrency=task.concurrency,
        failure_strategy=task.failure_strategy,
        variables=task.variables or {},
        cron_expression=task.cron_expression,
        enabled=task.enabled,
        last_run_at=task.last_run_at,
        next_run_at=task.next_run_at,
        creator_id=task.creator_id,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.delete("/{task_id}")
def delete_scheduled_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除定时任务"""
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="定时任务不存在")
    db.delete(task)
    db.commit()
    return {"message": "删除成功"}


@router.post("/{task_id}/toggle")
def toggle_scheduled_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """启用/禁用定时任务"""
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="定时任务不存在")

    task.enabled = not task.enabled
    if task.enabled:
        task.next_run_at = calc_next_run(task.cron_expression)
    else:
        task.next_run_at = None

    db.commit()
    return {"message": "操作成功", "enabled": task.enabled}


@router.post("/{task_id}/run-now")
def run_scheduled_task_now(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """立即执行一次定时任务"""
    from tasks.scheduler_task import execute_scheduled_task

    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="定时任务不存在")

    # 异步执行
    execute_scheduled_task.delay(task.id)
    return {"message": "已提交执行"}

"""定时调度器任务 —— Celery Beat 每分钟触发"""
import logging
from datetime import datetime
from celery_app import celery_app
from database import SessionLocal
from models import (
    ScheduledTask, TestRun, TestRunDetail, TestRunStatus, TestRunDetailStatus,
    TestSuite, UITestSuite, UICase, APITestCase, SceneNode,
)

logger = logging.getLogger(__name__)


def calc_next_run(cron_expr: str, base_time: datetime) -> datetime:
    """计算下次执行时间"""
    from croniter import croniter
    cron = croniter(cron_expr, base_time)
    return cron.get_next(datetime)


@celery_app.task(bind=True, name="tasks.scheduler_tick")
def scheduler_tick(self):
    """每分钟轮询数据库，执行到期的定时任务"""
    db = SessionLocal()
    try:
        now = datetime.now()
        logger.info(f"[调度器] 当前时间: {now}")

        # 查询所有启用的任务
        all_enabled = db.query(ScheduledTask).filter(
            ScheduledTask.enabled == True,
        ).all()
        logger.info(f"[调度器] 启用的任务数: {len(all_enabled)}")
        for t in all_enabled:
            logger.info(f"[调度器] 任务#{t.id} {t.name}: next_run_at={t.next_run_at}, 到期={t.next_run_at <= now if t.next_run_at else 'N/A'}")

        tasks = db.query(ScheduledTask).filter(
            ScheduledTask.enabled == True,
            ScheduledTask.next_run_at != None,
            ScheduledTask.next_run_at <= now,
        ).all()

        logger.info(f"[调度器] 到期任务数: {len(tasks)}")
        for task in tasks:
            try:
                execute_scheduled_task.delay(task.id)
                # 更新 last_run_at，计算 next_run_at
                task.last_run_at = now
                task.next_run_at = calc_next_run(task.cron_expression, now)
                db.commit()
                logger.info(f"定时任务 [{task.name}] 已触发，下次执行: {task.next_run_at}")
            except Exception as e:
                logger.error(f"定时任务 [{task.name}] 触发失败: {e}")
                db.rollback()
    finally:
        db.close()


@celery_app.task(bind=True, name="tasks.execute_scheduled_task")
def execute_scheduled_task(self, scheduled_task_id: int):
    """执行定时任务：创建 TestRun 并分发给 Worker"""
    db = SessionLocal()
    try:
        task = db.query(ScheduledTask).filter(ScheduledTask.id == scheduled_task_id).first()
        if not task:
            logger.warning(f"定时任务 {scheduled_task_id} 不存在")
            return

        # 从套件获取信息
        if task.task_type == "ui_batch":
            suite = db.query(UITestSuite).filter(UITestSuite.id == task.suite_id).first()
        else:
            suite = db.query(TestSuite).filter(TestSuite.id == task.suite_id).first()

        if not suite:
            logger.error(f"定时任务 [{task.name}] 关联的套件 {task.suite_id} 不存在")
            return

        config_mode = suite.config_mode if hasattr(suite, 'config_mode') else "simple"
        run_name = f"[定时] {task.name}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # ========== 编排模式 ==========
        if config_mode == "orchestration" and task.task_type != "ui_batch":
            scene_nodes = db.query(SceneNode).filter(
                SceneNode.suite_id == task.suite_id
            ).order_by(SceneNode.sort_order).all()

            enabled_nodes = [n for n in scene_nodes if n.enabled]
            if not enabled_nodes:
                logger.warning(f"定时任务 [{task.name}] 套件中无启用的编排节点，跳过")
                return

            api_call_nodes = [n for n in enabled_nodes if n.node_type == "api_call" and n.case_id]

            test_run = TestRun(
                project_id=suite.project_id,
                name=run_name,
                test_type="api_scene",
                config_mode="orchestration",
                case_ids=[],
                environment_id=task.environment_id or suite.environment_id,
                concurrency=task.concurrency,
                failure_strategy=task.failure_strategy,
                variables=task.variables or {},
                status=TestRunStatus.PENDING.value,
                total_count=len(enabled_nodes),
                creator_id=task.creator_id,
            )
            db.add(test_run)
            db.flush()

            # 为每个节点创建执行明细
            case_snapshot = {}
            if api_call_nodes:
                case_snapshot = {c.id: c for c in db.query(APITestCase).filter(
                    APITestCase.id.in_([n.case_id for n in api_call_nodes])
                ).all()}

            for order, node in enumerate(enabled_nodes, start=1):
                case = case_snapshot.get(node.case_id) if node.case_id else None
                detail = TestRunDetail(
                    test_run_id=test_run.id,
                    node_id=node.id,
                    node_type=node.node_type,
                    case_id=node.case_id if node.node_type == "api_call" else None,
                    case_name=case.name if case else node.name,
                    case_number=case.case_number if case else None,
                    execution_order=order,
                    status=TestRunDetailStatus.PENDING.value,
                )
                db.add(detail)

            db.commit()
            db.refresh(test_run)

            from tasks.scene_run_task import scene_run_task
            celery_result = scene_run_task.delay(test_run.id)

        # ========== UI 批量模式 ==========
        elif task.task_type == "ui_batch":
            case_ids = suite.case_ids or []
            if not case_ids:
                logger.warning(f"定时任务 [{task.name}] 套件中无用例，跳过")
                return

            test_run = TestRun(
                project_id=suite.project_id,
                name=run_name,
                test_type="ui_batch",
                config_mode="simple",
                case_ids=case_ids,
                environment_id=task.environment_id or suite.environment_id,
                concurrency=task.concurrency,
                failure_strategy=task.failure_strategy,
                variables=task.variables or {},
                status=TestRunStatus.PENDING.value,
                total_count=len(case_ids),
                creator_id=task.creator_id,
            )
            db.add(test_run)
            db.flush()

            case_snapshot = {c.id: c for c in db.query(UICase).filter(UICase.id.in_(case_ids)).all()}
            for order, case_id in enumerate(case_ids, start=1):
                case = case_snapshot.get(case_id)
                detail = TestRunDetail(
                    test_run_id=test_run.id,
                    case_id=None,
                    case_number=str(case_id),
                    case_name=case.name if case else None,
                    execution_order=order,
                    status=TestRunDetailStatus.PENDING.value,
                    node_type="ui_case",
                )
                db.add(detail)

            db.commit()
            db.refresh(test_run)

            from tasks.ui_batch_run_task import ui_batch_run_task
            celery_result = ui_batch_run_task.delay(test_run.id)

        # ========== 接口简单模式 ==========
        else:
            case_ids = suite.case_ids or []
            if not case_ids:
                logger.warning(f"定时任务 [{task.name}] 套件中无用例，跳过")
                return

            test_run = TestRun(
                project_id=suite.project_id,
                name=run_name,
                test_type="api_batch",
                config_mode="simple",
                case_ids=case_ids,
                environment_id=task.environment_id or suite.environment_id,
                concurrency=task.concurrency,
                failure_strategy=task.failure_strategy,
                variables=task.variables or {},
                status=TestRunStatus.PENDING.value,
                total_count=len(case_ids),
                creator_id=task.creator_id,
            )
            db.add(test_run)
            db.flush()

            case_snapshot = {c.id: c for c in db.query(APITestCase).filter(APITestCase.id.in_(case_ids)).all()}
            for order, case_id in enumerate(case_ids, start=1):
                case = case_snapshot.get(case_id)
                detail = TestRunDetail(
                    test_run_id=test_run.id,
                    case_id=case_id,
                    case_name=case.name if case else None,
                    case_number=case.case_number if case else None,
                    execution_order=order,
                    status=TestRunDetailStatus.PENDING.value,
                )
                db.add(detail)

            db.commit()
            db.refresh(test_run)

            from tasks.batch_run_task import batch_run_task
            celery_result = batch_run_task.delay(test_run.id)

        test_run.celery_task_id = celery_result.id
        db.commit()

        logger.info(f"定时任务 [{task.name}] 已创建执行记录 #{test_run.id}")

    except Exception as e:
        logger.error(f"执行定时任务 {scheduled_task_id} 失败: {e}")
        db.rollback()
    finally:
        db.close()

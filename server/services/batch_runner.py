import json
import asyncio
import redis.asyncio as aioredis
from datetime import datetime
from sqlalchemy.orm import Session
from models import TestRun, TestRunDetail, TestRunStatus, TestRunDetailStatus, APITestCase
from services.api_test_runner.runner import TestRunner
from core.config import settings


def _now():
    """获取当前时间（无时区信息，避免 MySQL 时区问题）"""
    return datetime.now()


class BatchRunner:
    """批量执行服务"""

    def __init__(self, db: Session, test_run_id: int, celery_task_id: str):
        self.db = db
        self.test_run_id = test_run_id
        self.celery_task_id = celery_task_id
        self.redis: aioredis.Redis | None = None
        self.channel = f"batch_run:{test_run_id}"

    async def execute(self):
        """执行批量任务"""
        # 初始化 Redis 连接
        self.redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

        try:
            # 加载任务
            test_run = self.db.query(TestRun).filter(TestRun.id == self.test_run_id).first()
            if not test_run:
                return

            # 更新任务状态为运行中
            test_run.status = TestRunStatus.RUNNING.value
            test_run.celery_task_id = self.celery_task_id
            test_run.start_time = _now()
            self.db.commit()

            # 发送任务开始消息
            await self._publish({
                "type": "task_start",
                "task_id": self.test_run_id,
                "total": test_run.total_count,
            })

            # 获取执行配置
            concurrency = test_run.concurrency or 1
            failure_strategy = test_run.failure_strategy or "continue"
            shared_variables = dict(test_run.variables or {})

            # 加载环境变量
            if test_run.environment_id:
                env_vars = self._load_env_vars(test_run.environment_id)
                shared_variables.update(env_vars)

            # 获取用例明细列表
            details = self.db.query(TestRunDetail).filter(
                TestRunDetail.test_run_id == self.test_run_id
            ).order_by(TestRunDetail.execution_order).all()

            # 分阶段执行
            cancelled = False
            for batch_start in range(0, len(details), concurrency):
                # 检查取消标志
                if await self._is_cancelled():
                    cancelled = True
                    break

                batch = details[batch_start:batch_start + concurrency]

                # 并发执行当前批次
                tasks = []
                for detail in batch:
                    # 为每个用例创建变量快照（只读副本）
                    variables_snapshot = dict(shared_variables)
                    tasks.append(self._run_single_case(detail, variables_snapshot))

                # 等待当前批次完成
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # 合并提取的变量（串行，避免竞态）
                for detail, result in zip(batch, results):
                    if isinstance(result, Exception):
                        continue
                    if detail.status == TestRunDetailStatus.PASS.value and detail.extracted_vars:
                        shared_variables.update(detail.extracted_vars)

                    # 失败策略：如果设置了 stop，遇到失败则停止
                    if failure_strategy == "stop" and detail.status in (
                        TestRunDetailStatus.FAIL.value, TestRunDetailStatus.ERROR.value
                    ):
                        # 将剩余用例标记为 skipped
                        remaining_details = details[batch_start + concurrency:]
                        for d in remaining_details:
                            d.status = TestRunDetailStatus.SKIPPED.value
                        self.db.commit()
                        cancelled = True
                        break

                if cancelled:
                    break

            # 更新任务状态
            test_run = self.db.query(TestRun).filter(TestRun.id == self.test_run_id).first()
            if cancelled and await self._is_cancelled():
                test_run.status = TestRunStatus.CANCELLED.value
            elif cancelled:
                test_run.status = TestRunStatus.DONE.value
            else:
                test_run.status = TestRunStatus.DONE.value

            test_run.end_time = _now()
            if test_run.start_time:
                delta = test_run.end_time - test_run.start_time
                test_run.duration = int(delta.total_seconds() * 1000)

            # 重新统计
            self._update_counts(test_run)
            self.db.commit()

            # 发送任务完成消息
            await self._publish({
                "type": "task_finish",
                "task_id": self.test_run_id,
                "pass_count": test_run.pass_count,
                "fail_count": test_run.fail_count,
                "error_count": test_run.error_count,
            })

        except Exception as e:
            # 任务异常
            test_run = self.db.query(TestRun).filter(TestRun.id == self.test_run_id).first()
            if test_run:
                test_run.status = TestRunStatus.ERROR.value
                test_run.end_time = _now()
                self.db.commit()

            await self._publish({
                "type": "task_finish",
                "task_id": self.test_run_id,
                "pass_count": 0,
                "fail_count": 0,
                "error_count": 0,
            })
        finally:
            if self.redis:
                await self.redis.close()

    async def _run_single_case(self, detail: TestRunDetail, variables: dict):
        """执行单个用例"""
        # 更新状态为运行中
        detail.status = TestRunDetailStatus.RUNNING.value
        detail.started_at = _now()
        self.db.commit()

        # 获取用例名称
        case = self.db.query(APITestCase).filter(APITestCase.id == detail.case_id).first()
        case_name = case.name if case else f"用例{detail.case_id}"

        # 发送用例开始消息
        await self._publish({
            "type": "case_start",
            "detail_id": detail.id,
            "case_name": case_name,
            "order": detail.execution_order,
        })

        # 复用 TestRunner 执行
        runner = TestRunner(self.db)
        result = await runner.run_case(
            case_id=detail.case_id,
            environment_id=None,  # 环境变量已合并到 variables
            temp_variables=variables,
        )

        # 保存执行结果
        detail.status = result.status
        detail.request_snapshot = result.request_snapshot
        detail.response_info = result.response_info
        detail.assertions = [a.model_dump() for a in result.assertions]
        detail.extracted_vars = result.extracted_variables
        detail.script_output = result.script_output
        detail.error_message = result.error_message
        detail.duration_ms = result.duration_ms
        detail.finished_at = _now()
        self.db.commit()

        # 发送用例完成消息
        await self._publish({
            "type": "case_finish",
            "detail_id": detail.id,
            "case_name": case_name,
            "order": detail.execution_order,
            "status": detail.status.value,
            "duration_ms": detail.duration_ms,
        })

        return result

    def _load_env_vars(self, environment_id: int) -> dict:
        """加载环境变量"""
        from models import Environment
        env = self.db.query(Environment).filter(Environment.id == environment_id).first()
        if not env:
            return {}
        variables = dict(env.variables or {})
        if env.base_url:
            variables["base_url"] = env.base_url.rstrip("/")
        return variables

    def _update_counts(self, test_run: TestRun):
        """更新任务统计"""
        details = self.db.query(TestRunDetail).filter(
            TestRunDetail.test_run_id == self.test_run_id
        ).all()
        test_run.total_count = len(details)
        test_run.pass_count = sum(1 for d in details if d.status == TestRunDetailStatus.PASS.value)
        test_run.fail_count = sum(1 for d in details if d.status == TestRunDetailStatus.FAIL.value)
        test_run.error_count = sum(1 for d in details if d.status == TestRunDetailStatus.ERROR.value)

    async def _publish(self, message: dict):
        """发布消息到 Redis Pub/Sub"""
        if self.redis:
            await self.redis.publish(self.channel, json.dumps(message, ensure_ascii=False))

    async def _is_cancelled(self) -> bool:
        """检查任务是否被取消"""
        test_run = self.db.query(TestRun).filter(TestRun.id == self.test_run_id).first()
        return test_run.cancelled if test_run else False

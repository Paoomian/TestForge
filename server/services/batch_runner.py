import json
import time
import asyncio
import logging
import httpx
import redis
import redis.asyncio as aioredis
from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from models import TestRun, TestRunDetail, TestRunStatus, TestRunDetailStatus, APITestCase
from schemas.test_run import RunResult
from services.api_test_runner.runner import TestRunner
from core.config import settings

logger = logging.getLogger(__name__)


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
        self.sync_redis: redis.Redis | None = None
        self.channel = f"batch_run:{test_run_id}"

    async def execute(self):
        """执行批量任务"""
        # 初始化 Redis 连接（异步用于主流程，同步用于线程池内的发布）
        self.redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        self.sync_redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

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
            logger.info(f"[BatchRun] 任务 {self.test_run_id} 开始执行, 共 {len(details)} 个用例, 并发数 {concurrency}")
            cancelled = False
            # 创建共享 HTTP 客户端，所有并发任务复用同一连接池
            shared_client = httpx.AsyncClient(timeout=30, follow_redirects=True)
            try:
                for batch_start in range(0, len(details), concurrency):
                    # 检查取消标志
                    if await self._is_cancelled():
                        cancelled = True
                        break

                    batch = details[batch_start:batch_start + concurrency]

                    # 并发执行 HTTP 请求，DB 更新在主 session 串行处理
                    batch_results = await self._run_batch(batch, shared_variables, shared_client)

                    # 处理结果
                    for detail, batch_result in zip(batch, batch_results):
                        if isinstance(batch_result, Exception):
                            logger.error(f"[BatchRun] 用例执行异常 detail_id={detail.id}: {batch_result}")
                            # 标记为 error
                            detail.status = TestRunDetailStatus.ERROR.value
                            detail.error_message = f"执行异常: {str(batch_result)}"
                            detail.finished_at = _now()
                            self.db.commit()
                            continue

                        result, extracted_vars = batch_result

                        # 更新详情状态（主 session）
                        detail.status = result.status
                        detail.request_snapshot = result.request_snapshot
                        detail.response_info = result.response_info
                        detail.assertions = [a.model_dump() for a in result.assertions]
                        detail.extracted_vars = extracted_vars
                        detail.script_output = result.script_output
                        detail.error_message = result.error_message
                        detail.duration_ms = result.duration_ms
                        detail.finished_at = _now()
                        self.db.commit()

                        # 合并变量
                        if result.status == "pass" and extracted_vars:
                            shared_variables.update(extracted_vars)

                        # 失败策略
                        if failure_strategy == "stop" and result.status in ("fail", "error"):
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
                logger.info(f"[BatchRun] 任务 {self.test_run_id} 统计: pass={test_run.pass_count}, fail={test_run.fail_count}, error={test_run.error_count}, total={test_run.total_count}")
                self.db.commit()

                # 发送任务完成消息
                await self._publish({
                    "type": "task_finish",
                    "task_id": self.test_run_id,
                    "pass_count": test_run.pass_count,
                    "fail_count": test_run.fail_count,
                    "error_count": test_run.error_count,
                })
            finally:
                await shared_client.aclose()

        except Exception as e:
            logger.error(f"[BatchRun] 任务异常: {e}", exc_info=True)
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
            if self.sync_redis:
                self.sync_redis.close()

    async def _run_batch(self, batch: list, variables: dict, shared_client: httpx.AsyncClient):
        """并发执行一批用例的 HTTP 请求，返回 [(result, vars), ...]"""
        # 1. 批量标记为 running（一次 commit，不阻塞 HTTP）
        now = _now()
        for detail in batch:
            detail.status = TestRunDetailStatus.RUNNING.value
            detail.started_at = now
        self.db.commit()

        # 2. 预加载用例信息和发布开始消息
        case_names = {}
        for detail in batch:
            case = self.db.query(APITestCase).filter(APITestCase.id == detail.case_id).first()
            case_names[detail.id] = case.name if case else f"用例{detail.case_id}"

            if self.sync_redis:
                self.sync_redis.publish(self.channel, json.dumps({
                    "type": "case_start",
                    "detail_id": detail.id,
                    "case_name": case_names[detail.id],
                    "order": detail.execution_order,
                }, ensure_ascii=False))

        # 3. 三阶段并发执行：DB加载(线程) -> HTTP请求(事件循环) -> 后置处理(线程)
        async def _execute_case(detail):
            db = SessionLocal()
            try:
                runner = TestRunner(db, shared_client=shared_client)
                start_time = time.monotonic()

                # 阶段1: DB 加载 + 请求构建（线程池，不阻塞事件循环）
                prepare_result = await asyncio.to_thread(
                    runner.prepare_case,
                    case_id=detail.case_id,
                    environment_id=None,
                    temp_variables=variables,
                )
                case, request_config, req_vars, request_snapshot, setup_output, err = prepare_result
                if err:
                    result = RunResult(status="error")
                    result.error_message = err
                    result.duration_ms = int((time.monotonic() - start_time) * 1000)
                    merged_vars = {}
                    return result, merged_vars

                # 阶段2: HTTP 请求（事件循环上执行，所有用例真正并发）
                http_result = await runner.send_http_request(request_config, case.body_type)

                response_info = http_result["response_info"]
                http_error = http_result.get("error")

                # 阶段3: 后置处理（线程池，不阻塞事件循环）
                result = await asyncio.to_thread(
                    runner.post_process,
                    case=case,
                    variables=req_vars,
                    request_snapshot=request_snapshot,
                    response_info=response_info,
                    setup_output=setup_output,
                    http_error=http_error,
                )
                result.duration_ms = int((time.monotonic() - start_time) * 1000)

                merged_vars = {}
                merged_vars.update(result.extracted_variables)
                merged_vars.update(result.data_rule_variables)
                return result, merged_vars
            finally:
                db.close()

        tasks = [_execute_case(detail) for detail in batch]
        return await asyncio.gather(*tasks, return_exceptions=True)

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
        # 诊断日志
        status_summary = {}
        for d in details:
            status_summary[d.status] = status_summary.get(d.status, 0) + 1
        logger.info(f"[BatchRun] _update_counts 详情状态分布: {status_summary}")

    async def _publish(self, message: dict):
        """发布消息到 Redis Pub/Sub"""
        if self.redis:
            await self.redis.publish(self.channel, json.dumps(message, ensure_ascii=False))

    async def _is_cancelled(self) -> bool:
        """检查任务是否被取消"""
        test_run = self.db.query(TestRun).filter(TestRun.id == self.test_run_id).first()
        return test_run.cancelled if test_run else False

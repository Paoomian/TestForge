"""场景编排执行引擎"""
import json
import time
import asyncio
import logging
import operator
import httpx
import redis
import redis.asyncio as aioredis
from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from models import (
    TestRun, TestRunDetail, TestRunStatus, TestRunDetailStatus,
    SceneNode, APITestCase, Environment
)
from schemas.test_run import RunResult
from services.api_test_runner.runner import TestRunner
from core.config import settings

logger = logging.getLogger(__name__)


def _now():
    """获取当前时间（无时区信息，避免 MySQL 时区问题）"""
    return datetime.now()


# 条件运算符映射
OPERATORS = {
    "eq": operator.eq,
    "neq": operator.ne,
    "gt": operator.gt,
    "lt": operator.lt,
    "gte": operator.ge,
    "lte": operator.le,
}


class SceneRunner:
    """场景编排执行服务"""

    def __init__(self, db: Session, test_run_id: int, celery_task_id: str):
        self.db = db
        self.test_run_id = test_run_id
        self.celery_task_id = celery_task_id
        self.redis: aioredis.Redis | None = None
        self.sync_redis: redis.Redis | None = None
        self.channel = f"batch_run:{test_run_id}"

    async def execute(self):
        """执行场景编排任务"""
        self.redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        self.sync_redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

        try:
            test_run = self.db.query(TestRun).filter(TestRun.id == self.test_run_id).first()
            if not test_run:
                return

            # 更新状态为运行中
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

            # 加载场景节点（按 sort_order）
            scene_nodes = self.db.query(SceneNode).filter(
                SceneNode.suite_id == test_run.suite_id if hasattr(test_run, 'suite_id') else False
            ).order_by(SceneNode.sort_order).all()

            # 如果没有 suite_id 关联，从 TestRunDetail 的 node_id 加载
            if not scene_nodes:
                details = self.db.query(TestRunDetail).filter(
                    TestRunDetail.test_run_id == self.test_run_id
                ).order_by(TestRunDetail.execution_order).all()

                node_ids = [d.node_id for d in details if d.node_id]
                if node_ids:
                    scene_nodes = self.db.query(SceneNode).filter(
                        SceneNode.id.in_(node_ids)
                    ).order_by(SceneNode.sort_order).all()

            # 构建节点索引
            node_map = {n.id: n for n in scene_nodes}
            node_list = list(scene_nodes)  # 有序列表

            # 加载变量
            shared_variables = dict(test_run.variables or {})
            if test_run.environment_id:
                env_vars = self._load_env_vars(test_run.environment_id)
                shared_variables.update(env_vars)

            # 获取详情记录（按 execution_order）
            details = self.db.query(TestRunDetail).filter(
                TestRunDetail.test_run_id == self.test_run_id
            ).order_by(TestRunDetail.execution_order).all()

            detail_map = {d.node_id: d for d in details if d.node_id}

            # 共享 HTTP 客户端
            shared_client = httpx.AsyncClient(timeout=30, follow_redirects=True)

            try:
                # 按节点顺序执行
                i = 0
                cancelled = False
                while i < len(node_list):
                    # 检查取消
                    if await self._is_cancelled():
                        cancelled = True
                        break

                    node = node_list[i]
                    detail = detail_map.get(node.id)

                    if not node.enabled:
                        # 跳过禁用节点
                        if detail:
                            detail.status = TestRunDetailStatus.SKIPPED.value
                            detail.finished_at = _now()
                            self.db.commit()
                        i += 1
                        continue

                    if not detail:
                        i += 1
                        continue

                    # 根据节点类型执行
                    next_node_id = None

                    if node.node_type == "api_call":
                        next_node_id = await self._execute_api_call(
                            node, detail, shared_variables, shared_client
                        )
                    elif node.node_type == "condition":
                        next_node_id = await self._execute_condition(
                            node, detail, shared_variables
                        )
                    elif node.node_type == "wait":
                        next_node_id = await self._execute_wait(node, detail)
                    elif node.node_type == "data_assign":
                        next_node_id = await self._execute_data_assign(
                            node, detail, shared_variables
                        )
                    else:
                        # 未知节点类型，跳过
                        if detail:
                            detail.status = TestRunDetailStatus.SKIPPED.value
                            detail.finished_at = _now()
                            self.db.commit()
                        i += 1
                        continue

                    # 失败策略检查
                    if detail.status in (TestRunDetailStatus.FAIL.value, TestRunDetailStatus.ERROR.value):
                        test_run = self.db.query(TestRun).filter(TestRun.id == self.test_run_id).first()
                        if test_run.failure_strategy == "stop":
                            # 标记后续节点为 skipped
                            remaining = details[i + 1:] if i + 1 < len(details) else []
                            for d in remaining:
                                if d.status == TestRunDetailStatus.PENDING.value:
                                    d.status = TestRunDetailStatus.SKIPPED.value
                            self.db.commit()
                            cancelled = True
                            break

                    # 跳转逻辑
                    if next_node_id and next_node_id in node_map:
                        # 跳转到指定节点
                        target_node = node_map[next_node_id]
                        try:
                            i = node_list.index(target_node)
                        except ValueError:
                            i += 1
                    else:
                        i += 1

                # 更新任务状态
                test_run = self.db.query(TestRun).filter(TestRun.id == self.test_run_id).first()
                if cancelled and await self._is_cancelled():
                    test_run.status = TestRunStatus.CANCELLED.value
                else:
                    test_run.status = TestRunStatus.DONE.value

                test_run.end_time = _now()
                if test_run.start_time:
                    delta = test_run.end_time - test_run.start_time
                    test_run.duration = int(delta.total_seconds() * 1000)

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

            finally:
                await shared_client.aclose()

        except Exception as e:
            logger.error(f"[SceneRun] 任务异常: {e}", exc_info=True)
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

    async def _execute_api_call(
        self, node: SceneNode, detail: TestRunDetail,
        variables: dict, shared_client: httpx.AsyncClient
    ) -> int | None:
        """执行接口调用节点"""
        if not node.case_id:
            detail.status = TestRunDetailStatus.ERROR.value
            detail.error_message = "接口调用节点未关联用例"
            detail.finished_at = _now()
            self.db.commit()
            return None

        # 标记运行中
        detail.status = TestRunDetailStatus.RUNNING.value
        detail.started_at = _now()
        self.db.commit()

        # 发送开始消息
        if self.sync_redis:
            self.sync_redis.publish(self.channel, json.dumps({
                "type": "case_start",
                "detail_id": detail.id,
                "case_name": detail.case_name or node.name,
                "order": detail.execution_order,
            }, ensure_ascii=False))

        start_time = time.monotonic()

        try:
            # 使用 TestRunner 三阶段执行
            db = SessionLocal()
            try:
                runner = TestRunner(db, shared_client=shared_client)

                # 阶段1: 准备
                prepare_result = await asyncio.to_thread(
                    runner.prepare_case,
                    case_id=node.case_id,
                    environment_id=None,
                    temp_variables=variables,
                )
                case, request_config, req_vars, request_snapshot, setup_output, err = prepare_result

                if err:
                    detail.status = TestRunDetailStatus.ERROR.value
                    detail.error_message = err
                    detail.duration_ms = int((time.monotonic() - start_time) * 1000)
                    detail.finished_at = _now()
                    self.db.commit()
                    return None

                # 阶段2: HTTP 请求
                http_result = await runner.send_http_request(request_config, case.body_type)
                response_info = http_result["response_info"]
                http_error = http_result.get("error")

                # 阶段3: 后置处理
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

                # 更新详情
                detail.status = result.status
                detail.request_snapshot = result.request_snapshot
                detail.response_info = result.response_info
                detail.assertions = [a.model_dump() for a in result.assertions]
                detail.extracted_vars = {
                    **result.extracted_variables,
                    **result.data_rule_variables,
                }
                detail.script_output = result.script_output
                detail.error_message = result.error_message
                detail.duration_ms = result.duration_ms
                detail.finished_at = _now()
                self.db.commit()

                # 合并提取的变量到共享变量
                if result.extracted_variables:
                    variables.update(result.extracted_variables)
                if result.data_rule_variables:
                    variables.update(result.data_rule_variables)

                return None

            finally:
                db.close()

        except Exception as e:
            logger.error(f"[SceneRun] API调用异常: {e}", exc_info=True)
            detail.status = TestRunDetailStatus.ERROR.value
            detail.error_message = str(e)
            detail.duration_ms = int((time.monotonic() - start_time) * 1000)
            detail.finished_at = _now()
            self.db.commit()
            return None

    async def _execute_condition(
        self, node: SceneNode, detail: TestRunDetail, variables: dict
    ) -> int | None:
        """执行条件判断节点，返回下一个节点 ID"""
        detail.status = TestRunDetailStatus.RUNNING.value
        detail.started_at = _now()
        self.db.commit()

        start_time = time.monotonic()

        try:
            var_name = node.condition_variable
            op = node.condition_operator or "eq"
            compare_value = node.condition_value

            # 获取变量值
            actual_value = variables.get(var_name)

            # 评估条件
            result = self._evaluate_condition(actual_value, op, compare_value)

            # 记录结果到 detail
            detail.request_snapshot = {
                "node_type": "condition",
                "variable": var_name,
                "operator": op,
                "expected": compare_value,
                "actual": actual_value,
                "result": result,
            }
            detail.status = TestRunDetailStatus.PASS.value
            detail.duration_ms = int((time.monotonic() - start_time) * 1000)
            detail.finished_at = _now()
            self.db.commit()

            # 发送消息
            if self.sync_redis:
                self.sync_redis.publish(self.channel, json.dumps({
                    "type": "case_finish",
                    "detail_id": detail.id,
                    "status": "pass",
                    "duration_ms": detail.duration_ms,
                }, ensure_ascii=False))

            # 返回跳转目标
            if result:
                branches = node.true_branch or []
                return branches[0] if branches else None
            else:
                branches = node.false_branch or []
                return branches[0] if branches else None

        except Exception as e:
            logger.error(f"[SceneRun] 条件评估异常: {e}", exc_info=True)
            detail.status = TestRunDetailStatus.ERROR.value
            detail.error_message = f"条件评估异常: {str(e)}"
            detail.duration_ms = int((time.monotonic() - start_time) * 1000)
            detail.finished_at = _now()
            self.db.commit()
            return None

    async def _execute_wait(self, node: SceneNode, detail: TestRunDetail) -> int | None:
        """执行等待节点"""
        detail.status = TestRunDetailStatus.WAITING.value
        detail.started_at = _now()
        self.db.commit()

        # 发送开始消息
        if self.sync_redis:
            self.sync_redis.publish(self.channel, json.dumps({
                "type": "case_start",
                "detail_id": detail.id,
                "case_name": f"等待 {node.wait_seconds}秒",
                "order": detail.execution_order,
            }, ensure_ascii=False))

        seconds = node.wait_seconds or 5
        await asyncio.sleep(seconds)

        detail.status = TestRunDetailStatus.PASS.value
        detail.request_snapshot = {
            "node_type": "wait",
            "wait_seconds": seconds,
        }
        detail.duration_ms = seconds * 1000
        detail.finished_at = _now()
        self.db.commit()

        # 发送完成消息
        if self.sync_redis:
            self.sync_redis.publish(self.channel, json.dumps({
                "type": "case_finish",
                "detail_id": detail.id,
                "status": "pass",
                "duration_ms": detail.duration_ms,
            }, ensure_ascii=False))

        return None

    async def _execute_data_assign(
        self, node: SceneNode, detail: TestRunDetail, variables: dict
    ) -> int | None:
        """执行数据赋值节点"""
        detail.status = TestRunDetailStatus.RUNNING.value
        detail.started_at = _now()
        self.db.commit()

        start_time = time.monotonic()

        try:
            var_name = node.assign_variable
            source = node.assign_source or "static"
            raw_value = node.assign_value or ""

            # 解析值
            if source == "expression":
                # 支持 {{variable}} 模板语法
                value = self._resolve_expression(raw_value, variables)
            else:
                value = raw_value

            # 设置变量
            if var_name:
                variables[var_name] = value

            # 记录结果
            detail.request_snapshot = {
                "node_type": "data_assign",
                "variable": var_name,
                "source": source,
                "value": value,
            }
            detail.extracted_vars = {var_name: value} if var_name else {}
            detail.status = TestRunDetailStatus.PASS.value
            detail.duration_ms = int((time.monotonic() - start_time) * 1000)
            detail.finished_at = _now()
            self.db.commit()

            # 发送完成消息
            if self.sync_redis:
                self.sync_redis.publish(self.channel, json.dumps({
                    "type": "case_finish",
                    "detail_id": detail.id,
                    "status": "pass",
                    "duration_ms": detail.duration_ms,
                }, ensure_ascii=False))

            return None

        except Exception as e:
            logger.error(f"[SceneRun] 数据赋值异常: {e}", exc_info=True)
            detail.status = TestRunDetailStatus.ERROR.value
            detail.error_message = f"数据赋值异常: {str(e)}"
            detail.duration_ms = int((time.monotonic() - start_time) * 1000)
            detail.finished_at = _now()
            self.db.commit()
            return None

    def _evaluate_condition(self, actual, op: str, expected) -> bool:
        """评估条件"""
        if op in ("empty",):
            return actual is None or actual == "" or actual == "null"
        if op in ("not_empty",):
            return actual is not None and actual != "" and actual != "null"

        # 类型转换
        try:
            if isinstance(expected, str) and expected.replace(".", "").replace("-", "").isdigit():
                expected = float(expected)
                if isinstance(actual, str) and actual.replace(".", "").replace("-", "").isdigit():
                    actual = float(actual)
        except (ValueError, TypeError):
            pass

        op_func = OPERATORS.get(op)
        if not op_func:
            if op == "contains":
                return str(expected) in str(actual) if actual else False
            if op == "not_contains":
                return str(expected) not in str(actual) if actual else True
            return False

        try:
            return op_func(actual, expected)
        except TypeError:
            return str(actual) == str(expected)

    def _resolve_expression(self, template: str, variables: dict) -> str:
        """解析 {{variable}} 模板表达式"""
        import re
        def replace_var(match):
            var_name = match.group(1).strip()
            return str(variables.get(var_name, match.group(0)))

        return re.sub(r'\{\{(.+?)\}\}', replace_var, template)

    def _load_env_vars(self, environment_id: int) -> dict:
        """加载环境变量"""
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

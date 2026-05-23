import time
from typing import Any
from sqlalchemy.orm import Session
from models import (
    APITestCase, Environment,
    TestCaseHeader, TestCaseQueryParam, TestCaseBodyForm, TestCaseBodyRaw,
    TestCaseAssertion, TestCaseAuth,
)
from schemas.test_run import RunResult, AssertionResult
from .variable_service import VariableService
from .script_service import ScriptService
from .http_service import HttpService
from .assertion_service import AssertionService
from .extract_service import ExtractService
from .data_rule_service import DataRuleService


class TestRunner:
    """测试用例执行器"""

    def __init__(self, db: Session, shared_client=None):
        self.db = db
        self.variable_service = VariableService()
        self.script_service = ScriptService()
        self.http_service = HttpService(shared_client=shared_client)
        self.assertion_service = AssertionService()
        self.extract_service = ExtractService()
        self.data_rule_service = DataRuleService()

    async def run_case(
        self,
        case_id: int,
        environment_id: int | None = None,
        temp_variables: dict[str, str] | None = None,
    ) -> RunResult:
        """执行单个用例"""
        start_time = time.monotonic()

        # 初始化结果
        result = RunResult(status="pass")
        variables: dict[str, str] = {}
        request_snapshot = None
        response_info = None

        try:
            # 1. 加载用例数据
            case = self._load_case(case_id)
            if not case:
                result.status = "error"
                result.error_message = f"用例不存在: {case_id}"
                return result

            # 2. 加载环境变量
            env_vars = {}
            if environment_id:
                env_vars = self._load_env_vars(environment_id)

            # 3. 合并变量
            variables = self.variable_service.merge_variables(
                env_vars=env_vars,
                temp_vars=temp_variables,
            )

            # 4. 变量替换 - 构建请求配置
            request_config = self._build_request_config(case, variables)

            # 5. 执行前置脚本
            if case.setup_script:
                script_result = self.script_service.execute(
                    case.setup_script,
                    {"variables": variables, "request": request_config}
                )
                result.script_output["setup"] = {
                    "success": script_result.success,
                    "output": script_result.output,
                    "error": script_result.error,
                }
                if script_result.variables:
                    variables.update(script_result.variables)

            # 6. 发送HTTP请求
            http_result = await self.http_service.send_request(
                method=request_config["method"],
                url=request_config["url"],
                headers=request_config["headers"],
                query_params=request_config["params"],
                body=request_config.get("body"),
                body_type=case.body_type,
                auth_config=request_config.get("auth"),
            )

            request_snapshot = http_result["request_snapshot"]
            response_info = http_result["response_info"]

            if http_result.get("error"):
                result.status = "error"
                result.error_message = http_result["error"]
                result.request_snapshot = request_snapshot
                result.duration_ms = int((time.monotonic() - start_time) * 1000)
                return result

            # 7. 执行后置脚本
            if case.teardown_script:
                script_result = self.script_service.execute(
                    case.teardown_script,
                    {"variables": variables, "request": request_snapshot, "response": response_info}
                )
                result.script_output["teardown"] = {
                    "success": script_result.success,
                    "output": script_result.output,
                    "error": script_result.error,
                }
                if script_result.variables:
                    variables.update(script_result.variables)

            # 8. 数据规则执行（含提取规则）
            data_rules = self._load_data_rules(case)
            if data_rules:
                rule_results = self.data_rule_service.execute_rules(data_rules, variables, response_info)
                result.data_rule_variables = rule_results
                variables.update(rule_results)

            # 9. 断言执行
            assertions = self._load_assertions(case)
            if assertions:
                assertion_results = self.assertion_service.execute_assertions(
                    assertions, response_info, variables
                )
                result.assertions = [
                    AssertionResult(
                        assertion_type=r.assertion_type,
                        field=r.field,
                        operator=r.operator,
                        expected=r.expected,
                        actual=r.actual,
                        passed=r.passed,
                        error=r.error,
                    )
                    for r in assertion_results
                ]

                # 判断最终状态
                if any(not r.passed for r in assertion_results):
                    result.status = "fail"

        except Exception as e:
            result.status = "error"
            result.error_message = f"执行异常: {str(e)}"

        # 填充请求和响应信息
        result.request_snapshot = request_snapshot
        result.response_info = response_info
        result.duration_ms = int((time.monotonic() - start_time) * 1000)

        return result

    def prepare_case(
        self,
        case_id: int,
        environment_id: int | None = None,
        temp_variables: dict[str, str] | None = None,
    ) -> tuple:
        """阶段1: 加载用例数据并构建请求配置（同步，供线程池调用）
        返回 (case, request_config, variables, request_snapshot, error_msg)
        """
        case = self._load_case(case_id)
        if not case:
            return None, None, None, None, None, f"用例不存在: {case_id}"

        env_vars = {}
        if environment_id:
            env_vars = self._load_env_vars(environment_id)

        variables = self.variable_service.merge_variables(
            env_vars=env_vars,
            temp_vars=temp_variables,
        )

        request_config = self._build_request_config(case, variables)

        # 构建请求快照（应用认证信息后脱敏，与 http_service 保持一致）
        snapshot_headers = dict(request_config["headers"])
        snapshot_params = dict(request_config["params"])
        auth_config = request_config.get("auth")
        if auth_config and auth_config.get("auth_type") != "none":
            self.http_service._apply_auth(auth_config, snapshot_headers, snapshot_params)

        request_snapshot = {
            "method": request_config["method"].upper(),
            "url": request_config["url"],
            "headers": self.variable_service.mask_sensitive(snapshot_headers),
            "params": snapshot_params,
            "body": request_config.get("body"),
            "body_type": case.body_type,
        }

        # 执行前置脚本
        setup_output = None
        if case.setup_script:
            script_result = self.script_service.execute(
                case.setup_script,
                {"variables": variables, "request": request_config}
            )
            setup_output = {
                "success": script_result.success,
                "output": script_result.output,
                "error": script_result.error,
            }
            if script_result.variables:
                variables.update(script_result.variables)

        return case, request_config, variables, request_snapshot, setup_output, None

    async def send_http_request(
        self,
        request_config: dict,
        body_type: str,
    ) -> dict:
        """阶段2: 发送HTTP请求（异步，在事件循环上执行，真正并发）"""
        return await self.http_service.send_request(
            method=request_config["method"],
            url=request_config["url"],
            headers=request_config["headers"],
            query_params=request_config["params"],
            body=request_config.get("body"),
            body_type=body_type,
            auth_config=request_config.get("auth"),
        )

    def post_process(
        self,
        case: APITestCase,
        variables: dict[str, str],
        request_snapshot: dict,
        response_info: dict,
        setup_output: dict | None,
        http_error: str | None,
    ) -> RunResult:
        """阶段3: 后置处理（同步，供线程池调用）- 脚本、变量提取、断言"""
        result = RunResult(status="pass")
        result.request_snapshot = request_snapshot

        if setup_output:
            result.script_output["setup"] = setup_output

        if http_error:
            result.status = "error"
            result.error_message = http_error
            result.response_info = response_info
            return result

        # 执行后置脚本
        if case.teardown_script:
            script_result = self.script_service.execute(
                case.teardown_script,
                {"variables": variables, "request": request_snapshot, "response": response_info}
            )
            result.script_output["teardown"] = {
                "success": script_result.success,
                "output": script_result.output,
                "error": script_result.error,
            }
            if script_result.variables:
                variables.update(script_result.variables)

        # 数据规则执行（含提取规则）
        data_rules = self._load_data_rules(case)
        if data_rules:
            rule_results = self.data_rule_service.execute_rules(data_rules, variables, response_info)
            result.data_rule_variables = rule_results
            variables.update(rule_results)

        # 断言执行
        assertions = self._load_assertions(case)
        if assertions:
            assertion_results = self.assertion_service.execute_assertions(
                assertions, response_info, variables
            )
            result.assertions = [
                AssertionResult(
                    assertion_type=r.assertion_type,
                    field=r.field,
                    operator=r.operator,
                    expected=r.expected,
                    actual=r.actual,
                    passed=r.passed,
                    error=r.error,
                )
                for r in assertion_results
            ]
            if any(not r.passed for r in assertion_results):
                result.status = "fail"

        result.response_info = response_info
        return result

    def _load_case(self, case_id: int) -> APITestCase | None:
        """加载用例"""
        from sqlalchemy.orm import joinedload
        return self.db.query(APITestCase).options(
            joinedload(APITestCase.headers),
            joinedload(APITestCase.query_params),
            joinedload(APITestCase.body_form),
            joinedload(APITestCase.body_raw),
            joinedload(APITestCase.assertions),
            joinedload(APITestCase.data_rules),
            joinedload(APITestCase.auth),
        ).filter(APITestCase.id == case_id).first()

    def _load_env_vars(self, environment_id: int) -> dict[str, str]:
        """加载环境变量"""
        env = self.db.query(Environment).filter(Environment.id == environment_id).first()
        if not env:
            return {}
        variables = dict(env.variables or {})
        # 如果环境有 base_url，自动注入
        if env.base_url:
            variables["base_url"] = env.base_url.rstrip("/")
        return variables

    def _build_request_config(self, case: APITestCase, variables: dict[str, str]) -> dict:
        """构建请求配置（变量替换后）"""
        # URL 处理 - 自动补全 base_url
        url = self.variable_service.resolve_variables(case.url, variables)
        if not url.startswith(("http://", "https://")):
            base_url = variables.get("base_url", "")
            if base_url:
                url = f"{base_url}/{url.lstrip('/')}"

        # Headers
        headers = {}
        for h in (case.headers or []):
            if h.enabled:
                headers[h.key] = self.variable_service.resolve_variables(h.value or "", variables)

        # Query params
        params = {}
        for p in (case.query_params or []):
            if p.enabled:
                params[p.key] = self.variable_service.resolve_variables(p.value or "", variables)

        # Body
        body = None
        if case.body_type == "raw-json" and case.body_raw:
            body = self.variable_service.resolve_variables(case.body_raw.content or "", variables)
            try:
                import json
                body = json.loads(body)
            except Exception:
                pass
        elif case.body_type in ("raw-xml", "raw-text") and case.body_raw:
            body = self.variable_service.resolve_variables(case.body_raw.content or "", variables)
        elif case.body_type in ("form-data", "x-www-form-urlencoded"):
            body = {}
            for f in (case.body_form or []):
                if f.enabled:
                    body[f.key] = self.variable_service.resolve_variables(f.value or "", variables)

        # Auth
        auth = None
        if case.auth and case.auth.auth_type != "none":
            auth = {
                "auth_type": case.auth.auth_type,
                "token": self.variable_service.resolve_variables(case.auth.token or "", variables),
                "username": self.variable_service.resolve_variables(case.auth.username or "", variables),
                "password": self.variable_service.resolve_variables(case.auth.password or "", variables),
                "api_key_name": case.auth.api_key_name,
                "api_key_value": self.variable_service.resolve_variables(case.auth.api_key_value or "", variables),
                "api_key_location": case.auth.api_key_location,
            }

        return {
            "method": case.method,
            "url": url,
            "headers": headers,
            "params": params,
            "body": body,
            "auth": auth,
        }

    def _load_assertions(self, case: APITestCase) -> list[dict]:
        """加载断言列表"""
        return [
            {
                "assertion_type": a.assertion_type,
                "operator": a.operator,
                "field": a.field,
                "expected": a.expected,
            }
            for a in (case.assertions or [])
        ]

    def _load_data_rules(self, case: APITestCase) -> list[dict]:
        """加载数据规则列表"""
        return [
            {
                "name": r.name,
                "rule_type": r.rule_type,
                "enabled": r.enabled,
                "description": r.description,
                "default_value": r.default_value,
                "sort_order": r.sort_order,
                "source": r.source,
                "expression": r.expression,
                "static_value": r.static_value,
                "generator": r.generator,
                "generator_params": r.generator_params,
                "source_variable": r.source_variable,
                "transform_type": r.transform_type,
                "transform_params": r.transform_params,
                "condition_variable": r.condition_variable,
                "condition_operator": r.condition_operator,
                "condition_value": r.condition_value,
                "true_value": r.true_value,
                "false_value": r.false_value,
            }
            for r in (case.data_rules or [])
        ]

import time
from typing import Any
from sqlalchemy.orm import Session
from models import (
    APITestCase, Environment,
    TestCaseHeader, TestCaseQueryParam, TestCaseBodyForm, TestCaseBodyRaw,
    TestCaseAssertion, TestCaseExtract, TestCaseAuth,
)
from schemas.test_run import RunResult, AssertionResult
from .variable_service import VariableService
from .script_service import ScriptService
from .http_service import HttpService
from .assertion_service import AssertionService
from .extract_service import ExtractService


class TestRunner:
    """测试用例执行器"""

    def __init__(self, db: Session):
        self.db = db
        self.variable_service = VariableService()
        self.script_service = ScriptService()
        self.http_service = HttpService()
        self.assertion_service = AssertionService()
        self.extract_service = ExtractService()

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

            # 8. 变量提取
            extracts = self._load_extracts(case)
            if extracts:
                extracted = self.extract_service.extract_variables(extracts, response_info)
                result.extracted_variables = extracted
                variables.update(extracted)

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

    def _load_case(self, case_id: int) -> APITestCase | None:
        """加载用例"""
        from sqlalchemy.orm import joinedload
        return self.db.query(APITestCase).options(
            joinedload(APITestCase.headers),
            joinedload(APITestCase.query_params),
            joinedload(APITestCase.body_form),
            joinedload(APITestCase.body_raw),
            joinedload(APITestCase.assertions),
            joinedload(APITestCase.extracts),
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

    def _load_extracts(self, case: APITestCase) -> list[dict]:
        """加载提取规则列表"""
        return [
            {
                "name": e.name,
                "source": e.source,
                "expression": e.expression,
                "default_value": e.default_value,
            }
            for e in (case.extracts or [])
        ]

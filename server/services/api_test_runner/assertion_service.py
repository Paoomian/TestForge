import re
import json
from typing import Any
from dataclasses import dataclass, field


@dataclass
class AssertionResult:
    """单条断言结果"""
    assertion_type: str = ""
    field: str | None = None
    operator: str = ""
    expected: str = ""
    actual: str | None = None
    passed: bool = False
    error: str | None = None


class AssertionService:
    """断言执行服务"""

    def execute_assertions(
        self,
        assertions: list[dict],
        response_info: dict[str, Any] | None,
        variables: dict[str, str],
    ) -> list[AssertionResult]:
        """逐条执行断言，互不影响"""
        results = []
        for assertion in assertions:
            result = self._execute_single(assertion, response_info)
            results.append(result)
        return results

    def _execute_single(self, assertion: dict, response_info: dict[str, Any] | None) -> AssertionResult:
        """执行单条断言"""
        result = AssertionResult(
            assertion_type=assertion.get("assertion_type", ""),
            field=assertion.get("field"),
            operator=assertion.get("operator", ""),
            expected=assertion.get("expected", ""),
        )

        if not response_info:
            result.error = "无响应信息"
            return result

        try:
            actual = self._get_actual_value(result.assertion_type, result.field, response_info)
            result.actual = str(actual) if actual is not None else None
            result.passed = self._compare(result.operator, actual, result.expected)
        except Exception as e:
            result.error = str(e)
            result.passed = False

        return result

    def _get_actual_value(self, assertion_type: str, field: str | None, response_info: dict) -> Any:
        """根据断言类型获取实际值"""
        if assertion_type == "status_code":
            return response_info.get("status_code")

        if assertion_type == "response_time":
            return response_info.get("elapsed_ms")

        if assertion_type == "header":
            if not field:
                raise ValueError("header 断言需要指定 field（header名称）")
            headers = response_info.get("headers", {})
            # header 名称不区分大小写
            for k, v in headers.items():
                if k.lower() == field.lower():
                    return v
            return None

        if assertion_type == "jsonpath":
            if not field:
                raise ValueError("jsonpath 断言需要指定 field（JSONPath表达式）")
            body = response_info.get("body", "")
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                raise ValueError("响应体不是有效的JSON")

            from jsonpath_ng import parse
            expressions = parse(field)
            matches = [match.value for match in expressions.find(data)]
            if not matches:
                return None
            return matches[0] if len(matches) == 1 else matches

        if assertion_type == "body_contains":
            body = response_info.get("body", "")
            return body

        raise ValueError(f"不支持的断言类型: {assertion_type}")

    def _compare(self, operator: str, actual: Any, expected: str) -> bool:
        """比较运算"""
        expected_str = str(expected)

        if operator == "equals":
            return str(actual) == expected_str

        if operator == "not_equals":
            return str(actual) != expected_str

        if operator == "contains":
            if actual is None:
                return False
            return expected_str in str(actual)

        if operator == "not_contains":
            if actual is None:
                return True
            return expected_str not in str(actual)

        if operator == "greater_than":
            return self._to_number(actual) > self._to_number(expected_str)

        if operator == "less_than":
            return self._to_number(actual) < self._to_number(expected_str)

        if operator == "exists":
            return actual is not None

        if operator == "not_exists":
            return actual is None

        if operator == "regex":
            if actual is None:
                return False
            return bool(re.search(expected_str, str(actual)))

        if operator == "is_empty":
            return actual is None or str(actual).strip() == ""

        if operator == "is_not_empty":
            return actual is not None and str(actual).strip() != ""

        raise ValueError(f"不支持的运算符: {operator}")

    def _to_number(self, value: Any) -> float:
        """转换为数字"""
        try:
            return float(value)
        except (TypeError, ValueError):
            raise ValueError(f"无法转换为数字: {value}")

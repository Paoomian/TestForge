import re
import json
import time
import uuid
import random
import string
from datetime import datetime
from typing import Any

from .extract_service import ExtractService
from .variable_service import VariableService


class DataRuleService:
    """数据规则执行引擎 - 可视化数据传递"""

    def __init__(self):
        self.extract_service = ExtractService()
        self.variable_service = VariableService()

    def execute_rules(
        self,
        rules: list[dict],
        variables: dict[str, str],
        response_info: dict[str, Any] | None,
    ) -> dict[str, str]:
        """执行所有数据规则，返回新设置/更新的变量

        规则按 sort_order 顺序执行，前面规则的输出可供后续规则引用。
        执行错误不中断流程，使用 default_value 兜底。
        """
        result = {}
        if not rules:
            return result

        for rule in rules:
            if not rule.get("enabled", True):
                continue

            name = rule.get("name", "")
            rule_type = rule.get("rule_type", "")
            default_value = rule.get("default_value", "")

            if not name or not rule_type:
                continue

            try:
                # 将当前已设置的变量合并到 variables 中，供后续规则引用
                merged_vars = {**variables, **result}
                value = self._execute_single(rule, merged_vars, response_info)
                if value is not None:
                    result[name] = str(value)
                elif default_value:
                    result[name] = default_value
            except Exception:
                if default_value:
                    result[name] = default_value

        return result

    def _execute_single(
        self,
        rule: dict,
        variables: dict[str, str],
        response_info: dict[str, Any] | None,
    ) -> str | None:
        """执行单条规则，按类型分发"""
        rule_type = rule["rule_type"]

        if rule_type == "extract":
            return self._execute_extract(rule, response_info)
        elif rule_type == "static":
            return self._execute_static(rule)
        elif rule_type == "generate":
            return self._execute_generate(rule)
        elif rule_type == "transform":
            return self._execute_transform(rule, variables)
        elif rule_type == "conditional":
            return self._execute_conditional(rule, variables)
        else:
            return None

    def _execute_extract(self, rule: dict, response_info: dict[str, Any] | None) -> str | None:
        """从响应中提取变量（复用 ExtractService 逻辑）"""
        if not response_info:
            return None
        source = rule.get("source", "")
        expression = rule.get("expression", "")
        if not source or not expression:
            return None
        return self.extract_service._extract(source, expression, response_info)

    def _execute_static(self, rule: dict) -> str | None:
        """设置静态值"""
        value = rule.get("static_value")
        if value is not None:
            return str(value)
        return None

    def _execute_generate(self, rule: dict) -> str | None:
        """生成测试数据"""
        generator = rule.get("generator", "")
        params = rule.get("generator_params") or {}

        if generator == "timestamp":
            return str(int(time.time()))
        elif generator == "uuid":
            return str(uuid.uuid4())
        elif generator == "random_int":
            min_val = int(params.get("min", 1))
            max_val = int(params.get("max", 999999))
            return str(random.randint(min_val, max_val))
        elif generator == "random_string":
            length = int(params.get("length", 16))
            charset = params.get("charset", string.ascii_letters + string.digits)
            return "".join(random.choices(charset, k=length))
        elif generator == "now":
            fmt = params.get("format", "")
            if fmt:
                return datetime.now().strftime(fmt)
            return datetime.now().isoformat()
        else:
            return None

    def _execute_transform(self, rule: dict, variables: dict[str, str]) -> str | None:
        """对已有变量做变换"""
        source_variable = rule.get("source_variable", "")
        if not source_variable:
            return None

        # 支持 {{var}} 格式或直接写变量名
        var_name = source_variable.strip("{}").strip() if source_variable.startswith("{{") else source_variable
        source_value = variables.get(var_name, "")
        if not source_value and var_name != source_variable:
            source_value = source_variable

        transform_type = rule.get("transform_type", "")
        params = rule.get("transform_params") or {}

        if transform_type == "substring":
            start = int(params.get("start", 0))
            end = params.get("end")
            if end is not None:
                return source_value[start:int(end)]
            return source_value[start:]
        elif transform_type == "concat":
            append_str = params.get("append", "")
            # 支持 {{var}} 引用
            append_str = self.variable_service.resolve_variables(append_str, variables)
            return source_value + append_str
        elif transform_type == "replace":
            old = params.get("old", "")
            new = params.get("new", "")
            return source_value.replace(old, new)
        elif transform_type == "upper":
            return source_value.upper()
        elif transform_type == "lower":
            return source_value.lower()
        elif transform_type == "trim":
            return source_value.strip()
        elif transform_type == "to_int":
            try:
                return str(int(float(source_value)))
            except (ValueError, TypeError):
                return source_value
        elif transform_type == "to_string":
            return str(source_value)
        elif transform_type == "format_date":
            input_format = params.get("input_format", "")
            output_format = params.get("output_format", "%Y-%m-%d %H:%M:%S")
            try:
                dt = datetime.strptime(source_value, input_format)
                return dt.strftime(output_format)
            except (ValueError, TypeError):
                return source_value
        else:
            return source_value

    def _execute_conditional(self, rule: dict, variables: dict[str, str]) -> str | None:
        """条件赋值"""
        condition_variable = rule.get("condition_variable", "")
        condition_operator = rule.get("condition_operator", "")
        condition_value = rule.get("condition_value", "")

        if not condition_variable or not condition_operator:
            return None

        # 获取条件变量的实际值
        var_name = condition_variable.strip("{}").strip() if condition_variable.startswith("{{") else condition_variable
        actual_value = variables.get(var_name, "")

        # 评估条件
        condition_met = self._evaluate_condition(actual_value, condition_operator, condition_value)

        # 设置对应的值
        if condition_met:
            result_value = rule.get("true_value", "")
        else:
            result_value = rule.get("false_value", "")

        if result_value:
            # 支持 {{var}} 引用
            return self.variable_service.resolve_variables(result_value, variables)
        return None

    def _evaluate_condition(self, actual: str, operator: str, expected: str) -> bool:
        """评估条件表达式"""
        if operator == "equals":
            return actual == expected
        elif operator == "not_equals":
            return actual != expected
        elif operator == "contains":
            return expected in actual
        elif operator == "is_empty":
            return not actual or actual.strip() == ""
        elif operator == "is_not_empty":
            return bool(actual) and actual.strip() != ""
        elif operator == "greater_than":
            try:
                return float(actual) > float(expected)
            except (ValueError, TypeError):
                return actual > expected
        elif operator == "less_than":
            try:
                return float(actual) < float(expected)
            except (ValueError, TypeError):
                return actual < expected
        else:
            return False

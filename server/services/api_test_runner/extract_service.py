import re
import json
from typing import Any


class ExtractService:
    """变量提取服务"""

    def extract_variables(
        self,
        extracts: list[dict],
        response_info: dict[str, Any] | None,
    ) -> dict[str, str]:
        """执行所有提取规则，返回提取到的变量"""
        result = {}
        if not extracts or not response_info:
            return result

        for extract in extracts:
            name = extract.get("name", "")
            source = extract.get("source", "")
            expression = extract.get("expression", "")
            default_value = extract.get("default_value", "")

            if not name or not source or not expression:
                continue

            try:
                value = self._extract(source, expression, response_info)
                if value is not None:
                    result[name] = str(value)
                elif default_value:
                    result[name] = default_value
            except Exception:
                if default_value:
                    result[name] = default_value

        return result

    def _extract(self, source: str, expression: str, response_info: dict) -> str | None:
        """根据来源类型提取值"""
        if source == "jsonpath":
            return self._extract_jsonpath(expression, response_info.get("body", ""))

        if source == "regex":
            return self._extract_regex(expression, response_info.get("body", ""))

        if source == "header":
            return self._extract_header(expression, response_info.get("headers", {}))

        return None

    def _extract_jsonpath(self, expression: str, body: str) -> str | None:
        """JSONPath 提取"""
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return None

        try:
            from jsonpath_ng import parse
            matches = [match.value for match in parse(expression).find(data)]
            if not matches:
                return None
            value = matches[0]
            return json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
        except Exception:
            return None

    def _extract_regex(self, expression: str, body: str) -> str | None:
        """正则提取"""
        try:
            match = re.search(expression, body)
            if match:
                # 如果有捕获组，返回第一个捕获组
                return match.group(1) if match.lastindex else match.group(0)
            return None
        except re.error:
            return None

    def _extract_header(self, header_name: str, headers: dict[str, str]) -> str | None:
        """响应头提取"""
        for k, v in headers.items():
            if k.lower() == header_name.lower():
                return v
        return None

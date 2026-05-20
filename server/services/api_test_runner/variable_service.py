import re
from typing import Any


class VariableService:
    """变量替换服务"""

    # 匹配 {{variable}} 占位符
    _pattern = re.compile(r"\{\{(\w+(?:\.\w+)*)\}\}")

    def resolve_variables(self, template: str, variables: dict[str, str]) -> str:
        """将 {{variable}} 替换为实际值"""
        if not template:
            return template

        def replacer(match: re.Match) -> str:
            key = match.group(1)
            value = variables.get(key, match.group(0))
            return str(value)

        return self._pattern.sub(replacer, template)

    def resolve_in_dict(self, data: dict[str, Any], variables: dict[str, str]) -> dict[str, Any]:
        """递归替换字典中的所有字符串值"""
        if not data:
            return data
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.resolve_variables(value, variables)
            elif isinstance(value, dict):
                result[key] = self.resolve_in_dict(value, variables)
            elif isinstance(value, list):
                result[key] = [
                    self.resolve_variables(item, variables) if isinstance(item, str)
                    else self.resolve_in_dict(item, variables) if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                result[key] = value
        return result

    def merge_variables(
        self,
        env_vars: dict[str, str] | None = None,
        global_vars: dict[str, str] | None = None,
        temp_vars: dict[str, str] | None = None,
    ) -> dict[str, str]:
        """合并变量，优先级：临时 > 环境 > 全局"""
        merged = {}
        if global_vars:
            merged.update(global_vars)
        if env_vars:
            merged.update(env_vars)
        if temp_vars:
            merged.update(temp_vars)
        return merged

    def mask_sensitive(self, data: dict[str, Any], sensitive_keys: list[str] | None = None) -> dict[str, Any]:
        """敏感字段脱敏"""
        if sensitive_keys is None:
            sensitive_keys = ["password", "secret", "api_key", "api_key_value"]

        result = {}
        for key, value in data.items():
            if isinstance(value, dict):
                result[key] = self.mask_sensitive(value, sensitive_keys)
            elif any(sk in key.lower() for sk in sensitive_keys):
                print(f"[DEBUG] 脱敏字段: key={key}, matched_keywords={[sk for sk in sensitive_keys if sk in key.lower()]}")
                result[key] = "****" if value else value
            else:
                result[key] = value
        return result

import json
from typing import Dict, Any, List, Optional
from models.api_test_case import APITestCase
from models.test_case_header import TestCaseHeader
from models.test_case_query_param import TestCaseQueryParam
from models.test_case_body import TestCaseBodyRaw
from models.test_case_assertion import TestCaseAssertion
from models.test_case_data_rule import TestCaseDataRule
from models.test_case_auth import TestCaseAuth


def convert_to_test_case(
    case_data: Dict[str, Any],
    project_id: int,
    generate_type: str,
    module: Optional[str] = None,
    creator_id: Optional[int] = None,
    case_number: Optional[str] = None
) -> APITestCase:
    """将 AI 生成的用例数据转换为测试用例模型

    Args:
        case_data: AI 生成的用例数据
        project_id: 项目 ID
        generate_type: 生成类型 (functional/api)
        module: 模块名称
        creator_id: 创建者 ID

    Returns:
        APITestCase 实例
    """
    converters = {
        "api": _convert_api_case,
        "functional": _convert_functional_case,
    }

    converter = converters.get(generate_type)
    if not converter:
        raise ValueError(f"不支持的生成类型: {generate_type}，支持: functional, api")

    # 接口测试用例需要传递 case_number
    if generate_type == "api":
        return converter(case_data, project_id, module, creator_id, case_number)
    return converter(case_data, project_id, module, creator_id)


def _convert_api_case(
    case_data: Dict[str, Any],
    project_id: int,
    module: Optional[str],
    creator_id: Optional[int],
    case_number: Optional[str] = None
) -> APITestCase:
    """转换接口测试用例

    支持两种格式：
    1. Excel模板格式：headers/query_params 是对象，断言用 type 字段
    2. 旧格式：headers/query_params 是数组，断言用 assertion_type 字段
    """
    # 使用用例自身的 module，如果没有则使用传入的 module
    case_module = case_data.get("module") or module

    # 转换 headers（支持对象格式和数组格式）
    headers = []
    headers_data = case_data.get("headers", {})
    if isinstance(headers_data, dict):
        # 对象格式：{"Content-Type": "application/json"}
        for key, value in headers_data.items():
            headers.append(TestCaseHeader(
                enabled=True,
                key=key,
                value=str(value),
                sort_order=len(headers)
            ))
    elif isinstance(headers_data, list):
        # 数组格式：[{"key": "xxx", "value": "xxx"}]
        for h in headers_data:
            headers.append(TestCaseHeader(
                enabled=True,
                key=h.get("key", ""),
                value=h.get("value", ""),
                sort_order=len(headers)
            ))

    # 转换 query_params（支持对象格式和数组格式）
    query_params = []
    params_data = case_data.get("query_params", {})
    if isinstance(params_data, dict):
        # 对象格式：{"page": "1", "size": "10"}
        for key, value in params_data.items():
            query_params.append(TestCaseQueryParam(
                enabled=True,
                key=key,
                value=str(value),
                sort_order=len(query_params)
            ))
    elif isinstance(params_data, list):
        # 数组格式：[{"key": "xxx", "value": "xxx"}]
        for p in params_data:
            query_params.append(TestCaseQueryParam(
                enabled=True,
                key=p.get("key", ""),
                value=p.get("value", ""),
                sort_order=len(query_params)
            ))

    # 转换 assertions（支持 type 和 assertion_type 两种字段名）
    assertions = []
    for a in case_data.get("assertions", []):
        assertions.append(TestCaseAssertion(
            assertion_type=a.get("type") or a.get("assertion_type", "status_code"),
            operator=a.get("operator", "equals"),
            field=a.get("field", ""),
            expected=str(a.get("expected", "")),
            description=a.get("description", ""),
            sort_order=len(assertions)
        ))

    # 处理 body
    body_type = case_data.get("body_type", "none")
    body_content = case_data.get("body_content")
    body_raw = None
    if body_type in ("raw-json", "raw-xml", "raw-text") and body_content:
        body_raw = {"content": body_content}

    # 处理数据规则（支持 data_extract 和 data_rules 两种字段名）
    data_rules = []
    extract_data = case_data.get("data_extract") or case_data.get("data_rules", [])
    for rule in extract_data:
        rule_type = rule.get("rule_type", "extract")
        rule_kwargs = {
            "name": rule.get("name", ""),
            "rule_type": rule_type,
            "enabled": True,
            "description": rule.get("description", ""),
            "sort_order": len(data_rules)
        }

        # 根据规则类型设置对应字段
        if rule_type == "extract":
            rule_kwargs["source"] = rule.get("source", "jsonpath")
            rule_kwargs["expression"] = rule.get("expression", "")
        elif rule_type == "static":
            rule_kwargs["static_value"] = rule.get("static_value", "")
        elif rule_type == "generate":
            rule_kwargs["generator"] = rule.get("generator", "timestamp")
            rule_kwargs["generator_params"] = rule.get("generator_params", {})
        elif rule_type == "transform":
            rule_kwargs["source_variable"] = rule.get("source_variable", "")
            rule_kwargs["transform_type"] = rule.get("transform_type", "")
            rule_kwargs["transform_params"] = rule.get("transform_params", {})
        elif rule_type == "conditional":
            rule_kwargs["condition_variable"] = rule.get("condition_variable", "")
            rule_kwargs["condition_operator"] = rule.get("condition_operator", "equals")
            rule_kwargs["condition_value"] = rule.get("condition_value", "")
            rule_kwargs["true_value"] = rule.get("true_value", "")
            rule_kwargs["false_value"] = rule.get("false_value", "")

        data_rules.append(TestCaseDataRule(**rule_kwargs))

    # 构建用例
    test_case = APITestCase(
        project_id=project_id,
        case_number=case_number,
        module=case_module,
        name=case_data.get("name", "未命名用例"),
        description=case_data.get("description", ""),
        preconditions=case_data.get("preconditions", ""),
        remark=case_data.get("remark", ""),
        method=case_data.get("method", "GET").upper(),
        url=case_data.get("url", ""),
        body_type=body_type,
        auth_type=case_data.get("auth_type", "none"),
        priority=case_data.get("priority", "P2"),
        status="active",
        creator_id=creator_id,
        setup_script=case_data.get("setup_script"),
        teardown_script=case_data.get("teardown_script"),
        headers=headers,
        query_params=query_params,
        assertions=assertions,
        data_rules=data_rules
    )

    # 设置 raw body
    if body_raw:
        test_case.body_raw = TestCaseBodyRaw(**body_raw)

    # 设置认证配置
    auth_type = case_data.get("auth_type", "none")
    if auth_type and auth_type != "none":
        auth_data = {
            "auth_type": auth_type,
            "token": case_data.get("token"),
            "username": case_data.get("username"),
            "password": case_data.get("password"),
            "api_key_name": case_data.get("api_key_name"),
            "api_key_value": case_data.get("api_key_value"),
            "api_key_location": case_data.get("api_key_location"),
        }
        test_case.auth = TestCaseAuth(**auth_data)

    return test_case


def _convert_functional_case(
    case_data: Dict[str, Any],
    project_id: int,
    module: Optional[str],
    creator_id: Optional[int]
) -> APITestCase:
    """转换功能测试用例"""
    # 构建描述
    preconditions = case_data.get("preconditions", "无")
    steps = case_data.get("steps", [])
    expected_result = case_data.get("expected_result", "")

    description_parts = [f"前置条件: {preconditions}", "", "测试步骤:"]
    for i, step in enumerate(steps, 1):
        description_parts.append(f"{i}. {step}")
    description_parts.extend(["", f"预期结果: {expected_result}"])

    return APITestCase(
        project_id=project_id,
        module=module,
        name=case_data.get("name", "未命名用例"),
        description="\n".join(description_parts),
        preconditions=preconditions,
        method="GET",  # 默认值，用户需要手动修改
        url="/",  # 默认值，用户需要手动修改
        priority=case_data.get("priority", "P2"),
        status="draft",
        creator_id=creator_id
    )

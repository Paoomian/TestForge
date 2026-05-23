from typing import Dict, Any, List, Optional
from models.api_test_case import APITestCase


def convert_to_test_case(
    case_data: Dict[str, Any],
    project_id: int,
    generate_type: str,
    module: Optional[str] = None,
    creator_id: Optional[int] = None
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

    return converter(case_data, project_id, module, creator_id)


def _convert_api_case(
    case_data: Dict[str, Any],
    project_id: int,
    module: Optional[str],
    creator_id: Optional[int]
) -> APITestCase:
    """转换接口测试用例"""
    # 转换 headers
    headers = []
    for h in case_data.get("headers", []):
        headers.append({
            "enabled": True,
            "key": h.get("key", ""),
            "value": h.get("value", ""),
            "sort_order": len(headers)
        })

    # 转换 query_params
    query_params = []
    for p in case_data.get("query_params", []):
        query_params.append({
            "enabled": True,
            "key": p.get("key", ""),
            "value": p.get("value", ""),
            "sort_order": len(query_params)
        })

    # 转换 assertions
    assertions = []
    for a in case_data.get("assertions", []):
        assertions.append({
            "assertion_type": a.get("assertion_type", "status_code"),
            "operator": a.get("operator", "equals"),
            "field": a.get("field", ""),
            "expected": a.get("expected", ""),
            "sort_order": len(assertions)
        })

    return APITestCase(
        project_id=project_id,
        module=module,
        name=case_data.get("name", "未命名用例"),
        description=case_data.get("description", ""),
        method=case_data.get("method", "GET"),
        url=case_data.get("url", ""),
        body_type=case_data.get("body_type", "none"),
        priority=case_data.get("priority", "P2"),
        status="draft",
        creator_id=creator_id,
        headers=headers,
        query_params=query_params,
        assertions=assertions
    )


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

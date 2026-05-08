TEMPLATES = [
    {
        "name": "用户登录",
        "description": "标准登录接口模板",
        "method": "POST",
        "url": "/api/v1/auth/login",
        "headers": [
            {"enabled": True, "key": "Content-Type", "value": "application/json", "description": ""}
        ],
        "body_type": "raw-json",
        "body_raw_content": '{\n  "username": "",\n  "password": ""\n}',
        "assertions": [
            {"assertion_type": "status_code", "operator": "equals", "field": "", "expected": "200", "description": "状态码为200"}
        ],
        "extracts": [
            {"name": "token", "source": "jsonpath", "expression": "$.access_token", "default_value": "", "description": "提取登录token"}
        ],
        "priority": "P1",
    },
    {
        "name": "列表查询",
        "description": "通用列表查询接口模板",
        "method": "GET",
        "url": "/api/v1/items",
        "headers": [],
        "query_params": [
            {"enabled": True, "key": "page", "value": "1", "description": "页码"},
            {"enabled": True, "key": "page_size", "value": "20", "description": "每页数量"},
        ],
        "body_type": "none",
        "assertions": [
            {"assertion_type": "status_code", "operator": "equals", "field": "", "expected": "200", "description": "状态码为200"},
            {"assertion_type": "jsonpath", "operator": "exists", "field": "$.data", "expected": "", "description": "返回数据存在"},
        ],
        "priority": "P2",
    },
    {
        "name": "创建资源",
        "description": "通用创建资源接口模板",
        "method": "POST",
        "url": "/api/v1/items",
        "headers": [
            {"enabled": True, "key": "Content-Type", "value": "application/json", "description": ""}
        ],
        "body_type": "raw-json",
        "body_raw_content": '{\n  "name": ""\n}',
        "assertions": [
            {"assertion_type": "status_code", "operator": "equals", "field": "", "expected": "201", "description": "状态码为201"},
        ],
        "extracts": [
            {"name": "new_id", "source": "jsonpath", "expression": "$.id", "default_value": "", "description": "提取新创建资源ID"}
        ],
        "priority": "P1",
    },
    {
        "name": "更新资源",
        "description": "通用PUT更新接口模板",
        "method": "PUT",
        "url": "/api/v1/items/${item_id}",
        "headers": [
            {"enabled": True, "key": "Content-Type", "value": "application/json", "description": ""}
        ],
        "body_type": "raw-json",
        "body_raw_content": '{\n  "name": ""\n}',
        "assertions": [
            {"assertion_type": "status_code", "operator": "equals", "field": "", "expected": "200", "description": "状态码为200"},
        ],
        "priority": "P2",
    },
    {
        "name": "删除资源",
        "description": "通用删除接口模板",
        "method": "DELETE",
        "url": "/api/v1/items/${item_id}",
        "assertions": [
            {"assertion_type": "status_code", "operator": "equals", "field": "", "expected": "200", "description": "状态码为200"},
        ],
        "priority": "P2",
    },
]


def get_templates() -> list:
    return TEMPLATES

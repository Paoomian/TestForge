from typing import List, Dict


# 功能测试自动附加的格式要求和示例
FUNCTIONAL_FORMAT_REQUIREMENTS = '''

=== 强制要求（不满足则输出无效） ===
1. 你的输出必须包含 combination 类型用例（≥8条），使用 Pairwise 成对测试方法，必须附带参数表和组合矩阵
2. 你的输出必须包含 backend_ui 类型用例（≥3条），步骤中必须写"打开浏览器开发者工具Network面板"，预期结果必须写明HTTP状态码
3. expected_results 必须是数组，与 steps 一一对应
4. 输出纯JSON数组，不要包含markdown代码块或其他文本

=== combination 用例格式（照此生成≥8条） ===

先输出参数表（从需求中提取4-6个关键参数）：
参数表：用户名类型(手机号/邮箱) × 密码(正确/错误) × 验证码(正确/错误) × 账户状态(正常/接近锁定/已锁定)

再输出Pairwise组合矩阵（每对取值至少出现一次）：
C1: 手机号+正确+正确+正常
C2: 手机号+错误+错误+接近锁定
C3: 手机号+正确+过期+已锁定
C4: 邮箱+正确+错误+正常
C5: 邮箱+错误+正确+接近锁定
C6: 邮箱+正确+正确+已锁定
C7: 手机号+错误+正确+正常
C8: 邮箱+错误+过期+已锁定

每条combination用例示例：
{
  "name": "组合C2-手机号+错误密码+错误验证码+接近锁定",
  "priority": "P1",
  "preconditions": "数据库存在手机号13800138000的用户，密码为Abc123；该用户连续登录失败次数为4（未锁定）；当前会话验证码为Xk9m",
  "steps": ["打开登录页面", "在用户名输入框输入13800138000", "在密码输入框输入WrongPwd", "在验证码输入框输入YYYY", "点击登录按钮"],
  "expected_results": ["登录页面正常显示", "用户名输入框显示13800138000", "密码输入框显示密文", "验证码输入框显示YYYY", "页面提示'验证码错误'，验证码图片刷新；数据库中该用户连续失败次数仍为4"],
  "test_type": "combination"
}

=== backend_ui 用例格式（照此生成≥3条） ===

{
  "name": "后端验证-锁定状态下直接调用登录API",
  "priority": "P1",
  "preconditions": "数据库存在手机号13800138000的用户，密码为Abc123；该用户连续失败5次，账户已锁定30分钟",
  "steps": ["打开浏览器开发者工具，切换到Network面板，清空已有请求记录", "在地址栏直接访问登录页面", "在用户名输入框输入13800138000", "在密码输入框输入Abc123（正确密码）", "在验证码输入框输入当前正确验证码", "点击登录按钮", "在Network面板中找到login请求，查看响应"],
  "expected_results": ["Network面板已清空，无残留请求", "登录页面正常加载", "用户名输入框显示13800138000", "密码输入框显示密文", "验证码输入框显示正确验证码", "页面提示'账户已锁定，请30分钟后再试'", "Network面板中POST /api/v1/auth/login请求的HTTP状态码为403，响应体包含message字段值为'账户已锁定'，响应体不包含密码明文或内部错误堆栈"],
  "test_type": "backend_ui"
}

=== 单条用例JSON结构 ===
{
  "name": "用例名称",
  "priority": "P0/P1/P2",
  "preconditions": "具体可验证的前置条件",
  "steps": ["步骤1", "步骤2"],
  "expected_results": ["预期1", "预期2"],
  "test_type": "normal/exception/boundary/combination/backend_ui"
}

=== 输出前自检 ===
□ combination 用例是否≥8条？（必须有参数表和组合矩阵）
□ backend_ui 用例是否是否≥3条？（步骤含Network面板，预期含HTTP状态码）
□ 每个边界参数是否有最小值-1/最小值/最大值/最大值+1（具体数值）？
□ expected_results 数组长度是否等于 steps 数组长度？'''


# 接口测试自动附加的格式要求（与Excel导入模板格式一致）
API_FORMAT_REQUIREMENTS = '''

【输出格式要求】
- 输出纯JSON数组，不要包含markdown代码块标记或其他文本
- 每个接口至少生成：正向用例、参数校验用例、边界值用例
- 每条用例必须包含断言，断言必须覆盖状态码和关键业务字段

【字段规范】（严格按此格式，字段名必须完全一致）

=== 主表字段（必填/建议填/可选） ===
- name（必填）：用例名称，简洁明确，最大200字符
- method（必填）：请求方法，大写 GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS
- url（必填）：接口地址，相对路径如 /api/v1/auth/login
- module（建议填）：所属模块，如"认证模块"、"用户管理"
- priority（建议填）：P0(致命)/P1(严重)/P2(一般)/P3(轻微)，默认P2
- description（可选）：用例描述
- preconditions（可选）：前置条件，如"已注册账号admin"
- remark（可选）：备注信息

=== 请求配置 ===
- headers（可选）：请求头，JSON对象格式，如 {"Content-Type":"application/json","Authorization":"Bearer {{token}}"}
- query_params（可选）：查询参数，JSON对象格式，如 {"page":"1","size":"10"}
- body_type（可选）：请求体类型，默认 none
  * none：无请求体（GET/DELETE常用）
  * form-data：表单数据，文件上传用此类型
  * x-www-form-urlencoded：URL编码表单
  * raw-json：JSON格式请求体（POST/PUT常用）
  * raw-xml：XML格式请求体
  * raw-text：纯文本请求体
- body_content（可选）：请求体内容
  * raw-json类型：填写JSON字符串，如 "{\\"username\\":\\"admin\\",\\"password\\":\\"123456\\"}"
  * raw-xml类型：填写XML字符串
  * raw-text类型：填写纯文本
  * form-data类型：留空，使用body_form字段

=== 认证配置 ===
- auth_type（可选）：认证类型，默认 none
  * none：无认证
  * bearer：Bearer Token认证，需要token字段
  * basic：Basic认证，需要username和password字段
  * api_key：API Key认证，需要api_key_name、api_key_value、api_key_location字段
- token（可选）：Bearer Token值，支持变量如 "{{access_token}}"
- username（可选）：Basic认证用户名
- password（可选）：Basic认证密码
- api_key_name（可选）：API Key名称
- api_key_value（可选）：API Key值
- api_key_location（可选）：API Key位置，header或query

=== 脚本配置 ===
- setup_script（可选）：前置脚本，用例执行前运行的JavaScript代码
- teardown_script（可选）：后置脚本，用例执行后运行的JavaScript代码

=== 断言配置（必填） ===
- assertions（必填）：断言数组，格式见下方【断言规范】

=== 数据规则配置（可选） ===
- data_extract（可选）：数据提取/规则数组，格式见下方【数据规则规范】


【断言规范】（重要：字段名必须是 type，不是 assertion_type）

断言是列表+字典格式，每条断言包含以下字段：
- type（必填）：断言类型
- operator（必填）：比较方式
- expected（必填）：期望值（字符串类型）
- field（条件必填）：目标字段，仅 jsonpath 和 header 类型需要
- description（可选）：断言描述

=== 断言类型（type）详细说明 ===

1. status_code - HTTP状态码
   - 用途：验证接口返回的HTTP状态码
   - 不需要 field 字段
   - expected 示例："200"、"201"、"400"、"401"、"403"、"404"、"500"
   - 常用组合：
     * 正向用例：{"type":"status_code","operator":"equals","expected":"200"}
     * 创建成功：{"type":"status_code","operator":"equals","expected":"201"}
     * 未授权：{"type":"status_code","operator":"equals","expected":"401"}
     * 禁止访问：{"type":"status_code","operator":"equals","expected":"403"}
     * 资源不存在：{"type":"status_code","operator":"equals","expected":"404"}
     * 参数错误：{"type":"status_code","operator":"equals","expected":"400"}
     * 服务器错误：{"type":"status_code","operator":"equals","expected":"500"}

2. jsonpath - JSONPath提取值
   - 用途：从JSON响应体中提取字段值进行验证
   - 需要 field 字段：填写 JSONPath 表达式
   - field 示例："$.code"、"$.data.id"、"$.data.token"、"$.message"、"$.result.list[0].name"、"$.data.items.length"
   - expected 示例："0"、"success"、"true"、"admin"
   - 常用组合：
     * 业务状态码：{"type":"jsonpath","field":"$.code","operator":"equals","expected":"0"}
     * 业务成功：{"type":"jsonpath","field":"$.success","operator":"equals","expected":"true"}
     * 字段存在：{"type":"jsonpath","field":"$.data.token","operator":"exists","expected":""}
     * 字段不存在：{"type":"jsonpath","field":"$.error","operator":"not_exists","expected":""}
     * 字段包含：{"type":"jsonpath","field":"$.message","operator":"contains","expected":"成功"}
     * 字段不包含：{"type":"jsonpath","field":"$.data","operator":"not_contains","expected":"password"}
     * 数值比较：{"type":"jsonpath","field":"$.data.total","operator":"greater_than","expected":"0"}
     * 数组长度：{"type":"jsonpath","field":"$.data.list","operator":"length_greater_than","expected":"0"}
     * 字段类型：{"type":"jsonpath","field":"$.data.id","operator":"is_type","expected":"integer"}
     * 正则匹配：{"type":"jsonpath","field":"$.data.phone","operator":"regex","expected":"^1[3-9]\\d{9}$"}

3. header - 响应头字段
   - 用途：验证HTTP响应头
   - 需要 field 字段：填写响应头名称
   - field 示例："Content-Type"、"X-Request-Id"、"Cache-Control"、"Authorization"、"X-RateLimit-Limit"
   - expected 示例："application/json"、"no-cache"、"60"
   - 常用组合：
     * Content-Type：{"type":"header","field":"Content-Type","operator":"contains","expected":"application/json"}
     * 缓存控制：{"type":"header","field":"Cache-Control","operator":"contains","expected":"no-cache"}
     * 限流：{"type":"header","field":"X-RateLimit-Remaining","operator":"greater_than","expected":"0"}

4. response_time - 响应时间(毫秒)
   - 用途：验证接口响应性能
   - 不需要 field 字段
   - expected 示例："100"、"500"、"1000"、"3000"（单位：毫秒）
   - 常用组合：
     * 极快响应：{"type":"response_time","operator":"less_than","expected":"100"}
     * 快速响应：{"type":"response_time","operator":"less_than","expected":"500"}
     * 一般响应：{"type":"response_time","operator":"less_than","expected":"1000"}
     * 慢接口：{"type":"response_time","operator":"less_than","expected":"3000"}

5. body_contains - 响应体包含文本
   - 用途：验证响应体包含特定文本
   - 不需要 field 字段
   - expected 示例："success"、"操作成功"、"token"、"error"
   - 常用组合：
     * 成功标识：{"type":"body_contains","operator":"contains","expected":"success"}
     * 关键字：{"type":"body_contains","operator":"contains","expected":"token"}
     * 错误标识：{"type":"body_contains","operator":"not_contains","expected":"error"}
     * 版本号：{"type":"body_contains","operator":"regex","expected":"\\\\d+\\\\.\\\\d+\\\\.\\\\d+"}

=== 比较方式（operator）详细说明 ===

- equals：等于，精确匹配
  示例：{"type":"status_code","operator":"equals","expected":"200"}

- not_equals：不等于
  示例：{"type":"jsonpath","field":"$.data","operator":"not_equals","expected":"null"}

- contains：包含（字符串包含）
  示例：{"type":"body_contains","operator":"contains","expected":"成功"}

- not_contains：不包含
  示例：{"type":"body_contains","operator":"not_contains","expected":"error"}

- greater_than：大于（数值比较）
  示例：{"type":"jsonpath","field":"$.data.total","operator":"greater_than","expected":"0"}

- less_than：小于（数值比较）
  示例：{"type":"response_time","operator":"less_than","expected":"1000"}

- greater_than_or_equals：大于等于
  示例：{"type":"jsonpath","field":"$.data.count","operator":"greater_than_or_equals","expected":"1"}

- less_than_or_equals：小于等于
  示例：{"type":"jsonpath","field":"$.data.retry","operator":"less_than_or_equals","expected":"3"}

- regex：正则匹配
  示例：{"type":"jsonpath","field":"$.data.phone","operator":"regex","expected":"^1[3-9]\\d{9}$"}

- exists：存在（检查字段是否存在）
  示例：{"type":"jsonpath","field":"$.data.token","operator":"exists","expected":""}

- not_exists：不存在
  示例：{"type":"jsonpath","field":"$.error","operator":"not_exists","expected":""}

- is_type：类型检查（string/integer/float/boolean/array/object/null）
  示例：{"type":"jsonpath","field":"$.data.id","operator":"is_type","expected":"integer"}

- length_equals：长度等于（数组/字符串）
  示例：{"type":"jsonpath","field":"$.data.list","operator":"length_equals","expected":"10"}

- length_greater_than：长度大于
  示例：{"type":"jsonpath","field":"$.data.list","operator":"length_greater_than","expected":"0"}

- length_less_than：长度小于
  示例：{"type":"jsonpath","field":"$.data.items","operator":"length_less_than","expected":"100"}


【断言生成要求】
每条用例至少包含以下断言：
1. 状态码断言（status_code）- 验证HTTP状态码
2. 业务状态码断言（jsonpath $.code 或 $.success）- 验证业务逻辑成功
3. 关键字段存在性断言（jsonpath + exists）- 验证返回数据结构完整
4. 响应时间断言（response_time，建议 <1000ms）- 验证性能

根据接口特性可额外添加：
- 登录接口：验证 token 字段存在且不为空
- 列表接口：验证 total > 0 或 list 数组长度 > 0
- 增删改接口：验证返回的 message 包含成功提示
- 分页接口：验证 page、size、total 字段存在
- 文件接口：验证 Content-Type 为对应文件类型


【数据规则规范】（用于数据提取、变量生成、条件判断等）

数据规则是列表+字典格式，支持5种类型：

=== 1. extract - 从响应提取值（最常用） ===
用于提取响应中的值，供后续用例通过 {{变量名}} 引用
{
  "name": "token",
  "rule_type": "extract",
  "source": "jsonpath",
  "expression": "$.data.token",
  "description": "提取登录token"
}

字段说明：
- name（必填）：变量名，后续用例通过 {{变量名}} 引用，如 {"Authorization":"Bearer {{token}}"}
- rule_type（必填）：固定为 "extract"
- source（必填）：提取方式
  * jsonpath：从JSON响应体提取，expression填JSONPath表达式
  * regex：用正则表达式提取，expression填正则（含捕获组）
  * header：从响应头提取，expression填响应头名称
- expression（必填）：提取表达式
- description（可选）：描述说明

常用提取示例：
[
  {"name":"access_token","rule_type":"extract","source":"jsonpath","expression":"$.data.token","description":"提取登录token"},
  {"name":"user_id","rule_type":"extract","source":"jsonpath","expression":"$.data.id","description":"提取用户ID"},
  {"name":"csrf_token","rule_type":"extract","source":"regex","expression":"csrf_token=([^;]+)","description":"从Cookie提取CSRF Token"},
  {"name":"rate_limit","rule_type":"extract","source":"header","expression":"X-RateLimit-Limit","description":"提取限流阈值"}
]

=== 2. static - 设置静态值 ===
直接设置一个固定值作为变量
{
  "name": "test_env",
  "rule_type": "static",
  "static_value": "staging",
  "description": "设置测试环境标识"
}

字段说明：
- name（必填）：变量名
- rule_type（必填）：固定为 "static"
- static_value（必填）：静态值
- description（可选）：描述说明

=== 3. generate - 生成动态值 ===
自动生成随机值，用于测试数据隔离
{
  "name": "random_email",
  "rule_type": "generate",
  "generator": "random_string",
  "generator_params": {"length": 8, "suffix": "@test.com"},
  "description": "生成随机邮箱"
}

字段说明：
- name（必填）：变量名
- rule_type（必填）：固定为 "generate"
- generator（必填）：生成器类型
  * timestamp：当前时间戳（毫秒），如 1716720000000
  * uuid：UUID v4，如 550e8400-e29b-41d4-a716-446655440000
  * random_int：随机整数，params: {"min":1,"max":1000}
  * random_string：随机字符串，params: {"length":8,"prefix":"","suffix":""}
  * now：当前日期时间，params: {"format":"YYYY-MM-DD HH:mm:ss"}
- generator_params（可选）：生成器参数，JSON对象
- description（可选）：描述说明

常用生成示例：
[
  {"name":"timestamp","rule_type":"generate","generator":"timestamp","description":"当前时间戳"},
  {"name":"uuid","rule_type":"generate","generator":"uuid","description":"生成UUID"},
  {"name":"random_phone","rule_type":"generate","generator":"random_string","generator_params":{"length":11,"prefix":"138"},"description":"生成随机手机号"},
  {"name":"current_time","rule_type":"generate","generator":"now","generator_params":{"format":"YYYY-MM-DD HH:mm:ss"},"description":"当前时间"}
]

=== 4. transform - 变换已有变量 ===
对已有变量进行转换处理
{
  "name": "upper_name",
  "rule_type": "transform",
  "source_variable": "username",
  "transform_type": "upper",
  "transform_params": {},
  "description": "用户名转大写"
}

字段说明：
- name（必填）：新变量名
- rule_type（必填）：固定为 "transform"
- source_variable（必填）：源变量名（已存在的变量）
- transform_type（必填）：变换类型
  * substring：截取子串，params: {"start":0,"end":5}
  * concat：拼接，params: {"suffix":"_test"} 或 {"prefix":"user_"}
  * replace：替换，params: {"old":"foo","new":"bar"}
  * upper：转大写
  * lower：转小写
  * trim：去除首尾空格
  * to_int：转整数
  * to_string：转字符串
  * format_date：格式化日期，params: {"format":"YYYY-MM-DD"}
- transform_params（可选）：变换参数，JSON对象
- description（可选）：描述说明

=== 5. conditional - 条件赋值 ===
根据条件判断设置不同的值
{
  "name": "env_url",
  "rule_type": "conditional",
  "condition_variable": "test_env",
  "condition_operator": "equals",
  "condition_value": "staging",
  "true_value": "https://staging.example.com",
  "false_value": "https://prod.example.com",
  "description": "根据环境选择URL"
}

字段说明：
- name（必填）：变量名
- rule_type（必填）：固定为 "conditional"
- condition_variable（必填）：条件变量名
- condition_operator（必填）：条件比较方式
  * equals / not_equals
  * contains / not_contains
  * is_empty / is_not_empty
  * greater_than / less_than
- condition_value（必填）：条件值
- true_value（必填）：条件为真时的值
- false_value（必填）：条件为假时的值
- description（可选）：描述说明


【单条用例完整示例】（严格按此格式输出）

示例1 - 登录用例（Bearer Token认证）：
{
  "name": "用户登录-正确的用户名和密码",
  "method": "POST",
  "url": "/api/v1/auth/login",
  "module": "认证模块",
  "priority": "P0",
  "description": "使用正确的用户名和密码登录，验证返回token",
  "preconditions": "已注册账号admin，密码admin123",
  "headers": {"Content-Type": "application/json"},
  "query_params": {},
  "body_type": "raw-json",
  "body_content": "{\\"username\\":\\"admin\\",\\"password\\":\\"admin123\\"}",
  "auth_type": "none",
  "assertions": [
    {"type": "status_code", "operator": "equals", "expected": "200", "description": "HTTP状态码200"},
    {"type": "response_time", "operator": "less_than", "expected": "1000", "description": "响应时间<1秒"},
    {"type": "jsonpath", "field": "$.code", "operator": "equals", "expected": "0", "description": "业务状态码为0"},
    {"type": "jsonpath", "field": "$.data.token", "operator": "exists", "expected": "", "description": "token字段存在"},
    {"type": "jsonpath", "field": "$.data.token", "operator": "not_equals", "expected": "", "description": "token不为空"}
  ],
  "data_extract": [
    {"name": "access_token", "rule_type": "extract", "source": "jsonpath", "expression": "$.data.token", "description": "提取登录token用于后续接口"}
  ]
}

示例2 - 获取用户信息（使用变量）：
{
  "name": "获取当前用户信息",
  "method": "GET",
  "url": "/api/v1/users/me",
  "module": "用户管理",
  "priority": "P0",
  "description": "使用登录获取的token获取当前用户信息",
  "preconditions": "已登录获取access_token",
  "headers": {"Authorization": "Bearer {{access_token}}"},
  "query_params": {},
  "body_type": "none",
  "body_content": "",
  "auth_type": "bearer",
  "assertions": [
    {"type": "status_code", "operator": "equals", "expected": "200", "description": "HTTP状态码200"},
    {"type": "jsonpath", "field": "$.data.username", "operator": "equals", "expected": "admin", "description": "用户名正确"},
    {"type": "jsonpath", "field": "$.data.email", "operator": "exists", "expected": "", "description": "邮箱字段存在"},
    {"type": "jsonpath", "field": "$.data.id", "operator": "is_type", "expected": "integer", "description": "用户ID为整数"}
  ],
  "data_extract": [
    {"name": "user_id", "rule_type": "extract", "source": "jsonpath", "expression": "$.data.id", "description": "提取用户ID"},
    {"name": "user_email", "rule_type": "extract", "source": "jsonpath", "expression": "$.data.email", "description": "提取用户邮箱"}
  ]
}

示例3 - 创建资源（带动态数据）：
{
  "name": "创建新项目",
  "method": "POST",
  "url": "/api/v1/projects",
  "module": "项目管理",
  "priority": "P0",
  "description": "创建新项目并验证返回",
  "preconditions": "已登录",
  "headers": {"Content-Type": "application/json", "Authorization": "Bearer {{access_token}}"},
  "query_params": {},
  "body_type": "raw-json",
  "body_content": "{\\"name\\":\\"测试项目_{{timestamp}}\\",\\"description\\":\\"自动化测试创建\\"}",
  "assertions": [
    {"type": "status_code", "operator": "equals", "expected": "201", "description": "创建成功状态码201"},
    {"type": "jsonpath", "field": "$.data.id", "operator": "exists", "expected": "", "description": "返回项目ID"},
    {"type": "jsonpath", "field": "$.data.name", "operator": "contains", "expected": "测试项目", "description": "项目名称正确"},
    {"type": "body_contains", "operator": "contains", "expected": "创建成功", "description": "返回成功提示"}
  ],
  "data_extract": [
    {"name": "project_id", "rule_type": "extract", "source": "jsonpath", "expression": "$.data.id", "description": "提取项目ID用于后续操作"}
  ]
}'''


PROMPT_TEMPLATES = {
    "functional": {
        "system": """你是一个资深的测试工程师，擅长根据需求文档生成功能测试用例。

要求：
1. 根据需求的复杂度和覆盖度，自行决定生成用例的数量，确保全面覆盖
2. 用例必须覆盖以下测试方法：
   - 正常流程测试：验证主要功能的正常操作路径
   - 异常流程测试：验证错误处理和异常场景
   - 边界值测试：验证输入参数的边界条件（最小值、最大值、空值、特殊字符等）
   - 组合测试：验证多个参数组合的交互情况（使用 Pairwise 方法）
3. 每个用例包含：用例名称、前置条件、测试步骤、预期结果、优先级
4. 用例名称简洁明确，步骤可执行
5. 必须以 JSON 格式返回，不要包含其他内容""",

        "user": """请根据以下需求文档生成功能测试用例：

{input_content}

请根据需求的复杂度自行决定生成数量，确保全面覆盖以下测试方法：
- 正常流程测试（test_type: normal）
- 异常流程测试（test_type: exception）
- 边界值测试（test_type: boundary）：数值边界、字符串边界、日期边界等
- 组合测试（test_type: combination）：多参数组合场景

请严格以 JSON 数组格式返回，结构如下：
[
  {{
    "name": "用例名称",
    "priority": "P0/P1/P2/P3",
    "preconditions": "前置条件",
    "steps": ["步骤1", "步骤2"],
    "expected_result": "预期结果",
    "test_type": "normal/exception/boundary/combination"
  }}
]"""
    },

    "api": {
        "system": """你是一个接口测试专家，擅长根据接口文档生成接口测试用例。

要求：
1. 根据接口数量和复杂度，自行决定生成用例的数量
2. 每个接口生成：正向用例、参数校验用例、边界值用例
3. 输出格式为 JSON，包含完整的请求配置和断言
4. 断言必须覆盖状态码、关键字段
5. 考虑认证、鉴权场景
6. 必须以 JSON 格式返回，不要包含其他内容""",

        "user": """请根据以下接口文档生成接口测试用例：

{input_content}

请为每个接口生成测试用例，严格遵循以下字段规范：

字段说明（字段名必须完全一致）：
- name（必填）：用例名称
- method（必填）：请求方法，大写 GET/POST/PUT/DELETE
- url（必填）：接口地址，相对路径
- module（建议填）：所属模块
- priority（建议填）：P0/P1/P2/P3
- description（可选）：用例描述
- preconditions（可选）：前置条件
- headers（可选）：JSON对象格式，如 {{"Content-Type":"application/json"}}
- query_params（可选）：JSON对象格式，如 {{"page":"1"}}
- body_type（可选）：none/form-data/raw-json
- body_content（可选）：请求体JSON字符串
- assertions（必填）：断言数组
- data_extract（可选）：数据提取数组

断言规范（字段名是 type，不是 assertion_type）：
[
  {{"type":"status_code","operator":"equals","expected":"200"}},
  {{"type":"jsonpath","field":"$.code","operator":"equals","expected":"0"}}
]

数据提取规范：
[{{"name":"token","source":"jsonpath","expression":"$.data.token"}}]

请严格以 JSON 数组格式返回。"""
    }
}


class PromptEngine:
    """Prompt 引擎"""

    @staticmethod
    def build_messages_from_skill(skill, input_content: str) -> List[Dict[str, str]]:
        """从数据库 Skill 构建 AI 对话消息

        支持两种模式：
        1. 新模式（user_prompt 为空）：system_prompt 作为 system 消息，自动生成 user 消息
        2. 旧模式（user_prompt 非空）：兼容旧格式，分别使用 system_prompt 和 user_prompt

        Args:
            skill: AISkill 数据库对象
            input_content: 输入内容

        Returns:
            消息列表，包含 system 和 user 消息
        """
        if skill.user_prompt and skill.user_prompt.strip():
            # 旧模式：user_prompt 由用户/前端生成，包含 {input_content} 占位符
            try:
                user_content = skill.user_prompt.format(input_content=input_content)
            except (KeyError, ValueError):
                user_content = skill.user_prompt.replace("{input_content}", input_content)

            return [
                {"role": "system", "content": skill.system_prompt},
                {"role": "user", "content": user_content}
            ]

        # 新模式：system_prompt 是用户写的 Prompt 模板，user 消息自动生成
        system_content = skill.system_prompt

        # 根据 generate_type 选择格式要求
        if skill.generate_type == 'functional':
            format_req = FUNCTIONAL_FORMAT_REQUIREMENTS
        elif skill.generate_type == 'api':
            format_req = API_FORMAT_REQUIREMENTS
        else:
            format_req = ''

        # 检查模板中是否包含 {input_content} 占位符
        if '{input_content}' in system_content:
            # 将模板中的 {input_content} 替换为实际内容
            try:
                system_content = system_content.format(input_content=input_content)
            except (KeyError, ValueError):
                system_content = system_content.replace("{input_content}", input_content)
            # user 消息只放格式要求
            user_content = format_req.strip()
        else:
            # 模板中没有占位符，user 消息包含输入内容 + 格式要求
            user_content = f'请根据以下内容生成测试用例：\n\n{input_content}{format_req}'

        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ]

    @staticmethod
    def build_messages(
        generate_type: str,
        input_content: str
    ) -> List[Dict[str, str]]:
        """构建 AI 对话消息（从硬编码模板，向后兼容）

        Args:
            generate_type: 生成类型 (functional/api)
            input_content: 输入内容

        Returns:
            消息列表，包含 system 和 user 消息
        """
        template = PROMPT_TEMPLATES.get(generate_type)
        if not template:
            raise ValueError(f"不支持的生成类型: {generate_type}，支持: {', '.join(PROMPT_TEMPLATES.keys())}")

        return [
            {"role": "system", "content": template["system"]},
            {"role": "user", "content": template["user"].format(
                input_content=input_content
            )}
        ]

    @staticmethod
    def get_supported_types() -> List[str]:
        """获取支持的生成类型"""
        return list(PROMPT_TEMPLATES.keys())

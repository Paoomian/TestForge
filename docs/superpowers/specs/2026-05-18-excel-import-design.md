# Excel 批量导入用例功能设计

**日期**: 2026-05-18
**状态**: 已确认

---

## 概述

支持通过 Excel 文件批量导入接口测试用例，降低新项目接入成本。用户通过下载模板、填写用例数据、上传文件、预览编辑、确认导入的流程，快速创建大量用例。

## 用户流程

```
进入导入页面 → 下载模板（可选） → 上传文件 → 格式预校验 → 数据预览与编辑 → 确认导入 → 导入结果反馈
```

## 技术方案

**前端解析 + 后端校验**（方案 C）

- 前端使用 `xlsx` 库解析 Excel 文件，提供流畅的预览体验
- 前端做格式校验（必填字段、枚举值）
- 后端做业务校验（项目存在性、数据合法性）
- 后端复用现有批量创建逻辑

## Excel 模板设计

### 单 Sheet 扁平化结构

**前 10 列 - 主表字段**：

| 列 | 字段名 | 必填 | 说明 |
|---|---|---|---|
| A | 用例名称 | 是 | 最大 200 字符 |
| B | 请求方法 | 是 | GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS |
| C | 请求URL | 是 | 支持完整 URL 或路径 |
| D | 所属模块 | 否 | 如：用户管理、订单系统 |
| E | 优先级 | 否 | P0/P1/P2/P3，默认 P2 |
| F | 描述 | 否 | |
| G | 前置条件 | 否 | |
| H | Body类型 | 否 | none/form-data/raw-json/raw-xml/raw-text，默认 none |
| I | Body内容 | 否 | raw 类型填 JSON 字符串，form 类型留空 |
| J | 备注 | 否 | |

**后 N 列 - 子表数据（编号关联）**：

```
Headers（3 组）:
  K: header1_key  |  L: header1_value  |  M: header2_key  |  N: header2_value  |  O: header3_key  |  P: header3_value

Query Params（3 组）:
  Q: param1_key   |  R: param1_value   |  S: param2_key   |  T: param2_value   |  U: param3_key   |  V: param3_value

Assertions（3 组）:
  W: assert1_type |  X: assert1_field  |  Y: assert1_operator | Z: assert1_expected
  AA: assert2_type | AB: assert2_field | AC: assert2_operator | AD: assert2_expected
  AE: assert3_type | AF: assert3_field | AG: assert3_operator | AH: assert3_expected
```

### 子表字段说明

**Headers / Query Params**：
- `key`: 参数名
- `value`: 参数值

**Assertions**：
- `type`: status_code / jsonpath / header / body_contains
- `field`: JSONPath 表达式或 Header 名称（status_code 和 body_contains 留空）
- `operator`: equals / not_equals / contains / greater_than / less_than
- `expected`: 期望值

## 前端设计

### 入口位置

在 TestCaseList.vue 工具栏新增「导入Excel」按钮，与「新增用例」按钮并列。

### 组件结构

```
ExcelImportModal.vue（导入主弹窗）
├── Step 1: 上传区
│   ├── 模板下载链接
│   └── a-upload 文件上传（.xlsx/.xls）
├── Step 2: 预览编辑区
│   ├── a-table 可编辑表格
│   ├── 行级校验提示（红色标记错误行）
│   └── 批量操作（删除选中行、清空全部）
└── Step 3: 导入结果
    ├── 成功数量 / 失败数量
    ├── 失败详情列表（行号 + 错误原因）
    └── 「查看用例」跳转按钮
```

### 状态管理

```typescript
const importVisible = ref(false)
const importStep = ref(1)          // 1=上传, 2=预览, 3=结果
const importLoading = ref(false)
const parsedCases = ref<ParsedCase[]>()
const importResult = ref<ImportResult>()
```

### 前端解析映射

```typescript
// Excel 列 → 用例字段映射
const COLUMN_MAP = {
  '用例名称': 'name',
  '请求方法': 'method',
  '请求URL': 'url',
  '所属模块': 'module',
  '优先级': 'priority',
  '描述': 'description',
  '前置条件': 'preconditions',
  'Body类型': 'body_type',
  'Body内容': 'body_raw_content',
  '备注': 'remark',
}

// 解析 Headers
function parseHeaders(row): HeaderItem[] {
  const headers = []
  for (let i = 1; i <= 3; i++) {
    const key = row[`header${i}_key`]
    const value = row[`header${i}_value`]
    if (key) headers.push({ enabled: true, key, value: value || '', description: '' })
  }
  return headers
}

// parseQueryParams、parseAssertions 类似处理
```

### 前端校验规则

1. `name` 必填，最大 200 字符
2. `method` 必填，必须是有效 HTTP 方法
3. `url` 必填
4. `priority` 如有值，必须是 P0/P1/P2/P3
5. `body_type` 如有值，必须是有效枚举值
6. `assertion_type` 如有值，必须是有效枚举值
7. `assertion_operator` 如有值，必须是有效枚举值

错误行通过 `row-class` 返回 `row-error` 类名，配合 CSS 高亮显示。

### 可编辑表格实现

```vue
<a-table :data="parsedCases" :row-class="getRowClass">
  <template #columns>
    <a-table-column title="用例名称" data-index="name">
      <template #cell="{ record }">
        <a-input v-model="record.name" size="mini" />
      </template>
    </a-table-column>
    <!-- 其他列类似 -->
  </template>
</a-table>
```

## 后端设计

### API 接口

**POST `/api/v1/api-test-cases/import-excel`**

### 请求体

```python
class ExcelImportRequest(BaseModel):
    cases: list[ExcelCaseItem]
    project_id: int

class ExcelCaseItem(BaseModel):
    # 主表字段
    name: str
    method: str
    url: str
    module: str | None = None
    priority: str = "P2"
    description: str | None = None
    preconditions: str | None = None
    body_type: str = "none"
    body_raw_content: str | None = None
    remark: str | None = None
    
    # 子表字段
    headers: list[dict] = []
    query_params: list[dict] = []
    body_form: list[dict] = []
    assertions: list[dict] = []
```

### 响应体

```python
class ExcelImportResult(BaseModel):
    total: int
    success: int
    failed: int
    created_ids: list[int]
    errors: list[ImportError]

class ImportError(BaseModel):
    row: int
    name: str
    error: str
```

### 后端校验规则

1. `name` 非空且长度 ≤ 200
2. `method` 必须是 GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS 之一
3. `url` 非空
4. `priority` 必须是 P0/P1/P2/P3 之一
5. `body_type` 必须是有效枚举值
6. `project_id` 必须存在
7. `assertion_type` 和 `assertion_operator` 必须是有效枚举值

### 复用逻辑

- 复用 `APITestCaseCreate` Schema 的校验规则
- 复用 `case_number` 生成器
- 复用子表创建逻辑（删旧插新策略）

## 数据流

```
Excel 文件
    ↓ (前端 xlsx 库解析)
ParsedCase[] (扁平结构)
    ↓ (前端格式校验 + 用户编辑)
ExcelCaseItem[] (结构化 JSON)
    ↓ (POST /import-excel)
后端业务校验
    ↓ (逐条校验，收集错误)
APITestCaseCreate[] (有效用例)
    ↓ (批量创建)
数据库写入
    ↓
ExcelImportResult (结果反馈)
```

## 错误处理

| 阶段 | 错误类型 | 处理方式 |
|------|----------|----------|
| 文件上传 | 格式错误、文件过大 | Message.error 提示，不进入下一步 |
| 前端解析 | 列名不匹配、空文件 | 弹窗内提示，允许重新上传 |
| 前端校验 | 必填字段为空、枚举值无效 | 错误行标红，tooltip 显示原因 |
| 后端校验 | 业务规则不满足 | 返回错误列表，展示在结果页 |
| 后端创建 | 数据库写入失败 | 事务回滚，返回具体错误 |

## 依赖

### 前端

- `xlsx`: Excel 文件解析库（新增）

### 后端

- 无新增依赖，复用现有 SQLAlchemy + Pydantic

## 文件清单

### 新增文件

- `frontend/src/components/ExcelImportModal.vue` - 导入主弹窗
- `frontend/src/utils/excelParser.ts` - Excel 解析工具函数
- `server/core/excel_import_service.py` - 导入服务（校验 + 创建）

### 修改文件

- `frontend/src/views/api-test/TestCaseList.vue` - 添加导入按钮
- `frontend/src/api/apiTestCase.ts` - 添加导入 API
- `server/api/api_test_cases.py` - 添加导入端点
- `server/schemas/api_test_case.py` - 添加导入相关 Schema
- `frontend/package.json` - 添加 xlsx 依赖

## 验收标准

1. 用户能下载 Excel 模板
2. 用户能上传 .xlsx/.xls 文件
3. 前端正确解析 Excel 并展示预览表格
4. 预览表格支持编辑
5. 前端校验错误行标红显示
6. 确认导入后后端正确创建用例
7. 导入结果正确展示成功/失败数量
8. 失败用例显示具体错误原因
9. 导入成功后能在用例列表中看到新用例

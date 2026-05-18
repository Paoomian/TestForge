# Excel 批量导入用例功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现通过 Excel 文件批量导入接口测试用例的功能，支持下载模板、上传文件、预览编辑、确认导入的完整流程。

**Architecture:** 前端使用 xlsx 库解析 Excel 文件并提供可编辑预览，后端接收结构化 JSON 进行业务校验和批量创建。采用前端解析 + 后端校验的混合方案，平衡用户体验和实现复杂度。

**Tech Stack:** Vue 3 + TypeScript + Arco Design Vue（前端），FastAPI + SQLAlchemy + Pydantic（后端），xlsx（Excel 解析）

---

## 文件结构

### 新增文件

| 文件路径 | 职责 |
|----------|------|
| `server/schemas/excel_import.py` | 导入相关 Schema 定义 |
| `server/core/excel_import_service.py` | 导入服务（校验 + 批量创建） |
| `frontend/src/utils/excelParser.ts` | Excel 解析工具函数 |
| `frontend/src/api/excelImport.ts` | 导入 API 接口 |
| `frontend/src/views/api-test/components/ExcelImportModal.vue` | 导入主弹窗组件 |

### 修改文件

| 文件路径 | 修改内容 |
|----------|----------|
| `server/api/api_test_cases.py` | 添加 import-excel 端点 |
| `server/schemas/__init__.py` | 导出新 Schema |
| `frontend/package.json` | 添加 xlsx 依赖 |
| `frontend/src/views/api-test/TestCaseList.vue` | 添加导入按钮 |

---

## Task 1: 后端 Schema 定义

**Files:**
- Create: `server/schemas/excel_import.py`
- Modify: `server/schemas/__init__.py`

- [ ] **Step 1: 创建 Excel 导入 Schema 文件**

```python
# server/schemas/excel_import.py
from pydantic import BaseModel, Field


class ExcelHeaderItem(BaseModel):
    """Excel 导入的 Header 项"""
    enabled: bool = True
    key: str
    value: str = ""
    description: str = ""


class ExcelQueryParamItem(BaseModel):
    """Excel 导入的查询参数项"""
    enabled: bool = True
    key: str
    value: str = ""
    description: str = ""


class ExcelBodyFormItem(BaseModel):
    """Excel 导入的表单 Body 项"""
    enabled: bool = True
    key: str
    value: str = ""
    param_type: str = "text"
    description: str = ""


class ExcelAssertionItem(BaseModel):
    """Excel 导入的断言项"""
    assertion_type: str = Field(..., description="status_code/jsonpath/header/body_contains")
    operator: str = Field(..., description="equals/not_equals/contains/greater_than/less_than")
    field: str = ""
    expected: str = ""
    description: str = ""


class ExcelCaseItem(BaseModel):
    """Excel 导入的单条用例"""
    # 主表字段
    name: str = Field(..., min_length=1, max_length=200)
    method: str = Field(..., description="GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS")
    url: str = Field(..., min_length=1)
    module: str | None = None
    priority: str = Field(default="P2", description="P0/P1/P2/P3")
    description: str | None = None
    preconditions: str | None = None
    body_type: str = Field(default="none", description="none/form-data/raw-json/raw-xml/raw-text")
    body_raw_content: str | None = None
    remark: str | None = None

    # 子表字段
    headers: list[ExcelHeaderItem] = []
    query_params: list[ExcelQueryParamItem] = []
    body_form: list[ExcelBodyFormItem] = []
    assertions: list[ExcelAssertionItem] = []


class ExcelImportRequest(BaseModel):
    """Excel 导入请求"""
    cases: list[ExcelCaseItem]
    project_id: int


class ImportError(BaseModel):
    """导入错误详情"""
    row: int
    name: str
    error: str


class ExcelImportResult(BaseModel):
    """导入结果"""
    total: int
    success: int
    failed: int
    created_ids: list[int]
    errors: list[ImportError]
```

- [ ] **Step 2: 更新 Schema 导出**

在 `server/schemas/__init__.py` 中添加导出：

```python
from .excel_import import (
    ExcelImportRequest,
    ExcelCaseItem,
    ExcelImportResult,
    ImportError as ExcelImportError,
)
```

- [ ] **Step 3: 验证 Schema 可导入**

运行：`cd server && python -c "from schemas.excel_import import ExcelImportRequest; print('OK')"`

预期：输出 `OK`

- [ ] **Step 4: 提交**

```bash
git add server/schemas/excel_import.py server/schemas/__init__.py
git commit -m "feat: 添加 Excel 导入 Schema 定义"
```

---

## Task 2: 后端导入服务

**Files:**
- Create: `server/core/excel_import_service.py`

- [ ] **Step 1: 创建导入服务文件**

```python
# server/core/excel_import_service.py
from sqlalchemy.orm import Session

from models.api_test_case import APITestCase
from models.test_case_header import TestCaseHeader
from models.test_case_query_param import TestCaseQueryParam
from models.test_case_body import TestCaseBodyRaw
from models.test_case_assertion import TestCaseAssertion
from schemas.excel_import import ExcelCaseItem, ExcelImportResult, ImportError
from core.case_number import generate_case_number


# 有效枚举值
VALID_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
VALID_PRIORITIES = {"P0", "P1", "P2", "P3"}
VALID_BODY_TYPES = {"none", "form-data", "x-www-form-urlencoded", "raw-json", "raw-xml", "raw-text"}
VALID_ASSERTION_TYPES = {"status_code", "jsonpath", "header", "body_contains"}
VALID_ASSERTION_OPERATORS = {"equals", "not_equals", "contains", "greater_than", "less_than", "regex", "exists"}


def validate_case_item(case: ExcelCaseItem, row: int) -> str | None:
    """校验单条用例数据，返回错误信息或 None"""
    if not case.name or len(case.name) > 200:
        return f"用例名称无效（必填，最大200字符）"
    
    if case.method.upper() not in VALID_METHODS:
        return f"请求方法无效：{case.method}（有效值：{', '.join(VALID_METHODS)}）"
    
    if not case.url:
        return "请求URL不能为空"
    
    if case.priority and case.priority not in VALID_PRIORITIES:
        return f"优先级无效：{case.priority}（有效值：{', '.join(VALID_PRIORITIES)}）"
    
    if case.body_type and case.body_type not in VALID_BODY_TYPES:
        return f"Body类型无效：{case.body_type}（有效值：{', '.join(VALID_BODY_TYPES)}）"
    
    # 校验断言
    for i, assertion in enumerate(case.assertions):
        if assertion.assertion_type not in VALID_ASSERTION_TYPES:
            return f"断言{i+1}类型无效：{assertion.assertion_type}"
        if assertion.operator not in VALID_ASSERTION_OPERATORS:
            return f"断言{i+1}运算符无效：{assertion.operator}"
    
    return None


def create_case_from_excel(
    db: Session,
    case: ExcelCaseItem,
    project_id: int,
    creator_id: int,
) -> APITestCase:
    """从 Excel 数据创建用例"""
    # 生成用例编号
    case_number = generate_case_number(db, case.module or "DEFAULT")
    
    # 创建主表记录
    db_case = APITestCase(
        project_id=project_id,
        case_number=case_number,
        name=case.name,
        method=case.method.upper(),
        url=case.url,
        module=case.module,
        priority=case.priority or "P2",
        description=case.description,
        preconditions=case.preconditions,
        body_type=case.body_type or "none",
        remark=case.remark,
        creator_id=creator_id,
    )
    db.add(db_case)
    db.flush()  # 获取 ID
    
    # 创建 Headers
    for i, header in enumerate(case.headers):
        if header.key:  # 跳过空行
            db.add(TestCaseHeader(
                test_case_id=db_case.id,
                enabled=header.enabled,
                key=header.key,
                value=header.value,
                description=header.description,
                sort_order=i,
            ))
    
    # 创建 Query Params
    for i, param in enumerate(case.query_params):
        if param.key:
            db.add(TestCaseQueryParam(
                test_case_id=db_case.id,
                enabled=param.enabled,
                key=param.key,
                value=param.value,
                description=param.description,
                sort_order=i,
            ))
    
    # 创建 Body Raw（如果 body_type 是 raw 类型）
    if case.body_type and case.body_type.startswith("raw-") and case.body_raw_content:
        db.add(TestCaseBodyRaw(
            test_case_id=db_case.id,
            content=case.body_raw_content,
        ))
    
    # 创建断言
    for i, assertion in enumerate(case.assertions):
        db.add(TestCaseAssertion(
            test_case_id=db_case.id,
            assertion_type=assertion.assertion_type,
            operator=assertion.operator,
            field=assertion.field,
            expected=assertion.expected,
            description=assertion.description,
            sort_order=i,
        ))
    
    return db_case


def import_excel_cases(
    db: Session,
    cases: list[ExcelCaseItem],
    project_id: int,
    creator_id: int,
) -> ExcelImportResult:
    """批量导入用例"""
    total = len(cases)
    success = 0
    failed = 0
    created_ids = []
    errors = []
    
    for i, case in enumerate(cases):
        row = i + 2  # Excel 行号从 2 开始（第 1 行是表头）
        
        # 校验
        error = validate_case_item(case, row)
        if error:
            failed += 1
            errors.append(ImportError(row=row, name=case.name or f"第{row}行", error=error))
            continue
        
        try:
            # 创建用例
            db_case = create_case_from_excel(db, case, project_id, creator_id)
            success += 1
            created_ids.append(db_case.id)
        except Exception as e:
            failed += 1
            errors.append(ImportError(row=row, name=case.name, error=str(e)))
    
    # 提交事务
    if success > 0:
        db.commit()
    
    return ExcelImportResult(
        total=total,
        success=success,
        failed=failed,
        created_ids=created_ids,
        errors=errors,
    )
```

- [ ] **Step 2: 验证服务可导入**

运行：`cd server && python -c "from core.excel_import_service import import_excel_cases; print('OK')"`

预期：输出 `OK`

- [ ] **Step 3: 提交**

```bash
git add server/core/excel_import_service.py
git commit -m "feat: 添加 Excel 导入服务（校验 + 批量创建）"
```

---

## Task 3: 后端 API 端点

**Files:**
- Modify: `server/api/api_test_cases.py`

- [ ] **Step 1: 添加导入端点**

在 `server/api/api_test_cases.py` 文件末尾添加：

```python
from schemas.excel_import import ExcelImportRequest, ExcelImportResult
from core.excel_import_service import import_excel_cases


@router.post("/import-excel", response_model=ExcelImportResult)
def import_excel(
    req: ExcelImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Excel 批量导入用例"""
    # 验证项目是否存在
    project = db.query(Project).filter(Project.id == req.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    result = import_excel_cases(
        db=db,
        cases=req.cases,
        project_id=req.project_id,
        creator_id=current_user.id,
    )
    
    return result
```

- [ ] **Step 2: 验证端点可访问**

启动后端服务后运行：
```bash
curl -X POST http://localhost:8000/api/v1/api-test-cases/import-excel \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"cases": [], "project_id": 1}'
```

预期：返回 `{"total": 0, "success": 0, "failed": 0, "created_ids": [], "errors": []}`

- [ ] **Step 3: 提交**

```bash
git add server/api/api_test_cases.py
git commit -m "feat: 添加 Excel 导入 API 端点"
```

---

## Task 4: 前端依赖安装

**Files:**
- Modify: `frontend/package.json`

- [ ] **Step 1: 安装 xlsx 依赖**

```bash
cd frontend
npm install xlsx
```

- [ ] **Step 2: 验证安装成功**

```bash
cd frontend
node -e "const XLSX = require('xlsx'); console.log('xlsx version:', XLSX.version)"
```

预期：输出 xlsx 版本号

- [ ] **Step 3: 提交**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "feat: 添加 xlsx 依赖"
```

---

## Task 5: 前端 Excel 解析工具

**Files:**
- Create: `frontend/src/utils/excelParser.ts`

- [ ] **Step 1: 创建 Excel 解析工具文件**

```typescript
// frontend/src/utils/excelParser.ts
import * as XLSX from 'xlsx'

// 类型定义
export interface ParsedHeader {
  enabled: boolean
  key: string
  value: string
  description: string
}

export interface ParsedQueryParam {
  enabled: boolean
  key: string
  value: string
  description: string
}

export interface ParsedBodyForm {
  enabled: boolean
  key: string
  value: string
  param_type: string
  description: string
}

export interface ParsedAssertion {
  assertion_type: string
  operator: string
  field: string
  expected: string
  description: string
}

export interface ParsedCase {
  name: string
  method: string
  url: string
  module?: string
  priority: string
  description?: string
  preconditions?: string
  body_type: string
  body_raw_content?: string
  remark?: string
  headers: ParsedHeader[]
  query_params: ParsedQueryParam[]
  body_form: ParsedBodyForm[]
  assertions: ParsedAssertion[]
  _row: number  // 原始行号，用于错误提示
  _errors: string[]  // 校验错误
}

// 有效枚举值
const VALID_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
const VALID_PRIORITIES = ['P0', 'P1', 'P2', 'P3']
const VALID_BODY_TYPES = ['none', 'form-data', 'x-www-form-urlencoded', 'raw-json', 'raw-xml', 'raw-text']
const VALID_ASSERTION_TYPES = ['status_code', 'jsonpath', 'header', 'body_contains']
const VALID_ASSERTION_OPERATORS = ['equals', 'not_equals', 'contains', 'greater_than', 'less_than', 'regex', 'exists']

// Excel 列名映射
const COLUMN_MAP: Record<string, keyof ParsedCase> = {
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

/**
 * 解析 Headers 列
 */
function parseHeaders(row: Record<string, any>): ParsedHeader[] {
  const headers: ParsedHeader[] = []
  for (let i = 1; i <= 3; i++) {
    const key = row[`header${i}_key`]
    const value = row[`header${i}_value`]
    if (key && typeof key === 'string' && key.trim()) {
      headers.push({
        enabled: true,
        key: String(key).trim(),
        value: value ? String(value).trim() : '',
        description: '',
      })
    }
  }
  return headers
}

/**
 * 解析 Query Params 列
 */
function parseQueryParams(row: Record<string, any>): ParsedQueryParam[] {
  const params: ParsedQueryParam[] = []
  for (let i = 1; i <= 3; i++) {
    const key = row[`param${i}_key`]
    const value = row[`param${i}_value`]
    if (key && typeof key === 'string' && key.trim()) {
      params.push({
        enabled: true,
        key: String(key).trim(),
        value: value ? String(value).trim() : '',
        description: '',
      })
    }
  }
  return params
}

/**
 * 解析 Assertions 列
 */
function parseAssertions(row: Record<string, any>): ParsedAssertion[] {
  const assertions: ParsedAssertion[] = []
  for (let i = 1; i <= 3; i++) {
    const type = row[`assert${i}_type`]
    const field = row[`assert${i}_field`]
    const operator = row[`assert${i}_operator`]
    const expected = row[`assert${i}_expected`]
    if (type && typeof type === 'string' && type.trim()) {
      assertions.push({
        assertion_type: String(type).trim().toLowerCase(),
        operator: operator ? String(operator).trim().toLowerCase() : '',
        field: field ? String(field).trim() : '',
        expected: expected ? String(expected).trim() : '',
        description: '',
      })
    }
  }
  return assertions
}

/**
 * 校验单条用例
 */
function validateCase(parsed: ParsedCase): string[] {
  const errors: string[] = []
  
  if (!parsed.name || parsed.name.length > 200) {
    errors.push('用例名称无效（必填，最大200字符）')
  }
  
  if (!parsed.method || !VALID_METHODS.includes(parsed.method.toUpperCase())) {
    errors.push(`请求方法无效（有效值：${VALID_METHODS.join(', ')}）`)
  }
  
  if (!parsed.url) {
    errors.push('请求URL不能为空')
  }
  
  if (parsed.priority && !VALID_PRIORITIES.includes(parsed.priority)) {
    errors.push(`优先级无效（有效值：${VALID_PRIORITIES.join(', ')}）`)
  }
  
  if (parsed.body_type && !VALID_BODY_TYPES.includes(parsed.body_type)) {
    errors.push(`Body类型无效（有效值：${VALID_BODY_TYPES.join(', ')}）`)
  }
  
  // 校验断言
  parsed.assertions.forEach((assertion, index) => {
    if (assertion.assertion_type && !VALID_ASSERTION_TYPES.includes(assertion.assertion_type)) {
      errors.push(`断言${index + 1}类型无效`)
    }
    if (assertion.operator && !VALID_ASSERTION_OPERATORS.includes(assertion.operator)) {
      errors.push(`断言${index + 1}运算符无效`)
    }
  })
  
  return errors
}

/**
 * 解析 Excel 文件
 */
export function parseExcelFile(file: File): Promise<ParsedCase[]> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target?.result as ArrayBuffer)
        const workbook = XLSX.read(data, { type: 'array' })
        
        // 获取第一个 Sheet
        const sheetName = workbook.SheetNames[0]
        if (!sheetName) {
          reject(new Error('Excel 文件为空'))
          return
        }
        
        const sheet = workbook.Sheets[sheetName]
        const jsonData = XLSX.utils.sheet_to_json(sheet)
        
        if (jsonData.length === 0) {
          reject(new Error('Excel 文件没有数据行'))
          return
        }
        
        // 解析每行数据
        const parsedCases: ParsedCase[] = jsonData.map((row: any, index: number) => {
          const parsed: ParsedCase = {
            name: '',
            method: '',
            url: '',
            priority: 'P2',
            body_type: 'none',
            headers: [],
            query_params: [],
            body_form: [],
            assertions: [],
            _row: index + 2,  // Excel 行号从 2 开始
            _errors: [],
          }
          
          // 映射主表字段
          for (const [excelCol, field] of Object.entries(COLUMN_MAP)) {
            const value = row[excelCol]
            if (value !== undefined && value !== null) {
              (parsed as any)[field] = String(value).trim()
            }
          }
          
          // 处理 method 大写
          if (parsed.method) {
            parsed.method = parsed.method.toUpperCase()
          }
          
          // 解析子表
          parsed.headers = parseHeaders(row)
          parsed.query_params = parseQueryParams(row)
          parsed.assertions = parseAssertions(row)
          
          // 校验
          parsed._errors = validateCase(parsed)
          
          return parsed
        })
        
        resolve(parsedCases)
      } catch (error) {
        reject(new Error('Excel 文件解析失败：' + (error as Error).message))
      }
    }
    
    reader.onerror = () => {
      reject(new Error('文件读取失败'))
    }
    
    reader.readAsArrayBuffer(file)
  })
}

/**
 * 生成 Excel 模板
 */
export function generateExcelTemplate(): Blob {
  // 表头
  const headers = [
    '用例名称', '请求方法', '请求URL', '所属模块', '优先级',
    '描述', '前置条件', 'Body类型', 'Body内容', '备注',
    'header1_key', 'header1_value', 'header2_key', 'header2_value', 'header3_key', 'header3_value',
    'param1_key', 'param1_value', 'param2_key', 'param2_value', 'param3_key', 'param3_value',
    'assert1_type', 'assert1_field', 'assert1_operator', 'assert1_expected',
    'assert2_type', 'assert2_field', 'assert2_operator', 'assert2_expected',
    'assert3_type', 'assert3_field', 'assert3_operator', 'assert3_expected',
  ]
  
  // 示例数据
  const exampleRow = [
    '用户登录', 'POST', '/api/v1/auth/login', '认证模块', 'P0',
    '用户登录接口', '', 'raw-json', '{"username":"admin","password":"123456"}', '',
    'Content-Type', 'application/json', '', '', '', '',
    '', '', '', '', '', '',
    'status_code', '', 'equals', '200',
    'jsonpath', '$.code', 'equals', '0',
    '', '', '', '',
  ]
  
  const ws = XLSX.utils.aoa_to_sheet([headers, exampleRow])
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '用例模板')
  
  const wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'array' })
  return new Blob([wbout], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
}
```

- [ ] **Step 2: 验证工具可导入**

在浏览器控制台或测试文件中验证：
```typescript
import { parseExcelFile, generateExcelTemplate } from '@/utils/excelParser'
console.log('Excel parser loaded successfully')
```

预期：无报错

- [ ] **Step 3: 提交**

```bash
git add frontend/src/utils/excelParser.ts
git commit -m "feat: 添加 Excel 解析工具函数"
```

---

## Task 6: 前端 API 层

**Files:**
- Create: `frontend/src/api/excelImport.ts`

- [ ] **Step 1: 创建导入 API 文件**

```typescript
// frontend/src/api/excelImport.ts
import request from '@/utils/request'

// 类型定义
export interface ExcelHeaderItem {
  enabled: boolean
  key: string
  value: string
  description: string
}

export interface ExcelQueryParamItem {
  enabled: boolean
  key: string
  value: string
  description: string
}

export interface ExcelBodyFormItem {
  enabled: boolean
  key: string
  value: string
  param_type: string
  description: string
}

export interface ExcelAssertionItem {
  assertion_type: string
  operator: string
  field: string
  expected: string
  description: string
}

export interface ExcelCaseItem {
  name: string
  method: string
  url: string
  module?: string
  priority: string
  description?: string
  preconditions?: string
  body_type: string
  body_raw_content?: string
  remark?: string
  headers: ExcelHeaderItem[]
  query_params: ExcelQueryParamItem[]
  body_form: ExcelBodyFormItem[]
  assertions: ExcelAssertionItem[]
}

export interface ImportError {
  row: number
  name: string
  error: string
}

export interface ExcelImportResult {
  total: number
  success: number
  failed: number
  created_ids: number[]
  errors: ImportError[]
}

export interface ExcelImportRequest {
  cases: ExcelCaseItem[]
  project_id: number
}

/**
 * 批量导入用例
 */
export const importExcelCases = (data: ExcelImportRequest) => {
  return request<ExcelImportResult>({
    url: '/api-test-cases/import-excel',
    method: 'post',
    data,
  })
}
```

- [ ] **Step 2: 验证 API 可导入**

运行：`cd frontend && npm run type-check`（如果有 type-check 脚本）

预期：无类型错误

- [ ] **Step 3: 提交**

```bash
git add frontend/src/api/excelImport.ts
git commit -m "feat: 添加 Excel 导入 API 接口"
```

---

## Task 7: 前端导入组件

**Files:**
- Create: `frontend/src/views/api-test/components/ExcelImportModal.vue`

- [ ] **Step 1: 创建导入弹窗组件**

```vue
<!-- frontend/src/views/api-test/components/ExcelImportModal.vue -->
<template>
  <a-modal
    v-model:visible="visible"
    title="导入Excel用例"
    :width="900"
    :mask-closable="false"
    @cancel="handleClose"
  >
    <!-- Step 1: 上传区 -->
    <div v-if="step === 1" class="upload-section">
      <div class="template-download">
        <a-button type="text" @click="downloadTemplate">
          <template #icon><icon-download /></template>
          下载模板
        </a-button>
        <span class="template-hint">建议先下载模板，按格式填写用例数据</span>
      </div>
      
      <a-upload
        :auto-upload="false"
        :show-file-list="false"
        accept=".xlsx,.xls"
        @change="handleFileChange"
      >
        <template #upload-button>
          <div class="upload-area">
            <icon-upload />
            <div class="upload-text">点击或拖拽 Excel 文件到此处</div>
            <div class="upload-hint">支持 .xlsx / .xls 格式</div>
          </div>
        </template>
      </a-upload>
      
      <div v-if="parseError" class="parse-error">
        <icon-exclamation-circle />
        {{ parseError }}
      </div>
    </div>
    
    <!-- Step 2: 预览编辑区 -->
    <div v-else-if="step === 2" class="preview-section">
      <div class="preview-toolbar">
        <div class="preview-info">
          共 <strong>{{ parsedCases.length }}</strong> 条用例
          <span v-if="errorCount > 0" class="error-count">
            ，<strong class="error-text">{{ errorCount }}</strong> 条有误
          </span>
        </div>
        <div class="preview-actions">
          <a-button size="small" @click="deleteSelected" :disabled="selectedRows.length === 0">
            删除选中 ({{ selectedRows.length }})
          </a-button>
          <a-button size="small" @click="clearAll">清空全部</a-button>
          <a-button size="small" @click="reupload">重新上传</a-button>
        </div>
      </div>
      
      <a-table
        :data="parsedCases"
        :pagination="{ pageSize: 10 }"
        :row-selection="{ selectedRowKeys: selectedRows, onChange: onSelectChange }"
        :row-class="getRowClass"
        :scroll="{ x: 1200 }"
        size="small"
      >
        <template #columns>
          <a-table-column title="行号" :width="60" align="center">
            <template #cell="{ record }">{{ record._row }}</template>
          </a-table-column>
          
          <a-table-column title="用例名称" :width="150" :tooltip="true">
            <template #cell="{ record }">
              <a-input v-model="record.name" size="mini" :class="{ 'input-error': hasFieldError(record, 'name') }" />
            </template>
          </a-table-column>
          
          <a-table-column title="请求方法" :width="100">
            <template #cell="{ record }">
              <a-select v-model="record.method" size="mini" :class="{ 'input-error': hasFieldError(record, 'method') }">
                <a-option v-for="m in methods" :key="m" :value="m">{{ m }}</a-option>
              </a-select>
            </template>
          </a-table-column>
          
          <a-table-column title="请求URL" :width="200" :tooltip="true">
            <template #cell="{ record }">
              <a-input v-model="record.url" size="mini" :class="{ 'input-error': hasFieldError(record, 'url') }" />
            </template>
          </a-table-column>
          
          <a-table-column title="所属模块" :width="120">
            <template #cell="{ record }">
              <a-input v-model="record.module" size="mini" />
            </template>
          </a-table-column>
          
          <a-table-column title="优先级" :width="80">
            <template #cell="{ record }">
              <a-select v-model="record.priority" size="mini">
                <a-option v-for="p in priorities" :key="p" :value="p">{{ p }}</a-option>
              </a-select>
            </template>
          </a-table-column>
          
          <a-table-column title="Body类型" :width="120">
            <template #cell="{ record }">
              <a-select v-model="record.body_type" size="mini">
                <a-option v-for="bt in bodyTypes" :key="bt" :value="bt">{{ bt }}</a-option>
              </a-select>
            </template>
          </a-table-column>
          
          <a-table-column title="状态" :width="80" align="center">
            <template #cell="{ record }">
              <a-tag v-if="record._errors.length === 0" color="green">正常</a-tag>
              <a-tooltip v-else :content="record._errors.join('\n')">
                <a-tag color="red">{{ record._errors.length }}个错误</a-tag>
              </a-tooltip>
            </template>
          </a-table-column>
        </template>
      </a-table>
    </div>
    
    <!-- Step 3: 导入结果 -->
    <div v-else-if="step === 3" class="result-section">
      <div class="result-summary">
        <a-row :gutter="16">
          <a-col :span="8">
            <a-statistic title="总数" :value="importResult?.total || 0" />
          </a-col>
          <a-col :span="8">
            <a-statistic title="成功" :value="importResult?.success || 0" :value-style="{ color: '#00b42a' }" />
          </a-col>
          <a-col :span="8">
            <a-statistic title="失败" :value="importResult?.failed || 0" :value-style="{ color: '#f53f3f' }" />
          </a-col>
        </a-row>
      </div>
      
      <div v-if="importResult?.errors && importResult.errors.length > 0" class="error-list">
        <div class="error-list-title">失败详情：</div>
        <a-table :data="importResult.errors" :pagination="false" size="small">
          <template #columns>
            <a-table-column title="行号" data-index="row" :width="80" />
            <a-table-column title="用例名称" data-index="name" :width="200" />
            <a-table-column title="错误原因" data-index="error" />
          </template>
        </a-table>
      </div>
    </div>
    
    <template #footer>
      <a-button v-if="step > 1" @click="step--">上一步</a-button>
      <a-button v-if="step === 1" type="primary" :disabled="!file" @click="handleParse">
        解析文件
      </a-button>
      <a-button v-if="step === 2" type="primary" :loading="importLoading" @click="handleImport">
        确认导入
      </a-button>
      <a-button v-if="step === 3" type="primary" @click="handleFinish">
        完成
      </a-button>
    </template>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Message } from '@arco-design/web-vue'
import { IconUpload, IconDownload, IconExclamationCircle } from '@arco-design/web-vue/es/icon'
import { parseExcelFile, generateExcelTemplate } from '@/utils/excelParser'
import type { ParsedCase } from '@/utils/excelParser'
import { importExcelCases } from '@/api/excelImport'
import type { ExcelImportResult } from '@/api/excelImport'

// Props
const props = defineProps<{
  projectId: number
}>()

// Emits
const emit = defineEmits<{
  (e: 'success'): void
}>()

// 状态
const visible = defineModel<boolean>('visible', { default: false })
const step = ref(1)
const file = ref<File | null>(null)
const parseError = ref('')
const parsedCases = ref<ParsedCase[]>([])
const selectedRows = ref<number[]>([])
const importLoading = ref(false)
const importResult = ref<ExcelImportResult | null>(null)

// 枚举值
const methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
const priorities = ['P0', 'P1', 'P2', 'P3']
const bodyTypes = ['none', 'form-data', 'x-www-form-urlencoded', 'raw-json', 'raw-xml', 'raw-text']

// 计算属性
const errorCount = computed(() => parsedCases.value.filter(c => c._errors.length > 0).length)

// 方法
const handleFileChange = (fileList: any) => {
  if (fileList.length > 0) {
    file.value = fileList[0].file
    parseError.value = ''
  }
}

const downloadTemplate = () => {
  const blob = generateExcelTemplate()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = '用例导入模板.xlsx'
  a.click()
  URL.revokeObjectURL(url)
}

const handleParse = async () => {
  if (!file.value) return
  
  try {
    parseError.value = ''
    parsedCases.value = await parseExcelFile(file.value)
    step.value = 2
  } catch (error) {
    parseError.value = (error as Error).message
  }
}

const onSelectChange = (keys: (string | number)[]) => {
  selectedRows.value = keys as number[]
}

const deleteSelected = () => {
  parsedCases.value = parsedCases.value.filter((_, index) => !selectedRows.value.includes(index))
  selectedRows.value = []
}

const clearAll = () => {
  parsedCases.value = []
  selectedRows.value = []
}

const reupload = () => {
  step.value = 1
  file.value = null
  parsedCases.value = []
  selectedRows.value = []
  parseError.value = ''
}

const getRowClass = (record: ParsedCase) => {
  return record._errors.length > 0 ? 'row-error' : ''
}

const hasFieldError = (record: ParsedCase, field: string) => {
  return record._errors.some(e => e.includes(field))
}

const handleImport = async () => {
  if (errorCount.value > 0) {
    Message.warning('请先修正所有错误再导入')
    return
  }
  
  importLoading.value = true
  
  try {
    const result = await importExcelCases({
      cases: parsedCases.value.map(c => ({
        name: c.name,
        method: c.method,
        url: c.url,
        module: c.module,
        priority: c.priority,
        description: c.description,
        preconditions: c.preconditions,
        body_type: c.body_type,
        body_raw_content: c.body_raw_content,
        remark: c.remark,
        headers: c.headers,
        query_params: c.query_params,
        body_form: c.body_form,
        assertions: c.assertions,
      })),
      project_id: props.projectId,
    })
    
    importResult.value = result
    step.value = 3
    
    if (result.success > 0) {
      Message.success(`成功导入 ${result.success} 条用例`)
      emit('success')
    }
  } catch (error) {
    Message.error('导入失败：' + (error as Error).message)
  } finally {
    importLoading.value = false
  }
}

const handleClose = () => {
  step.value = 1
  file.value = null
  parsedCases.value = []
  selectedRows.value = []
  importResult.value = null
  parseError.value = ''
}

const handleFinish = () => {
  visible.value = false
  handleClose()
}
</script>

<style scoped>
.upload-section {
  padding: 20px 0;
}

.template-download {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.template-hint {
  color: var(--color-text-3);
  font-size: 13px;
}

.upload-area {
  width: 100%;
  padding: 40px;
  border: 2px dashed var(--color-border-2);
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-area:hover {
  border-color: var(--color-primary);
  background: var(--color-primary-light-1);
}

.upload-area .arco-icon {
  font-size: 48px;
  color: var(--color-text-3);
}

.upload-text {
  margin-top: 12px;
  font-size: 16px;
  color: var(--color-text-2);
}

.upload-hint {
  margin-top: 8px;
  font-size: 13px;
  color: var(--color-text-3);
}

.parse-error {
  margin-top: 16px;
  padding: 12px;
  background: var(--color-danger-light-1);
  border-radius: 4px;
  color: var(--color-danger);
  display: flex;
  align-items: center;
  gap: 8px;
}

.preview-section {
  max-height: 500px;
  overflow: auto;
}

.preview-toolbar {
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.preview-info {
  font-size: 14px;
  color: var(--color-text-2);
}

.error-count {
  color: var(--color-text-3);
}

.error-text {
  color: var(--color-danger);
}

.preview-actions {
  display: flex;
  gap: 8px;
}

.row-error {
  background: var(--color-danger-light-1);
}

.input-error {
  border-color: var(--color-danger);
}

.result-section {
  padding: 20px 0;
}

.result-summary {
  margin-bottom: 24px;
}

.error-list {
  margin-top: 24px;
}

.error-list-title {
  margin-bottom: 12px;
  font-weight: 500;
  color: var(--color-text-1);
}
</style>
```

- [ ] **Step 2: 验证组件可编译**

运行：`cd frontend && npm run build`（或 `npm run dev` 启动开发服务器）

预期：无编译错误

- [ ] **Step 3: 提交**

```bash
git add frontend/src/views/api-test/components/ExcelImportModal.vue
git commit -m "feat: 添加 Excel 导入弹窗组件"
```

---

## Task 8: 集成到用例列表

**Files:**
- Modify: `frontend/src/views/api-test/TestCaseList.vue`

- [ ] **Step 1: 添加导入按钮和组件**

在 `TestCaseList.vue` 中：

1. 导入组件：
```typescript
import ExcelImportModal from './components/ExcelImportModal.vue'
```

2. 添加状态：
```typescript
const showExcelImport = ref(false)
```

3. 在工具栏添加按钮（与「新增用例」按钮并列）：
```vue
<a-button type="primary" @click="showExcelImport = true">
  <template #icon><icon-import /></template>
  导入Excel
</a-button>
```

4. 添加组件：
```vue
<ExcelImportModal
  v-model:visible="showExcelImport"
  :project-id="currentProjectId"
  @success="handleImportSuccess"
/>
```

5. 添加成功回调：
```typescript
const handleImportSuccess = () => {
  // 刷新用例列表
  fetchTestCases()
}
```

- [ ] **Step 2: 验证功能可用**

1. 启动前端开发服务器
2. 进入用例列表页面
3. 点击「导入Excel」按钮
4. 验证弹窗正常显示
5. 下载模板并验证模板内容
6. 上传模板文件并验证解析结果
7. 确认导入并验证用例创建成功

- [ ] **Step 3: 提交**

```bash
git add frontend/src/views/api-test/TestCaseList.vue
git commit -m "feat: 集成 Excel 导入功能到用例列表"
```

---

## Task 9: 端到端测试

**Files:**
- 无新增文件

- [ ] **Step 1: 测试完整流程**

1. 启动后端服务：`cd server && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000`
2. 启动前端服务：`cd frontend && npm run dev`
3. 登录系统，进入接口测试用例列表
4. 点击「导入Excel」按钮
5. 下载模板，填写 2-3 条测试用例
6. 上传填写好的 Excel 文件
7. 验证预览表格正确显示
8. 修改预览表格中的数据
9. 点击「确认导入」
10. 验证导入结果正确显示
11. 关闭弹窗，验证用例列表已刷新
12. 点击导入的用例，验证数据正确

- [ ] **Step 2: 测试错误场景**

1. 上传空文件 - 验证错误提示
2. 上传格式错误的文件 - 验证错误提示
3. 填写缺少必填字段的数据 - 验证错误行标红
4. 填写无效枚举值 - 验证错误提示
5. 导入包含错误的数据 - 验证部分导入成功

- [ ] **Step 3: 提交测试结果**

```bash
git add .
git commit -m "test: 完成 Excel 导入功能端到端测试"
```

---

## 验收检查清单

- [ ] 用户能下载 Excel 模板
- [ ] 用户能上传 .xlsx/.xls 文件
- [ ] 前端正确解析 Excel 并展示预览表格
- [ ] 预览表格支持编辑
- [ ] 前端校验错误行标红显示
- [ ] 确认导入后后端正确创建用例
- [ ] 导入结果正确展示成功/失败数量
- [ ] 失败用例显示具体错误原因
- [ ] 导入成功后能在用例列表中看到新用例
- [ ] 点击导入的用例能正确显示所有数据

---

**最后更新**: 2026-05-18

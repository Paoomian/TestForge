import * as XLSX from 'xlsx'
import ExcelJS from 'exceljs'

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

export interface ParsedDataRule {
  name: string
  rule_type: string
  source: string
  expression: string
  default_value: string
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
  headers_json?: string
  params_json?: string
  assertions_json?: string
  data_rules_json?: string
  data_rules: ParsedDataRule[]
  remark?: string
  headers: ParsedHeader[]
  query_params: ParsedQueryParam[]
  body_form: ParsedBodyForm[]
  assertions: ParsedAssertion[]
  _row: number
  _errors: string[]
}

// 有效枚举值
const VALID_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
const VALID_PRIORITIES = ['P0', 'P1', 'P2', 'P3']
const VALID_BODY_TYPES = ['none', 'form-data', 'x-www-form-urlencoded', 'raw-json', 'raw-xml', 'raw-text']
const VALID_ASSERTION_TYPES = ['status_code', 'jsonpath', 'header', 'response_time', 'body_contains']
const VALID_ASSERTION_OPERATORS = [
  'equals', 'not_equals',
  'contains', 'not_contains',
  'greater_than', 'less_than',
  'greater_than_or_equals', 'less_than_or_equals',
  'regex',
  'exists', 'not_exists',
  'is_type',
  'length_equals', 'length_greater_than', 'length_less_than'
]

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
  '请求头': 'headers_json',
  '查询参数': 'params_json',
  '断言': 'assertions_json',
  '数据提取': 'data_rules_json',
  '备注': 'remark',
}

/**
 * 安全解析 JSON，失败返回 null
 */
function safeParseJson(str: string): any {
  if (!str || typeof str !== 'string') return null
  try {
    return JSON.parse(str.trim())
  } catch {
    return null
  }
}

/**
 * 解析 Headers JSON 字典
 * 格式: {"Content-Type":"application/json","Authorization":"Bearer xxx"}
 */
export function parseHeaders(jsonStr?: string): ParsedHeader[] {
  if (!jsonStr) return []
  const obj = safeParseJson(jsonStr)
  if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return []

  return Object.entries(obj).map(([key, value]) => ({
    enabled: true,
    key,
    value: String(value ?? ''),
    description: '',
  }))
}

/**
 * 解析 Query Params JSON 字典
 * 格式: {"page":"1","size":"10"}
 */
export function parseQueryParams(jsonStr?: string): ParsedQueryParam[] {
  if (!jsonStr) return []
  const obj = safeParseJson(jsonStr)
  if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return []

  return Object.entries(obj).map(([key, value]) => ({
    enabled: true,
    key,
    value: String(value ?? ''),
    description: '',
  }))
}

/**
 * 解析 Assertions JSON 数组
 * 格式: [{"type":"status_code","operator":"equals","expected":"200"},{"type":"jsonpath","field":"$.code","operator":"equals","expected":"0"}]
 */
export function parseAssertions(jsonStr?: string): ParsedAssertion[] {
  if (!jsonStr) return []
  const arr = safeParseJson(jsonStr)
  if (!Array.isArray(arr)) return []

  return arr.map((item: any) => ({
    assertion_type: String(item.type || '').trim().toLowerCase(),
    operator: String(item.operator || '').trim().toLowerCase(),
    field: String(item.field || '').trim(),
    expected: String(item.expected || '').trim(),
    description: '',
  }))
}

/**
 * 解析数据提取 JSON 数组（输出为 data_rules 格式）
 * 格式: [{"name":"token","source":"jsonpath","expression":"$.data.token","default_value":"","description":"提取token"}]
 */
export function parseDataRules(jsonStr?: string): ParsedDataRule[] {
  if (!jsonStr) return []
  const arr = safeParseJson(jsonStr)
  if (!Array.isArray(arr)) return []

  return arr.map((item: any) => ({
    name: String(item.name || '').trim(),
    rule_type: 'extract',
    source: String(item.source || 'jsonpath').trim().toLowerCase(),
    expression: String(item.expression || '').trim(),
    default_value: String(item.default_value || item.default || '').trim(),
    description: String(item.description || '').trim(),
  }))
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

  // 校验 JSON 格式
  if (parsed.headers_json) {
    const parsed2 = safeParseJson(parsed.headers_json)
    if (parsed2 === null) {
      errors.push('请求头JSON格式无效')
    } else if (typeof parsed2 !== 'object' || Array.isArray(parsed2)) {
      errors.push('请求头必须是JSON对象格式')
    }
  }

  if (parsed.params_json) {
    const parsed2 = safeParseJson(parsed.params_json)
    if (parsed2 === null) {
      errors.push('查询参数JSON格式无效')
    } else if (typeof parsed2 !== 'object' || Array.isArray(parsed2)) {
      errors.push('查询参数必须是JSON对象格式')
    }
  }

  if (parsed.assertions_json) {
    const parsed2 = safeParseJson(parsed.assertions_json)
    if (parsed2 === null) {
      errors.push('断言JSON格式无效')
    } else if (!Array.isArray(parsed2)) {
      errors.push('断言必须是JSON数组格式')
    }
  }

  // 校验断言内容
  parsed.assertions.forEach((assertion, index) => {
    if (assertion.assertion_type && !VALID_ASSERTION_TYPES.includes(assertion.assertion_type)) {
      errors.push(`断言${index + 1}类型无效：${assertion.assertion_type}`)
    }
    if (assertion.operator && !VALID_ASSERTION_OPERATORS.includes(assertion.operator)) {
      errors.push(`断言${index + 1}运算符无效：${assertion.operator}`)
    }
  })

  // 校验数据规则（提取类型）
  parsed.data_rules.forEach((rule, index) => {
    if (rule.rule_type === 'extract') {
      if (!rule.name) {
        errors.push(`数据规则${index + 1}变量名不能为空`)
      }
      if (rule.source && !['jsonpath', 'regex', 'header'].includes(rule.source)) {
        errors.push(`数据规则${index + 1}来源无效：${rule.source}`)
      }
      if (!rule.expression) {
        errors.push(`数据规则${index + 1}表达式不能为空`)
      }
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

        const parsedCases: ParsedCase[] = jsonData.map((row: any, index: number) => {
          const parsed: ParsedCase = {
            name: '',
            method: 'GET',
            url: '',
            module: '',
            priority: 'P2',
            description: '',
            preconditions: '',
            body_type: 'none',
            body_raw_content: '',
            headers_json: '',
            params_json: '',
            assertions_json: '',
            data_rules_json: '',
            data_rules: [],
            remark: '',
            headers: [],
            query_params: [],
            body_form: [],
            assertions: [],
            _row: index + 2,
            _errors: [],
          }

          // 构建列名映射（去除空格）
          const normalizedRow: Record<string, any> = {}
          for (const [key, value] of Object.entries(row)) {
            if (typeof key === 'string') {
              normalizedRow[key.trim()] = value
            }
          }

          // 映射主表字段
          for (const [excelCol, field] of Object.entries(COLUMN_MAP)) {
            let value = normalizedRow[excelCol]
            if (value === undefined) {
              // 尝试去除空格后匹配
              for (const [rowKey, rowValue] of Object.entries(normalizedRow)) {
                if (rowKey.replace(/\s+/g, '') === excelCol.replace(/\s+/g, '')) {
                  value = rowValue
                  break
                }
              }
            }
            // 转换为字符串并赋值
            if (value !== undefined && value !== null) {
              let strValue = String(value).trim()
              if (strValue !== '') {
                // 特殊处理 method 字段，统一转大写
                if (field === 'method') {
                  strValue = strValue.toUpperCase()
                }
                (parsed as any)[field] = strValue
              }
            }
          }

          if (parsed.method) {
            parsed.method = parsed.method.toUpperCase()
          }

          // 解析子表
          parsed.headers = parseHeaders(parsed.headers_json)
          parsed.query_params = parseQueryParams(parsed.params_json)
          parsed.assertions = parseAssertions(parsed.assertions_json)
          parsed.data_rules = parseDataRules(parsed.data_rules_json)

          // 校验
          parsed._errors = validateCase(parsed)

          return parsed
        })

        // 过滤掉空行（用例名称为空的行）
        const filteredCases = parsedCases.filter(c => c.name.trim() !== '')

        if (filteredCases.length === 0) {
          reject(new Error('Excel 文件没有有效数据行'))
          return
        }

        resolve(filteredCases)
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
 * 生成 Excel 模板（使用 exceljs 支持样式）
 */
export async function generateExcelTemplate(): Promise<Blob> {
  const workbook = new ExcelJS.Workbook()
  workbook.creator = 'TestForge'
  workbook.created = new Date()

  // ========== 用例模板 Sheet ==========
  const ws = workbook.addWorksheet('用例模板', {
    views: [{ state: 'frozen', ySplit: 1 }],
  })

  // 表头定义
  const headers = [
    '用例名称', '请求方法', '请求URL', '所属模块', '优先级',
    '描述', '前置条件', 'Body类型', 'Body内容',
    '请求头', '查询参数', '断言', '数据提取', '备注',
  ]

  // 列宽配置
  ws.columns = [
    { width: 16 }, { width: 10 }, { width: 30 }, { width: 12 }, { width: 8 },
    { width: 20 }, { width: 18 }, { width: 14 }, { width: 45 },
    { width: 45 }, { width: 35 }, { width: 80 }, { width: 80 }, { width: 18 },
  ]

  // 添加表头行
  const headerRow = ws.addRow(headers)

  // 表头样式：蓝色背景 + 白色字体 + 加粗 + 居中
  headerRow.eachCell((cell) => {
    cell.fill = {
      type: 'pattern',
      pattern: 'solid',
      fgColor: { argb: 'FF4472C4' },
    }
    cell.font = {
      bold: true,
      color: { argb: 'FFFFFFFF' },
      size: 12,
    }
    cell.alignment = {
      horizontal: 'center',
      vertical: 'middle',
    }
    cell.border = {
      top: { style: 'thin' },
      bottom: { style: 'thin' },
      left: { style: 'thin' },
      right: { style: 'thin' },
    }
  })
  headerRow.height = 24

  // 靠左对齐的列索引（1-based）：Body内容(9)、请求头(10)、查询参数(11)、断言(12)、数据提取(13)
  const leftAlignCols = [9, 10, 11, 12, 13]

  // 示例数据
  const exampleRows = [
    [
      '用户登录', 'POST', '/api/v1/auth/login', '认证模块', 'P0',
      '用户登录接口', '无', 'raw-json',
      '{"username":"admin","password":"123456"}',
      '{"Content-Type":"application/json","Authorization":"Bearer token123"}',
      '',
      JSON.stringify([
        { type: 'status_code', operator: 'equals', expected: '200', description: '状态码等于200' },
        { type: 'jsonpath', field: '$.code', operator: 'equals', expected: '0', description: '返回code为0表示成功' },
        { type: 'jsonpath', field: '$.data.token', operator: 'exists', expected: '', description: 'token字段存在' },
        { type: 'response_time', operator: 'less_than', expected: '1000', description: '响应时间小于1秒' },
        { type: 'header', field: 'Content-Type', operator: 'contains', expected: 'application/json', description: '响应头包含JSON类型' },
        { type: 'body_contains', operator: 'contains', expected: 'success', description: '响应体包含success' },
      ]),
      JSON.stringify([
        { name: 'token', source: 'jsonpath', expression: '$.data.token', default_value: '', description: '提取登录token' },
        { name: 'userId', source: 'jsonpath', expression: '$.data.user.id', default_value: '0', description: '提取用户ID' },
      ]),
      '首次登录需要验证码',
    ],
    [
      '获取用户列表', 'GET', '/api/v1/users', '用户模块', 'P1',
      '分页查询用户列表', '已登录', 'none', '',
      '{"Authorization":"Bearer {{token}}"}',
      '{"page":"1","size":"10","keyword":"test"}',
      JSON.stringify([
        { type: 'status_code', operator: 'equals', expected: '200' },
        { type: 'jsonpath', field: '$.data.list', operator: 'exists', expected: '' },
        { type: 'jsonpath', field: '$.data.total', operator: 'greater_than', expected: '0' },
      ]),
      JSON.stringify([
        { name: 'userList', source: 'jsonpath', expression: '$.data.list', default_value: '[]', description: '提取用户列表' },
        { name: 'total', source: 'jsonpath', expression: '$.data.total', default_value: '0', description: '提取总数' },
      ]),
      '',
    ],
    [
      '上传头像', 'PUT', '/api/v1/users/avatar', '用户模块', 'P2',
      '上传用户头像', '已登录', 'form-data',
      '{"file":"@avatar.png","type":"image"}',
      '{"Authorization":"Bearer {{token}}"}', '',
      JSON.stringify([
        { type: 'status_code', operator: 'equals', expected: '200' },
        { type: 'jsonpath', field: '$.data.url', operator: 'regex', expected: 'https?://.*', description: '返回有效的图片URL' },
      ]),
      JSON.stringify([
        { name: 'avatarUrl', source: 'jsonpath', expression: '$.data.url', default_value: '', description: '提取头像URL' },
        { name: 'contentType', source: 'header', expression: 'Content-Type', default_value: 'application/json', description: '提取响应头Content-Type' },
      ]),
      '支持 jpg/png 格式',
    ],
    [
      '删除用户', 'DELETE', '/api/v1/users/1001', '用户模块', 'P1',
      '删除指定用户', '已登录，用户存在', 'none', '',
      '{"Authorization":"Bearer {{token}}"}', '',
      JSON.stringify([
        { type: 'status_code', operator: 'equals', expected: '200' },
        { type: 'jsonpath', field: '$.code', operator: 'not_equals', expected: '-1', description: 'code不等于-1表示未失败' },
      ]),
      JSON.stringify([
        { name: 'deleteMsg', source: 'regex', expression: '"message":"(.*?)"', default_value: '', description: '用正则提取删除提示信息' },
      ]),
      '软删除',
    ],
  ]

  // 设置行样式的函数
  const applyRowStyle = (row: ExcelJS.Row) => {
    row.eachCell((cell, colNumber) => {
      cell.alignment = {
        horizontal: leftAlignCols.includes(colNumber) ? 'left' : 'center',
        vertical: 'middle',
        wrapText: true,
      }
      cell.border = {
        top: { style: 'thin' },
        bottom: { style: 'thin' },
        left: { style: 'thin' },
        right: { style: 'thin' },
      }
    })
  }

  // 添加示例数据行并设置样式
  exampleRows.forEach((rowData) => {
    const row = ws.addRow(rowData)
    applyRowStyle(row)
  })

  // 添加空行（预留20行供用户填写）并设置样式
  const emptyRow = new Array(headers.length).fill('')
  for (let i = 0; i < 20; i++) {
    const row = ws.addRow(emptyRow)
    applyRowStyle(row)
  }

  // ========== 填写说明 Sheet ==========
  const helpWs = workbook.addWorksheet('填写说明')

  // 设置列宽
  helpWs.columns = [
    { width: 20 }, { width: 8 }, { width: 40 }, { width: 50 },
  ]

  // 帮助数据
  const helpData = [
    ['字段说明'],
    [''],
    ['字段', '必填', '说明', '示例值'],
    ['用例名称', '是', '用例的名称，最大200字符', '用户登录'],
    ['请求方法', '是', 'HTTP请求方法（大写）', 'GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS'],
    ['请求URL', '是', '接口地址，支持相对路径', '/api/v1/auth/login'],
    ['所属模块', '否', '用例所属模块', '认证模块'],
    ['优先级', '否', '默认P2', 'P0(致命)/P1(严重)/P2(一般)/P3(轻微)'],
    ['描述', '否', '用例描述', '用户登录接口'],
    ['前置条件', '否', '执行前需要满足的条件', '已注册账号'],
    ['Body类型', '否', '请求体类型，默认none', 'none/form-data/x-www-form-urlencoded/raw-json/raw-xml/raw-text'],
    ['Body内容', '否', '请求体内容，JSON格式', '{"key":"value"}'],
    ['请求头', '否', 'JSON对象格式', '{"Content-Type":"application/json"}'],
    ['查询参数', '否', 'JSON对象格式，URL查询参数', '{"page":"1","size":"10"}'],
    ['断言', '否', 'JSON数组格式，详见下方说明', '[{"type":"status_code","operator":"equals","expected":"200"}]'],
    ['数据提取', '否', 'JSON数组格式，详见数据提取规则', '[{"name":"token","source":"jsonpath","expression":"$.data.token"}]'],
    ['备注', '否', '备注信息', ''],
    [''],
    ['断言规则说明'],
    [''],
    ['断言类型(type)', '说明', '需要field', 'expected示例'],
    ['status_code', 'HTTP状态码', '否', '200'],
    ['jsonpath', 'JSONPath提取值', '是($.data.id)', '123'],
    ['header', '响应头字段', '是(Content-Type)', 'application/json'],
    ['response_time', '响应时间(毫秒)', '否', '1000'],
    ['body_contains', '响应体包含文本', '否', 'success'],
    [''],
    ['比较方式(operator)', '说明'],
    ['equals', '等于'],
    ['not_equals', '不等于'],
    ['contains', '包含'],
    ['greater_than', '大于'],
    ['less_than', '小于'],
    ['regex', '正则匹配'],
    ['exists', '存在（不需要expected）'],
    [''],
    ['断言示例：'],
    ['状态码断言', '[{"type":"status_code","operator":"equals","expected":"200"}]'],
    ['JSON字段断言', '[{"type":"jsonpath","field":"$.code","operator":"equals","expected":"0"}]'],
    ['响应时间断言', '[{"type":"response_time","operator":"less_than","expected":"1000","description":"响应<1秒"}]'],
    ['响应头断言', '[{"type":"header","field":"Content-Type","operator":"contains","expected":"application/json"}]'],
    ['正文包含断言', '[{"type":"body_contains","operator":"contains","expected":"success"}]'],
    ['字段存在断言', '[{"type":"jsonpath","field":"$.data.token","operator":"exists","expected":""}]'],
    ['正则匹配断言', '[{"type":"jsonpath","field":"$.data.url","operator":"regex","expected":"https?://.*"}]'],
    [''],
    ['数据提取规则说明'],
    [''],
    ['提取来源(source)', '说明', 'expression示例', '说明'],
    ['jsonpath', 'JSONPath表达式提取', '$.data.token', '提取响应JSON中的token字段'],
    ['regex', '正则表达式提取', '"token":"(.*?)"', '用正则捕获组提取'],
    ['header', '响应头提取', 'Content-Type', '提取响应头字段值'],
    [''],
    ['数据提取示例：'],
    ['提取token', '[{"name":"token","source":"jsonpath","expression":"$.data.token","description":"提取登录token"}]'],
    ['正则提取', '[{"name":"code","source":"regex","expression":"\\"code\\":(\\\\d+)","description":"提取状态码"}]'],
    ['响应头提取', '[{"name":"contentType","source":"header","expression":"Content-Type","description":"提取Content-Type"}]'],
    ['多字段提取', '[{"name":"token","source":"jsonpath","expression":"$.data.token"},{"name":"userId","source":"jsonpath","expression":"$.data.user.id"}]'],
  ]

  // 添加数据行
  helpData.forEach((rowData) => {
    helpWs.addRow(rowData)
  })

  // 合并标题单元格
  helpWs.mergeCells('A1:D1')
  helpWs.mergeCells('A19:D19')
  helpWs.mergeCells('A40:D40')

  // 设置标题样式
  const titleRows = [1, 19, 40]
  titleRows.forEach((rowNum) => {
    const row = helpWs.getRow(rowNum)
    row.getCell(1).font = { bold: true, size: 14 }
  })

  // 为表格添加边框样式
  // 字段说明表格: 第4-18行（表头第4行 + 数据第5-18行）
  // 断言类型表格: 第21-26行（表头第21行 + 数据第22-26行）
  // 比较方式表格: 第29-35行（表头第29行 + 数据第30-35行）
  // 提取来源表格: 第41-44行（表头第41行 + 数据第42-44行）
  const tableRanges = [
    { start: 4, end: 18 },
    { start: 21, end: 26 },
    { start: 29, end: 35 },
    { start: 41, end: 44 },
  ]

  tableRanges.forEach(({ start, end }) => {
    for (let rowNum = start; rowNum <= end; rowNum++) {
      const row = helpWs.getRow(rowNum)
      // 确保行有数据
      if (row.hasValues) {
        row.eachCell({ includeEmpty: true }, (cell, colNumber) => {
          if (colNumber <= 4) {
            cell.border = {
              top: { style: 'thin' },
              bottom: { style: 'thin' },
              left: { style: 'thin' },
              right: { style: 'thin' },
            }
            cell.alignment = {
              vertical: 'middle',
              wrapText: true,
            }
          }
        })
      }
    }
  })

  // 生成 Blob
  const buffer = await workbook.xlsx.writeBuffer()
  return new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
}

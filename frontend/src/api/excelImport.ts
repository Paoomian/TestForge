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

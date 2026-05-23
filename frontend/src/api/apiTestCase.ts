import request from '@/utils/request'

// ==================== 子表接口 ====================

export interface HeaderItem {
  enabled: boolean
  key: string
  value: string
  description?: string
  sort_order?: number
}

export interface QueryParamItem {
  enabled: boolean
  key: string
  value: string
  description?: string
  sort_order?: number
}

export interface BodyFormItem {
  enabled: boolean
  key: string
  value: string
  param_type: 'text' | 'file'
  description?: string
  sort_order?: number
}

export interface BodyRawItem {
  content: string
}

export interface AssertionItem {
  assertion_type: 'status_code' | 'response_time' | 'jsonpath' | 'header' | 'body_contains'
  operator: 'equals' | 'not_equals' | 'contains' | 'greater_than' | 'less_than' | 'regex' | 'exists'
  field?: string
  expected?: string
  description?: string
  sort_order?: number
}

export interface DataRuleItem {
  name: string
  rule_type: 'extract' | 'static' | 'generate' | 'transform' | 'conditional'
  enabled?: boolean
  description?: string
  default_value?: string
  sort_order?: number
  // extract 类型专用
  source?: 'jsonpath' | 'regex' | 'header'
  expression?: string
  // static 类型专用
  static_value?: string
  // generate 类型专用
  generator?: 'timestamp' | 'uuid' | 'random_int' | 'random_string' | 'now'
  generator_params?: Record<string, any>
  // transform 类型专用
  source_variable?: string
  transform_type?: 'substring' | 'concat' | 'replace' | 'upper' | 'lower' | 'trim' | 'to_int' | 'to_string' | 'format_date'
  transform_params?: Record<string, any>
  // conditional 类型专用
  condition_variable?: string
  condition_operator?: 'equals' | 'not_equals' | 'contains' | 'is_empty' | 'is_not_empty' | 'greater_than' | 'less_than'
  condition_value?: string
  true_value?: string
  false_value?: string
}

export interface AuthConfig {
  auth_type: 'none' | 'bearer' | 'basic' | 'api_key'
  token?: string
  username?: string
  password?: string
  api_key_name?: string
  api_key_value?: string
  api_key_location?: 'header' | 'query'
}

// ==================== 主表接口 ====================

export interface APITestCase {
  id: number
  project_id: number
  environment_id?: number
  environment_name?: string
  case_number?: string
  module?: string
  name: string
  description?: string
  preconditions?: string
  remark?: string
  method: string
  url: string
  body_type: string
  auth_type: string
  setup_script?: string
  teardown_script?: string
  priority: string
  status: string
  creator_id?: number
  created_at: string
  updated_at?: string
  headers: HeaderItem[]
  query_params: QueryParamItem[]
  body_form: BodyFormItem[]
  body_raw?: BodyRawItem
  assertions: AssertionItem[]
  data_rules: DataRuleItem[]
  auth?: AuthConfig
}

export interface APITestCaseCreate {
  project_id: number
  environment_id?: number
  module?: string
  name: string
  description?: string
  preconditions?: string
  remark?: string
  method?: string
  url?: string
  body_type?: string
  auth_type?: string
  setup_script?: string
  teardown_script?: string
  priority?: string
  status?: string
  headers?: HeaderItem[]
  query_params?: QueryParamItem[]
  body_form?: BodyFormItem[]
  body_raw?: BodyRawItem
  assertions?: AssertionItem[]
  data_rules?: DataRuleItem[]
  auth?: AuthConfig
}

export interface APITestCaseUpdate {
  environment_id?: number
  module?: string
  name?: string
  description?: string
  preconditions?: string
  remark?: string
  method?: string
  url?: string
  body_type?: string
  auth_type?: string
  setup_script?: string
  teardown_script?: string
  priority?: string
  status?: string
  headers?: HeaderItem[]
  query_params?: QueryParamItem[]
  body_form?: BodyFormItem[]
  body_raw?: BodyRawItem
  assertions?: AssertionItem[]
  data_rules?: DataRuleItem[]
  auth?: AuthConfig
}

export interface ModuleTree {
  project_id: number
  modules: string[]
}

// ==================== cURL导入 ====================

export interface CurlParseResult {
  method: string
  url: string
  headers: HeaderItem[]
  query_params: QueryParamItem[]
  body_type: string
  body_raw_content: string
  body_form: BodyFormItem[]
  auth_type: string
  auth?: AuthConfig
}

// ==================== 环境 ====================

export interface Environment {
  id: number
  project_id: number
  name: string
  base_url?: string
  variables: Record<string, string>
  created_at: string
  updated_at?: string
}

export interface EnvironmentCreate {
  project_id: number
  name: string
  base_url?: string
  variables?: Record<string, string>
}

export interface EnvironmentUpdate {
  name?: string
  base_url?: string
  variables?: Record<string, string>
}

// ==================== 模板 ====================

export interface TestCaseTemplate {
  name: string
  description: string
  method: string
  url: string
  headers?: HeaderItem[]
  query_params?: QueryParamItem[]
  body_type?: string
  body_raw_content?: string
  assertions?: AssertionItem[]
  priority?: string
}

// ==================== API 函数 ====================

export const getTestCases = (params?: {
  skip?: number
  limit?: number
  project_id?: number
  module?: string
  keyword?: string
  priority?: string
  status?: string
}) => {
  return request<APITestCase[]>({
    url: '/api-test-cases',
    method: 'get',
    params
  })
}

export const createTestCase = (data: APITestCaseCreate) => {
  return request<APITestCase>({
    url: '/api-test-cases',
    method: 'post',
    data
  })
}

export const getTestCase = (id: number) => {
  return request<APITestCase>({
    url: `/api-test-cases/${id}`,
    method: 'get'
  })
}

export const updateTestCase = (id: number, data: APITestCaseUpdate) => {
  return request<APITestCase>({
    url: `/api-test-cases/${id}`,
    method: 'put',
    data
  })
}

export const deleteTestCase = (id: number) => {
  return request({
    url: `/api-test-cases/${id}`,
    method: 'delete'
  })
}

export const batchDelete = (case_ids: number[]) => {
  return request({
    url: '/api-test-cases/batch-delete',
    method: 'post',
    data: { case_ids }
  })
}

export const copyTestCase = (id: number) => {
  return request<APITestCase>({
    url: `/api-test-cases/${id}/copy`,
    method: 'post'
  })
}

export const getModuleTree = (project_id?: number) => {
  return request<ModuleTree[]>({
    url: '/api-test-cases/modules/tree',
    method: 'get',
    params: { project_id }
  })
}

export const createModule = (project_id: number, module: string) => {
  return request({
    url: '/api-test-cases/modules',
    method: 'post',
    data: { project_id, module }
  })
}

export const deleteModule = (project_id: number, module: string) => {
  return request({
    url: '/api-test-cases/modules',
    method: 'delete',
    params: { project_id, module }
  })
}

export const renameModule = (project_id: number, old_module: string, new_module: string) => {
  return request({
    url: '/api-test-cases/modules',
    method: 'put',
    data: { project_id, old_module, new_module }
  })
}

export const importCurl = (curl_command: string) => {
  return request<CurlParseResult>({
    url: '/api-test-cases/import-curl',
    method: 'post',
    data: { curl_command }
  })
}

export const getTemplates = () => {
  return request<TestCaseTemplate[]>({
    url: '/api-test-cases/templates',
    method: 'get'
  })
}

// ==================== 调试执行 ====================

export interface RunRequest {
  environment_id?: number
  variables?: Record<string, string>
}

export interface AssertionRunResult {
  assertion_type: string
  field?: string
  operator: string
  expected: string
  actual?: string
  passed: boolean
  error?: string
}

export interface RunResult {
  status: 'pass' | 'fail' | 'error'
  request_snapshot?: Record<string, any>
  response_info?: {
    status_code: number
    headers: Record<string, string>
    body: string
    elapsed_ms: number
    size_bytes: number
    truncated: boolean
  }
  assertions: AssertionRunResult[]
  extracted_variables: Record<string, string>
  data_rule_variables: Record<string, string>
  script_output: Record<string, any>
  error_message?: string
  duration_ms: number
}

export const runTestCase = (caseId: number, data: RunRequest) => {
  return request<RunResult>({
    url: `/test-runner/${caseId}/run`,
    method: 'post',
    data
  })
}

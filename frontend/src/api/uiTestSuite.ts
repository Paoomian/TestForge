import request from '@/utils/request'

/** UI 任务配置 */
export interface UITestSuite {
  id: number
  project_id: number
  project_name?: string
  name: string
  description?: string
  case_ids: number[]
  case_count: number
  environment_id?: number
  environment_name?: string
  failure_strategy: string
  browser: string
  viewport_width: number
  viewport_height: number
  tags: string[]
  created_at: string
  updated_at?: string
}

/** 创建 UI 任务配置参数 */
export interface UITestSuiteCreate {
  project_id: number
  name: string
  description?: string
  case_ids: number[]
  environment_id?: number
  failure_strategy: string
  browser: string
  viewport_width: number
  viewport_height: number
  tags?: string[]
}

/** 更新 UI 任务配置参数 */
export interface UITestSuiteUpdate {
  name?: string
  description?: string
  case_ids?: number[]
  environment_id?: number
  failure_strategy?: string
  browser?: string
  viewport_width?: number
  viewport_height?: number
  tags?: string[]
}

/** 获取 UI 任务配置列表 */
export function getUITestSuites(params?: {
  project_id?: number
  keyword?: string
  page?: number
  page_size?: number
}) {
  return request.get('/ui-test-suites', { params })
}

/** 获取 UI 任务配置详情 */
export function getUITestSuite(suiteId: number) {
  return request.get<UITestSuite>(`/ui-test-suites/${suiteId}`)
}

/** 创建 UI 任务配置 */
export function createUITestSuite(data: UITestSuiteCreate) {
  return request.post<UITestSuite>('/ui-test-suites', data)
}

/** 更新 UI 任务配置 */
export function updateUITestSuite(suiteId: number, data: UITestSuiteUpdate) {
  return request.put<UITestSuite>(`/ui-test-suites/${suiteId}`, data)
}

/** 删除 UI 任务配置 */
export function deleteUITestSuite(suiteId: number) {
  return request.delete(`/ui-test-suites/${suiteId}`)
}

/** 批量删除 UI 任务配置 */
export function batchDeleteUITestSuites(suiteIds: number[]) {
  return request.post('/ui-test-suites/batch-delete', { suite_ids: suiteIds })
}

/** 执行 UI 任务配置 */
export function runUITestSuite(suiteId: number) {
  return request.post<{ id: number; name: string }>(`/ui-test-suites/${suiteId}/run`)
}

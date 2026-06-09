import request from '@/utils/request'

/** UI批量执行创建参数 */
export interface UIBatchRunCreate {
  case_ids: number[]
  environment_id?: number
  failure_strategy: string
  browser: string
  viewport_width: number
  viewport_height: number
}

/** UI批量执行任务 */
export interface UIBatchRun {
  id: number
  name: string
  test_type: string
  status: string
  total_count: number
  pass_count: number
  fail_count: number
  error_count: number
  duration: number | null
  created_at: string
  details?: UIBatchRunDetail[]
}

/** UI批量执行详情 */
export interface UIBatchRunDetail {
  id: number
  case_id: number
  case_name: string
  execution_order: number
  status: string
  screenshot?: string
  error_message?: string
  duration_ms: number
  script_output?: {
    steps?: UIBatchStepResult[]
  }
  steps?: UIBatchStepResult[]
}

/** UI步骤执行结果 */
export interface UIBatchStepResult {
  step_order: number
  action: string
  status: string
  message?: string
  screenshot?: string
  duration_ms: number
}

/** 创建UI批量执行任务 */
export function createUIBatchRun(data: UIBatchRunCreate) {
  return request.post<UIBatchRun>('/batch-runs', {
    ...data,
    test_type: 'ui_batch',
  })
}

/** 获取UI批量执行任务列表 */
export function getUIBatchRuns(params?: { page?: number; page_size?: number; status?: string }) {
  return request.get('/batch-runs', {
    params: { test_type: 'ui_batch', ...params },
  })
}

/** 获取UI批量执行任务详情 */
export function getUIBatchRun(runId: number) {
  return request.get<UIBatchRun>(`/batch-runs/${runId}`)
}

/** 获取UI批量执行任务详情（含步骤） */
export function getUIBatchRunDetail(runId: number, detailId: number) {
  return request.get<UIBatchRunDetail>(`/batch-runs/${runId}/details/${detailId}`)
}

/** 取消UI批量执行任务 */
export function cancelUIBatchRun(runId: number) {
  return request.post(`/batch-runs/${runId}/cancel`)
}

/** 删除UI批量执行任务 */
export function deleteUIBatchRun(runId: number) {
  return request.delete(`/batch-runs/${runId}`)
}

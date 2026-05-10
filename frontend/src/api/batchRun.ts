import request from '@/utils/request'

// ==================== 类型定义 ====================

export interface BatchRunCreate {
  case_ids: number[]
  environment_id?: number
  concurrency: 1 | 3 | 5 | 10
  failure_strategy: 'continue' | 'stop'
  variables?: Record<string, string>
}

export interface CaseDetailSummary {
  id: number
  case_id: number
  case_name?: string
  case_number?: string
  execution_order: number
  status: 'pending' | 'running' | 'pass' | 'fail' | 'error' | 'skipped'
  duration_ms: number
  api_duration_ms?: number
  status_code?: number
  error_message?: string
}

export interface BatchRunInfo {
  id: number
  project_id: number
  name: string
  status: 'pending' | 'running' | 'done' | 'error' | 'cancelled'
  case_ids: number[]
  environment_id?: number
  concurrency: number
  failure_strategy: string
  variables: Record<string, string>
  total_count: number
  pass_count: number
  fail_count: number
  error_count: number
  progress: number
  celery_task_id?: string
  start_time?: string
  end_time?: string
  duration?: number
  creator_id?: number
  created_at: string
  details: CaseDetailSummary[]
}

export interface BatchRunListItem {
  id: number
  name: string
  status: string
  concurrency: number
  failure_strategy: string
  total_count: number
  pass_count: number
  fail_count: number
  error_count: number
  progress: number
  start_time?: string
  end_time?: string
  duration?: number
  creator_id?: number
  created_at: string
}

export interface CaseDetailFull {
  id: number
  test_run_id: number
  case_id: number
  case_name?: string
  case_number?: string
  execution_order: number
  status: string
  request_snapshot?: Record<string, any>
  response_info?: Record<string, any>
  assertions: any[]
  extracted_vars: Record<string, string>
  script_output: Record<string, any>
  error_message?: string
  duration_ms: number
  started_at?: string
  finished_at?: string
}

export interface WSMessage {
  type: 'task_start' | 'case_start' | 'case_finish' | 'task_finish' | 'task_cancelled' | 'ping'
  task_id?: number
  detail_id?: number
  case_name?: string
  order?: number
  status?: string
  duration_ms?: number
  total?: number
  pass_count?: number
  fail_count?: number
  error_count?: number
}

// ==================== API 函数 ====================

export const createBatchRun = (data: BatchRunCreate) => {
  return request<BatchRunInfo>({
    url: '/batch-runs',
    method: 'post',
    data
  })
}

export const getBatchRuns = (params?: {
  page?: number
  page_size?: number
  status?: string
}) => {
  return request<{ total: number; page: number; page_size: number; items: BatchRunListItem[] }>({
    url: '/batch-runs',
    method: 'get',
    params
  })
}

export const getBatchRun = (id: number) => {
  return request<BatchRunInfo>({
    url: `/batch-runs/${id}`,
    method: 'get'
  })
}

export const getBatchRunDetail = (runId: number, detailId: number) => {
  return request<CaseDetailFull>({
    url: `/batch-runs/${runId}/details/${detailId}`,
    method: 'get'
  })
}

export const cancelBatchRun = (id: number) => {
  return request({
    url: `/batch-runs/${id}/cancel`,
    method: 'post'
  })
}

export const deleteBatchRun = (id: number) => {
  return request({
    url: `/batch-runs/${id}`,
    method: 'delete'
  })
}

// ==================== WebSocket ====================

export const connectBatchWS = (
  runId: number,
  onMessage: (msg: WSMessage) => void,
  onClose?: () => void,
  onError?: (err: Event) => void
): WebSocket => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const ws = new WebSocket(`${protocol}//${window.location.host}/ws/batch/${runId}`)

  ws.onmessage = (event) => {
    try {
      const msg: WSMessage = JSON.parse(event.data)
      if (msg.type !== 'ping') {
        onMessage(msg)
      }
    } catch (e) {
      console.error('WebSocket 消息解析失败:', e)
    }
  }

  ws.onclose = () => {
    onClose?.()
  }

  ws.onerror = (err) => {
    onError?.(err)
  }

  return ws
}

import request from '@/utils/request'

// ========== 类型定义 ==========

export interface UIStep {
  id: string
  order: number
  action: string
  target?: {
    selector?: string
    xpath?: string
    text?: string
    tagName?: string
    rect?: { x: number; y: number; width: number; height: number }
    attributes?: Record<string, string | undefined>
  }
  url?: string
  value?: string
  key?: string
  screenshot?: string
  timestamp?: number
  waitBefore?: number
  timeout?: number
  // 拖拽操作专用
  from?: { x: number; y: number }
  to?: { x: number; y: number }
  // 新窗口操作专用
  from_url?: string
  // 等待操作专用
  waitMs?: number
}

export interface UICase {
  id: number
  project_id: number
  case_number?: string
  module?: string
  name: string
  description?: string
  priority: string  // P0/P1/P2/P3
  steps: UIStep[]
  locators: Record<string, unknown>
  assertions: Record<string, unknown>[]
  base_url?: string
  browser_config?: Record<string, unknown>
  created_at: string
  updated_at?: string
}

export interface RecordingSession {
  session_id: string
  status: string
  url: string
  websocket_url: string
}

export interface RecordingStartParams {
  url: string
  project_id: number
  environment_id?: number
  viewport_width?: number
  viewport_height?: number
  user_agent?: string
}

export interface RecordingStopParams {
  name: string
  description?: string
  project_id: number
  save_to_project?: boolean
  steps?: UIStep[]
}

// ========== API 函数 ==========

/**
 * 获取 UI 用例列表
 */
export function getUICaseList(projectId: number, skip = 0, limit = 100, filters?: { keyword?: string; priority?: string; module?: string }) {
  return request.get<UICase[]>('/ui-cases/', {
    params: { project_id: projectId, skip, limit, ...filters }
  })
}

/**
 * 获取 UI 用例模块树
 */
export function getUICaseModules(projectId: number) {
  return request.get<any[]>('/ui-cases/modules/tree', {
    params: { project_id: projectId }
  })
}

/**
 * 获取 UI 用例详情
 */
export function getUICase(id: number) {
  return request.get<UICase>(`/ui-cases/${id}`)
}

/**
 * 创建 UI 用例
 */
export function createUICase(data: { project_id: number; name: string; description?: string; steps?: UIStep[] }) {
  return request.post<UICase>('/ui-cases/', data)
}

/**
 * 更新 UI 用例
 */
export function updateUICase(id: number, data: Partial<UICase>) {
  return request.put<UICase>(`/ui-cases/${id}`, data)
}

/**
 * 删除 UI 用例
 */
export function deleteUICase(id: number) {
  return request.delete(`/ui-cases/${id}`)
}

// ========== 录制相关 API ==========

/**
 * 启动录制会话（浏览器启动较慢，超时设为50秒）
 */
export function startRecording(data: RecordingStartParams) {
  return request.post<RecordingSession>('/ui-recordings/start', data, { timeout: 50000 })
}

/**
 * 停止录制并保存用例
 */
export function stopRecording(sessionId: string, data: RecordingStopParams) {
  return request.post(`/ui-recordings/stop?session_id=${sessionId}`, data)
}

/**
 * 获取录制会话状态
 */
export function getRecordingStatus(sessionId: string) {
  return request.get(`/ui-recordings/status/${sessionId}`)
}

/**
 * 删除录制会话
 */
export function deleteRecordingSession(sessionId: string) {
  return request.delete(`/ui-recordings/${sessionId}`)
}

/**
 * 保存录制为用例
 */
export function saveRecordingAsCase(sessionId: string, data: { name: string; project_id: number; description?: string }) {
  return request.post(`/ui-recordings/save?session_id=${sessionId}`, data)
}

// ========== 执行相关 API ==========

export interface RunResult {
  status: string
  total: number
  passed: number
  failed: number
  results: StepResult[]
  error?: string
}

export interface StepResult {
  step: number
  action: string
  success: boolean
  message: string
  screenshot?: string
  duration: number
}

/**
 * 执行单个用例
 */
export function runUICase(caseId: number) {
  return request.post<RunResult>(`/ui-runner/run/${caseId}`)
}

/**
 * 执行自定义步骤（用于调试）
 */
export function runCustomSteps(steps: UIStep[], baseUrl?: string) {
  return request.post<RunResult>('/ui-runner/run-steps', { steps, base_url: baseUrl })
}

/**
 * 创建 WebSocket 连接（录制用）
 */
export function createRecordingWebSocket(sessionId: string): WebSocket {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/ws/ui-record/${sessionId}`
  return new WebSocket(wsUrl)
}

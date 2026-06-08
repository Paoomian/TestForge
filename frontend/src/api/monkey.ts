import request from '@/utils/request'

/** 设备信息 */
export interface DeviceInfo {
  serial: string
  status: string
  model: string
}

/** Monkey 配置 */
export interface MonkeyConfig {
  device_serial: string
  event_count: number
  interval: number
  seed?: number | null
  package?: string | null
  pct_touch: number
  pct_motion: number
  pct_trackball: number
  pct_nav: number
  pct_majornav: number
  pct_syskeys: number
  pct_appswitch: number
  pct_anyevent: number
}

/** Monkey 任务响应 */
export interface MonkeyTaskResponse {
  task_id: string
  device_serial: string
  status: string
}

/** 获取已连接设备列表 */
export function getDevices() {
  return request.get<DeviceInfo[]>('/monkey/devices')
}

/** 启动 Monkey 测试 */
export function startMonkey(config: MonkeyConfig) {
  return request.post<MonkeyTaskResponse>('/monkey/start', config)
}

/** 停止 Monkey 测试 */
export function stopMonkey(taskId: string) {
  return request.post('/monkey/stop', null, { params: { task_id: taskId } })
}

/** 获取任务状态 */
export function getMonkeyStatus(taskId: string) {
  return request.get(`/monkey/status/${taskId}`)
}

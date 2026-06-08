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

/** Monkey 预设 */
export interface MonkeyPreset {
  id: number
  name: string
  pct_touch: number
  pct_motion: number
  pct_trackball: number
  pct_nav: number
  pct_majornav: number
  pct_syskeys: number
  pct_appswitch: number
  pct_anyevent: number
  event_count: number
  interval: number
  created_at: string
  updated_at: string
}

/** 创建预设参数 */
export interface MonkeyPresetCreate {
  name: string
  pct_touch: number
  pct_motion: number
  pct_trackball: number
  pct_nav: number
  pct_majornav: number
  pct_syskeys: number
  pct_appswitch: number
  pct_anyevent: number
  event_count: number
  interval: number
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

/** 获取默认预设模板 */
export function getDefaultMonkeyPresets() {
  return request.get<MonkeyPreset[]>('/monkey/presets/default')
}

/** 获取用户预设列表 */
export function getMonkeyPresets() {
  return request.get<MonkeyPreset[]>('/monkey/presets')
}

/** 创建预设 */
export function createMonkeyPreset(data: MonkeyPresetCreate) {
  return request.post<MonkeyPreset>('/monkey/presets', data)
}

/** 删除预设 */
export function deleteMonkeyPreset(id: number) {
  return request.delete(`/monkey/presets/${id}`)
}

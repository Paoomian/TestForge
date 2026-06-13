import request from '@/utils/request'

export interface ScheduledTask {
  id: number
  name: string
  task_type: string
  suite_id: number
  suite_name: string | null
  environment_id: number | null
  environment_name: string | null
  concurrency: number
  failure_strategy: string
  variables: Record<string, string>
  cron_expression: string
  enabled: boolean
  last_run_at: string | null
  next_run_at: string | null
  creator_id: number | null
  created_at: string
  updated_at: string | null
}

export interface ScheduledTaskCreate {
  name: string
  task_type: string
  suite_id: number
  environment_id?: number | null
  concurrency?: number
  failure_strategy?: string
  variables?: Record<string, string>
  cron_expression: string
  enabled?: boolean
}

export interface ScheduledTaskUpdate {
  name?: string
  task_type?: string
  suite_id?: number
  environment_id?: number | null
  concurrency?: number
  failure_strategy?: string
  variables?: Record<string, string>
  cron_expression?: string
  enabled?: boolean
}

/** 获取定时任务列表 */
export function getScheduledTasks(params?: {
  page?: number
  page_size?: number
  enabled?: boolean
  task_type?: string
}) {
  return request<{ total: number; page: number; page_size: number; items: ScheduledTask[] }>({
    url: '/scheduled-tasks',
    method: 'get',
    params,
  })
}

/** 创建定时任务 */
export function createScheduledTask(data: ScheduledTaskCreate) {
  return request<ScheduledTask>({
    url: '/scheduled-tasks',
    method: 'post',
    data,
  })
}

/** 更新定时任务 */
export function updateScheduledTask(id: number, data: ScheduledTaskUpdate) {
  return request<ScheduledTask>({
    url: `/scheduled-tasks/${id}`,
    method: 'put',
    data,
  })
}

/** 删除定时任务 */
export function deleteScheduledTask(id: number) {
  return request({
    url: `/scheduled-tasks/${id}`,
    method: 'delete',
  })
}

/** 启用/禁用定时任务 */
export function toggleScheduledTask(id: number) {
  return request<{ message: string; enabled: boolean }>({
    url: `/scheduled-tasks/${id}/toggle`,
    method: 'post',
  })
}

/** 立即执行 */
export function runScheduledTaskNow(id: number) {
  return request({
    url: `/scheduled-tasks/${id}/run-now`,
    method: 'post',
  })
}

/** 获取接口测试套件列表 */
export function getTestSuites(params?: { page?: number; page_size?: number }) {
  return request<{ total: number; items: { id: number; name: string }[] }>({
    url: '/test-suites',
    method: 'get',
    params: { page: 1, page_size: 100, ...params },
  })
}

/** 获取 UI 测试套件列表 */
export function getUITestSuites(params?: { page?: number; page_size?: number }) {
  return request<{ total: number; items: { id: number; name: string }[] }>({
    url: '/ui-test-suites',
    method: 'get',
    params: { page: 1, page_size: 100, ...params },
  })
}

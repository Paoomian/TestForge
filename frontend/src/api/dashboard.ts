import request from '@/utils/request'

/** 统计数据 */
export interface DashboardStats {
  project_count: number
  ui_case_count: number
  api_case_count: number
  today_run_count: number
  total_run_count: number
  last_run: {
    id: number
    name: string
    status: string
    created_at: string
  } | null
}

/** 最近执行记录 */
export interface RecentRun {
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
}

/** 执行趋势 */
export interface TrendItem {
  date: string
  total: number
  pass: number
  fail: number
  error: number
}

/** 通过率 */
export interface PassRate {
  total: number
  pass: number
  fail: number
  error: number
  pass_rate: number
}

/** 用例分布 */
export interface CaseDistribution {
  name: string
  value: number
}

/** 获取统计数据 */
export function getDashboardStats() {
  return request.get<DashboardStats>('/dashboard/stats')
}

/** 获取最近执行记录 */
export function getRecentRuns(limit = 10) {
  return request.get<RecentRun[]>('/dashboard/recent-runs', { params: { limit } })
}

/** 获取执行趋势 */
export function getRunTrend(days = 7) {
  return request.get<TrendItem[]>('/dashboard/run-trend', { params: { days } })
}

/** 获取通过率 */
export function getPassRate() {
  return request.get<PassRate>('/dashboard/pass-rate')
}

/** 获取用例分布 */
export function getCaseDistribution() {
  return request.get<CaseDistribution[]>('/dashboard/case-distribution')
}

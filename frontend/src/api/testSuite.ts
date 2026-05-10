import request from '@/utils/request'

// ==================== 类型定义 ====================

export interface TestSuiteCreate {
  project_id: number
  name: string
  description?: string
  case_ids: number[]
  environment_id?: number
  concurrency?: 1 | 3 | 5 | 10
  failure_strategy?: 'continue' | 'stop'
  variables?: Record<string, string>
  tags?: string[]
}

export interface TestSuiteUpdate {
  name?: string
  description?: string
  case_ids?: number[]
  environment_id?: number
  concurrency?: 1 | 3 | 5 | 10
  failure_strategy?: 'continue' | 'stop'
  variables?: Record<string, string>
  tags?: string[]
}

export interface TestSuiteInfo {
  id: number
  project_id: number
  name: string
  description?: string
  case_ids: number[]
  case_count: number
  environment_id?: number
  environment_name?: string
  concurrency: number
  failure_strategy: string
  variables: Record<string, string>
  tags: string[]
  creator_id?: number
  created_at: string
  updated_at?: string
}

export interface TestSuiteListItem {
  id: number
  project_id: number
  project_name?: string
  name: string
  description?: string
  case_count: number
  environment_name?: string
  concurrency: number
  failure_strategy: string
  tags: string[]
  creator_id?: number
  created_at: string
}

export interface TestSuiteRunRequest {
  environment_id?: number
  concurrency?: 1 | 3 | 5 | 10
  failure_strategy?: 'continue' | 'stop'
  variables?: Record<string, string>
}

// ==================== API 函数 ====================

export const createTestSuite = (data: TestSuiteCreate) => {
  return request<TestSuiteInfo>({
    url: '/test-suites',
    method: 'post',
    data
  })
}

export const getTestSuites = (params?: {
  project_id?: number
  keyword?: string
  tag?: string
  page?: number
  page_size?: number
}) => {
  return request<{ total: number; page: number; page_size: number; items: TestSuiteListItem[] }>({
    url: '/test-suites',
    method: 'get',
    params
  })
}

export const getTestSuite = (id: number) => {
  return request<TestSuiteInfo>({
    url: `/test-suites/${id}`,
    method: 'get'
  })
}

export const updateTestSuite = (id: number, data: TestSuiteUpdate) => {
  return request<TestSuiteInfo>({
    url: `/test-suites/${id}`,
    method: 'put',
    data
  })
}

export const deleteTestSuite = (id: number) => {
  return request({
    url: `/test-suites/${id}`,
    method: 'delete'
  })
}

export const copyTestSuite = (id: number) => {
  return request<TestSuiteInfo>({
    url: `/test-suites/${id}/copy`,
    method: 'post'
  })
}

export const runTestSuite = (id: number, data?: TestSuiteRunRequest) => {
  return request<{ id: number; message: string }>({
    url: `/test-suites/${id}/run`,
    method: 'post',
    data
  })
}

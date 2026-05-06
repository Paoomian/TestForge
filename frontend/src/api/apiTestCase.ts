import request from '@/utils/request'

// ==================== TypeScript 接口定义 ====================

export interface APITestCase {
  id: number
  project_id: number
  module?: string
  name: string
  description?: string
  method: string
  url: string
  headers: Record<string, any>
  body?: string
  query_params: Record<string, any>
  variables: Record<string, any>
  setup_script?: string
  teardown_script?: string
  assertions: Assertion[]
  tags: string[]
  priority: string
  status: string
  version: number
  creator_id?: number
  created_at: string
  updated_at?: string
}

export interface Assertion {
  id: string
  type: 'status_code' | 'jsonpath' | 'xpath' | 'header' | 'response_time' | 'schema'
  operator: 'equals' | 'contains' | 'not_equals' | 'greater_than' | 'less_than' | 'regex' | 'exists'
  field?: string
  expected: any
  description?: string
}

export interface APITestCaseCreate {
  project_id: number
  module?: string
  name: string
  description?: string
  method: string
  url: string
  headers?: Record<string, any>
  body?: string
  query_params?: Record<string, any>
  variables?: Record<string, any>
  setup_script?: string
  teardown_script?: string
  assertions?: Assertion[]
  tags?: string[]
  priority?: string
  status?: string
}

export interface APITestCaseUpdate {
  name?: string
  description?: string
  module?: string
  method?: string
  url?: string
  headers?: Record<string, any>
  body?: string
  query_params?: Record<string, any>
  variables?: Record<string, any>
  setup_script?: string
  teardown_script?: string
  assertions?: Assertion[]
  tags?: string[]
  priority?: string
  status?: string
}

export interface APITestCaseHistory {
  id: number
  test_case_id: number
  version: number
  snapshot: Record<string, any>
  change_description?: string
  changed_by?: number
  created_at: string
}

export interface ModuleTree {
  project_id: number
  modules: string[]
}

// ==================== Mock 数据 ====================

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

const mockCases: APITestCase[] = [
  {
    id: 1,
    project_id: 1,
    module: '用户模块/登录',
    name: '手机号登录',
    description: '使用手机号和验证码登录',
    method: 'POST',
    url: '/api/v1/auth/login',
    headers: { 'Content-Type': 'application/json' },
    body: '{"phone": "13800138000", "code": "123456"}',
    query_params: {},
    variables: {},
    assertions: [
      {
        id: '1',
        type: 'status_code',
        operator: 'equals',
        expected: 200,
        description: '状态码为200'
      }
    ],
    tags: ['登录', '核心功能'],
    priority: 'high',
    status: 'active',
    version: 1,
    creator_id: 1,
    created_at: '2024-01-01T10:00:00Z'
  },
  {
    id: 2,
    project_id: 1,
    module: '用户模块/注册',
    name: '用户注册',
    description: '新用户注册接口',
    method: 'POST',
    url: '/api/v1/auth/register',
    headers: { 'Content-Type': 'application/json' },
    body: '{"username": "test", "password": "123456"}',
    query_params: {},
    variables: {},
    assertions: [],
    tags: ['注册'],
    priority: 'medium',
    status: 'active',
    version: 1,
    creator_id: 1,
    created_at: '2024-01-02T10:00:00Z'
  }
]

const mockHistories: APITestCaseHistory[] = [
  {
    id: 1,
    test_case_id: 1,
    version: 1,
    snapshot: {},
    change_description: '初始版本',
    changed_by: 1,
    created_at: '2024-01-01T10:00:00Z'
  }
]

// ==================== API 函数 ====================

export const getTestCases = (params?: {
  skip?: number
  limit?: number
  project_id?: number
  module?: string
  keyword?: string
  tags?: string
  priority?: string
  status?: string
}) => {
  if (USE_MOCK) {
    return Promise.resolve(mockCases.filter(c => {
      if (params?.project_id && c.project_id !== params.project_id) return false
      if (params?.module && !c.module?.startsWith(params.module)) return false
      if (params?.keyword && !c.name.includes(params.keyword)) return false
      if (params?.priority && c.priority !== params.priority) return false
      if (params?.status && c.status !== params.status) return false
      return true
    }))
  }

  return request<APITestCase[]>({
    url: '/api-test-cases',
    method: 'get',
    params
  })
}

export const createTestCase = (data: APITestCaseCreate) => {
  if (USE_MOCK) {
    const newCase: APITestCase = {
      id: mockCases.length + 1,
      ...data,
      headers: data.headers || {},
      query_params: data.query_params || {},
      variables: data.variables || {},
      assertions: data.assertions || [],
      tags: data.tags || [],
      priority: data.priority || 'medium',
      status: data.status || 'active',
      version: 1,
      creator_id: 1,
      created_at: new Date().toISOString()
    }
    mockCases.push(newCase)
    return Promise.resolve(newCase)
  }

  return request<APITestCase>({
    url: '/api-test-cases',
    method: 'post',
    data
  })
}

export const getTestCase = (id: number) => {
  if (USE_MOCK) {
    const found = mockCases.find(c => c.id === id)
    return found ? Promise.resolve(found) : Promise.reject(new Error('Not found'))
  }

  return request<APITestCase>({
    url: `/api-test-cases/${id}`,
    method: 'get'
  })
}

export const updateTestCase = (id: number, data: APITestCaseUpdate) => {
  if (USE_MOCK) {
    const index = mockCases.findIndex(c => c.id === id)
    if (index >= 0) {
      mockCases[index] = { ...mockCases[index], ...data, version: mockCases[index].version + 1 }
      return Promise.resolve(mockCases[index])
    }
    return Promise.reject(new Error('Not found'))
  }

  return request<APITestCase>({
    url: `/api-test-cases/${id}`,
    method: 'put',
    data
  })
}

export const deleteTestCase = (id: number) => {
  if (USE_MOCK) {
    const index = mockCases.findIndex(c => c.id === id)
    if (index >= 0) {
      mockCases.splice(index, 1)
      return Promise.resolve({ message: 'Deleted' })
    }
    return Promise.reject(new Error('Not found'))
  }

  return request({
    url: `/api-test-cases/${id}`,
    method: 'delete'
  })
}

export const batchTag = (case_ids: number[], tags: string[], operation: 'add' | 'remove' = 'add') => {
  if (USE_MOCK) {
    mockCases.forEach(c => {
      if (case_ids.includes(c.id)) {
        if (operation === 'add') {
          c.tags = [...new Set([...c.tags, ...tags])]
        } else {
          c.tags = c.tags.filter(t => !tags.includes(t))
        }
      }
    })
    return Promise.resolve({ message: 'Success' })
  }

  return request({
    url: '/api-test-cases/batch-tag',
    method: 'post',
    data: { case_ids, tags, operation }
  })
}

export const batchDelete = (case_ids: number[]) => {
  if (USE_MOCK) {
    case_ids.forEach(id => {
      const index = mockCases.findIndex(c => c.id === id)
      if (index >= 0) mockCases.splice(index, 1)
    })
    return Promise.resolve({ message: 'Success' })
  }

  return request({
    url: '/api-test-cases/batch-delete',
    method: 'post',
    data: { case_ids }
  })
}

export const copyTestCase = (id: number) => {
  if (USE_MOCK) {
    const original = mockCases.find(c => c.id === id)
    if (original) {
      const newCase = { ...original, id: mockCases.length + 1, name: `${original.name} (副本)` }
      mockCases.push(newCase)
      return Promise.resolve(newCase)
    }
    return Promise.reject(new Error('Not found'))
  }

  return request<APITestCase>({
    url: `/api-test-cases/${id}/copy`,
    method: 'post'
  })
}

export const getHistories = (id: number) => {
  if (USE_MOCK) {
    return Promise.resolve(mockHistories.filter(h => h.test_case_id === id))
  }

  return request<APITestCaseHistory[]>({
    url: `/api-test-cases/${id}/histories`,
    method: 'get'
  })
}

export const rollbackVersion = (id: number, version: number) => {
  if (USE_MOCK) {
    const found = mockCases.find(c => c.id === id)
    return found ? Promise.resolve(found) : Promise.reject(new Error('Not found'))
  }

  return request<APITestCase>({
    url: `/api-test-cases/${id}/rollback/${version}`,
    method: 'post'
  })
}

export const getModuleTree = (project_id?: number) => {
  if (USE_MOCK) {
    const tree: ModuleTree[] = [
      {
        project_id: 1,
        modules: ['用户模块/登录', '用户模块/注册', '订单模块/创建订单', '订单模块/查询订单']
      }
    ]
    return Promise.resolve(project_id ? tree.filter(t => t.project_id === project_id) : tree)
  }

  return request<ModuleTree[]>({
    url: '/api-test-cases/modules/tree',
    method: 'get',
    params: { project_id }
  })
}

export const createModule = (project_id: number, module: string) => {
  if (USE_MOCK) {
    return Promise.resolve({ message: 'Success' })
  }

  return request({
    url: '/api-test-cases/modules',
    method: 'post',
    data: { project_id, module }
  })
}

export const deleteModule = (project_id: number, module: string) => {
  if (USE_MOCK) {
    return Promise.resolve({ message: 'Success' })
  }

  return request({
    url: '/api-test-cases/modules',
    method: 'delete',
    params: { project_id, module }
  })
}

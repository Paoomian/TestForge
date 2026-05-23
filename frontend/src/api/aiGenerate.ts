import request from '@/utils/request'

// ==================== 类型定义 ====================

export interface AIProviderConfig {
  id: number
  user_id: number
  provider: string
  model_name: string
  api_base_url?: string
  is_default: boolean
  created_at: string
  updated_at?: string
}

export interface AIProviderConfigCreate {
  provider: string
  api_key: string
  model_name: string
  api_base_url?: string
  is_default?: boolean
}

export interface AIProviderConfigUpdate {
  provider?: string
  api_key?: string
  model_name?: string
  api_base_url?: string
  is_default?: boolean
}

export interface AIGenerateTask {
  id: number
  user_id: number
  project_id?: number
  input_type: string
  input_content?: string
  input_file_path?: string
  input_file_name?: string
  generate_type: string
  skill_id?: number
  provider: string
  model_name: string
  target_count: number
  status: string
  progress: number
  error_message?: string
  generated_cases?: any[]
  cases_count: number
  created_at: string
  updated_at?: string
  completed_at?: string
}

export interface AIGenerateTaskCreate {
  project_id?: number
  input_type: 'prd' | 'swagger' | 'text'
  input_content?: string
  input_file_path?: string
  input_file_name?: string
  generate_type: 'functional' | 'api'
  config_id?: number
  skill_id?: number
  target_count?: number
}

// ==================== API 函数 ====================

// AI 配置管理
export const getAIConfigs = () => {
  return request<AIProviderConfig[]>({
    url: '/ai-generate/configs',
    method: 'get'
  })
}

export const createAIConfig = (data: AIProviderConfigCreate) => {
  return request<AIProviderConfig>({
    url: '/ai-generate/configs',
    method: 'post',
    data
  })
}

export const updateAIConfig = (id: number, data: AIProviderConfigUpdate) => {
  return request<AIProviderConfig>({
    url: `/ai-generate/configs/${id}`,
    method: 'put',
    data
  })
}

export const deleteAIConfig = (id: number) => {
  return request({
    url: `/ai-generate/configs/${id}`,
    method: 'delete'
  })
}

export const testAIConfig = (id: number) => {
  return request<{ success: boolean; message: string }>({
    url: `/ai-generate/configs/${id}/test`,
    method: 'post'
  })
}

// 文档上传
export const uploadPRD = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return request<{
    file_path: string
    file_name: string
    parsed_content: any
  }>({
    url: '/ai-generate/upload/prd',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export const uploadSwagger = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return request<{
    file_path: string
    file_name: string
    parsed_content: any
  }>({
    url: '/ai-generate/upload/swagger',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 生成任务管理
export const createGenerateTask = (data: AIGenerateTaskCreate) => {
  return request<AIGenerateTask>({
    url: '/ai-generate/tasks',
    method: 'post',
    data
  })
}

export const getGenerateTasks = (params?: {
  project_id?: number
  status?: string
  skip?: number
  limit?: number
}) => {
  return request<AIGenerateTask[]>({
    url: '/ai-generate/tasks',
    method: 'get',
    params
  })
}

export const getGenerateTask = (id: number) => {
  return request<AIGenerateTask>({
    url: `/ai-generate/tasks/${id}`,
    method: 'get'
  })
}

export const deleteGenerateTask = (id: number) => {
  return request({
    url: `/ai-generate/tasks/${id}`,
    method: 'delete'
  })
}

export const retryGenerateTask = (id: number) => {
  return request({
    url: `/ai-generate/tasks/${id}/retry`,
    method: 'post'
  })
}

export const cancelGenerateTask = (id: number) => {
  return request({
    url: `/ai-generate/tasks/${id}/cancel`,
    method: 'post'
  })
}

// 获取模型列表
export const fetchModels = (data: {
  provider: string
  api_key?: string
  api_base_url?: string
  config_id?: number
}) => {
  return request<{ models: { id: string; name: string }[] }>({
    url: '/ai-generate/fetch-models',
    method: 'post',
    data
  })
}

// 结果操作
export const getGeneratedCases = (taskId: number) => {
  return request<{ cases: any[] }>({
    url: `/ai-generate/tasks/${taskId}/cases`,
    method: 'get'
  })
}

export const updateGeneratedCase = (taskId: number, caseIndex: number, caseData: any) => {
  return request({
    url: `/ai-generate/tasks/${taskId}/cases/${caseIndex}`,
    method: 'put',
    data: caseData
  })
}

export const saveCasesToProject = (taskId: number, data: {
  case_indices?: number[]
  module?: string
}) => {
  return request<{ message: string; saved_count: number }>({
    url: `/ai-generate/tasks/${taskId}/save`,
    method: 'post',
    data
  })
}

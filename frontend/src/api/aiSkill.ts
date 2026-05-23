import request from '@/utils/request'

export interface AISkill {
  id: number
  user_id: number
  name: string
  description: string
  generate_type: 'functional' | 'api'
  system_prompt: string
  user_prompt: string
  is_default: boolean
  created_at: string
  updated_at?: string
}

export interface AISkillCreate {
  name: string
  description?: string
  generate_type: 'functional' | 'api'
  system_prompt: string
  user_prompt: string
  is_default?: boolean
}

export interface AISkillUpdate {
  name?: string
  description?: string
  generate_type?: 'functional' | 'api'
  system_prompt?: string
  user_prompt?: string
  is_default?: boolean
}

// 获取技能列表
export const getAISkills = (generateType?: string) => {
  return request<AISkill[]>({
    url: '/ai-skills/',
    method: 'get',
    params: generateType ? { generate_type: generateType } : {}
  })
}

// 创建技能
export const createAISkill = (data: AISkillCreate) => {
  return request<AISkill>({
    url: '/ai-skills/',
    method: 'post',
    data
  })
}

// 更新技能
export const updateAISkill = (id: number, data: AISkillUpdate) => {
  return request<AISkill>({
    url: `/ai-skills/${id}`,
    method: 'put',
    data
  })
}

// 删除技能
export const deleteAISkill = (id: number) => {
  return request({
    url: `/ai-skills/${id}`,
    method: 'delete'
  })
}

// 初始化默认技能
export const initDefaultSkills = () => {
  return request({
    url: '/ai-skills/init-defaults',
    method: 'post'
  })
}

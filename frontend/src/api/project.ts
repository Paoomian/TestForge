import request from '@/utils/request'

export interface Project {
  id: number
  name: string
  description?: string
  creator_id: number
  created_at: string
  updated_at: string
}

export interface ProjectCreate {
  name: string
  description?: string
}

export interface ProjectUpdate {
  name?: string
  description?: string
}

export const getProjects = (skip = 0, limit = 100) => {
  return request<Project[]>({
    url: '/projects',
    method: 'get',
    params: { skip, limit }
  })
}

export const createProject = (data: ProjectCreate) => {
  return request<Project>({
    url: '/projects',
    method: 'post',
    data
  })
}

export const getProject = (id: number) => {
  return request<Project>({
    url: `/projects/${id}`,
    method: 'get'
  })
}

export const updateProject = (id: number, data: ProjectUpdate) => {
  return request<Project>({
    url: `/projects/${id}`,
    method: 'put',
    data
  })
}

export const deleteProject = (id: number) => {
  return request({
    url: `/projects/${id}`,
    method: 'delete'
  })
}

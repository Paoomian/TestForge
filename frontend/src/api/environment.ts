import request from '@/utils/request'
import type { Environment, EnvironmentCreate, EnvironmentUpdate } from '@/api/apiTestCase'

export const getEnvironments = (project_id: number) => {
  return request<Environment[]>({
    url: '/environments',
    method: 'get',
    params: { project_id }
  })
}

export const createEnvironment = (data: EnvironmentCreate) => {
  return request<Environment>({
    url: '/environments',
    method: 'post',
    data
  })
}

export const updateEnvironment = (id: number, data: EnvironmentUpdate) => {
  return request<Environment>({
    url: `/environments/${id}`,
    method: 'put',
    data
  })
}

export const deleteEnvironment = (id: number) => {
  return request({
    url: `/environments/${id}`,
    method: 'delete'
  })
}

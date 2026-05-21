import request from '@/utils/request'

// 节点类型
export type SceneNodeType = 'api_call' | 'condition' | 'wait' | 'data_assign'

// 条件运算符
export type ConditionOperator = 'eq' | 'neq' | 'gt' | 'lt' | 'gte' | 'lte' | 'contains' | 'not_contains' | 'empty' | 'not_empty'

// 赋值来源
export type AssignSource = 'static' | 'expression'

// 节点数据
export interface SceneNodeItem {
  id?: number
  suite_id: number
  node_type: SceneNodeType
  name: string
  enabled: boolean
  sort_order: number
  // 接口调用
  case_id?: number | null
  case_name?: string
  // 条件判断
  condition_variable?: string
  condition_operator?: ConditionOperator
  condition_value?: string
  true_branch?: number[]
  false_branch?: number[]
  // 等待
  wait_seconds: number
  // 数据赋值
  assign_variable?: string
  assign_value?: string
  assign_source: AssignSource
}

// 创建请求
export interface SceneNodeCreate {
  suite_id: number
  node_type: SceneNodeType
  name: string
  enabled?: boolean
  sort_order?: number
  case_id?: number | null
  condition_variable?: string
  condition_operator?: ConditionOperator
  condition_value?: string
  true_branch?: number[]
  false_branch?: number[]
  wait_seconds?: number
  assign_variable?: string
  assign_value?: string
  assign_source?: AssignSource
}

// 更新请求
export interface SceneNodeUpdate {
  name?: string
  enabled?: boolean
  sort_order?: number
  case_id?: number | null
  condition_variable?: string
  condition_operator?: ConditionOperator
  condition_value?: string
  true_branch?: number[]
  false_branch?: number[]
  wait_seconds?: number
  assign_variable?: string
  assign_value?: string
  assign_source?: AssignSource
}

// API 函数
export const getSceneNodes = (suiteId: number) => {
  return request<SceneNodeItem[]>({
    url: '/scene-nodes',
    params: { suite_id: suiteId }
  })
}

export const createSceneNode = (data: SceneNodeCreate) => {
  return request<SceneNodeItem>({
    url: '/scene-nodes',
    method: 'post',
    data
  })
}

export const updateSceneNode = (nodeId: number, data: SceneNodeUpdate) => {
  return request<SceneNodeItem>({
    url: `/scene-nodes/${nodeId}`,
    method: 'put',
    data
  })
}

export const deleteSceneNode = (nodeId: number) => {
  return request({
    url: `/scene-nodes/${nodeId}`,
    method: 'delete'
  })
}

export const batchSortSceneNodes = (suiteId: number, nodeIds: number[]) => {
  return request({
    url: '/scene-nodes/batch-sort',
    method: 'put',
    data: { suite_id: suiteId, node_ids: nodeIds }
  })
}

<template>
  <a-drawer
    :width="900"
    :visible="visible"
    :title="isEdit ? '编辑任务配置' : '新建任务配置'"
    @update:visible="$emit('update:visible', $event)"
    :mask-closable="false"
  >
    <a-form :model="form" layout="vertical">
      <!-- 基本信息 -->
      <a-row :gutter="16">
        <a-col :span="12">
          <a-form-item label="任务名称" required>
            <a-input v-model="form.name" placeholder="如：冒烟测试" />
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="所属项目" required>
            <a-select v-model="form.project_id" placeholder="选择项目" @change="handleProjectChange">
              <a-option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</a-option>
            </a-select>
          </a-form-item>
        </a-col>
      </a-row>

      <a-form-item label="描述">
        <a-textarea v-model="form.description" placeholder="任务描述（可选）" :max-length="200" show-word-limit />
      </a-form-item>

      <!-- 用例配置 -->
      <a-form-item label="用例配置">
        <a-tabs v-model:active-key="configMode" type="card">
          <!-- 简单模式 -->
          <a-tab-pane key="simple" title="简单模式">
            <div class="case-selector">
              <!-- 筛选条件 -->
              <div class="case-filter">
                <a-select v-model="filterPriority" placeholder="优先级" style="width: 120px" allow-clear>
                  <a-option value="P0">P0 致命</a-option>
                  <a-option value="P1">P1 严重</a-option>
                  <a-option value="P2">P2 一般</a-option>
                  <a-option value="P3">P3 轻微</a-option>
                </a-select>
                <a-select v-model="filterModule" placeholder="模块" style="width: 150px" allow-clear>
                  <a-option v-for="m in modules" :key="m" :value="m">{{ m }}</a-option>
                </a-select>
                <a-input v-model="filterKeyword" placeholder="搜索用例名称" style="width: 180px" allow-clear>
                  <template #prefix><icon-search /></template>
                </a-input>
                <a-button type="outline" size="small" @click="selectAllFiltered">全选筛选结果</a-button>
                <a-button size="small" @click="clearSelection">清空选择</a-button>
              </div>

              <!-- 用例列表 -->
              <div class="case-list">
                <a-checkbox-group v-model="form.case_ids">
                  <div v-for="c in filteredCases" :key="c.id" class="case-item">
                    <a-checkbox :value="c.id">
                      <div class="case-info">
                        <span class="case-number">{{ c.case_number }}</span>
                        <span class="case-name">{{ c.name }}</span>
                        <a-tag size="small" :color="getMethodColor(c.method)">{{ c.method }}</a-tag>
                        <a-tag size="small" :color="getPriorityColor(c.priority)">{{ c.priority }}</a-tag>
                      </div>
                    </a-checkbox>
                  </div>
                </a-checkbox-group>
                <a-empty v-if="filteredCases.length === 0" description="暂无用例" />
              </div>

              <div class="case-selected-count">
                已选 <strong>{{ form.case_ids.length }}</strong> 个用例
              </div>
            </div>

            <!-- 已选用例排序 -->
            <SelectedCaseList
              :cases="selectedCases"
              @reorder="handleReorder"
              @remove="handleRemoveCase"
              style="margin-top: 16px;"
            />
          </a-tab-pane>

          <!-- 场景编排模式 -->
          <a-tab-pane key="orchestration" title="场景编排">
            <SceneOrchestrator
              v-model="sceneNodes"
              :cases="cases"
              :suite-id="form.id || 0"
            />
          </a-tab-pane>
        </a-tabs>
      </a-form-item>

      <!-- 执行配置 -->
      <a-divider>默认执行配置</a-divider>

      <a-row :gutter="16">
        <a-col :span="8">
          <a-form-item label="执行环境" required>
            <a-select v-model="form.environment_id" placeholder="选择环境" :loading="envLoading">
              <a-option v-for="env in environments" :key="env.id" :value="env.id">{{ env.name }}</a-option>
            </a-select>
          </a-form-item>
        </a-col>
        <a-col :span="8">
          <a-form-item label="并发数">
            <a-select v-model="form.concurrency">
              <a-option :value="1">串行</a-option>
              <a-option :value="3">3 并发</a-option>
              <a-option :value="5">5 并发</a-option>
              <a-option :value="10">10 并发</a-option>
            </a-select>
          </a-form-item>
        </a-col>
        <a-col :span="8">
          <a-form-item label="失败策略">
            <a-select v-model="form.failure_strategy">
              <a-option value="continue">继续执行</a-option>
              <a-option value="stop">遇错停止</a-option>
            </a-select>
          </a-form-item>
        </a-col>
      </a-row>

      <!-- 标签 -->
      <a-form-item label="标签">
        <a-input-tag v-model="form.tags" placeholder="输入标签后回车" allow-clear />
      </a-form-item>
    </a-form>

    <template #footer>
      <a-space>
        <a-button @click="$emit('update:visible', false)">取消</a-button>
        <a-button type="primary" :loading="loading" @click="handleSubmit">
          {{ isEdit ? '保存' : '创建' }}
        </a-button>
      </a-space>
    </template>
  </a-drawer>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { Message } from '@arco-design/web-vue'
import { getProjects } from '@/api/project'
import { getTestCases } from '@/api/apiTestCase'
import { getEnvironments } from '@/api/environment'
import { createTestSuite, updateTestSuite, getTestSuite } from '@/api/testSuite'
import { getSceneNodes, createSceneNode, updateSceneNode, deleteSceneNode, batchSortSceneNodes } from '@/api/sceneNode'
import type { TestSuiteListItem } from '@/api/testSuite'
import type { APITestCase, Environment } from '@/api/apiTestCase'
import type { SceneNodeItem } from '@/api/sceneNode'
import SceneOrchestrator from './SceneOrchestrator.vue'
import SelectedCaseList from './SelectedCaseList.vue'

interface Props {
  visible: boolean
  editData: TestSuiteListItem | null
  projectId?: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'success'): void
}>()

const loading = ref(false)
const envLoading = ref(false)
const isEdit = computed(() => !!props.editData)

// 项目列表
const projects = ref<any[]>([])
const environments = ref<Environment[]>([])
const cases = ref<APITestCase[]>([])
const modules = ref<string[]>([])

// 筛选条件
const filterPriority = ref<string>()
const filterModule = ref<string>()
const filterKeyword = ref('')

// 配置模式：simple-简单模式 / orchestration-场景编排
const configMode = ref<'simple' | 'orchestration'>('simple')
const sceneNodes = ref<SceneNodeItem[]>([])

const form = reactive({
  id: undefined as number | undefined,
  project_id: undefined as number | undefined,
  name: '',
  description: '',
  case_ids: [] as number[],
  environment_id: undefined as number | undefined,
  concurrency: 1 as 1 | 3 | 5 | 10,
  failure_strategy: 'continue' as 'continue' | 'stop',
  tags: [] as string[],
  variables: {} as Record<string, string>
})

// 筛选后的用例
const filteredCases = computed(() => {
  return cases.value.filter(c => {
    if (filterPriority.value && c.priority !== filterPriority.value) return false
    if (filterModule.value && c.module !== filterModule.value) return false
    if (filterKeyword.value && !c.name.includes(filterKeyword.value)) return false
    return true
  })
})

// 已选用例（按 case_ids 顺序）
const selectedCases = computed(() => {
  return form.case_ids
    .map(id => cases.value.find(c => c.id === id))
    .filter(Boolean) as APITestCase[]
})

// 加载项目列表
const loadProjects = async () => {
  try {
    projects.value = await getProjects()
  } catch (e) {
    console.error('加载项目失败:', e)
  }
}

// 加载用例列表
const loadCases = async (projectId?: number) => {
  if (!projectId) {
    cases.value = []
    return
  }
  try {
    cases.value = await getTestCases({ project_id: projectId, limit: 1000 })
    // 提取模块列表
    const moduleSet = new Set(cases.value.map(c => c.module).filter(Boolean))
    modules.value = Array.from(moduleSet) as string[]
  } catch (e) {
    console.error('加载用例失败:', e)
  }
}

// 加载环境列表
const loadEnvironments = async (projectId?: number) => {
  if (!projectId) {
    environments.value = []
    return
  }
  envLoading.value = true
  try {
    environments.value = await getEnvironments(projectId)
  } catch (e) {
    console.error('加载环境失败:', e)
  } finally {
    envLoading.value = false
  }
}

const handleProjectChange = (projectId: number) => {
  form.case_ids = []
  form.environment_id = undefined
  loadCases(projectId)
  loadEnvironments(projectId)
}

const selectAllFiltered = () => {
  const ids = filteredCases.value.map(c => c.id)
  const newIds = [...new Set([...form.case_ids, ...ids])]
  form.case_ids = newIds
}

const clearSelection = () => {
  form.case_ids = []
}

const handleReorder = (orderedIds: number[]) => {
  form.case_ids = orderedIds
}

const handleRemoveCase = (caseId: number) => {
  form.case_ids = form.case_ids.filter(id => id !== caseId)
}

// 保存场景节点
const saveSceneNodes = async (suiteId: number) => {
  try {
    // 获取现有节点
    const existingNodes = await getSceneNodes(suiteId)
    const existingIds = new Set(existingNodes.map(n => n.id))
    const currentIds = new Set(sceneNodes.value.filter(n => n.id).map(n => n.id))

    // 删除不再存在的节点
    for (const node of existingNodes) {
      if (!currentIds.has(node.id)) {
        await deleteSceneNode(node.id)
      }
    }

    // 创建或更新节点
    const nodeIds: number[] = []
    for (const node of sceneNodes.value) {
      const nodeData = {
        suite_id: suiteId,
        node_type: node.node_type,
        name: node.name,
        enabled: node.enabled,
        sort_order: node.sort_order,
        case_id: node.case_id,
        condition_variable: node.condition_variable,
        condition_operator: node.condition_operator,
        condition_value: node.condition_value,
        true_branch: node.true_branch,
        false_branch: node.false_branch,
        wait_seconds: node.wait_seconds,
        assign_variable: node.assign_variable,
        assign_value: node.assign_value,
        assign_source: node.assign_source
      }

      if (node.id && existingIds.has(node.id)) {
        // 更新现有节点
        await updateSceneNode(node.id, nodeData)
        nodeIds.push(node.id)
      } else {
        // 创建新节点
        const created = await createSceneNode(nodeData)
        nodeIds.push(created.id)
      }
    }

    // 批量排序
    if (nodeIds.length > 0) {
      await batchSortSceneNodes(suiteId, nodeIds)
    }
  } catch (e) {
    console.error('保存场景节点失败:', e)
    Message.warning('场景节点保存失败，请重试')
  }
}

const getMethodColor = (method: string) => {
  const colors: Record<string, string> = { GET: 'blue', POST: 'green', PUT: 'orange', DELETE: 'red', PATCH: 'purple' }
  return colors[method] || 'gray'
}

const getPriorityColor = (priority: string) => {
  const colors: Record<string, string> = { P0: 'red', P1: 'orange', P2: 'blue', P3: 'green' }
  return colors[priority] || 'gray'
}

const handleSubmit = async () => {
  if (!form.name.trim()) {
    Message.warning('请输入任务名称')
    return
  }
  if (!form.project_id) {
    Message.warning('请选择项目')
    return
  }
  if (!form.environment_id) {
    Message.warning('请选择执行环境')
    return
  }

  // 根据模式校验
  if (configMode.value === 'simple' && form.case_ids.length === 0) {
    Message.warning('请至少选择一个用例')
    return
  }
  if (configMode.value === 'orchestration' && sceneNodes.value.length === 0) {
    Message.warning('请至少添加一个编排节点')
    return
  }

  loading.value = true
  try {
    // 简单模式提交 case_ids，编排模式提交空数组（节点通过 scene-nodes API 保存）
    const submitCaseIds = configMode.value === 'simple' ? form.case_ids : []

    let suiteId: number

    if (isEdit.value && props.editData) {
      await updateTestSuite(props.editData.id, {
        name: form.name,
        description: form.description,
        config_mode: configMode.value,
        case_ids: submitCaseIds,
        environment_id: form.environment_id,
        concurrency: form.concurrency,
        failure_strategy: form.failure_strategy,
        tags: form.tags,
        variables: form.variables
      })
      suiteId = props.editData.id
      Message.success('更新成功')
    } else {
      const result = await createTestSuite({
        project_id: form.project_id!,
        name: form.name,
        description: form.description,
        config_mode: configMode.value,
        case_ids: submitCaseIds,
        environment_id: form.environment_id,
        concurrency: form.concurrency,
        failure_strategy: form.failure_strategy,
        tags: form.tags,
        variables: form.variables
      })
      suiteId = result.id
      Message.success('创建成功')
    }

    // 保存场景节点
    if (configMode.value === 'orchestration') {
      await saveSceneNodes(suiteId)
    }

    emit('update:visible', false)
    emit('success')
  } catch (e: any) {
    Message.error(e?.message || '操作失败')
  } finally {
    loading.value = false
  }
}

// 初始化
watch(() => props.visible, async (val) => {
  if (val) {
    await loadProjects()

    if (isEdit.value && props.editData) {
      // 编辑模式，加载详情
      try {
        const detail = await getTestSuite(props.editData.id)
        form.id = detail.id
        form.project_id = detail.project_id
        form.name = detail.name
        form.description = detail.description || ''
        form.case_ids = detail.case_ids
        form.environment_id = detail.environment_id
        form.concurrency = detail.concurrency as 1 | 3 | 5 | 10
        form.failure_strategy = detail.failure_strategy as 'continue' | 'stop'
        form.tags = detail.tags
        form.variables = detail.variables

        await loadCases(detail.project_id)
        await loadEnvironments(detail.project_id)

        // 恢复配置模式
        configMode.value = (detail.config_mode as 'simple' | 'orchestration') || 'simple'

        // 编排模式下加载场景节点
        if (configMode.value === 'orchestration') {
          sceneNodes.value = await getSceneNodes(detail.id)
        } else {
          sceneNodes.value = []
        }
      } catch (e) {
        Message.error('加载任务详情失败')
      }
    } else {
      // 新建模式
      form.id = undefined
      form.project_id = props.projectId
      form.name = ''
      form.description = ''
      form.case_ids = []
      form.environment_id = undefined
      form.concurrency = 1
      form.failure_strategy = 'continue'
      form.tags = []
      form.variables = {}
      configMode.value = 'simple'
      sceneNodes.value = []

      if (props.projectId) {
        await loadCases(props.projectId)
        await loadEnvironments(props.projectId)
      }
    }
  }
})
</script>

<style scoped>
/* Tab 样式增强 */
:deep(.arco-tabs-nav-type-card) {
  margin-bottom: 16px;
}

:deep(.arco-tabs-tab) {
  font-size: 13px;
}

:deep(.arco-tabs-content) {
  padding: 0;
}

.case-selector {
  border: 1px solid var(--color-border-2);
  border-radius: var(--radius-medium);
  overflow: hidden;
}

.case-filter {
  display: flex;
  gap: 8px;
  padding: 12px;
  background: var(--color-fill-1);
  border-bottom: 1px solid var(--color-border-2);
  flex-wrap: wrap;
  align-items: center;
}

.case-list {
  max-height: 300px;
  overflow-y: auto;
  padding: 8px;
}

.case-item {
  padding: 8px 12px;
  border-radius: var(--radius-small);
  transition: background 0.2s;
}

.case-item:hover {
  background: var(--color-fill-1);
}

.case-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.case-number {
  font-size: 12px;
  color: var(--color-text-3);
  min-width: 100px;
}

.case-name {
  flex: 1;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.case-selected-count {
  padding: 8px 12px;
  background: var(--color-fill-1);
  border-top: 1px solid var(--color-border-2);
  font-size: 13px;
  color: var(--color-text-2);
}
</style>

<template>
  <a-drawer
    :visible="visible"
    :title="isEdit ? '编辑任务配置' : '新建任务配置'"
    :width="800"
    :mask-closable="false"
    @update:visible="$emit('update:visible', $event)"
    @close="handleClose"
  >
    <a-form :model="form" layout="vertical">
      <!-- 基础信息 -->
      <a-row :gutter="16">
        <a-col :span="12">
          <a-form-item label="任务名称" required>
            <a-input v-model="form.name" placeholder="请输入任务名称" />
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="所属项目" required>
            <a-select
              v-model="form.project_id"
              placeholder="选择项目"
              :loading="projectsLoading"
              @change="handleProjectChange"
            >
              <a-option v-for="p in projects" :key="p.id" :value="p.id">
                {{ p.name }}
              </a-option>
            </a-select>
          </a-form-item>
        </a-col>
      </a-row>

      <!-- 选择用例（内嵌表格） -->
      <div class="section-label">
        <span class="label-required">*</span> 选择用例
      </div>
      <!-- 筛选栏 -->
      <div class="filter-bar">
        <a-input
          v-model="selectorKeyword"
          placeholder="搜索用例名称"
          style="width: 180px"
          allow-clear
          @press-enter="loadCases"
        >
          <template #prefix><icon-search /></template>
        </a-input>
        <a-select
          v-model="selectorPriority"
          placeholder="优先级"
          style="width: 110px"
          allow-clear
          @change="loadCases"
        >
          <a-option value="P0">P0 致命</a-option>
          <a-option value="P1">P1 严重</a-option>
          <a-option value="P2">P2 一般</a-option>
          <a-option value="P3">P3 轻微</a-option>
        </a-select>
        <a-select
          v-model="selectorModule"
          placeholder="模块"
          style="width: 140px"
          allow-clear
          @change="loadCases"
        >
          <a-option v-for="m in moduleOptions" :key="m.value" :value="m.value">
            {{ m.label }}
          </a-option>
        </a-select>
      </div>

      <!-- 用例表格 -->
      <a-table
        v-model:selectedKeys="form.case_ids"
        :data="selectorCases"
        :loading="selectorLoading"
        :pagination="false"
        :row-selection="{ type: 'checkbox' }"
        row-key="id"
        :scroll="{ y: 240 }"
        size="small"
        style="margin-top: 8px; margin-bottom: 16px"
      >
        <template #columns>
          <a-table-column title="编号" data-index="case_number" :width="110" />
          <a-table-column title="用例名称" data-index="name" />
          <a-table-column title="模块" data-index="module" :width="100">
            <template #cell="{ record }">
              <span v-if="record.module">{{ record.module }}</span>
              <span v-else class="text-gray">-</span>
            </template>
          </a-table-column>
          <a-table-column title="优先级" :width="80">
            <template #cell="{ record }">
              <a-tag size="small" :color="getPriorityColor(record.priority)">
                {{ record.priority || 'P2' }}
              </a-tag>
            </template>
          </a-table-column>
          <a-table-column title="步骤" :width="60">
            <template #cell="{ record }">
              {{ record.steps?.length || 0 }}
            </template>
          </a-table-column>
        </template>
      </a-table>

      <!-- 已选用例排序 -->
      <a-form-item v-if="form.case_ids.length > 0" label="已选用例">
        <UISelectedCaseList
          :cases="selectedCasesData"
          @remove="removeCase"
          @reorder="reorderCases"
        />
      </a-form-item>

      <!-- 执行配置 -->
      <a-row :gutter="16">
        <a-col :span="8">
          <a-form-item label="执行环境">
            <a-select
              v-model="form.environment_id"
              placeholder="可选"
              allow-clear
              :loading="envLoading"
            >
              <a-option v-for="env in environments" :key="env.id" :value="env.id">
                {{ env.name }}
              </a-option>
            </a-select>
          </a-form-item>
        </a-col>
        <a-col :span="8">
          <a-form-item label="浏览器">
            <a-select v-model="form.browser">
              <a-option value="chrome">Chrome</a-option>
              <a-option value="firefox">Firefox</a-option>
              <a-option value="edge">Edge</a-option>
            </a-select>
          </a-form-item>
        </a-col>
        <a-col :span="8">
          <a-form-item label="视口尺寸">
            <a-select v-model="viewportSize">
              <a-option value="1280x720">1280 x 720</a-option>
              <a-option value="1920x1080">1920 x 1080</a-option>
              <a-option value="375x812">iPhone</a-option>
            </a-select>
          </a-form-item>
        </a-col>
      </a-row>

      <a-form-item label="失败策略">
        <a-radio-group v-model="form.failure_strategy">
          <a-radio value="continue">继续执行后续用例</a-radio>
          <a-radio value="stop">遇到失败停止执行</a-radio>
        </a-radio-group>
      </a-form-item>

      <a-form-item label="描述">
        <a-textarea v-model="form.description" placeholder="可选描述" :max-length="500" />
      </a-form-item>
    </a-form>

    <template #footer>
      <div class="drawer-footer">
        <a-button @click="handleClose">取消</a-button>
        <a-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ isEdit ? '保存' : '创建' }}
        </a-button>
      </div>
    </template>
  </a-drawer>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { Message } from '@arco-design/web-vue'
import { IconSearch } from '@arco-design/web-vue/es/icon'
import { getProjects, type Project } from '@/api/project'
import { getUICaseList, getUICaseModules, type UICase } from '@/api/uiCase'
import { getEnvironments } from '@/api/environment'
import type { Environment } from '@/api/apiTestCase'
import { createUITestSuite, updateUITestSuite } from '@/api/uiTestSuite'
import type { UITestSuite } from '@/api/uiTestSuite'
import UISelectedCaseList from './UISelectedCaseList.vue'

interface Props {
  visible: boolean
  editData?: UITestSuite | null
  projectId?: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:visible': [value: boolean]
  success: []
}>()

// 项目和环境
const projects = ref<Project[]>([])
const projectsLoading = ref(false)
const environments = ref<Environment[]>([])
const envLoading = ref(false)

// 用例列表
const selectorCases = ref<UICase[]>([])
const selectorLoading = ref(false)

// 筛选条件
const selectorKeyword = ref('')
const selectorPriority = ref<string | undefined>(undefined)
const selectorModule = ref<string | undefined>(undefined)
const moduleOptions = ref<{ label: string; value: string }[]>([])

// 已选用例数据
const selectedCasesData = computed(() => {
  return form.case_ids
    .map(id => selectorCases.value.find(c => c.id === id))
    .filter(Boolean) as UICase[]
})

// 表单
const form = reactive({
  project_id: undefined as number | undefined,
  name: '',
  description: '',
  case_ids: [] as number[],
  environment_id: undefined as number | undefined,
  failure_strategy: 'continue',
  browser: 'chrome',
  viewport_width: 1280,
  viewport_height: 720,
  tags: [] as string[],
})

// 视口尺寸
const viewportSize = computed({
  get: () => `${form.viewport_width}x${form.viewport_height}`,
  set: (val: string) => {
    const [w, h] = val.split('x').map(Number)
    form.viewport_width = w
    form.viewport_height = h
  }
})

const submitting = ref(false)
const isEdit = computed(() => !!props.editData)

function getPriorityColor(priority: string): string {
  const colors: Record<string, string> = { P0: 'red', P1: 'orange', P2: 'blue', P3: 'green' }
  return colors[priority] || 'blue'
}

// 监听编辑数据变化
watch(() => props.editData, (data) => {
  if (data) {
    form.project_id = data.project_id
    form.name = data.name
    form.description = data.description || ''
    form.case_ids = [...data.case_ids]
    form.environment_id = data.environment_id
    form.failure_strategy = data.failure_strategy
    form.browser = data.browser
    form.viewport_width = data.viewport_width
    form.viewport_height = data.viewport_height
    form.tags = [...(data.tags || [])]
  } else {
    resetForm()
  }
}, { immediate: true })

// 监听 visible 变化
watch(() => props.visible, async (visible) => {
  if (visible) {
    await loadProjects()
    if (props.projectId) {
      form.project_id = props.projectId
    }
    if (form.project_id) {
      await Promise.all([loadCases(), loadEnvironments(), loadModules()])
    }
  }
})

function resetForm() {
  form.project_id = props.projectId
  form.name = ''
  form.description = ''
  form.case_ids = []
  form.environment_id = undefined
  form.failure_strategy = 'continue'
  form.browser = 'chrome'
  form.viewport_width = 1280
  form.viewport_height = 720
  form.tags = []
}

async function loadProjects() {
  projectsLoading.value = true
  try {
    projects.value = await getProjects() as any || []
  } catch (e) {
    console.error('加载项目列表失败:', e)
  } finally {
    projectsLoading.value = false
  }
}

async function loadEnvironments() {
  if (!form.project_id) return
  envLoading.value = true
  try {
    const res = await getEnvironments(form.project_id)
    environments.value = (res as any) || []
  } catch (e) {
    console.error('加载环境列表失败:', e)
  } finally {
    envLoading.value = false
  }
}

async function loadModules() {
  if (!form.project_id) return
  try {
    const res = await getUICaseModules(form.project_id)
    moduleOptions.value = flattenModuleTree(res || [])
  } catch (e) {
    console.error('加载模块列表失败:', e)
  }
}

function flattenModuleTree(tree: any[]): { label: string; value: string }[] {
  const result: { label: string; value: string }[] = []
  function walk(nodes: any[], prefix = '') {
    for (const node of nodes) {
      const fullPath = prefix ? `${prefix}/${node.label}` : node.label
      result.push({ label: fullPath, value: node.value || fullPath })
      if (node.children?.length) {
        walk(node.children, fullPath)
      }
    }
  }
  walk(tree)
  return result
}

async function loadCases() {
  if (!form.project_id) return
  selectorLoading.value = true
  try {
    const filters: Record<string, string> = {}
    if (selectorKeyword.value) filters.keyword = selectorKeyword.value
    if (selectorPriority.value) filters.priority = selectorPriority.value
    if (selectorModule.value) filters.module = selectorModule.value
    const res = await getUICaseList(form.project_id, 0, 1000, filters)
    selectorCases.value = (res as any) || []
  } catch (e) {
    console.error('加载用例列表失败:', e)
  } finally {
    selectorLoading.value = false
  }
}

async function handleProjectChange() {
  form.environment_id = undefined
  form.case_ids = []
  await Promise.all([loadCases(), loadEnvironments(), loadModules()])
}

function removeCase(caseId: number) {
  form.case_ids = form.case_ids.filter(id => id !== caseId)
}

function reorderCases(orderedIds: number[]) {
  form.case_ids = orderedIds
}

function handleClose() {
  emit('update:visible', false)
}

async function handleSubmit() {
  if (!form.name.trim()) {
    Message.warning('请输入任务名称')
    return
  }
  if (!form.project_id) {
    Message.warning('请选择项目')
    return
  }
  if (form.case_ids.length === 0) {
    Message.warning('请选择用例')
    return
  }

  submitting.value = true
  try {
    if (isEdit.value && props.editData) {
      await updateUITestSuite(props.editData.id, {
        name: form.name,
        description: form.description,
        case_ids: form.case_ids,
        environment_id: form.environment_id,
        failure_strategy: form.failure_strategy,
        browser: form.browser,
        viewport_width: form.viewport_width,
        viewport_height: form.viewport_height,
        tags: form.tags,
      })
      Message.success('保存成功')
    } else {
      await createUITestSuite({
        project_id: form.project_id,
        name: form.name,
        description: form.description,
        case_ids: form.case_ids,
        environment_id: form.environment_id,
        failure_strategy: form.failure_strategy,
        browser: form.browser,
        viewport_width: form.viewport_width,
        viewport_height: form.viewport_height,
        tags: form.tags,
      })
      Message.success('创建成功')
    }
    emit('success')
    handleClose()
  } catch (e: any) {
    Message.error(e?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.section-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-2);
  margin-bottom: 8px;
}

.section-label .label-required {
  color: var(--color-danger-6);
  margin-right: 4px;
}

.filter-bar {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.text-gray {
  color: var(--color-text-4);
}
</style>

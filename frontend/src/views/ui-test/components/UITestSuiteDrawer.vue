<template>
  <a-drawer
    :visible="visible"
    :title="isEdit ? '编辑任务配置' : '新建任务配置'"
    :width="500"
    :mask-closable="false"
    @update:visible="$emit('update:visible', $event)"
    @close="handleClose"
  >
    <a-form :model="form" layout="vertical">
      <!-- 任务名称 -->
      <a-form-item label="任务名称" required>
        <a-input v-model="form.name" placeholder="请输入任务名称" />
      </a-form-item>

      <!-- 项目选择 -->
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

      <!-- 选择用例 -->
      <a-form-item label="选择用例" required>
        <div class="case-selector">
          <a-button type="outline" @click="showCaseSelector = true" :disabled="!form.project_id">
            <template #icon><icon-plus /></template>
            选择用例 ({{ form.case_ids.length }} 已选)
          </a-button>
          <div v-if="selectedCaseNames.length > 0" class="selected-cases">
            <a-tag
              v-for="(name, index) in selectedCaseNames"
              :key="index"
              closable
              @close="removeCase(index)"
            >
              {{ name }}
            </a-tag>
          </div>
        </div>
      </a-form-item>

      <!-- 执行环境 -->
      <a-form-item label="执行环境">
        <a-select
          v-model="form.environment_id"
          placeholder="选择环境（可选）"
          allow-clear
          :loading="envLoading"
        >
          <a-option v-for="env in environments" :key="env.id" :value="env.id">
            {{ env.name }}
          </a-option>
        </a-select>
      </a-form-item>

      <!-- 失败策略 -->
      <a-form-item label="失败策略">
        <a-radio-group v-model="form.failure_strategy">
          <a-radio value="continue">继续执行后续用例</a-radio>
          <a-radio value="stop">遇到失败停止执行</a-radio>
        </a-radio-group>
      </a-form-item>

      <!-- 浏览器配置 -->
      <a-row :gutter="16">
        <a-col :span="12">
          <a-form-item label="浏览器">
            <a-select v-model="form.browser">
              <a-option value="chrome">Chrome</a-option>
              <a-option value="firefox">Firefox</a-option>
              <a-option value="edge">Edge</a-option>
            </a-select>
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="视口尺寸">
            <a-select v-model="viewportSize">
              <a-option value="1280x720">1280 x 720</a-option>
              <a-option value="1920x1080">1920 x 1080</a-option>
              <a-option value="375x812">iPhone (375 x 812)</a-option>
            </a-select>
          </a-form-item>
        </a-col>
      </a-row>

      <!-- 描述 -->
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

    <!-- 用例选择弹窗 -->
    <a-modal
      v-model:visible="showCaseSelector"
      title="选择用例"
      :width="700"
      :footer="false"
    >
      <a-table
        v-model:selectedKeys="selectorSelectedKeys"
        :data="selectorCases"
        :loading="selectorLoading"
        :pagination="false"
        :row-selection="{ type: 'checkbox' }"
        row-key="id"
        :scroll="{ y: 400 }"
      >
        <template #columns>
          <a-table-column title="用例名称" data-index="name" />
          <a-table-column title="步骤数" :width="100">
            <template #cell="{ record }">
              {{ record.steps?.length || 0 }} 步
            </template>
          </a-table-column>
        </template>
      </a-table>

      <div class="selector-footer">
        <a-button @click="showCaseSelector = false">取消</a-button>
        <a-button type="primary" @click="confirmCaseSelection">
          确认选择 ({{ selectorSelectedKeys.length }})
        </a-button>
      </div>
    </a-modal>
  </a-drawer>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { Message } from '@arco-design/web-vue'
import { IconPlus } from '@arco-design/web-vue/es/icon'
import { getProjects, type Project } from '@/api/project'
import { getUICaseList, type UICase } from '@/api/uiCase'
import { getEnvironments } from '@/api/environment'
import type { Environment } from '@/api/apiTestCase'
import { createUITestSuite, updateUITestSuite } from '@/api/uiTestSuite'
import type { UITestSuite } from '@/api/uiTestSuite'

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

// 用例选择
const showCaseSelector = ref(false)
const selectorCases = ref<UICase[]>([])
const selectorLoading = ref(false)
const selectorSelectedKeys = ref<number[]>([])
const selectedCaseNames = ref<string[]>([])

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

// 提交状态
const submitting = ref(false)

// 是否编辑模式
const isEdit = computed(() => !!props.editData)

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
    // 加载用例名称
    loadCaseNames()
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
      await loadEnvironments()
    }
  }
})

// 监听用例选择弹窗打开
watch(showCaseSelector, async (visible) => {
  if (visible && form.project_id) {
    await loadCasesForSelector()
    // 回显已选中的用例
    selectorSelectedKeys.value = [...form.case_ids]
  }
})

// 重置表单
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
  selectedCaseNames.value = []
}

// 加载项目列表
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

// 加载环境列表
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

// 加载用例列表（选择器用）
async function loadCasesForSelector() {
  if (!form.project_id) return
  selectorLoading.value = true
  try {
    const res = await getUICaseList(form.project_id, 0, 1000)
    selectorCases.value = (res as any) || []
  } catch (e) {
    console.error('加载用例列表失败:', e)
  } finally {
    selectorLoading.value = false
  }
}

// 加载用例名称
async function loadCaseNames() {
  if (!form.project_id || form.case_ids.length === 0) {
    selectedCaseNames.value = []
    return
  }
  try {
    const res = await getUICaseList(form.project_id, 0, 1000)
    const cases = (res as any) || []
    const caseMap = new Map(cases.map((c: UICase) => [c.id, c.name]))
    selectedCaseNames.value = form.case_ids.map(id => caseMap.get(id) || `用例#${id}`)
  } catch (e) {
    selectedCaseNames.value = form.case_ids.map(id => `用例#${id}`)
  }
}

// 项目变化
async function handleProjectChange() {
  form.environment_id = undefined
  form.case_ids = []
  selectedCaseNames.value = []
  await loadEnvironments()
}

// 确认选择用例
function confirmCaseSelection() {
  form.case_ids = [...selectorSelectedKeys.value]
  const caseMap = new Map(selectorCases.value.map(c => [c.id, c.name]))
  selectedCaseNames.value = form.case_ids.map(id => caseMap.get(id) || `用例#${id}`)
  showCaseSelector.value = false
}

// 移除用例
function removeCase(index: number) {
  form.case_ids.splice(index, 1)
  selectedCaseNames.value.splice(index, 1)
}

// 关闭抽屉
function handleClose() {
  emit('update:visible', false)
}

// 提交
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
.case-selector {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.selected-cases {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.selector-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 16px;
}
</style>

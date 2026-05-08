<template>
  <a-drawer
    v-model:visible="visible"
    :title="isEdit ? '编辑用例' : '新建用例'"
    width="900px"
    unmount-on-close
    @cancel="handleCancel"
  >
    <!-- 工具栏 -->
    <template #title-extra>
      <a-space v-if="!isEdit">
        <a-button size="small" @click="showTemplateModal = true">
          <template #icon><icon-file /></template>
          从模板创建
        </a-button>
        <a-button size="small" @click="showCurlModal = true">
          <template #icon><icon-import /></template>
          导入cURL
        </a-button>
      </a-space>
    </template>

    <a-tabs v-model:active-key="activeTab">
      <!-- Tab1: 基本信息 -->
      <a-tab-pane key="basic" title="基本信息">
        <BasicInfoTab
          :form-data="formData"
          :projects="projects"
          :module-tree-raw="moduleTreeRaw"
          :is-edit="isEdit"
          @update="handleFieldUpdate"
        />
      </a-tab-pane>

      <!-- Tab2: 请求配置 -->
      <a-tab-pane key="request" title="请求配置">
        <RequestConfigTab
          :form-data="formData"
          :raw-content="rawContent"
          :project-id="formData.project_id"
          @update="handleFieldUpdate"
          @update:raw-content="rawContent = $event"
        />
      </a-tab-pane>

      <!-- Tab3: 断言与提取 -->
      <a-tab-pane key="assertion-extract" title="断言与提取">
        <AssertionExtractTab
          :assertions="formData.assertions"
          :extracts="formData.extracts"
          @update:assertions="formData.assertions = $event"
          @update:extracts="formData.extracts = $event"
        />
      </a-tab-pane>

      <!-- Tab4: 脚本 -->
      <a-tab-pane key="script" title="脚本">
        <ScriptTab
          :setup-script="formData.setup_script || ''"
          :teardown-script="formData.teardown_script || ''"
          @update:setup-script="formData.setup_script = $event"
          @update:teardown-script="formData.teardown_script = $event"
        />
      </a-tab-pane>
    </a-tabs>

    <template #footer>
      <a-space>
        <a-button @click="handleCancel">取消</a-button>
        <a-button type="secondary" :loading="submitting" @click="handleSubmit('draft')">
          暂存草稿
        </a-button>
        <a-button type="primary" :loading="submitting" @click="handleSubmit('active')">
          保存
        </a-button>
      </a-space>
    </template>

    <!-- 模板选择弹窗 -->
    <a-modal
      v-model:visible="showTemplateModal"
      title="选择模板"
      width="600px"
      :footer="false"
    >
      <a-list :data="templates" :loading="templatesLoading">
        <template #item="{ item }">
          <a-list-item>
            <a-list-item-meta :title="item.name" :description="item.description" />
            <template #actions>
              <a-button type="primary" size="small" @click="applyTemplate(item)">
                使用
              </a-button>
            </template>
          </a-list-item>
        </template>
      </a-list>
    </a-modal>

    <!-- cURL导入弹窗 -->
    <a-modal
      v-model:visible="showCurlModal"
      title="导入 cURL 命令"
      @ok="handleCurlImport"
      :ok-loading="curlLoading"
    >
      <a-form :model="{ curlCommand }" layout="vertical">
        <a-form-item label="粘贴 cURL 命令">
          <a-textarea
            v-model="curlCommand"
            placeholder='curl -X POST "https://api.example.com/users" -H "Content-Type: application/json" -d {"name":"test"}'
            :auto-size="{ minRows: 6, maxRows: 12 }"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </a-drawer>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { Message } from '@arco-design/web-vue'
import { getProjects } from '@/api/project'
import {
  createTestCase,
  updateTestCase,
  getTestCase,
  getModuleTree,
  getTemplates,
  importCurl,
} from '@/api/apiTestCase'
import type {
  APITestCase,
  APITestCaseCreate,
  APITestCaseUpdate,
  ModuleTree,
  TestCaseTemplate,
  HeaderItem,
  QueryParamItem,
  BodyFormItem,
  AssertionItem,
  ExtractItem,
  AuthConfig,
} from '@/api/apiTestCase'
import type { Project } from '@/api/project'
import BasicInfoTab from './BasicInfoTab.vue'
import RequestConfigTab from './RequestConfigTab.vue'
import AssertionExtractTab from './AssertionExtractTab.vue'
import ScriptTab from './ScriptTab.vue'

interface Props {
  visible: boolean
  editData?: APITestCase | null
  defaultProjectId?: number
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}>()

const visible = ref(props.visible)
const isEdit = ref(false)
const submitting = ref(false)
const activeTab = ref('basic')
const projects = ref<Project[]>([])
const moduleTreeRaw = ref<ModuleTree[]>([])

// 模板相关
const showTemplateModal = ref(false)
const templates = ref<TestCaseTemplate[]>([])
const templatesLoading = ref(false)

// cURL相关
const showCurlModal = ref(false)
const curlCommand = ref('')
const curlLoading = ref(false)

const rawContent = ref('')

const formData = reactive({
  id: undefined as number | undefined,
  project_id: 0,
  case_number: '',
  module: '',
  name: '',
  description: '',
  preconditions: '',
  remark: '',
  method: 'GET',
  url: '',
  body_type: 'none',
  auth_type: 'none',
  setup_script: '',
  teardown_script: '',
  tags: [] as string[],
  priority: 'P2',
  status: 'draft',
  headers: [] as HeaderItem[],
  query_params: [] as QueryParamItem[],
  body_form: [] as BodyFormItem[],
  assertions: [] as AssertionItem[],
  extracts: [] as ExtractItem[],
  auth: { auth_type: 'none' } as AuthConfig,
})

// 监听visible
watch(() => props.visible, (val) => {
  visible.value = val
  if (val) {
    loadProjects()
    loadModuleTree()
    if (props.editData) {
      isEdit.value = true
      loadEditData(props.editData)
    } else {
      isEdit.value = false
      resetForm()
    }
  }
})

watch(visible, (val) => {
  emit('update:visible', val)
})

// 项目列表
const loadProjects = async () => {
  try {
    projects.value = await getProjects()
    if (projects.value.length === 0 && !isEdit.value) {
      Message.warning('暂无项目，请先创建项目')
      visible.value = false
    }
  } catch {
    Message.error('加载项目列表失败')
  }
}

// 模块树
const loadModuleTree = async () => {
  try {
    moduleTreeRaw.value = await getModuleTree()
  } catch {
    console.error('Failed to load module tree')
  }
}

// 加载编辑数据
const loadEditData = async (data: APITestCase) => {
  // 如果editData是完整数据（有子表），直接使用；否则重新获取
  let fullData = data
  if (!data.headers && !data.assertions) {
    try {
      fullData = await getTestCase(data.id)
    } catch {
      Message.error('加载用例详情失败')
      return
    }
  }

  formData.id = fullData.id
  formData.project_id = fullData.project_id
  formData.case_number = fullData.case_number || ''
  formData.module = fullData.module || ''
  formData.name = fullData.name
  formData.description = fullData.description || ''
  formData.preconditions = fullData.preconditions || ''
  formData.remark = fullData.remark || ''
  formData.method = fullData.method
  formData.url = fullData.url
  formData.body_type = fullData.body_type || 'none'
  formData.auth_type = fullData.auth_type || 'none'
  formData.setup_script = fullData.setup_script || ''
  formData.teardown_script = fullData.teardown_script || ''
  formData.tags = fullData.tags || []
  formData.priority = fullData.priority || 'P2'
  formData.status = fullData.status || 'draft'
  formData.headers = (fullData.headers || []).map(h => ({ ...h }))
  formData.query_params = (fullData.query_params || []).map(p => ({ ...p }))
  formData.body_form = (fullData.body_form || []).map(f => ({ ...f }))
  formData.assertions = (fullData.assertions || []).map(a => ({ ...a }))
  formData.extracts = (fullData.extracts || []).map(e => ({ ...e }))
  formData.auth = fullData.auth ? { ...fullData.auth } : { auth_type: 'none' }

  rawContent.value = fullData.body_raw?.content || ''
}

const resetForm = () => {
  formData.id = undefined
  formData.project_id = props.defaultProjectId || 0
  formData.case_number = ''
  formData.module = ''
  formData.name = ''
  formData.description = ''
  formData.preconditions = ''
  formData.remark = ''
  formData.method = 'GET'
  formData.url = ''
  formData.body_type = 'none'
  formData.auth_type = 'none'
  formData.setup_script = ''
  formData.teardown_script = ''
  formData.tags = []
  formData.priority = 'P2'
  formData.status = 'draft'
  formData.headers = []
  formData.query_params = []
  formData.body_form = []
  formData.assertions = []
  formData.extracts = []
  formData.auth = { auth_type: 'none' }
  rawContent.value = ''
  activeTab.value = 'basic'
}

const handleFieldUpdate = (field: string, value: any) => {
  ;(formData as any)[field] = value
}

const handleCancel = () => {
  visible.value = false
}

// 表单校验
const validate = (): boolean => {
  if (!formData.name.trim()) {
    Message.warning('请输入用例名称')
    activeTab.value = 'basic'
    return false
  }
  if (!formData.project_id) {
    Message.warning('请选择所属项目')
    activeTab.value = 'basic'
    return false
  }
  if (!formData.url.trim()) {
    Message.warning('请输入请求URL')
    activeTab.value = 'request'
    return false
  }
  return true
}

const handleSubmit = async (saveStatus?: string) => {
  if (!validate()) return

  submitting.value = true
  try {
    const bodyRaw = rawContent.value ? { content: rawContent.value } : undefined

    if (isEdit.value && formData.id) {
      const updateData: APITestCaseUpdate = {
        name: formData.name,
        description: formData.description,
        module: formData.module,
        preconditions: formData.preconditions,
        remark: formData.remark,
        method: formData.method,
        url: formData.url,
        body_type: formData.body_type,
        auth_type: formData.auth_type,
        setup_script: formData.setup_script,
        teardown_script: formData.teardown_script,
        tags: formData.tags,
        priority: formData.priority,
        status: saveStatus || formData.status,
        headers: formData.headers,
        query_params: formData.query_params,
        body_form: formData.body_form,
        body_raw: bodyRaw,
        assertions: formData.assertions,
        extracts: formData.extracts,
        auth: formData.auth,
      }
      await updateTestCase(formData.id, updateData)
      Message.success('更新成功')
    } else {
      const createData: APITestCaseCreate = {
        project_id: formData.project_id,
        name: formData.name,
        description: formData.description,
        module: formData.module,
        preconditions: formData.preconditions,
        remark: formData.remark,
        method: formData.method,
        url: formData.url,
        body_type: formData.body_type,
        auth_type: formData.auth_type,
        setup_script: formData.setup_script,
        teardown_script: formData.teardown_script,
        tags: formData.tags,
        priority: formData.priority,
        status: saveStatus || formData.status,
        headers: formData.headers,
        query_params: formData.query_params,
        body_form: formData.body_form,
        body_raw: bodyRaw,
        assertions: formData.assertions,
        extracts: formData.extracts,
        auth: formData.auth,
      }
      await createTestCase(createData)
      Message.success('创建成功')
    }
    visible.value = false
    emit('success')
  } catch {
    Message.error(isEdit.value ? '更新失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

// 模板
const loadTemplates = async () => {
  templatesLoading.value = true
  try {
    templates.value = await getTemplates()
  } catch {
    Message.error('加载模板失败')
  } finally {
    templatesLoading.value = false
  }
}

watch(showTemplateModal, (val) => {
  if (val && templates.value.length === 0) loadTemplates()
})

const applyTemplate = (tpl: TestCaseTemplate) => {
  formData.method = tpl.method
  formData.url = tpl.url
  formData.body_type = tpl.body_type || 'none'
  formData.headers = (tpl.headers || []).map(h => ({ ...h }))
  formData.query_params = (tpl.query_params || []).map(p => ({ ...p }))
  formData.assertions = (tpl.assertions || []).map(a => ({ ...a }))
  formData.extracts = (tpl.extracts || []).map(e => ({ ...e }))
  if (tpl.body_raw_content) {
    rawContent.value = tpl.body_raw_content
  }
  if (tpl.priority) {
    formData.priority = tpl.priority
  }
  showTemplateModal.value = false
  activeTab.value = 'request'
  Message.success('模板已应用')
}

// cURL导入
const handleCurlImport = async () => {
  if (!curlCommand.value.trim()) {
    Message.warning('请输入cURL命令')
    return
  }
  curlLoading.value = true
  try {
    const result = await importCurl(curlCommand.value)
    formData.method = result.method
    formData.url = result.url
    formData.body_type = result.body_type
    formData.headers = result.headers || []
    formData.query_params = result.query_params || []
    formData.body_form = result.body_form || []
    if (result.body_raw_content) {
      rawContent.value = result.body_raw_content
    }
    if (result.auth_type && result.auth_type !== 'none') {
      formData.auth_type = result.auth_type
      formData.auth = result.auth || { auth_type: result.auth_type as 'none' | 'bearer' | 'basic' | 'api_key' }
    }
    showCurlModal.value = false
    curlCommand.value = ''
    activeTab.value = 'request'
    Message.success('cURL已导入')
  } catch {
    Message.error('cURL解析失败，请检查命令格式')
  } finally {
    curlLoading.value = false
  }
}
</script>

<style scoped>
:deep(.arco-drawer-body) {
  padding: 0;
}

:deep(.arco-tabs-content) {
  padding: 20px;
}
</style>

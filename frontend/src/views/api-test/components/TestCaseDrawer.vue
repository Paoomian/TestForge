<template>
  <a-drawer
    v-model:visible="visible"
    :title="isEdit ? '编辑用例' : '新建用例'"
    :width="drawerWidth"
    @cancel="handleCancel"
  >
    <!-- 工具栏 -->
    <template #title-extra>
      <a-space>
        <a-button v-if="!isEdit" size="small" @click="showTemplateModal = true">
          <template #icon><icon-file /></template>
          从模板创建
        </a-button>
        <a-button v-if="!isEdit" size="small" @click="showCurlModal = true">
          <template #icon><icon-import /></template>
          导入cURL
        </a-button>
        <a-button
          type="outline"
          status="success"
          size="small"
          :loading="debugLoading"
          @click="handleDebug"
        >
          发送请求
        </a-button>
      </a-space>
    </template>

    <div class="drawer-body" :class="{ 'has-response': showResponse }">
      <!-- 左侧：编辑表单 -->
      <div class="editor-panel">
        <a-tabs v-model:active-key="activeTab" :destroy-on-hide="false">
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
              :data-rules="formData.data_rules"
              @update:assertions="formData.assertions = $event"
              @update:data-rules="formData.data_rules = $event"
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
      </div>

      <!-- 右侧：响应面板 -->
      <div v-if="showResponse" class="response-panel">
        <div class="response-header">
          <span class="response-title">响应结果</span>
          <a-button type="text" size="mini" @click="showResponse = false">
            <template #icon><icon-close /></template>
          </a-button>
        </div>

        <!-- 加载中 -->
        <div v-if="debugLoading" class="response-loading">
          <a-spin dot />
          <span>请求发送中...</span>
        </div>

        <!-- 响应结果 -->
        <template v-else-if="debugResult">
          <!-- 状态栏 -->
          <div class="response-status">
            <a-tag :color="getStatusColor(debugResult.status)" size="small">
              {{ debugResult.status === 'pass' ? '通过' : debugResult.status === 'fail' ? '失败' : '错误' }}
            </a-tag>
            <span v-if="debugResult.response_info?.status_code" class="status-code">
              {{ debugResult.response_info.status_code }}
            </span>
            <span class="duration">{{ debugResult.duration_ms }}ms</span>
            <span v-if="debugResult.response_info?.size_bytes" class="size">
              {{ formatSize(debugResult.response_info.size_bytes) }}
            </span>
          </div>

          <!-- 错误信息 -->
          <a-alert
            v-if="debugResult.error_message"
            type="error"
            :content="debugResult.error_message"
            style="margin: 8px 12px"
          />

          <!-- 响应内容 Tab -->
          <a-tabs v-model:active-key="responseTab" size="small" class="response-tabs">
            <a-tab-pane key="body" title="响应体">
              <div class="response-body">
                <JsonViewer
                  v-if="debugResult.response_info?.body"
                  :content="debugResult.response_info.body"
                  max-height="400px"
                />
                <a-empty v-else description="无响应内容" />
              </div>
            </a-tab-pane>

            <a-tab-pane key="assertions" title="断言结果">
              <div class="assertions-result">
                <a-table
                  v-if="debugResult.assertions?.length"
                  :columns="assertionColumns"
                  :data="debugResult.assertions"
                  :pagination="false"
                  size="small"
                  :bordered="true"
                >
                  <template #status="{ record }">
                    <a-tag :color="record.passed ? 'green' : 'red'" size="small">
                      {{ record.passed ? '通过' : '失败' }}
                    </a-tag>
                  </template>
                  <template #type="{ record }">
                    <a-tag size="small">{{ assertionTypeMap[record.assertion_type] || record.assertion_type }}</a-tag>
                  </template>
                  <template #actual="{ record }">
                    <span :class="{ 'value-mismatch': !record.passed }" :title="record.actual ?? '-'">{{ record.actual ?? '-' }}</span>
                  </template>
                  <template #expected="{ record }">
                    <span :title="record.expected">{{ record.expected }}</span>
                  </template>
                  <template #error="{ record }">
                    <span v-if="record.error" class="error-text" :title="record.error">{{ record.error }}</span>
                    <span v-else>-</span>
                  </template>
                </a-table>
                <a-empty v-else description="未配置断言" />
              </div>
            </a-tab-pane>

            <a-tab-pane key="snapshot" title="请求快照">
              <div class="request-snapshot">
                <JsonViewer
                  v-if="debugResult.request_snapshot"
                  :content="debugResult.request_snapshot"
                  max-height="400px"
                />
                <a-empty v-else description="无请求快照" />
              </div>
            </a-tab-pane>
          </a-tabs>
        </template>
      </div>
    </div>

    <template #footer>
      <div style="display: flex; justify-content: space-between;">
        <a-button
          type="outline"
          status="success"
          :loading="debugLoading"
          @click="handleDebug"
        >
          发送请求
        </a-button>
        <a-space>
          <a-button @click="handleCancel">取消</a-button>
          <a-button type="primary" :loading="submitting" @click="handleSubmit">
            保存
          </a-button>
        </a-space>
      </div>
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
import { ref, reactive, watch, computed } from 'vue'
import { Message } from '@arco-design/web-vue'
import { IconSend } from '@arco-design/web-vue/es/icon'
import { getProjects } from '@/api/project'
import {
  createTestCase,
  updateTestCase,
  getTestCase,
  getModuleTree,
  getTemplates,
  importCurl,
  debugTestCase,
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
  DataRuleItem,
  AuthConfig,
  RunResult,
} from '@/api/apiTestCase'
import type { Project } from '@/api/project'
import JsonViewer from '@/components/JsonViewer.vue'
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

// 调试相关
const debugLoading = ref(false)
const showResponse = ref(false)
const debugResult = ref<RunResult | null>(null)
const responseTab = ref('body')

// 动态宽度
const drawerWidth = computed(() => showResponse.value ? '1400px' : '900px')

const rawContent = ref('')

const formData = reactive({
  id: undefined as number | undefined,
  project_id: 0,
  environment_id: undefined as number | undefined,
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
  priority: 'P2',
  status: 'draft',
  headers: [] as HeaderItem[],
  query_params: [] as QueryParamItem[],
  body_form: [] as BodyFormItem[],
  assertions: [] as AssertionItem[],
  data_rules: [] as DataRuleItem[],
  auth: { auth_type: 'none' } as AuthConfig,
})

// 监听visible
watch(() => props.visible, (val) => {
  visible.value = val
  if (val) {
    // 重置调试状态
    showResponse.value = false
    debugResult.value = null
    debugLoading.value = false
    responseTab.value = 'body'

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
  formData.environment_id = fullData.environment_id
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
  formData.priority = fullData.priority || 'P2'
  formData.status = fullData.status || 'draft'
  formData.headers = (fullData.headers || []).map(h => ({ ...h }))
  formData.query_params = (fullData.query_params || []).map(p => ({ ...p }))
  formData.body_form = (fullData.body_form || []).map(f => ({ ...f }))
  formData.assertions = (fullData.assertions || []).map(a => ({ ...a }))
  formData.data_rules = (fullData.data_rules || []).map(r => ({ ...r }))
  formData.auth = fullData.auth ? { ...fullData.auth } : { auth_type: 'none' }

  rawContent.value = fullData.body_raw?.content || ''
}

const resetForm = () => {
  formData.id = undefined
  formData.project_id = props.defaultProjectId || 0
  formData.environment_id = undefined
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
  formData.priority = 'P2'
  formData.status = 'draft'
  formData.headers = []
  formData.query_params = []
  formData.body_form = []
  formData.assertions = []
  formData.data_rules = []
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

const handleSubmit = async () => {
  if (!validate()) return

  submitting.value = true
  try {
    const bodyRaw = rawContent.value ? { content: rawContent.value } : undefined

    if (isEdit.value && formData.id) {
      const updateData: APITestCaseUpdate = {
        environment_id: formData.environment_id,
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
        priority: formData.priority,
        status: formData.status,
        headers: formData.headers,
        query_params: formData.query_params,
        body_form: formData.body_form,
        body_raw: bodyRaw,
        assertions: formData.assertions,
        data_rules: formData.data_rules,
        auth: formData.auth,
      }
      await updateTestCase(formData.id, updateData)
      Message.success('更新成功')
    } else {
      const createData: APITestCaseCreate = {
        project_id: formData.project_id,
        environment_id: formData.environment_id,
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
        priority: formData.priority,
        status: formData.status,
        headers: formData.headers,
        query_params: formData.query_params,
        body_form: formData.body_form,
        body_raw: bodyRaw,
        assertions: formData.assertions,
        data_rules: formData.data_rules,
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

// 调试请求
const handleDebug = async () => {
  if (!formData.url) {
    Message.warning('请输入请求URL')
    activeTab.value = 'request'
    return
  }

  debugLoading.value = true
  showResponse.value = true
  debugResult.value = null
  responseTab.value = 'body'

  try {
    const result = await debugTestCase({
      environment_id: formData.environment_id,
      method: formData.method,
      url: formData.url,
      body_type: formData.body_type,
      headers: formData.headers,
      query_params: formData.query_params,
      body_form: formData.body_form,
      body_raw: rawContent.value || undefined,
      auth: formData.auth,
      setup_script: formData.setup_script || undefined,
      teardown_script: formData.teardown_script || undefined,
      assertions: formData.assertions.map(a => ({
        assertion_type: a.assertion_type,
        field: a.field,
        operator: a.operator,
        expected: a.expected || '',
      })),
      data_rules: formData.data_rules,
    })
    debugResult.value = result
  } catch (e: any) {
    Message.error(e?.detail || '请求执行失败')
    showResponse.value = false
  } finally {
    debugLoading.value = false
  }
}

// 断言表格列定义
const assertionColumns = [
  { title: '状态', dataIndex: 'passed', slotName: 'status', width: 80 },
  { title: '类型', dataIndex: 'assertion_type', slotName: 'type', width: 120 },
  { title: '实际值', dataIndex: 'actual', slotName: 'actual', ellipsis: true },
  { title: '期望值', dataIndex: 'expected', slotName: 'expected', ellipsis: true },
  { title: '错误', dataIndex: 'error', slotName: 'error', ellipsis: true },
]

// 断言类型映射
const assertionTypeMap: Record<string, string> = {
  status_code: '状态码',
  jsonpath: 'JSONPath',
  header: '响应头',
  response_time: '响应时间',
  body_contains: 'Body包含',
}

// 状态颜色
const getStatusColor = (status: string) => {
  const map: Record<string, string> = {
    pass: 'green',
    fail: 'red',
    error: 'orange',
  }
  return map[status] || 'gray'
}

// 格式化大小
const formatSize = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
</script>

<style scoped>
:deep(.arco-drawer) {
  overflow: hidden;
  contain: layout;
}

:deep(.arco-drawer-body) {
  padding: 0;
  overflow: hidden;
  contain: layout;
}

:deep(.arco-tabs-content) {
  padding: 20px;
}

.drawer-body {
  display: flex;
  height: 100%;
  overflow: hidden;
}

.drawer-body.has-response {
  gap: 0;
}

.editor-panel {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  overflow-x: hidden;
}

.response-panel {
  width: 450px;
  border-left: 1px solid var(--color-border-2);
  display: flex;
  flex-direction: column;
  background: var(--color-bg-1);
  overflow: hidden;
}

.response-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border-2);
  background: var(--color-fill-1);
}

.response-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-1);
}

.response-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px 20px;
  color: var(--color-text-3);
}

.response-status {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border-2);
}

.status-code {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-1);
}

.duration,
.size {
  font-size: 13px;
  color: var(--color-text-3);
}

.response-tabs {
  flex: 1;
  overflow: hidden;
}

:deep(.response-tabs .arco-tabs-content) {
  padding: 0;
  height: calc(100% - 36px);
  overflow-y: auto;
}

:deep(.response-tabs .arco-tabs-nav) {
  padding: 0 12px;
}

.response-body,
.request-snapshot {
  padding: 12px 16px;
}

.response-body pre,
.request-snapshot pre {
  margin: 0;
  padding: 12px;
  background: var(--color-fill-1);
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.6;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.assertions-result {
  padding: 12px 16px;
  overflow: auto;
}

.assertions-result :deep(.arco-table) {
  overflow: visible;
}

.assertions-result :deep(.arco-tooltip) {
  position: relative;
}

.assertion-pass {
  background-color: var(--color-success-light-1);
}

.assertion-fail {
  background-color: var(--color-danger-light-1);
}

.value-mismatch {
  color: var(--color-danger-6);
  font-weight: 500;
}

.error-text {
  color: var(--color-danger-6);
  font-size: 12px;
}

.assertion-actual {
  font-size: 12px;
  color: var(--color-text-3);
}
</style>

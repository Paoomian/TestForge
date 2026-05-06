<template>
  <a-drawer
    v-model:visible="visible"
    :title="isEdit ? '编辑用例' : '新建用例'"
    width="800px"
    unmount-on-close
    @cancel="handleCancel"
  >
    <a-form :model="formData" layout="vertical">
      <a-tabs default-active-key="basic">
        <!-- 基本信息 -->
        <a-tab-pane key="basic" title="基本信息">
          <a-form-item label="用例名称" required>
            <a-input v-model="formData.name" placeholder="请输入用例名称" />
          </a-form-item>

          <a-form-item label="所属项目" required>
            <a-select
              v-model="formData.project_id"
              placeholder="选择项目"
              :disabled="isEdit"
            >
              <a-option
                v-for="project in projects"
                :key="project.id"
                :value="project.id"
              >
                {{ project.name }}
              </a-option>
            </a-select>
          </a-form-item>

          <a-form-item label="所属模块">
            <a-tree-select
              v-model="formData.module"
              :data="moduleTreeData"
              placeholder="选择已有模块或输入新模块路径"
              allow-clear
              allow-search
              :filter-tree-node="filterModuleTree"
            />
          </a-form-item>

          <a-form-item label="用例描述">
            <a-textarea
              v-model="formData.description"
              placeholder="请输入用例描述"
              :auto-size="{ minRows: 3, maxRows: 6 }"
            />
          </a-form-item>

          <a-row :gutter="16">
            <a-col :span="8">
              <a-form-item label="优先级">
                <a-select v-model="formData.priority">
                  <a-option value="low">低</a-option>
                  <a-option value="medium">中</a-option>
                  <a-option value="high">高</a-option>
                  <a-option value="critical">紧急</a-option>
                </a-select>
              </a-form-item>
            </a-col>

            <a-col :span="8">
              <a-form-item label="状态">
                <a-select v-model="formData.status">
                  <a-option value="active">启用</a-option>
                  <a-option value="deprecated">废弃</a-option>
                  <a-option value="draft">草稿</a-option>
                </a-select>
              </a-form-item>
            </a-col>

            <a-col :span="8">
              <a-form-item label="标签">
                <a-select
                  v-model="formData.tags"
                  placeholder="添加标签"
                  multiple
                  allow-create
                  allow-clear
                />
              </a-form-item>
            </a-col>
          </a-row>
        </a-tab-pane>

        <!-- 请求配置 -->
        <a-tab-pane key="request" title="请求配置">
          <a-form-item label="请求方法" required>
            <a-select v-model="formData.method">
              <a-option value="GET">GET</a-option>
              <a-option value="POST">POST</a-option>
              <a-option value="PUT">PUT</a-option>
              <a-option value="DELETE">DELETE</a-option>
              <a-option value="PATCH">PATCH</a-option>
            </a-select>
          </a-form-item>

          <a-form-item label="请求URL" required>
            <a-input
              v-model="formData.url"
              placeholder="例如: /api/v1/users"
            />
          </a-form-item>

          <a-form-item label="请求头 (Headers)">
            <JsonEditor
              v-model="headersJson"
              height="200px"
            />
          </a-form-item>

          <a-form-item label="查询参数 (Query Params)">
            <JsonEditor
              v-model="queryParamsJson"
              height="150px"
            />
          </a-form-item>

          <a-form-item label="请求体 (Body)">
            <a-textarea
              v-model="formData.body"
              placeholder="请输入请求体内容"
              :auto-size="{ minRows: 6, maxRows: 12 }"
            />
          </a-form-item>
        </a-tab-pane>

        <!-- 断言配置 -->
        <a-tab-pane key="assertions" title="断言配置">
          <AssertionEditor
            v-model="formData.assertions"
            v-model:assertion-logic="assertionLogic"
          />
        </a-tab-pane>

        <!-- 高级配置 -->
        <a-tab-pane key="advanced" title="高级配置">
          <a-form-item label="变量 (Variables)">
            <JsonEditor
              v-model="variablesJson"
              height="150px"
            />
          </a-form-item>

          <a-form-item label="前置脚本 (Setup Script)">
            <a-textarea
              v-model="formData.setup_script"
              placeholder="在请求发送前执行的脚本"
              :auto-size="{ minRows: 4, maxRows: 8 }"
            />
          </a-form-item>

          <a-form-item label="后置脚本 (Teardown Script)">
            <a-textarea
              v-model="formData.teardown_script"
              placeholder="在请求完成后执行的脚本"
              :auto-size="{ minRows: 4, maxRows: 8 }"
            />
          </a-form-item>
        </a-tab-pane>
      </a-tabs>
    </a-form>

    <template #footer>
      <a-space>
        <a-button @click="handleCancel">取消</a-button>
        <a-button type="primary" :loading="submitting" @click="handleSubmit">
          保存
        </a-button>
      </a-space>
    </template>
  </a-drawer>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import { getProjects } from '@/api/project'
import { createTestCase, updateTestCase, getModuleTree } from '@/api/apiTestCase'
import type { Project } from '@/api/project'
import type { APITestCase, APITestCaseCreate, APITestCaseUpdate, ModuleTree } from '@/api/apiTestCase'
import JsonEditor from '@/components/JsonEditor.vue'
import AssertionEditor from './AssertionEditor.vue'

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
const projects = ref<Project[]>([])
const assertionLogic = ref<'and' | 'or'>('and')
const moduleTreeRaw = ref<ModuleTree[]>([])

interface ModuleTreeNode {
  key: string
  title: string
  children?: ModuleTreeNode[]
}

const moduleTreeData = computed(() => {
  const projectId = formData.project_id
  if (!projectId) return []

  const projectModules = moduleTreeRaw.value.find(m => m.project_id === projectId)
  if (!projectModules || projectModules.modules.length === 0) return []

  const nodes: ModuleTreeNode[] = []
  const nodeMap = new Map<string, ModuleTreeNode>()

  projectModules.modules.forEach(modulePath => {
    const parts = modulePath.split('/')
    let currentPath = ''

    parts.forEach((part, index) => {
      const parentPath = currentPath
      currentPath = currentPath ? `${currentPath}/${part}` : part

      if (!nodeMap.has(currentPath)) {
        const node: ModuleTreeNode = {
          key: currentPath,
          title: part,
          children: []
        }
        nodeMap.set(currentPath, node)

        if (index === 0) {
          nodes.push(node)
        } else {
          const parentNode = nodeMap.get(parentPath)
          if (parentNode) {
            parentNode.children!.push(node)
          }
        }
      }
    })
  })

  return nodes
})

const filterModuleTree = (searchValue: string, nodeData: any) => {
  return nodeData.title.toLowerCase().includes(searchValue.toLowerCase())
}

const loadModuleTree = async () => {
  try {
    moduleTreeRaw.value = await getModuleTree()
  } catch (error) {
    console.error('Failed to load module tree:', error)
  }
}

const formData = reactive<APITestCaseCreate & { id?: number }>({
  project_id: 0,
  name: '',
  description: '',
  module: '',
  method: 'GET',
  url: '',
  headers: {},
  body: '',
  query_params: {},
  variables: {},
  setup_script: '',
  teardown_script: '',
  assertions: [],
  tags: [],
  priority: 'medium',
  status: 'active'
})

const headersJson = ref('{}')
const queryParamsJson = ref('{}')
const variablesJson = ref('{}')

watch(() => props.visible, (newValue) => {
  visible.value = newValue
  if (newValue) {
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

watch(visible, (newValue) => {
  emit('update:visible', newValue)
})

watch(headersJson, (newValue) => {
  try {
    formData.headers = JSON.parse(newValue)
  } catch (e) {
    // 忽略JSON解析错误
  }
})

watch(queryParamsJson, (newValue) => {
  try {
    formData.query_params = JSON.parse(newValue)
  } catch (e) {
    // 忽略JSON解析错误
  }
})

watch(variablesJson, (newValue) => {
  try {
    formData.variables = JSON.parse(newValue)
  } catch (e) {
    // 忽略JSON解析错误
  }
})

const loadProjects = async () => {
  try {
    projects.value = await getProjects()
    if (projects.value.length === 0 && !isEdit.value) {
      Message.warning('暂无项目，请先创建项目')
      visible.value = false
    }
  } catch (error) {
    Message.error('加载项目列表失败')
  }
}

const loadEditData = (data: APITestCase) => {
  formData.id = data.id
  formData.project_id = data.project_id
  formData.name = data.name
  formData.description = data.description
  formData.module = data.module
  formData.method = data.method
  formData.url = data.url
  formData.headers = data.headers
  formData.body = data.body
  formData.query_params = data.query_params
  formData.variables = data.variables
  formData.setup_script = data.setup_script
  formData.teardown_script = data.teardown_script
  formData.assertions = data.assertions
  formData.tags = data.tags
  formData.priority = data.priority
  formData.status = data.status

  headersJson.value = JSON.stringify(data.headers, null, 2)
  queryParamsJson.value = JSON.stringify(data.query_params, null, 2)
  variablesJson.value = JSON.stringify(data.variables, null, 2)
}

const resetForm = () => {
  formData.id = undefined
  formData.project_id = props.defaultProjectId || 0
  formData.name = ''
  formData.description = ''
  formData.module = ''
  formData.method = 'GET'
  formData.url = ''
  formData.headers = {}
  formData.body = ''
  formData.query_params = {}
  formData.variables = {}
  formData.setup_script = ''
  formData.teardown_script = ''
  formData.assertions = []
  formData.tags = []
  formData.priority = 'medium'
  formData.status = 'active'

  headersJson.value = '{}'
  queryParamsJson.value = '{}'
  variablesJson.value = '{}'
}

const handleCancel = () => {
  visible.value = false
}

const handleSubmit = async () => {
  if (!formData.name) {
    Message.warning('请输入用例名称')
    return
  }
  if (!formData.project_id) {
    Message.warning(projects.value.length === 0 ? '暂无项目，请先去创建项目' : '请选择所属项目')
    return
  }
  if (!formData.url) {
    Message.warning('请输入请求URL')
    return
  }

  submitting.value = true
  try {
    if (isEdit.value && formData.id) {
      const updateData: APITestCaseUpdate = {
        name: formData.name,
        description: formData.description,
        module: formData.module,
        method: formData.method,
        url: formData.url,
        headers: formData.headers,
        body: formData.body,
        query_params: formData.query_params,
        variables: formData.variables,
        setup_script: formData.setup_script,
        teardown_script: formData.teardown_script,
        assertions: formData.assertions,
        tags: formData.tags,
        priority: formData.priority,
        status: formData.status
      }
      await updateTestCase(formData.id, updateData)
      Message.success('更新成功')
    } else {
      await createTestCase(formData)
      Message.success('创建成功')
    }
    visible.value = false
    emit('success')
  } catch (error) {
    Message.error(isEdit.value ? '更新失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadProjects()
})
</script>

<style scoped>
:deep(.arco-drawer-body) {
  padding: 0;
}

:deep(.arco-tabs-content) {
  padding: 20px;
}
</style>

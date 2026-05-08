<template>
  <a-drawer
    :visible="visible"
    title="环境管理"
    :width="700"
    :footer="false"
    @cancel="emit('update:visible', false)"
  >
    <div style="margin-bottom: 16px; text-align: right;">
      <a-button type="primary" size="small" @click="openCreateModal">
        <template #icon><icon-plus /></template>
        新增环境
      </a-button>
    </div>

    <a-table :columns="columns" :data="environments" :loading="loading" :pagination="false">
      <template #name="{ record }">
        <a-tag :color="getEnvColor(record.name)">{{ record.name }}</a-tag>
      </template>
      <template #variables="{ record }">
        <a-space wrap>
          <a-tag v-for="(_, key) in record.variables" :key="key" size="small" color="gray">
            {{ key }}
          </a-tag>
          <span v-if="!record.variables || Object.keys(record.variables).length === 0" style="color: var(--color-text-3)">
            无变量
          </span>
        </a-space>
      </template>
      <template #actions="{ record }">
        <a-space>
          <a-button type="text" size="small" @click="openEditModal(record)">编辑</a-button>
          <a-popconfirm content="确认删除该环境？" @ok="handleDelete(record.id)">
            <a-button type="text" size="small" status="danger">删除</a-button>
          </a-popconfirm>
        </a-space>
      </template>
    </a-table>

    <!-- 新增/编辑弹窗 -->
    <a-modal
      v-model:visible="modalVisible"
      :title="isEdit ? '编辑环境' : '新增环境'"
      :width="560"
      :loading="submitting"
      @ok="handleSubmit"
      @cancel="resetForm"
    >
      <a-form :model="formData" layout="vertical">
        <a-form-item label="环境名称" required>
          <a-input v-model="formData.name" placeholder="如：开发环境、测试环境、生产环境" />
        </a-form-item>
        <a-form-item label="基础地址">
          <a-input v-model="formData.base_url" placeholder="如：http://localhost:8000" />
        </a-form-item>
        <a-form-item label="环境变量">
          <div class="variables-editor">
            <div v-for="(item, index) in variablesList" :key="index" class="variable-row">
              <a-input v-model="item.key" placeholder="变量名" style="width: 35%" />
              <a-input v-model="item.value" placeholder="变量值" style="width: 50%" />
              <a-button type="text" status="danger" size="small" @click="removeVariable(index)">
                <template #icon><icon-delete /></template>
              </a-button>
            </div>
            <a-button type="dashed" long @click="addVariable" style="margin-top: 8px">
              <template #icon><icon-plus /></template>
              添加变量
            </a-button>
          </div>
        </a-form-item>
      </a-form>
    </a-modal>
  </a-drawer>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { Message } from '@arco-design/web-vue'
import { getEnvironments, createEnvironment, updateEnvironment, deleteEnvironment } from '@/api/environment'
import type { Environment } from '@/api/apiTestCase'

const props = defineProps<{
  visible: boolean
  projectId: number | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
}>()

const loading = ref(false)
const submitting = ref(false)
const environments = ref<Environment[]>([])
const modalVisible = ref(false)
const isEdit = ref(false)
const editingId = ref<number | null>(null)

const formData = reactive({
  name: '',
  base_url: ''
})

interface VariableItem {
  key: string
  value: string
}

const variablesList = ref<VariableItem[]>([])

const columns = [
  { title: '环境名称', dataIndex: 'name', slotName: 'name', width: 120 },
  { title: '基础地址', dataIndex: 'base_url', ellipsis: true },
  { title: '变量', slotName: 'variables', width: 200 },
  { title: '操作', slotName: 'actions', width: 120, align: 'center' as const }
]

const envColors: Record<string, string> = {
  '开发': 'blue', '开发环境': 'blue', 'dev': 'blue', 'development': 'blue',
  '测试': 'green', '测试环境': 'green', 'test': 'green', 'testing': 'green',
  '预发': 'orange', '预发环境': 'orange', 'staging': 'orange',
  '生产': 'red', '生产环境': 'red', 'prod': 'red', 'production': 'red'
}

function getEnvColor(name: string): string {
  const lower = name.toLowerCase()
  for (const [key, color] of Object.entries(envColors)) {
    if (lower.includes(key)) return color
  }
  return 'gray'
}

async function loadEnvironments() {
  if (!props.projectId) return
  loading.value = true
  try {
    environments.value = await getEnvironments(props.projectId)
  } catch {
    Message.error('加载环境列表失败')
  } finally {
    loading.value = false
  }
}

function openCreateModal() {
  isEdit.value = false
  editingId.value = null
  resetForm()
  modalVisible.value = true
}

function openEditModal(env: Environment) {
  isEdit.value = true
  editingId.value = env.id
  formData.name = env.name
  formData.base_url = env.base_url || ''
  variablesList.value = Object.entries(env.variables || {}).map(([key, value]) => ({ key, value }))
  modalVisible.value = true
}

function resetForm() {
  formData.name = ''
  formData.base_url = ''
  variablesList.value = []
}

function addVariable() {
  variablesList.value.push({ key: '', value: '' })
}

function removeVariable(index: number) {
  variablesList.value.splice(index, 1)
}

function buildVariables(): Record<string, string> {
  const result: Record<string, string> = {}
  for (const item of variablesList.value) {
    if (item.key.trim()) {
      result[item.key.trim()] = item.value
    }
  }
  return result
}

async function handleSubmit() {
  if (!formData.name.trim()) {
    Message.warning('请输入环境名称')
    modalVisible.value = true
    return
  }
  if (!props.projectId) return

  submitting.value = true
  const variables = buildVariables()

  try {
    if (isEdit.value && editingId.value) {
      await updateEnvironment(editingId.value, {
        name: formData.name.trim(),
        base_url: formData.base_url.trim() || undefined,
        variables
      })
      Message.success('环境更新成功')
    } else {
      await createEnvironment({
        project_id: props.projectId,
        name: formData.name.trim(),
        base_url: formData.base_url.trim() || undefined,
        variables
      })
      Message.success('环境创建成功')
    }
    modalVisible.value = false
    loadEnvironments()
  } catch {
    Message.error(isEdit.value ? '环境更新失败' : '环境创建失败')
  } finally {
    submitting.value = false
  }
}

async function handleDelete(id: number) {
  try {
    await deleteEnvironment(id)
    Message.success('环境删除成功')
    loadEnvironments()
  } catch {
    Message.error('环境删除失败')
  }
}

watch(() => props.visible, (val) => {
  if (val && props.projectId) {
    loadEnvironments()
  }
})
</script>

<style scoped>
.variables-editor {
  width: 100%;
}
.variable-row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  align-items: center;
}
</style>

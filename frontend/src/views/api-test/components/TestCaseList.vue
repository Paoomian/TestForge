<template>
  <div class="test-case-list">
    <!-- 搜索栏 -->
    <a-card :bordered="false" style="margin-bottom: 16px">
      <a-space wrap>
        <a-input
          v-model="searchForm.keyword"
          placeholder="搜索用例名称"
          style="width: 200px"
          allow-clear
          @press-enter="handleSearch"
        >
          <template #prefix>
            <icon-search />
          </template>
        </a-input>
        <a-select
          v-model="searchForm.priority"
          placeholder="优先级"
          style="width: 120px"
          allow-clear
        >
          <a-option value="low">低</a-option>
          <a-option value="medium">中</a-option>
          <a-option value="high">高</a-option>
          <a-option value="critical">紧急</a-option>
        </a-select>
        <a-select
          v-model="searchForm.status"
          placeholder="状态"
          style="width: 120px"
          allow-clear
        >
          <a-option value="active">启用</a-option>
          <a-option value="deprecated">废弃</a-option>
          <a-option value="draft">草稿</a-option>
        </a-select>
        <a-button type="primary" @click="handleSearch">
          <template #icon><icon-search /></template>
          搜索
        </a-button>
        <a-button @click="handleReset">
          <template #icon><icon-refresh /></template>
          重置
        </a-button>
      </a-space>
    </a-card>

    <!-- 操作栏 -->
    <a-card :bordered="false" style="margin-bottom: 16px">
      <a-space>
        <a-button
          type="primary"
          @click="handleCreate"
        >
          <template #icon><icon-plus /></template>
          新建用例
        </a-button>
        <a-button
          :disabled="selectedRowKeys.length === 0"
          @click="showBatchTagModal = true"
        >
          <template #icon><icon-tags /></template>
          批量打标签
        </a-button>
        <a-popconfirm
          content="确定要删除选中的用例吗？"
          @ok="handleBatchDelete"
        >
          <a-button
            status="danger"
            :disabled="selectedRowKeys.length === 0"
          >
            <template #icon><icon-delete /></template>
            批量删除
          </a-button>
        </a-popconfirm>
      </a-space>
    </a-card>

    <!-- 表格 -->
    <a-table
      :columns="columns"
      :data="tableData"
      :loading="loading"
      :pagination="pagination"
      :row-selection="rowSelection"
      @page-change="handlePageChange"
    >
      <template #method="{ record }">
        <a-tag :color="getMethodColor(record.method)">{{ record.method }}</a-tag>
      </template>
      <template #priority="{ record }">
        <a-tag :color="getPriorityColor(record.priority)">
          {{ getPriorityText(record.priority) }}
        </a-tag>
      </template>
      <template #status="{ record }">
        <a-tag :color="getStatusColor(record.status)">
          {{ getStatusText(record.status) }}
        </a-tag>
      </template>
      <template #tags="{ record }">
        <a-space wrap>
          <a-tag v-for="tag in record.tags" :key="tag" size="small">{{ tag }}</a-tag>
        </a-space>
      </template>
      <template #actions="{ record }">
        <a-space>
          <a-button type="text" size="small" @click="handleEdit(record)">
            编辑
          </a-button>
          <a-button type="text" size="small" @click="handleCopy(record)">
            复制
          </a-button>
          <a-button type="text" size="small" @click="handleViewHistory(record)">
            历史
          </a-button>
          <a-popconfirm
            content="确定要删除该用例吗？"
            @ok="handleDelete(record)"
          >
            <a-button type="text" size="small" status="danger">
              删除
            </a-button>
          </a-popconfirm>
        </a-space>
      </template>
    </a-table>

    <!-- 批量打标签弹窗 -->
    <a-modal
      v-model:visible="showBatchTagModal"
      title="批量打标签"
      @ok="handleBatchTag"
    >
      <a-form layout="vertical">
        <a-form-item label="操作类型">
          <a-radio-group v-model="batchTagForm.operation">
            <a-radio value="add">添加标签</a-radio>
            <a-radio value="remove">移除标签</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="标签">
          <a-select
            v-model="batchTagForm.tags"
            placeholder="请输入标签"
            multiple
            allow-create
            allow-clear
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { Message } from '@arco-design/web-vue'
import {
  getTestCases,
  deleteTestCase,
  copyTestCase,
  batchTag,
  batchDelete
} from '@/api/apiTestCase'
import type { APITestCase } from '@/api/apiTestCase'

interface Props {
  projectId?: number
  module?: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'edit', record: APITestCase): void
  (e: 'viewHistory', record: APITestCase): void
  (e: 'create'): void
}>()

const loading = ref(false)
const tableData = ref<APITestCase[]>([])
const selectedRowKeys = ref<number[]>([])
const showBatchTagModal = ref(false)

const searchForm = reactive({
  keyword: '',
  priority: '',
  status: ''
})

const batchTagForm = reactive({
  operation: 'add' as 'add' | 'remove',
  tags: [] as string[]
})

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0
})

const columns = [
  { title: 'ID', dataIndex: 'id', width: 80 },
  { title: '用例名称', dataIndex: 'name', width: 200 },
  { title: '请求方法', dataIndex: 'method', slotName: 'method', width: 100 },
  { title: '模块', dataIndex: 'module', width: 150 },
  { title: '标签', dataIndex: 'tags', slotName: 'tags', width: 150 },
  { title: '优先级', dataIndex: 'priority', slotName: 'priority', width: 100 },
  { title: '状态', dataIndex: 'status', slotName: 'status', width: 100 },
  { title: '操作', slotName: 'actions', width: 250, fixed: 'right' }
]

const rowSelection = computed(() => ({
  type: 'checkbox' as const,
  selectedRowKeys: selectedRowKeys.value,
  onChange: (keys: number[]) => {
    selectedRowKeys.value = keys
  }
}))

const getMethodColor = (method: string) => {
  const colors: Record<string, string> = {
    GET: 'blue',
    POST: 'green',
    PUT: 'orange',
    DELETE: 'red',
    PATCH: 'purple'
  }
  return colors[method] || 'gray'
}

const getPriorityColor = (priority: string) => {
  const colors: Record<string, string> = {
    low: 'gray',
    medium: 'blue',
    high: 'orange',
    critical: 'red'
  }
  return colors[priority] || 'gray'
}

const getPriorityText = (priority: string) => {
  const texts: Record<string, string> = {
    low: '低',
    medium: '中',
    high: '高',
    critical: '紧急'
  }
  return texts[priority] || priority
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    active: 'green',
    deprecated: 'red',
    draft: 'gray'
  }
  return colors[status] || 'gray'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    active: '启用',
    deprecated: '废弃',
    draft: '草稿'
  }
  return texts[status] || status
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.current - 1) * pagination.pageSize,
      limit: pagination.pageSize,
      project_id: props.projectId,
      module: props.module,
      keyword: searchForm.keyword || undefined,
      priority: searchForm.priority || undefined,
      status: searchForm.status || undefined
    }
    const data = await getTestCases(params)
    tableData.value = data
    pagination.total = data.length
  } catch (error) {
    Message.error('加载用例列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.current = 1
  loadData()
}

const handleReset = () => {
  searchForm.keyword = ''
  searchForm.priority = ''
  searchForm.status = ''
  handleSearch()
}

const handlePageChange = (page: number) => {
  pagination.current = page
  loadData()
}

const handleCreate = () => {
  emit('create')
}

const handleEdit = (record: APITestCase) => {
  emit('edit', record)
}

const handleCopy = async (record: APITestCase) => {
  try {
    await copyTestCase(record.id)
    Message.success('复制成功')
    loadData()
  } catch (error) {
    Message.error('复制失败')
  }
}

const handleDelete = async (record: APITestCase) => {
  try {
    await deleteTestCase(record.id)
    Message.success('删除成功')
    loadData()
  } catch (error) {
    Message.error('删除失败')
  }
}

const handleViewHistory = (record: APITestCase) => {
  emit('viewHistory', record)
}

const handleBatchTag = async () => {
  if (batchTagForm.tags.length === 0) {
    Message.warning('请输入标签')
    return
  }

  try {
    await batchTag(selectedRowKeys.value, batchTagForm.tags, batchTagForm.operation)
    Message.success('操作成功')
    showBatchTagModal.value = false
    batchTagForm.tags = []
    selectedRowKeys.value = []
    loadData()
  } catch (error) {
    Message.error('操作失败')
  }
}

const handleBatchDelete = async () => {
  try {
    await batchDelete(selectedRowKeys.value)
    Message.success('删除成功')
    selectedRowKeys.value = []
    loadData()
  } catch (error) {
    Message.error('删除失败')
  }
}

defineExpose({
  refresh: loadData
})
</script>

<style scoped>
.test-case-list {
  height: 100%;
}
</style>

<template>
  <div class="test-case-list">
    <template v-if="props.projectId">
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
          <a-option value="P0">P0 致命</a-option>
          <a-option value="P1">P1 严重</a-option>
          <a-option value="P2">P2 一般</a-option>
          <a-option value="P3">P3 轻微</a-option>
        </a-select>
        <a-select
          v-model="searchForm.status"
          placeholder="状态"
          style="width: 120px"
          allow-clear
        >
          <a-option value="draft">草稿</a-option>
          <a-option value="reviewed">已评审</a-option>
          <a-option value="deprecated">已废弃</a-option>
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
          type="primary"
          status="success"
          @click="showExcelImport = true"
        >
          <template #icon><icon-import /></template>
          导入Excel
        </a-button>
        <a-button
          type="primary"
          status="success"
          :disabled="selectedRowKeys.length === 0"
          @click="handleBatchRun"
        >
          <template #icon><icon-play-arrow /></template>
          批量执行
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
      v-if="props.projectId"
      :columns="columns"
      :data="tableData"
      :loading="loading"
      :pagination="pagination"
      :row-selection="{ type: 'checkbox' }"
      v-model:selectedKeys="selectedRowKeys"
      row-key="id"
      @page-change="handlePageChange"
    >
      <template #case_number="{ record }">
        <span :title="record.case_number">{{ record.case_number }}</span>
      </template>
      <template #name="{ record }">
        <span :title="record.name">{{ record.name }}</span>
      </template>
      <template #module="{ record }">
        <span :title="record.module">{{ record.module || '-' }}</span>
      </template>
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
      <template #environment="{ record }">
        <span v-if="record.environment_name">
          <a-tag color="arcoblue" size="small">{{ record.environment_name }}</a-tag>
        </span>
        <span v-else style="color: var(--color-text-3);">-</span>
      </template>
      <template #actions="{ record }">
        <a-space>
          <a-button type="text" size="small" @click="handleEdit(record)">
            编辑
          </a-button>
          <a-button type="text" size="small" @click="handleDebug(record)">
            调试
          </a-button>
          <a-button type="text" size="small" @click="handleCopy(record)">
            复制
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
    </template>

    <!-- 未选中项目时的提示 -->
    <a-empty v-else description="请先在左侧选择项目或模块" style="margin-top: 120px" />

    <!-- Excel 导入弹窗 -->
    <ExcelImportModal
      v-model:visible="showExcelImport"
      :project-id="props.projectId || 0"
      @success="handleImportSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import {
  getTestCases,
  deleteTestCase,
  copyTestCase,
  batchDelete
} from '@/api/apiTestCase'
import type { APITestCase } from '@/api/apiTestCase'
import ExcelImportModal from './ExcelImportModal.vue'

interface Props {
  projectId?: number
  module?: string
}

const props = defineProps<Props>()
const router = useRouter()

watch(() => [props.projectId, props.module], () => {
  pagination.current = 1
  loadData()
}, { immediate: false })

const emit = defineEmits<{
  (e: 'edit', record: APITestCase): void
  (e: 'create'): void
  (e: 'batch-run', cases: APITestCase[]): void
}>()

const loading = ref(false)
const tableData = ref<APITestCase[]>([])
const selectedRowKeys = ref<number[]>([])
const showExcelImport = ref(false)

const searchForm = reactive({
  keyword: '',
  priority: '',
  status: ''
})

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0
})

const columns = [
  { title: '编号', dataIndex: 'case_number', slotName: 'case_number', width: 180, ellipsis: true },
  { title: '用例名称', dataIndex: 'name', slotName: 'name', width: 200, ellipsis: true },
  { title: '请求方法', dataIndex: 'method', slotName: 'method', width: 100 },
  { title: '模块', dataIndex: 'module', slotName: 'module', width: 150, ellipsis: true },
  { title: '优先级', dataIndex: 'priority', slotName: 'priority', width: 100 },
  { title: '状态', dataIndex: 'status', slotName: 'status', width: 100 },
  { title: '环境', dataIndex: 'environment_id', slotName: 'environment', width: 120 },
  { title: '操作', slotName: 'actions', width: 250, fixed: 'right' as const }
]

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
    P0: 'red',
    P1: 'orange',
    P2: 'blue',
    P3: 'green',
  }
  return colors[priority] || 'gray'
}

const getPriorityText = (priority: string) => {
  const texts: Record<string, string> = {
    P0: 'P0 致命',
    P1: 'P1 严重',
    P2: 'P2 一般',
    P3: 'P3 轻微',
  }
  return texts[priority] || priority
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    draft: 'gray',
    reviewed: 'green',
    deprecated: 'red',
  }
  return colors[status] || 'gray'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    draft: '草稿',
    reviewed: '已评审',
    deprecated: '已废弃',
  }
  return texts[status] || status
}

const loadData = async () => {
  loading.value = true
  try {
    const params: Record<string, any> = {
      skip: (pagination.current - 1) * pagination.pageSize,
      limit: pagination.pageSize
    }
    if (props.projectId) {
      params.project_id = props.projectId
    }
    if (props.module) {
      params.module = props.module
    }
    if (searchForm.keyword) {
      params.keyword = searchForm.keyword
    }
    if (searchForm.priority) {
      params.priority = searchForm.priority
    }
    if (searchForm.status) {
      params.status = searchForm.status
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

const handleDebug = (record: APITestCase) => {
  router.push({ name: 'api-test-debug', params: { caseId: record.id } })
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

const handleBatchRun = () => {
  const selectedCases = tableData.value.filter(c => selectedRowKeys.value.includes(c.id))
  if (selectedCases.length === 0) {
    Message.warning('请先选择要执行的用例')
    return
  }
  emit('batch-run', selectedCases)
}

const handleImportSuccess = () => {
  loadData()
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

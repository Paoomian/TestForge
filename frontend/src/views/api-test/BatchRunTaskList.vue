<template>
  <div class="batch-run-task-list">
    <!-- 搜索栏 -->
    <a-card :bordered="false" style="margin-bottom: 16px">
      <a-space wrap>
        <a-select
          v-model="searchForm.status"
          placeholder="任务状态"
          style="width: 160px"
          allow-clear
        >
          <a-option value="pending">待执行</a-option>
          <a-option value="running">执行中</a-option>
          <a-option value="done">已完成</a-option>
          <a-option value="error">异常</a-option>
          <a-option value="cancelled">已取消</a-option>
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

    <!-- 表格 -->
    <a-card :bordered="false">
      <a-table
        :columns="columns"
        :data="tableData"
        :loading="loading"
        :pagination="pagination"
        @page-change="handlePageChange"
      >
        <template #status="{ record }">
          <a-tag :color="getStatusColor(record.status)">
            <template #icon>
              <icon-loading v-if="record.status === 'running'" spin />
            </template>
            {{ getStatusText(record.status) }}
          </a-tag>
        </template>

        <template #progress="{ record }">
          <a-progress
            :percent="record.progress / 100"
            :status="getProgressStatus(record)"
            size="small"
            :show-text="false"
            style="width: 120px"
          />
          <span style="margin-left: 8px; font-size: 12px; color: var(--color-text-3)">
            {{ record.progress.toFixed(0) }}%
          </span>
        </template>

        <template #stats="{ record }">
          <a-space>
            <span class="stat-pass">{{ record.pass_count }}</span>
            <span class="stat-fail">{{ record.fail_count }}</span>
            <span class="stat-error">{{ record.error_count }}</span>
          </a-space>
        </template>

        <template #duration="{ record }">
          {{ record.duration ? formatDuration(record.duration) : '-' }}
        </template>

        <template #created_at="{ record }">
          {{ formatTime(record.created_at) }}
        </template>

        <template #actions="{ record }">
          <a-space>
            <a-button type="text" size="small" @click="handleViewDetail(record)">
              详情
            </a-button>
            <a-button
              v-if="record.status === 'running' || record.status === 'pending'"
              type="text"
              size="small"
              status="warning"
              @click="handleCancel(record)"
            >
              取消
            </a-button>
            <a-popconfirm
              v-if="record.status !== 'running'"
              content="确定要删除该任务吗？"
              @ok="handleDelete(record)"
            >
              <a-button type="text" size="small" status="danger">
                删除
              </a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { getBatchRuns, cancelBatchRun, deleteBatchRun } from '@/api/batchRun'
import type { BatchRunListItem } from '@/api/batchRun'

const router = useRouter()
const loading = ref(false)
const tableData = ref<BatchRunListItem[]>([])

const searchForm = reactive({
  status: ''
})

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0
})

const columns = [
  { title: 'ID', dataIndex: 'id', width: 80 },
  { title: '任务名称', dataIndex: 'name', width: 200, ellipsis: true },
  { title: '状态', dataIndex: 'status', slotName: 'status', width: 100 },
  { title: '进度', dataIndex: 'progress', slotName: 'progress', width: 200 },
  { title: '结果', slotName: 'stats', width: 120 },
  { title: '耗时', slotName: 'duration', width: 100 },
  { title: '创建时间', slotName: 'created_at', width: 160 },
  { title: '操作', slotName: 'actions', width: 180, fixed: 'right' as const }
]

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    pending: 'gray',
    running: 'blue',
    done: 'green',
    error: 'red',
    cancelled: 'orange'
  }
  return colors[status] || 'gray'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: '待执行',
    running: '执行中',
    done: '已完成',
    error: '异常',
    cancelled: '已取消'
  }
  return texts[status] || status
}

const getProgressStatus = (record: BatchRunListItem) => {
  if (record.status === 'error') return 'danger'
  if (record.status === 'cancelled') return 'warning'
  if (record.status === 'done') {
    return record.fail_count > 0 || record.error_count > 0 ? 'warning' : 'success'
  }
  return 'normal'
}

const formatDuration = (ms: number) => {
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  const min = Math.floor(ms / 60000)
  const sec = ((ms % 60000) / 1000).toFixed(0)
  return `${min}m ${sec}s`
}

const formatTime = (time: string) => {
  return new Date(time).toLocaleString('zh-CN')
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await getBatchRuns({
      page: pagination.current,
      page_size: pagination.pageSize,
      status: searchForm.status || undefined
    })
    tableData.value = res.items
    pagination.total = res.total
  } catch (e) {
    Message.error('加载任务列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.current = 1
  loadData()
}

const handleReset = () => {
  searchForm.status = ''
  handleSearch()
}

const handlePageChange = (page: number) => {
  pagination.current = page
  loadData()
}

const handleViewDetail = (record: BatchRunListItem) => {
  router.push({ name: 'api-batch-task-detail', params: { taskId: record.id } })
}

const handleCancel = async (record: BatchRunListItem) => {
  try {
    await cancelBatchRun(record.id)
    Message.success('取消请求已提交')
    loadData()
  } catch (e: any) {
    Message.error(e?.message || '取消失败')
  }
}

const handleDelete = async (record: BatchRunListItem) => {
  try {
    await deleteBatchRun(record.id)
    Message.success('删除成功')
    loadData()
  } catch (e: any) {
    Message.error(e?.message || '删除失败')
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.batch-run-task-list {
  height: 100%;
}

.stat-pass {
  color: #00b42a;
  font-weight: 600;
}

.stat-pass::after {
  content: ' ✓';
  font-size: 10px;
}

.stat-fail {
  color: #f53f3f;
  font-weight: 600;
}

.stat-fail::after {
  content: ' ✗';
  font-size: 10px;
}

.stat-error {
  color: #ff7d00;
  font-weight: 600;
}

.stat-error::after {
  content: ' !';
  font-size: 10px;
}
</style>

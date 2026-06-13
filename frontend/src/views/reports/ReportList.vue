<template>
  <div class="report-list-page">
    <!-- 顶部筛选 -->
    <a-card class="filter-card" :bordered="false">
      <a-space :size="12">
        <a-select
          v-model="filterForm.test_type"
          placeholder="任务类型"
          style="width: 140px"
          allow-clear
        >
          <a-option value="api_batch">接口批量</a-option>
          <a-option value="api_scene">接口场景</a-option>
          <a-option value="ui_batch">UI批量</a-option>
        </a-select>
        <a-select
          v-model="filterForm.status"
          placeholder="任务状态"
          style="width: 140px"
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
        <a-button @click="handleReset">重置</a-button>
      </a-space>
    </a-card>

    <!-- 任务列表（按日期分组） -->
    <a-card :bordered="false" style="margin-top: 16px">
      <a-spin :loading="loading">
        <a-empty v-if="!loading && groupedData.length === 0" description="暂无任务记录" />

        <a-collapse
          v-else
          v-model:active-key="activeKeys"
          :bordered="false"
          expand-icon-position="left"
        >
          <a-collapse-item
            v-for="group in groupedData"
            :key="group.key"
            :disabled="group.items.length === 0"
          >
            <template #header>
              <div class="group-header">
                <span class="group-label">{{ group.label }}</span>
                <a-tag size="small" color="arcoblue">{{ group.items.length }} 条</a-tag>
              </div>
            </template>

            <a-table
              v-if="group.items.length > 0"
              :columns="columns"
              :data="group.items"
              :pagination="false"
              row-key="id"
              size="small"
            >
              <template #name="{ record }">
                <a-link @click="handleViewDetail(record)">{{ record.name }}</a-link>
              </template>

              <template #test_type="{ record }">
                <a-tag :color="getTypeColor(record.test_type)" size="small">
                  {{ getTypeText(record.test_type) }}
                </a-tag>
              </template>

              <template #status="{ record }">
                <a-tag :color="getStatusColor(record.status)" class="status-tag">
                  <template #icon>
                    <icon-loading v-if="record.status === 'running'" spin />
                  </template>
                  {{ getStatusText(record.status) }}
                </a-tag>
              </template>

              <template #progress="{ record }">
                <a-progress
                  :percent="getProgress(record)"
                  :status="getProgressStatus(record)"
                  size="small"
                  :show-text="false"
                  style="width: 120px"
                />
                <span style="margin-left: 8px; font-size: 12px; color: var(--color-text-3)">
                  {{ Math.round(getProgress(record) * 100) }}%
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
          </a-collapse-item>
        </a-collapse>
      </a-spin>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { getBatchRuns, deleteBatchRun, type BatchRunListItem } from '@/api/batchRun'

const router = useRouter()
const loading = ref(false)
const tableData = ref<BatchRunListItem[]>([])
const activeKeys = ref<string[]>(['today', 'yesterday'])

const filterForm = reactive({
  test_type: undefined as string | undefined,
  status: undefined as string | undefined,
})

const columns = [
  { title: '任务名称', slotName: 'name', width: 200, ellipsis: true },
  { title: '类型', slotName: 'test_type', width: 100 },
  { title: '状态', slotName: 'status', width: 100 },
  { title: '进度', slotName: 'progress', width: 200 },
  { title: '结果', slotName: 'stats', width: 130 },
  { title: '耗时', slotName: 'duration', width: 100 },
  { title: '创建时间', slotName: 'created_at', width: 160 },
  { title: '操作', slotName: 'actions', width: 130, fixed: 'right' as const },
]

// 日期分组
interface DateGroup {
  key: string
  label: string
  daysAgo: [number, number]
}

const dateGroups: DateGroup[] = [
  { key: 'today', label: '今天', daysAgo: [0, 0] },
  { key: 'yesterday', label: '昨天', daysAgo: [1, 1] },
  { key: 'before_yesterday', label: '前天', daysAgo: [2, 2] },
  { key: '3_days_ago', label: '3天前', daysAgo: [3, 3] },
  { key: '7_days_ago', label: '4-7天前', daysAgo: [4, 7] },
  { key: 'older', label: '更早', daysAgo: [8, 999] },
]

const groupedData = computed(() => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  const groups = dateGroups.map(group => ({
    ...group,
    items: [] as BatchRunListItem[],
  }))

  tableData.value.forEach(item => {
    const createdDate = new Date(item.created_at)
    createdDate.setHours(0, 0, 0, 0)
    const diffTime = today.getTime() - createdDate.getTime()
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
    const group = groups.find(g => diffDays >= g.daysAgo[0] && diffDays <= g.daysAgo[1])
    if (group) {
      group.items.push(item)
    } else {
      groups[groups.length - 1].items.push(item)
    }
  })

  return groups.filter(g => g.items.length > 0)
})

const loadData = async () => {
  loading.value = true
  try {
    const res = await getBatchRuns({
      page: 1,
      page_size: 200,
      test_type: filterForm.test_type,
      status: filterForm.status,
    })
    tableData.value = res.items
  } catch (e: any) {
    Message.error(e?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  loadData()
}

const handleReset = () => {
  filterForm.test_type = undefined
  filterForm.status = undefined
  loadData()
}

const handleViewDetail = (record: BatchRunListItem) => {
  if (record.test_type === 'ui_batch') {
    router.push({ name: 'ui-batch-run-detail', params: { runId: record.id } })
  } else {
    router.push({ name: 'api-batch-task-detail', params: { taskId: record.id } })
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

function getProgress(task: BatchRunListItem): number {
  if (!task.total_count) return 0
  return (task.pass_count + task.fail_count + task.error_count) / task.total_count
}

function getProgressStatus(task: BatchRunListItem): 'danger' | 'warning' | 'success' | 'normal' {
  if (task.status === 'error') return 'danger'
  if (task.status === 'cancelled') return 'warning'
  if (task.status === 'done') {
    return task.fail_count > 0 || task.error_count > 0 ? 'warning' : 'success'
  }
  return 'normal'
}

const getTypeColor = (type: string) => {
  const map: Record<string, string> = {
    api_batch: 'blue',
    api_scene: 'purple',
    ui_batch: 'green',
  }
  return map[type] || 'gray'
}

const getTypeText = (type: string) => {
  const map: Record<string, string> = {
    api_batch: '接口批量',
    api_scene: '接口场景',
    ui_batch: 'UI批量',
  }
  return map[type] || type
}

const getStatusColor = (status: string) => {
  const map: Record<string, string> = {
    pending: 'gray',
    running: 'blue',
    done: 'green',
    error: 'red',
    cancelled: 'orange',
  }
  return map[status] || 'gray'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    pending: '待执行',
    running: '执行中',
    done: '已完成',
    error: '异常',
    cancelled: '已取消',
  }
  return map[status] || status
}

const formatDuration = (ms: number) => {
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  const m = Math.floor(ms / 60000)
  const s = Math.floor((ms % 60000) / 1000)
  return `${m}m${s}s`
}

const formatTime = (time: string) => {
  if (!time) return '-'
  return time.replace('T', ' ').slice(0, 16)
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.report-list-page {
  padding: 0;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.group-label {
  font-weight: 600;
  font-size: 14px;
}

.status-tag {
  min-width: 60px;
  display: inline-flex;
  justify-content: center;
}

.status-tag :deep(.arco-tag-icon) {
  display: none;
}

.stat-pass { color: #00b42a; font-weight: 600; }
.stat-fail { color: #f53f3f; font-weight: 600; }
.stat-error { color: #ff7d00; font-weight: 600; }
</style>

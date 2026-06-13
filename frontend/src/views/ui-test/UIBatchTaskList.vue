<template>
  <div class="ui-batch-task-list">
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
        <a-button
          v-if="allSelectedKeys.length > 0"
          type="primary"
          status="danger"
          @click="handleBatchDelete"
        >
          <template #icon><icon-delete /></template>
          批量删除 ({{ allSelectedKeys.length }})
        </a-button>
      </a-space>
    </a-card>

    <!-- 任务列表（按日期分组） -->
    <a-card :bordered="false">
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
                <a-checkbox
                  v-if="group.items.length > 0"
                  :model-value="isGroupSelected(group.key)"
                  :indeterminate="isGroupIndeterminate(group.key)"
                  @click.stop
                  @change="(checked: boolean) => toggleGroupSelection(group.key, checked)"
                >
                  全选
                </a-checkbox>
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
              <template #checkbox="{ record }">
                <a-checkbox
                  :model-value="(selectedKeysMap[group.key] || []).includes(record.id)"
                  @change="(checked: boolean) => toggleRowSelection(group.key, record.id, checked)"
                />
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
          </a-collapse-item>
        </a-collapse>
      </a-spin>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Message, Modal } from '@arco-design/web-vue'
import { getUIBatchRuns, deleteUIBatchRun, cancelUIBatchRun } from '@/api/uiBatchRun'
import type { UIBatchRun } from '@/api/uiBatchRun'

const router = useRouter()
const loading = ref(false)
const tableData = ref<UIBatchRun[]>([])

// 按分组存储选中的任务 ID
const selectedKeysMap = reactive<Record<string, number[]>>({})

// 所有选中 ID
const allSelectedKeys = computed(() => {
  const ids: number[] = []
  for (const keys of Object.values(selectedKeysMap)) {
    ids.push(...keys)
  }
  return [...new Set(ids)]
})

// 展开的分组
const activeKeys = ref<string[]>(['today', 'yesterday', 'before_yesterday'])

const searchForm = reactive({
  status: ''
})

const columns = [
  { title: '', slotName: 'checkbox', width: 50 },
  { title: 'ID', dataIndex: 'id', width: 80 },
  { title: '任务名称', dataIndex: 'name', width: 220, ellipsis: true },
  { title: '状态', dataIndex: 'status', slotName: 'status', width: 100 },
  { title: '进度', dataIndex: 'progress', slotName: 'progress', width: 200 },
  { title: '结果', slotName: 'stats', width: 120 },
  { title: '耗时', slotName: 'duration', width: 100 },
  { title: '创建时间', slotName: 'created_at', width: 160 },
  { title: '操作', slotName: 'actions', width: 200, fixed: 'right' as const }
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
  { key: 'older', label: '更早', daysAgo: [8, 999] }
]

const groupedData = computed(() => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  const groups = dateGroups.map(group => ({
    ...group,
    items: [] as UIBatchRun[]
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

  const result = groups.filter(g => g.items.length > 0)

  for (const g of result) {
    if (!(g.key in selectedKeysMap)) {
      selectedKeysMap[g.key] = []
    }
  }

  return result
})

function getProgress(task: UIBatchRun): number {
  if (!task.total_count) return 0
  return (task.pass_count + task.fail_count + task.error_count) / task.total_count
}

function getProgressStatus(task: UIBatchRun): 'danger' | 'warning' | 'success' | 'normal' {
  if (task.status === 'error') return 'danger'
  if (task.status === 'cancelled') return 'warning'
  if (task.status === 'done') {
    return task.fail_count > 0 || task.error_count > 0 ? 'warning' : 'success'
  }
  return 'normal'
}

const isGroupSelected = (groupKey: string) => {
  const group = groupedData.value.find(g => g.key === groupKey)
  if (!group || group.items.length === 0) return false
  const selected = selectedKeysMap[groupKey] || []
  return group.items.every(item => selected.includes(item.id))
}

const isGroupIndeterminate = (groupKey: string) => {
  const group = groupedData.value.find(g => g.key === groupKey)
  if (!group || group.items.length === 0) return false
  const selected = selectedKeysMap[groupKey] || []
  const selectedCount = group.items.filter(item => selected.includes(item.id)).length
  return selectedCount > 0 && selectedCount < group.items.length
}

const toggleRowSelection = (groupKey: string, id: number, checked: boolean) => {
  if (!selectedKeysMap[groupKey]) selectedKeysMap[groupKey] = []
  const arr = selectedKeysMap[groupKey]
  const idx = arr.indexOf(id)
  if (checked && idx === -1) arr.push(id)
  else if (!checked && idx !== -1) arr.splice(idx, 1)
}

const toggleGroupSelection = (groupKey: string, checked: boolean) => {
  const group = groupedData.value.find(g => g.key === groupKey)
  if (!group) return
  selectedKeysMap[groupKey] = checked ? group.items.map(item => item.id) : []
}

const handleBatchDelete = async () => {
  const ids = allSelectedKeys.value
  if (ids.length === 0) return
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除选中的 ${ids.length} 条任务记录吗？`,
    okText: '删除',
    cancelText: '取消',
    okButtonProps: { status: 'danger' },
    onOk: async () => {
      try {
        await Promise.all(ids.map(id => deleteUIBatchRun(id)))
        Message.success(`成功删除 ${ids.length} 条记录`)
        for (const key of Object.keys(selectedKeysMap)) selectedKeysMap[key] = []
        loadData()
      } catch (e: any) {
        Message.error(e?.message || '批量删除失败')
      }
    }
  })
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = { pending: 'gray', running: 'blue', done: 'green', error: 'red', cancelled: 'orange' }
  return colors[status] || 'gray'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = { pending: '待执行', running: '执行中', done: '已完成', error: '异常', cancelled: '已取消' }
  return texts[status] || status
}

const formatDuration = (ms: number) => {
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  const min = Math.floor(ms / 60000)
  const sec = ((ms % 60000) / 1000).toFixed(0)
  return `${min}m ${sec}s`
}

const formatTime = (time: string) => new Date(time).toLocaleString('zh-CN')

const loadData = async () => {
  loading.value = true
  try {
    const res = await getUIBatchRuns({
      page: 1,
      page_size: 100,
      status: searchForm.status || undefined,
    })
    const data = res as any
    tableData.value = data?.items || []
  } catch (e) {
    Message.error('加载任务列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  for (const key of Object.keys(selectedKeysMap)) selectedKeysMap[key] = []
  loadData()
}

const handleReset = () => {
  searchForm.status = ''
  handleSearch()
}

const handleViewDetail = (record: UIBatchRun) => {
  router.push({ name: 'ui-batch-run-detail', params: { runId: record.id } })
}

const handleCancel = async (record: UIBatchRun) => {
  try {
    await cancelUIBatchRun(record.id)
    Message.success('取消请求已提交')
    loadData()
  } catch (e: any) {
    Message.error(e?.message || '取消失败')
  }
}

const handleDelete = async (record: UIBatchRun) => {
  try {
    await deleteUIBatchRun(record.id)
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
.ui-batch-task-list {
  height: 100%;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.group-label {
  font-weight: 600;
  font-size: 14px;
}

.status-tag {
  display: inline-flex !important;
  align-items: center;
  justify-content: center;
}

.status-tag :deep(.arco-tag-icon:empty) {
  display: none;
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

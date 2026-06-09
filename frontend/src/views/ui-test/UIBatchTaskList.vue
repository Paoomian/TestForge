<template>
  <div class="ui-batch-task-list">
    <div class="page-header">
      <h2 class="page-title">UI 执行任务</h2>
      <p class="page-desc">查看 UI 自动化批量执行任务记录</p>
    </div>

    <!-- 状态筛选 -->
    <div class="filter-bar">
      <a-space>
        <a-button
          v-for="item in statusOptions"
          :key="item.value"
          :type="statusFilter === item.value ? 'primary' : 'outline'"
          size="small"
          @click="statusFilter = item.value"
        >
          {{ item.label }}
        </a-button>
      </a-space>
    </div>

    <!-- 任务列表 -->
    <div class="task-list">
      <div
        v-for="task in tasks"
        :key="task.id"
        class="task-card"
        @click="goToDetail(task.id)"
      >
        <div class="task-header">
          <div class="task-name">{{ task.name }}</div>
          <a-tag :color="getStatusColor(task.status)" size="small">
            {{ getStatusLabel(task.status) }}
          </a-tag>
        </div>

        <div class="task-progress">
          <a-progress
            :percent="getProgress(task)"
            :status="getProgressStatus(task)"
            :show-text="false"
            :stroke-width="4"
          />
        </div>

        <div class="task-stats">
          <span class="stat-item">
            <span class="stat-label">通过</span>
            <span class="stat-value stat-pass">{{ task.pass_count }}</span>
          </span>
          <span class="stat-item">
            <span class="stat-label">失败</span>
            <span class="stat-value stat-fail">{{ task.fail_count }}</span>
          </span>
          <span class="stat-item">
            <span class="stat-label">错误</span>
            <span class="stat-value stat-error">{{ task.error_count }}</span>
          </span>
          <span class="stat-item" v-if="task.duration">
            <span class="stat-label">耗时</span>
            <span class="stat-value">{{ formatDuration(task.duration) }}</span>
          </span>
        </div>

        <div class="task-time">
          {{ task.created_at }}
        </div>
      </div>

      <div v-if="tasks.length === 0" class="empty-state">
        <icon-empty />
        <span>暂无执行记录</span>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination-wrapper" v-if="total > 0">
      <a-pagination
        v-model:current="page"
        :page-size="pageSize"
        :total="total"
        show-total
        @change="loadTasks"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { IconEmpty } from '@arco-design/web-vue/es/icon'
import { getUIBatchRuns, type UIBatchRun } from '@/api/uiBatchRun'

const router = useRouter()

// 任务列表
const tasks = ref<UIBatchRun[]>([])
const loading = ref(false)

// 分页
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 筛选
const statusFilter = ref('')
const statusOptions = [
  { label: '全部', value: '' },
  { label: '待执行', value: 'pending' },
  { label: '执行中', value: 'running' },
  { label: '已完成', value: 'done' },
  { label: '异常', value: 'error' },
]

// 加载任务列表
async function loadTasks() {
  loading.value = true
  try {
    const res = await getUIBatchRuns({
      page: page.value,
      page_size: pageSize.value,
      status: statusFilter.value || undefined,
    })
    const data = res as any
    tasks.value = data?.items || []
    total.value = data?.total || 0
  } catch (e) {
    console.error('加载任务列表失败:', e)
  } finally {
    loading.value = false
  }
}

// 跳转详情
function goToDetail(taskId: number) {
  router.push({ name: 'ui-batch-run-detail', params: { runId: taskId } })
}

// 获取进度
function getProgress(task: UIBatchRun): number {
  if (task.total_count === 0) return 0
  const completed = task.pass_count + task.fail_count + task.error_count
  return completed / task.total_count
}

// 获取进度状态
function getProgressStatus(task: UIBatchRun): 'danger' | 'warning' | 'success' | 'normal' {
  if (task.status === 'error') return 'danger'
  if (task.fail_count > 0 || task.error_count > 0) return 'warning'
  if (task.status === 'done') return 'success'
  return 'normal'
}

// 获取状态颜色
function getStatusColor(status: string): string {
  const map: Record<string, string> = {
    pending: 'gray',
    running: 'blue',
    done: 'green',
    error: 'red',
    cancelled: 'orange',
  }
  return map[status] || 'gray'
}

// 获取状态标签
function getStatusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: '待执行',
    running: '执行中',
    done: '已完成',
    error: '异常',
    cancelled: '已取消',
  }
  return map[status] || '未知'
}

// 格式化时长
function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${Math.floor(ms / 60000)}m ${Math.round((ms % 60000) / 1000)}s`
}

// 监听筛选变化
watch(statusFilter, () => {
  page.value = 1
  loadTasks()
})

onMounted(() => {
  loadTasks()
})
</script>

<style scoped>
.ui-batch-task-list {
  width: 100%;
}

.page-header {
  margin-bottom: 20px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-1);
  margin: 0 0 4px 0;
}

.page-desc {
  font-size: 13px;
  color: var(--color-text-3);
  margin: 0;
}

.filter-bar {
  margin-bottom: 16px;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-card {
  background: white;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  padding: 16px 20px;
  cursor: pointer;
  transition: all 0.2s;
}

.task-card:hover {
  border-color: var(--color-primary-light-4);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.task-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.task-name {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-1);
}

.task-progress {
  margin-bottom: 12px;
}

.task-stats {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 8px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.stat-label {
  font-size: 12px;
  color: var(--color-text-3);
}

.stat-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-1);
}

.stat-pass { color: #00b42a; }
.stat-fail { color: #f53f3f; }
.stat-error { color: #ff7d00; }

.task-time {
  font-size: 12px;
  color: var(--color-text-3);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px 0;
  color: var(--color-text-3);
  font-size: 14px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
</style>

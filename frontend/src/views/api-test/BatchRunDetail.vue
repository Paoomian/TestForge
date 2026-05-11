<template>
  <div class="batch-run-detail">
    <!-- 顶部导航 -->
    <div class="detail-header">
      <a-button type="text" @click="goBack">
        <template #icon><icon-left /></template>
        返回任务列表
      </a-button>
      <div class="header-actions">
        <a-button
          v-if="taskInfo?.status === 'running' || taskInfo?.status === 'pending'"
          status="warning"
          @click="handleCancel"
        >
          <template #icon><icon-stop /></template>
          取消任务
        </a-button>
      </div>
    </div>

    <a-spin :loading="pageLoading" style="width: 100%">
      <template v-if="taskInfo">
        <!-- 任务信息卡片 -->
        <a-card :bordered="false" style="margin-bottom: 16px">
          <a-descriptions :column="3">
            <a-descriptions-item label="任务名称">{{ taskInfo.name }}</a-descriptions-item>
            <a-descriptions-item label="状态">
              <a-tag :color="getStatusColor(taskInfo.status)">
                <template #icon>
                  <icon-loading v-if="taskInfo.status === 'running'" spin />
                </template>
                {{ getStatusText(taskInfo.status) }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="执行环境">
              {{ taskInfo.environment_name || (taskInfo.environment_id ? `环境 #${taskInfo.environment_id}` : '未指定') }}
            </a-descriptions-item>
            <a-descriptions-item label="并发数">{{ taskInfo.concurrency === 1 ? '串行' : `${taskInfo.concurrency}并发` }}</a-descriptions-item>
            <a-descriptions-item label="失败策略">
              {{ taskInfo.failure_strategy === 'continue' ? '继续执行' : '遇错停止' }}
            </a-descriptions-item>
            <a-descriptions-item v-if="taskInfo.duration" label="耗时">
              {{ formatDuration(taskInfo.duration) }}
            </a-descriptions-item>
          </a-descriptions>
        </a-card>

        <!-- 进度卡片（执行中显示） -->
        <a-card v-if="['pending', 'running'].includes(taskInfo.status)" :bordered="false" style="margin-bottom: 16px">
          <BatchRunProgress
            :total="taskInfo.total_count"
            :pass-count="taskInfo.pass_count"
            :fail-count="taskInfo.fail_count"
            :error-count="taskInfo.error_count"
            :status="taskInfo.status"
          />
        </a-card>

        <!-- 测试报告（完成后显示） -->
        <a-card
          v-else
          :bordered="false"
          title="测试报告"
          style="margin-bottom: 16px"
        >
          <TestReportPanel
            :run-id="Number(taskId)"
            :status="taskInfo.status"
            @view-detail="handleViewDetail"
          />
        </a-card>

        <!-- 用例执行列表 -->
        <a-card :bordered="false" title="用例执行列表">
          <a-table
            :columns="detailColumns"
            :data="taskInfo.details"
            :pagination="false"
            :loading="tableLoading"
          >
            <template #status="{ record }">
              <a-tag :color="getDetailStatusColor(record.status)" size="small">
                {{ getDetailStatusText(record.status) }}
              </a-tag>
            </template>

            <template #api_duration_ms="{ record }">
              <span v-if="record.api_duration_ms" class="api-time">{{ record.api_duration_ms }}ms</span>
              <span v-else>-</span>
            </template>

            <template #duration_ms="{ record }">
              {{ record.duration_ms ? `${record.duration_ms}ms` : '-' }}
            </template>

            <template #actions="{ record }">
              <a-button
                v-if="record.status !== 'pending' && record.status !== 'running'"
                type="text"
                size="small"
                @click="viewCaseDetail(record)"
              >
                详情
              </a-button>
            </template>
          </a-table>
        </a-card>
      </template>
    </a-spin>

    <!-- 用例详情抽屉 -->
    <CaseResultDetail
      v-model:visible="detailDrawerVisible"
      :run-id="Number(taskId)"
      :detail-id="selectedDetailId"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { getBatchRun, cancelBatchRun } from '@/api/batchRun'
import type { BatchRunInfo, CaseDetailSummary } from '@/api/batchRun'
import BatchRunProgress from './components/BatchRunProgress.vue'
import CaseResultDetail from './components/CaseResultDetail.vue'
import TestReportPanel from './components/TestReportPanel.vue'

const route = useRoute()
const router = useRouter()
const taskId = route.params.taskId as string

const pageLoading = ref(false)
const tableLoading = ref(false)
const taskInfo = ref<BatchRunInfo | null>(null)
const pollTimer = ref<number | null>(null)

// 用例详情抽屉
const detailDrawerVisible = ref(false)
const selectedDetailId = ref(0)

const detailColumns = [
  { title: '序号', dataIndex: 'execution_order', width: 80 },
  { title: '用例编号', dataIndex: 'case_number', width: 150, ellipsis: true },
  { title: '用例名称', dataIndex: 'case_name', width: 200, ellipsis: true },
  { title: '状态', dataIndex: 'status', slotName: 'status', width: 100 },
  { title: '状态码', dataIndex: 'status_code', width: 80 },
  { title: '接口耗时', dataIndex: 'api_duration_ms', slotName: 'api_duration_ms', width: 100 },
  { title: '总耗时', dataIndex: 'duration_ms', slotName: 'duration_ms', width: 100 },
  { title: '错误信息', dataIndex: 'error_message', width: 200, ellipsis: true },
  { title: '操作', slotName: 'actions', width: 100, fixed: 'right' as const }
]

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    pending: 'gray', running: 'blue', done: 'green', error: 'red', cancelled: 'orange'
  }
  return colors[status] || 'gray'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: '待执行', running: '执行中', done: '已完成', error: '异常', cancelled: '已取消'
  }
  return texts[status] || status
}

const getDetailStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    pending: 'gray', running: 'blue', pass: 'green', fail: 'red', error: 'orange', skipped: 'gray'
  }
  return colors[status] || 'gray'
}

const getDetailStatusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: '待执行', running: '执行中', pass: '通过', fail: '失败', error: '错误', skipped: '已跳过'
  }
  return texts[status] || status
}

const formatDuration = (ms: number) => {
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  const min = Math.floor(ms / 60000)
  const sec = ((ms % 60000) / 1000).toFixed(0)
  return `${min}m ${sec}s`
}

const goBack = () => {
  router.push({ name: 'api-batch-tasks' })
}

const loadTaskInfo = async () => {
  pageLoading.value = true
  try {
    taskInfo.value = await getBatchRun(Number(taskId))
  } catch (e) {
    Message.error('加载任务信息失败')
  } finally {
    pageLoading.value = false
  }
}

const handleCancel = async () => {
  try {
    await cancelBatchRun(Number(taskId))
    Message.success('取消请求已提交')
    loadTaskInfo()
  } catch (e: any) {
    Message.error(e?.message || '取消失败')
  }
}

const viewCaseDetail = (record: CaseDetailSummary) => {
  selectedDetailId.value = record.id
  detailDrawerVisible.value = true
}

const handleViewDetail = (detailId: number) => {
  selectedDetailId.value = detailId
  detailDrawerVisible.value = true
}

// 启动轮询
const startPolling = () => {
  stopPolling()
  pollTimer.value = window.setInterval(async () => {
    await loadTaskInfo()
    // 如果任务已完成，停止轮询
    if (taskInfo.value?.status && !['pending', 'running'].includes(taskInfo.value.status)) {
      stopPolling()
    }
  }, 1500) // 每1.5秒轮询一次
}

const stopPolling = () => {
  if (pollTimer.value) {
    clearInterval(pollTimer.value)
    pollTimer.value = null
  }
}

onMounted(async () => {
  await loadTaskInfo()

  // 如果任务正在运行或待执行，启动轮询
  if (taskInfo.value?.status === 'running' || taskInfo.value?.status === 'pending') {
    startPolling()
  }
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.batch-run-detail {
  padding: 0;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: white;
  border-radius: var(--radius-medium);
  border: 1px solid var(--color-border-2);
}

.header-actions {
  display: flex;
  gap: 8px;
}

.api-time {
  font-weight: 600;
  color: #165dff;
}
</style>

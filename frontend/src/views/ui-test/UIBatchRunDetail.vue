<template>
  <div class="ui-batch-detail">
    <!-- 顶部工具栏 -->
    <div class="detail-toolbar">
      <div class="toolbar-left">
        <a-button @click="goBack">
          <template #icon><icon-left /></template>
          返回
        </a-button>
        <span class="task-name">{{ taskInfo?.name || '加载中...' }}</span>
        <a-tag :color="statusColor" size="large">{{ statusLabel }}</a-tag>
      </div>
      <div class="toolbar-right">
        <a-button
          v-if="isRunning"
          status="danger"
          @click="handleCancel"
        >
          <template #icon><icon-record-stop /></template>
          取消执行
        </a-button>
      </div>
    </div>

    <!-- 进度区域 -->
    <div class="progress-section" v-if="taskInfo">
      <div class="progress-stats">
        <div class="stat-item">
          <span class="stat-label">总用例</span>
          <span class="stat-value">{{ taskInfo.total_count }}</span>
        </div>
        <div class="stat-item stat-pass">
          <span class="stat-label">通过</span>
          <span class="stat-value">{{ taskInfo.pass_count }}</span>
        </div>
        <div class="stat-item stat-fail">
          <span class="stat-label">失败</span>
          <span class="stat-value">{{ taskInfo.fail_count }}</span>
        </div>
        <div class="stat-item stat-error">
          <span class="stat-label">错误</span>
          <span class="stat-value">{{ taskInfo.error_count }}</span>
        </div>
      </div>
      <a-progress
        :percent="progress"
        :status="progressStatus"
        :show-text="false"
        :stroke-width="8"
      />
    </div>

    <!-- 主内容区 -->
    <div class="detail-content">
      <!-- 左侧：用例列表 -->
      <div class="case-list-panel">
        <div class="panel-header">
          <span class="panel-title">用例执行列表</span>
        </div>
        <div class="case-list">
          <div
            v-for="detail in (taskInfo as any)?.details"
            :key="detail.id"
            class="case-item"
            :class="{ active: selectedDetailId === detail.id }"
            @click="selectDetail(detail)"
          >
            <div class="case-status">
              <icon-check-circle v-if="detail.status === 'pass'" style="color: #00b42a;" />
              <icon-close-circle v-else-if="detail.status === 'fail' || detail.status === 'error'" style="color: #f53f3f;" />
              <icon-loading v-else-if="detail.status === 'running'" style="color: #165DFF;" />
              <icon-clock-circle v-else style="color: #c9cdd4;" />
            </div>
            <div class="case-info">
              <div class="case-name">{{ detail.case_name }}</div>
              <div class="case-meta">
                <span v-if="detail.duration_ms">{{ detail.duration_ms }}ms</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：详情/截图 -->
      <div class="detail-panel">
        <template v-if="selectedDetail">
          <div class="detail-header">
            <span class="detail-title">{{ selectedDetail.case_name }}</span>
            <a-tag :color="getDetailStatusColor(selectedDetail.status)" size="small">
              {{ getDetailStatusLabel(selectedDetail.status) }}
            </a-tag>
          </div>

          <!-- 步骤列表 -->
          <div class="steps-list" v-if="selectedDetail.steps?.length">
            <div
              v-for="step in selectedDetail.steps"
              :key="step.step_order"
              class="step-item"
              :class="`step-${step.status}`"
            >
              <div class="step-header">
                <span class="step-order">{{ step.step_order }}</span>
                <span class="step-action">{{ getActionLabel(step.action) }}</span>
                <span class="step-duration">{{ step.duration_ms }}ms</span>
              </div>
              <div v-if="step.message" class="step-message" :class="{ error: step.status === 'fail' }">
                {{ step.message }}
              </div>
              <div v-if="step.screenshot" class="step-screenshot">
                <img :src="`data:image/jpeg;base64,${step.screenshot}`" alt="截图" />
              </div>
            </div>
          </div>

          <!-- 错误信息 -->
          <div v-if="selectedDetail.error_message" class="error-message">
            <icon-exclamation-circle />
            <span>{{ selectedDetail.error_message }}</span>
          </div>
        </template>

        <div v-else class="empty-detail">
          <icon-info-circle />
          <span>点击左侧用例查看详情</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import {
  IconLeft,
  IconCheckCircle,
  IconCloseCircle,
  IconLoading,
  IconClockCircle,
  IconRecordStop,
  IconInfoCircle,
  IconExclamationCircle,
} from '@arco-design/web-vue/es/icon'
import { getUIBatchRun, getUIBatchRunDetail, cancelUIBatchRun } from '@/api/uiBatchRun'
import type { UIBatchRun, UIBatchRunDetail } from '@/api/uiBatchRun'

const route = useRoute()
const router = useRouter()

const runId = computed(() => Number(route.params.runId))

// 任务信息
const taskInfo = ref<UIBatchRun | null>(null)

// 选中的详情
const selectedDetailId = ref<number | null>(null)
const selectedDetail = ref<UIBatchRunDetail | null>(null)

// 加载详情
async function loadDetail(detailId: number) {
  try {
    const res = await getUIBatchRunDetail(runId.value, detailId)
    const detail = res as unknown as UIBatchRunDetail
    // 从 script_output 中提取 steps
    if (detail.script_output?.steps) {
      detail.steps = detail.script_output.steps
    }
    selectedDetail.value = detail
  } catch (e) {
    console.error('加载详情失败:', e)
  }
}

// 状态相关
const isRunning = computed(() => {
  return taskInfo.value?.status === 'pending' || taskInfo.value?.status === 'running'
})

const statusColor = computed(() => {
  const map: Record<string, string> = {
    pending: 'gray',
    running: 'blue',
    done: 'green',
    error: 'red',
    cancelled: 'orange',
  }
  return map[taskInfo.value?.status || ''] || 'gray'
})

const statusLabel = computed(() => {
  const map: Record<string, string> = {
    pending: '待执行',
    running: '执行中',
    done: '已完成',
    error: '执行失败',
    cancelled: '已取消',
  }
  return map[taskInfo.value?.status || ''] || '未知'
})

// 进度
const progress = computed(() => {
  if (!taskInfo.value || taskInfo.value.total_count === 0) return 0
  const completed = taskInfo.value.pass_count + taskInfo.value.fail_count + taskInfo.value.error_count
  return completed / taskInfo.value.total_count
})

const progressStatus = computed(() => {
  if (taskInfo.value?.status === 'error') return 'danger'
  if (taskInfo.value?.fail_count || taskInfo.value?.error_count) return 'warning'
  return 'success'
})

// 轮询
let pollTimer: number | null = null

async function loadTaskInfo() {
  try {
    const res = await getUIBatchRun(runId.value)
    taskInfo.value = res as unknown as UIBatchRun
    // 自动选中第一个并加载详情
    if (!selectedDetailId.value && taskInfo.value?.details?.length) {
      const firstDetail = taskInfo.value.details[0]
      selectedDetailId.value = firstDetail.id
      await loadDetail(firstDetail.id)
    }
    // 同步更新选中用例的状态（从列表中获取最新状态）
    if (selectedDetailId.value && taskInfo.value?.details) {
      const updated = taskInfo.value.details.find((d: UIBatchRunDetail) => d.id === selectedDetailId.value)
      if (updated && selectedDetail.value) {
        selectedDetail.value.status = updated.status
        selectedDetail.value.duration_ms = updated.duration_ms
      }
    }
  } catch (e) {
    console.error('加载任务信息失败:', e)
  }
}

function startPolling() {
  pollTimer = window.setInterval(async () => {
    await loadTaskInfo()
    // 刷新当前选中的用例详情
    if (selectedDetailId.value) {
      await loadDetail(selectedDetailId.value)
    }
    if (!isRunning.value && pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }, 1500)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

// 选择详情
async function selectDetail(detail: UIBatchRunDetail) {
  selectedDetailId.value = detail.id
  await loadDetail(detail.id)
}

// 返回
function goBack() {
  router.push({ name: 'ui-batch-tasks' })
}

// 取消
async function handleCancel() {
  try {
    await cancelUIBatchRun(runId.value) as any
    Message.success('已发送取消指令')
    await loadTaskInfo()
  } catch (e: any) {
    Message.error(e?.detail || '取消失败')
  }
}

// 获取操作标签
function getActionLabel(action: string): string {
  const map: Record<string, string> = {
    navigate: '导航',
    click: '点击',
    type: '输入',
    press: '按键',
    wait: '等待',
    assert: '断言',
    new_page: '新窗口',
    go_back: '返回',
  }
  return map[action] || action
}

// 详情状态颜色
function getDetailStatusColor(status: string): string {
  const map: Record<string, string> = {
    pass: 'green',
    fail: 'red',
    error: 'orange',
    running: 'blue',
    pending: 'gray',
    skipped: 'gray',
  }
  return map[status] || 'gray'
}

// 详情状态标签
function getDetailStatusLabel(status: string): string {
  const map: Record<string, string> = {
    pass: '通过',
    fail: '失败',
    error: '错误',
    running: '执行中',
    pending: '待执行',
    skipped: '已跳过',
  }
  return map[status] || status
}

onMounted(async () => {
  await loadTaskInfo()
  if (isRunning.value) {
    startPolling()
  }
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.ui-batch-detail {
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--header-height));
  background: #f7f8fa;
  margin: calc(-1 * var(--content-padding));
  padding: var(--content-padding);
  gap: 16px;
}

/* 工具栏 */
.detail-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e6eb;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.task-name {
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
}

/* 进度区域 */
.progress-section {
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e6eb;
  padding: 16px 20px;
}

.progress-stats {
  display: flex;
  gap: 32px;
  margin-bottom: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: #86909c;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #1d2129;
}

.stat-pass .stat-value { color: #00b42a; }
.stat-fail .stat-value { color: #f53f3f; }
.stat-error .stat-value { color: #ff7d00; }

/* 主内容区 */
.detail-content {
  flex: 1;
  display: flex;
  gap: 16px;
  min-height: 0;
}

/* 左侧用例列表 */
.case-list-panel {
  width: 300px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e6eb;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  padding: 12px 16px;
  border-bottom: 1px solid #e5e6eb;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
}

.case-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.case-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.case-item:hover {
  background: #f2f3f5;
}

.case-item.active {
  background: #e8f3ff;
  border: 1px solid #165DFF;
}

.case-status {
  font-size: 16px;
  flex-shrink: 0;
}

.case-info {
  flex: 1;
  min-width: 0;
}

.case-name {
  font-size: 13px;
  font-weight: 500;
  color: #1d2129;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.case-meta {
  font-size: 11px;
  color: #86909c;
  margin-top: 2px;
}

/* 右侧详情面板 */
.detail-panel {
  flex: 1;
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e6eb;
  padding: 20px;
  overflow-y: auto;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.detail-title {
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
}

/* 步骤列表 */
.steps-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.step-item {
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid #e5e6eb;
}

.step-pass {
  border-left: 4px solid #00b42a;
}

.step-fail,
.step-error {
  border-left: 4px solid #f53f3f;
}

.step-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.step-order {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f2f3f5;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 600;
  color: #4e5969;
}

.step-action {
  font-size: 13px;
  font-weight: 500;
  color: #1d2129;
}

.step-duration {
  margin-left: auto;
  font-size: 12px;
  color: #86909c;
}

.step-message {
  margin-top: 8px;
  font-size: 13px;
  color: #4e5969;
}

.step-message.error {
  color: #f53f3f;
}

.step-screenshot {
  margin-top: 12px;
}

.step-screenshot img {
  max-width: 100%;
  border-radius: 6px;
  border: 1px solid #e5e6eb;
}

/* 错误信息 */
.error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #fff2f0;
  border-radius: 8px;
  color: #f53f3f;
  font-size: 13px;
  margin-top: 16px;
}

/* 空状态 */
.empty-detail {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 12px;
  color: #c9cdd4;
  font-size: 14px;
}
</style>

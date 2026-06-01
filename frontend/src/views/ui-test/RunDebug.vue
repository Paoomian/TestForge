<template>
  <div class="run-debug-page">
    <!-- 顶部工具栏 -->
    <div class="debug-toolbar">
      <div class="toolbar-left">
        <a-button @click="goBack">
          <template #icon><icon-left /></template>
          返回
        </a-button>
        <span class="case-name">{{ caseName }}</span>
      </div>
      <div class="toolbar-center">
        <a-tag :color="statusColor" size="large">
          {{ statusLabel }}
        </a-tag>
        <span class="step-progress" v-if="totalSteps > 0">
          {{ currentStep }} / {{ totalSteps }}
        </span>
      </div>
      <div class="toolbar-right">
        <a-button
          v-if="isRunning"
          status="danger"
          @click="handleStop"
        >
          <template #icon><icon-close /></template>
          停止
        </a-button>
        <a-button
          v-if="!isRunning && !isCompleted"
          type="primary"
          @click="handleStart"
        >
          <template #icon><icon-play-arrow /></template>
          开始执行
        </a-button>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="debug-content">
      <!-- 左侧：浏览器画面 -->
      <div class="content-left">
        <div class="browser-view">
          <canvas ref="canvasRef" class="preview-canvas" />
          <div v-if="!currentScreenshot" class="empty-state">
            <icon-play-arrow style="font-size: 48px; color: #c9cdd4;" />
            <span>点击"开始执行"查看实时画面</span>
          </div>
        </div>
      </div>

      <!-- 右侧：步骤列表 -->
      <div class="content-right">
        <div class="steps-panel">
          <div class="panel-header">
            <span>执行步骤</span>
            <a-tag v-if="isCompleted" :color="allPassed ? 'green' : 'red'" size="small">
              {{ allPassed ? '全部通过' : '有失败' }}
            </a-tag>
          </div>
          <div class="steps-list">
            <div
              v-for="(result, index) in stepResults"
              :key="index"
              class="step-item"
              :class="{
                'step-current': currentStep === index + 1 && isRunning,
                'step-success': result.success,
                'step-failed': !result.success && isStepDone(index),
                'step-pending': !isStepDone(index)
              }"
            >
              <div class="step-index">
                <span v-if="isStepDone(index)">
                  <icon-check-circle v-if="result.success" style="color: #00b42a;" />
                  <icon-close-circle v-else style="color: #f53f3f;" />
                </span>
                <span v-else>{{ index + 1 }}</span>
              </div>
              <div class="step-info">
                <div class="step-action">{{ getActionLabel(steps[index]?.action) }}</div>
                <div class="step-desc">{{ getStepDesc(steps[index]) }}</div>
                <div v-if="isStepDone(index) && result.message" class="step-message" :class="{ 'message-error': !result.success }">
                  {{ result.message }}
                </div>
              </div>
              <div class="step-duration" v-if="isStepDone(index)">
                {{ result.duration }}ms
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import {
  IconLeft,
  IconPlayArrow,
  IconClose,
  IconCheckCircle,
  IconCloseCircle,
} from '@arco-design/web-vue/es/icon'
import { getUICase, type UICase, type UIStep } from '@/api/uiCase'

const route = useRoute()
const router = useRouter()

// ========== 状态 ==========

const caseId = computed(() => Number(route.params.caseId))
const caseName = ref('')
const steps = ref<UIStep[]>([])
const base_url = ref('')

const ws = ref<WebSocket | null>(null)
const canvasRef = ref<HTMLCanvasElement>()
const currentScreenshot = ref('')

const execStatus = ref('idle') // idle / running / completed
const currentStep = ref(0)
const totalSteps = ref(0)
const stepResults = ref<Array<{ success: boolean; message: string; duration: number }>>([])

// ========== 计算属性 ==========

const isRunning = computed(() => execStatus.value === 'running')
const isCompleted = computed(() => execStatus.value === 'completed')

const statusColor = computed(() => {
  const map: Record<string, string> = {
    idle: 'gray',
    running: 'blue',
    completed: 'green',
    failed: 'red',
  }
  return map[execStatus.value] || 'gray'
})

const statusLabel = computed(() => {
  const map: Record<string, string> = {
    idle: '未执行',
    running: '执行中...',
    completed: '执行完成',
    failed: '执行失败',
  }
  return map[execStatus.value] || '未知'
})

const allPassed = computed(() => {
  return stepResults.value.length > 0 && stepResults.value.every(r => r.success)
})

// ========== 方法 ==========

function isStepDone(index: number): boolean {
  return index < stepResults.value.length
}

function getActionLabel(action?: string): string {
  const map: Record<string, string> = {
    navigate: '导航',
    click: '点击',
    dblclick: '双击',
    type: '输入',
    press: '按键',
    select: '选择',
    check: '勾选',
    uncheck: '取消勾选',
    hover: '悬停',
    scroll: '滚动',
    wait: '等待',
    assert: '断言',
    drag: '拖拽',
    new_page: '新窗口',
    go_back: '返回',
  }
  return map[action || ''] || action || ''
}

function getStepDesc(step?: UIStep): string {
  if (!step) return ''
  if (step.action === 'navigate') return step.url || ''
  if (step.action === 'new_page') return step.url || '新窗口'
  if (step.action === 'go_back') return step.url || '返回上一页'
  if (step.action === 'type') {
    return `${step.target?.text || step.target?.selector || ''} → "${step.value}"`
  }
  if (step.action === 'press') return step.key || ''
  if (step.action === 'assert') {
    const assertType = (step as Record<string, unknown>).type as string
    const expected = (step as Record<string, unknown>).expected as string
    return expected || assertType || ''
  }
  if (step.target) {
    return step.target.text || step.target.selector || ''
  }
  return ''
}

function updateScreenshot(base64Data: string) {
  currentScreenshot.value = base64Data
  const canvas = canvasRef.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const img = new Image()
  img.onload = () => {
    // 调整 canvas 大小
    const container = canvas.parentElement
    if (container) {
      const ratio = Math.min(
        container.clientWidth / img.width,
        container.clientHeight / img.height
      )
      canvas.width = img.width * ratio
      canvas.height = img.height * ratio
    }
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
  }
  img.src = `data:image/jpeg;base64,${base64Data}`
}

async function loadCase() {
  try {
    const caseData = await getUICase(caseId.value)
    caseName.value = caseData.name
    steps.value = caseData.steps || []
    base_url.value = caseData.base_url || ''
    totalSteps.value = steps.value.length

    // 初始化步骤结果
    stepResults.value = steps.value.map(() => ({
      success: false,
      message: '',
      duration: 0,
    }))
  } catch (err) {
    Message.error('加载用例失败')
    router.back()
  }
}

function handleStart() {
  execStatus.value = 'running'
  currentStep.value = 0
  stepResults.value = steps.value.map(() => ({
    success: false,
    message: '',
    duration: 0,
  }))

  // 建立 WebSocket 连接
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/ws/ui-run/${caseId.value}`
  ws.value = new WebSocket(wsUrl)

  ws.value.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      handleWsMessage(data)
    } catch (e) {
      console.error('解析消息失败:', e)
    }
  }

  ws.value.onclose = () => {
    if (execStatus.value === 'running') {
      execStatus.value = 'idle'
    }
  }

  ws.value.onerror = () => {
    Message.error('WebSocket 连接失败')
    execStatus.value = 'idle'
  }
}

function handleStop() {
  if (ws.value && ws.value.readyState === WebSocket.OPEN) {
    ws.value.send(JSON.stringify({
      type: 'command',
      action: 'stop',
    }))
  }
}

function handleWsMessage(data: Record<string, unknown>) {
  switch (data.type) {
    case 'screenshot':
      updateScreenshot(data.data as string)
      break

    case 'progress':
      handleProgress(data)
      break

    case 'completed':
      execStatus.value = (data.status as string) === 'completed' ? 'completed' : 'failed'
      if (ws.value) {
        ws.value.close()
      }
      Message.success('执行完成')
      break

    case 'error':
      Message.error(data.message as string)
      execStatus.value = 'failed'
      break

    case 'ping':
      break
  }
}

function handleProgress(data: Record<string, unknown>) {
  const progressType = data.type as string
  const current = data.current as number
  const total = data.total as number

  currentStep.value = current
  totalSteps.value = total

  if (progressType === 'step_end') {
    const result = data.result as Record<string, unknown>
    const index = current - 1
    if (index >= 0 && index < stepResults.value.length) {
      stepResults.value[index] = {
        success: result.success as boolean,
        message: result.message as string,
        duration: result.duration as number,
      }
    }
  }
}

function goBack() {
  if (isRunning.value) {
    handleStop()
  }
  router.push('/ui-cases')
}

// ========== 生命周期 ==========

onMounted(() => {
  loadCase()
})

onUnmounted(() => {
  if (ws.value) {
    ws.value.close()
  }
})
</script>

<style scoped>
.run-debug-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
  background: #f7f8fa;
}

.debug-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: #fff;
  border-bottom: 1px solid #e5e6eb;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.case-name {
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
}

.toolbar-center {
  display: flex;
  align-items: center;
  gap: 12px;
}

.step-progress {
  font-size: 14px;
  color: #86909c;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.debug-content {
  flex: 1;
  display: flex;
  gap: 12px;
  padding: 12px;
  overflow: hidden;
}

.content-left {
  flex: 1;
  min-width: 0;
}

.browser-view {
  height: 100%;
  background: #1a1a2e;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-canvas {
  max-width: 100%;
  max-height: 100%;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #86909c;
}

.content-right {
  width: 360px;
  flex-shrink: 0;
}

.steps-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e5e6eb;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #e5e6eb;
  font-weight: 600;
}

.steps-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.step-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 6px;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.step-item:hover {
  background: #f2f3f5;
}

.step-item.step-current {
  background: #e8f3ff;
  border-color: #165DFF;
}

.step-item.step-success {
  background: #e8ffea;
}

.step-item.step-failed {
  background: #ffe8e8;
}

.step-item.step-pending {
  opacity: 0.6;
}

.step-index {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 500;
  color: #4e5969;
}

.step-info {
  flex: 1;
  min-width: 0;
}

.step-action {
  font-size: 13px;
  font-weight: 500;
  color: #1d2129;
}

.step-desc {
  font-size: 12px;
  color: #86909c;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.step-message {
  font-size: 12px;
  color: #4e5969;
  margin-top: 4px;
}

.step-message.message-error {
  color: #f53f3f;
}

.step-duration {
  font-size: 12px;
  color: #86909c;
  flex-shrink: 0;
}
</style>

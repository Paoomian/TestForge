<template>
  <div class="ui-record-page">
    <!-- 顶部工具栏 -->
    <div class="record-toolbar">
      <div class="toolbar-left">
        <div class="url-input-group">
          <a-select
            v-model="selectedProjectId"
            :style="{ width: '140px' }"
            placeholder="选择项目"
            allow-search
            :disabled="isRecording"
            @change="handleProjectChange"
          >
            <a-option
              v-for="p in projects"
              :key="p.id"
              :value="p.id"
              :label="p.name"
            />
          </a-select>
          <a-select
            v-model="selectedEnvironmentId"
            :style="{ width: '140px' }"
            placeholder="选择环境"
            allow-clear
            :disabled="isRecording"
            @change="handleEnvironmentChange"
          >
            <a-option
              v-for="env in environments"
              :key="env.id"
              :value="env.id"
              :label="env.name"
            />
          </a-select>
          <a-input
            v-model="targetUrl"
            placeholder="输入要录制的网页 URL，如 https://example.com"
            :disabled="isRecording"
            class="url-input"
            @press-enter="handleStartRecording"
          >
            <template #prefix><icon-link /></template>
          </a-input>
          <a-button
            v-if="!isRecording && !isPaused"
            type="primary"
            :disabled="!targetUrl"
            @click="handleStartRecording"
          >
            <template #icon><icon-video-camera /></template>
            开始录制
          </a-button>
          <a-button
            v-if="isRecording && !isPaused"
            status="warning"
            @click="handlePauseRecording"
          >
            <template #icon><icon-pause /></template>
            暂停
          </a-button>
          <a-button
            v-if="isPaused"
            type="primary"
            @click="handleResumeRecording"
          >
            <template #icon><icon-play-arrow /></template>
            继续
          </a-button>
          <a-button
            v-if="isRecording || isPaused"
            status="danger"
            @click="handleStopRecording"
          >
            <template #icon><icon-record-stop /></template>
            停止录制
          </a-button>
        </div>
      </div>

      <div class="toolbar-right">
        <a-tag :color="statusColor" size="small">
          {{ statusLabel }}
        </a-tag>
        <a-button
          v-if="isRecording"
          @click="assertModalVisible = true"
        >
          <template #icon><icon-check-circle /></template>
          添加断言
        </a-button>
        <a-button
          v-if="isRecording && hasPageHistory"
          @click="handleGoBack"
        >
          <template #icon><icon-left /></template>
          返回上一页
        </a-button>
        <template v-if="steps.length > 0 && !isRecording">
          <a-button
            status="danger"
            @click="handleDiscardRecording"
          >
            <template #icon><icon-delete /></template>
            放弃录制
          </a-button>
          <a-button
            type="primary"
            @click="handleSaveCase"
          >
            <template #icon><icon-save /></template>
            保存用例
          </a-button>
        </template>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="record-content">
      <!-- 左侧：浏览器预览 / 步骤预览 -->
      <div class="content-left">
        <!-- 浏览器预览模式 -->
        <BrowserPreview
          v-if="rightActiveTab !== 'preview'"
          :ws="ws"
          :is-recording="isRecording"
          :is-select-mode="isSelectMode"
          :has-modal="assertModalVisible || saveModalVisible || inputModalVisible"
          :loading="browserLoading"
          :viewport-width="1280"
          :viewport-height="720"
          @step-recorded="handleStepRecorded"
          @step-updated="handleStepUpdated"
          @status-changed="handleStatusChanged"
          @element-selected="handleElementSelected"
          @input-target="handleInputTarget"
        />

        <!-- 步骤预览模式（实时执行） -->
        <div v-else class="preview-mode">
          <div class="preview-container">
            <!-- 预览截图 -->
            <div class="preview-screenshot">
              <canvas ref="previewCanvasRef" class="preview-canvas" />
              <div v-if="!previewStarted" class="preview-placeholder">
                <icon-play-arrow :style="{ fontSize: '64px', color: 'var(--color-text-4)' }" />
                <p>点击"开始预览"实时执行用例</p>
              </div>
            </div>

            <!-- 步骤信息和控制栏 -->
            <div class="preview-bottom">
              <div class="preview-info">
                <div class="preview-step-action" v-if="previewCurrentStep">
                  {{ getActionLabel(previewCurrentStep.action) }}
                </div>
                <div class="preview-step-desc" v-if="previewCurrentStep">
                  {{ getStepDesc(previewCurrentStep) }}
                </div>
                <div v-else class="preview-step-hint">
                  实时执行录制的用例，观察执行效果
                </div>
              </div>

              <!-- 控制栏 -->
              <div class="preview-controls">
                <a-button-group>
                  <a-button
                    v-if="!previewRunning"
                    type="primary"
                    @click="startPreview()"
                    :disabled="steps.length === 0"
                  >
                    <template #icon><icon-play-arrow /></template>
                    {{ previewCompleted ? '重新预览' : '开始预览' }}
                  </a-button>
                  <a-button
                    v-else
                    status="danger"
                    @click="stopPreview"
                  >
                    <template #icon><icon-record-stop /></template>
                    停止
                  </a-button>
                </a-button-group>

                <!-- 进度 -->
                <div class="preview-progress" v-if="previewTotalSteps > 0">
                  {{ previewCurrentStepIndex }} / {{ previewTotalSteps }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：步骤列表 + 详情 -->
      <div class="content-right">
        <a-tabs v-model:active-key="rightActiveTab" class="right-tabs">
          <a-tab-pane key="steps" title="录制步骤">
            <div class="tab-pane-content">
              <StepList
                :steps="steps"
                :selected-index="selectedStepIndex"
                @select-step="handleSelectStep"
                @delete-step="handleDeleteStep"
                @clear-all="handleClearSteps"
                @reorder="handleReorderSteps"
                @insert-step="handleInsertStep"
              />
            </div>
          </a-tab-pane>
          <a-tab-pane key="detail" title="步骤详情">
            <div class="tab-pane-content">
              <StepDetail
                :step="selectedStep"
                @update-step="handleUpdateStep"
              />
            </div>
          </a-tab-pane>
          <a-tab-pane key="preview" title="步骤预览" :disabled="steps.length === 0">
            <div class="tab-pane-content">
              <StepList
                :steps="steps"
                :selected-index="previewCurrentStepIndex > 0 ? previewCurrentStepIndex - 1 : -1"
                :step-results="previewStepResults"
                :current-step-index="previewCurrentStepIndex"
                :readonly="true"
                @select-step="handlePreviewStepSelect"
              />
            </div>
          </a-tab-pane>
        </a-tabs>
      </div>
    </div>

    <!-- 断言弹窗 -->
    <AssertModal
      v-model:visible="assertModalVisible"
      :selected-element="selectedElement"
      @start-select="handleStartSelect"
      @reselect="handleStartSelect"
      @confirm="handleAddAssert"
      @update:visible="handleAssertModalVisibleChange"
    />

    <!-- 保存用例弹窗 -->
    <a-modal
      v-model:visible="saveModalVisible"
      title="保存录制用例"
      @ok="handleConfirmSave"
      @cancel="saveModalVisible = false"
    >
      <a-form :model="saveForm" layout="vertical">
        <a-form-item label="用例名称" required>
          <a-input v-model="saveForm.name" placeholder="请输入用例名称" />
        </a-form-item>
        <a-form-item label="所属项目" required>
          <a-select
            v-model="saveForm.projectId"
            :loading="projectsLoading"
            placeholder="请选择项目"
            allow-search
          >
            <a-option
              v-for="p in projects"
              :key="p.id"
              :value="p.id"
              :label="p.name"
            />
          </a-select>
        </a-form-item>
        <a-form-item label="用例描述">
          <a-textarea v-model="saveForm.description" placeholder="可选描述" :max-length="500" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 输入弹窗 -->
    <InputModal
      v-model:visible="inputModalVisible"
      :target="inputTarget"
      @confirm="handleInputConfirm"
      @update:visible="handleInputModalVisibleChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import {
  IconLink,
  IconVideoCamera,
  IconRecordStop,
  IconSave,
  IconLeft,
  IconCheckCircle,
  IconPause,
  IconPlayArrow,
  IconDelete,
} from '@arco-design/web-vue/es/icon'
import BrowserPreview from './components/BrowserPreview.vue'
import StepList from './components/StepList.vue'
import StepDetail from './components/StepDetail.vue'
import AssertModal from './components/AssertModal.vue'
import InputModal from './components/InputModal.vue'
import {
  startRecording,
  stopRecording,
  createRecordingWebSocket,
  type UIStep,
} from '@/api/uiCase'
import { getProjects } from '@/api/project'
import { getEnvironments, type Environment } from '@/api/environment'

// ========== 状态 ==========

const targetUrl = ref('')
const sessionId = ref('')
const ws = ref<WebSocket | null>(null)
const recordingStatus = ref('idle') // idle / connecting / recording / paused / stopped
const steps = ref<UIStep[]>([])
const selectedStepIndex = ref(-1)
const pageHistoryCount = ref(0) // 页面历史栈深度
const browserLoading = ref(false) // 浏览器加载状态

// 项目和环境相关
const projects = ref<{ id: number; name: string }[]>([])
const selectedProjectId = ref<number | undefined>(undefined)
const environments = ref<Environment[]>([])
const selectedEnvironmentId = ref<number | undefined>(undefined)

// 元素选择模式
const isSelectMode = ref(false)
const selectedElement = ref<Record<string, unknown> | null>(null)

// 输入弹窗
const inputModalVisible = ref(false)
const inputTarget = ref<Record<string, unknown> | null>(null)

// 断言弹窗
const assertModalVisible = ref(false)

// 保存弹窗
const saveModalVisible = ref(false)
const saveForm = ref({
  name: '',
  description: '',
  projectId: null as number | null,
})
const projectsLoading = ref(false)

// 右侧 Tab 当前激活的 key
const rightActiveTab = ref('steps')

// 预览相关（实时执行模式）
const previewCanvasRef = ref<HTMLCanvasElement>()
const previewWs = ref<WebSocket | null>(null)
const previewStarted = ref(false)
const previewRunning = ref(false)
const previewCompleted = ref(false)
const previewCurrentStepIndex = ref(0)
const previewTotalSteps = ref(0)
const previewStepResults = ref<Array<{ success: boolean; message: string; done: boolean }>>([])

// 当前预览的步骤
const previewCurrentStep = computed(() => {
  if (previewCurrentStepIndex.value > 0 && previewCurrentStepIndex.value <= steps.value.length) {
    return steps.value[previewCurrentStepIndex.value - 1]
  }
  return null
})

// ========== 计算属性 ==========

const isRecording = computed(() =>
  recordingStatus.value === 'recording' || recordingStatus.value === 'paused'
)

const isPaused = computed(() => recordingStatus.value === 'paused')

const selectedStep = computed(() =>
  selectedStepIndex.value >= 0 ? steps.value[selectedStepIndex.value] : null
)

const hasPageHistory = computed(() => pageHistoryCount.value > 0)

const statusColor = computed(() => {
  const map: Record<string, string> = {
    idle: 'gray',
    connecting: 'blue',
    recording: 'green',
    paused: 'orange',
    stopped: 'red',
  }
  return map[recordingStatus.value] || 'gray'
})

const statusLabel = computed(() => {
  const map: Record<string, string> = {
    idle: '未录制',
    connecting: '连接中...',
    recording: '录制中',
    paused: '已暂停',
    stopped: '已停止',
  }
  return map[recordingStatus.value] || '未知'
})

// ========== 方法 ==========

async function handleStartRecording() {
  if (!targetUrl.value) return

  // 补全协议
  let url = targetUrl.value
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    url = 'https://' + url
    targetUrl.value = url
  }

  recordingStatus.value = 'connecting'
  // 开始新录制时清空之前的步骤
  steps.value = []
  selectedStepIndex.value = -1
  // 重置预览状态
  previewStarted.value = false
  previewRunning.value = false
  previewCompleted.value = false
  previewCurrentStepIndex.value = 0

  try {
    // 调用后端启动录制
    browserLoading.value = true
    const res = await startRecording({
      url,
      project_id: selectedProjectId.value || 1,
      environment_id: selectedEnvironmentId.value,
      viewport_width: 1280,
      viewport_height: 720,
    })

    sessionId.value = res.session_id
    recordingStatus.value = res.status

    // 建立 WebSocket 连接
    ws.value = createRecordingWebSocket(res.session_id)

    ws.value.onopen = () => {
      console.log('WebSocket 已连接')
    }

    ws.value.onclose = () => {
      console.log('WebSocket 已断开')
      if (recordingStatus.value === 'recording') {
        recordingStatus.value = 'stopped'
      }
    }

    ws.value.onerror = (err) => {
      console.error('WebSocket 错误:', err)
      Message.error('WebSocket 连接失败')
      recordingStatus.value = 'stopped'
    }

    Message.success('录制已启动')
  } catch (err: unknown) {
    console.error('启动录制失败:', err)
    Message.error(`启动录制失败: ${(err as Error).message || '未知错误'}`)
    recordingStatus.value = 'idle'
    browserLoading.value = false
  }
}

function handlePauseRecording() {
  recordingStatus.value = 'paused'
  // 通知后端暂停录制
  if (ws.value && ws.value.readyState === WebSocket.OPEN) {
    ws.value.send(JSON.stringify({
      type: 'command',
      action: 'pause',
    }))
  }
  Message.info('录制已暂停')
}

function handleResumeRecording() {
  recordingStatus.value = 'recording'
  // 通知后端恢复录制
  if (ws.value && ws.value.readyState === WebSocket.OPEN) {
    ws.value.send(JSON.stringify({
      type: 'command',
      action: 'resume',
    }))
  }
  Message.success('录制已恢复')
}

async function handleStopRecording() {
  if (!sessionId.value) return

  recordingStatus.value = 'stopped'

  // 关闭 WebSocket
  if (ws.value) {
    ws.value.close()
    ws.value = null
  }

  // 停止后进入编辑/预览模式，不自动弹出保存弹窗
  Message.info(`录制已停止，共 ${steps.value.length} 步，可预览或编辑后保存`)
}

function handleStepRecorded(step: UIStep) {
  steps.value.push(step)
  // 收到第一个步骤时，说明浏览器已启动成功
  if (browserLoading.value) {
    browserLoading.value = false
  }
  // 跟踪页面历史
  if (step.action === 'new_page') {
    pageHistoryCount.value++
  } else if (step.action === 'go_back') {
    pageHistoryCount.value = Math.max(0, pageHistoryCount.value - 1)
  }
}

function handleStepUpdated(step: UIStep) {
  // 更新已有步骤（合并 click + new_page 时使用）
  const index = steps.value.findIndex(s => s.id === step.id)
  if (index >= 0) {
    steps.value[index] = step
  }
}

function handleReorderSteps(fromIndex: number, toIndex: number) {
  // 重新排序步骤
  const newSteps = [...steps.value]
  const [movedStep] = newSteps.splice(fromIndex, 1)
  newSteps.splice(toIndex, 0, movedStep)
  // 更新 order 字段
  newSteps.forEach((step, index) => {
    step.order = index + 1
  })
  steps.value = newSteps
  // 更新选中的步骤索引
  if (selectedStepIndex.value === fromIndex) {
    selectedStepIndex.value = toIndex
  }
}

function handleInsertStep(afterIndex: number, action: string) {
  // 创建新步骤
  const newStep: UIStep = {
    id: `step_${Date.now()}`,
    order: afterIndex + 2,
    action: action,
    timestamp: Date.now(),
  } as UIStep

  // 根据 action 类型设置默认值
  if (action === 'navigate') {
    newStep.url = ''
  } else if (action === 'type') {
    newStep.value = ''
    newStep.target = { selector: '', text: '' }
  } else if (action === 'press') {
    newStep.key = 'Enter'
  } else if (action === 'wait') {
    ;(newStep as any).waitMs = 1000
  } else if (action === 'assert') {
    ;(newStep as any).type = 'text_equals'
    ;(newStep as any).expected = ''
    ;(newStep as any).selector = ''
  } else {
    newStep.target = { selector: '', text: '' }
  }

  // 插入到指定位置
  const newSteps = [...steps.value]
  newSteps.splice(afterIndex + 1, 0, newStep)
  // 更新 order 字段
  newSteps.forEach((step, index) => {
    step.order = index + 1
  })
  steps.value = newSteps
  // 选中新插入的步骤
  selectedStepIndex.value = afterIndex + 1

  Message.success(`已插入${getActionLabel(action)}步骤`)
}

function getActionLabel(action: string): string {
  const map: Record<string, string> = {
    navigate: '导航',
    click: '点击',
    type: '输入',
    press: '按键',
    wait: '等待',
    assert: '断言',
    drag: '拖拽',
    scroll: '滚动',
    new_page: '新窗口',
    go_back: '返回',
  }
  return map[action] || action
}

function getStepDesc(step: UIStep): string {
  if (step.action === 'navigate') return step.url || ''
  if (step.action === 'new_page') return step.url || '新窗口'
  if (step.action === 'go_back') return step.url || '返回上一页'
  if (step.action === 'type') {
    return `${step.target?.text || step.target?.selector || ''} → "${step.value}"`
  }
  if (step.action === 'press') return step.key || ''
  if (step.action === 'wait') {
    const waitMs = (step as Record<string, unknown>).waitMs as number || step.waitBefore || 0
    return `${waitMs}ms`
  }
  if (step.action === 'drag') {
    const from = step.from as { x: number; y: number } | undefined
    const to = step.to as { x: number; y: number } | undefined
    if (from && to) return `(${from.x},${from.y}) → (${to.x},${to.y})`
    return '拖拽'
  }
  if (step.target) {
    return step.target.text || step.target.selector || ''
  }
  return ''
}

function updatePreviewScreenshot(base64Data: string) {
  const canvas = previewCanvasRef.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const img = new Image()
  img.onload = () => {
    // 调整 canvas 大小以适应容器
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

function handlePreviewStepSelect(index: number) {
  // 实时执行模式下，点击步骤列表不做任何操作
  // 只是高亮显示当前步骤
}

function startPreview() {
  if (steps.value.length === 0) {
    Message.warning('没有录制步骤')
    return
  }

  // 重置状态
  previewStarted.value = true
  previewRunning.value = true
  previewCompleted.value = false
  previewCurrentStepIndex.value = 0
  previewTotalSteps.value = steps.value.length
  previewStepResults.value = steps.value.map(() => ({
    success: false,
    message: '',
    done: false,
  }))

  // 建立 WebSocket 连接
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/ws/ui-preview`
  previewWs.value = new WebSocket(wsUrl)

  previewWs.value.onopen = () => {
    console.log('[Preview] WebSocket 已连接，发送步骤数据...')
    // 发送步骤数据
    previewWs.value?.send(JSON.stringify({
      type: 'start_preview',
      steps: steps.value,
      base_url: targetUrl.value,
    }))
  }

  previewWs.value.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      handlePreviewMessage(data)
    } catch (e) {
      console.error('[Preview] 解析消息失败:', e)
    }
  }

  previewWs.value.onclose = () => {
    console.log('[Preview] WebSocket 已断开')
    if (previewRunning.value) {
      previewRunning.value = false
      previewCompleted.value = true
    }
  }

  previewWs.value.onerror = () => {
    Message.error('预览连接失败')
    previewRunning.value = false
  }
}

function handlePreviewMessage(data: Record<string, unknown>) {
  switch (data.type) {
    case 'screenshot':
      updatePreviewScreenshot(data.data as string)
      break

    case 'progress':
      handlePreviewProgress(data)
      break

    case 'started':
      previewTotalSteps.value = data.total_steps as number
      console.log('[Preview] 开始执行，共', previewTotalSteps.value, '步')
      break

    case 'completed':
      previewRunning.value = false
      previewCompleted.value = true
      const allSuccess = previewStepResults.value.every(r => r.success)
      Message.success(allSuccess ? '预览完成，所有步骤执行成功' : '预览完成，有步骤执行失败')
      break

    case 'error':
      Message.error(data.message as string)
      previewRunning.value = false
      break

    case 'ping':
      // 心跳，忽略
      break
  }
}

function handlePreviewProgress(data: Record<string, unknown>) {
  const progressType = data.progress_type as string
  const current = data.current as number
  const total = data.total as number

  previewCurrentStepIndex.value = current
  previewTotalSteps.value = total

  if (progressType === 'step_end') {
    const result = data.result as Record<string, unknown>
    const index = current - 1
    if (index >= 0 && index < previewStepResults.value.length) {
      previewStepResults.value[index] = {
        success: result.success as boolean,
        message: result.message as string,
        done: true,
      }
    }
  }
}

function stopPreview() {
  // 发送停止命令
  if (previewWs.value && previewWs.value.readyState === WebSocket.OPEN) {
    previewWs.value.send(JSON.stringify({
      type: 'command',
      action: 'stop',
    }))
  }

  // 关闭 WebSocket
  if (previewWs.value) {
    previewWs.value.close()
    previewWs.value = null
  }

  previewRunning.value = false
  previewCompleted.value = true
}

function handleGoBack() {
  if (ws.value && ws.value.readyState === WebSocket.OPEN) {
    ws.value.send(JSON.stringify({
      type: 'command',
      action: 'go_back',
    }))
  }
}

function handleStatusChanged(status: string) {
  recordingStatus.value = status
}

function handleSelectStep(index: number) {
  selectedStepIndex.value = index
}

function handleDeleteStep(index: number) {
  steps.value.splice(index, 1)
  if (selectedStepIndex.value >= steps.value.length) {
    selectedStepIndex.value = steps.value.length - 1
  }
}

function handleClearSteps() {
  steps.value = []
  selectedStepIndex.value = -1
}

function handleUpdateStep(updatedStep: UIStep) {
  const index = steps.value.findIndex(s => s.id === updatedStep.id)
  if (index >= 0) {
    // 使用展开运算符创建新数组，确保触发响应式更新
    const newSteps = [...steps.value]
    newSteps[index] = updatedStep
    steps.value = newSteps
  }
}

function handleStartSelect() {
  // 进入元素选择模式
  isSelectMode.value = true
  selectedElement.value = null
}

function handleElementSelected(element: Record<string, unknown>) {
  // 元素被选中
  selectedElement.value = element
  isSelectMode.value = false
  // 关闭输入弹窗（如果打开的话）
  inputModalVisible.value = false
  inputTarget.value = null
  // 打开断言弹窗
  assertModalVisible.value = true
}

function handleInputTarget(target: Record<string, unknown>) {
  // 收到输入框信息，弹出输入弹窗
  inputTarget.value = target
  // 关闭断言弹窗（如果打开的话）
  assertModalVisible.value = false
  selectedElement.value = null
  // 打开输入弹窗
  inputModalVisible.value = true
}

function handleAddAssert(assertion: Record<string, unknown>) {
  // 只发送给后端，等待后端的 step_recorded 消息再添加到步骤列表
  if (ws.value && ws.value.readyState === WebSocket.OPEN) {
    ws.value.send(JSON.stringify({
      type: 'command',
      action: 'add_assert',
      assertion,
    }))
  }
  // 清除选中的元素，下次添加断言时需要重新选择
  selectedElement.value = null
}

function handleInputConfirm(value: string) {
  // 发送输入命令给后端
  if (ws.value && ws.value.readyState === WebSocket.OPEN && inputTarget.value) {
    ws.value.send(JSON.stringify({
      type: 'command',
      action: 'input_text',
      target: inputTarget.value,
      value: value,
    }))
  }
  inputTarget.value = null
}

function handleInputModalVisibleChange(visible: boolean) {
  if (!visible) {
    // 关闭弹窗时清除数据
    inputTarget.value = null
  }
}

function handleAssertModalVisibleChange(visible: boolean) {
  if (!visible) {
    // 关闭弹窗时清除数据
    selectedElement.value = null
  }
}

async function loadProjects() {
  try {
    const res = await getProjects()
    projects.value = res || []
    // 默认选中第一个项目
    if (projects.value.length > 0 && !selectedProjectId.value) {
      selectedProjectId.value = projects.value[0].id
      saveForm.value.projectId = projects.value[0].id
      // 加载第一个项目的环境列表
      await loadEnvironments(projects.value[0].id)
    }
  } catch (err) {
    console.error('加载项目列表失败:', err)
  }
}

async function loadEnvironments(projectId: number) {
  try {
    const res = await getEnvironments(projectId)
    environments.value = res || []
    // 清空已选环境
    selectedEnvironmentId.value = undefined
  } catch (err) {
    console.error('加载环境列表失败:', err)
  }
}

function handleProjectChange(projectId: number) {
  // 切换项目时重新加载环境列表
  loadEnvironments(projectId)
  saveForm.value.projectId = projectId
}

function handleEnvironmentChange(envId: number | undefined) {
  // 选择环境后自动填充 base_url
  if (envId) {
    const env = environments.value.find(e => e.id === envId)
    if (env && env.base_url) {
      targetUrl.value = env.base_url
    }
  }
}

async function handleSaveCase() {
  await loadProjects()
  saveForm.value.name = `录制用例 ${new Date().toLocaleString()}`
  saveModalVisible.value = true
}

function handleDiscardRecording() {
  // 放弃录制，清空所有状态
  steps.value = []
  selectedStepIndex.value = -1
  sessionId.value = ''
  recordingStatus.value = 'idle'
  Message.info('已放弃录制')
}

async function handleConfirmSave() {
  if (!saveForm.value.name) {
    Message.warning('请输入用例名称')
    return
  }
  if (!saveForm.value.projectId) {
    Message.warning('请选择所属项目')
    return
  }

  try {
    await stopRecording(sessionId.value, {
      name: saveForm.value.name,
      description: saveForm.value.description,
      project_id: saveForm.value.projectId,
      save_to_project: true,
      steps: steps.value,  // 传入前端修改后的步骤
    })

    Message.success('用例保存成功')
    saveModalVisible.value = false

    // 保存成功后保留步骤，用户可以继续编辑或开始新录制
    // 清除 sessionId，因为已经保存过了
    sessionId.value = ''
  } catch (err: unknown) {
    Message.error(`保存失败: ${(err as Error).message || '未知错误'}`)
  }
}

// ========== 生命周期 ==========

onMounted(() => {
  loadProjects()
})

onUnmounted(() => {
  // 清理 WebSocket
  if (ws.value) {
    ws.value.close()
  }
  // 清理预览 WebSocket
  if (previewWs.value) {
    previewWs.value.close()
  }
})
</script>

<style scoped>
.ui-record-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
  background: #f7f8fa;
  overflow: hidden;
  margin: -20px;  /* 抵消 content-wrapper 的 padding */
}

/* 覆盖父布局的 overflow 设置 */
:deep(.layout-content) {
  overflow: hidden !important;
}

:deep(.content-wrapper) {
  min-height: auto !important;
  height: calc(100vh - 60px) !important;
  overflow: hidden !important;
}

.ui-record-page :deep(.step-items) {
  overflow-y: auto !important;  /* 只允许步骤列表滚动 */
}

.record-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: #fff;
  border-bottom: 1px solid #e5e6eb;
  gap: 16px;
}

.toolbar-left {
  flex: 1;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.url-input-group {
  display: flex;
  gap: 8px;
}

.url-input {
  width: 400px;
}

.record-content {
  flex: 1;
  display: flex;
  gap: 12px;
  padding: 12px;
  overflow: hidden;
  min-height: 0;  /* 确保 flex 子元素可以正确滚动 */
}

.content-left {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.content-right {
  width: 360px;
  flex-shrink: 0;
  height: 100%;
  overflow: hidden;
  min-height: 0;  /* 确保 flex 子元素可以正确滚动 */
  display: flex;
  flex-direction: column;
}

.right-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.right-tabs :deep(.arco-tabs-nav) {
  flex-shrink: 0;
}

.right-tabs :deep(.arco-tabs-content) {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.right-tabs :deep(.arco-tabs-content-list) {
  height: 100%;
}

.right-tabs :deep(.arco-tabs-content-item) {
  height: 100% !important;
  overflow: hidden;
}

.right-tabs :deep(.arco-tabs-pane) {
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.tab-pane-content {
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

/* 预览模式样式 */
.preview-mode {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e5e6eb;
  overflow: hidden;
}

.preview-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
  gap: 16px;
}

.preview-screenshot {
  flex: 1;
  background: #1a1a2e;
  border-radius: 8px;
  overflow: hidden;
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.preview-canvas {
  max-width: 100%;
  max-height: 100%;
}

.preview-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: #86909c;
  font-size: 14px;
  width: 100%;
  height: 100%;
}

.preview-bottom {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background: #f7f8fa;
  border-radius: 8px;
}

.preview-info {
  flex: 1;
  min-width: 0;
}

.preview-step-action {
  font-size: 16px;
  font-weight: 600;
  color: #165DFF;
  margin-bottom: 4px;
}

.preview-step-desc {
  font-size: 14px;
  color: #4e5969;
  word-break: break-all;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.preview-controls {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

.preview-progress {
  font-size: 14px;
  color: #86909c;
  white-space: nowrap;
}

.preview-step-hint {
  font-size: 14px;
  color: #86909c;
}
</style>

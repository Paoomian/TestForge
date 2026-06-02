<template>
  <div class="ui-record-page">
    <!-- 顶部工具栏 -->
    <div class="record-toolbar">
      <div class="toolbar-left">
        <div class="url-input-group">
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
            v-if="!isRecording"
            type="primary"
            :disabled="!targetUrl"
            @click="handleStartRecording"
          >
            <template #icon><icon-video-camera /></template>
            开始录制
          </a-button>
          <a-button
            v-else
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
        <a-button
          v-if="steps.length > 0 && !isRecording"
          type="primary"
          @click="handleSaveCase"
        >
          <template #icon><icon-save /></template>
          保存用例
        </a-button>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="record-content">
      <!-- 左侧：浏览器预览 -->
      <div class="content-left">
        <BrowserPreview
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
      </div>

      <!-- 右侧：步骤列表 + 详情 -->
      <div class="content-right">
        <a-tabs default-active-key="steps" class="right-tabs">
          <a-tab-pane key="steps" title="录制步骤">
            <div class="tab-pane-content">
              <StepList
                :steps="steps"
                :selected-index="selectedStepIndex"
                @select-step="handleSelectStep"
                @delete-step="handleDeleteStep"
                @clear-all="handleClearSteps"
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

// ========== 状态 ==========

const targetUrl = ref('')
const sessionId = ref('')
const ws = ref<WebSocket | null>(null)
const recordingStatus = ref('idle') // idle / connecting / recording / paused / stopped
const steps = ref<UIStep[]>([])
const selectedStepIndex = ref(-1)
const pageHistoryCount = ref(0) // 页面历史栈深度
const browserLoading = ref(false) // 浏览器加载状态

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
const projects = ref<{ id: number; name: string }[]>([])
const projectsLoading = ref(false)

// ========== 计算属性 ==========

const isRecording = computed(() =>
  recordingStatus.value === 'recording' || recordingStatus.value === 'paused'
)

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
  steps.value = []

  try {
    // 调用后端启动录制
    browserLoading.value = true
    const res = await startRecording({
      url,
      project_id: 1, // 临时默认项目，后续从上下文获取
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

async function handleStopRecording() {
  if (!sessionId.value) return

  recordingStatus.value = 'stopped'

  // 关闭 WebSocket
  if (ws.value) {
    ws.value.close()
    ws.value = null
  }

  // 如果有步骤，弹出保存弹窗
  if (steps.value.length > 0) {
    saveForm.value.name = `录制用例 ${new Date().toLocaleString()}`
    await loadProjects()
    saveModalVisible.value = true
  }

  Message.info(`录制已停止，共 ${steps.value.length} 步`)
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
    steps.value[index] = updatedStep
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
  assertModalVisible.value = true
}

function handleInputTarget(target: Record<string, unknown>) {
  // 收到输入框信息，弹出输入弹窗
  inputTarget.value = target
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

async function loadProjects() {
  projectsLoading.value = true
  try {
    const res = await getProjects()
    projects.value = res || []
    // 默认选中第一个项目
    if (projects.value.length > 0 && !saveForm.value.projectId) {
      saveForm.value.projectId = projects.value[0].id
    }
  } catch (err) {
    console.error('加载项目列表失败:', err)
  } finally {
    projectsLoading.value = false
  }
}

async function handleSaveCase() {
  await loadProjects()
  saveForm.value.name = `录制用例 ${new Date().toLocaleString()}`
  saveModalVisible.value = true
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
    })

    Message.success('用例保存成功')
    saveModalVisible.value = false

    // 清理状态
    steps.value = []
    sessionId.value = ''
    recordingStatus.value = 'idle'
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
})
</script>

<style scoped>
.ui-record-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
  background: #f7f8fa;
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
}

.content-left {
  flex: 1;
  min-width: 0;
}

.content-right {
  width: 360px;
  flex-shrink: 0;
  height: 100%;
  overflow: hidden;
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
</style>

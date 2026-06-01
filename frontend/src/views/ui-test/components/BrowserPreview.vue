<template>
  <div class="browser-preview" ref="containerRef">
    <!-- 浏览器画面 -->
    <canvas
      ref="canvasRef"
      class="preview-canvas"
      @mousedown="handleMouseDown"
      @mouseup="handleMouseUp"
      @mousemove="handleMouseMove"
      @dblclick="handleDblClick"
      @wheel.prevent="handleWheel"
      @contextmenu.prevent="handleContextMenu"
    />

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <a-spin :size="40" />
      <span class="loading-text">{{ loadingText }}</span>
    </div>

    <!-- 鼠标悬停高亮框 -->
    <div
      v-if="hoverHighlight.visible"
      class="hover-highlight"
      :style="hoverHighlightStyle"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed, nextTick } from 'vue'

interface Props {
  /** WebSocket 连接 */
  ws: WebSocket | null
  /** 是否正在录制 */
  isRecording: boolean
  /** 浏览器视口宽度 */
  viewportWidth?: number
  /** 浏览器视口高度 */
  viewportHeight?: number
  /** 是否为元素选择模式 */
  isSelectMode?: boolean
  /** 是否有弹窗打开（忽略弹窗中的键盘输入） */
  hasModal?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  viewportWidth: 1280,
  viewportHeight: 720,
  isSelectMode: false,
  hasModal: false,
})

const emit = defineEmits<{
  stepRecorded: [step: Record<string, unknown>]
  stepUpdated: [step: Record<string, unknown>]
  statusChanged: [status: string]
  elementSelected: [element: Record<string, unknown>]
  inputTarget: [target: Record<string, unknown>]
}>()

const containerRef = ref<HTMLDivElement>()
const canvasRef = ref<HTMLCanvasElement>()
const loading = ref(true)
const loadingText = ref('正在启动浏览器...')
const currentImage = ref<HTMLImageElement | null>(null)

// 鼠标悬停高亮
const hoverHighlight = ref({
  visible: false,
  x: 0,
  y: 0,
  width: 0,
  height: 0,
})

// 计算画布实际缩放比例
const scaleX = ref(1)
const scaleY = ref(1)

// 鼠标按下状态（用于区分 click 和拖拽）
const mouseDownPos = ref({ x: 0, y: 0 })
const isMouseDown = ref(false)
const isDragging = ref(false)
let mouseDownTime = 0

// 鼠标节流
let lastMouseMoveTime = 0
const MOUSE_MOVE_THROTTLE = 50 // 50ms 节流

const hoverHighlightStyle = computed(() => ({
  left: `${hoverHighlight.value.x * scaleX.value}px`,
  top: `${hoverHighlight.value.y * scaleY.value}px`,
  width: `${hoverHighlight.value.width * scaleX.value}px`,
  height: `${hoverHighlight.value.height * scaleY.value}px`,
}))

// 监听 WebSocket 消息
watch(() => props.ws, (newWs) => {
  if (!newWs) return

  newWs.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      handleWsMessage(data)
    } catch (e) {
      console.error('解析WebSocket消息失败:', e)
    }
  }

  newWs.onclose = () => {
    loading.value = true
    loadingText.value = '连接已断开'
  }
}, { immediate: true })

function handleWsMessage(data: Record<string, unknown>) {
  const msgType = data.type as string
  console.log(`[BrowserPreview] 收到消息类型: ${msgType}`, msgType === 'step_recorded' || msgType === 'step_updated' ? {
    action: data.step?.action,
    url: data.step?.url?.substring(0, 50),
    id: data.step?.id
  } : '')

  switch (msgType) {
    case 'screenshot':
      updateScreenshot(data.data as string)
      loading.value = false
      break
    case 'step_recorded':
      emit('stepRecorded', data.step as Record<string, unknown>)
      break
    case 'step_updated':
      emit('stepUpdated', data.step as Record<string, unknown>)
      break
    case 'page_switch':
      // 页面切换通知，不记录为步骤
      console.log('[BrowserPreview] 页面切换:', (data.url as string)?.substring(0, 50))
      break
    case 'element_info':
      // 元素信息响应（选择模式）
      console.log('[BrowserPreview] 收到元素信息:', data.element)
      emit('elementSelected', data.element as Record<string, unknown>)
      break
    case 'input_target':
      // 输入框信息，让前端弹出输入弹窗
      console.log('[BrowserPreview] 收到输入框信息:', data.target)
      emit('inputTarget', data.target as Record<string, unknown>)
      break
    case 'status':
      emit('statusChanged', data.status as string)
      if (data.status === 'recording') {
        loading.value = false
      }
      break
    case 'error':
      loading.value = true
      loadingText.value = data.message as string
      break
    case 'ping':
      // 心跳，忽略
      break
    default:
      console.log('[BrowserPreview] 未知消息类型:', msgType, data)
  }
}

function updateScreenshot(base64Data: string) {
  const img = new Image()
  img.onload = () => {
    currentImage.value = img
    drawImage()
  }
  img.src = `data:image/jpeg;base64,${base64Data}`
}

function drawImage() {
  const canvas = canvasRef.value
  const img = currentImage.value
  if (!canvas || !img) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  // 根据容器大小自适应
  const container = containerRef.value
  if (container) {
    const containerWidth = container.clientWidth
    const containerHeight = container.clientHeight

    // 计算缩放比例，保持宽高比
    const ratio = Math.min(
      containerWidth / props.viewportWidth,
      containerHeight / props.viewportHeight
    )

    canvas.width = props.viewportWidth * ratio
    canvas.height = props.viewportHeight * ratio

    scaleX.value = ratio
    scaleY.value = ratio
  }

  // 绘制截图
  ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
}

// 坐标转换：canvas 坐标 → 页面坐标
function canvasToPageCoords(canvasX: number, canvasY: number) {
  return {
    x: Math.round(canvasX / scaleX.value),
    y: Math.round(canvasY / scaleY.value),
  }
}

// 获取 canvas 相对于容器的坐标
function getCanvasCoords(event: MouseEvent) {
  const canvas = canvasRef.value
  if (!canvas) return { x: 0, y: 0 }

  const rect = canvas.getBoundingClientRect()
  return {
    x: event.clientX - rect.left,
    y: event.clientY - rect.top,
  }
}

function sendEvent(event: Record<string, unknown>) {
  if (props.ws && props.ws.readyState === WebSocket.OPEN) {
    console.log('[BrowserPreview] 发送事件:', event.type, event.action || '')
    props.ws.send(JSON.stringify(event))
  }
}

// 滚轮事件节流
let lastWheelTime = 0
const WHEEL_THROTTLE = 100 // 100ms 节流

function handleWheel(event: WheelEvent) {
  if (!props.isRecording) return
  event.preventDefault()

  // 节流
  const now = Date.now()
  if (now - lastWheelTime < WHEEL_THROTTLE) return
  lastWheelTime = now

  const coords = getCanvasCoords(event)
  const pageCoords = canvasToPageCoords(coords.x, coords.y)

  sendEvent({
    type: 'mouse_event',
    action: 'scroll',
    x: pageCoords.x,
    y: pageCoords.y,
    deltaX: event.deltaX,
    deltaY: event.deltaY,
  })
}

function handleMouseDown(event: MouseEvent) {
  // 录制模式或选择模式下都处理鼠标按下
  if (!props.isRecording && !props.isSelectMode) return

  const coords = getCanvasCoords(event)
  mouseDownPos.value = coords
  isMouseDown.value = true
  isDragging.value = false
  mouseDownTime = Date.now()

  // 发送 mousedown 事件
  const pageCoords = canvasToPageCoords(coords.x, coords.y)
  console.log('[BrowserPreview] mousedown at:', pageCoords.x, pageCoords.y)
  sendEvent({
    type: 'mouse_event',
    action: 'mousedown',
    x: pageCoords.x,
    y: pageCoords.y,
  })
}

function handleMouseUp(event: MouseEvent) {
  if (!isMouseDown.value) return

  const coords = getCanvasCoords(event)
  const pageCoords = canvasToPageCoords(coords.x, coords.y)

  // 检查是否是点击（移动距离小于 5px 且时间小于 300ms）
  const dx = Math.abs(coords.x - mouseDownPos.value.x)
  const dy = Math.abs(coords.y - mouseDownPos.value.y)
  const dt = Date.now() - mouseDownTime
  const isClick = dx < 5 && dy < 5 && dt < 300

  // 元素选择模式：点击时获取元素信息
  if (props.isSelectMode && isClick) {
    sendEvent({
      type: 'command',
      action: 'get_element',
      x: pageCoords.x,
      y: pageCoords.y,
    })
    isMouseDown.value = false
    return
  }

  // 录制模式：正常录制
  if (props.isRecording) {
    sendEvent({
      type: 'mouse_event',
      action: 'mouseup',
      x: pageCoords.x,
      y: pageCoords.y,
      isClick,
      isDragging: isDragging.value,
    })
  }

  isMouseDown.value = false
  isDragging.value = false
}

function handleMouseMove(event: MouseEvent) {
  // 节流
  const now = Date.now()
  if (now - lastMouseMoveTime < MOUSE_MOVE_THROTTLE) return
  lastMouseMoveTime = now

  const coords = getCanvasCoords(event)
  const pageCoords = canvasToPageCoords(coords.x, coords.y)

  // 如果鼠标按下且移动超过 5px，认为是拖拽
  if (isMouseDown.value) {
    const dx = Math.abs(coords.x - mouseDownPos.value.x)
    const dy = Math.abs(coords.y - mouseDownPos.value.y)
    if (dx > 5 || dy > 5) {
      isDragging.value = true
    }
  }

  // 选择模式或录制模式都发送鼠标移动事件
  if (props.isSelectMode || props.isRecording) {
    sendEvent({
      type: 'mouse_event',
      action: 'mousemove',
      x: pageCoords.x,
      y: pageCoords.y,
      isDragging: isDragging.value,
      isSelectMode: props.isSelectMode,
    })
  }
}

function handleDblClick(event: MouseEvent) {
  if (!props.isRecording) return
  const coords = getCanvasCoords(event)
  const pageCoords = canvasToPageCoords(coords.x, coords.y)
  sendEvent({
    type: 'mouse_event',
    action: 'dblclick',
    x: pageCoords.x,
    y: pageCoords.y,
  })
}

function handleContextMenu(event: MouseEvent) {
  // 右键菜单已禁用（prevent）
}

// 输入状态跟踪
let isInputActive = false
let inputTimer: number | null = null
const INPUT_DEBOUNCE = 500 // 500ms 防抖

// 监听键盘事件（只监听特殊按键，普通字符输入让页面自己处理）
function handleKeyDown(event: KeyboardEvent) {
  if (!props.isRecording) return

  // 如果有弹窗打开，忽略所有键盘事件
  if (props.hasModal) return

  // 检查事件目标是否在弹窗内部
  const target = event.target as HTMLElement
  if (target) {
    const isInModal = target.closest('.arco-modal-container') !== null
    if (isInModal) return
  }

  // 忽略组合键
  if (event.ctrlKey || event.altKey || event.metaKey) return

  // 只处理特殊按键（Enter, Tab, Escape, Backspace 等）
  const specialKeys = ['Enter', 'Tab', 'Escape']
  if (specialKeys.includes(event.key)) {
    // 如果输入框正在输入中，先结束输入
    if (isInputActive) {
      finishInput()
    }
    sendEvent({
      type: 'keyboard_event',
      key: event.key,
    })
  }
  // 其他按键（包括普通字符、Backspace 等）不拦截，让页面自己处理
}

// 输入框输入事件处理（由后端通过 input 事件触发）
function handleInputEvent(value: string) {
  isInputActive = true

  // 清除之前的定时器
  if (inputTimer) {
    clearTimeout(inputTimer)
  }

  // 设置新的定时器，输入停止后自动结束
  inputTimer = window.setTimeout(() => {
    finishInput()
  }, INPUT_DEBOUNCE)
}

function finishInput() {
  if (isInputActive) {
    isInputActive = false
    if (inputTimer) {
      clearTimeout(inputTimer)
      inputTimer = null
    }
    // 通知后端结束输入
    sendEvent({
      type: 'input_event',
      action: 'finish',
    })
  }
}

// 窗口大小变化时重绘
function handleResize() {
  drawImage()
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
  window.addEventListener('resize', handleResize)
  nextTick(drawImage)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.browser-preview {
  position: relative;
  width: 100%;
  height: 100%;
  background: #1a1a2e;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-canvas {
  cursor: crosshair;
  border-radius: 4px;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(26, 26, 46, 0.9);
  gap: 16px;
}

.loading-text {
  color: #999;
  font-size: 14px;
}

.hover-highlight {
  position: absolute;
  border: 2px solid #165DFF;
  background: rgba(22, 93, 255, 0.1);
  pointer-events: none;
  transition: all 0.1s ease;
  border-radius: 2px;
}
</style>

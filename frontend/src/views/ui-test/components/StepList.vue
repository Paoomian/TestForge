<template>
  <div class="step-list">
    <!-- 步骤列表头部 -->
    <div class="step-list-header">
      <span class="step-count">共 {{ steps.length }} 步</span>
      <a-button
        v-if="steps.length > 0 && !readonly"
        type="text"
        size="mini"
        status="danger"
        @click="$emit('clearAll')"
      >
        清空
      </a-button>
    </div>

    <!-- 步骤列表 -->
    <div class="step-items" ref="listRef">
      <div
        v-for="(step, index) in steps"
        :key="step.id"
        class="step-item"
        :class="{
          'step-item--active': selectedIndex === index,
          'step-item--current': currentStepIndex === index + 1,
          'step-item--success': stepResults[index]?.done && stepResults[index]?.success,
          'step-item--failed': stepResults[index]?.done && !stepResults[index]?.success,
          'step-item--pending': stepResults.length > 0 && !stepResults[index]?.done,
          'step-item--dragging': dragIndex === index,
          'step-item--drag-over': dragOverIndex === index && dragIndex !== index,
        }"
        :draggable="!readonly"
        @click="$emit('selectStep', index)"
        @dragstart="handleDragStart(index, $event)"
        @dragover.prevent="handleDragOver(index, $event)"
        @dragleave="handleDragLeave"
        @drop="handleDrop(index, $event)"
        @dragend="handleDragEnd"
      >
        <!-- 步骤序号/状态 -->
        <div class="step-index">
          <icon-check-circle v-if="stepResults[index]?.done && stepResults[index]?.success" style="color: #00b42a;" />
          <icon-close-circle v-else-if="stepResults[index]?.done && !stepResults[index]?.success" style="color: #f53f3f;" />
          <span v-else>{{ index + 1 }}</span>
        </div>

        <!-- 步骤信息 -->
        <div class="step-info">
          <div class="step-action">{{ getActionLabel(step.action) }}</div>
          <div class="step-desc">{{ getStepDescription(step) }}</div>
          <div v-if="stepResults[index]?.done && stepResults[index]?.message" class="step-message" :class="{ 'message-error': !stepResults[index]?.success }">
            {{ stepResults[index]?.message }}
          </div>
        </div>

        <!-- 操作按钮（非只读模式显示） -->
        <div v-if="!readonly" class="step-actions">
          <a-dropdown @select="(value) => handleInsertStep(index, value as string)" position="br">
            <a-button
              type="text"
              size="mini"
              class="step-insert"
              @click.stop
            >
              <template #icon><icon-plus /></template>
            </a-button>
            <template #content>
              <a-doption value="navigate">导航</a-doption>
              <a-doption value="click">点击</a-doption>
              <a-doption value="type">输入</a-doption>
              <a-doption value="press">按键</a-doption>
              <a-doption value="wait">等待</a-doption>
              <a-doption value="assert">断言</a-doption>
            </template>
          </a-dropdown>
          <a-button
            type="text"
            size="mini"
            status="danger"
            class="step-delete"
            @click.stop="$emit('deleteStep', index)"
          >
            <template #icon><icon-delete /></template>
          </a-button>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="steps.length === 0" class="step-empty">
        <icon-video-camera style="font-size: 32px; color: #ccc;" />
        <span>点击"开始录制"后，在左侧浏览器中操作</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import {
  IconDelete,
  IconVideoCamera,
  IconLink,
  IconPen,
  IconEdit,
  IconSelectAll,
  IconCheckSquare,
  IconSwap,
  IconClockCircle,
  IconObliqueLine,
  IconCheckCircle,
  IconCloseCircle,
  IconPlus,
} from '@arco-design/web-vue/es/icon'
import type { UIStep } from '@/api/uiCase'

interface StepResult {
  success: boolean
  message: string
  done: boolean
}

interface Props {
  steps: UIStep[]
  selectedIndex: number
  stepResults?: StepResult[]
  currentStepIndex?: number
  readonly?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  stepResults: () => [],
  currentStepIndex: 0,
  readonly: false,
})

const emit = defineEmits<{
  selectStep: [index: number]
  deleteStep: [index: number]
  clearAll: []
  reorder: [fromIndex: number, toIndex: number]
  insertStep: [afterIndex: number, action: string]
}>()

const listRef = ref<HTMLDivElement>()

// 拖拽状态
const dragIndex = ref<number | null>(null)
const dragOverIndex = ref<number | null>(null)

// 拖拽处理函数
function handleDragStart(index: number, event: DragEvent) {
  dragIndex.value = index
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', index.toString())
  }
}

function handleDragOver(index: number, event: DragEvent) {
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move'
  }
  dragOverIndex.value = index
}

function handleDragLeave() {
  dragOverIndex.value = null
}

function handleDrop(toIndex: number, event: DragEvent) {
  event.preventDefault()
  if (dragIndex.value !== null && dragIndex.value !== toIndex) {
    emit('reorder', dragIndex.value, toIndex)
  }
  dragIndex.value = null
  dragOverIndex.value = null
}

function handleDragEnd() {
  dragIndex.value = null
  dragOverIndex.value = null
}

function handleInsertStep(afterIndex: number, action: string) {
  emit('insertStep', afterIndex, action)
}

// 自动滚动到底部
watch(() => props.steps.length, () => {
  nextTick(() => {
    if (listRef.value) {
      listRef.value.scrollTop = listRef.value.scrollHeight
    }
  })
})

function getStepIcon(action: string) {
  const iconMap: Record<string, unknown> = {
    navigate: IconLink,
    click: IconPen,
    dblclick: IconPen,
    type: IconEdit,
    press: IconPen,
    select: IconSelectAll,
    check: IconCheckSquare,
    uncheck: IconCheckSquare,
    hover: IconObliqueLine,
    scroll: IconSwap,
    wait: IconClockCircle,
    drag: IconSwap,
    new_page: IconLink,
    go_back: IconLink,
    assert: IconCheckCircle,
  }
  return iconMap[action] || IconPen
}

function getActionLabel(action: string): string {
  const labelMap: Record<string, string> = {
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
  return labelMap[action] || action
}

function getAssertTypeLabel(type: string): string {
  const map: Record<string, string> = {
    element_exists: '元素存在',
    element_not_exists: '元素不存在',
    text_equals: '文本等于',
    text_contains: '文本包含',
    url_equals: 'URL 等于',
    url_contains: 'URL 包含',
    title_equals: '标题等于',
    title_contains: '标题包含',
    value_equals: '值等于',
    attribute_equals: '属性等于',
  }
  return map[type] || type
}

function getStepDescription(step: UIStep): string {
  if (step.action === 'navigate') {
    return step.url || ''
  }
  if (step.action === 'new_page') {
    return step.url || '新窗口'
  }
  if (step.action === 'go_back') {
    return step.url || '返回上一页'
  }
  if (step.action === 'assert') {
    const assertType = (step as Record<string, unknown>).type as string
    const expected = (step as Record<string, unknown>).expected as string
    const selector = (step as Record<string, unknown>).selector as string
    const label = getAssertTypeLabel(assertType)
    if (expected) return `${label}: ${expected}`
    if (selector) return `${label}: ${selector}`
    return label
  }
  if (step.action === 'type') {
    return `${step.target?.text || step.target?.selector || ''} → "${step.value}"`
  }
  if (step.action === 'press') {
    return step.key || ''
  }
  if (step.action === 'wait') {
    const waitMs = (step as Record<string, unknown>).waitMs as number || step.waitBefore || 0
    return `${waitMs}ms`
  }
  if (step.action === 'drag') {
    const from = step.from as { x: number; y: number } | undefined
    const to = step.to as { x: number; y: number } | undefined
    if (from && to) {
      return `(${from.x},${from.y}) → (${to.x},${to.y})`
    }
    return '拖拽'
  }
  if (step.target) {
    return step.target.text || step.target.selector || step.target.xpath || ''
  }
  return ''
}
</script>

<style scoped>
.step-list {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  max-height: 100%;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e5e6eb;
  overflow: hidden;
}

.step-list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #e5e6eb;
  flex-shrink: 0;
}

.step-count {
  font-size: 13px;
  color: #86909c;
}

.step-items {
  flex: 1;
  min-height: 0;
  max-height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 8px;
  /* 确保滚动条样式 */
  scrollbar-width: thin;
  scrollbar-color: #c9cdd4 transparent;
}

.step-items::-webkit-scrollbar {
  width: 6px;
}

.step-items::-webkit-scrollbar-track {
  background: transparent;
}

.step-items::-webkit-scrollbar-thumb {
  background-color: #c9cdd4;
  border-radius: 3px;
}

.step-items::-webkit-scrollbar-thumb:hover {
  background-color: #86909c;
}

.step-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.step-item:hover {
  background: #f2f3f5;
}

.step-item--active {
  background: #e8f3ff;
  border-color: #165DFF;
}

.step-item--current {
  background: #e8f3ff;
  border-color: #165DFF;
}

.step-item--success {
  background: #e8ffea;
}

.step-item--failed {
  background: #ffe8e8;
}

.step-item--pending {
  opacity: 0.6;
}

/* 拖拽样式 */
.step-item[draggable="true"] {
  cursor: grab;
}

.step-item[draggable="true"]:active {
  cursor: grabbing;
}

.step-item--dragging {
  opacity: 0.5;
  background: #e8f3ff;
}

.step-item--drag-over {
  border-top: 2px solid #165DFF;
  margin-top: -2px;
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

.step-item--active .step-index {
  background: #165DFF;
  color: #fff;
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

.step-thumbnail {
  width: 48px;
  height: 32px;
  border-radius: 4px;
  overflow: hidden;
  flex-shrink: 0;
  border: 1px solid #e5e6eb;
}

.step-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.step-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  opacity: 0;
  flex-shrink: 0;
  transition: opacity 0.2s ease;
}

.step-item:hover .step-actions {
  opacity: 1;
}

.step-insert,
.step-delete {
  flex-shrink: 0;
}

.step-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px 20px;
  color: #c9cdd4;
  font-size: 13px;
  text-align: center;
}
</style>

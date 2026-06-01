<template>
  <div class="step-list">
    <!-- 步骤列表头部 -->
    <div class="step-list-header">
      <span class="step-count">共 {{ steps.length }} 步</span>
      <a-button
        v-if="steps.length > 0"
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
        :class="{ 'step-item--active': selectedIndex === index }"
        @click="$emit('selectStep', index)"
      >
        <!-- 步骤序号 -->
        <div class="step-index">{{ index + 1 }}</div>

        <!-- 步骤图标 -->
        <div class="step-icon">
          <component :is="getStepIcon(step.action)" />
        </div>

        <!-- 步骤信息 -->
        <div class="step-info">
          <span class="step-action">{{ getActionLabel(step.action) }}</span>
          <span class="step-target">{{ getStepDescription(step) }}</span>
        </div>

        <!-- 截图缩略图 -->
        <div v-if="step.screenshot" class="step-thumbnail">
          <img :src="`data:image/jpeg;base64,${step.screenshot}`" alt="截图" />
        </div>

        <!-- 删除按钮 -->
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
} from '@arco-design/web-vue/es/icon'
import type { UIStep } from '@/api/uiCase'

interface Props {
  steps: UIStep[]
  selectedIndex: number
}

const props = defineProps<Props>()

defineEmits<{
  selectStep: [index: number]
  deleteStep: [index: number]
  clearAll: []
}>()

const listRef = ref<HTMLDivElement>()

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
  align-items: center;
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

.step-index {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f2f3f5;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 500;
  color: #4e5969;
  flex-shrink: 0;
}

.step-item--active .step-index {
  background: #165DFF;
  color: #fff;
}

.step-icon {
  font-size: 16px;
  color: #86909c;
  flex-shrink: 0;
}

.step-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.step-action {
  font-size: 12px;
  color: #165DFF;
  font-weight: 500;
}

.step-target {
  font-size: 13px;
  color: #4e5969;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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

.step-delete {
  opacity: 0;
  flex-shrink: 0;
}

.step-item:hover .step-delete {
  opacity: 1;
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

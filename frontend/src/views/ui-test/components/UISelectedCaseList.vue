<template>
  <div class="selected-case-list">
    <div v-if="cases.length === 0" class="empty-state">
      <span>暂未选择用例</span>
    </div>

    <div v-else class="list-body" ref="listRef">
      <div
        v-for="(caseItem, index) in cases"
        :key="caseItem.id"
        class="case-row"
        :class="{ dragging: dragIndex === index, 'drag-over': dragOverIndex === index }"
        draggable="true"
        @dragstart="onDragStart(index, $event)"
        @dragover.prevent="onDragOver(index, $event)"
        @dragleave="onDragLeave"
        @drop="onDrop(index)"
        @dragend="onDragEnd"
      >
        <icon-drag-dot-vertical class="drag-handle" />
        <span class="case-index">{{ index + 1 }}</span>
        <span class="case-name" :title="caseItem.name">{{ caseItem.name }}</span>
        <a-tag size="small" color="blue">{{ caseItem.steps?.length || 0 }} 步</a-tag>
        <a-button
          type="text"
          size="mini"
          status="danger"
          class="remove-btn"
          @click="$emit('remove', caseItem.id)"
        >
          <template #icon><icon-close /></template>
        </a-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import {
  IconSwap,
  IconEmpty,
  IconDragDotVertical,
  IconClose,
} from '@arco-design/web-vue/es/icon'
import type { UICase } from '@/api/uiCase'

const props = defineProps<{
  cases: UICase[]
}>()

const emit = defineEmits<{
  (e: 'reorder', orderedIds: number[]): void
  (e: 'remove', caseId: number): void
}>()

// 拖拽状态
const dragIndex = ref<number>(-1)
const dragOverIndex = ref<number>(-1)

function onDragStart(index: number, event: DragEvent) {
  dragIndex.value = index
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', String(index))
  }
}

function onDragOver(index: number, _event: DragEvent) {
  _event.preventDefault()
  if (dragIndex.value !== index) {
    dragOverIndex.value = index
  }
}

function onDragLeave() {
  dragOverIndex.value = -1
}

function onDrop(targetIndex: number) {
  if (dragIndex.value === -1 || dragIndex.value === targetIndex) {
    return
  }

  const newCases = [...props.cases]
  const [removed] = newCases.splice(dragIndex.value, 1)
  newCases.splice(targetIndex, 0, removed)

  emit('reorder', newCases.map(c => c.id))

  dragIndex.value = -1
  dragOverIndex.value = -1
}

function onDragEnd() {
  dragIndex.value = -1
  dragOverIndex.value = -1
}
</script>

<style scoped>
.selected-case-list {
  border: 1px solid var(--color-border-2);
  border-radius: var(--radius-small);
  overflow: hidden;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  color: var(--color-text-4);
  font-size: 12px;
}

.list-body {
  max-height: 200px;
  overflow-y: auto;
}

.case-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-bottom: 1px solid var(--color-border-1);
  background: var(--color-bg-white);
  cursor: grab;
  transition: background 0.15s ease;
}

.case-row:last-child {
  border-bottom: none;
}

.case-row:hover {
  background: var(--color-fill-1);
}

.case-row:active {
  cursor: grabbing;
}

.case-row.dragging {
  opacity: 0.5;
  background: var(--color-fill-2);
}

.case-row.drag-over {
  border-top: 2px solid var(--color-primary-light-4);
}

.drag-handle {
  color: var(--color-text-4);
  font-size: 14px;
  flex-shrink: 0;
  cursor: grab;
}

.case-index {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-fill-2);
  border-radius: 50%;
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-2);
  flex-shrink: 0;
}

.case-name {
  flex: 1;
  font-size: 13px;
  color: var(--color-text-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.remove-btn {
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.case-row:hover .remove-btn {
  opacity: 1;
}
</style>

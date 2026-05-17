<template>
  <div class="selected-case-list">
    <div class="list-header">
      <div class="header-title">
        <icon-swap />
        <span>执行顺序</span>
        <a-tag size="small" color="blue">已选 {{ cases.length }} 个</a-tag>
      </div>
      <span class="header-hint">拖拽调整顺序</span>
    </div>

    <div v-if="cases.length === 0" class="empty-state">
      <icon-inbox :size="32" />
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
        <div class="drag-handle">
          <icon-drag-arrow-vertical />
        </div>
        <div class="case-index">{{ index + 1 }}</div>
        <div class="case-info">
          <span class="case-number">{{ caseItem.case_number }}</span>
          <span class="case-name">{{ caseItem.name }}</span>
        </div>
        <a-tag size="small" :color="getMethodColor(caseItem.method)">{{ caseItem.method }}</a-tag>
        <a-tag size="small" :color="getPriorityColor(caseItem.priority)">{{ caseItem.priority }}</a-tag>
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
import type { APITestCase } from '@/api/apiTestCase'

const props = defineProps<{
  cases: APITestCase[]
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

function onDragOver(index: number, event: DragEvent) {
  event.preventDefault()
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

function getMethodColor(method: string): string {
  const colors: Record<string, string> = {
    GET: 'blue', POST: 'green', PUT: 'orange', DELETE: 'red', PATCH: 'purple'
  }
  return colors[method] || 'gray'
}

function getPriorityColor(priority: string): string {
  const colors: Record<string, string> = {
    P0: 'red', P1: 'orange', P2: 'blue', P3: 'green'
  }
  return colors[priority] || 'gray'
}
</script>

<style scoped>
.selected-case-list {
  border: 1px solid var(--color-border-2);
  border-radius: var(--radius-medium);
  overflow: hidden;
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: var(--color-fill-1);
  border-bottom: 1px solid var(--color-border-2);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-2);
}

.header-hint {
  font-size: 12px;
  color: var(--color-text-4);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px;
  color: var(--color-text-4);
  gap: 8px;
  font-size: 13px;
}

.list-body {
  max-height: 300px;
  overflow-y: auto;
}

.case-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--color-border-1);
  background: var(--color-bg-white);
  cursor: grab;
  transition: background 0.15s ease, box-shadow 0.15s ease;
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
  font-size: 16px;
  flex-shrink: 0;
  cursor: grab;
}

.drag-handle:active {
  cursor: grabbing;
}

.case-index {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-fill-2);
  border-radius: 50%;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-2);
  flex-shrink: 0;
}

.case-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.case-number {
  font-size: 12px;
  color: var(--color-text-3);
  flex-shrink: 0;
}

.case-name {
  font-size: 13px;
  color: var(--color-text-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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

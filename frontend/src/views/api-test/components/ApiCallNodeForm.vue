<template>
  <div class="api-call-form">
    <a-form-item label="选择用例" label-col-flex="80px">
      <a-select
        :model-value="node.case_id"
        placeholder="请选择测试用例"
        allow-search
        :filter-option="filterOption"
        @update:model-value="$emit('update', { case_id: $event, case_name: getCaseName($event) })"
      >
        <a-option v-for="c in cases" :key="c.id" :value="c.id">
          <div class="case-option">
            <span class="case-number">{{ c.case_number }}</span>
            <span class="case-name">{{ c.name }}</span>
            <a-tag size="small" :color="getMethodColor(c.method)">{{ c.method }}</a-tag>
          </div>
        </a-option>
      </a-select>
    </a-form-item>

    <div v-if="selectedCase" class="case-preview">
      <a-descriptions :column="2" size="small" bordered>
        <a-descriptions-item label="用例编号">{{ selectedCase.case_number }}</a-descriptions-item>
        <a-descriptions-item label="请求方法">
          <a-tag :color="getMethodColor(selectedCase.method)">{{ selectedCase.method }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="模块">{{ selectedCase.module || '-' }}</a-descriptions-item>
        <a-descriptions-item label="优先级">
          <a-tag :color="getPriorityColor(selectedCase.priority)">{{ selectedCase.priority }}</a-tag>
        </a-descriptions-item>
      </a-descriptions>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { SceneNodeItem } from '@/api/sceneNode'
import type { APITestCase } from '@/api/apiTestCase'

const props = defineProps<{
  node: SceneNodeItem
  cases: APITestCase[]
}>()

defineEmits<{
  (e: 'update', data: Partial<SceneNodeItem>): void
}>()

const selectedCase = computed(() => {
  return props.cases.find(c => c.id === props.node.case_id)
})

function getCaseName(caseId: number): string {
  return props.cases.find(c => c.id === caseId)?.name || ''
}

function filterOption(inputValue: string, option: any): boolean {
  const caseItem = props.cases.find(c => c.id === option.value)
  if (!caseItem) return false
  const searchStr = inputValue.toLowerCase()
  return (
    caseItem.name.toLowerCase().includes(searchStr) ||
    caseItem.case_number.toLowerCase().includes(searchStr)
  )
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
.api-call-form {
  width: 100%;
}

.case-option {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.case-number {
  font-size: 12px;
  color: var(--color-text-3);
  min-width: 100px;
}

.case-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.case-preview {
  margin-top: 12px;
  padding: 12px;
  background: var(--color-fill-1);
  border-radius: var(--radius-small);
}
</style>

<template>
  <div
    class="scene-node-card"
    :class="[`node-type-${node.node_type}`, { selected, disabled: !node.enabled }]"
    @click="$emit('click')"
  >
    <div class="card-left">
      <span class="node-index">{{ index + 1 }}</span>
      <div class="node-type-dot" :style="{ background: nodeColors[node.node_type] }"></div>
    </div>
    <div class="card-content">
      <div class="card-header">
        <a-tag :color="nodeColors[node.node_type]" size="small">
          {{ nodeTypeLabels[node.node_type] }}
        </a-tag>
      </div>
      <div class="card-summary" v-if="summaryText">
        {{ summaryText }}
      </div>
    </div>
    <div class="card-actions" @click.stop>
      <a-tooltip :content="node.enabled ? '禁用' : '启用'">
        <a-button type="text" size="mini" @click="$emit('toggle')">
          <template #icon>
            <icon-check-circle-fill v-if="node.enabled" style="color: #00b42a" />
            <icon-minus-circle v-else style="color: #86909c" />
          </template>
        </a-button>
      </a-tooltip>
      <a-tooltip content="删除">
        <a-button type="text" size="mini" status="danger" @click="$emit('delete')">
          <template #icon><icon-delete /></template>
        </a-button>
      </a-tooltip>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { SceneNodeItem, SceneNodeType } from '@/api/sceneNode'

const nodeColors: Record<SceneNodeType, string> = {
  api_call: '#3370ff', condition: '#ff7d00', wait: '#86909c', data_assign: '#00b42a'
}

const nodeTypeLabels: Record<SceneNodeType, string> = {
  api_call: '接口调用', condition: '条件判断', wait: '等待延时', data_assign: '数据赋值'
}

const operatorLabels: Record<string, string> = {
  eq: '==', neq: '!=', gt: '>', lt: '<', gte: '>=', lte: '<=',
  contains: '包含', not_contains: '不包含', empty: '为空', not_empty: '不为空'
}

const props = defineProps<{
  node: SceneNodeItem
  selected: boolean
  index: number
}>()

defineEmits<{
  (e: 'click'): void
  (e: 'toggle'): void
  (e: 'delete'): void
}>()

const summaryText = computed(() => {
  const n = props.node
  switch (n.node_type) {
    case 'api_call':
      return n.case_name || undefined
    case 'condition':
      if (n.condition_variable) {
        return `${n.condition_variable} ${operatorLabels[n.condition_operator || 'eq']} ${n.condition_value || ''}`
      }
      return undefined
    case 'wait':
      return `等待 ${n.wait_seconds || 5} 秒`
    case 'data_assign':
      return n.assign_variable ? `${n.assign_variable} = ${n.assign_value || '...'}` : undefined
    default:
      return undefined
  }
})
</script>

<style scoped>
.scene-node-card {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 10px 12px;
  background: white;
  border: 1.5px solid var(--color-border-3);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  gap: 10px;
}

.scene-node-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border-color: var(--color-border-4);
}

.scene-node-card.selected {
  border-color: var(--color-primary-6);
  box-shadow: 0 0 0 2px rgba(var(--primary-6), 0.15);
}

.scene-node-card.disabled {
  opacity: 0.5;
  background: var(--color-fill-1);
}

.scene-node-card.node-type-api_call { border-left: 4px solid #3370ff; }
.scene-node-card.node-type-condition { border-left: 4px solid #ff7d00; }
.scene-node-card.node-type-wait { border-left: 4px solid #86909c; }
.scene-node-card.node-type-data_assign { border-left: 4px solid #00b42a; }

.card-left {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.node-index {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-3);
  background: var(--color-fill-2);
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.node-type-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.card-content {
  flex: 1;
  min-width: 0;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 6px;
}

.card-summary {
  font-size: 11px;
  color: var(--color-text-3);
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-actions {
  display: flex;
  gap: 0;
  flex-shrink: 0;
}
</style>

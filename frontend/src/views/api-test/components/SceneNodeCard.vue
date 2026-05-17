<template>
  <a-card
    class="scene-node-card"
    :class="[`node-type-${node.node_type}`, { disabled: !node.enabled }]"
    :bordered="true"
    size="small"
  >
    <div class="node-header">
      <div class="node-type-badge" :class="`badge-${node.node_type}`">
        <icon-code v-if="node.node_type === 'api_call'" />
        <icon-branch v-else-if="node.node_type === 'condition'" />
        <icon-clock-circle v-else-if="node.node_type === 'wait'" />
        <icon-storage v-else-if="node.node_type === 'data_assign'" />
        <span class="badge-text">{{ nodeTypeLabels[node.node_type] }}</span>
      </div>

      <a-input
        :model-value="node.name"
        size="small"
        class="node-name-input"
        placeholder="节点名称"
        @update:model-value="$emit('update', { name: $event })"
      />

      <a-space :size="4">
        <a-tooltip :content="node.enabled ? '点击禁用' : '点击启用'">
          <a-switch
            :model-value="node.enabled"
            size="small"
            @update:model-value="$emit('update', { enabled: $event })"
          />
        </a-tooltip>
        <a-tooltip content="删除节点">
          <a-button type="text" size="mini" status="danger" @click="handleDelete">
            <template #icon><icon-delete /></template>
          </a-button>
        </a-tooltip>
      </a-space>
    </div>

    <div class="node-body">
      <ApiCallNodeForm
        v-if="node.node_type === 'api_call'"
        :node="node"
        :cases="cases"
        @update="$emit('update', $event)"
      />

      <ConditionNodeForm
        v-else-if="node.node_type === 'condition'"
        :node="node"
        @update="$emit('update', $event)"
      />

      <WaitNodeForm
        v-else-if="node.node_type === 'wait'"
        :node="node"
        @update="$emit('update', $event)"
      />

      <DataAssignNodeForm
        v-else-if="node.node_type === 'data_assign'"
        :node="node"
        @update="$emit('update', $event)"
      />
    </div>
  </a-card>
</template>

<script setup lang="ts">
import { Modal } from '@arco-design/web-vue'
import type { SceneNodeItem, SceneNodeType } from '@/api/sceneNode'
import type { APITestCase } from '@/api/apiTestCase'
import ApiCallNodeForm from './ApiCallNodeForm.vue'
import ConditionNodeForm from './ConditionNodeForm.vue'
import WaitNodeForm from './WaitNodeForm.vue'
import DataAssignNodeForm from './DataAssignNodeForm.vue'

const nodeTypeLabels: Record<SceneNodeType, string> = {
  api_call: '接口调用',
  condition: '条件判断',
  wait: '等待延时',
  data_assign: '数据赋值'
}

defineProps<{
  node: SceneNodeItem
  cases: APITestCase[]
}>()

const emit = defineEmits<{
  (e: 'update', data: Partial<SceneNodeItem>): void
  (e: 'remove'): void
}>()

function handleDelete() {
  Modal.confirm({
    title: '确认删除',
    content: '确定要删除这个节点吗？',
    onOk: () => {
      emit('remove')
    }
  })
}
</script>

<style scoped>
.scene-node-card {
  width: 100%;
  border-left: 4px solid var(--color-border-3);
  transition: all 0.2s ease;
}

.scene-node-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.scene-node-card.node-type-api_call {
  border-left-color: #3370ff;
}

.scene-node-card.node-type-condition {
  border-left-color: #ff7d00;
}

.scene-node-card.node-type-wait {
  border-left-color: #86909c;
}

.scene-node-card.node-type-data_assign {
  border-left-color: #00b42a;
}

.scene-node-card.disabled {
  opacity: 0.6;
  background: var(--color-fill-1);
}

.node-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.node-type-badge {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  flex-shrink: 0;
}

.badge-api_call {
  background: #e8f3ff;
  color: #3370ff;
}

.badge-condition {
  background: #fff7e8;
  color: #ff7d00;
}

.badge-wait {
  background: #f2f3f5;
  color: #86909c;
}

.badge-data_assign {
  background: #e8ffea;
  color: #00b42a;
}

.badge-text {
  white-space: nowrap;
}

.node-name-input {
  flex: 1;
  min-width: 0;
}

.node-body {
  padding-top: 4px;
}

:deep(.arco-card-body) {
  padding: 14px;
}
</style>

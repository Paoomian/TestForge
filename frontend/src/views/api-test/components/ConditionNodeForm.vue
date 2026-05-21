<template>
  <div class="condition-form">
    <a-form-item label="变量名" label-col-flex="80px">
      <a-input
        :model-value="node.condition_variable"
        placeholder="如: status, code, user_id"
        @update:model-value="$emit('update', { condition_variable: $event })"
      >
        <template #prefix><span v-text="'{{'"></span></template>
        <template #suffix><span v-text="'}}'"></span></template>
      </a-input>
    </a-form-item>

    <a-row :gutter="12">
      <a-col :span="8">
        <a-form-item label="运算符" label-col-flex="80px">
          <a-select
            :model-value="node.condition_operator || 'eq'"
            @update:model-value="$emit('update', { condition_operator: $event })"
          >
            <a-option value="eq">等于 (==)</a-option>
            <a-option value="neq">不等于 (!=)</a-option>
            <a-option value="gt">大于 (>)</a-option>
            <a-option value="lt">小于 (<)</a-option>
            <a-option value="gte">大于等于 (>=)</a-option>
            <a-option value="lte">小于等于 (<=)</a-option>
            <a-option value="contains">包含</a-option>
            <a-option value="not_contains">不包含</a-option>
            <a-option value="empty">为空</a-option>
            <a-option value="not_empty">不为空</a-option>
          </a-select>
        </a-form-item>
      </a-col>
      <a-col :span="16">
        <a-form-item label="比较值" label-col-flex="80px">
          <a-input
            :model-value="node.condition_value"
            placeholder="输入比较值"
            :disabled="node.condition_operator === 'empty' || node.condition_operator === 'not_empty'"
            @update:model-value="$emit('update', { condition_value: $event })"
          />
        </a-form-item>
      </a-col>
    </a-row>

    <a-divider style="margin: 12px 0;">分支跳转</a-divider>

    <div class="branch-config">
      <a-form-item label="为真时" label-col-flex="80px">
        <a-select
          :model-value="trueBranchTarget"
          placeholder="继续下一个节点"
          allow-clear
          @update:model-value="onTrueBranchChange"
        >
          <a-option
            v-for="n in otherNodes"
            :key="n.id || n.sort_order"
            :value="n.id || n.sort_order"
          >
            {{ n.sort_order + 1 }}. {{ n.name }}
          </a-option>
        </a-select>
      </a-form-item>

      <a-form-item label="为假时" label-col-flex="80px">
        <a-select
          :model-value="falseBranchTarget"
          placeholder="继续下一个节点"
          allow-clear
          @update:model-value="onFalseBranchChange"
        >
          <a-option
            v-for="n in otherNodes"
            :key="n.id || n.sort_order"
            :value="n.id || n.sort_order"
          >
            {{ n.sort_order + 1 }}. {{ n.name }}
          </a-option>
        </a-select>
      </a-form-item>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { SceneNodeItem } from '@/api/sceneNode'

const props = defineProps<{
  node: SceneNodeItem
  nodes: SceneNodeItem[]
}>()

const emit = defineEmits<{
  (e: 'update', data: Partial<SceneNodeItem>): void
}>()

// 过滤掉当前节点
const otherNodes = computed(() =>
  props.nodes.filter(n => n !== props.node)
)

// 当前真分支目标
const trueBranchTarget = computed(() => {
  const branches = props.node.true_branch || []
  return branches.length > 0 ? branches[0] : undefined
})

// 当前假分支目标
const falseBranchTarget = computed(() => {
  const branches = props.node.false_branch || []
  return branches.length > 0 ? branches[0] : undefined
})

function onTrueBranchChange(val: number | undefined) {
  emit('update', { true_branch: val ? [val] : [] })
}

function onFalseBranchChange(val: number | undefined) {
  emit('update', { false_branch: val ? [val] : [] })
}
</script>

<style scoped>
.condition-form {
  width: 100%;
}

.branch-config {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
</style>

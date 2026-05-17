<template>
  <div class="data-assign-form">
    <a-form-item label="变量名" label-col-flex="80px">
      <a-input
        :model-value="node.assign_variable"
        placeholder="如: user_id, token, order_no"
        @update:model-value="$emit('update', { assign_variable: $event })"
      />
    </a-form-item>

    <a-form-item label="赋值方式" label-col-flex="80px">
      <a-radio-group
        :model-value="node.assign_source || 'static'"
        @update:model-value="$emit('update', { assign_source: $event })"
      >
        <a-radio value="static">静态值</a-radio>
        <a-radio value="expression">表达式</a-radio>
      </a-radio-group>
    </a-form-item>

    <a-form-item label="变量值" label-col-flex="80px">
      <a-input
        v-if="(node.assign_source || 'static') === 'static'"
        :model-value="node.assign_value"
        placeholder="输入固定值"
        @update:model-value="$emit('update', { assign_value: $event })"
      />
      <a-textarea
        v-else
        :model-value="node.assign_value"
        placeholder="支持 {{变量名}} 模板语法"
        :auto-size="{ minRows: 2, maxRows: 4 }"
        @update:model-value="$emit('update', { assign_value: $event })"
      />
    </a-form-item>

    <div v-if="(node.assign_source || 'static') === 'expression'" class="expression-hint">
      <icon-info-circle />
      <span>使用 <code v-text="'{{变量名}}'"></code> 引用其他变量，系统会自动替换为实际值</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { SceneNodeItem } from '@/api/sceneNode'

defineProps<{
  node: SceneNodeItem
}>()

defineEmits<{
  (e: 'update', data: Partial<SceneNodeItem>): void
}>()
</script>

<style scoped>
.data-assign-form {
  width: 100%;
}

.expression-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  padding: 8px 12px;
  background: var(--color-fill-1);
  border-radius: var(--radius-small);
  font-size: 12px;
  color: var(--color-text-3);
}

.expression-hint code {
  background: var(--color-fill-3);
  padding: 1px 6px;
  border-radius: 3px;
  font-family: monospace;
  font-size: 11px;
}
</style>

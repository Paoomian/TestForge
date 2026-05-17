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

    <a-divider style="margin: 12px 0;">分支说明</a-divider>

    <div class="branch-info">
      <div class="branch-item branch-true">
        <div class="branch-icon">
          <icon-check-circle />
        </div>
        <div class="branch-content">
          <div class="branch-label">条件为真时</div>
          <div class="branch-desc">执行"真"分支中的节点（暂不支持可视化配置分支，执行时按顺序执行后续节点）</div>
        </div>
      </div>
      <div class="branch-item branch-false">
        <div class="branch-icon">
          <icon-close-circle />
        </div>
        <div class="branch-content">
          <div class="branch-label">条件为假时</div>
          <div class="branch-desc">跳过后续节点或执行"假"分支（暂不支持可视化配置分支）</div>
        </div>
      </div>
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
.condition-form {
  width: 100%;
}

.branch-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.branch-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 12px;
  border-radius: var(--radius-small);
  background: var(--color-fill-1);
}

.branch-true .branch-icon {
  color: #00b42a;
}

.branch-false .branch-icon {
  color: #f53f3f;
}

.branch-icon {
  font-size: 16px;
  margin-top: 2px;
}

.branch-content {
  flex: 1;
}

.branch-label {
  font-weight: 500;
  font-size: 13px;
  margin-bottom: 4px;
}

.branch-desc {
  font-size: 12px;
  color: var(--color-text-3);
}
</style>

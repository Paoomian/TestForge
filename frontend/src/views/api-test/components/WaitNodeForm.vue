<template>
  <div class="wait-form">
    <a-form-item label="等待时间" label-col-flex="80px">
      <a-input-number
        :model-value="node.wait_seconds || 1"
        :min="1"
        :max="300"
        :step="1"
        @update:model-value="$emit('update', { wait_seconds: $event })"
      >
        <template #suffix>秒</template>
      </a-input-number>
    </a-form-item>

    <div class="wait-presets">
      <span class="preset-label">快捷选择：</span>
      <a-space>
        <a-button size="mini" @click="$emit('update', { wait_seconds: 1 })">1秒</a-button>
        <a-button size="mini" @click="$emit('update', { wait_seconds: 3 })">3秒</a-button>
        <a-button size="mini" @click="$emit('update', { wait_seconds: 5 })">5秒</a-button>
        <a-button size="mini" @click="$emit('update', { wait_seconds: 10 })">10秒</a-button>
        <a-button size="mini" @click="$emit('update', { wait_seconds: 30 })">30秒</a-button>
      </a-space>
    </div>

    <div class="wait-hint">
      <icon-info-circle />
      <span>等待节点会暂停执行，适用于需要等待异步操作完成的场景</span>
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
.wait-form {
  width: 100%;
}

.wait-presets {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}

.preset-label {
  font-size: 13px;
  color: var(--color-text-3);
}

.wait-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  padding: 8px 12px;
  background: var(--color-fill-1);
  border-radius: var(--radius-small);
  font-size: 12px;
  color: var(--color-text-3);
}
</style>

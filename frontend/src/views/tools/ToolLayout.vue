<template>
  <div class="tool-layout">
    <div class="tool-header">
      <div class="tool-header-left">
        <h3 class="tool-title">{{ title }}</h3>
        <p v-if="description" class="tool-desc">{{ description }}</p>
      </div>
      <div class="tool-actions">
        <slot name="actions" />
      </div>
    </div>
    <div class="tool-body">
      <div class="tool-input">
        <slot name="input" />
      </div>
      <div class="tool-output">
        <slot name="output" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  description?: string
}>()
</script>

<style scoped>
.tool-layout {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 16px;
}

.tool-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.tool-header-left {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.tool-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-1);
  margin: 0;
}

.tool-desc {
  font-size: 13px;
  color: var(--color-text-3);
  margin: 0;
}

.tool-body {
  flex: 1;
  display: flex;
  gap: 16px;
  min-height: 0;
}

.tool-input,
.tool-output {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.tool-actions {
  flex-shrink: 0;
  display: flex;
  gap: 8px;
}

@media (max-width: 768px) {
  .tool-body {
    flex-direction: column;
  }

  .tool-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .tool-header-left {
    flex-direction: column;
    gap: 4px;
  }
}
</style>

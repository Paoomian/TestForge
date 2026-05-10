<template>
  <div class="batch-run-progress">
    <!-- 进度条 -->
    <div class="progress-bar-wrapper">
      <a-progress
        :percent="progress / 100"
        :status="progressStatus"
        :stroke-width="12"
        :show-text="false"
      />
      <span class="progress-text">{{ progress.toFixed(1) }}%</span>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-item">
        <span class="stat-value">{{ total }}</span>
        <span class="stat-label">总数</span>
      </div>
      <div class="stat-item stat-pass">
        <span class="stat-value">{{ passCount }}</span>
        <span class="stat-label">通过</span>
      </div>
      <div class="stat-item stat-fail">
        <span class="stat-value">{{ failCount }}</span>
        <span class="stat-label">失败</span>
      </div>
      <div class="stat-item stat-error">
        <span class="stat-value">{{ errorCount }}</span>
        <span class="stat-label">错误</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  total: number
  passCount: number
  failCount: number
  errorCount: number
  status: string
}

const props = defineProps<Props>()

const progress = computed(() => {
  if (props.total === 0) return 0
  const completed = props.passCount + props.failCount + props.errorCount
  return (completed / props.total) * 100
})

const progressStatus = computed(() => {
  if (props.status === 'error') return 'danger'
  if (props.status === 'cancelled') return 'warning'
  if (props.status === 'done') {
    return props.failCount > 0 || props.errorCount > 0 ? 'warning' : 'success'
  }
  return 'normal'
})
</script>

<style scoped>
.batch-run-progress {
  padding: 20px;
  background: var(--color-bg-2);
  border-radius: var(--radius-medium);
  border: 1px solid var(--color-border-2);
}

.progress-bar-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.progress-bar-wrapper :deep(.arco-progress) {
  flex: 1;
}

.progress-text {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-1);
  min-width: 60px;
  text-align: right;
}

.stats-row {
  display: flex;
  gap: 16px;
}

.stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px;
  background: var(--color-fill-1);
  border-radius: var(--radius-small);
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text-1);
}

.stat-label {
  font-size: 12px;
  color: var(--color-text-3);
  margin-top: 4px;
}

.stat-pass .stat-value {
  color: #00b42a;
}

.stat-fail .stat-value {
  color: #f53f3f;
}

.stat-error .stat-value {
  color: #ff7d00;
}
</style>

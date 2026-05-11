<template>
  <div class="test-summary-card">
    <!-- 核心指标 -->
    <div class="metrics-grid">
      <div class="metric-item highlight">
        <div class="metric-label">通过率</div>
        <div class="metric-value" :class="passRateClass">
          {{ summary.pass_rate }}%
        </div>
      </div>
      <div class="metric-item">
        <div class="metric-label">总用例数</div>
        <div class="metric-value">{{ summary.total_count }}</div>
      </div>
      <div class="metric-item pass">
        <div class="metric-label">通过</div>
        <div class="metric-value">{{ summary.pass_count }}</div>
      </div>
      <div class="metric-item fail">
        <div class="metric-label">失败</div>
        <div class="metric-value">{{ summary.fail_count }}</div>
      </div>
      <div class="metric-item error">
        <div class="metric-label">错误</div>
        <div class="metric-value">{{ summary.error_count }}</div>
      </div>
      <div class="metric-item skipped" v-if="summary.skipped_count > 0">
        <div class="metric-label">跳过</div>
        <div class="metric-value">{{ summary.skipped_count }}</div>
      </div>
    </div>

    <!-- 时间信息 -->
    <a-divider style="margin: 16px 0" />
    <div class="time-info">
      <div class="time-item">
        <icon-clock-circle />
        <span class="time-label">开始时间</span>
        <span class="time-value">{{ formatTime(summary.start_time) }}</span>
      </div>
      <div class="time-item">
        <icon-clock-circle />
        <span class="time-label">结束时间</span>
        <span class="time-value">{{ formatTime(summary.end_time) }}</span>
      </div>
      <div class="time-item">
        <icon-history />
        <span class="time-label">耗时</span>
        <span class="time-value">{{ formatDuration(summary.duration_ms) }}</span>
      </div>
      <div class="time-item" v-if="summary.creator_name">
        <icon-user />
        <span class="time-label">执行人</span>
        <span class="time-value">{{ summary.creator_name }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { TestSummary } from '@/api/batchRun'

const props = defineProps<{
  summary: TestSummary
}>()

const passRateClass = computed(() => {
  const rate = props.summary.pass_rate
  if (rate >= 95) return 'rate-high'
  if (rate >= 80) return 'rate-medium'
  return 'rate-low'
})

const formatTime = (time?: string) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const formatDuration = (ms?: number) => {
  if (!ms) return '-'
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  const min = Math.floor(ms / 60000)
  const sec = ((ms % 60000) / 1000).toFixed(0)
  return `${min}m ${sec}s`
}
</script>

<style scoped>
.test-summary-card {
  padding: 8px 0;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: 16px;
  text-align: center;
}

.metric-item {
  padding: 12px;
  border-radius: 8px;
  background: var(--color-fill-1);
}

.metric-item.highlight {
  background: linear-gradient(135deg, var(--color-primary-light-1), var(--color-primary-light-2));
}

.metric-label {
  font-size: 12px;
  color: var(--color-text-3);
  margin-bottom: 4px;
}

.metric-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text-1);
}

.metric-item.pass .metric-value {
  color: var(--color-success-6);
}

.metric-item.fail .metric-value {
  color: var(--color-danger-6);
}

.metric-item.error .metric-value {
  color: var(--color-warning-6);
}

.metric-item.skipped .metric-value {
  color: var(--color-text-3);
}

.rate-high {
  color: var(--color-success-6) !important;
}

.rate-medium {
  color: var(--color-warning-6) !important;
}

.rate-low {
  color: var(--color-danger-6) !important;
}

.time-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.time-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.time-item svg {
  color: var(--color-text-3);
  flex-shrink: 0;
}

.time-label {
  color: var(--color-text-3);
  min-width: 60px;
}

.time-value {
  color: var(--color-text-1);
  font-weight: 500;
}
</style>

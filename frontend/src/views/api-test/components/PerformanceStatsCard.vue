<template>
  <div class="performance-stats-card">
    <!-- 性能指标概览 -->
    <div class="stats-overview">
      <div class="stat-item">
        <div class="stat-label">平均响应</div>
        <div class="stat-value primary">{{ performance.avg_response_ms }}ms</div>
      </div>
      <div class="stat-item">
        <div class="stat-label">最快</div>
        <div class="stat-value success">{{ performance.min_response_ms }}ms</div>
      </div>
      <div class="stat-item">
        <div class="stat-label">最慢</div>
        <div class="stat-value danger">{{ performance.max_response_ms }}ms</div>
      </div>
      <div class="stat-item">
        <div class="stat-label">P50</div>
        <div class="stat-value">{{ performance.p50_response_ms }}ms</div>
      </div>
      <div class="stat-item">
        <div class="stat-label">P90</div>
        <div class="stat-value warning">{{ performance.p90_response_ms }}ms</div>
      </div>
      <div class="stat-item">
        <div class="stat-label">P95</div>
        <div class="stat-value warning">{{ performance.p95_response_ms }}ms</div>
      </div>
    </div>

    <div class="request-count">
      有效请求总数: <strong>{{ performance.total_requests }}</strong>
    </div>

    <!-- Top5 图表 -->
    <a-row :gutter="16" style="margin-top: 16px">
      <a-col :span="12">
        <div class="chart-title">
          <icon-arrow-rise style="color: var(--color-danger-6)" />
          最慢接口 Top5
        </div>
        <div ref="slowestChartRef" class="chart-container"></div>
      </a-col>
      <a-col :span="12">
        <div class="chart-title">
          <icon-arrow-fall style="color: var(--color-success-6)" />
          最快接口 Top5
        </div>
        <div ref="fastestChartRef" class="chart-container"></div>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import type { PerformanceStats } from '@/api/batchRun'

const props = defineProps<{
  performance: PerformanceStats
}>()

const slowestChartRef = ref<HTMLElement>()
const fastestChartRef = ref<HTMLElement>()
let slowestChart: echarts.ECharts | null = null
let fastestChart: echarts.ECharts | null = null

const initCharts = () => {
  // 最慢 Top5
  if (slowestChartRef.value && props.performance.slowest_top5.length > 0) {
    slowestChart = echarts.init(slowestChartRef.value)
    const slowestData = props.performance.slowest_top5.map(item => ({
      name: item.case_name || `用例#${item.case_id}`,
      value: item.api_duration_ms
    }))

    slowestChart.setOption({
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: '{b}: {c}ms'
      },
      grid: {
        left: '20%',
        right: '15%',
        top: '5%',
        bottom: '15%'
      },
      xAxis: {
        type: 'value',
        axisLabel: {
          formatter: '{value}ms',
          fontSize: 11
        }
      },
      yAxis: {
        type: 'category',
        data: slowestData.map(d => d.name).reverse(),
        axisLabel: {
          width: 120,
          overflow: 'truncate',
          ellipsis: '...'
        }
      },
      series: [{
        type: 'bar',
        data: slowestData.map(d => d.value).reverse(),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#ff7875' },
            { offset: 1, color: '#ff4d4f' }
          ])
        },
        barWidth: '40%',
        label: {
          show: true,
          position: 'right',
          formatter: '{c}ms'
        }
      }]
    })
  }

  // 最快 Top5
  if (fastestChartRef.value && props.performance.fastest_top5.length > 0) {
    fastestChart = echarts.init(fastestChartRef.value)
    const fastestData = props.performance.fastest_top5.map(item => ({
      name: item.case_name || `用例#${item.case_id}`,
      value: item.api_duration_ms
    }))

    fastestChart.setOption({
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: '{b}: {c}ms'
      },
      grid: {
        left: '20%',
        right: '15%',
        top: '5%',
        bottom: '15%'
      },
      xAxis: {
        type: 'value',
        axisLabel: {
          formatter: '{value}ms',
          fontSize: 11
        }
      },
      yAxis: {
        type: 'category',
        data: fastestData.map(d => d.name).reverse(),
        axisLabel: {
          width: 120,
          overflow: 'truncate',
          ellipsis: '...'
        }
      },
      series: [{
        type: 'bar',
        data: fastestData.map(d => d.value).reverse(),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#95de64' },
            { offset: 1, color: '#52c41a' }
          ])
        },
        barWidth: '40%',
        label: {
          show: true,
          position: 'right',
          formatter: '{c}ms'
        }
      }]
    })
  }
}

const handleResize = () => {
  slowestChart?.resize()
  fastestChart?.resize()
}

onMounted(() => {
  initCharts()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  slowestChart?.dispose()
  fastestChart?.dispose()
})

watch(() => props.performance, () => {
  slowestChart?.dispose()
  fastestChart?.dispose()
  initCharts()
}, { deep: true })
</script>

<style scoped>
.performance-stats-card {
  padding: 8px 0;
}

.stats-overview {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
  margin-bottom: 12px;
}

.stat-item {
  text-align: center;
  padding: 12px 8px;
  background: var(--color-fill-1);
  border-radius: 8px;
}

.stat-label {
  font-size: 12px;
  color: var(--color-text-3);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-1);
}

.stat-value.primary {
  color: var(--color-primary-6);
}

.stat-value.success {
  color: var(--color-success-6);
}

.stat-value.danger {
  color: var(--color-danger-6);
}

.stat-value.warning {
  color: var(--color-warning-6);
}

.request-count {
  text-align: center;
  font-size: 13px;
  color: var(--color-text-3);
}

.chart-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
  color: var(--color-text-1);
}

.chart-container {
  height: 200px;
  width: 100%;
}

@media (max-width: 1200px) {
  .stats-overview {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>

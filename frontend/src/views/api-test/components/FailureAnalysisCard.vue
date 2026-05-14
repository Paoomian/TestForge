<template>
  <div class="failure-analysis-card">
    <!-- 无失败时显示成功提示 -->
    <a-empty v-if="failureAnalysis.total_fail_count === 0" description="全部通过，无失败用例">
      <template #image>
        <icon-check-circle-fill style="font-size: 48px; color: var(--color-success-6)" />
      </template>
    </a-empty>

    <template v-else>
      <div class="analysis-content">
        <!-- 饼图 -->
        <div class="chart-section">
          <div ref="pieChartRef" class="pie-chart"></div>
          <div class="total-fail">
            失败/错误总数: <strong>{{ failureAnalysis.total_fail_count }}</strong>
          </div>
        </div>

        <!-- 分类列表 -->
        <div class="categories-section">
          <a-collapse :default-active-key="defaultActiveKeys">
            <a-collapse-item
              v-for="category in failureAnalysis.categories"
              :key="category.category"
            >
              <template #header>
                <div class="category-header">
                  <span class="category-name">{{ category.category }}</span>
                  <a-tag :color="getCategoryColor(category.category)" size="small">
                    {{ category.count }} 个 ({{ category.percentage }}%)
                  </a-tag>
                </div>
              </template>
              <div class="category-cases">
                <div
                  v-for="caseItem in category.cases"
                  :key="caseItem.case_id"
                  class="case-item"
                >
                  <div class="case-header">
                    <div class="case-name">
                      {{ caseItem.case_name || `用例#${caseItem.case_id}` }}
                    </div>
                    <a-button type="text" size="mini" @click="$emit('viewDetail', caseItem.detail_id)">
                      详情
                    </a-button>
                  </div>
                  <!-- 断言失败详情 -->
                  <div v-if="caseItem.assertions && caseItem.assertions.length > 0" class="assertion-details">
                    <div
                      v-for="(assertion, idx) in caseItem.assertions"
                      :key="idx"
                      class="assertion-row"
                    >
                      <span class="assertion-type">{{ getAssertionTypeLabel(assertion.assertion_type) }}</span>
                      <span v-if="assertion.field" class="assertion-field">{{ assertion.field }}</span>
                      <span class="assertion-operator">{{ getOperatorLabel(assertion.operator) }}</span>
                      <span class="assertion-expected">期望: {{ assertion.expected }}</span>
                      <span class="assertion-actual">实际: {{ assertion.actual }}</span>
                    </div>
                  </div>
                  <!-- 其他错误信息 -->
                  <div class="case-error" v-else-if="caseItem.error_message">
                    {{ caseItem.error_message }}
                  </div>
                </div>
              </div>
            </a-collapse-item>
          </a-collapse>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import * as echarts from 'echarts'
import type { FailureAnalysis } from '@/api/batchRun'

const props = defineProps<{
  failureAnalysis: FailureAnalysis
}>()

const emit = defineEmits<{
  viewDetail: [detailId: number]
}>()

const pieChartRef = ref<HTMLElement>()
let pieChart: echarts.ECharts | null = null

const defaultActiveKeys = computed(() => {
  return props.failureAnalysis.categories.map(c => c.category)
})

const getCategoryColor = (category: string) => {
  if (category.includes('断言失败')) return 'red'
  if (category.includes('请求超时')) return 'orange'
  if (category.includes('连接失败')) return 'gold'
  return 'gray'
}

const getAssertionTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    status_code: '状态码',
    jsonpath: 'JSONPath',
    response_time: '响应时间',
    header: '响应头',
    body_contains: 'Body包含'
  }
  return labels[type] || type
}

const getOperatorLabel = (operator: string) => {
  const labels: Record<string, string> = {
    equals: '等于',
    not_equals: '不等于',
    contains: '包含',
    greater_than: '大于',
    less_than: '小于',
    regex: '正则匹配',
    exists: '存在'
  }
  return labels[operator] || operator
}

const initChart = () => {
  if (!pieChartRef.value || props.failureAnalysis.categories.length === 0) return

  pieChart = echarts.init(pieChartRef.value)
  const data = props.failureAnalysis.categories.map(c => ({
    name: c.category,
    value: c.count
  }))

  pieChart.setOption({
    tooltip: {
      trigger: 'item',
      confine: true,
      formatter: (params: any) => {
        return `${params.name}: ${params.value} 个 (${params.percent}%)`
      }
    },
    legend: {
      show: false
    },
    series: [{
      type: 'pie',
      radius: ['45%', '75%'],
      center: ['50%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 6,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: false
      },
      labelLine: {
        show: false
      },
      emphasis: {
        scaleSize: 8
      },
      data,
      color: ['#f5222d', '#fa8c16', '#faad14', '#8c8c8c', '#597ef7']
    }]
  })
}

const handleResize = () => {
  pieChart?.resize()
}

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  pieChart?.dispose()
})

watch(() => props.failureAnalysis, () => {
  pieChart?.dispose()
  initChart()
}, { deep: true })
</script>

<style scoped>
.failure-analysis-card {
  padding: 8px 0;
}

.analysis-content {
  display: flex;
  gap: 24px;
}

.chart-section {
  flex-shrink: 0;
  width: 300px;
  text-align: center;
}

.pie-chart {
  height: 220px;
  width: 100%;
}

.total-fail {
  font-size: 13px;
  color: var(--color-text-3);
  margin-top: 8px;
}

.categories-section {
  flex: 1;
  min-width: 0;
}

.category-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 12px;
}

.category-name {
  font-weight: 500;
}

.category-cases {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.case-item {
  padding: 8px 12px;
  background: var(--color-fill-1);
  border-radius: 6px;
  border-left: 3px solid var(--color-danger-6);
}

.case-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.case-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-1);
}

.case-error {
  font-size: 12px;
  color: var(--color-text-3);
  word-break: break-all;
}

.assertion-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 6px;
}

.assertion-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  padding: 4px 8px;
  background: var(--color-danger-light-1);
  border-radius: 4px;
}

.assertion-type {
  font-weight: 600;
  color: var(--color-danger-6);
  min-width: 60px;
  margin-right: 8px;
}

.assertion-field {
  color: var(--color-text-2);
  font-family: monospace;
}

.assertion-operator {
  color: var(--color-text-3);
}

.assertion-expected {
  color: var(--color-success-6);
}

.assertion-actual {
  color: var(--color-danger-6);
  font-weight: 500;
}

@media (max-width: 900px) {
  .analysis-content {
    flex-direction: column;
  }

  .chart-section {
    width: 100%;
  }
}
</style>

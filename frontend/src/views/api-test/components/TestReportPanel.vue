<template>
  <div class="test-report-panel">
    <a-spin :loading="loading" style="width: 100%">
      <template v-if="reportData">
        <a-tabs default-active-key="summary" type="rounded">
          <a-tab-pane key="summary" title="测试摘要">
            <TestSummaryCard :summary="reportData.summary" />
          </a-tab-pane>
          <a-tab-pane key="performance" title="性能统计">
            <PerformanceStatsCard :performance="reportData.performance" />
          </a-tab-pane>
          <a-tab-pane key="failure" title="失败分析">
            <FailureAnalysisCard
              :failure-analysis="reportData.failure_analysis"
              @view-detail="$emit('viewDetail', $event)"
            />
          </a-tab-pane>
        </a-tabs>
      </template>
      <template v-else-if="!loading">
        <a-empty description="暂无报告数据" />
      </template>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { Message } from '@arco-design/web-vue'
import { getBatchRunReport } from '@/api/batchRun'
import type { BatchRunReport } from '@/api/batchRun'
import TestSummaryCard from './TestSummaryCard.vue'
import PerformanceStatsCard from './PerformanceStatsCard.vue'
import FailureAnalysisCard from './FailureAnalysisCard.vue'

const props = defineProps<{
  runId: number
  status: string
}>()

const emit = defineEmits<{
  viewDetail: [detailId: number]
}>()

const loading = ref(false)
const reportData = ref<BatchRunReport | null>(null)

const loadReport = async () => {
  // 只有任务完成时才加载报告
  if (['pending', 'running'].includes(props.status)) {
    return
  }

  loading.value = true
  try {
    reportData.value = await getBatchRunReport(props.runId)
  } catch (e) {
    Message.error('加载测试报告失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadReport()
})

// 状态变化时重新加载
watch(() => props.status, (newStatus) => {
  if (!['pending', 'running'].includes(newStatus)) {
    loadReport()
  }
})
</script>

<style scoped>
.test-report-panel {
  min-height: 200px;
}
</style>

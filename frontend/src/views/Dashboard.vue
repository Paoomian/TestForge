<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <a-row :gutter="20">
      <a-col :span="6">
        <div class="stat-card stat-card-purple" @click="$router.push({ name: 'project-list' })">
          <div class="stat-icon-wrapper">
            <icon-folder class="stat-icon" />
          </div>
          <div class="stat-content">
            <div class="stat-label">项目总数</div>
            <div class="stat-value">{{ stats.project_count }}</div>
          </div>
        </div>
      </a-col>
      <a-col :span="6">
        <div class="stat-card stat-card-indigo" @click="$router.push({ name: 'ui-case-list' })">
          <div class="stat-icon-wrapper">
            <icon-desktop class="stat-icon" />
          </div>
          <div class="stat-content">
            <div class="stat-label">UI 用例</div>
            <div class="stat-value">{{ stats.ui_case_count }}</div>
          </div>
        </div>
      </a-col>
      <a-col :span="6">
        <div class="stat-card stat-card-blue" @click="$router.push({ name: 'api-test-manage' })">
          <div class="stat-icon-wrapper">
            <icon-code class="stat-icon" />
          </div>
          <div class="stat-content">
            <div class="stat-label">接口用例</div>
            <div class="stat-value">{{ stats.api_case_count }}</div>
          </div>
        </div>
      </a-col>
      <a-col :span="6">
        <div class="stat-card stat-card-cyan" @click="$router.push({ name: 'report-list' })">
          <div class="stat-icon-wrapper">
            <icon-play-arrow class="stat-icon" />
          </div>
          <div class="stat-content">
            <div class="stat-label">今日执行</div>
            <div class="stat-value">{{ stats.today_run_count }}</div>
          </div>
        </div>
      </a-col>
    </a-row>

    <!-- 图表区域 -->
    <a-row :gutter="20" style="margin-top: 20px">
      <!-- 执行趋势 -->
      <a-col :span="16">
        <a-card class="chart-card" :bordered="false">
          <template #title>
            <div class="card-title-wrapper">
              <span class="card-title">执行趋势</span>
              <a-space>
                <a-button :type="trendDays === 7 ? 'primary' : 'outline'" size="mini" @click="trendDays = 7; loadTrendData()">近7天</a-button>
                <a-button :type="trendDays === 14 ? 'primary' : 'outline'" size="mini" @click="trendDays = 14; loadTrendData()">近14天</a-button>
                <a-button :type="trendDays === 30 ? 'primary' : 'outline'" size="mini" @click="trendDays = 30; loadTrendData()">近30天</a-button>
              </a-space>
            </div>
          </template>
          <div ref="trendChartRef" class="chart-container"></div>
        </a-card>
      </a-col>

      <!-- 测试通过率 -->
      <a-col :span="8">
        <a-card class="chart-card" :bordered="false">
          <template #title>
            <span class="card-title">测试通过率</span>
          </template>
          <div ref="passRateChartRef" class="chart-container"></div>
          <div class="pass-rate-info">
            <div class="pass-rate-value">{{ passRate.pass_rate }}%</div>
            <div class="pass-rate-label">通过率</div>
          </div>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="20" style="margin-top: 20px">
      <!-- 最近执行记录 -->
      <a-col :span="16">
        <a-card class="table-card" :bordered="false">
          <template #title>
            <div class="card-title-wrapper">
              <span class="card-title">最近执行记录</span>
              <a-button type="text" size="small" @click="$router.push({ name: 'report-list' })">
                查看全部 <icon-right />
              </a-button>
            </div>
          </template>
          <a-table :data="recentRuns" :pagination="false" :bordered="false" size="small">
            <template #columns>
              <a-table-column title="名称" data-index="name" :width="180" />
              <a-table-column title="状态" :width="80">
                <template #cell="{ record }">
                  <a-tag :color="getStatusColor(record.status)" size="small">
                    {{ getStatusLabel(record.status) }}
                  </a-tag>
                </template>
              </a-table-column>
              <a-table-column title="通过" :width="60">
                <template #cell="{ record }">
                  <span class="text-success">{{ record.pass_count }}</span>
                </template>
              </a-table-column>
              <a-table-column title="失败" :width="60">
                <template #cell="{ record }">
                  <span class="text-danger">{{ record.fail_count }}</span>
                </template>
              </a-table-column>
              <a-table-column title="耗时" :width="80">
                <template #cell="{ record }">
                  {{ record.duration ? `${(record.duration / 1000).toFixed(1)}s` : '-' }}
                </template>
              </a-table-column>
              <a-table-column title="时间" data-index="created_at" />
            </template>
          </a-table>
        </a-card>
      </a-col>

      <!-- 用例分布 -->
      <a-col :span="8">
        <a-card class="chart-card" :bordered="false">
          <template #title>
            <span class="card-title">用例分布</span>
          </template>
          <div ref="distributionChartRef" class="chart-container"></div>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { IconRight } from '@arco-design/web-vue/es/icon'
import * as echarts from 'echarts'
import {
  getDashboardStats,
  getRecentRuns,
  getRunTrend,
  getPassRate,
  getCaseDistribution,
} from '@/api/dashboard'
import type { DashboardStats, RecentRun, TrendItem, PassRate, CaseDistribution } from '@/api/dashboard'

// 统计数据
const stats = reactive<DashboardStats>({
  project_count: 0,
  ui_case_count: 0,
  api_case_count: 0,
  today_run_count: 0,
  total_run_count: 0,
  last_run: null,
})

// 最近执行记录
const recentRuns = ref<RecentRun[]>([])

// 执行趋势
const trendDays = ref(7)
const trendData = ref<TrendItem[]>([])

// 通过率
const passRate = reactive<PassRate>({
  total: 0,
  pass: 0,
  fail: 0,
  error: 0,
  pass_rate: 0,
})

// 用例分布
const distributionData = ref<CaseDistribution[]>([])

// 图表引用
const trendChartRef = ref<HTMLElement>()
const passRateChartRef = ref<HTMLElement>()
const distributionChartRef = ref<HTMLElement>()

// 图表实例
let trendChart: echarts.ECharts | null = null
let passRateChart: echarts.ECharts | null = null
let distributionChart: echarts.ECharts | null = null

// 加载统计数据
async function loadStats() {
  try {
    const data = await getDashboardStats()
    Object.assign(stats, data)
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

// 加载最近执行记录
async function loadRecentRuns() {
  try {
    recentRuns.value = await getRecentRuns(8)
  } catch (error) {
    console.error('加载最近执行记录失败:', error)
  }
}

// 加载执行趋势
async function loadTrendData() {
  try {
    trendData.value = await getRunTrend(trendDays.value)
    renderTrendChart()
  } catch (error) {
    console.error('加载执行趋势失败:', error)
  }
}

// 加载通过率
async function loadPassRate() {
  try {
    const data = await getPassRate()
    Object.assign(passRate, data)
    renderPassRateChart()
  } catch (error) {
    console.error('加载通过率失败:', error)
  }
}

// 加载用例分布
async function loadDistribution() {
  try {
    distributionData.value = await getCaseDistribution()
    renderDistributionChart()
  } catch (error) {
    console.error('加载用例分布失败:', error)
  }
}

// 渲染执行趋势图表
function renderTrendChart() {
  if (!trendChartRef.value) return

  if (!trendChart) {
    trendChart = echarts.init(trendChartRef.value)
  }

  const dates = trendData.value.map(item => item.date)
  const passData = trendData.value.map(item => item.pass)
  const failData = trendData.value.map(item => item.fail)
  const errorData = trendData.value.map(item => item.error)

  trendChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow',
      },
    },
    legend: {
      data: ['通过', '失败', '错误'],
      right: 0,
      top: 0,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '40px',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: {
        lineStyle: { color: '#e5e6eb' },
      },
      axisLabel: {
        color: '#86909c',
      },
    },
    yAxis: {
      type: 'value',
      axisLine: {
        show: false,
      },
      axisTick: {
        show: false,
      },
      axisLabel: {
        color: '#86909c',
      },
      splitLine: {
        lineStyle: { color: '#f2f3f5' },
      },
    },
    series: [
      {
        name: '通过',
        type: 'bar',
        stack: 'total',
        data: passData,
        itemStyle: {
          color: '#00b42a',
          borderRadius: [0, 0, 0, 0],
        },
      },
      {
        name: '失败',
        type: 'bar',
        stack: 'total',
        data: failData,
        itemStyle: {
          color: '#f53f3f',
        },
      },
      {
        name: '错误',
        type: 'bar',
        stack: 'total',
        data: errorData,
        itemStyle: {
          color: '#ff7d00',
          borderRadius: [4, 4, 0, 0],
        },
      },
    ],
  })
}

// 渲染通过率图表
function renderPassRateChart() {
  if (!passRateChartRef.value) return

  if (!passRateChart) {
    passRateChart = echarts.init(passRateChartRef.value)
  }

  passRateChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      orient: 'vertical',
      right: '10%',
      top: 'center',
      itemWidth: 10,
      itemHeight: 10,
      textStyle: {
        fontSize: 12,
      },
    },
    series: [
      {
        type: 'pie',
        radius: ['50%', '70%'],
        center: ['40%', '50%'],
        avoidLabelOverlap: false,
        label: {
          show: false,
        },
        emphasis: {
          label: {
            show: false,
          },
        },
        labelLine: {
          show: false,
        },
        data: [
          {
            value: passRate.pass,
            name: '通过',
            itemStyle: { color: '#00b42a' },
          },
          {
            value: passRate.fail,
            name: '失败',
            itemStyle: { color: '#f53f3f' },
          },
          {
            value: passRate.error,
            name: '错误',
            itemStyle: { color: '#ff7d00' },
          },
        ],
      },
    ],
  })
}

// 渲染用例分布图表
function renderDistributionChart() {
  if (!distributionChartRef.value) return

  if (!distributionChart) {
    distributionChart = echarts.init(distributionChartRef.value)
  }

  distributionChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      orient: 'vertical',
      right: '10%',
      top: 'center',
      itemWidth: 10,
      itemHeight: 10,
      textStyle: {
        fontSize: 12,
      },
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '65%'],
        center: ['40%', '50%'],
        avoidLabelOverlap: false,
        label: {
          show: false,
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold',
          },
        },
        labelLine: {
          show: false,
        },
        data: distributionData.value.map((item, index) => ({
          ...item,
          itemStyle: {
            color: index === 0 ? '#6366f1' : '#3b82f6',
          },
        })),
      },
    ],
  })
}

// 获取状态颜色
function getStatusColor(status: string) {
  const map: Record<string, string> = {
    done: 'green',
    completed: 'green',
    running: 'blue',
    failed: 'red',
    error: 'orange',
    pending: 'gray',
    cancelled: 'gray',
  }
  return map[status] || 'gray'
}

// 获取状态标签
function getStatusLabel(status: string) {
  const map: Record<string, string> = {
    done: '完成',
    completed: '完成',
    running: '运行中',
    failed: '失败',
    error: '错误',
    pending: '待执行',
    cancelled: '已取消',
  }
  return map[status] || status
}

// 窗口大小变化时重新渲染图表
function handleResize() {
  trendChart?.resize()
  passRateChart?.resize()
  distributionChart?.resize()
}

onMounted(async () => {
  // 并行加载数据
  await Promise.all([
    loadStats(),
    loadRecentRuns(),
    loadTrendData(),
    loadPassRate(),
    loadDistribution(),
  ])

  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  // 销毁图表实例
  trendChart?.dispose()
  passRateChart?.dispose()
  distributionChart?.dispose()

  // 移除事件监听
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.dashboard {
  width: 100%;
}

/* ---- 统计卡片 ---- */
.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  background: white;
  border-radius: var(--radius-lg);
  border: 1px solid rgba(224, 212, 252, 0.25);
  box-shadow: var(--shadow-card);
  transition: all var(--transition-slow);
  cursor: pointer;
}

.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-card-hover);
  border-color: rgba(167, 139, 250, 0.25);
}

.stat-icon-wrapper {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-lg);
  flex-shrink: 0;
}

.stat-card-purple .stat-icon-wrapper {
  background: linear-gradient(135deg, #ede9fe, #ddd6fe);
  color: #7c3aed;
}

.stat-card-indigo .stat-icon-wrapper {
  background: linear-gradient(135deg, #e0e7ff, #c7d2fe);
  color: #6366f1;
}

.stat-card-blue .stat-icon-wrapper {
  background: linear-gradient(135deg, #dbeafe, #bfdbfe);
  color: #3b82f6;
}

.stat-card-cyan .stat-icon-wrapper {
  background: linear-gradient(135deg, #cffafe, #a5f3fc);
  color: #0891b2;
}

.stat-icon {
  font-size: 22px;
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--gray-500);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 28px;
  font-weight: var(--font-weight-bold);
  color: var(--gray-800);
  line-height: 1.2;
}

/* ---- 图表卡片 ---- */
.chart-card {
  height: 100%;
}

.chart-card :deep(.arco-card-body) {
  padding: 16px 20px 20px;
}

.card-title-wrapper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.card-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--gray-800);
}

.chart-container {
  width: 100%;
  height: 280px;
}

/* ---- 通过率信息 ---- */
.pass-rate-info {
  text-align: center;
  margin-top: -20px;
  position: relative;
  z-index: 1;
}

.pass-rate-value {
  font-size: 32px;
  font-weight: var(--font-weight-bold);
  color: #00b42a;
}

.pass-rate-label {
  font-size: var(--font-size-sm);
  color: var(--gray-500);
  margin-top: 4px;
}

/* ---- 表格卡片 ---- */
.table-card {
  height: 100%;
}

.table-card :deep(.arco-card-body) {
  padding: 0 20px 20px;
}

.text-success {
  color: #00b42a;
  font-weight: 500;
}

.text-danger {
  color: #f53f3f;
  font-weight: 500;
}
</style>

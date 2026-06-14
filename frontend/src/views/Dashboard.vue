<template>
  <div class="dashboard">
    <!-- 欢迎横幅 -->
    <div class="welcome-banner">
      <div class="banner-content">
        <div class="banner-text">
          <h1 class="banner-title">{{ timeOfDay }}好，{{ username }} 👋</h1>
          <p class="banner-desc">这是你的测试工作台概览，今天也要加油哦！</p>
        </div>
        <div class="banner-actions">
          <a-button type="primary" shape="round" @click="$router.push({ name: 'project-list' })">
            <template #icon><icon-plus /></template>
            创建项目
          </a-button>
          <a-button shape="round" @click="$router.push({ name: 'api-debug' })">
            <template #icon><icon-bug /></template>
            接口调试
          </a-button>
        </div>
      </div>
      <div class="banner-bg">
        <div class="bg-circle bg-circle-1"></div>
        <div class="bg-circle bg-circle-2"></div>
        <div class="bg-circle bg-circle-3"></div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div
        v-for="(card, index) in statCards"
        :key="index"
        class="stat-card"
        @click="$router.push(card.route)"
      >
        <div class="stat-card-icon" :style="{ background: card.iconBg }">
          <component :is="card.icon" :style="{ color: card.iconColor }" />
        </div>
        <div class="stat-card-body">
          <div class="stat-card-label">{{ card.label }}</div>
          <div class="stat-card-value">
            <span class="stat-number">{{ card.value }}</span>
            <span class="stat-unit">{{ card.unit }}</span>
          </div>
        </div>
        <div class="stat-card-trend" :class="card.trend > 0 ? 'trend-up' : 'trend-down'" v-if="card.trend">
          <icon-arrow-rise v-if="card.trend > 0" />
          <icon-arrow-fall v-else />
          <template v-if="card.trendLabel === '较昨日'">{{ Math.abs(card.trend) }}%</template>
          <template v-else>本周+{{ card.trend }}</template>
        </div>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧：趋势 + 记录 -->
      <div class="content-left">
        <!-- 执行趋势 -->
        <div class="panel">
          <div class="panel-head">
            <div>
              <h3 class="panel-title">执行趋势</h3>
              <p class="panel-sub">用例执行情况统计</p>
            </div>
            <div class="pill-tabs">
              <button
                v-for="d in [7, 14, 30]"
                :key="d"
                class="pill-tab"
                :class="{ active: trendDays === d }"
                @click="trendDays = d; loadTrendData()"
              >
                近{{ d }}天
              </button>
            </div>
          </div>
          <div class="chart-legend">
            <span class="legend-item"><i class="dot dot-green"></i>通过</span>
            <span class="legend-item"><i class="dot dot-red"></i>失败</span>
            <span class="legend-item"><i class="dot dot-yellow"></i>错误</span>
          </div>
          <div ref="trendChartRef" class="chart-box"></div>
        </div>

        <!-- 最近执行 -->
        <div class="panel">
          <div class="panel-head">
            <div>
              <h3 class="panel-title">最近执行</h3>
              <p class="panel-sub">最近的测试执行记录</p>
            </div>
            <a-button type="text" size="small" @click="$router.push({ name: 'report-list' })">
              查看全部 <icon-right />
            </a-button>
          </div>
          <div class="run-cards">
            <div
              v-for="run in recentRuns"
              :key="run.id"
              class="run-card"
              @click="run.test_type === 'ui_batch' ? $router.push({ name: 'ui-batch-run-detail', params: { runId: run.id } }) : $router.push({ name: 'api-batch-task-detail', params: { taskId: run.id } })"
            >
              <div class="run-card-top">
                <span class="run-card-name">{{ run.name }}</span>
                <span class="run-card-badge" :class="`badge-${run.status}`">{{ getStatusLabel(run.status) }}</span>
              </div>
              <div class="run-card-bottom">
                <div class="run-card-stats">
                  <span class="rcs rcs-pass">{{ run.pass_count }}</span>
                  <span class="rcs rcs-fail">{{ run.fail_count }}</span>
                  <span class="rcs rcs-error">{{ run.error_count }}</span>
                </div>
                <span class="run-card-time">{{ run.created_at?.slice(5, 16) }}</span>
              </div>
            </div>
            <div v-if="recentRuns.length === 0" class="empty-hint">暂无执行记录</div>
          </div>
        </div>
      </div>

      <!-- 右侧 -->
      <div class="content-right">
        <!-- 通过率 -->
        <div class="panel rate-panel">
          <h3 class="panel-title">通过率</h3>
          <div class="rate-body">
            <div class="rate-chart-wrap">
              <div ref="passRateChartRef" class="rate-chart"></div>
              <div class="rate-center">
                <span class="rate-num">{{ passRate.pass_rate }}</span>
                <span class="rate-pct">%</span>
              </div>
            </div>
            <div class="rate-bars">
              <div class="rate-bar-item" v-for="r in rateItems" :key="r.label">
                <div class="rbi-head">
                  <span class="rbi-dot" :style="{ background: r.color }"></span>
                  <span class="rbi-label">{{ r.label }}</span>
                  <span class="rbi-val">{{ r.value }}</span>
                  <span class="rbi-pct">{{ r.pct }}%</span>
                </div>
                <div class="rbi-track">
                  <div class="rbi-fill" :style="{ width: r.pct + '%', background: `linear-gradient(90deg, ${r.color}, ${r.colorLight})` }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 用例分布 -->
        <div class="panel">
          <h3 class="panel-title">用例分布</h3>
          <div class="dist-body">
            <div ref="distributionChartRef" class="dist-chart"></div>
            <div class="dist-legend">
              <div v-for="(item, i) in distributionData" :key="item.name" class="dl-item">
                <div class="dl-color" :style="{ background: distColors[i] || '#94a3b8' }"></div>
                <div class="dl-info">
                  <span class="dl-name">{{ item.name }}</span>
                  <span class="dl-pct">{{ distributionTotal > 0 ? Math.round(item.value / distributionTotal * 100) : 0 }}%</span>
                </div>
                <span class="dl-val">{{ item.value }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 快捷入口 -->
        <div class="panel shortcuts-panel">
          <h3 class="panel-title">快捷入口</h3>
          <div class="shortcuts">
            <div v-for="s in shortcuts" :key="s.label" class="shortcut" @click="$router.push(s.route)">
              <div class="sc-icon" :style="{ background: s.bg }">
                <component :is="s.icon" :style="{ color: s.color }" />
              </div>
              <span class="sc-label">{{ s.label }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, markRaw } from 'vue'
import {
  IconFolder, IconDesktop, IconCode, IconPlayArrow,
  IconRight, IconPlus, IconBug, IconFile, IconStorage, IconSettings,
  IconArrowRise, IconArrowFall,
} from '@arco-design/web-vue/es/icon'
import * as echarts from 'echarts'
import {
  getDashboardStats, getRecentRuns, getRunTrend, getPassRate, getCaseDistribution,
} from '@/api/dashboard'
import type { RecentRun, TrendItem, PassRate, CaseDistribution } from '@/api/dashboard'

const username = ref('用户')
const timeOfDay = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return '早上'
  if (h < 18) return '下午'
  return '晚上'
})

const statCards = ref([
  { label: '项目总数', value: 0, unit: '个', icon: markRaw(IconFolder), iconBg: 'linear-gradient(135deg,#ede9fe,#ddd6fe)', iconColor: '#7c3aed', route: { name: 'project-list' }, trend: 0, trendLabel: '本周新增' },
  { label: 'UI 用例', value: 0, unit: '条', icon: markRaw(IconDesktop), iconBg: 'linear-gradient(135deg,#e0e7ff,#c7d2fe)', iconColor: '#6366f1', route: { name: 'ui-case-list' }, trend: 0, trendLabel: '本周新增' },
  { label: '接口用例', value: 0, unit: '条', icon: markRaw(IconCode), iconBg: 'linear-gradient(135deg,#dbeafe,#bfdbfe)', iconColor: '#3b82f6', route: { name: 'api-test-manage' }, trend: 0, trendLabel: '本周新增' },
  { label: '今日执行', value: 0, unit: '次', icon: markRaw(IconPlayArrow), iconBg: 'linear-gradient(135deg,#d1fae5,#a7f3d0)', iconColor: '#059669', route: { name: 'report-list' }, trend: 0, trendLabel: '较昨日' },
])

const recentRuns = ref<RecentRun[]>([])
const trendDays = ref(7)
const trendData = ref<TrendItem[]>([])
const passRate = reactive<PassRate>({ total: 0, pass: 0, fail: 0, error: 0, pass_rate: 0 })
const distributionData = ref<CaseDistribution[]>([])

const rateItems = computed(() => {
  const t = passRate.total || 1
  return [
    { label: '通过', value: passRate.pass, pct: (passRate.pass / t * 100).toFixed(1), color: '#10b981', colorLight: '#6ee7b7' },
    { label: '失败', value: passRate.fail, pct: (passRate.fail / t * 100).toFixed(1), color: '#f43f5e', colorLight: '#fda4af' },
    { label: '错误', value: passRate.error, pct: (passRate.error / t * 100).toFixed(1), color: '#f59e0b', colorLight: '#fcd34d' },
  ]
})

const distColors = ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#f43f5e', '#ec4899']

const distributionTotal = computed(() => {
  return distributionData.value.reduce((sum, item) => sum + item.value, 0)
})

const shortcuts = [
  { label: '项目', icon: markRaw(IconFolder), bg: '#f3e8ff', color: '#7c3aed', route: { name: 'project-list' } },
  { label: '接口', icon: markRaw(IconCode), bg: '#e0e7ff', color: '#6366f1', route: { name: 'api-test-manage' } },
  { label: '调试', icon: markRaw(IconBug), bg: '#dbeafe', color: '#3b82f6', route: { name: 'api-debug' } },
  { label: '报告', icon: markRaw(IconFile), bg: '#d1fae5', color: '#059669', route: { name: 'report-list' } },
  { label: '环境', icon: markRaw(IconStorage), bg: '#fef3c7', color: '#d97706', route: { name: 'project-list' } },
  { label: '设置', icon: markRaw(IconSettings), bg: '#fce7f3', color: '#db2777', route: { name: 'project-list' } },
]

const trendChartRef = ref<HTMLElement>()
const passRateChartRef = ref<HTMLElement>()
const distributionChartRef = ref<HTMLElement>()
let trendChart: echarts.ECharts | null = null
let passRateChart: echarts.ECharts | null = null
let distributionChart: echarts.ECharts | null = null

async function loadStats() {
  try {
    const d = await getDashboardStats()
    statCards.value[0].value = d.project_count
    statCards.value[1].value = d.ui_case_count
    statCards.value[2].value = d.api_case_count
    statCards.value[3].value = d.today_run_count
    if (d.trends) {
      statCards.value[0].trend = d.trends.project
      statCards.value[1].trend = d.trends.ui_case
      statCards.value[2].trend = d.trends.api_case
      statCards.value[3].trend = d.trends.today_run
    }
  } catch (e) { console.error(e) }
}
async function loadRecentRuns() {
  try { recentRuns.value = await getRecentRuns(4) } catch (e) { console.error(e) }
}
async function loadTrendData() {
  try { trendData.value = await getRunTrend(trendDays.value); renderTrend() } catch (e) { console.error(e) }
}
async function loadPassRate() {
  try { Object.assign(passRate, await getPassRate()); renderRate() } catch (e) { console.error(e) }
}
async function loadDistribution() {
  try { distributionData.value = await getCaseDistribution(); renderDist() } catch (e) { console.error(e) }
}

function renderTrend() {
  if (!trendChartRef.value) return
  if (!trendChart) trendChart = echarts.init(trendChartRef.value)
  const dates = trendData.value.map(i => i.date)
  trendChart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#fff',
      borderColor: '#f3f4f6',
      textStyle: { color: '#374151', fontSize: 12 },
      formatter: (params: any) => {
        const colors: Record<string, string> = { '通过': '#10b981', '失败': '#f43f5e', '错误': '#f59e0b' }
        let html = `<div style="font-weight:600;margin-bottom:4px">${params[0].axisValue}</div>`
        for (const p of params) {
          html += `<div style="display:flex;align-items:center;gap:6px"><span style="width:8px;height:8px;border-radius:50%;background:${colors[p.seriesName] || '#9ca3af'}"></span>${p.seriesName}：${p.value}</div>`
        }
        return html
      },
    },
    legend: { show: false },
    grid: { left: 40, right: 16, top: 16, bottom: 28 },
    xAxis: { type: 'category', data: dates, boundaryGap: false, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#9ca3af', fontSize: 11 } },
    yAxis: { type: 'value', axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#9ca3af', fontSize: 11 }, splitLine: { lineStyle: { color: '#f3f4f6' } } },
    series: [
      { name: '通过', type: 'line', data: trendData.value.map(i => i.pass), smooth: 0.5, symbol: 'none', lineStyle: { width: 2.5, color: '#10b981' }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(16,185,129,0.2)' }, { offset: 1, color: 'rgba(16,185,129,0)' }] } } },
      { name: '失败', type: 'line', data: trendData.value.map(i => i.fail), smooth: 0.5, symbol: 'none', lineStyle: { width: 2.5, color: '#f43f5e' }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(244,63,94,0.15)' }, { offset: 1, color: 'rgba(244,63,94,0)' }] } } },
      { name: '错误', type: 'line', data: trendData.value.map(i => i.error), smooth: 0.5, symbol: 'none', lineStyle: { width: 2.5, color: '#f59e0b' }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(245,158,11,0.15)' }, { offset: 1, color: 'rgba(245,158,11,0)' }] } } },
    ],
    animationDuration: 1000,
  })
}

function renderRate() {
  if (!passRateChartRef.value) return
  if (passRateChart) passRateChart.dispose()
  passRateChart = echarts.init(passRateChartRef.value)
  const total = passRate.pass + passRate.fail + passRate.error
  const colors = [
    { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [{ offset: 0, color: '#10b981' }, { offset: 1, color: '#6ee7b7' }] },
    { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [{ offset: 0, color: '#ef4444' }, { offset: 1, color: '#fca5a5' }] },
    { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [{ offset: 0, color: '#f59e0b' }, { offset: 1, color: '#fcd34d' }] },
  ]
  passRateChart.setOption({
    series: [{
      type: 'pie',
      radius: ['45%', '80%'],
      center: ['50%', '50%'],
      padAngle: 3,
      label: { show: false },
      labelLine: { show: false },
      emphasis: { scale: true, scaleSize: 6 },
      itemStyle: {
        borderRadius: 8,
        borderColor: '#fff',
        borderWidth: 3,
      },
      data: [
        { value: passRate.pass, itemStyle: { color: colors[0] } },
        { value: passRate.fail, itemStyle: { color: colors[1] } },
        { value: passRate.error, itemStyle: { color: colors[2] } },
        { value: total === 0 ? 1 : 0, itemStyle: { color: '#f3f4f6' } },
      ],
    }],
    animationDuration: 800,
    animationEasing: 'cubicOut',
  })
}

function renderDist() {
  if (!distributionChartRef.value) return
  if (distributionChart) distributionChart.dispose()
  distributionChart = echarts.init(distributionChartRef.value)
  const colors = [
    { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [{ offset: 0, color: '#8b5cf6' }, { offset: 1, color: '#a78bfa' }] },
    { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [{ offset: 0, color: '#3b82f6' }, { offset: 1, color: '#93c5fd' }] },
    { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [{ offset: 0, color: '#10b981' }, { offset: 1, color: '#6ee7b7' }] },
    { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [{ offset: 0, color: '#f59e0b' }, { offset: 1, color: '#fcd34d' }] },
  ]
  distributionChart.setOption({
    series: [{
      type: 'pie',
      radius: ['45%', '80%'],
      center: ['50%', '50%'],
      padAngle: 3,
      label: { show: false },
      labelLine: { show: false },
      emphasis: { scale: true, scaleSize: 6 },
      itemStyle: {
        borderRadius: 8,
        borderColor: '#fff',
        borderWidth: 3,
      },
      data: distributionData.value.map((item, i) => ({
        ...item,
        itemStyle: { color: colors[i] || colors[0] },
      })),
    }],
    animationDuration: 800,
    animationEasing: 'cubicOut',
  })
}

function getStatusLabel(s: string) {
  return { done: '完成', completed: '完成', running: '运行中', error: '失败', failed: '失败', pending: '等待' }[s] || s
}

function handleResize() { trendChart?.resize(); passRateChart?.resize(); distributionChart?.resize() }

onMounted(async () => {
  await Promise.all([loadStats(), loadRecentRuns(), loadTrendData(), loadPassRate(), loadDistribution()])
  window.addEventListener('resize', handleResize)
})
onUnmounted(() => {
  trendChart?.dispose(); passRateChart?.dispose(); distributionChart?.dispose()
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.dashboard { width: 100%; }

/* ---- 欢迎横幅 ---- */
.welcome-banner {
  position: relative;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 20px;
  padding: 32px 40px;
  margin-bottom: 24px;
  overflow: hidden;
  color: white;
}
.banner-content { position: relative; z-index: 2; display: flex; align-items: center; justify-content: space-between; }
.banner-title { font-size: 24px; font-weight: 700; margin: 0 0 8px; }
.banner-desc { font-size: 14px; opacity: 0.85; margin: 0; }
.banner-actions { display: flex; gap: 12px; }
.banner-bg { position: absolute; inset: 0; z-index: 1; overflow: hidden; }
.bg-circle { position: absolute; border-radius: 50%; background: rgba(255,255,255,0.08); }
.bg-circle-1 { width: 300px; height: 300px; top: -100px; right: -50px; }
.bg-circle-2 { width: 200px; height: 200px; bottom: -80px; right: 200px; }
.bg-circle-3 { width: 150px; height: 150px; top: 20px; right: 350px; }

/* ---- 统计卡片 ---- */
.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 24px; }
.stat-card {
  display: flex; align-items: center; gap: 16px;
  background: white; border-radius: 16px; padding: 20px;
  border: 1px solid #f3f4f6; cursor: pointer;
  transition: all 0.3s ease;
}
.stat-card:hover { transform: translateY(-4px); box-shadow: 0 12px 40px rgba(0,0,0,0.08); border-color: transparent; }
.stat-card-icon { width: 48px; height: 48px; display: flex; align-items: center; justify-content: center; border-radius: 14px; font-size: 22px; flex-shrink: 0; }
.stat-card-body { flex: 1; }
.stat-card-label { font-size: 12px; color: #9ca3af; margin-bottom: 4px; }
.stat-card-value { display: flex; align-items: baseline; gap: 4px; }
.stat-number { font-size: 28px; font-weight: 700; color: #111827; }
.stat-unit { font-size: 13px; color: #9ca3af; }
.stat-card-trend { font-size: 12px; font-weight: 500; padding: 2px 8px; border-radius: 20px; }
.trend-up { color: #059669; background: #ecfdf5; }
.trend-down { color: #dc2626; background: #fef2f2; }

/* ---- 主内容区 ---- */
.main-content { display: grid; grid-template-columns: 1.5fr 1fr; gap: 24px; }
.content-left, .content-right { display: flex; flex-direction: column; gap: 24px; }

/* ---- 面板 ---- */
.panel {
  background: white; border-radius: 16px; padding: 24px;
  border: 1px solid #f3f4f6;
}
.panel-head { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 20px; }
.panel-title { font-size: 15px; font-weight: 600; color: #111827; margin: 0; }
.panel-sub { font-size: 12px; color: #9ca3af; margin: 4px 0 0; }

/* ---- 胶囊切换 ---- */
.pill-tabs { display: flex; background: #f9fafb; border-radius: 10px; padding: 3px; }
.pill-tab {
  padding: 6px 14px; border: none; background: transparent;
  color: #6b7280; font-size: 12px; border-radius: 8px; cursor: pointer; transition: all 0.2s;
}
.pill-tab.active { background: white; color: #111827; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }

/* ---- 图例 ---- */
.chart-legend { display: flex; gap: 20px; margin-bottom: 12px; }
.legend-item { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #6b7280; }
.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.dot-green { background: #10b981; }
.dot-red { background: #f43f5e; }
.dot-yellow { background: #f59e0b; }

.chart-box { width: 100%; height: 280px; }

/* ---- 执行记录卡片 ---- */
.run-cards { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.run-card {
  background: #f9fafb; border-radius: 12px; padding: 16px;
  cursor: pointer; transition: all 0.2s; border: 1px solid transparent;
}
.run-card:hover { background: white; border-color: #e5e7eb; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
.run-card-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.run-card-name { font-size: 13px; font-weight: 500; color: #111827; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 70%; }
.run-card-badge { font-size: 11px; padding: 2px 8px; border-radius: 20px; font-weight: 500; }
.badge-done, .badge-completed { background: #ecfdf5; color: #059669; }
.badge-running { background: #eff6ff; color: #2563eb; }
.badge-error, .badge-failed { background: #fef2f2; color: #dc2626; }
.badge-pending { background: #f3f4f6; color: #6b7280; }
.run-card-bottom { display: flex; align-items: center; justify-content: space-between; }
.run-card-stats { display: flex; gap: 8px; font-size: 13px; font-weight: 600; }
.rcs-pass { color: #059669; }
.rcs-fail { color: #dc2626; }
.rcs-error { color: #d97706; }
.run-card-time { font-size: 11px; color: #9ca3af; }
.empty-hint { grid-column: 2; text-align: center; padding: 32px; color: #9ca3af; font-size: 13px; }

/* ---- 通过率 ---- */
.rate-body { display: flex; align-items: center; gap: 32px; }
.rate-chart-wrap { position: relative; width: 150px; height: 150px; flex-shrink: 0; background: white; border-radius: 50%; }
.rate-chart { width: 100%; height: 100%; position: relative; z-index: 0; }
.rate-center {
  position: absolute; inset: 0; display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  background: radial-gradient(circle, rgba(255,255,255,1) 38%, rgba(255,255,255,1) 42%, rgba(255,255,255,0) 43%);
  border-radius: 50%;
  z-index: 1;
}
.rate-num { font-size: 26px; font-weight: 700; color: #374151; line-height: 1; }
.rate-pct { font-size: 12px; color: #9ca3af; margin-top: 1px; font-weight: 500; }
.rate-bars { flex: 1; display: flex; flex-direction: column; gap: 16px; }
.rate-bar-item { transition: all 0.2s; }
.rate-bar-item:hover { transform: translateX(4px); }
.rbi-head { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.rbi-dot { width: 10px; height: 10px; border-radius: 50%; box-shadow: 0 0 0 3px rgba(0,0,0,0.04); }
.rbi-label { font-size: 13px; color: #6b7280; flex: 1; font-weight: 500; }
.rbi-val { font-size: 14px; font-weight: 700; color: #111827; min-width: 32px; text-align: right; }
.rbi-pct { font-size: 11px; color: #9ca3af; min-width: 44px; text-align: right; }
.rbi-track { height: 8px; background: #f3f4f6; border-radius: 4px; overflow: hidden; }
.rbi-fill { height: 100%; border-radius: 4px; transition: width 1s cubic-bezier(0.4, 0, 0.2, 1); }

/* ---- 用例分布 ---- */
.dist-body { display: flex; align-items: center; gap: 28px; }
.dist-chart { width: 140px; height: 140px; flex-shrink: 0; }
.dist-legend { flex: 1; display: flex; flex-direction: column; gap: 12px; }
.dl-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 14px; background: #f9fafb; border-radius: 12px;
  transition: all 0.2s;
}
.dl-item:hover { background: #f3f4f6; transform: translateX(4px); }
.dl-color { width: 4px; height: 32px; border-radius: 2px; flex-shrink: 0; }
.dl-info { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.dl-name { font-size: 13px; color: #6b7280; font-weight: 500; }
.dl-pct { font-size: 11px; color: #9ca3af; }
.dl-val { font-size: 18px; font-weight: 700; color: #111827; }

/* ---- 快捷入口 ---- */
.shortcuts { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.shortcut {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  padding: 14px 8px; background: #f9fafb; border-radius: 12px;
  cursor: pointer; transition: all 0.2s;
}
.shortcut:hover { background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.06); transform: translateY(-2px); }
.sc-icon { width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; border-radius: 12px; font-size: 18px; }
.sc-label { font-size: 12px; color: #4b5563; font-weight: 500; }
</style>

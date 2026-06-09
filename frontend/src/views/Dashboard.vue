<template>
  <div class="dashboard">
    <!-- 欢迎横幅 -->
    <div class="welcome-banner">
      <div class="banner-content">
        <div class="banner-text">
          <h1 class="banner-title">Good {{ timeOfDay }}，{{ username }} 👋</h1>
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
          {{ Math.abs(card.trend) }}%
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
              @click="$router.push({ name: 'api-batch-task-detail', params: { taskId: run.id } })"
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
              <div class="rate-val">
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
                </div>
                <div class="rbi-track">
                  <div class="rbi-fill" :style="{ width: r.pct + '%', background: r.color }"></div>
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
                <span class="dl-dot" :class="i === 0 ? 'dl-purple' : 'dl-blue'"></span>
                <span class="dl-name">{{ item.name }}</span>
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
  { label: '项目总数', value: 0, unit: '个', icon: markRaw(IconFolder), iconBg: 'linear-gradient(135deg,#ede9fe,#ddd6fe)', iconColor: '#7c3aed', route: { name: 'project-list' }, trend: 12 },
  { label: 'UI 用例', value: 0, unit: '条', icon: markRaw(IconDesktop), iconBg: 'linear-gradient(135deg,#e0e7ff,#c7d2fe)', iconColor: '#6366f1', route: { name: 'ui-case-list' }, trend: 8 },
  { label: '接口用例', value: 0, unit: '条', icon: markRaw(IconCode), iconBg: 'linear-gradient(135deg,#dbeafe,#bfdbfe)', iconColor: '#3b82f6', route: { name: 'api-test-manage' }, trend: 15 },
  { label: '今日执行', value: 0, unit: '次', icon: markRaw(IconPlayArrow), iconBg: 'linear-gradient(135deg,#d1fae5,#a7f3d0)', iconColor: '#059669', route: { name: 'report-list' }, trend: -5 },
])

const recentRuns = ref<RecentRun[]>([])
const trendDays = ref(7)
const trendData = ref<TrendItem[]>([])
const passRate = reactive<PassRate>({ total: 0, pass: 0, fail: 0, error: 0, pass_rate: 0 })
const distributionData = ref<CaseDistribution[]>([])

const rateItems = computed(() => {
  const t = passRate.total || 1
  return [
    { label: '通过', value: passRate.pass, pct: (passRate.pass / t * 100).toFixed(0), color: '#10b981' },
    { label: '失败', value: passRate.fail, pct: (passRate.fail / t * 100).toFixed(0), color: '#f43f5e' },
    { label: '错误', value: passRate.error, pct: (passRate.error / t * 100).toFixed(0), color: '#f59e0b' },
  ]
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
    tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#f3f4f6', textStyle: { color: '#374151' } },
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
  if (!passRateChart) passRateChart = echarts.init(passRateChartRef.value)
  const total = passRate.pass + passRate.fail + passRate.error
  passRateChart.setOption({
    series: [{
      type: 'pie', radius: ['75%', '92%'], center: ['50%', '50%'],
      label: { show: false }, labelLine: { show: false },
      emphasis: { scale: false, disabled: true },
      itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 3 },
      data: [
        { value: passRate.pass, itemStyle: { color: '#10b981' } },
        { value: passRate.fail, itemStyle: { color: '#f43f5e' } },
        { value: passRate.error, itemStyle: { color: '#f59e0b' } },
        { value: total === 0 ? 1 : 0, itemStyle: { color: '#f9fafb' } },
      ],
    }],
    animationDuration: 1200,
  })
}

function renderDist() {
  if (!distributionChartRef.value) return
  if (!distributionChart) distributionChart = echarts.init(distributionChartRef.value)
  distributionChart.setOption({
    series: [{
      type: 'pie', radius: ['50%', '78%'], center: ['50%', '50%'],
      label: { show: false }, labelLine: { show: false },
      emphasis: { scale: false, disabled: true },
      itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 3 },
      data: distributionData.value.map((item, i) => ({
        ...item,
        itemStyle: { color: i === 0 ? '#8b5cf6' : '#3b82f6' },
      })),
    }],
    animationDuration: 800,
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
.rate-chart-wrap { position: relative; width: 140px; height: 140px; flex-shrink: 0; }
.rate-chart { width: 100%; height: 100%; }
.rate-val { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; }
.rate-num { font-size: 36px; font-weight: 700; color: #111827; }
.rate-pct { font-size: 16px; color: #9ca3af; margin-top: 4px; }
.rate-bars { flex: 1; display: flex; flex-direction: column; gap: 16px; }
.rate-bar-item {}
.rbi-head { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.rbi-dot { width: 8px; height: 8px; border-radius: 50%; }
.rbi-label { font-size: 12px; color: #6b7280; flex: 1; }
.rbi-val { font-size: 14px; font-weight: 600; color: #111827; }
.rbi-track { height: 6px; background: #f3f4f6; border-radius: 3px; overflow: hidden; }
.rbi-fill { height: 100%; border-radius: 3px; transition: width 0.8s ease; }

/* ---- 用例分布 ---- */
.dist-body { display: flex; align-items: center; gap: 24px; }
.dist-chart { width: 120px; height: 120px; flex-shrink: 0; }
.dist-legend { display: flex; flex-direction: column; gap: 14px; }
.dl-item { display: flex; align-items: center; gap: 10px; }
.dl-dot { width: 10px; height: 10px; border-radius: 4px; }
.dl-purple { background: #8b5cf6; }
.dl-blue { background: #3b82f6; }
.dl-name { font-size: 12px; color: #6b7280; min-width: 56px; }
.dl-val { font-size: 15px; font-weight: 600; color: #111827; }

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

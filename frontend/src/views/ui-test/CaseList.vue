<template>
  <div class="ui-case-list-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>UI 用例管理</h2>
        <a-select
          v-model="selectedProjectId"
          :loading="projectsLoading"
          placeholder="选择项目"
          style="width: 200px"
          allow-search
          @change="loadCases"
        >
          <a-option
            v-for="p in projects"
            :key="p.id"
            :value="p.id"
            :label="p.name"
          />
        </a-select>
      </div>
      <div class="header-right">
        <a-button type="primary" @click="goToRecord">
          <template #icon><icon-video-camera /></template>
          录制新用例
        </a-button>
      </div>
    </div>

    <!-- 用例表格 -->
    <div class="case-table-wrapper">
      <a-table
        :data="cases"
        :loading="loading"
        :pagination="pagination"
        @page-change="onPageChange"
        @page-size-change="onPageSizeChange"
      >
        <template #columns>
          <a-table-column title="ID" data-index="id" :width="80" />
          <a-table-column title="用例名称" data-index="name">
            <template #cell="{ record }">
              <a-link @click="viewCaseDetail(record)">{{ record.name }}</a-link>
            </template>
          </a-table-column>
          <a-table-column title="目标 URL" data-index="base_url" :ellipsis="true" />
          <a-table-column title="步骤数" :width="100">
            <template #cell="{ record }">
              <a-tag color="blue" size="small">{{ record.steps?.length || 0 }} 步</a-tag>
            </template>
          </a-table-column>
          <a-table-column title="创建时间" data-index="created_at" :width="180">
            <template #cell="{ record }">
              {{ formatTime(record.created_at) }}
            </template>
          </a-table-column>
          <a-table-column title="操作" :width="250" fixed="right">
            <template #cell="{ record }">
              <a-space>
                <a-button type="text" size="mini" @click="viewCaseDetail(record)">
                  查看
                </a-button>
                <a-button
                  type="text"
                  size="mini"
                  status="success"
                  :loading="runningCaseId === record.id"
                  @click="handleRun(record)"
                >
                  <template #icon><icon-play-arrow /></template>
                  执行
                </a-button>
                <a-button type="text" size="mini" status="danger" @click="handleDelete(record)">
                  删除
                </a-button>
              </a-space>
            </template>
          </a-table-column>
        </template>
      </a-table>
    </div>

    <!-- 用例详情弹窗 -->
    <a-modal
      v-model:visible="detailVisible"
      :title="detailCase?.name || '用例详情'"
      :width="800"
      :footer="false"
    >
      <div class="case-detail" v-if="detailCase">
        <a-descriptions :column="2" bordered size="small">
          <a-descriptions-item label="用例名称">{{ detailCase.name }}</a-descriptions-item>
          <a-descriptions-item label="目标 URL">{{ detailCase.base_url || '-' }}</a-descriptions-item>
          <a-descriptions-item label="步骤数">{{ detailCase.steps?.length || 0 }}</a-descriptions-item>
          <a-descriptions-item label="创建时间">{{ formatTime(detailCase.created_at) }}</a-descriptions-item>
          <a-descriptions-item label="描述" :span="2">{{ detailCase.description || '-' }}</a-descriptions-item>
        </a-descriptions>

        <!-- 步骤列表 -->
        <div class="detail-steps">
          <h4>执行步骤</h4>
          <a-timeline>
            <a-timeline-item
              v-for="(step, index) in detailCase.steps"
              :key="step.id"
              :dot-color="getStepColor(step.action)"
            >
              <div class="timeline-content">
                <span class="step-index">{{ index + 1 }}.</span>
                <span class="step-action">{{ getActionLabel(step.action) }}</span>
                <span class="step-desc">{{ getStepDesc(step) }}</span>
              </div>
            </a-timeline-item>
          </a-timeline>
        </div>
      </div>
    </a-modal>

    <!-- 执行结果弹窗 -->
    <a-modal
      v-model:visible="runResultVisible"
      title="执行结果"
      :width="800"
      :footer="false"
    >
      <div class="run-result" v-if="runResult">
        <!-- 执行统计 -->
        <div class="result-summary">
          <a-tag :color="runResult.status === 'completed' ? 'green' : 'red'" size="large">
            {{ runResult.status === 'completed' ? '执行成功' : '执行失败' }}
          </a-tag>
          <span class="result-stats">
            共 {{ runResult.total }} 步，
            <span class="passed">{{ runResult.passed }} 通过</span>，
            <span class="failed">{{ runResult.failed }} 失败</span>
          </span>
        </div>

        <!-- 步骤详情 -->
        <div class="result-steps">
          <div
            v-for="result in runResult.results"
            :key="result.step"
            class="result-step"
            :class="{ 'step-success': result.success, 'step-failed': !result.success }"
          >
            <div class="step-header">
              <a-tag :color="result.success ? 'green' : 'red'" size="small">
                {{ result.step }}
              </a-tag>
              <span class="step-action">{{ getActionLabel(result.action) }}</span>
              <span class="step-duration">{{ result.duration }}ms</span>
            </div>
            <div class="step-message">{{ result.message }}</div>
            <div class="step-screenshot" v-if="result.screenshot">
              <img :src="`data:image/jpeg;base64,${result.screenshot}`" alt="截图" />
            </div>
          </div>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import { IconVideoCamera, IconPlayArrow, IconClose } from '@arco-design/web-vue/es/icon'
import { useRouter } from 'vue-router'
import { getUICaseList, deleteUICase, runUICase, type UICase, type RunResult, type StepResult } from '@/api/uiCase'
import { getProjects, type Project } from '@/api/project'

const router = useRouter()

// ========== 状态 ==========

const projects = ref<Project[]>([])
const selectedProjectId = ref<number | null>(null)
const projectsLoading = ref(false)

const cases = ref<UICase[]>([])
const loading = ref(false)
const pagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
  showTotal: true,
  showJumper: true,
})

const detailVisible = ref(false)
const detailCase = ref<UICase | null>(null)

// 执行相关
const runResultVisible = ref(false)
const runResult = ref<RunResult | null>(null)
const runningCaseId = ref<number | null>(null)

// ========== 方法 ==========

async function loadProjects() {
  projectsLoading.value = true
  try {
    const res = await getProjects()
    projects.value = res || []
    if (projects.value.length > 0 && !selectedProjectId.value) {
      selectedProjectId.value = projects.value[0].id
    }
  } catch (err) {
    console.error('加载项目列表失败:', err)
  } finally {
    projectsLoading.value = false
  }
}

async function loadCases() {
  if (!selectedProjectId.value) return

  loading.value = true
  try {
    const skip = (pagination.value.current - 1) * pagination.value.pageSize
    const res = await getUICaseList(selectedProjectId.value, skip, pagination.value.pageSize)
    cases.value = res || []
    // TODO: 后端需要返回总数
    pagination.value.total = cases.value.length
  } catch (err) {
    console.error('加载用例列表失败:', err)
    Message.error('加载用例列表失败')
  } finally {
    loading.value = false
  }
}

function onPageChange(page: number) {
  pagination.value.current = page
  loadCases()
}

function onPageSizeChange(pageSize: number) {
  pagination.value.pageSize = pageSize
  pagination.value.current = 1
  loadCases()
}

function goToRecord() {
  router.push('/ui-record')
}

function viewCaseDetail(caseItem: UICase) {
  detailCase.value = caseItem
  detailVisible.value = true
}

async function handleDelete(caseItem: UICase) {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除用例 "${caseItem.name}" 吗？`,
    onOk: async () => {
      try {
        await deleteUICase(caseItem.id)
        Message.success('删除成功')
        loadCases()
      } catch (err) {
        Message.error('删除失败')
      }
    },
  })
}

async function handleRun(caseItem: UICase) {
  // 跳转到执行调试页面
  router.push(`/ui-run-debug/${caseItem.id}`)
}

function formatTime(time: string): string {
  if (!time) return '-'
  return new Date(time).toLocaleString()
}

function getActionLabel(action: string): string {
  const map: Record<string, string> = {
    navigate: '导航',
    click: '点击',
    dblclick: '双击',
    type: '输入',
    press: '按键',
    select: '选择',
    check: '勾选',
    uncheck: '取消勾选',
    hover: '悬停',
    scroll: '滚动',
    wait: '等待',
    assert: '断言',
    drag: '拖拽',
    new_page: '新窗口',
  }
  return map[action] || action
}

function getStepColor(action: string): string {
  const map: Record<string, string> = {
    navigate: 'blue',
    click: 'green',
    dblclick: 'green',
    type: 'orange',
    press: 'purple',
    assert: 'red',
    drag: 'cyan',
    new_page: 'blue',
  }
  return map[action] || 'gray'
}

function getStepDesc(step: Record<string, unknown>): string {
  if (step.action === 'navigate') return step.url as string || ''
  if (step.action === 'new_page') return step.url as string || '新窗口'
  if (step.action === 'type') {
    const target = step.target as Record<string, unknown> | undefined
    return `${target?.text || target?.selector || ''} → "${step.value}"`
  }
  if (step.action === 'press') return step.key as string || ''
  if (step.action === 'drag') {
    const from = step.from as { x: number; y: number } | undefined
    const to = step.to as { x: number; y: number } | undefined
    if (from && to) return `(${from.x},${from.y}) → (${to.x},${to.y})`
    return '拖拽'
  }
  const target = step.target as Record<string, unknown> | undefined
  if (target) return (target.text || target.selector || '') as string
  return ''
}

// ========== 生命周期 ==========

onMounted(() => {
  loadProjects().then(() => loadCases())
})
</script>

<style scoped>
.ui-case-list-page {
  padding: 20px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-left h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.case-table-wrapper {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
}

.case-detail {
  max-height: 60vh;
  overflow-y: auto;
}

.detail-steps {
  margin-top: 20px;
}

.detail-steps h4 {
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 600;
}

.timeline-content {
  display: flex;
  gap: 8px;
  align-items: baseline;
}

.step-index {
  font-weight: 600;
  color: #4e5969;
}

.step-action {
  color: #165DFF;
  font-weight: 500;
}

.step-desc {
  color: #86909c;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 执行结果样式 */
.run-result {
  max-height: 70vh;
  overflow-y: auto;
}

.result-summary {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #f2f3f5;
  border-radius: 8px;
  margin-bottom: 16px;
}

.result-stats {
  font-size: 14px;
  color: #4e5969;
}

.passed {
  color: #00b42a;
  font-weight: 600;
}

.failed {
  color: #f53f3f;
  font-weight: 600;
}

.result-steps {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-step {
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #e5e6eb;
}

.result-step.step-success {
  border-left: 4px solid #00b42a;
}

.result-step.step-failed {
  border-left: 4px solid #f53f3f;
}

.result-step .step-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.result-step .step-action {
  font-weight: 500;
  color: #1d2129;
}

.result-step .step-duration {
  margin-left: auto;
  font-size: 12px;
  color: #86909c;
}

.result-step .step-message {
  font-size: 13px;
  color: #4e5969;
}

.result-step .step-screenshot {
  margin-top: 8px;
}

.result-step .step-screenshot img {
  max-width: 100%;
  border-radius: 4px;
  border: 1px solid #e5e6eb;
}
</style>

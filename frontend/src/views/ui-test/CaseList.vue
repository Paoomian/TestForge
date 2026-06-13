<template>
  <div class="ui-case-manage">
    <a-layout style="height: 100%">
      <!-- 左侧项目列表 -->
      <a-layout-sider :width="260" class="project-sider">
        <div class="sider-header">
          <h3 class="sider-title">项目列表</h3>
        </div>
        <div class="sider-content">
          <div class="project-list">
            <div
              v-for="p in projects"
              :key="p.id"
              class="project-item"
              :class="{ active: selectedProjectId === p.id }"
              @click="handleSelectProject(p.id)"
            >
              <icon-folder class="project-icon" />
              <span class="project-name">{{ p.name }}</span>
              <a-tag size="small" color="arcoblue">{{ getProjectCaseCount(p.id) }}</a-tag>
            </div>
            <div v-if="projects.length === 0" class="empty-tip">
              暂无项目
            </div>
          </div>
        </div>
      </a-layout-sider>

      <!-- 右侧用例列表 -->
      <a-layout-content class="list-content">
        <!-- 工具栏 -->
        <div class="list-toolbar">
          <div class="toolbar-left">
            <h3 class="list-title">{{ currentProjectName || '请选择项目' }}</h3>
            <span v-if="selectedRowKeys.length > 0" class="selected-count">
              已选 {{ selectedRowKeys.length }} 项
            </span>
          </div>
          <div class="toolbar-right">
            <a-button
              v-if="selectedRowKeys.length > 0"
              type="primary"
              status="success"
              @click="handleBatchRun"
            >
              <template #icon><icon-play-arrow /></template>
              批量执行
            </a-button>
            <a-button type="primary" @click="goToRecord">
              <template #icon><icon-video-camera /></template>
              录制新用例
            </a-button>
          </div>
        </div>

        <!-- 用例表格 -->
        <div class="case-table-wrapper">
          <a-table
            v-model:selectedKeys="selectedRowKeys"
            :data="cases"
            :loading="loading"
            :pagination="pagination"
            :row-selection="{ type: 'checkbox' }"
            row-key="id"
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
              <a-table-column title="目标 URL" data-index="base_url" :ellipsis="true">
                <template #cell="{ record }">
                  <span :title="record.base_url">{{ record.base_url || '-' }}</span>
                </template>
              </a-table-column>
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
      </a-layout-content>
    </a-layout>

    <!-- 批量执行配置抽屉 -->
    <UIBatchRunDrawer
      v-model:visible="batchDrawerVisible"
      :cases="batchDrawerCases"
      @success="handleBatchRunSuccess"
    />

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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import {
  IconVideoCamera,
  IconPlayArrow,
  IconFolder,
} from '@arco-design/web-vue/es/icon'
import { useRouter } from 'vue-router'
import { getUICaseList, deleteUICase, type UICase } from '@/api/uiCase'
import { getProjects, type Project } from '@/api/project'
import UIBatchRunDrawer from './components/UIBatchRunDrawer.vue'

const router = useRouter()

// ========== 状态 ==========

const projects = ref<Project[]>([])
const selectedProjectId = ref<number | null>(null)
const projectsLoading = ref(false)
const projectCaseCounts = ref<Record<number, number>>({})

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
const runningCaseId = ref<number | null>(null)

// 多选相关
const selectedRowKeys = ref<number[]>([])

// 批量执行抽屉
const batchDrawerVisible = ref(false)
const batchDrawerCases = ref<UICase[]>([])

// ========== 计算属性 ==========

const currentProjectName = computed(() => {
  const p = projects.value.find(p => p.id === selectedProjectId.value)
  return p?.name || ''
})

// ========== 方法 ==========

function getProjectCaseCount(projectId: number): number {
  return projectCaseCounts.value[projectId] || 0
}

async function loadProjectCaseCounts() {
  // 加载每个项目的用例数
  for (const p of projects.value) {
    try {
      const res = await getUICaseList(p.id, 0, 1000)
      projectCaseCounts.value[p.id] = res?.length || 0
    } catch {
      projectCaseCounts.value[p.id] = 0
    }
  }
}

async function loadProjects() {
  projectsLoading.value = true
  try {
    const res = await getProjects()
    projects.value = res || []
    if (projects.value.length > 0 && !selectedProjectId.value) {
      selectedProjectId.value = projects.value[0].id
    }
    // 加载每个项目的用例数
    await loadProjectCaseCounts()
  } catch (err) {
    console.error('加载项目列表失败:', err)
  } finally {
    projectsLoading.value = false
  }
}

function handleSelectProject(projectId: number) {
  selectedProjectId.value = projectId
  pagination.value.current = 1
  loadCases()
}

async function loadCases() {
  if (!selectedProjectId.value) return

  loading.value = true
  try {
    const skip = (pagination.value.current - 1) * pagination.value.pageSize
    const res = await getUICaseList(selectedProjectId.value, skip, pagination.value.pageSize)
    cases.value = res || []
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

async function handleRun(caseItem: UICase) {
  router.push(`/ui-run-debug/${caseItem.id}`)
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
        // 更新项目用例数
        if (selectedProjectId.value) {
          projectCaseCounts.value[selectedProjectId.value] = Math.max(0, (projectCaseCounts.value[selectedProjectId.value] || 1) - 1)
        }
      } catch (err) {
        Message.error('删除失败')
      }
    },
  })
}

function handleBatchRun() {
  const selectedCases = cases.value.filter(c => selectedRowKeys.value.includes(c.id))
  if (selectedCases.length === 0) {
    Message.warning('请先选择要执行的用例')
    return
  }
  batchDrawerCases.value = selectedCases
  batchDrawerVisible.value = true
}

function handleBatchRunSuccess(runId: number) {
  batchDrawerVisible.value = false
  selectedRowKeys.value = []
  router.push({ name: 'ui-batch-run-detail', params: { runId } })
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
    go_back: '返回',
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
  if (step.action === 'go_back') return step.url as string || '返回上一页'
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
.ui-case-manage {
  height: calc(100vh - var(--header-height));
  background: var(--gray-50);
  margin: calc(-1 * var(--content-padding));
}

.project-sider {
  background: white !important;
  border-right: 1px solid rgba(224, 212, 252, 0.25) !important;
  box-shadow: 2px 0 8px rgba(99, 102, 241, 0.03);
}

.sider-header {
  padding: 20px 16px 12px;
  border-bottom: 1px solid rgba(224, 212, 252, 0.2);
}

.sider-title {
  margin: 0;
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--gray-800);
}

.sider-content {
  padding: 12px 8px;
  overflow-y: auto;
  height: calc(100% - 60px);
}

.project-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.project-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.project-item:hover {
  background: var(--gray-100);
}

.project-item.active {
  background: #e8f3ff;
  color: #165DFF;
}

.project-icon {
  font-size: 18px;
  color: #86909c;
}

.project-item.active .project-icon {
  color: #165DFF;
}

.project-name {
  flex: 1;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-tip {
  text-align: center;
  color: #c9cdd4;
  padding: 40px 0;
  font-size: 13px;
}

.list-content {
  padding: var(--content-padding);
  background: var(--gray-50);
  display: flex;
  flex-direction: column;
}

.list-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.list-title {
  margin: 0;
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--gray-800);
}

.case-table-wrapper {
  flex: 1;
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

.result-step .step-message.message-error {
  color: #f53f3f;
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

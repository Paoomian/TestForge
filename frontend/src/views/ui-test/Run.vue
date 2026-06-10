<template>
  <div class="ui-task-config">
    <!-- 页面头部 -->
    <div class="page-header">
      <div>
        <h2 class="page-title">UI 任务配置</h2>
        <p class="page-desc">配置并执行 UI 自动化批量测试任务</p>
      </div>
    </div>

    <!-- 筛选栏 -->
    <a-card :bordered="false" style="margin-bottom: 16px">
      <a-space wrap>
        <a-select
          v-model="selectorProjectId"
          placeholder="选择项目"
          style="width: 180px"
          @change="onProjectChange"
        >
          <a-option v-for="p in projects" :key="p.id" :value="p.id">
            {{ p.name }}
          </a-option>
        </a-select>
        <a-input
          v-model="selectorKeyword"
          placeholder="搜索用例名称"
          style="width: 200px"
          allow-clear
          @press-enter="loadCases"
        >
          <template #prefix><icon-search /></template>
        </a-input>
        <a-select
          v-model="selectorPriority"
          placeholder="优先级"
          style="width: 120px"
          allow-clear
          @change="loadCases"
        >
          <a-option value="P0">P0 致命</a-option>
          <a-option value="P1">P1 严重</a-option>
          <a-option value="P2">P2 一般</a-option>
          <a-option value="P3">P3 轻微</a-option>
        </a-select>
        <a-select
          v-model="selectorModule"
          placeholder="模块"
          style="width: 150px"
          allow-clear
          @change="loadCases"
        >
          <a-option v-for="m in moduleOptions" :key="m.value" :value="m.value">
            {{ m.label }}
          </a-option>
        </a-select>
        <a-button type="primary" @click="loadCases">
          <template #icon><icon-search /></template>
          搜索
        </a-button>
        <a-button @click="resetFilters">
          <template #icon><icon-refresh /></template>
          重置
        </a-button>
      </a-space>
    </a-card>

    <!-- 用例表格 -->
    <a-card :bordered="false" style="margin-bottom: 16px">
      <a-table
        v-model:selectedKeys="selectedCaseIds"
        :data="caseList"
        :loading="caseLoading"
        :pagination="false"
        :row-selection="{ type: 'checkbox' }"
        row-key="id"
        :scroll="{ y: 400 }"
      >
        <template #columns>
          <a-table-column title="编号" data-index="case_number" :width="120" />
          <a-table-column title="用例名称" data-index="name" />
          <a-table-column title="模块" data-index="module" :width="120">
            <template #cell="{ record }">
              <span v-if="record.module">{{ record.module }}</span>
              <span v-else class="text-gray">-</span>
            </template>
          </a-table-column>
          <a-table-column title="优先级" :width="90">
            <template #cell="{ record }">
              <a-tag size="small" :color="getPriorityColor(record.priority)">
                {{ record.priority || 'P2' }}
              </a-tag>
            </template>
          </a-table-column>
          <a-table-column title="步骤数" :width="80">
            <template #cell="{ record }">
              {{ record.steps?.length || 0 }} 步
            </template>
          </a-table-column>
        </template>
      </a-table>
    </a-card>

    <!-- 已选用例 + 执行配置 -->
    <a-row :gutter="16">
      <a-col :span="14">
        <a-card :bordered="false" title="已选用例">
          <UISelectedCaseList
            :cases="selectedCases"
            @remove="removeCase"
            @reorder="reorderCases"
          />
        </a-card>
      </a-col>
      <a-col :span="10">
        <a-card :bordered="false" title="执行配置">
          <a-form :model="form" layout="vertical">
            <a-form-item label="执行环境">
              <a-select
                v-model="form.environment_id"
                placeholder="选择环境（可选）"
                allow-clear
                :loading="envLoading"
              >
                <a-option v-for="env in environments" :key="env.id" :value="env.id">
                  {{ env.name }}
                </a-option>
              </a-select>
            </a-form-item>
            <a-form-item label="失败策略">
              <a-radio-group v-model="form.failure_strategy">
                <a-radio value="continue">继续执行</a-radio>
                <a-radio value="stop">遇到失败停止</a-radio>
              </a-radio-group>
            </a-form-item>
            <a-form-item label="浏览器">
              <a-select v-model="form.browser">
                <a-option value="chrome">Chrome</a-option>
                <a-option value="firefox">Firefox</a-option>
                <a-option value="edge">Edge</a-option>
              </a-select>
            </a-form-item>
            <a-form-item label="视口尺寸">
              <a-select v-model="form.viewport">
                <a-option value="1280x720">1280 x 720</a-option>
                <a-option value="1920x1080">1920 x 1080</a-option>
                <a-option value="375x812">iPhone (375 x 812)</a-option>
              </a-select>
            </a-form-item>
          </a-form>
        </a-card>
      </a-col>
    </a-row>

    <!-- 执行按钮 -->
    <a-card :bordered="false" style="margin-top: 16px">
      <a-button
        type="primary"
        size="large"
        :disabled="selectedCases.length === 0"
        :loading="submitting"
        @click="handleSubmit"
      >
        <template #icon><icon-play-arrow /></template>
        开始执行 ({{ selectedCases.length }} 个用例)
      </a-button>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { IconPlayArrow, IconSearch, IconRefresh } from '@arco-design/web-vue/es/icon'
import { getUICaseList, getUICaseModules, type UICase } from '@/api/uiCase'
import { getProjects, type Project } from '@/api/project'
import { getEnvironments } from '@/api/environment'
import type { Environment } from '@/api/apiTestCase'
import { createUIBatchRun } from '@/api/uiBatchRun'
import UISelectedCaseList from './components/UISelectedCaseList.vue'

const router = useRouter()

// 项目列表
const projects = ref<Project[]>([])
const environments = ref<Environment[]>([])
const envLoading = ref(false)

// 用例列表
const caseList = ref<UICase[]>([])
const caseLoading = ref(false)
const selectedCaseIds = ref<number[]>([])

// 已选用例（保持顺序）
const selectedCases = computed(() => {
  return selectedCaseIds.value
    .map(id => caseList.value.find(c => c.id === id))
    .filter(Boolean) as UICase[]
})

// 筛选条件
const selectorProjectId = ref<number | null>(null)
const selectorKeyword = ref('')
const selectorPriority = ref<string | undefined>(undefined)
const selectorModule = ref<string | undefined>(undefined)
const moduleOptions = ref<{ label: string; value: string }[]>([])

// 表单
const form = reactive({
  environment_id: undefined as number | undefined,
  failure_strategy: 'continue',
  browser: 'chrome',
  viewport: '1280x720',
})

// 提交状态
const submitting = ref(false)

// 优先级颜色
function getPriorityColor(priority: string): string {
  const colors: Record<string, string> = { P0: 'red', P1: 'orange', P2: 'blue', P3: 'green' }
  return colors[priority] || 'blue'
}

// 加载项目列表
async function loadProjects() {
  try {
    projects.value = await getProjects()
    if (projects.value.length > 0) {
      selectorProjectId.value = projects.value[0].id
      loadCases()
      loadModules()
    }
  } catch (e) {
    console.error('加载项目列表失败:', e)
  }
}

// 加载模块列表
async function loadModules() {
  if (!selectorProjectId.value) return
  try {
    const res = await getUICaseModules(selectorProjectId.value)
    moduleOptions.value = flattenModuleTree(res || [])
  } catch (e) {
    console.error('加载模块列表失败:', e)
  }
}

// 展平模块树为下拉选项
function flattenModuleTree(tree: any[]): { label: string; value: string }[] {
  const result: { label: string; value: string }[] = []
  function walk(nodes: any[], prefix = '') {
    for (const node of nodes) {
      const fullPath = prefix ? `${prefix}/${node.label}` : node.label
      result.push({ label: fullPath, value: node.value || fullPath })
      if (node.children?.length) {
        walk(node.children, fullPath)
      }
    }
  }
  walk(tree)
  return result
}

// 项目切换
function onProjectChange() {
  selectorKeyword.value = ''
  selectorPriority.value = undefined
  selectorModule.value = undefined
  selectedCaseIds.value = []
  loadCases()
  loadModules()
  loadEnvironments()
}

// 重置筛选
function resetFilters() {
  selectorKeyword.value = ''
  selectorPriority.value = undefined
  selectorModule.value = undefined
  loadCases()
}

// 加载用例列表
async function loadCases() {
  if (!selectorProjectId.value) return
  caseLoading.value = true
  try {
    const filters: Record<string, string> = {}
    if (selectorKeyword.value) filters.keyword = selectorKeyword.value
    if (selectorPriority.value) filters.priority = selectorPriority.value
    if (selectorModule.value) filters.module = selectorModule.value
    const res = await getUICaseList(selectorProjectId.value, 0, 1000, filters)
    caseList.value = (res as any) || []
  } catch (e) {
    console.error('加载用例列表失败:', e)
  } finally {
    caseLoading.value = false
  }
}

// 加载环境列表
async function loadEnvironments() {
  if (!selectorProjectId.value) return
  envLoading.value = true
  try {
    const res = await getEnvironments(selectorProjectId.value)
    environments.value = (res as any) || []
  } catch (e) {
    console.error('加载环境列表失败:', e)
  } finally {
    envLoading.value = false
  }
}

// 移除用例
function removeCase(caseId: number) {
  selectedCaseIds.value = selectedCaseIds.value.filter(id => id !== caseId)
}

// 重排序用例
function reorderCases(orderedIds: number[]) {
  // 保留不在当前表格中的已选用例
  const inTable = new Set(caseList.value.map(c => c.id))
  const keepOutside = selectedCaseIds.value.filter(id => !inTable.has(id))
  selectedCaseIds.value = [...keepOutside, ...orderedIds]
}

// 提交
async function handleSubmit() {
  if (selectedCases.value.length === 0) {
    Message.warning('请先选择用例')
    return
  }

  submitting.value = true
  try {
    const [width, height] = form.viewport.split('x').map(Number)
    const result = await createUIBatchRun({
      case_ids: selectedCases.value.map(c => c.id),
      environment_id: form.environment_id,
      failure_strategy: form.failure_strategy,
      browser: form.browser,
      viewport_width: width,
      viewport_height: height,
    })

    Message.success('任务已创建，开始执行')
    router.push({ name: 'ui-batch-run-detail', params: { runId: (result as any).id } })
  } catch (e: any) {
    Message.error(e?.detail || '创建失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadProjects()
})
</script>

<style scoped>
.ui-task-config {
  width: 100%;
}

.page-header {
  margin-bottom: 20px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-1);
  margin: 0 0 4px 0;
}

.page-desc {
  font-size: 13px;
  color: var(--color-text-3);
  margin: 0;
}

.text-gray {
  color: var(--color-text-4);
}
</style>

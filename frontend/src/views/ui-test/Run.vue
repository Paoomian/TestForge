<template>
  <div class="ui-task-config">
    <!-- 页面头部 -->
    <div class="page-header">
      <div>
        <h2 class="page-title">UI 任务配置</h2>
        <p class="page-desc">配置并执行 UI 自动化批量测试任务</p>
      </div>
    </div>

    <!-- 配置区域 -->
    <a-card :bordered="false" class="config-card">
      <a-form :model="form" layout="vertical">
        <!-- 选择用例 -->
        <a-form-item label="选择用例" required>
          <div class="case-selector">
            <a-button type="outline" @click="showCaseSelector = true">
              <template #icon><icon-plus /></template>
              选择用例 ({{ selectedCases.length }} 已选)
            </a-button>
            <div v-if="selectedCases.length > 0" class="selected-cases">
              <a-tag
                v-for="c in selectedCases"
                :key="c.id"
                closable
                @close="removeCase(c.id)"
              >
                {{ c.name }}
              </a-tag>
            </div>
          </div>
        </a-form-item>

        <!-- 执行环境 -->
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

        <!-- 失败策略 -->
        <a-form-item label="失败策略">
          <a-radio-group v-model="form.failure_strategy">
            <a-radio value="continue">继续执行后续用例</a-radio>
            <a-radio value="stop">遇到失败停止执行</a-radio>
          </a-radio-group>
        </a-form-item>

        <!-- 浏览器配置 -->
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="浏览器">
              <a-select v-model="form.browser">
                <a-option value="chrome">Chrome</a-option>
                <a-option value="firefox">Firefox</a-option>
                <a-option value="edge">Edge</a-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="视口尺寸">
              <a-select v-model="form.viewport">
                <a-option value="1280x720">1280 x 720</a-option>
                <a-option value="1920x1080">1920 x 1080</a-option>
                <a-option value="375x812">iPhone (375 x 812)</a-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>

        <!-- 执行按钮 -->
        <a-form-item>
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
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 用例选择弹窗 -->
    <a-modal
      v-model:visible="showCaseSelector"
      title="选择用例"
      :width="800"
      :footer="false"
    >
      <div class="case-selector-modal">
        <!-- 项目选择 -->
        <div class="project-filter">
          <a-select
            v-model="selectorProjectId"
            placeholder="选择项目"
            style="width: 200px"
            @change="loadCasesForSelector"
          >
            <a-option v-for="p in projects" :key="p.id" :value="p.id">
              {{ p.name }}
            </a-option>
          </a-select>
        </div>

        <!-- 用例列表 -->
        <a-table
          v-model:selectedKeys="selectorSelectedKeys"
          :data="selectorCases"
          :loading="selectorLoading"
          :pagination="false"
          :row-selection="{ type: 'checkbox' }"
          row-key="id"
          :scroll="{ y: 400 }"
        >
          <template #columns>
            <a-table-column title="用例名称" data-index="name" />
            <a-table-column title="步骤数" :width="100">
              <template #cell="{ record }">
                {{ record.steps?.length || 0 }} 步
              </template>
            </a-table-column>
          </template>
        </a-table>

        <!-- 确认按钮 -->
        <div class="selector-footer">
          <a-button @click="showCaseSelector = false">取消</a-button>
          <a-button type="primary" @click="confirmCaseSelection">
            确认选择 ({{ selectorSelectedKeys.length }})
          </a-button>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { IconPlus, IconPlayArrow } from '@arco-design/web-vue/es/icon'
import { getUICaseList, type UICase } from '@/api/uiCase'
import { getProjects, type Project } from '@/api/project'
import { getEnvironments } from '@/api/environment'
import type { Environment } from '@/api/apiTestCase'
import { createUIBatchRun } from '@/api/uiBatchRun'

const router = useRouter()

// 项目列表
const projects = ref<Project[]>([])
const environments = ref<Environment[]>([])
const envLoading = ref(false)

// 用例选择
const selectedCases = ref<UICase[]>([])
const showCaseSelector = ref(false)
const selectorProjectId = ref<number | null>(null)
const selectorCases = ref<UICase[]>([])
const selectorLoading = ref(false)
const selectorSelectedKeys = ref<number[]>([])

// 表单
const form = reactive({
  environment_id: undefined as number | undefined,
  failure_strategy: 'continue',
  browser: 'chrome',
  viewport: '1280x720',
})

// 提交状态
const submitting = ref(false)

// 加载项目列表
async function loadProjects() {
  try {
    projects.value = await getProjects()
    if (projects.value.length > 0) {
      selectorProjectId.value = projects.value[0].id
      loadCasesForSelector()
    }
  } catch (e) {
    console.error('加载项目列表失败:', e)
  }
}

// 加载用例列表（选择器用）
async function loadCasesForSelector() {
  if (!selectorProjectId.value) return
  selectorLoading.value = true
  try {
    const res = await getUICaseList(selectorProjectId.value, 0, 1000)
    selectorCases.value = (res as any) || []
  } catch (e) {
    console.error('加载用例列表失败:', e)
  } finally {
    selectorLoading.value = false
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

// 确认选择
function confirmCaseSelection() {
  const selected = selectorCases.value.filter(c => selectorSelectedKeys.value.includes(c.id))
  selectedCases.value = selected
  showCaseSelector.value = false
  // 加载环境
  loadEnvironments()
}

// 移除用例
function removeCase(caseId: number) {
  selectedCases.value = selectedCases.value.filter(c => c.id !== caseId)
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

.config-card {
  max-width: 800px;
}

.case-selector {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.selected-cases {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.case-selector-modal {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.project-filter {
  display: flex;
  gap: 12px;
}

.selector-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 16px;
}
</style>

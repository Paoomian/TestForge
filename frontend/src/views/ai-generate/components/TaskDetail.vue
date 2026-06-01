<template>
  <div class="task-detail">
    <!-- 任务信息 -->
    <div class="task-info">
      <a-descriptions :column="3" bordered>
        <a-descriptions-item label="任务 ID">{{ currentTask.id }}</a-descriptions-item>
        <a-descriptions-item label="输入类型">{{ getInputTypeText(currentTask.input_type) }}</a-descriptions-item>
        <a-descriptions-item label="生成类型">{{ getGenerateTypeText(currentTask.generate_type) }}</a-descriptions-item>
        <a-descriptions-item label="AI 模型">{{ currentTask.provider }} - {{ currentTask.model_name }}</a-descriptions-item>
        <a-descriptions-item label="生成数量">{{ currentTask.cases_count }}</a-descriptions-item>
        <a-descriptions-item label="状态">
          <a-tag :color="getStatusColor(currentTask.status)">
            {{ getStatusText(currentTask.status) }}
          </a-tag>
        </a-descriptions-item>
      </a-descriptions>
    </div>

    <!-- 进度显示（处理中或等待中时显示） -->
    <div class="progress-section" v-if="currentTask.status === 'processing' || currentTask.status === 'pending'">
      <a-card>
        <div class="progress-content">
          <a-progress
            :percent="currentTask.progress / 100"
            :status="currentTask.status === 'processing' ? 'active' : 'normal'"
          />
          <p class="stage-text">{{ currentTask.error_message || '等待中...' }}</p>
        </div>
      </a-card>
    </div>

    <!-- 用例列表 -->
    <div class="case-list" v-if="currentTask.status === 'completed'">
      <div class="case-header">
        <h3>生成的用例</h3>
        <a-space>
          <a-button @click="selectAll">全选</a-button>
          <a-button @click="selectNone">取消全选</a-button>
          <!-- 功能测试：只能导出Excel -->
          <a-button
            v-if="currentTask.generate_type === 'functional'"
            type="primary"
            :disabled="!selectedCases.length"
            @click="handleExportExcel"
          >
            导出 Excel ({{ selectedCases.length }})
          </a-button>
          <!-- 接口测试：保存到项目 + 导出Excel -->
          <template v-if="currentTask.generate_type === 'api'">
            <a-button type="primary" :disabled="!selectedCases.length" @click="handleSave">
              保存到项目 ({{ selectedCases.length }})
            </a-button>
            <a-button :disabled="!selectedCases.length" @click="handleExportExcel">
              导出 Excel ({{ selectedCases.length }})
            </a-button>
          </template>
        </a-space>
      </div>

      <a-table
        :columns="isFunctional ? functionalCaseColumns : apiCaseColumns"
        :data="cases"
        :pagination="{ pageSize: 10, showTotal: true }"
        :row-selection="{ type: 'checkbox' }"
        v-model:selectedKeys="selectedCases"
        row-key="_id"
      >
        <template #name="{ record, rowIndex }">
          <a @click="handleEditCase(rowIndex)">{{ record.name }}</a>
        </template>

        <template #priority="{ record }">
          <a-tag :color="getPriorityColor(record.priority)">
            {{ record.priority }}
          </a-tag>
        </template>

        <template #steps="{ record }">
          <div class="steps-cell" v-if="record.steps && record.steps.length">
            <ol>
              <li v-for="(step, idx) in record.steps" :key="idx">{{ stripStepNumber(step) }}</li>
            </ol>
          </div>
          <span v-else>-</span>
        </template>

        <template #expected_result="{ record }">
          <div class="expected-cell" v-if="record.expected_results && record.expected_results.length">
            <ol>
              <li v-for="(er, idx) in record.expected_results" :key="idx">{{ er }}</li>
            </ol>
          </div>
          <div class="expected-cell" v-else-if="record.expected_result">
            {{ record.expected_result }}
          </div>
          <span v-else>-</span>
        </template>

        <template #assertions="{ record }">
          <div class="assertions-cell" v-if="record.assertions && record.assertions.length">
            <a-tag v-for="(a, idx) in record.assertions.slice(0, 3)" :key="idx" size="small" class="assertion-tag">
              {{ a.assertion_type || a.type }}: {{ a.field || '' }} {{ a.operator }} {{ a.expected }}
            </a-tag>
            <a-tag v-if="record.assertions.length > 3" size="small">+{{ record.assertions.length - 3 }}</a-tag>
          </div>
          <span v-else>-</span>
        </template>

        <template #actions="{ rowIndex }">
          <a-button type="text" size="small" @click="handleEditCase(rowIndex)">
            编辑
          </a-button>
        </template>
      </a-table>
    </div>

    <!-- 错误信息 -->
    <div class="error-info" v-if="currentTask.status === 'failed'">
      <a-alert type="error" :content="currentTask.error_message || '未知错误'" />
    </div>

    <!-- 用例编辑弹窗 -->
    <a-modal
      v-model:visible="showCaseEditor"
      title="编辑用例"
      :width="800"
      @ok="handleSaveCase"
    >
      <CaseEditor
        v-if="editingCase"
        ref="caseEditorRef"
        :model-value="editingCase"
      />
    </a-modal>

    <!-- 保存配置弹窗 -->
    <a-modal
      v-model:visible="showSaveConfig"
      title="保存配置"
      @ok="confirmSave"
    >
      <a-form :model="{}" layout="vertical">
        <a-form-item label="目标项目" required>
          <a-select v-model="selectedProject" placeholder="请选择项目">
            <a-option
              v-for="project in projects"
              :key="project.id"
              :value="project.id"
            >
              {{ project.name }}
            </a-option>
          </a-select>
        </a-form-item>
        <div style="color: var(--color-text-3); font-size: 12px; margin-top: -8px;">
          模块将使用用例中已设置的所属模块
        </div>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { Message } from '@arco-design/web-vue'
import CaseEditor from './CaseEditor.vue'
import { getGeneratedCases, updateGeneratedCase, getGenerateTask } from '@/api/aiGenerate'
import type { AIGenerateTask } from '@/api/aiGenerate'

const props = defineProps<{
  task: AIGenerateTask
  projects?: { id: number; name: string }[]
}>()

const emit = defineEmits<{
  save: [taskId: number, caseIndices: number[], projectId: number]
}>()

// 状态
const currentTask = ref<AIGenerateTask>({ ...props.task })
const cases = ref<any[]>([])
const selectedCases = ref<number[]>([])
const showCaseEditor = ref(false)
const editingCase = ref<any>(null)
const editingIndex = ref(-1)
const caseEditorRef = ref<any>(null)
const showSaveConfig = ref(false)
const selectedProject = ref<number | undefined>()
let refreshTimer: number | null = null

// 是否功能测试类型
const isFunctional = computed(() => currentTask.value.generate_type === 'functional')

// 功能测试用例表格列
const functionalCaseColumns = [
  { title: '用例名称', dataIndex: 'name', slotName: 'name', width: 200 },
  { title: '优先级', dataIndex: 'priority', slotName: 'priority', width: 80 },
  { title: '操作步骤', dataIndex: 'steps', slotName: 'steps', width: 300 },
  { title: '预期结果', dataIndex: 'expected_result', slotName: 'expected_result', width: 250 },
  { title: '操作', slotName: 'actions', width: 80 }
]

// 接口测试用例表格列
const apiCaseColumns = [
  { title: '用例名称', dataIndex: 'name', slotName: 'name', width: 180 },
  { title: '请求方法', dataIndex: 'method', width: 80 },
  { title: '请求URL', dataIndex: 'url', ellipsis: true, width: 200 },
  { title: '优先级', dataIndex: 'priority', slotName: 'priority', width: 80 },
  { title: '断言', dataIndex: 'assertions', slotName: 'assertions', width: 250 },
  { title: '操作', slotName: 'actions', width: 80 }
]

// 刷新任务状态
const refreshTask = async () => {
  try {
    const result = await getGenerateTask(props.task.id)
    currentTask.value = result
    // 如果任务完成或失败，停止刷新并加载用例
    if (result.status === 'completed') {
      stopAutoRefresh()
      await loadCases()
    } else if (result.status === 'failed' || result.status === 'cancelled') {
      stopAutoRefresh()
    }
  } catch (error) {
    console.error('刷新任务状态失败:', error)
  }
}

// 启动自动刷新
const startAutoRefresh = () => {
  if (refreshTimer) return
  refreshTimer = window.setInterval(refreshTask, 2000) // 每2秒刷新
}

// 停止自动刷新
const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// 加载用例
const loadCases = async () => {
  try {
    const result = await getGeneratedCases(props.task.id)
    // 给每条用例添加唯一标识
    cases.value = result.cases.map((c: any, i: number) => ({ ...c, _id: i }))
  } catch (error) {
    console.error('加载用例失败:', error)
  }
}

// 选择操作
const selectAll = () => {
  selectedCases.value = cases.value.map((_, index) => index)
}

const selectNone = () => {
  selectedCases.value = []
}

// 编辑用例
const handleEditCase = (index: number) => {
  editingIndex.value = index
  // 深拷贝，避免修改原始数据
  editingCase.value = JSON.parse(JSON.stringify(cases.value[index]))
  showCaseEditor.value = true
}

const handleSaveCase = async () => {
  // 从 CaseEditor 获取最新数据
  const caseData = caseEditorRef.value?.getData() || { ...editingCase.value }

  // 过滤空步骤和空预期结果
  if (caseData.steps) {
    caseData.steps = caseData.steps.filter((s: string) => s.trim())
  }
  if (caseData.expected_results) {
    caseData.expected_results = caseData.expected_results.filter((s: string) => s.trim())
  }

  try {
    await updateGeneratedCase(props.task.id, editingIndex.value, caseData)
    cases.value[editingIndex.value] = JSON.parse(JSON.stringify(caseData))
    showCaseEditor.value = false
    Message.success('用例已更新')
  } catch (error) {
    Message.error('更新用例失败')
  }
}

// 保存到项目
const handleSave = () => {
  if (!selectedCases.value.length) {
    Message.warning('请先选择要保存的用例')
    return
  }
  showSaveConfig.value = true
}

// 导出Excel
const handleExportExcel = async () => {
  if (!selectedCases.value.length) {
    Message.warning('请先选择要导出的用例')
    return
  }
  try {
    const ExcelJS = await import('exceljs')
    const workbook = new ExcelJS.Workbook()
    workbook.creator = 'TestForge'
    workbook.created = new Date()

    const selectedData = selectedCases.value.map(i => cases.value[i]).filter(Boolean)

    // 辅助函数：将对象格式的headers/query_params转为数组格式
    const toArray = (data: any): any[] => {
      if (Array.isArray(data)) return data
      if (data && typeof data === 'object') {
        return Object.entries(data).map(([key, value]) => ({ key, value }))
      }
      return []
    }

    // 辅助函数：格式化断言
    const formatAssertion = (a: any): string => {
      const type = a.type || a.assertion_type || ''
      const field = a.field ? ` ${a.field}` : ''
      const operator = a.operator || ''
      const expected = a.expected || ''
      return `${type}${field} ${operator} ${expected}`
    }
    const isFunc = currentTask.value.generate_type === 'functional'

    if (isFunc) {
      // 功能测试用例导出
      const ws = workbook.addWorksheet('功能测试用例', {
        views: [{ state: 'frozen', ySplit: 1 }]
      })

      const headers = ['用例名称', '优先级', '前置条件', '测试步骤', '预期结果', '测试类型']
      ws.columns = [
        { width: 25 }, { width: 10 }, { width: 25 }, { width: 50 }, { width: 40 }, { width: 12 }
      ]

      const headerRow = ws.addRow(headers)
      headerRow.eachCell((cell) => {
        cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF4472C4' } }
        cell.font = { bold: true, color: { argb: 'FFFFFFFF' }, size: 11 }
        cell.alignment = { horizontal: 'center', vertical: 'middle' }
        cell.border = { top: { style: 'thin' }, bottom: { style: 'thin' }, left: { style: 'thin' }, right: { style: 'thin' } }
      })

      for (const c of selectedData) {
        const steps = (c.steps || []).map((s: string, i: number) => `${i + 1}. ${stripStepNumber(s)}`).join('\n')
        const expectedResult = c.expected_results && c.expected_results.length
          ? c.expected_results.map((er: string, i: number) => `${i + 1}. ${er}`).join('\n')
          : c.expected_result || ''
        const row = ws.addRow([
          c.name || '',
          c.priority || '',
          c.preconditions || '',
          steps,
          expectedResult,
          c.test_type || ''
        ])
        row.eachCell((cell) => {
          cell.alignment = { vertical: 'top', wrapText: true }
          cell.border = { top: { style: 'thin' }, bottom: { style: 'thin' }, left: { style: 'thin' }, right: { style: 'thin' } }
        })
      }
    } else {
      // 接口测试用例导出 - 按照导入模板格式
      const ws = workbook.addWorksheet('用例模板', {
        views: [{ state: 'frozen', ySplit: 1 }]
      })

      // 表头定义（与导入模板一致）
      const headers = ['用例名称', '请求方法', '请求URL', '所属模块', '优先级', '描述', '前置条件', 'Body类型', 'Body内容', '请求头', '查询参数', '断言', '数据提取', '备注']
      ws.columns = [
        { width: 25 }, { width: 10 }, { width: 35 }, { width: 15 }, { width: 10 },
        { width: 25 }, { width: 25 }, { width: 12 }, { width: 40 },
        { width: 40 }, { width: 30 }, { width: 60 }, { width: 50 }, { width: 20 }
      ]

      const headerRow = ws.addRow(headers)
      headerRow.eachCell((cell) => {
        cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF4472C4' } }
        cell.font = { bold: true, color: { argb: 'FFFFFFFF' }, size: 11 }
        cell.alignment = { horizontal: 'center', vertical: 'middle' }
        cell.border = { top: { style: 'thin' }, bottom: { style: 'thin' }, left: { style: 'thin' }, right: { style: 'thin' } }
      })

      // 辅助函数：将数组/对象格式的headers转为JSON对象字符串
      const headersToJson = (data: any): string => {
        const arr = toArray(data)
        if (arr.length === 0) return ''
        const obj: Record<string, string> = {}
        arr.forEach((h: any) => { if (h.key) obj[h.key] = h.value || '' })
        return JSON.stringify(obj)
      }

      // 辅助函数：将数组/对象格式的query_params转为JSON对象字符串
      const queryParamsToJson = (data: any): string => {
        const arr = toArray(data)
        if (arr.length === 0) return ''
        const obj: Record<string, string> = {}
        arr.forEach((p: any) => { if (p.key) obj[p.key] = p.value || '' })
        return JSON.stringify(obj)
      }

      // 辅助函数：将断言数组转为JSON字符串
      const assertionsToJson = (assertions: any[]): string => {
        if (!assertions || assertions.length === 0) return ''
        return JSON.stringify(assertions.map(a => ({
          type: a.type || a.assertion_type || '',
          ...(a.field ? { field: a.field } : {}),
          operator: a.operator || '',
          expected: a.expected || '',
          ...(a.description ? { description: a.description } : {})
        })))
      }

      // 辅助函数：将数据规则转为JSON字符串
      const dataRulesToJson = (rules: any[]): string => {
        if (!rules || rules.length === 0) return ''
        return JSON.stringify(rules.map(r => ({
          name: r.name || '',
          source: r.source || 'jsonpath',
          expression: r.expression || '',
          ...(r.default_value ? { default_value: r.default_value } : {}),
          ...(r.description ? { description: r.description } : {})
        })))
      }

      for (const c of selectedData) {
        const row = ws.addRow([
          c.name || '',
          c.method || '',
          c.url || '',
          c.module || '',
          c.priority || 'P2',
          c.description || '',
          c.preconditions || '',
          c.body_type || 'none',
          c.body_content || '',
          headersToJson(c.headers),
          queryParamsToJson(c.query_params),
          assertionsToJson(c.assertions || []),
          dataRulesToJson(c.data_rules || c.data_extract || []),
          c.remark || ''
        ])
        row.eachCell((cell) => {
          cell.alignment = { vertical: 'top', wrapText: true }
          cell.border = { top: { style: 'thin' }, bottom: { style: 'thin' }, left: { style: 'thin' }, right: { style: 'thin' } }
        })
      }
    }

    const buffer = await workbook.xlsx.writeBuffer()
    const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `AI生成用例_${isFunc ? '功能测试' : '接口测试'}_${new Date().toLocaleDateString('zh-CN')}.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    Message.success('导出成功')
  } catch (error) {
    Message.error('导出失败')
    console.error('导出Excel失败:', error)
  }
}

const confirmSave = () => {
  if (!selectedProject.value) {
    Message.warning('请选择目标项目')
    return
  }

  emit('save', props.task.id, selectedCases.value, selectedProject.value)
  showSaveConfig.value = false
}

// 辅助函数
const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    pending: 'blue',
    processing: 'orange',
    completed: 'green',
    failed: 'red',
    cancelled: 'gray'
  }
  return colors[status] || 'gray'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: '等待中',
    processing: '生成中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return texts[status] || status
}

const getInputTypeText = (type: string) => {
  const texts: Record<string, string> = {
    prd: 'PRD 文档',
    swagger: '接口文档',
    text: '文本输入'
  }
  return texts[type] || type
}

const getGenerateTypeText = (type: string) => {
  const texts: Record<string, string> = {
    functional: '功能测试',
    api: '接口测试'
  }
  return texts[type] || type
}

const getPriorityColor = (priority: string) => {
  const colors: Record<string, string> = {
    P0: 'red',
    P1: 'orange',
    P2: 'blue',
    P3: 'gray'
  }
  return colors[priority] || 'gray'
}

// 去除步骤文本中的前导序号（如 "1. xxx" → "xxx"）
const stripStepNumber = (step: string) => {
  return step.replace(/^\d+\.\s*/, '')
}

// 初始化
onMounted(async () => {
  // 先刷新一次任务状态，获取最新的错误信息
  await refreshTask()

  if (currentTask.value.status === 'completed') {
    loadCases()
  } else if (currentTask.value.status === 'processing' || currentTask.value.status === 'pending') {
    startAutoRefresh()
  }
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.task-detail {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.task-info {
  margin-bottom: 20px;
}

.progress-section {
  margin-bottom: 20px;
}

.progress-content {
  text-align: center;
  padding: 20px;
}

.stage-text {
  margin-top: 12px;
  color: #86909c;
  font-size: 14px;
}

.case-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.case-header h3 {
  margin: 0;
}

.error-info {
  margin-top: 20px;
}

.steps-cell ol {
  margin: 0;
  padding-left: 16px;
  font-size: 13px;
  line-height: 1.6;
}

.steps-cell li {
  margin-bottom: 2px;
}

.expected-cell {
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
}

.expected-cell ol {
  margin: 0;
  padding-left: 16px;
  font-size: 13px;
  line-height: 1.6;
}

.expected-cell li {
  margin-bottom: 2px;
}

.assertions-cell {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.assertion-tag {
  font-size: 11px;
}
</style>

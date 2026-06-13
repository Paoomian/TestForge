<template>
  <div class="scheduled-page">
    <!-- 顶部操作栏 -->
    <a-card :bordered="false" class="filter-card">
      <a-space :size="12">
        <a-select v-model="filterForm.task_type" placeholder="任务类型" style="width: 140px" allow-clear>
          <a-option value="api_batch">接口任务</a-option>
          <a-option value="ui_batch">UI任务</a-option>
        </a-select>
        <a-select v-model="filterForm.enabled" placeholder="状态" style="width: 120px" allow-clear>
          <a-option :value="true">启用</a-option>
          <a-option :value="false">禁用</a-option>
        </a-select>
        <a-button type="primary" @click="loadData">
          <template #icon><icon-search /></template>搜索
        </a-button>
        <a-button @click="resetFilter">重置</a-button>
        <a-button type="primary" status="success" @click="openDrawer()">
          <template #icon><icon-plus /></template>新建定时任务
        </a-button>
      </a-space>
    </a-card>

    <!-- 任务列表 -->
    <a-card :bordered="false" style="margin-top: 16px">
      <a-table :data="tableData" :loading="loading" :pagination="pagination"
        @page-change="onPageChange" @page-size-change="onPageSizeChange" :bordered="false" :stripe="true">
        <template #columns>
          <a-table-column title="任务名称" data-index="name" :width="160" :ellipsis="true">
            <template #cell="{ record }">
              <span :title="record.name">{{ record.name }}</span>
            </template>
          </a-table-column>
          <a-table-column title="类型" :width="90">
            <template #cell="{ record }">
              <a-tag :color="typeColorMap[record.task_type]" size="small">{{ typeTextMap[record.task_type] }}</a-tag>
            </template>
          </a-table-column>
          <a-table-column title="关联套件" data-index="suite_name" :width="160" :ellipsis="true">
            <template #cell="{ record }">
              <span :title="record.suite_name">{{ record.suite_name || '-' }}</span>
            </template>
          </a-table-column>
          <a-table-column title="执行计划" :width="130">
            <template #cell="{ record }">
              <span style="font-size: 13px">{{ formatCronText(record.cron_expression) }}</span>
            </template>
          </a-table-column>
          <a-table-column title="状态" :width="70">
            <template #cell="{ record }">
              <a-switch :model-value="record.enabled" @change="handleToggle(record)" size="small" />
            </template>
          </a-table-column>
          <a-table-column title="上次执行" :width="150">
            <template #cell="{ record }">
              {{ record.last_run_at ? formatTime(record.last_run_at) : '-' }}
            </template>
          </a-table-column>
          <a-table-column title="下次执行" :width="150">
            <template #cell="{ record }">
              {{ record.next_run_at ? formatTime(record.next_run_at) : '-' }}
            </template>
          </a-table-column>
          <a-table-column title="操作" :width="260" fixed="right">
            <template #cell="{ record }">
              <a-space>
                <a-button type="text" size="small" @click="openDrawer(record)">编辑</a-button>
                <a-button type="text" size="small" status="success" @click="handleRunNow(record)">立即执行</a-button>
                <a-button type="text" size="small" @click="viewRecords(record)">执行记录</a-button>
                <a-popconfirm content="确定删除该定时任务？" @ok="handleDelete(record)">
                  <a-button type="text" size="small" status="danger">删除</a-button>
                </a-popconfirm>
              </a-space>
            </template>
          </a-table-column>
        </template>
      </a-table>
    </a-card>

    <!-- 新建/编辑抽屉 -->
    <a-drawer :visible="drawerVisible" :title="editingId ? '编辑定时任务' : '新建定时任务'"
      :width="500" @cancel="drawerVisible = false" :footer="true">
      <a-form :model="form" layout="vertical" ref="formRef">
        <a-form-item label="任务名称" field="name" :rules="[{ required: true, message: '请输入任务名称' }]">
          <a-input v-model="form.name" placeholder="如：每日回归测试" />
        </a-form-item>
        <a-form-item label="任务类型" field="task_type" :rules="[{ required: true, message: '请选择任务类型' }]">
          <a-select v-model="form.task_type" placeholder="选择类型" @change="onTypeChange">
            <a-option value="api_batch">接口任务</a-option>
            <a-option value="ui_batch">UI任务</a-option>
          </a-select>
        </a-form-item>
        <a-form-item label="关联套件" field="suite_id" :rules="[{ required: true, message: '请选择套件' }]">
          <a-select v-model="form.suite_id" placeholder="选择测试套件" :loading="suitesLoading" filterable>
            <a-option v-for="s in suiteOptions" :key="s.id" :value="s.id">{{ s.name }}</a-option>
          </a-select>
        </a-form-item>
        <a-form-item label="执行频率" required>
          <a-select v-model="scheduleType" style="width: 100%">
            <a-option value="daily">每天</a-option>
            <a-option value="weekday">工作日</a-option>
            <a-option value="weekly">每周</a-option>
            <a-option value="interval">每隔一段时间</a-option>
          </a-select>
        </a-form-item>
        <a-form-item v-if="scheduleType === 'weekly'" label="执行日期">
          <a-select v-model="scheduleDay" style="width: 100%">
            <a-option :value="1">周一</a-option>
            <a-option :value="2">周二</a-option>
            <a-option :value="3">周三</a-option>
            <a-option :value="4">周四</a-option>
            <a-option :value="5">周五</a-option>
            <a-option :value="6">周六</a-option>
            <a-option :value="0">周日</a-option>
          </a-select>
        </a-form-item>
        <a-form-item v-if="scheduleType !== 'interval'" label="执行时间">
          <a-space>
            <a-select v-model="scheduleHour" style="width: 80px">
              <a-option v-for="h in 24" :key="h-1" :value="h-1">{{ String(h-1).padStart(2, '0') }}时</a-option>
            </a-select>
            <a-select v-model="scheduleMinute" style="width: 80px">
              <a-option :value="0">00分</a-option>
              <a-option :value="5">05分</a-option>
              <a-option :value="10">10分</a-option>
              <a-option :value="15">15分</a-option>
              <a-option :value="20">20分</a-option>
              <a-option :value="25">25分</a-option>
              <a-option :value="30">30分</a-option>
              <a-option :value="35">35分</a-option>
              <a-option :value="40">40分</a-option>
              <a-option :value="45">45分</a-option>
              <a-option :value="50">50分</a-option>
              <a-option :value="55">55分</a-option>
            </a-select>
          </a-space>
        </a-form-item>
        <a-form-item v-if="scheduleType === 'interval'" label="间隔">
          <a-space>
            <a-input-number v-model="intervalValue" :min="1" :max="24" style="width: 120px" />
            <a-select v-model="intervalUnit" style="width: 100px">
              <a-option value="hour">小时</a-option>
              <a-option value="minute">分钟</a-option>
            </a-select>
          </a-space>
        </a-form-item>
        <a-form-item label="并发数" field="concurrency">
          <a-select v-model="form.concurrency">
            <a-option :value="1">1</a-option>
            <a-option :value="3">3</a-option>
            <a-option :value="5">5</a-option>
            <a-option :value="10">10</a-option>
          </a-select>
        </a-form-item>
        <a-form-item label="失败策略" field="failure_strategy">
          <a-radio-group v-model="form.failure_strategy">
            <a-radio value="continue">继续执行</a-radio>
            <a-radio value="stop">遇到失败停止</a-radio>
          </a-radio-group>
        </a-form-item>
      </a-form>
      <template #footer>
        <a-space>
          <a-button @click="drawerVisible = false">取消</a-button>
          <a-button type="primary" :loading="submitting" @click="handleSubmit">确定</a-button>
        </a-space>
      </template>
    </a-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import {
  getScheduledTasks, createScheduledTask, updateScheduledTask,
  deleteScheduledTask, toggleScheduledTask, runScheduledTaskNow,
  getTestSuites, getUITestSuites,
  type ScheduledTask,
} from '@/api/scheduledTask'

const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const suitesLoading = ref(false)
const tableData = ref<ScheduledTask[]>([])
const drawerVisible = ref(false)
const editingId = ref<number | null>(null)
const suiteOptions = ref<{ id: number; name: string }[]>([])

// 执行计划相关
const scheduleType = ref('daily')
const scheduleDay = ref(1)
const scheduleHour = ref(9)
const scheduleMinute = ref(0)
const intervalValue = ref(2)
const intervalUnit = ref('hour')

const filterForm = reactive({
  task_type: undefined as string | undefined,
  enabled: undefined as boolean | undefined,
})

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showTotal: true,
  showJumper: true,
  showPageSize: true,
})

const form = reactive({
  name: '',
  task_type: 'api_batch' as string,
  suite_id: null as number | null,
  concurrency: 1,
  failure_strategy: 'continue',
})

/** 将可视化配置转为 Cron 表达式 */
function buildCron(): string {
  const h = String(scheduleHour.value)
  const m = String(scheduleMinute.value).padStart(2, '0')

  if (scheduleType.value === 'daily') {
    return `${m} ${h} * * *`
  }
  if (scheduleType.value === 'weekday') {
    return `${m} ${h} * * 1-5`
  }
  if (scheduleType.value === 'weekly') {
    return `${m} ${h} * * ${scheduleDay.value}`
  }
  if (scheduleType.value === 'interval') {
    if (intervalUnit.value === 'hour') {
      return `0 */${intervalValue.value} * * *`
    }
    return `*/${intervalValue.value} * * * *`
  }
  return `${m} ${h} * * *`
}

/** 将 Cron 表达式解析为可视化配置 */
function parseCron(cron: string) {
  const parts = cron.split(' ')
  if (parts.length !== 5) return

  const [m, h, , , dow] = parts

  // 间隔模式
  if (h.startsWith('*/')) {
    scheduleType.value = 'interval'
    intervalUnit.value = 'hour'
    intervalValue.value = parseInt(h.replace('*/', ''))
    return
  }
  if (m.startsWith('*/')) {
    scheduleType.value = 'interval'
    intervalUnit.value = 'minute'
    intervalValue.value = parseInt(m.replace('*/', ''))
    return
  }

  scheduleHour.value = parseInt(h) || 0
  scheduleMinute.value = parseInt(m) || 0

  if (dow === '1-5') {
    scheduleType.value = 'weekday'
  } else if (dow === '*') {
    scheduleType.value = 'daily'
  } else {
    scheduleType.value = 'weekly'
    scheduleDay.value = parseInt(dow)
  }
}

const typeColorMap: Record<string, string> = {
  api_batch: 'blue',
  ui_batch: 'green',
}

const typeTextMap: Record<string, string> = {
  api_batch: '接口任务',
  ui_batch: 'UI任务',
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await getScheduledTasks({
      page: pagination.current,
      page_size: pagination.pageSize,
      task_type: filterForm.task_type,
      enabled: filterForm.enabled,
    })
    tableData.value = res.items
    pagination.total = res.total
  } catch (e: any) {
    Message.error(e?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

const resetFilter = () => {
  filterForm.task_type = undefined
  filterForm.enabled = undefined
  pagination.current = 1
  loadData()
}

const onPageChange = (page: number) => {
  pagination.current = page
  loadData()
}

const onPageSizeChange = (pageSize: number) => {
  pagination.pageSize = pageSize
  pagination.current = 1
  loadData()
}

/** 加载套件选项 */
const loadSuites = async (type: string) => {
  suitesLoading.value = true
  try {
    if (type === 'ui_batch') {
      const res = await getUITestSuites()
      suiteOptions.value = res.items
    } else {
      const res = await getTestSuites()
      suiteOptions.value = res.items
    }
  } catch (e) {
    suiteOptions.value = []
  } finally {
    suitesLoading.value = false
  }
}

const onTypeChange = (val: string) => {
  form.suite_id = null
  loadSuites(val)
}

/** 打开抽屉 */
const openDrawer = (record?: ScheduledTask) => {
  if (record) {
    editingId.value = record.id
    form.name = record.name
    form.task_type = record.task_type
    form.suite_id = record.suite_id
    form.concurrency = record.concurrency
    form.failure_strategy = record.failure_strategy
    parseCron(record.cron_expression)
    loadSuites(record.task_type)
  } else {
    editingId.value = null
    form.name = ''
    form.task_type = 'api_batch'
    form.suite_id = null
    form.concurrency = 1
    form.failure_strategy = 'continue'
    scheduleType.value = 'daily'
    scheduleHour.value = 9
    scheduleMinute.value = 0
    intervalValue.value = 2
    intervalUnit.value = 'hour'
    loadSuites('api_batch')
  }
  drawerVisible.value = true
}

/** 提交 */
const handleSubmit = async () => {
  if (!form.name || !form.task_type || !form.suite_id) {
    Message.warning('请填写必填项')
    return
  }

  const cron = buildCron()

  submitting.value = true
  try {
    const data = {
      name: form.name,
      task_type: form.task_type,
      suite_id: form.suite_id!,
      concurrency: form.concurrency,
      failure_strategy: form.failure_strategy,
      cron_expression: cron,
      enabled: true,
    }

    if (editingId.value) {
      await updateScheduledTask(editingId.value, data)
      Message.success('更新成功')
    } else {
      await createScheduledTask(data)
      Message.success('创建成功')
    }
    drawerVisible.value = false
    loadData()
  } catch (e: any) {
    Message.error(e?.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

const handleToggle = async (record: ScheduledTask) => {
  try {
    await toggleScheduledTask(record.id)
    loadData()
  } catch (e: any) {
    Message.error(e?.message || '操作失败')
  }
}

const handleRunNow = async (record: ScheduledTask) => {
  try {
    await runScheduledTaskNow(record.id)
    Message.success('已提交执行')
  } catch (e: any) {
    Message.error(e?.message || '执行失败')
  }
}

const viewRecords = (record: ScheduledTask) => {
  // 定时任务执行时 name 格式为 [定时] 任务名-时间戳，跳转到报告列表
  router.push({ name: 'report-list' })
}

const handleDelete = async (record: ScheduledTask) => {
  try {
    await deleteScheduledTask(record.id)
    Message.success('删除成功')
    loadData()
  } catch (e: any) {
    Message.error(e?.message || '删除失败')
  }
}

const formatTime = (time: string) => {
  if (!time) return '-'
  return time.replace('T', ' ').slice(0, 16)
}

/** Cron 表达式转友好文本 */
const dayNames = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
function formatCronText(cron: string): string {
  if (!cron) return '-'
  const parts = cron.split(' ')
  if (parts.length !== 5) return cron
  const [m, h, , , dow] = parts
  const time = `${h.padStart(2, '0')}:${m.padStart(2, '0')}`

  if (h.startsWith('*/')) return `每隔 ${h.replace('*/', '')} 小时`
  if (m.startsWith('*/')) return `每隔 ${m.replace('*/', '')} 分钟`
  if (dow === '1-5') return `工作日 ${time}`
  if (dow === '*') return `每天 ${time}`
  return `每${dayNames[parseInt(dow)] || dow} ${time}`
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.scheduled-page {
  padding: 0;
}
</style>

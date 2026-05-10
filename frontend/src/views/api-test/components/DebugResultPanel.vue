<template>
  <div class="debug-result-panel">
    <!-- 顶部操作栏 -->
    <div class="action-bar">
      <!-- 只有一个环境时显示名称，多个时显示下拉 -->
      <div v-if="environments.length <= 1" class="env-display">
        <icon-desktop />
        <span>{{ environments[0]?.name || '未配置环境' }}</span>
      </div>
      <a-select
        v-else
        v-model="selectedEnvId"
        style="width: 200px"
      >
        <a-option v-for="env in environments" :key="env.id" :value="env.id">
          {{ env.name }}
        </a-option>
      </a-select>

      <a-popover trigger="click" position="bottom" :content-style="{ width: '360px' }">
        <a-button>
          <template #icon><icon-settings /></template>
          临时变量
          <a-badge v-if="tempVarCount" :count="tempVarCount" />
        </a-button>
        <template #content>
          <div class="temp-vars-popover">
            <div class="temp-vars-header">
              <span>临时变量（优先级最高）</span>
              <a-button type="text" size="mini" @click="addTempVar">
                <template #icon><icon-plus /></template>
              </a-button>
            </div>
            <div v-for="(v, i) in tempVars" :key="i" class="temp-var-row">
              <a-input v-model="v.key" placeholder="变量名" size="small" />
              <a-input v-model="v.value" placeholder="值" size="small" />
              <a-button type="text" size="mini" status="danger" @click="tempVars.splice(i, 1)">
                <template #icon><icon-delete /></template>
              </a-button>
            </div>
            <div v-if="!tempVars.length" class="temp-vars-empty">暂无临时变量</div>
          </div>
        </template>
      </a-popover>

      <a-button
        type="primary"
        :loading="running"
        @click="handleRun"
      >
        <template #icon><icon-play-arrow /></template>
        执行调试
      </a-button>
    </div>

    <!-- 结果区 -->
    <div class="result-area" ref="resultAreaRef">
      <!-- 空状态 -->
      <div v-if="!result && !running" class="empty-state">
        <div class="empty-icon">
          <icon-code-block :size="48" />
        </div>
        <p>选择环境后点击「执行调试」查看结果</p>
      </div>

      <!-- 执行中 -->
      <div v-if="running" class="loading-state">
        <a-spin :size="32" />
        <p>正在执行测试...</p>
      </div>

      <!-- 执行结果 -->
      <template v-if="result && !running">
        <!-- 状态行 -->
        <div class="status-bar" :class="`status-${result.status}`">
          <a-tag :color="statusColor" size="large">
            <template #icon>
              <icon-check-circle-fill v-if="result.status === 'pass'" />
              <icon-close-circle-fill v-else-if="result.status === 'fail'" />
              <icon-exclamation-circle-fill v-else />
            </template>
            {{ statusText }}
          </a-tag>
          <span class="status-info">
            <span v-if="result.response_info">
              状态码: <strong>{{ result.response_info.status_code }}</strong>
            </span>
            <span>耗时: <strong>{{ result.duration_ms }}ms</strong></span>
            <span v-if="result.response_info">
              大小: <strong>{{ formatSize(result.response_info.size_bytes) }}</strong>
            </span>
          </span>
        </div>

        <!-- 错误信息 -->
        <a-alert
          v-if="result.error_message"
          type="error"
          :content="result.error_message"
          style="margin-bottom: 16px"
          show-icon
        />

        <!-- 请求快照 -->
        <a-collapse :bordered="false" style="margin-bottom: 16px">
          <a-collapse-item header="实际请求（变量替换后）" key="request">
            <div class="snapshot-content">
              <div class="snapshot-line">
                <strong>{{ result.request_snapshot?.method }}</strong>
                {{ result.request_snapshot?.url }}
              </div>
              <div v-if="result.request_snapshot?.headers" class="snapshot-section">
                <div class="snapshot-label">Headers</div>
                <div v-for="(v, k) in result.request_snapshot.headers" :key="k" class="snapshot-kv">
                  <span class="snapshot-key">{{ k }}</span>
                  <span class="snapshot-value">{{ v }}</span>
                </div>
              </div>
              <div v-if="result.request_snapshot?.body" class="snapshot-section">
                <div class="snapshot-label">Body</div>
                <pre class="code-block">{{ formatJson(result.request_snapshot.body) }}</pre>
              </div>
            </div>
          </a-collapse-item>
        </a-collapse>

        <!-- 响应体 -->
        <div v-if="result.response_info" class="section">
          <div class="section-header">
            <span class="section-title">响应体</span>
            <a-button type="text" size="mini" @click="copyResponse">
              <template #icon><icon-copy /></template>
              复制
            </a-button>
          </div>
          <div class="response-body-wrapper">
            <pre class="response-body" v-html="highlightedBody"></pre>
            <div v-if="result.response_info.truncated" class="truncated-tip">
              响应体过大，已截断显示
            </div>
          </div>
        </div>

        <!-- 断言结果 -->
        <div v-if="result.assertions?.length" class="section">
          <div class="section-title">断言结果</div>
          <a-table
            :columns="assertionColumns"
            :data="result.assertions"
            :pagination="false"
            size="small"
            :row-class="(_record: any, index: number) => result!.assertions[index].passed ? 'assertion-pass' : 'assertion-fail'"
          >
            <template #status="{ record }">
              <a-tag :color="record.passed ? 'green' : 'red'" size="small">
                {{ record.passed ? '通过' : '失败' }}
              </a-tag>
            </template>
            <template #type="{ record }">
              <a-tag size="small">{{ assertionTypeMap[record.assertion_type] || record.assertion_type }}</a-tag>
            </template>
            <template #actual="{ record }">
              <span :class="{ 'value-mismatch': !record.passed }">{{ record.actual ?? '-' }}</span>
            </template>
            <template #expected="{ record }">
              <span>{{ record.expected }}</span>
            </template>
            <template #error="{ record }">
              <span v-if="record.error" class="error-text">{{ record.error }}</span>
              <span v-else>-</span>
            </template>
          </a-table>
        </div>

        <!-- 提取的变量 -->
        <div v-if="extractedVars.length" class="section">
          <div class="section-title">提取的变量</div>
          <div class="var-list">
            <div class="var-item" v-for="v in extractedVars" :key="v.name">
              <span class="var-name">{{ v.name }}</span>
              <span class="var-value">{{ v.value }}</span>
              <a-button type="text" size="mini" @click="copyText(v.value)">
                <template #icon><icon-copy /></template>
              </a-button>
            </div>
          </div>
        </div>

        <!-- 脚本输出 -->
        <div v-if="hasScriptOutput" class="section">
          <div class="section-title">脚本输出</div>
          <a-collapse :bordered="false">
            <a-collapse-item
              v-if="result.script_output.setup"
              header="前置脚本"
              key="setup"
            >
              <div v-for="(log, i) in result.script_output.setup.output" :key="i" class="script-log">{{ log }}</div>
              <div v-if="result.script_output.setup.error" class="script-error">{{ result.script_output.setup.error }}</div>
            </a-collapse-item>
            <a-collapse-item
              v-if="result.script_output.teardown"
              header="后置脚本"
              key="teardown"
            >
              <div v-for="(log, i) in result.script_output.teardown.output" :key="i" class="script-log">{{ log }}</div>
              <div v-if="result.script_output.teardown.error" class="script-error">{{ result.script_output.teardown.error }}</div>
            </a-collapse-item>
          </a-collapse>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { Message } from '@arco-design/web-vue'
import { runTestCase } from '@/api/apiTestCase'
import { getEnvironments } from '@/api/environment'
import type { APITestCase, RunResult } from '@/api/apiTestCase'
import type { Environment } from '@/api/apiTestCase'

const props = defineProps<{
  caseData: APITestCase
}>()

const running = ref(false)
const result = ref<RunResult | null>(null)
const resultAreaRef = ref<HTMLElement>()
const environments = ref<Environment[]>([])
const selectedEnvId = ref<number>()

interface TempVar { key: string; value: string }
const tempVars = ref<TempVar[]>([])
const tempVarCount = computed(() => tempVars.value.filter(v => v.key).length)

const statusColor = computed(() => {
  if (!result.value) return 'gray'
  return { pass: 'green', fail: 'red', error: 'orange' }[result.value.status] || 'gray'
})

const statusText = computed(() => {
  if (!result.value) return ''
  return { pass: '全部通过', fail: '断言失败', error: '执行异常' }[result.value.status] || ''
})

// 断言类型中文映射
const assertionTypeMap: Record<string, string> = {
  status_code: '状态码',
  jsonpath: 'JSONPath',
  header: '响应头',
  response_time: '响应时间',
  body_contains: 'Body包含'
}

const extractedVars = computed(() => {
  if (!result.value?.extracted_variables) return []
  return Object.entries(result.value.extracted_variables).map(([name, value]) => ({ name, value }))
})

const hasScriptOutput = computed(() => {
  const so = result.value?.script_output
  return so && (so.setup || so.teardown)
})

const highlightedBody = computed(() => {
  const body = result.value?.response_info?.body
  if (!body) return ''
  try {
    const parsed = JSON.parse(body)
    return syntaxHighlight(JSON.stringify(parsed, null, 2))
  } catch {
    return escapeHtml(body)
  }
})

const assertionColumns = [
  { title: '状态', dataIndex: 'passed', slotName: 'status', width: 80 },
  { title: '类型', dataIndex: 'assertion_type', slotName: 'type', width: 120 },
  { title: '实际值', dataIndex: 'actual', slotName: 'actual', ellipsis: true },
  { title: '期望值', dataIndex: 'expected', slotName: 'expected', ellipsis: true },
  { title: '错误', dataIndex: 'error', slotName: 'error', ellipsis: true },
]

// 加载环境列表，优先使用用例保存的环境，否则选中第一个
watch(() => props.caseData.project_id, async (projectId) => {
  if (projectId) {
    try {
      environments.value = await getEnvironments(projectId)
      syncSelectedEnv()
    } catch {
      environments.value = []
    }
  }
}, { immediate: true })

// 监听用例environment_id变化
watch(() => props.caseData.environment_id, () => {
  syncSelectedEnv()
})

function syncSelectedEnv() {
  // 优先使用用例保存的environment_id
  if (props.caseData.environment_id) {
    const savedEnv = environments.value.find(e => e.id === props.caseData.environment_id)
    if (savedEnv) {
      selectedEnvId.value = savedEnv.id
      return
    }
  }
  // 否则默认选中第一个
  if (environments.value.length > 0 && !selectedEnvId.value) {
    selectedEnvId.value = environments.value[0].id
  }
}

const addTempVar = () => {
  tempVars.value.push({ key: '', value: '' })
}

const handleRun = async () => {
  running.value = true
  result.value = null

  const variables: Record<string, string> = {}
  for (const v of tempVars.value) {
    if (v.key) variables[v.key] = v.value
  }

  try {
    result.value = await runTestCase(props.caseData.id, {
      environment_id: selectedEnvId.value,
      variables
    })

    // 滚动到结果区
    await nextTick()
    resultAreaRef.value?.scrollTo({ top: 0, behavior: 'smooth' })
  } catch (e: any) {
    result.value = {
      status: 'error',
      error_message: e.response?.data?.detail || e.message || '执行失败',
      assertions: [],
      extracted_variables: {},
      script_output: {},
      duration_ms: 0
    }
  } finally {
    running.value = false
  }
}

const formatSize = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

const formatJson = (data: any) => {
  if (typeof data === 'string') return data
  try { return JSON.stringify(data, null, 2) } catch { return String(data) }
}

const syntaxHighlight = (json: string) => {
  return json.replace(/("(\\u[\da-fA-F]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)/g, (match) => {
    let cls = 'json-number'
    if (/^"/.test(match)) {
      cls = /:$/.test(match) ? 'json-key' : 'json-string'
    } else if (/true|false/.test(match)) {
      cls = 'json-boolean'
    } else if (/null/.test(match)) {
      cls = 'json-null'
    }
    return `<span class="${cls}">${match}</span>`
  })
}

const escapeHtml = (str: string) => {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

const copyText = (text: string) => {
  navigator.clipboard.writeText(text)
  Message.success('已复制')
}

const copyResponse = () => {
  const body = result.value?.response_info?.body
  if (body) copyText(body)
}
</script>

<style scoped>
.debug-result-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.action-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: white;
  border-bottom: 1px solid var(--gray-200);
  flex-shrink: 0;
}

.env-display {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  background: var(--primary-50);
  border: 1px solid var(--primary-200);
  border-radius: var(--radius-md);
  color: var(--primary-600);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.result-area {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.empty-state, .loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: var(--gray-400);
}

.empty-state p, .loading-state p {
  margin-top: 12px;
  font-size: var(--font-size-sm);
}

/* 状态行 */
.status-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  border-radius: var(--radius-md);
  margin-bottom: 16px;
}

.status-bar.status-pass { background: var(--success-light); border: 1px solid #bbf7d0; }
.status-bar.status-fail { background: var(--danger-light); border: 1px solid #fecaca; }
.status-bar.status-error { background: var(--warning-light); border: 1px solid #fed7aa; }

.status-info {
  display: flex;
  gap: 20px;
  font-size: var(--font-size-sm);
  color: var(--gray-600);
}

.status-info strong {
  color: var(--gray-800);
}

/* 区块 */
.section {
  margin-bottom: 16px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.section-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--gray-600);
  margin-bottom: 8px;
}

/* 响应体 */
.response-body-wrapper {
  position: relative;
  max-height: 400px;
  overflow: auto;
  border-radius: var(--radius-md);
  background: var(--gray-800);
}

.response-body {
  padding: 16px;
  font-family: monospace;
  font-size: var(--font-size-xs);
  color: #e5e7eb;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}

.truncated-tip {
  position: sticky;
  bottom: 0;
  text-align: center;
  padding: 6px;
  background: var(--warning-light);
  color: var(--warning-dark);
  font-size: var(--font-size-xs);
}

:deep(.json-key) { color: #93c5fd; }
:deep(.json-string) { color: #86efac; }
:deep(.json-number) { color: #fcd34d; }
:deep(.json-boolean) { color: #c4b5fd; }
:deep(.json-null) { color: #9ca3af; }

/* 请求快照 */
.snapshot-content {
  font-size: var(--font-size-sm);
}

.snapshot-line {
  padding: 8px 12px;
  background: var(--gray-50);
  border-radius: var(--radius-sm);
  margin-bottom: 8px;
  font-family: monospace;
  word-break: break-all;
}

.snapshot-section {
  margin-bottom: 8px;
}

.snapshot-label {
  font-size: var(--font-size-xs);
  color: var(--gray-500);
  margin-bottom: 4px;
  font-weight: var(--font-weight-medium);
}

.snapshot-kv {
  display: flex;
  padding: 4px 12px;
  font-family: monospace;
  font-size: var(--font-size-xs);
}

.snapshot-key {
  width: 200px;
  flex-shrink: 0;
  color: var(--gray-600);
}

.snapshot-value {
  color: var(--gray-500);
  word-break: break-all;
}

.code-block {
  background: var(--gray-800);
  color: #e5e7eb;
  padding: 12px;
  border-radius: var(--radius-md);
  font-size: var(--font-size-xs);
  font-family: monospace;
  overflow-x: auto;
  margin: 0;
  white-space: pre-wrap;
}

/* 断言表格 */
:deep(.assertion-pass td) {
  background: var(--success-light) !important;
}

:deep(.assertion-fail td) {
  background: var(--danger-light) !important;
}

.value-mismatch {
  color: var(--danger-main);
  font-weight: var(--font-weight-semibold);
}

.error-text {
  color: var(--danger-main);
  font-size: var(--font-size-xs);
}

/* 变量列表 */
.var-list {
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.var-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid var(--gray-100);
}

.var-item:last-child {
  border-bottom: none;
}

.var-name {
  width: 160px;
  flex-shrink: 0;
  font-weight: var(--font-weight-medium);
  color: var(--primary-600);
  font-family: monospace;
  font-size: var(--font-size-sm);
}

.var-value {
  flex: 1;
  color: var(--gray-600);
  font-family: monospace;
  font-size: var(--font-size-sm);
  word-break: break-all;
}

/* 脚本输出 */
.script-log {
  padding: 4px 0;
  font-family: monospace;
  font-size: var(--font-size-xs);
  color: var(--gray-600);
}

.script-error {
  color: var(--danger-main);
  font-family: monospace;
  font-size: var(--font-size-xs);
}

/* 临时变量弹出层 */
.temp-vars-popover {
  padding: 12px;
}

.temp-vars-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.temp-var-row {
  display: flex;
  gap: 6px;
  margin-bottom: 6px;
}

.temp-vars-empty {
  text-align: center;
  color: var(--gray-400);
  font-size: var(--font-size-sm);
  padding: 12px 0;
}
</style>

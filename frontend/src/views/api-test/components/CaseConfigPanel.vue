<template>
  <div class="case-config-panel">
    <!-- 请求行 -->
    <div class="section">
      <div class="request-line">
        <a-tag :color="methodColor" size="large">{{ caseData.method }}</a-tag>
        <span class="url-text" v-html="highlightVars(caseData.url)"></span>
      </div>
    </div>

    <!-- 基本信息 -->
    <div class="section">
      <div class="section-title">基本信息</div>
      <a-descriptions :column="2" size="small" bordered>
        <a-descriptions-item label="编号">{{ caseData.case_number || '-' }}</a-descriptions-item>
        <a-descriptions-item label="模块">{{ caseData.module || '-' }}</a-descriptions-item>
        <a-descriptions-item label="优先级">
          <a-tag :color="priorityColor">{{ caseData.priority }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="Body类型">
          <a-tag>{{ caseData.body_type }}</a-tag>
        </a-descriptions-item>
      </a-descriptions>
    </div>

    <!-- Headers -->
    <div class="section" v-if="enabledHeaders.length">
      <div class="section-title">请求头 (Headers)</div>
      <div class="kv-list">
        <div class="kv-row" v-for="h in enabledHeaders" :key="h.key">
          <span class="kv-key">{{ h.key }}</span>
          <span class="kv-value" v-html="highlightVars(h.value)"></span>
        </div>
      </div>
    </div>

    <!-- Query Params -->
    <div class="section" v-if="enabledParams.length">
      <div class="section-title">查询参数 (Query Params)</div>
      <div class="kv-list">
        <div class="kv-row" v-for="p in enabledParams" :key="p.key">
          <span class="kv-key">{{ p.key }}</span>
          <span class="kv-value" v-html="highlightVars(p.value)"></span>
        </div>
      </div>
    </div>

    <!-- Body -->
    <div class="section" v-if="bodyContent">
      <div class="section-title">请求体 (Body)</div>
      <div class="body-preview">
        <pre class="code-block">{{ bodyContent }}</pre>
      </div>
    </div>

    <!-- Auth -->
    <div class="section" v-if="caseData.auth && caseData.auth.auth_type !== 'none'">
      <div class="section-title">认证 (Auth)</div>
      <a-descriptions :column="2" size="small" bordered>
        <a-descriptions-item label="类型">
          <a-tag>{{ caseData.auth.auth_type }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item v-if="caseData.auth.token" label="Token">****</a-descriptions-item>
        <a-descriptions-item v-if="caseData.auth.username" label="用户名">{{ caseData.auth.username }}</a-descriptions-item>
        <a-descriptions-item v-if="caseData.auth.api_key_name" label="Key名">{{ caseData.auth.api_key_name }}</a-descriptions-item>
      </a-descriptions>
    </div>

    <!-- 断言 -->
    <div class="section" v-if="caseData.assertions?.length">
      <div class="section-title">断言规则 ({{ caseData.assertions.length }})</div>
      <div class="assertion-list">
        <div class="assertion-item" v-for="(a, i) in caseData.assertions" :key="i">
          <span class="assertion-index">#{{ i + 1 }}</span>
          <a-tag size="small">{{ assertionTypeMap[a.assertion_type] || a.assertion_type }}</a-tag>
          <span class="assertion-op">{{ operatorMap[a.operator] || a.operator }}</span>
          <span v-if="a.field" class="assertion-field">{{ a.field }}</span>
          <span class="assertion-expected">期望: {{ a.expected }}</span>
        </div>
      </div>
    </div>

    <!-- 脚本 -->
    <div class="section" v-if="caseData.setup_script || caseData.teardown_script">
      <div class="section-title">脚本</div>
      <a-collapse :bordered="false">
        <a-collapse-item v-if="caseData.setup_script" header="前置脚本" key="setup">
          <pre class="code-block">{{ caseData.setup_script }}</pre>
        </a-collapse-item>
        <a-collapse-item v-if="caseData.teardown_script" header="后置脚本" key="teardown">
          <pre class="code-block">{{ caseData.teardown_script }}</pre>
        </a-collapse-item>
      </a-collapse>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { APITestCase } from '@/api/apiTestCase'

const props = defineProps<{ caseData: APITestCase }>()

const methodColors: Record<string, string> = {
  GET: 'blue', POST: 'green', PUT: 'orange', DELETE: 'red', PATCH: 'purple'
}
const methodColor = computed(() => methodColors[props.caseData.method] || 'gray')

const priorityColors: Record<string, string> = {
  P0: 'red', P1: 'orange', P2: 'blue', P3: 'green'
}
const priorityColor = computed(() => priorityColors[props.caseData.priority] || 'gray')

// 断言类型中文映射
const assertionTypeMap: Record<string, string> = {
  status_code: '状态码',
  jsonpath: 'JSONPath',
  header: '响应头',
  response_time: '响应时间',
  body_contains: 'Body包含'
}

// 比较方式中文映射
const operatorMap: Record<string, string> = {
  equals: '等于',
  not_equals: '不等于',
  contains: '包含',
  greater_than: '大于',
  less_than: '小于',
  regex: '正则匹配',
  exists: '存在'
}

// 变量来源中文映射
const sourceMap: Record<string, string> = {
  jsonpath: 'JSONPath',
  regex: '正则',
  header: '响应头'
}

const enabledHeaders = computed(() => (props.caseData.headers || []).filter(h => h.enabled))
const enabledParams = computed(() => (props.caseData.query_params || []).filter(p => p.enabled))

const bodyContent = computed(() => {
  const c = props.caseData
  if (c.body_type === 'none') return ''
  if (c.body_raw?.content) return c.body_raw.content
  if ((c.body_type === 'form-data' || c.body_type === 'x-www-form-urlencoded') && c.body_form?.length) {
    return c.body_form.filter(f => f.enabled).map(f => `${f.key}=${f.value}`).join('\n')
  }
  return ''
})

const highlightVars = (text: string) => {
  if (!text) return ''
  return text.replace(/\{\{(\w+)\}\}/g, '<span class="var-highlight">{{$1}}</span>')
}
</script>

<style scoped>
.case-config-panel {
  padding: 16px;
  overflow-y: auto;
  height: 100%;
}

.section {
  margin-bottom: 20px;
}

.section-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--gray-600);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.request-line {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--gray-50);
  border-radius: var(--radius-md);
  border: 1px solid var(--gray-200);
}

.url-text {
  font-family: monospace;
  font-size: var(--font-size-sm);
  word-break: break-all;
  color: var(--gray-700);
}

:deep(.var-highlight) {
  background: var(--primary-100);
  color: var(--primary-600);
  padding: 1px 4px;
  border-radius: 3px;
  font-weight: 500;
}

.kv-list {
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.kv-row {
  display: flex;
  padding: 8px 12px;
  border-bottom: 1px solid var(--gray-100);
  font-size: var(--font-size-sm);
}

.kv-row:last-child {
  border-bottom: none;
}

.kv-key {
  width: 160px;
  flex-shrink: 0;
  font-weight: var(--font-weight-medium);
  color: var(--gray-700);
  font-family: monospace;
}

.kv-value {
  flex: 1;
  color: var(--gray-600);
  word-break: break-all;
  font-family: monospace;
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
  word-break: break-all;
}

.assertion-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.assertion-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--gray-50);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
}

.assertion-index {
  color: var(--gray-400);
  font-size: var(--font-size-xs);
  width: 24px;
}

.assertion-op {
  color: var(--gray-600);
  font-family: monospace;
}

.assertion-field {
  color: var(--primary-600);
  font-family: monospace;
  font-size: var(--font-size-xs);
}

.assertion-expected {
  color: var(--gray-500);
  margin-left: auto;
}

.extract-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.extract-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--gray-50);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
}

.extract-name {
  font-weight: var(--font-weight-medium);
  color: var(--gray-700);
}

.extract-expr {
  color: var(--gray-500);
  font-family: monospace;
  font-size: var(--font-size-xs);
}

.body-preview {
  max-height: 200px;
  overflow-y: auto;
}
</style>

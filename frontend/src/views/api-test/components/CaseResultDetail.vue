<template>
  <a-drawer
    :width="900"
    :visible="visible"
    title="用例执行详情"
    @update:visible="$emit('update:visible', $event)"
  >
    <template v-if="detail">
      <!-- 基本信息 -->
      <div class="detail-header">
        <div class="detail-title">
          <span class="case-number">{{ detail.case_number }}</span>
          <span class="case-name">{{ detail.case_name }}</span>
        </div>
        <a-tag :color="statusColor" size="large">
          <template #icon>
            <icon-check-circle-fill v-if="detail.status === 'pass'" />
            <icon-close-circle-fill v-else-if="detail.status === 'fail'" />
            <icon-exclamation-circle-fill v-else-if="detail.status === 'error'" />
            <icon-minus-circle v-else />
          </template>
          {{ statusText }}
        </a-tag>
      </div>

      <!-- 执行信息 -->
      <a-descriptions :column="2" style="margin-bottom: 16px">
        <a-descriptions-item label="执行顺序">{{ detail.execution_order }}</a-descriptions-item>
        <a-descriptions-item label="接口耗时">
          <span class="api-time">{{ detail.response_info?.elapsed_ms ?? '-' }}ms</span>
        </a-descriptions-item>
        <a-descriptions-item label="总耗时">{{ detail.duration_ms }}ms</a-descriptions-item>
        <a-descriptions-item label="状态码">
          <a-tag v-if="detail.response_info" :color="detail.response_info.status_code < 400 ? 'green' : 'red'">
            {{ detail.response_info.status_code }}
          </a-tag>
          <span v-else>-</span>
        </a-descriptions-item>
        <a-descriptions-item label="开始时间">{{ formatTime(detail.started_at) }}</a-descriptions-item>
        <a-descriptions-item label="结束时间">{{ formatTime(detail.finished_at) }}</a-descriptions-item>
      </a-descriptions>

      <!-- 错误信息 -->
      <a-alert
        v-if="detail.error_message"
        type="error"
        :content="detail.error_message"
        style="margin-bottom: 16px"
        show-icon
      />

      <!-- 请求快照 -->
      <a-collapse :bordered="false" style="margin-bottom: 16px">
        <a-collapse-item header="请求快照" key="request">
          <div v-if="detail.request_snapshot" class="snapshot-content">
            <div class="snapshot-line">
              <strong>{{ detail.request_snapshot.method }}</strong>
              {{ detail.request_snapshot.url }}
            </div>
            <div v-if="detail.request_snapshot.params && Object.keys(detail.request_snapshot.params).length" class="snapshot-section">
              <div class="snapshot-label">Query Params</div>
              <div v-for="(v, k) in detail.request_snapshot.params" :key="k" class="snapshot-kv">
                <span class="snapshot-key">{{ k }}</span>
                <span class="snapshot-value">{{ v }}</span>
              </div>
            </div>
            <div v-if="detail.request_snapshot.headers" class="snapshot-section">
              <div class="snapshot-label">Headers</div>
              <div v-for="(v, k) in detail.request_snapshot.headers" :key="k" class="snapshot-kv">
                <span class="snapshot-key">{{ k }}</span>
                <span class="snapshot-value">{{ v }}</span>
              </div>
            </div>
            <div v-if="detail.request_snapshot.body" class="snapshot-section">
              <div class="snapshot-label">Body</div>
              <pre class="code-block">{{ formatJson(detail.request_snapshot.body) }}</pre>
            </div>
          </div>
          <a-empty v-else description="无请求快照" />
        </a-collapse-item>
      </a-collapse>

      <!-- 响应信息 -->
      <a-collapse :bordered="false" style="margin-bottom: 16px">
        <a-collapse-item header="响应信息" key="response">
          <div v-if="detail.response_info" class="snapshot-content">
            <a-descriptions :column="3" style="margin-bottom: 12px">
              <a-descriptions-item label="状态码">
                <a-tag :color="detail.response_info.status_code < 400 ? 'green' : 'red'">
                  {{ detail.response_info.status_code }}
                </a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="耗时">{{ detail.response_info.elapsed_ms }}ms</a-descriptions-item>
              <a-descriptions-item label="大小">{{ formatSize(detail.response_info.size_bytes) }}</a-descriptions-item>
            </a-descriptions>
            <div class="snapshot-section">
              <div class="snapshot-label">响应体</div>
              <JsonViewer :content="detail.response_info.body" max-height="300px" />
            </div>
          </div>
          <a-empty v-else description="无响应信息" />
        </a-collapse-item>
      </a-collapse>

      <!-- 断言结果 -->
      <a-collapse v-if="detail.assertions?.length" :bordered="false" style="margin-bottom: 16px">
        <a-collapse-item header="断言结果" key="assertions">
          <a-table
            :columns="assertionColumns"
            :data="detail.assertions"
            :pagination="false"
            size="small"
          >
            <template #assertion_type="{ record }">
              {{ getAssertionTypeText(record.assertion_type) }}
            </template>
            <template #operator="{ record }">
              {{ getOperatorText(record.operator) }}
            </template>
            <template #passed="{ record }">
              <a-tag :color="record.passed ? 'green' : 'red'" size="small">
                {{ record.passed ? '通过' : '失败' }}
              </a-tag>
            </template>
          </a-table>
        </a-collapse-item>
      </a-collapse>

      <!-- 提取的变量 -->
      <a-collapse v-if="Object.keys(detail.extracted_vars).length" :bordered="false" style="margin-bottom: 16px">
        <a-collapse-item header="提取的变量" key="extracts">
          <div v-for="(v, k) in detail.extracted_vars" :key="k" class="snapshot-kv">
            <span class="snapshot-key">{{ k }}</span>
            <span class="snapshot-value">{{ v }}</span>
          </div>
        </a-collapse-item>
      </a-collapse>

      <!-- 脚本输出 -->
      <a-collapse v-if="Object.keys(detail.script_output).length" :bordered="false">
        <a-collapse-item header="脚本输出" key="scripts">
          <div v-for="(output, name) in detail.script_output" :key="name" class="script-output-item">
            <div class="script-name">{{ name }}</div>
            <a-tag :color="output.success ? 'green' : 'red'" size="small" style="margin-bottom: 8px">
              {{ output.success ? '成功' : '失败' }}
            </a-tag>
            <pre v-if="output.output" class="code-block">{{ output.output }}</pre>
            <pre v-if="output.error" class="code-block error">{{ output.error }}</pre>
          </div>
        </a-collapse-item>
      </a-collapse>
    </template>

    <a-spin v-else-if="loading" :size="32" style="display: flex; justify-content: center; padding: 40px" />

    <template #footer>
      <a-button @click="$emit('update:visible', false)">关闭</a-button>
    </template>
  </a-drawer>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import JsonViewer from '@/components/JsonViewer.vue'
import { getBatchRunDetail } from '@/api/batchRun'
import type { CaseDetailFull } from '@/api/batchRun'

interface Props {
  visible: boolean
  runId: number
  detailId: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
}>()

const loading = ref(false)
const detail = ref<CaseDetailFull | null>(null)

watch(() => props.visible, async (val) => {
  if (val && props.runId && props.detailId) {
    await loadDetail()
  }
})

const loadDetail = async () => {
  loading.value = true
  try {
    detail.value = await getBatchRunDetail(props.runId, props.detailId)
  } catch (e) {
    console.error('加载详情失败:', e)
  } finally {
    loading.value = false
  }
}

const statusColor = computed(() => {
  const colors: Record<string, string> = {
    pass: 'green', fail: 'red', error: 'orange', pending: 'gray', running: 'blue', skipped: 'gray'
  }
  return colors[detail.value?.status || ''] || 'gray'
})

const statusText = computed(() => {
  const texts: Record<string, string> = {
    pass: '通过', fail: '失败', error: '错误', pending: '待执行', running: '执行中', skipped: '已跳过'
  }
  return texts[detail.value?.status || ''] || detail.value?.status || ''
})

const assertionTypeMap: Record<string, string> = {
  status_code: '状态码',
  jsonpath: 'JSONPath',
  response_time: '响应时间(ms)',
  header: '响应头',
  body_contains: 'Body包含'
}

const operatorMap: Record<string, string> = {
  equals: '等于',
  not_equals: '不等于',
  contains: '包含',
  greater_than: '大于',
  less_than: '小于',
  regex: '正则匹配',
  exists: '存在'
}

const getAssertionTypeText = (type: string) => assertionTypeMap[type] || type
const getOperatorText = (op: string) => operatorMap[op] || op

const assertionColumns = [
  { title: '断言类型', dataIndex: 'assertion_type', slotName: 'assertion_type', width: 100 },
  { title: '字段', dataIndex: 'field', width: 120 },
  { title: '比较方式', dataIndex: 'operator', slotName: 'operator', width: 100 },
  { title: '预期值', dataIndex: 'expected', width: 120 },
  { title: '实际值', dataIndex: 'actual', width: 120 },
  { title: '结果', dataIndex: 'passed', slotName: 'passed', width: 80 }
]

const formatTime = (time?: string) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const formatJson = (data: any) => {
  if (typeof data === 'string') {
    try {
      return JSON.stringify(JSON.parse(data), null, 2)
    } catch {
      return data
    }
  }
  return JSON.stringify(data, null, 2)
}

const formatSize = (bytes?: number) => {
  if (!bytes) return '-'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

</script>

<style scoped>
.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-border-2);
}

.detail-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.case-number {
  font-size: 13px;
  color: var(--color-text-3);
}

.case-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-1);
}

.snapshot-content {
  font-size: 13px;
}

.snapshot-line {
  padding: 8px 0;
  word-break: break-all;
}

.snapshot-section {
  margin-top: 12px;
}

.snapshot-label {
  font-weight: 600;
  color: var(--color-text-2);
  margin-bottom: 8px;
  font-size: 12px;
  text-transform: uppercase;
}

.snapshot-kv {
  display: flex;
  padding: 4px 0;
  border-bottom: 1px solid var(--color-border-1);
}

.snapshot-key {
  width: 180px;
  color: var(--color-text-3);
  flex-shrink: 0;
  font-size: 12px;
}

.snapshot-value {
  flex: 1;
  word-break: break-all;
  font-size: 12px;
}

.code-block {
  background: var(--color-fill-1);
  padding: 12px;
  border-radius: var(--radius-small);
  overflow-x: auto;
  font-size: 12px;
  line-height: 1.6;
  margin: 0;
}

.code-block.error {
  color: var(--color-danger-6);
}

.script-output-item {
  padding: 12px 0;
  border-bottom: 1px solid var(--color-border-1);
}

.script-output-item:last-child {
  border-bottom: none;
}

.script-name {
  font-weight: 600;
  margin-bottom: 8px;
  font-size: 13px;
}

.api-time {
  font-weight: 600;
  color: #165dff;
}
</style>

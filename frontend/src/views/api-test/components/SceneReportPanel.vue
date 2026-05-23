<template>
  <div class="scene-report">
    <!-- 摘要卡片 -->
    <div class="summary-cards">
      <div class="summary-card pass-card">
        <div class="summary-value">{{ passRate }}%</div>
        <div class="summary-label">通过率</div>
      </div>
      <div class="summary-card">
        <div class="summary-value">{{ executedCount }}/{{ totalCount }}</div>
        <div class="summary-label">执行节点</div>
      </div>
      <div class="summary-card">
        <div class="summary-value">{{ skippedCount }}</div>
        <div class="summary-label">跳过</div>
      </div>
      <div class="summary-card">
        <div class="summary-value">{{ formatDuration(duration) }}</div>
        <div class="summary-label">耗时</div>
      </div>
    </div>

    <!-- 主体：流程图 + 详情面板 -->
    <div class="main-content">
      <!-- 左侧流程图 -->
      <div class="flow-panel">
        <div class="flow-title">执行流程</div>
        <div class="flow-scroll">
          <template v-for="(node, idx) in nodeTree" :key="node.node_id">
            <FlowNode
              :node="node"
              :selected-id="selectedNodeId"
              :depth="0"
              @select="handleSelectNode"
            />
            <!-- 顶层节点之间的连接线 -->
            <div v-if="idx < nodeTree.length - 1 && !isConditionWithBranch(node)" class="flow-connector" />
          </template>
        </div>
      </div>

      <!-- 右侧详情面板 -->
      <div class="detail-panel">
        <template v-if="selectedDetail">
          <!-- 头部：节点信息 + 状态 -->
          <div class="detail-header">
            <div class="detail-title">
              <a-tag :color="getNodeTypeColor(selectedDetail.node_type)" size="small">
                {{ getNodeTypeText(selectedDetail.node_type) }}
              </a-tag>
              <span v-if="selectedDetail.case_number" class="case-number">{{ selectedDetail.case_number }}</span>
              <span class="case-name">{{ selectedDetail.case_name || selectedNode?.name }}</span>
            </div>
            <a-tag :color="getStatusColor(selectedDetail.status)" size="large">
              <template #icon>
                <icon-check-circle-fill v-if="selectedDetail.status === 'pass'" />
                <icon-close-circle-fill v-else-if="selectedDetail.status === 'fail'" />
                <icon-exclamation-circle-fill v-else-if="selectedDetail.status === 'error'" />
                <icon-minus-circle v-else />
              </template>
              {{ getStatusText(selectedDetail.status) }}
            </a-tag>
          </div>

          <!-- 执行信息 -->
          <a-descriptions :column="2" style="margin-bottom: 16px">
            <a-descriptions-item label="执行顺序">{{ selectedDetail.execution_order }}</a-descriptions-item>
            <a-descriptions-item label="接口耗时">
              <span v-if="selectedDetail.node_type === 'api_call' && selectedDetail.response_info" class="api-time">
                {{ selectedDetail.response_info.elapsed_ms ?? '-' }}ms
              </span>
              <span v-else>-</span>
            </a-descriptions-item>
            <a-descriptions-item label="总耗时">{{ selectedDetail.duration_ms }}ms</a-descriptions-item>
            <a-descriptions-item v-if="selectedDetail.node_type === 'api_call'" label="状态码">
              <a-tag v-if="selectedDetail.response_info" :color="selectedDetail.response_info.status_code < 400 ? 'green' : 'red'">
                {{ selectedDetail.response_info.status_code }}
              </a-tag>
              <span v-else>-</span>
            </a-descriptions-item>
            <a-descriptions-item label="开始时间">{{ formatTime(selectedDetail.started_at) }}</a-descriptions-item>
            <a-descriptions-item label="结束时间">{{ formatTime(selectedDetail.finished_at) }}</a-descriptions-item>
          </a-descriptions>

          <!-- 错误信息 -->
          <a-alert
            v-if="selectedDetail.error_message"
            type="error"
            :content="selectedDetail.error_message"
            style="margin-bottom: 16px"
            show-icon
          />

          <!-- 条件节点详情 -->
          <template v-if="selectedDetail.node_type === 'condition' && selectedDetail.request_snapshot">
            <a-card :bordered="false" title="条件评估" style="margin-bottom: 16px">
              <a-descriptions :column="2">
                <a-descriptions-item label="变量名">{{ selectedDetail.request_snapshot.variable }}</a-descriptions-item>
                <a-descriptions-item label="运算符">{{ selectedDetail.request_snapshot.operator }}</a-descriptions-item>
                <a-descriptions-item label="实际值">{{ selectedDetail.request_snapshot.actual }}</a-descriptions-item>
                <a-descriptions-item label="比较值">{{ selectedDetail.request_snapshot.expected }}</a-descriptions-item>
                <a-descriptions-item label="评估结果">
                  <a-tag :color="selectedDetail.request_snapshot.result ? 'green' : 'red'">
                    {{ selectedDetail.request_snapshot.result ? '真' : '假' }}
                  </a-tag>
                </a-descriptions-item>
              </a-descriptions>
            </a-card>
          </template>

          <!-- 等待节点详情 -->
          <template v-if="selectedDetail.node_type === 'wait' && selectedDetail.request_snapshot">
            <a-card :bordered="false" title="等待信息" style="margin-bottom: 16px">
              <a-descriptions :column="1">
                <a-descriptions-item label="等待时长">{{ selectedDetail.request_snapshot.wait_seconds }}秒</a-descriptions-item>
              </a-descriptions>
            </a-card>
          </template>

          <!-- 数据赋值节点详情 -->
          <template v-if="selectedDetail.node_type === 'data_assign' && selectedDetail.request_snapshot">
            <a-card :bordered="false" title="赋值信息" style="margin-bottom: 16px">
              <a-descriptions :column="2">
                <a-descriptions-item label="变量名">{{ selectedDetail.request_snapshot.variable }}</a-descriptions-item>
                <a-descriptions-item label="赋值来源">{{ selectedDetail.request_snapshot.source === 'static' ? '静态值' : '表达式' }}</a-descriptions-item>
                <a-descriptions-item label="赋值值" :span="2">{{ selectedDetail.request_snapshot.value }}</a-descriptions-item>
              </a-descriptions>
            </a-card>
          </template>

          <!-- 请求快照 -->
          <a-collapse v-if="selectedDetail.node_type === 'api_call'" :bordered="false" style="margin-bottom: 16px">
            <a-collapse-item header="请求快照" key="request">
              <div v-if="selectedDetail.request_snapshot" class="snapshot-content">
                <div class="snapshot-line">
                  <strong>{{ selectedDetail.request_snapshot.method }}</strong>
                  {{ selectedDetail.request_snapshot.url }}
                </div>
                <div v-if="selectedDetail.request_snapshot.params && Object.keys(selectedDetail.request_snapshot.params).length" class="snapshot-section">
                  <div class="snapshot-label">Query Params</div>
                  <div v-for="(v, k) in selectedDetail.request_snapshot.params" :key="k" class="snapshot-kv">
                    <span class="snapshot-key">{{ k }}</span>
                    <span class="snapshot-value">{{ v }}</span>
                  </div>
                </div>
                <div v-if="selectedDetail.request_snapshot.headers" class="snapshot-section">
                  <div class="snapshot-label">Headers</div>
                  <div v-for="(v, k) in selectedDetail.request_snapshot.headers" :key="k" class="snapshot-kv">
                    <span class="snapshot-key">{{ k }}</span>
                    <span class="snapshot-value">{{ v }}</span>
                  </div>
                </div>
                <div v-if="selectedDetail.request_snapshot.body" class="snapshot-section">
                  <div class="snapshot-label">Body</div>
                  <JsonViewer :content="selectedDetail.request_snapshot.body" max-height="300px" />
                </div>
              </div>
              <a-empty v-else description="无请求快照" />
            </a-collapse-item>
          </a-collapse>

          <!-- 响应信息 -->
          <a-collapse v-if="selectedDetail.node_type === 'api_call'" :bordered="false" style="margin-bottom: 16px">
            <a-collapse-item header="响应信息" key="response">
              <div v-if="selectedDetail.response_info" class="snapshot-content">
                <a-descriptions :column="3" style="margin-bottom: 12px">
                  <a-descriptions-item label="状态码">
                    <a-tag :color="selectedDetail.response_info.status_code < 400 ? 'green' : 'red'">
                      {{ selectedDetail.response_info.status_code }}
                    </a-tag>
                  </a-descriptions-item>
                  <a-descriptions-item label="耗时">{{ selectedDetail.response_info.elapsed_ms }}ms</a-descriptions-item>
                  <a-descriptions-item label="大小">{{ formatSize(selectedDetail.response_info.size_bytes) }}</a-descriptions-item>
                </a-descriptions>
                <div class="snapshot-section">
                  <div class="snapshot-label">响应体</div>
                  <JsonViewer :content="selectedDetail.response_info.body" max-height="300px" />
                </div>
              </div>
              <a-empty v-else description="无响应信息" />
            </a-collapse-item>
          </a-collapse>

          <!-- 断言结果 -->
          <a-collapse v-if="selectedDetail.assertions?.length" :bordered="false" style="margin-bottom: 16px">
            <a-collapse-item header="断言结果" key="assertions">
              <a-table
                :columns="assertionColumns"
                :data="selectedDetail.assertions"
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
          <a-collapse v-if="selectedDetail.extracted_vars && Object.keys(selectedDetail.extracted_vars).length" :bordered="false" style="margin-bottom: 16px">
            <a-collapse-item header="提取的变量" key="extracts">
              <div v-for="(v, k) in selectedDetail.extracted_vars" :key="k" class="snapshot-kv" :class="{ 'var-empty': v == null || v === '' }">
                <span class="snapshot-key">{{ k }}</span>
                <span class="snapshot-value">{{ v ?? '(空)' }}</span>
                <a-tag v-if="v == null || v === ''" color="orange" size="small">提取失败</a-tag>
              </div>
            </a-collapse-item>
          </a-collapse>

          <!-- 脚本输出 -->
          <a-collapse v-if="selectedDetail.script_output && Object.keys(selectedDetail.script_output).length" :bordered="false">
            <a-collapse-item header="脚本输出" key="scripts">
              <div v-for="(output, name) in selectedDetail.script_output" :key="name" class="script-output-item">
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

        <a-empty v-else description="点击左侧节点查看详情" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import JsonViewer from '@/components/JsonViewer.vue'
import { getBatchRunDetail } from '@/api/batchRun'
import type { NodeTreeItem, CaseDetailFull } from '@/api/batchRun'
import FlowNode from './FlowNode.vue'

interface Props {
  runId: number
  nodeTree: NodeTreeItem[]
  details: any[]
  passCount: number
  failCount: number
  errorCount: number
  duration?: number
}

const props = defineProps<Props>()

const selectedNodeId = ref<number | null>(null)
const selectedDetail = ref<CaseDetailFull | null>(null)
const detailLoading = ref(false)

// 统计
const totalCount = computed(() => props.details.length)
const skippedCount = computed(() => props.details.filter((d: any) => d.status === 'skipped').length)
const executedCount = computed(() => props.passCount + props.failCount + props.errorCount)
const passRate = computed(() => {
  const executed = executedCount.value
  if (executed === 0) return 0
  return Math.round(props.passCount / executed * 100)
})

// 找到选中的节点
const selectedNode = computed(() => {
  if (!selectedNodeId.value) return null
  const find = (nodes: NodeTreeItem[]): NodeTreeItem | null => {
    for (const n of nodes) {
      if (n.node_id === selectedNodeId.value) return n
      if (n.true_branch) {
        const found = find(n.true_branch)
        if (found) return found
      }
      if (n.false_branch) {
        const found = find(n.false_branch)
        if (found) return found
      }
    }
    return null
  }
  return find(props.nodeTree)
})

// 判断是否是有分支的条件节点
const isConditionWithBranch = (node: NodeTreeItem) => {
  return node.node_type === 'condition' && (node.true_branch.length > 0 || node.false_branch.length > 0)
}

const findFirstFailed = (nodes: NodeTreeItem[]): NodeTreeItem | null => {
  for (const n of nodes) {
    if (n.status === 'fail' || n.status === 'error') return n
    if (n.true_branch) {
      const found = findFirstFailed(n.true_branch)
      if (found) return found
    }
    if (n.false_branch) {
      const found = findFirstFailed(n.false_branch)
      if (found) return found
    }
  }
  return null
}

// 选中节点时加载详情
const handleSelectNode = async (nodeId: number) => {
  selectedNodeId.value = nodeId
  const node = selectedNode.value
  if (!node?.detail_id) {
    selectedDetail.value = null
    return
  }
  detailLoading.value = true
  try {
    selectedDetail.value = await getBatchRunDetail(props.runId, node.detail_id)
  } catch {
    selectedDetail.value = null
  } finally {
    detailLoading.value = false
  }
}

// 监听 nodeTree 变化，自动选中第一个失败/错误节点
watch(() => props.nodeTree, (tree) => {
  if (tree.length > 0 && !selectedNodeId.value) {
    const firstFailed = findFirstFailed(tree)
    if (firstFailed) {
      handleSelectNode(firstFailed.node_id)
    }
  }
}, { immediate: true })

const getNodeTypeColor = (type?: string) => {
  const map: Record<string, string> = { api_call: 'blue', condition: 'orange', wait: 'gray', data_assign: 'green' }
  return map[type || ''] || 'gray'
}

const getNodeTypeText = (type?: string) => {
  const map: Record<string, string> = { api_call: '接口调用', condition: '条件判断', wait: '等待延时', data_assign: '数据赋值' }
  return map[type || ''] || type || ''
}

const getStatusColor = (status: string) => {
  const map: Record<string, string> = { pass: 'green', fail: 'red', error: 'orange', skipped: 'gray', pending: 'gray', running: 'blue' }
  return map[status] || 'gray'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = { pass: '通过', fail: '失败', error: '错误', skipped: '已跳过', pending: '待执行', running: '执行中' }
  return map[status] || status
}

const formatDuration = (ms?: number) => {
  if (!ms) return '-'
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${Math.floor(ms / 60000)}m ${((ms % 60000) / 1000).toFixed(0)}s`
}

const formatJson = (data: any) => {
  if (typeof data === 'string') {
    try { return JSON.stringify(JSON.parse(data), null, 2) } catch { return data }
  }
  return JSON.stringify(data, null, 2)
}

const formatTime = (time?: string) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const formatSize = (bytes?: number) => {
  if (!bytes) return '-'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

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
</script>

<style scoped>
.scene-report {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.summary-cards {
  display: flex;
  gap: 12px;
}

.summary-card {
  flex: 1;
  padding: 16px;
  background: var(--color-bg-2);
  border-radius: var(--radius-medium);
  text-align: center;
  border: 1px solid var(--color-border-2);
}

.summary-card.pass-card {
  border-left: 4px solid #00b42a;
}

.summary-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text-1);
}

.summary-label {
  font-size: 12px;
  color: var(--color-text-3);
  margin-top: 4px;
}

.main-content {
  display: flex;
  gap: 16px;
  min-height: 500px;
}

.flow-panel {
  width: 560px;
  flex-shrink: 0;
  background: var(--color-bg-2);
  border-radius: var(--radius-medium);
  border: 1px solid var(--color-border-2);
  overflow: hidden;
}

.flow-title {
  padding: 12px 16px;
  font-weight: 600;
  font-size: 14px;
  border-bottom: 1px solid var(--color-border-2);
  color: var(--color-text-1);
}

.flow-scroll {
  padding: 16px;
  overflow-y: auto;
  overflow-x: auto;
  max-height: 600px;
}

.flow-connector {
  width: 2px;
  height: 16px;
  background: var(--color-border-3);
  margin: 0 auto;
}

.detail-panel {
  flex: 1;
  background: var(--color-bg-2);
  border-radius: var(--radius-medium);
  border: 1px solid var(--color-border-2);
  padding: 16px;
  overflow-y: auto;
  max-height: 600px;
}

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
  white-space: pre-wrap;
  word-break: break-all;
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

.var-empty {
  background: var(--color-warning-light-1);
}

.var-empty .snapshot-key {
  color: var(--color-text-4);
}

.var-empty .snapshot-value {
  color: var(--color-text-4);
  font-style: italic;
}
</style>

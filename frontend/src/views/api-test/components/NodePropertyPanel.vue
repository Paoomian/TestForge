<template>
  <div class="node-property-panel">
    <!-- 节点类型 -->
    <div class="prop-section">
      <div class="prop-label">节点类型</div>
      <a-tag :color="nodeColors[node.node_type]" size="large" class="type-tag-full">
        {{ nodeTypeLabels[node.node_type] }}
      </a-tag>
    </div>

    <a-divider style="margin: 12px 0" />

    <!-- 接口调用配置 -->
    <template v-if="node.node_type === 'api_call'">
      <div class="prop-section">
        <div class="prop-label">选择用例</div>
        <a-select
          :model-value="node.case_id ?? undefined"
          placeholder="搜索用例名称或编号"
          allow-search
          :filter-option="filterOption"
          @update:model-value="onCaseChange"
        >
          <a-option v-for="c in cases" :key="c.id" :value="c.id">
            <div class="case-option">
              <span class="case-number">{{ c.case_number }}</span>
              <span class="case-name">{{ c.name }}</span>
              <a-tag size="small" :color="getMethodColor(c.method)">{{ c.method }}</a-tag>
            </div>
          </a-option>
        </a-select>
      </div>
      <div v-if="selectedCase" class="case-preview">
        <a-descriptions :column="1" size="small" bordered>
          <a-descriptions-item label="编号">{{ selectedCase.case_number }}</a-descriptions-item>
          <a-descriptions-item label="方法">
            <a-tag :color="getMethodColor(selectedCase.method)" size="small">{{ selectedCase.method }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="模块">{{ selectedCase.module || '-' }}</a-descriptions-item>
          <a-descriptions-item label="优先级">
            <a-tag :color="getPriorityColor(selectedCase.priority)" size="small">{{ selectedCase.priority }}</a-tag>
          </a-descriptions-item>
        </a-descriptions>
      </div>
    </template>

    <!-- 条件判断配置 -->
    <template v-if="node.node_type === 'condition'">
      <div class="prop-section">
        <div class="prop-label">变量名</div>
        <a-input
          :model-value="node.condition_variable"
          placeholder="如: status, code"
          @update:model-value="$emit('update', { condition_variable: $event })"
        >
          <template #prefix><span v-text="leftBraces"></span></template>
          <template #suffix><span v-text="rightBraces"></span></template>
        </a-input>
      </div>
      <div class="prop-section">
        <div class="prop-label">运算符</div>
        <a-select
          :model-value="node.condition_operator || 'eq'"
          @update:model-value="$emit('update', { condition_operator: $event as any })"
        >
          <a-option value="eq">等于 (==)</a-option>
          <a-option value="neq">不等于 (!=)</a-option>
          <a-option value="gt">大于 (>)</a-option>
          <a-option value="lt">小于 (<)</a-option>
          <a-option value="gte">大于等于 (>=)</a-option>
          <a-option value="lte">小于等于 (<=)</a-option>
          <a-option value="contains">包含</a-option>
          <a-option value="not_contains">不包含</a-option>
          <a-option value="empty">为空</a-option>
          <a-option value="not_empty">不为空</a-option>
        </a-select>
      </div>
      <div class="prop-section" v-if="node.condition_operator !== 'empty' && node.condition_operator !== 'not_empty'">
        <div class="prop-label">比较值</div>
        <a-input
          :model-value="node.condition_value"
          placeholder="输入比较值"
          @update:model-value="$emit('update', { condition_value: $event })"
        />
      </div>
      <div class="prop-hint">
        <icon-info-circle />
        <span>分支路径在左侧流程图中可视化配置</span>
      </div>
    </template>

    <!-- 等待延时配置 -->
    <template v-if="node.node_type === 'wait'">
      <div class="prop-section">
        <div class="prop-label">等待时间</div>
        <a-input-number
          :model-value="node.wait_seconds || 1"
          :min="1"
          :max="300"
          @update:model-value="$emit('update', { wait_seconds: $event })"
        >
          <template #suffix>秒</template>
        </a-input-number>
      </div>
      <div class="prop-presets">
        <span class="preset-label">快捷：</span>
        <a-space :size="4">
          <a-button size="mini" @click="$emit('update', { wait_seconds: 1 })">1s</a-button>
          <a-button size="mini" @click="$emit('update', { wait_seconds: 3 })">3s</a-button>
          <a-button size="mini" @click="$emit('update', { wait_seconds: 5 })">5s</a-button>
          <a-button size="mini" @click="$emit('update', { wait_seconds: 10 })">10s</a-button>
          <a-button size="mini" @click="$emit('update', { wait_seconds: 30 })">30s</a-button>
        </a-space>
      </div>
    </template>

    <!-- 数据赋值配置 -->
    <template v-if="node.node_type === 'data_assign'">
      <div class="prop-section">
        <div class="prop-label">变量名</div>
        <a-input
          :model-value="node.assign_variable"
          placeholder="如: user_id, token"
          @update:model-value="$emit('update', { assign_variable: $event })"
        />
      </div>
      <div class="prop-section">
        <div class="prop-label">赋值方式</div>
        <a-radio-group
          :model-value="node.assign_source || 'static'"
          @update:model-value="$emit('update', { assign_source: $event as any })"
        >
          <a-radio value="static">静态值</a-radio>
          <a-radio value="expression">表达式</a-radio>
        </a-radio-group>
      </div>
      <div class="prop-section">
        <div class="prop-label">变量值</div>
        <a-input
          v-if="(node.assign_source || 'static') === 'static'"
          :model-value="node.assign_value"
          placeholder="输入固定值"
          @update:model-value="$emit('update', { assign_value: $event })"
        />
        <a-textarea
          v-else
          :model-value="node.assign_value"
          placeholder="支持 {{变量名}} 模板语法"
          :auto-size="{ minRows: 2, maxRows: 4 }"
          @update:model-value="$emit('update', { assign_value: $event })"
        />
      </div>
      <div v-if="(node.assign_source || 'static') === 'expression'" class="prop-hint">
        <icon-info-circle />
        <span>使用 <code v-text="expressionHint"></code> 引用其他变量</span>
      </div>
    </template>

    <a-divider style="margin: 12px 0" />

    <!-- 操作区 -->
    <div class="prop-actions">
      <a-button type="text" size="small" status="danger" @click="$emit('delete')">
        <template #icon><icon-delete /></template>
        删除此节点
      </a-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { SceneNodeItem, SceneNodeType } from '@/api/sceneNode'
import type { APITestCase } from '@/api/apiTestCase'

const leftBraces = '{{'
const rightBraces = '}}'
const expressionHint = '{{变量名}}'

const nodeColors: Record<SceneNodeType, string> = {
  api_call: '#3370ff', condition: '#ff7d00', wait: '#86909c', data_assign: '#00b42a'
}

const nodeTypeLabels: Record<SceneNodeType, string> = {
  api_call: '接口调用', condition: '条件判断', wait: '等待延时', data_assign: '数据赋值'
}

const props = defineProps<{
  node: SceneNodeItem
  cases: APITestCase[]
}>()

const emit = defineEmits<{
  (e: 'update', data: Partial<SceneNodeItem>): void
  (e: 'delete'): void
}>()

const selectedCase = computed(() => {
  return props.cases.find(c => c.id === props.node.case_id)
})

function getCaseName(caseId: number): string {
  return props.cases.find(c => c.id === caseId)?.name || ''
}

function onCaseChange(val: string | number | boolean | Record<string, any> | (string | number | boolean | Record<string, any>)[]) {
  const caseId = val as number
  emit('update', { case_id: caseId, case_name: getCaseName(caseId) })
}

function filterOption(inputValue: string, option: any): boolean {
  const caseItem = props.cases.find(c => c.id === option.value)
  if (!caseItem) return false
  const s = inputValue.toLowerCase()
  return caseItem.name.toLowerCase().includes(s) || (caseItem.case_number ?? '').toLowerCase().includes(s)
}

function getMethodColor(method: string): string {
  const colors: Record<string, string> = { GET: 'blue', POST: 'green', PUT: 'orange', DELETE: 'red', PATCH: 'purple' }
  return colors[method] || 'gray'
}

function getPriorityColor(priority: string): string {
  const colors: Record<string, string> = { P0: 'red', P1: 'orange', P2: 'blue', P3: 'green' }
  return colors[priority] || 'gray'
}
</script>

<style scoped>
.node-property-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.prop-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.prop-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-2);
}

.type-tag-full {
  width: 100%;
  text-align: center;
  font-size: 13px;
  padding: 6px 0;
}

.case-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.case-number {
  font-size: 12px;
  color: var(--color-text-3);
  min-width: 80px;
}

.case-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.case-preview {
  padding: 10px;
  background: var(--color-fill-1);
  border-radius: var(--radius-small);
}

.prop-presets {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}

.preset-label {
  font-size: 12px;
  color: var(--color-text-3);
}

.prop-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  background: var(--color-fill-1);
  border-radius: var(--radius-small);
  font-size: 12px;
  color: var(--color-text-3);
}

.prop-hint code {
  background: var(--color-fill-3);
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 11px;
}

.prop-actions {
  display: flex;
  justify-content: center;
}
</style>

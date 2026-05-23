<template>
  <div class="scene-orchestrator">
    <!-- 工具栏 -->
    <div class="orchestrator-toolbar">
      <a-space :size="8">
        <a-button size="small" type="outline" @click="addNodeToMain('api_call')">
          <template #icon><icon-code style="color: #3370ff" /></template>
          接口调用
        </a-button>
        <a-button size="small" type="outline" @click="addNodeToMain('condition')">
          <template #icon><icon-branch style="color: #ff7d00" /></template>
          条件判断
        </a-button>
        <a-button size="small" type="outline" @click="addNodeToMain('wait')">
          <template #icon><icon-clock-circle style="color: #86909c" /></template>
          等待延时
        </a-button>
        <a-button size="small" type="outline" @click="addNodeToMain('data_assign')">
          <template #icon><icon-storage style="color: #00b42a" /></template>
          数据赋值
        </a-button>
      </a-space>
    </div>

    <!-- 主体：流程图 + 属性面板 -->
    <div class="orchestrator-body">
      <!-- 流程图区域 -->
      <div class="flow-canvas">
        <!-- 空状态 -->
        <div v-if="nodes.length === 0" class="empty-state">
          <div class="empty-icon"><icon-layers :size="48" /></div>
          <div class="empty-title">暂无编排节点</div>
          <div class="empty-desc">点击上方按钮添加节点，开始编排测试场景</div>
        </div>

        <!-- 流程图 -->
        <div v-else class="flow-list">
          <div
            v-for="(item, index) in flowItems"
            :key="item.type === 'condition' ? `cond-${item.node.id}` : `node-${item.node.id}`"
            class="flow-item"
          >
            <!-- 连接线（非首项） -->
            <div v-if="index > 0" class="flow-connector-line">
              <svg width="2" height="24"><line x1="1" y1="0" x2="1" y2="24" stroke="#c9cdd4" stroke-width="2" /></svg>
              <svg width="10" height="8" class="connector-arrow"><polygon points="1,0 9,0 5,8" fill="#c9cdd4" /></svg>
            </div>

            <!-- 条件节点（带分支） -->
            <template v-if="item.type === 'condition'">
              <div class="flow-condition">
                <!-- 条件卡片 -->
                <div
                  class="condition-card"
                  :class="{ selected: selectedNodeId === item.node.id, disabled: !item.node.enabled }"
                  @click="selectNode(item.node.id!)"
                  draggable="true"
                  @dragstart="onDragStart($event, item.node, 'main', index)"
                  @dragover.prevent
                  @drop="onDrop($event, 'main', index)"
                >
                  <div class="card-main">
                    <div class="card-header">
                      <a-tag :color="nodeColors.condition" size="small" class="type-tag">条件判断</a-tag>
                    </div>
                    <div class="card-summary" v-if="item.node.condition_variable">
                      {{ item.node.condition_variable }}
                      {{ operatorLabels[item.node.condition_operator || 'eq'] }}
                      {{ item.node.condition_value }}
                    </div>
                  </div>
                  <div class="card-actions" @click.stop>
                    <a-tooltip :content="item.node.enabled ? '禁用' : '启用'">
                      <a-button type="text" size="mini" @click="toggleNode(item.node)">
                        <template #icon>
                          <icon-check-circle-fill v-if="item.node.enabled" style="color: #00b42a" />
                          <icon-minus-circle v-else style="color: #86909c" />
                        </template>
                      </a-button>
                    </a-tooltip>
                    <a-tooltip content="删除">
                      <a-button type="text" size="mini" status="danger" @click="deleteMainNode(index)">
                        <template #icon><icon-delete /></template>
                      </a-button>
                    </a-tooltip>
                  </div>
                </div>

                <!-- 分支区域 -->
                <div class="branches-area">
                  <!-- Y形分叉连接 -->
                  <div class="branch-fork">
                    <svg width="100%" height="28" preserveAspectRatio="none">
                      <line x1="25%" y1="0" x2="25%" y2="12" stroke="#00b42a" stroke-width="2" />
                      <line x1="75%" y1="0" x2="75%" y2="12" stroke="#f53f3f" stroke-width="2" />
                      <line x1="25%" y1="12" x2="75%" y2="12" stroke="#c9cdd4" stroke-width="1.5" stroke-dasharray="4" />
                    </svg>
                  </div>

                  <div class="branches-columns">
                    <!-- 真分支 -->
                    <div class="branch-column">
                      <div class="branch-label branch-label-true">为真时</div>
                      <div class="branch-list">
                        <div
                          v-for="(bNode, bIndex) in item.trueBranch"
                          :key="bNode.id"
                          class="flow-branch-node"
                        >
                          <div v-if="bIndex > 0" class="branch-connector">
                            <svg width="2" height="16"><line x1="1" y1="0" x2="1" y2="16" stroke="#c9cdd4" stroke-width="1.5" /></svg>
                          </div>
                          <SceneNodeCard
                            :node="bNode"
                            :selected="selectedNodeId === bNode.id"
                            :index="bIndex + 1"
                            @click="selectNode(bNode.id!)"
                            @toggle="toggleNode(bNode)"
                            @delete="deleteBranchNode(item.node.id!, 'true', bIndex)"
                            draggable="true"
                            @dragstart="onDragStart($event, bNode, 'true', bIndex)"
                            @dragover.prevent
                            @drop="onDrop($event, 'true', bIndex)"
                          />
                        </div>
                        <a-dropdown trigger="click" @select="(type: any) => addBranchNode(item.node.id!, 'true', type)">
                          <a-button type="dashed" size="mini" long class="add-branch-btn">
                            <template #icon><icon-plus /></template>
                            添加节点
                          </a-button>
                          <template #content>
                            <a-doption value="api_call"><icon-code style="color:#3370ff" /> 接口调用</a-doption>
                            <a-doption value="condition"><icon-branch style="color:#ff7d00" /> 条件判断</a-doption>
                            <a-doption value="wait"><icon-clock-circle style="color:#86909c" /> 等待延时</a-doption>
                            <a-doption value="data_assign"><icon-storage style="color:#00b42a" /> 数据赋值</a-doption>
                          </template>
                        </a-dropdown>
                      </div>
                    </div>

                    <!-- 假分支 -->
                    <div class="branch-column">
                      <div class="branch-label branch-label-false">为假时</div>
                      <div class="branch-list">
                        <div
                          v-for="(bNode, bIndex) in item.falseBranch"
                          :key="bNode.id"
                          class="flow-branch-node"
                        >
                          <div v-if="bIndex > 0" class="branch-connector">
                            <svg width="2" height="16"><line x1="1" y1="0" x2="1" y2="16" stroke="#c9cdd4" stroke-width="1.5" /></svg>
                          </div>
                          <SceneNodeCard
                            :node="bNode"
                            :selected="selectedNodeId === bNode.id"
                            :index="bIndex + 1"
                            @click="selectNode(bNode.id!)"
                            @toggle="toggleNode(bNode)"
                            @delete="deleteBranchNode(item.node.id!, 'false', bIndex)"
                            draggable="true"
                            @dragstart="onDragStart($event, bNode, 'false', bIndex)"
                            @dragover.prevent
                            @drop="onDrop($event, 'false', bIndex)"
                          />
                        </div>
                        <a-dropdown trigger="click" @select="(type: any) => addBranchNode(item.node.id!, 'false', type)">
                          <a-button type="dashed" size="mini" long class="add-branch-btn">
                            <template #icon><icon-plus /></template>
                            添加节点
                          </a-button>
                          <template #content>
                            <a-doption value="api_call"><icon-code style="color:#3370ff" /> 接口调用</a-doption>
                            <a-doption value="condition"><icon-branch style="color:#ff7d00" /> 条件判断</a-doption>
                            <a-doption value="wait"><icon-clock-circle style="color:#86909c" /> 等待延时</a-doption>
                            <a-doption value="data_assign"><icon-storage style="color:#00b42a" /> 数据赋值</a-doption>
                          </template>
                        </a-dropdown>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </template>

            <!-- 普通节点 -->
            <template v-else>
              <SceneNodeCard
                :node="item.node"
                :selected="selectedNodeId === item.node.id"
                :index="index"
                @click="selectNode(item.node.id!)"
                @toggle="toggleNode(item.node)"
                @delete="deleteMainNode(index)"
                draggable="true"
                @dragstart="onDragStart($event, item.node, 'main', index)"
                @dragover.prevent
                @drop="onDrop($event, 'main', index)"
              />
            </template>
          </div>
        </div>
      </div>

      <!-- 属性面板 -->
      <div class="property-panel">
        <template v-if="selectedNode">
          <div class="panel-header">
            <span class="panel-title">编辑节点</span>
            <a-button type="text" size="mini" @click="selectedNodeId = null">
              <template #icon><icon-close /></template>
            </a-button>
          </div>
          <div class="panel-body">
            <NodePropertyPanel
              :node="selectedNode"
              :cases="cases"
              @update="updateSelectedNode"
              @delete="deleteSelectedNode"
            />
          </div>
        </template>
        <div v-else class="panel-empty">
          <icon-edit :size="32" style="opacity: 0.3" />
          <div>点击节点进行编辑</div>
        </div>
      </div>
    </div>

    <!-- 底部统计 -->
    <div v-if="nodes.length > 0" class="orchestrator-footer">
      <span class="stat-item">共 <strong>{{ nodes.length }}</strong> 个节点</span>
      <span class="stat-item">接口 <strong>{{ apiCallCount }}</strong></span>
      <span class="stat-item">条件 <strong>{{ conditionCount }}</strong></span>
      <span class="stat-item">等待 <strong>{{ waitCount }}</strong></span>
      <span class="stat-item">赋值 <strong>{{ dataAssignCount }}</strong></span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Modal } from '@arco-design/web-vue'
import type { SceneNodeItem, SceneNodeType } from '@/api/sceneNode'
import type { APITestCase } from '@/api/apiTestCase'
import SceneNodeCard from './SceneNodeCard.vue'
import NodePropertyPanel from './NodePropertyPanel.vue'

const props = defineProps<{
  modelValue: SceneNodeItem[]
  cases: APITestCase[]
  suiteId: number
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: SceneNodeItem[]): void
}>()

const nodes = ref<SceneNodeItem[]>([])
const selectedNodeId = ref<number | null>(null)

// 节点类型颜色
const nodeColors: Record<string, string> = {
  api_call: '#3370ff', condition: '#ff7d00', wait: '#86909c', data_assign: '#00b42a'
}

// 运算符标签
const operatorLabels: Record<string, string> = {
  eq: '==', neq: '!=', gt: '>', lt: '<', gte: '>=', lte: '<=',
  contains: '包含', not_contains: '不包含', empty: '为空', not_empty: '不为空'
}

// 同步 props
watch(() => props.modelValue, (val) => {
  nodes.value = (val || []).map(n => ({ ...n }))
}, { immediate: true })

// 流程项类型
interface FlowItem {
  node: SceneNodeItem
  type: 'normal' | 'condition'
  trueBranch: SceneNodeItem[]
  falseBranch: SceneNodeItem[]
}

// 构建流程数据
const flowItems = computed<FlowItem[]>(() => {
  const result: FlowItem[] = []
  const mainNodes = nodes.value.filter(n => !n.branch_of)

  for (const node of mainNodes) {
    if (node.node_type === 'condition') {
      result.push({
        node,
        type: 'condition',
        trueBranch: nodes.value.filter(n => n.branch_of === node.id && n.branch_type === 'true'),
        falseBranch: nodes.value.filter(n => n.branch_of === node.id && n.branch_type === 'false')
      })
    } else {
      result.push({ node, type: 'normal', trueBranch: [], falseBranch: [] })
    }
  }
  return result
})

// 选中节点
const selectedNode = computed(() => {
  if (!selectedNodeId.value) return null
  return nodes.value.find(n => n.id === selectedNodeId.value) || null
})

// 统计
const apiCallCount = computed(() => nodes.value.filter(n => n.node_type === 'api_call').length)
const conditionCount = computed(() => nodes.value.filter(n => n.node_type === 'condition').length)
const waitCount = computed(() => nodes.value.filter(n => n.node_type === 'wait').length)
const dataAssignCount = computed(() => nodes.value.filter(n => n.node_type === 'data_assign').length)

// 同步条件节点的 true_branch/false_branch 数组
function syncBranchArrays() {
  const conditions = nodes.value.filter(n => n.node_type === 'condition')
  for (const cond of conditions) {
    cond.true_branch = nodes.value
      .filter(n => n.branch_of === cond.id && n.branch_type === 'true')
      .map(n => n.id!)
    cond.false_branch = nodes.value
      .filter(n => n.branch_of === cond.id && n.branch_type === 'false')
      .map(n => n.id!)
  }
}

// 发送变更
function emitChange() {
  syncBranchArrays()
  emit('update:modelValue', nodes.value.map((n, i) => ({ ...n, sort_order: i })))
}

// 生成唯一 ID（临时，保存后会被后端 ID 替换）
let tempIdCounter = -1
function genTempId(): number { return tempIdCounter-- }

// 选择节点
function selectNode(id: number) {
  selectedNodeId.value = id
}

// 添加节点到主流
function addNodeToMain(type: SceneNodeType) {
  const names: Record<SceneNodeType, string> = {
    api_call: '接口调用', condition: '条件判断', wait: '等待', data_assign: '数据赋值'
  }
  const newNode: SceneNodeItem = {
    id: genTempId(),
    suite_id: props.suiteId,
    node_type: type,
    name: names[type],
    enabled: true,
    sort_order: nodes.value.filter(n => !n.branch_of).length,
    wait_seconds: 5,
    assign_source: 'static'
  }
  nodes.value.push(newNode)
  selectedNodeId.value = newNode.id!
  emitChange()
}

// 添加节点到分支
function addBranchNode(condId: number, branchType: 'true' | 'false', type: SceneNodeType = 'api_call') {
  const names: Record<SceneNodeType, string> = {
    api_call: '接口调用', condition: '条件判断', wait: '等待', data_assign: '数据赋值'
  }
  const branchNodes = nodes.value.filter(n => n.branch_of === condId && n.branch_type === branchType)
  const newNode: SceneNodeItem = {
    id: genTempId(),
    suite_id: props.suiteId,
    node_type: type,
    name: names[type],
    enabled: true,
    sort_order: branchNodes.length,
    branch_of: condId,
    branch_type: branchType,
    wait_seconds: 5,
    assign_source: 'static'
  }
  nodes.value.push(newNode)
  selectedNodeId.value = newNode.id!
  emitChange()
}

// 切换节点启用/禁用
function toggleNode(node: SceneNodeItem) {
  node.enabled = !node.enabled
  emitChange()
}

// 删除主流节点
function deleteMainNode(index: number) {
  const item = flowItems.value[index]
  if (!item) return

  Modal.confirm({
    title: '确认删除',
    content: `确定要删除节点「${item.node.name}」吗？`,
    onOk: () => {
      // 删除条件节点时，同时删除其分支节点
      if (item.type === 'condition') {
        const condId = item.node.id!
        nodes.value = nodes.value.filter(n => n.id !== condId && n.branch_of !== condId)
      } else {
        const idx = nodes.value.findIndex(n => n.id === item.node.id)
        if (idx >= 0) nodes.value.splice(idx, 1)
      }
      if (selectedNodeId.value === item.node.id) selectedNodeId.value = null
      emitChange()
    }
  })
}

// 删除分支节点
function deleteBranchNode(condId: number, branchType: 'true' | 'false', branchIndex: number) {
  const branchNodes = nodes.value.filter(n => n.branch_of === condId && n.branch_type === branchType)
  const node = branchNodes[branchIndex]
  if (!node) return

  Modal.confirm({
    title: '确认删除',
    content: `确定要删除节点「${node.name}」吗？`,
    onOk: () => {
      // 删除节点本身及其子分支节点（如果是条件节点）
      const idsToDelete = new Set<number>([node.id!])
      if (node.node_type === 'condition') {
        nodes.value.forEach(n => {
          if (n.branch_of === node.id) idsToDelete.add(n.id!)
        })
      }
      nodes.value = nodes.value.filter(n => !idsToDelete.has(n.id!))
      if (selectedNodeId.value && idsToDelete.has(selectedNodeId.value)) selectedNodeId.value = null
      emitChange()
    }
  })
}

// 更新选中节点
function updateSelectedNode(data: Partial<SceneNodeItem>) {
  if (!selectedNode.value) return
  Object.assign(selectedNode.value, data)
  emitChange()
}

// 删除选中节点
function deleteSelectedNode() {
  const node = selectedNode.value
  if (!node) return

  if (node.branch_of) {
    // 删除分支内节点（含子分支）
    const idsToDelete = new Set<number>([node.id!])
    if (node.node_type === 'condition') {
      nodes.value.forEach(n => {
        if (n.branch_of === node.id) idsToDelete.add(n.id!)
      })
    }
    nodes.value = nodes.value.filter(n => !idsToDelete.has(n.id!))
    selectedNodeId.value = null
    emitChange()
  } else {
    const idx = flowItems.value.findIndex(item => item.node.id === node.id)
    if (idx >= 0) deleteMainNode(idx)
  }
}

// 拖拽
const dragData = ref<{ node: SceneNodeItem; scope: string; index: number } | null>(null)

function onDragStart(e: DragEvent, node: SceneNodeItem, scope: string, index: number) {
  dragData.value = { node, scope, index }
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', '')
  }
}

function onDrop(e: DragEvent, targetScope: string, targetIndex: number) {
  e.preventDefault()
  if (!dragData.value) return

  const { node: dragNode, scope: srcScope, index: srcIndex } = dragData.value

  // 只允许同范围内拖拽
  if (srcScope !== targetScope) return
  if (srcIndex === targetIndex) return

  if (srcScope === 'main') {
    // 主流拖拽重排
    const mainNodes = nodes.value.filter(n => !n.branch_of)
    const [moved] = mainNodes.splice(srcIndex, 1)
    mainNodes.splice(targetIndex, 0, moved)
    // 更新 sort_order
    mainNodes.forEach((n, i) => { n.sort_order = i })
    emitChange()
  } else {
    // 分支内拖拽重排
    const branchNodes = nodes.value.filter(n => n.branch_of === dragNode.branch_of && n.branch_type === srcScope)
    const [moved] = branchNodes.splice(srcIndex, 1)
    branchNodes.splice(targetIndex, 0, moved)
    branchNodes.forEach((n, i) => { n.sort_order = i })
    emitChange()
  }

  dragData.value = null
}
</script>

<style scoped>
.scene-orchestrator {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 0;
  height: 100%;
}

/* 工具栏 */
.orchestrator-toolbar {
  padding: 10px 16px;
  background: var(--color-fill-1);
  border-bottom: 1px solid var(--color-border-2);
  flex-shrink: 0;
}

/* 主体 */
.orchestrator-body {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

/* 流程图区域 */
.flow-canvas {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
  min-width: 0;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 24px;
  color: var(--color-text-3);
}

.empty-icon { margin-bottom: 16px; opacity: 0.4; }
.empty-title { font-size: 16px; font-weight: 500; color: var(--color-text-2); margin-bottom: 8px; }
.empty-desc { font-size: 13px; }

/* 流程列表 */
.flow-list {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.flow-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 480px;
}

/* 连接线 */
.flow-connector-line {
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 32px;
  justify-content: flex-start;
}

.connector-arrow { margin-top: -2px; }

/* 条件节点容器 */
.flow-condition {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.condition-card {
  width: 100%;
  max-width: 480px;
  padding: 12px 16px;
  background: white;
  border: 2px solid #ff7d00;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-left: 6px solid #ff7d00;
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-main {
  flex: 1;
  min-width: 0;
}

.card-actions {
  display: flex;
  gap: 0;
  flex-shrink: 0;
}

.condition-card:hover {
  box-shadow: 0 4px 12px rgba(255, 125, 0, 0.15);
}

.condition-card.selected {
  border-color: #ff7d00;
  box-shadow: 0 0 0 3px rgba(255, 125, 0, 0.15);
}

.condition-card.disabled { opacity: 0.5; }

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.type-tag { flex-shrink: 0; }

.card-summary {
  margin-top: 6px;
  font-size: 12px;
  color: var(--color-text-3);
  font-family: monospace;
}

/* 分支区域 */
.branches-area {
  width: 100%;
  margin-top: 8px;
}

.branch-fork {
  display: flex;
  justify-content: center;
}

.branch-fork svg {
  width: 100%;
  max-width: 480px;
}

.branches-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  width: 100%;
  max-width: 480px;
  margin: 0 auto;
}

/* 分支列 */
.branch-column {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.branch-label {
  text-align: center;
  font-size: 11px;
  font-weight: 600;
  padding: 4px 0;
  border-radius: 4px;
  margin-bottom: 8px;
}

.branch-label-true {
  background: #e8ffea;
  color: #00b42a;
}

.branch-label-false {
  background: #ffece8;
  color: #f53f3f;
}

.branch-list {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.flow-branch-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}

.branch-connector {
  display: flex;
  justify-content: center;
  height: 20px;
}

.add-branch-btn {
  margin-top: 8px;
  border-style: dashed;
  font-size: 12px;
  height: 32px;
}

/* 属性面板 */
.property-panel {
  width: 340px;
  min-width: 340px;
  border-left: 1px solid var(--color-border-2);
  background: white;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border-2);
  flex-shrink: 0;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-1);
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.panel-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--color-text-3);
  font-size: 13px;
}

/* 底部统计 */
.orchestrator-footer {
  display: flex;
  gap: 16px;
  padding: 8px 16px;
  background: var(--color-fill-1);
  border-top: 1px solid var(--color-border-2);
  font-size: 12px;
  color: var(--color-text-3);
  flex-shrink: 0;
}

.stat-item strong {
  color: var(--color-text-2);
  font-weight: 600;
}
</style>

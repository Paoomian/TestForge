<template>
  <div class="flow-node-wrapper">
    <!-- 条件节点带分支 -->
    <template v-if="node.node_type === 'condition' && hasBranches">
      <!-- 条件节点本身 -->
      <div
        class="flow-node condition-node"
        :class="[statusClass, { selected: selectedId === node.node_id }]"
        @click="$emit('select', node.node_id)"
      >
        <div class="node-accent condition-accent" />
        <div class="node-body">
          <div class="node-top">
            <span class="node-type-badge condition-badge">条件</span>
            <span class="condition-result" :class="node.active_branch === 'true' ? 'result-true' : 'result-false'">
              {{ node.active_branch === 'true' ? '真' : '假' }}
            </span>
          </div>
          <div class="node-name">{{ node.name }}</div>
        </div>
      </div>

      <!-- 分支区域 -->
      <div class="branch-area">
        <div class="branch-fork">
          <div class="fork-line fork-left" :class="{ active: node.active_branch === 'true' }" />
          <div class="fork-line fork-right" :class="{ active: node.active_branch === 'false' }" />
        </div>

        <div class="branch-columns">
          <!-- 真分支 -->
          <div class="branch-col" :class="{ inactive: node.active_branch === 'false' }">
            <div class="branch-tag" :class="{ active: node.active_branch === 'true' }">
              <span class="branch-dot" :class="node.active_branch === 'true' ? 'dot-active' : 'dot-inactive'" />
              真
            </div>
            <div class="branch-children">
              <template v-for="(child, ci) in node.true_branch" :key="child.node_id">
                <FlowNode
                  :node="child"
                  :selected-id="selectedId"
                  :depth="depth + 1"
                  @select="$emit('select', $event)"
                />
                <div v-if="ci < node.true_branch.length - 1" class="flow-connector" />
              </template>
              <div v-if="node.true_branch.length === 0" class="branch-empty">无节点</div>
            </div>
          </div>

          <!-- 假分支 -->
          <div class="branch-col" :class="{ inactive: node.active_branch === 'true' }">
            <div class="branch-tag" :class="{ active: node.active_branch === 'false' }">
              <span class="branch-dot" :class="node.active_branch === 'false' ? 'dot-active' : 'dot-inactive'" />
              假
            </div>
            <div class="branch-children">
              <template v-for="(child, ci) in node.false_branch" :key="child.node_id">
                <FlowNode
                  :node="child"
                  :selected-id="selectedId"
                  :depth="depth + 1"
                  @select="$emit('select', $event)"
                />
                <div v-if="ci < node.false_branch.length - 1" class="flow-connector" />
              </template>
              <div v-if="node.false_branch.length === 0" class="branch-empty">无节点</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 合流连接线 -->
      <div class="flow-connector merge-connector" />
    </template>

    <!-- 普通节点 -->
    <div
      v-else
      class="flow-node"
      :class="[statusClass, nodeTypeClass, { selected: selectedId === node.node_id }]"
      @click="$emit('select', node.node_id)"
    >
      <div class="node-accent" :class="`accent-${node.node_type}`" />
      <div class="node-body">
        <div class="node-top">
          <span class="node-type-badge" :class="`badge-${node.node_type}`">{{ nodeTypeLabel }}</span>
          <span class="node-status-dot" :class="`dot-${node.status}`" />
        </div>
        <div class="node-name">{{ node.name }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { NodeTreeItem } from '@/api/batchRun'

interface Props {
  node: NodeTreeItem
  selectedId: number | null
  depth: number
}

const props = defineProps<Props>()
defineEmits<{ select: [nodeId: number] }>()

const hasBranches = computed(() =>
  props.node.true_branch.length > 0 || props.node.false_branch.length > 0
)

const nodeTypeLabel = computed(() => {
  const map: Record<string, string> = { api_call: '接口', condition: '条件', wait: '等待', data_assign: '赋值' }
  return map[props.node.node_type] || '节点'
})

const statusClass = computed(() => `status-${props.node.status}`)
const nodeTypeClass = computed(() => `type-${props.node.node_type}`)
</script>

<style scoped>
.flow-node-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* ========== 节点卡片 ========== */
.flow-node {
  display: flex;
  align-items: stretch;
  border-radius: 8px;
  border: 1px solid var(--color-border-2);
  background: var(--color-bg-2);
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 220px;
  max-width: 480px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.flow-node:hover {
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.flow-node.selected {
  border-color: #165dff;
  box-shadow: 0 0 0 2px rgba(22, 93, 255, 0.15), 0 3px 12px rgba(0, 0, 0, 0.1);
}

/* 左侧彩条 */
.node-accent {
  width: 4px;
  flex-shrink: 0;
  background: var(--color-border-3);
}

.accent-api_call { background: #165dff; }
.accent-wait { background: #86909c; }
.accent-data_assign { background: #00b42a; }
.condition-accent { background: #ff7d00; }

/* 节点内容 */
.node-body {
  flex: 1;
  padding: 10px 14px;
  min-width: 0;
}

.node-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

/* 类型标签 */
.node-type-badge {
  font-size: 11px;
  font-weight: 500;
  padding: 1px 8px;
  border-radius: 4px;
  line-height: 18px;
}

.badge-api_call {
  background: #e8f3ff;
  color: #165dff;
}

.badge-wait {
  background: var(--color-fill-2);
  color: var(--color-text-3);
}

.badge-data_assign {
  background: #e8ffea;
  color: #00b42a;
}

.condition-badge {
  background: #fff7e6;
  color: #ff7d00;
}

/* 节点名称 */
.node-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 20px;
}

/* 状态圆点 */
.node-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot-pass { background: #00b42a; }
.dot-fail { background: #f53f3f; }
.dot-error { background: #ff7d00; }
.dot-skipped { background: var(--color-border-3); }
.dot-pending { background: var(--color-border-3); }
.dot-running { background: #165dff; animation: pulse 1s infinite; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* 条件结果标签 */
.condition-result {
  font-size: 12px;
  font-weight: 600;
  padding: 1px 10px;
  border-radius: 4px;
  line-height: 20px;
}

.result-true {
  background: #e8ffea;
  color: #00b42a;
}

.result-false {
  background: #fff1f0;
  color: #f53f3f;
}

/* ========== 状态卡片样式 ========== */
.flow-node.status-pass {
  border-color: #b7eb8f;
  background: #f6ffed;
}

.flow-node.status-pass .node-accent { background: #00b42a; }

.flow-node.status-fail {
  border-color: #ffa39e;
  background: #fff1f0;
}

.flow-node.status-fail .node-accent { background: #f53f3f; }

.flow-node.status-error {
  border-color: #ffbb96;
  background: #fff7e6;
}

.flow-node.status-error .node-accent { background: #ff7d00; }

.flow-node.status-skipped {
  border-color: var(--color-border-2);
  background: var(--color-fill-1);
  opacity: 0.55;
}

.flow-node.status-skipped .node-accent { background: var(--color-border-3); }

/* ========== 分支区域 ========== */
.branch-area {
  width: 100%;
  margin-top: 6px;
}

/* Y形分叉线 */
.branch-fork {
  display: flex;
  justify-content: center;
  position: relative;
  height: 24px;
  margin: 0 25%;
}

.fork-line {
  position: absolute;
  top: 0;
  height: 24px;
  border-left: 2px solid var(--color-border-3);
}

.fork-left {
  left: 0;
  border-bottom-left-radius: 8px;
  transform-origin: top left;
}

.fork-right {
  right: 0;
  border-bottom-right-radius: 8px;
  transform-origin: top right;
}

.fork-line.active {
  border-color: #165dff;
}

/* 分支列 */
.branch-columns {
  display: flex;
  gap: 12px;
}

.branch-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 10px 8px;
  border-radius: 8px;
  background: var(--color-fill-1);
  border: 1px dashed var(--color-border-2);
  min-height: 60px;
  transition: all 0.2s;
}

.branch-col.inactive {
  opacity: 0.4;
}

/* 分支标签 */
.branch-tag {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 12px;
  border-radius: 10px;
  background: var(--color-fill-3);
  color: var(--color-text-3);
}

.branch-tag.active {
  background: #165dff;
  color: #fff;
}

.branch-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.dot-active {
  background: #fff;
}

.dot-inactive {
  background: var(--color-border-3);
}

/* 分支子节点区域 */
.branch-children {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0;
  width: 100%;
}

.branch-empty {
  font-size: 12px;
  color: var(--color-text-4);
  padding: 16px 8px;
}

/* 连接线 */
.flow-connector {
  width: 2px;
  height: 12px;
  background: var(--color-border-3);
  margin: 0 auto;
}

.merge-connector {
  margin-top: 6px;
}
</style>

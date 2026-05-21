<template>
  <div class="scene-orchestrator">
    <!-- 空状态 -->
    <div v-if="nodes.length === 0" class="empty-state">
      <div class="empty-icon">
        <icon-layers :size="48" />
      </div>
      <div class="empty-title">暂无编排节点</div>
      <div class="empty-desc">点击下方按钮添加节点，开始编排测试场景</div>
    </div>

    <!-- 节点列表 -->
    <div v-else class="node-list">
      <div
        v-for="(node, index) in nodes"
        :key="node.id || `new-${index}`"
        class="node-wrapper"
      >
        <!-- 连接线 -->
        <div v-if="index > 0" class="node-connector">
          <div class="connector-line"></div>
          <div class="connector-arrow"></div>
        </div>

        <!-- 节点序号 -->
        <div class="node-index">{{ index + 1 }}</div>

        <!-- 节点卡片 -->
        <div class="node-card-wrapper">
          <SceneNodeCard
            :node="node"
            :cases="cases"
            :nodes="nodes"
            @update="updateNode(index, $event)"
            @remove="removeNode(index)"
          />
        </div>
      </div>
    </div>

    <!-- 添加节点按钮 -->
    <div class="add-node-section" :class="{ 'has-nodes': nodes.length > 0 }">
      <a-dropdown @select="addNode" trigger="click">
        <a-button type="dashed" long class="add-node-btn">
          <template #icon><icon-plus /></template>
          添加节点
        </a-button>
        <template #content>
          <a-doption value="api_call">
            <div class="doption-content">
              <icon-code class="doption-icon api_call" />
              <div class="doption-text">
                <div class="doption-title">接口调用</div>
                <div class="doption-desc">执行一个测试用例</div>
              </div>
            </div>
          </a-doption>
          <a-doption value="condition">
            <div class="doption-content">
              <icon-branch class="doption-icon condition" />
              <div class="doption-text">
                <div class="doption-title">条件判断</div>
                <div class="doption-desc">根据变量值决定执行路径</div>
              </div>
            </div>
          </a-doption>
          <a-doption value="wait">
            <div class="doption-content">
              <icon-clock-circle class="doption-icon wait" />
              <div class="doption-text">
                <div class="doption-title">等待延时</div>
                <div class="doption-desc">暂停指定时间后继续</div>
              </div>
            </div>
          </a-doption>
          <a-doption value="data_assign">
            <div class="doption-content">
              <icon-storage class="doption-icon data_assign" />
              <div class="doption-text">
                <div class="doption-title">数据赋值</div>
                <div class="doption-desc">设置变量供后续节点使用</div>
              </div>
            </div>
          </a-doption>
        </template>
      </a-dropdown>
    </div>

    <!-- 底部统计 -->
    <div v-if="nodes.length > 0" class="orchestrator-footer">
      <div class="footer-stats">
        <span class="stat-item">
          <icon-layers /> 共 <strong>{{ nodes.length }}</strong> 个节点
        </span>
        <span class="stat-item">
          <icon-code /> 接口调用: <strong>{{ apiCallCount }}</strong>
        </span>
        <span class="stat-item">
          <icon-branch /> 条件: <strong>{{ conditionCount }}</strong>
        </span>
        <span class="stat-item">
          <icon-clock-circle /> 等待: <strong>{{ waitCount }}</strong>
        </span>
        <span class="stat-item">
          <icon-storage /> 赋值: <strong>{{ dataAssignCount }}</strong>
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { SceneNodeItem, SceneNodeType } from '@/api/sceneNode'
import type { APITestCase } from '@/api/apiTestCase'
import SceneNodeCard from './SceneNodeCard.vue'

const props = defineProps<{
  modelValue: SceneNodeItem[]
  cases: APITestCase[]
  suiteId: number
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: SceneNodeItem[]): void
}>()

const nodes = ref<SceneNodeItem[]>([])

// 同步 props 到本地
watch(() => props.modelValue, (val) => {
  nodes.value = (val || []).map(n => ({ ...n }))
}, { immediate: true })

// 统计
const apiCallCount = computed(() => nodes.value.filter(n => n.node_type === 'api_call').length)
const conditionCount = computed(() => nodes.value.filter(n => n.node_type === 'condition').length)
const waitCount = computed(() => nodes.value.filter(n => n.node_type === 'wait').length)
const dataAssignCount = computed(() => nodes.value.filter(n => n.node_type === 'data_assign').length)

function emitChange() {
  emit('update:modelValue', nodes.value.map((n, i) => ({ ...n, sort_order: i })))
}

function addNode(type: SceneNodeType) {
  const defaultNames: Record<SceneNodeType, string> = {
    api_call: '接口调用',
    condition: '条件判断',
    wait: '等待',
    data_assign: '数据赋值'
  }

  const newNode: SceneNodeItem = {
    suite_id: props.suiteId,
    node_type: type,
    name: defaultNames[type] || '新节点',
    enabled: true,
    sort_order: nodes.value.length,
    wait_seconds: 5,
    assign_source: 'static'
  }

  nodes.value.push(newNode)
  emitChange()
}

function updateNode(index: number, data: Partial<SceneNodeItem>) {
  Object.assign(nodes.value[index], data)
  emitChange()
}

function removeNode(index: number) {
  nodes.value.splice(index, 1)
  emitChange()
}
</script>

<style scoped>
.scene-orchestrator {
  width: 100%;
  min-height: 200px;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  color: var(--color-text-3);
}

.empty-icon {
  margin-bottom: 16px;
  opacity: 0.4;
}

.empty-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text-2);
  margin-bottom: 8px;
}

.empty-desc {
  font-size: 13px;
}

/* 节点列表 */
.node-list {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.node-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  position: relative;
}

.node-connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 32px;
  justify-content: center;
}

.connector-line {
  width: 2px;
  height: 20px;
  background: var(--color-border-3);
}

.connector-arrow {
  width: 0;
  height: 0;
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
  border-top: 8px solid var(--color-border-3);
}

.node-index {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-fill-2);
  border-radius: 50%;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-2);
}

.node-card-wrapper {
  width: 100%;
  padding-left: 32px;
}

/* 添加节点区域 */
.add-node-section {
  margin-top: 20px;
  padding-left: 32px;
}

.add-node-section.has-nodes {
  margin-top: 24px;
}

.add-node-btn {
  border-style: dashed;
  height: 44px;
}

/* 下拉选项样式 */
.doption-content {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 0;
}

.doption-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.doption-icon.api_call {
  color: #3370ff;
}

.doption-icon.condition {
  color: #ff7d00;
}

.doption-icon.wait {
  color: #86909c;
}

.doption-icon.data_assign {
  color: #00b42a;
}

.doption-text {
  flex: 1;
}

.doption-title {
  font-size: 13px;
  font-weight: 500;
}

.doption-desc {
  font-size: 11px;
  color: var(--color-text-3);
  margin-top: 2px;
}

/* 底部统计 */
.orchestrator-footer {
  margin-top: 20px;
  padding: 12px 16px;
  background: var(--color-fill-1);
  border-radius: var(--radius-small);
  margin-left: 32px;
}

.footer-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 12px;
  color: var(--color-text-3);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-item strong {
  color: var(--color-text-2);
  font-weight: 600;
}
</style>

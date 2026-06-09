<template>
  <a-drawer
    :visible="visible"
    title="批量执行配置"
    :width="480"
    :mask-closable="false"
    @update:visible="$emit('update:visible', $event)"
    @close="handleClose"
  >
    <div class="batch-drawer">
      <!-- 已选用例 -->
      <div class="section">
        <div class="section-header">
          <span class="section-title">已选用例 ({{ cases.length }})</span>
        </div>
        <div class="case-list">
          <div
            v-for="(c, index) in sortedCases"
            :key="c.id"
            class="case-item"
            draggable="true"
            @dragstart="onDragStart(index, $event)"
            @dragover.prevent="onDragOver(index)"
            @drop="onDrop(index)"
            @dragend="onDragEnd"
          >
            <icon-drag-dot-vertical class="drag-icon" />
            <span class="case-index">{{ index + 1 }}</span>
            <span class="case-name">{{ c.name }}</span>
            <a-button type="text" size="mini" status="danger" @click="removeCase(index)">
              <template #icon><icon-close /></template>
            </a-button>
          </div>
        </div>
      </div>

      <!-- 执行环境 -->
      <div class="section">
        <div class="section-title">执行环境</div>
        <a-select
          v-model="form.environment_id"
          placeholder="选择环境（可选）"
          allow-clear
          :loading="envLoading"
        >
          <a-option v-for="env in environments" :key="env.id" :value="env.id">
            {{ env.name }}
          </a-option>
        </a-select>
      </div>

      <!-- 失败策略 -->
      <div class="section">
        <div class="section-title">失败策略</div>
        <a-radio-group v-model="form.failure_strategy">
          <a-radio value="continue">继续执行后续用例</a-radio>
          <a-radio value="stop">遇到失败停止执行</a-radio>
        </a-radio-group>
      </div>

      <!-- 浏览器配置 -->
      <div class="section">
        <div class="section-title">浏览器配置</div>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="浏览器">
              <a-select v-model="form.browser">
                <a-option value="chrome">Chrome</a-option>
                <a-option value="firefox">Firefox</a-option>
                <a-option value="edge">Edge</a-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="视口尺寸">
              <a-select v-model="form.viewport">
                <a-option value="1280x720">1280 x 720</a-option>
                <a-option value="1920x1080">1920 x 1080</a-option>
                <a-option value="375x812">iPhone (375 x 812)</a-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
      </div>
    </div>

    <template #footer>
      <div class="drawer-footer">
        <a-button @click="handleClose">取消</a-button>
        <a-button type="primary" :loading="submitting" @click="handleSubmit">
          <template #icon><icon-play-arrow /></template>
          开始执行
        </a-button>
      </div>
    </template>
  </a-drawer>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { Message } from '@arco-design/web-vue'
import {
  IconClose,
  IconDragDotVertical,
  IconPlayArrow,
} from '@arco-design/web-vue/es/icon'
import type { UICase } from '@/api/uiCase'
import { getEnvironments } from '@/api/environment'
import type { Environment } from '@/api/apiTestCase'
import { createUIBatchRun } from '@/api/uiBatchRun'

interface Props {
  visible: boolean
  cases: UICase[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:visible': [value: boolean]
  success: [runId: number]
}>()

// 排序后的用例列表
const sortedCases = ref<UICase[]>([])

// 表单
const form = reactive({
  environment_id: undefined as number | undefined,
  failure_strategy: 'continue',
  browser: 'chrome',
  viewport: '1280x720',
})

// 环境列表
const environments = ref<Environment[]>([])
const envLoading = ref(false)

// 提交状态
const submitting = ref(false)

// 拖拽相关
let dragIndex = -1

// 监听 cases 变化，初始化排序列表
watch(() => props.cases, (newCases) => {
  sortedCases.value = [...newCases]
}, { immediate: true })

// 加载环境列表
watch(() => props.visible, async (visible) => {
  if (visible && props.cases.length > 0) {
    const projectId = props.cases[0].project_id
    if (projectId) {
      envLoading.value = true
      try {
        environments.value = await getEnvironments(projectId)
      } catch (e) {
        console.error('加载环境列表失败:', e)
      } finally {
        envLoading.value = false
      }
    }
  }
})

// 移除用例
function removeCase(index: number) {
  sortedCases.value.splice(index, 1)
}

// 拖拽函数
function onDragStart(index: number, event: DragEvent) {
  dragIndex = index
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
  }
}

function onDragOver(_index: number) {
  // 允许拖放
}

function onDrop(toIndex: number) {
  if (dragIndex === -1 || dragIndex === toIndex) return
  const item = sortedCases.value.splice(dragIndex, 1)[0]
  sortedCases.value.splice(toIndex, 0, item)
  dragIndex = -1
}

function onDragEnd() {
  dragIndex = -1
}

// 关闭抽屉
function handleClose() {
  emit('update:visible', false)
}

// 提交
async function handleSubmit() {
  if (sortedCases.value.length === 0) {
    Message.warning('请至少选择一个用例')
    return
  }

  submitting.value = true
  try {
    // 解析视口尺寸
    const [width, height] = form.viewport.split('x').map(Number)

    const result = await createUIBatchRun({
      case_ids: sortedCases.value.map(c => c.id),
      environment_id: form.environment_id,
      failure_strategy: form.failure_strategy,
      browser: form.browser,
      viewport_width: width,
      viewport_height: height,
    })

    Message.success('批量执行任务已创建')
    // result 包含完整的任务信息，其中 id 是任务ID
    const data = result as any
    emit('success', data.id)
  } catch (e: any) {
    Message.error(e?.detail || '创建失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.batch-drawer {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-1);
}

.case-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 8px;
}

.case-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--color-fill-1);
  border-radius: 4px;
  cursor: grab;
  transition: background 0.2s;
}

.case-item:hover {
  background: var(--color-fill-2);
}

.case-item:active {
  cursor: grabbing;
}

.drag-icon {
  color: var(--color-text-3);
  font-size: 14px;
}

.case-index {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-fill-2);
  border-radius: 4px;
  font-size: 12px;
  color: var(--color-text-2);
}

.case-name {
  flex: 1;
  font-size: 13px;
  color: var(--color-text-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>

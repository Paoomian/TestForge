<template>
  <a-drawer
    :width="600"
    :visible="visible"
    title="批量执行配置"
    @update:visible="$emit('update:visible', $event)"
    :mask-closable="false"
  >
    <a-form :model="form" layout="vertical">
      <!-- 已选用例 -->
      <a-form-item label="已选用例">
        <div class="case-summary">
          <a-tag color="arcoblue">{{ sortedCases.length }} 个用例</a-tag>
          <span class="drag-hint">拖拽调整执行顺序</span>
        </div>
        <div class="case-list">
          <div
            v-for="(item, index) in sortedCases"
            :key="item.id"
            class="case-item"
            :class="{ 'drag-over': dragOverIndex === index, 'dragging': dragIndex === index }"
            draggable="true"
            @dragstart="onDragStart(index, $event)"
            @dragover.prevent="onDragOver(index)"
            @dragleave="onDragLeave"
            @drop="onDrop(index)"
            @dragend="onDragEnd"
          >
            <icon-drag-dot-vertical class="drag-handle" />
            <span class="case-order">{{ index + 1 }}</span>
            <span class="case-name" :title="item.name">{{ item.name }}</span>
            <a-tag size="small" :color="getMethodColor(item.method)">{{ item.method }}</a-tag>
          </div>
        </div>
      </a-form-item>

      <!-- 执行环境 -->
      <a-form-item label="执行环境">
        <a-select
          v-model="form.environment_id"
          placeholder="选择执行环境（可选）"
          allow-clear
          :loading="envLoading"
        >
          <a-option
            v-for="env in environments"
            :key="env.id"
            :value="env.id"
          >
            {{ env.name }}
          </a-option>
        </a-select>
      </a-form-item>

      <!-- 并发数 -->
      <a-form-item label="并发数">
        <a-radio-group v-model="form.concurrency" type="button">
          <a-radio :value="1">串行</a-radio>
          <a-radio :value="3">3 并发</a-radio>
          <a-radio :value="5">5 并发</a-radio>
          <a-radio :value="10">10 并发</a-radio>
        </a-radio-group>
      </a-form-item>

      <!-- 失败策略 -->
      <a-form-item label="失败策略">
        <a-radio-group v-model="form.failure_strategy">
          <a-radio value="continue">继续执行后续用例</a-radio>
          <a-radio value="stop">遇到失败停止执行</a-radio>
        </a-radio-group>
      </a-form-item>

      <!-- 额外变量 -->
      <a-form-item label="额外变量">
        <div class="variable-header">
          <a-button size="mini" @click="addVariable">
            <template #icon><icon-plus /></template>
            添加
          </a-button>
        </div>
        <div v-for="(item, index) in variableList" :key="index" class="variable-row">
          <a-input
            v-model="item.key"
            placeholder="变量名"
            style="width: 40%"
          />
          <a-input
            v-model="item.value"
            placeholder="变量值"
            style="flex: 1"
          />
          <a-button
            type="text"
            status="danger"
            size="small"
            @click="removeVariable(index)"
          >
            <template #icon><icon-delete /></template>
          </a-button>
        </div>
      </a-form-item>
    </a-form>

    <template #footer>
      <a-space>
        <a-button @click="$emit('update:visible', false)">取消</a-button>
        <a-button type="primary" :loading="loading" @click="handleSubmit">
          <template #icon><icon-play-arrow /></template>
          开始执行
        </a-button>
      </a-space>
    </template>
  </a-drawer>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { Message } from '@arco-design/web-vue'
import { createBatchRun } from '@/api/batchRun'
import { getEnvironments } from '@/api/environment'
import type { Environment } from '@/api/apiTestCase'
import type { APITestCase } from '@/api/apiTestCase'

interface Props {
  visible: boolean
  cases: APITestCase[]
  projectId?: number
}

interface VariableItem {
  key: string
  value: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'success', runId: number): void
}>()

// 拖拽排序状态
const sortedCases = ref<APITestCase[]>([])
const dragIndex = ref(-1)
const dragOverIndex = ref(-1)

// 监听 cases 变化，同步到本地排序列表
watch(() => props.cases, (val) => {
  sortedCases.value = [...val]
}, { immediate: true })

const onDragStart = (index: number, e: DragEvent) => {
  dragIndex.value = index
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move'
  }
}

const onDragOver = (index: number) => {
  if (dragIndex.value !== index) {
    dragOverIndex.value = index
  }
}

const onDragLeave = () => {
  dragOverIndex.value = -1
}

const onDrop = (index: number) => {
  if (dragIndex.value === -1 || dragIndex.value === index) return
  const list = [...sortedCases.value]
  const [moved] = list.splice(dragIndex.value, 1)
  list.splice(index, 0, moved)
  sortedCases.value = list
  dragIndex.value = -1
  dragOverIndex.value = -1
}

const onDragEnd = () => {
  dragIndex.value = -1
  dragOverIndex.value = -1
}

const loading = ref(false)
const envLoading = ref(false)
const environments = ref<Environment[]>([])
const variableList = ref<VariableItem[]>([])

const form = reactive({
  environment_id: undefined as number | undefined,
  concurrency: 1 as 1 | 3 | 5 | 10,
  failure_strategy: 'continue' as 'continue' | 'stop'
})

// 加载环境列表
watch(() => props.visible, async (val) => {
  if (val && props.projectId) {
    await loadEnvironments()
  }
})

const loadEnvironments = async () => {
  if (!props.projectId) return
  envLoading.value = true
  try {
    environments.value = await getEnvironments(props.projectId)
  } catch (e) {
    console.error('加载环境失败:', e)
  } finally {
    envLoading.value = false
  }
}

const addVariable = () => {
  variableList.value.push({ key: '', value: '' })
}

const removeVariable = (index: number) => {
  variableList.value.splice(index, 1)
}

const getMethodColor = (method: string) => {
  const colors: Record<string, string> = {
    GET: 'blue', POST: 'green', PUT: 'orange', DELETE: 'red', PATCH: 'purple'
  }
  return colors[method] || 'gray'
}

const handleSubmit = async () => {
  if (sortedCases.value.length === 0) {
    Message.warning('请选择要执行的用例')
    return
  }

  // 构建变量
  const variables: Record<string, string> = {}
  for (const item of variableList.value) {
    if (item.key.trim()) {
      variables[item.key.trim()] = item.value
    }
  }

  loading.value = true
  try {
    const result = await createBatchRun({
      case_ids: sortedCases.value.map(c => c.id),
      environment_id: form.environment_id,
      concurrency: form.concurrency,
      failure_strategy: form.failure_strategy,
      variables
    })
    Message.success('批量执行任务已创建')
    emit('update:visible', false)
    emit('success', result.id)
  } catch (e: any) {
    Message.error(e?.message || '创建失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.case-summary {
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.drag-hint {
  font-size: 12px;
  color: var(--color-text-3);
}

.case-list {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid var(--color-border-2);
  border-radius: var(--radius-small);
  padding: 4px;
}

.case-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: var(--radius-small);
  cursor: grab;
  transition: background 0.15s, box-shadow 0.15s;

  &:hover {
    background: var(--color-fill-1);
  }

  &.dragging {
    opacity: 0.4;
    background: var(--color-fill-2);
  }

  &.drag-over {
    background: var(--color-primary-light-1);
    box-shadow: 0 -2px 0 0 var(--color-primary-6);
  }
}

.drag-handle {
  color: var(--color-text-3);
  cursor: grab;
  flex-shrink: 0;
}

.case-order {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-fill-2);
  border-radius: 50%;
  font-size: 12px;
  color: var(--color-text-3);
  flex-shrink: 0;
}

.case-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
}

.variable-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}

.variable-row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  align-items: center;
}
</style>

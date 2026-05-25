<template>
  <div class="task-list">
    <a-table
      :columns="columns"
      :data="tasks"
      :pagination="false"
      :loading="loading"
    >
      <template #status="{ record }">
        <a-tooltip v-if="record.status === 'failed' && record.error_message" :content="record.error_message" position="tl">
          <a-tag :color="getStatusColor(record.status)">
            {{ getStatusText(record.status) }}
          </a-tag>
        </a-tooltip>
        <a-tooltip v-else-if="record.status === 'processing'" :content="record.error_message || '处理中...'" position="tl">
          <a-tag :color="getStatusColor(record.status)">
            {{ getStatusText(record.status) }}
          </a-tag>
        </a-tooltip>
        <a-tag v-else :color="getStatusColor(record.status)">
          {{ getStatusText(record.status) }}
        </a-tag>
      </template>

      <template #input_type="{ record }">
        <a-tag :color="getInputTypeColor(record.input_type)">
          {{ getInputTypeText(record.input_type) }}
        </a-tag>
      </template>

      <template #generate_type="{ record }">
        <a-tag :color="getGenerateTypeColor(record.generate_type)">
          {{ getGenerateTypeText(record.generate_type) }}
        </a-tag>
      </template>

      <template #created_at="{ record }">
        {{ formatTime(record.created_at) }}
      </template>

      <template #actions="{ record }">
        <a-space>
          <a-button
            v-if="record.status === 'completed' || record.status === 'processing' || record.status === 'pending'"
            type="text"
            size="small"
            @click="$emit('view', record)"
          >
            {{ record.status === 'completed' ? '查看结果' : '查看详情' }}
          </a-button>
          <a-button
            v-if="record.status === 'failed'"
            type="text"
            size="small"
            @click="$emit('retry', record.id)"
          >
            重试
          </a-button>
          <a-button
            v-if="record.status === 'processing' || record.status === 'pending'"
            type="text"
            size="small"
            status="danger"
            @click="$emit('cancel', record.id)"
          >
            取消
          </a-button>
          <a-button
            v-if="record.status !== 'processing' && record.status !== 'pending'"
            type="text"
            size="small"
            status="danger"
            @click="handleDelete(record.id)"
          >
            删除
          </a-button>
        </a-space>
      </template>
    </a-table>
  </div>
</template>

<script setup lang="ts">
import { Modal } from '@arco-design/web-vue'
import type { AIGenerateTask } from '@/api/aiGenerate'

defineProps<{
  tasks: AIGenerateTask[]
  loading?: boolean
}>()

const emit = defineEmits<{
  refresh: []
  view: [task: AIGenerateTask]
  delete: [taskId: number]
  retry: [taskId: number]
  cancel: [taskId: number]
}>()

const columns = [
  { title: 'ID', dataIndex: 'id', width: 60, align: 'center' as const },
  { title: '输入类型', dataIndex: 'input_type', slotName: 'input_type', width: 90 },
  { title: '生成类型', dataIndex: 'generate_type', slotName: 'generate_type', width: 100 },
  { title: '状态', dataIndex: 'status', slotName: 'status', width: 100 },
  { title: '数量', dataIndex: 'cases_count', width: 60, align: 'center' as const },
  { title: '创建时间', dataIndex: 'created_at', slotName: 'created_at', width: 150 },
  { title: '操作', slotName: 'actions', width: 150, fixed: 'right' as const }
] as any[]

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    pending: 'blue',
    processing: 'orange',
    completed: 'green',
    failed: 'red',
    cancelled: 'gray'
  }
  return colors[status] || 'gray'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: '等待中',
    processing: '生成中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return texts[status] || status
}

const getInputTypeText = (type: string) => {
  const texts: Record<string, string> = {
    prd: 'PRD 文档',
    swagger: '接口文档',
    text: '文本输入'
  }
  return texts[type] || type
}

const getGenerateTypeText = (type: string) => {
  const texts: Record<string, string> = {
    functional: '功能测试',
    api: '接口测试'
  }
  return texts[type] || type
}

const getInputTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    prd: 'blue',
    swagger: 'green',
    text: 'orange'
  }
  return colors[type] || 'gray'
}

const getGenerateTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    functional: 'purple',
    api: 'cyan'
  }
  return colors[type] || 'gray'
}

const formatTime = (time: string) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const handleDelete = (taskId: number) => {
  Modal.confirm({
    title: '确认删除',
    content: '确定要删除这个任务吗？',
    onOk: () => {
      emit('delete', taskId)
    }
  })
}
</script>

<style scoped>
.task-list {
  width: 100%;
}
</style>

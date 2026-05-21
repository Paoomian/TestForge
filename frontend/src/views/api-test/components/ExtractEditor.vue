<template>
  <div class="extract-editor">
    <div v-if="extractors.length === 0" class="empty-hint">
      暂无数据提取规则，点击下方按钮添加
    </div>
    <div v-for="(item, index) in extractors" :key="index" class="extract-item">
      <div class="extract-item-header">
        <span class="extract-index">#{{ index + 1 }}</span>
        <a-button type="text" size="mini" status="danger" @click="removeItem(index)">
          <template #icon><icon-delete /></template>
        </a-button>
      </div>
      <a-form :model="item" layout="vertical" size="small">
        <a-row :gutter="12">
          <a-col :span="6">
            <a-form-item label="变量名" required>
              <a-input v-model="item.name" placeholder="token" @input="emitChange()" />
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="提取来源" required>
              <a-select v-model="item.source" @change="emitChange()">
                <a-option value="jsonpath">jsonpath</a-option>
                <a-option value="regex">regex</a-option>
                <a-option value="header">header</a-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="默认值">
              <a-input v-model="item.default_value" placeholder="可选" @input="emitChange()" />
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="说明">
              <a-input v-model="item.description" placeholder="可选" @input="emitChange()" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="表达式" required>
          <a-input v-model="item.expression" :placeholder="getPlaceholder(item.source)" @input="emitChange()" />
        </a-form-item>
      </a-form>
    </div>
    <a-button type="dashed" size="small" long @click="addItem">
      <template #icon><icon-plus /></template>
      添加数据提取
    </a-button>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { IconDelete, IconPlus } from '@arco-design/web-vue/es/icon'
import type { ExtractItem } from '@/api/apiTestCase'

const props = defineProps<{
  modelValue: ExtractItem[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: ExtractItem[]): void
}>()

const extractors = ref<ExtractItem[]>([])

// 监听props变化，同步到本地（仅在父组件主动设置时）
watch(() => props.modelValue, (newValue) => {
  if (JSON.stringify(newValue) !== JSON.stringify(extractors.value)) {
    extractors.value = (newValue || []).map(e => ({ ...e }))
  }
}, { immediate: true })

function emitChange() {
  emit('update:modelValue', extractors.value.map((e, i) => ({ ...e, sort_order: i })))
}

const getPlaceholder = (source: string) => {
  const placeholders: Record<string, string> = {
    jsonpath: '$.data.token',
    regex: '"token":"(.*?)"',
    header: 'Content-Type',
  }
  return placeholders[source] || ''
}

const addItem = () => {
  extractors.value.push({
    name: '',
    source: 'jsonpath',
    expression: '',
    default_value: '',
    description: '',
    sort_order: extractors.value.length,
  })
  emitChange()
}

const removeItem = (index: number) => {
  extractors.value.splice(index, 1)
  emitChange()
}
</script>

<style scoped>
.extract-editor {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.empty-hint {
  text-align: center;
  color: var(--color-text-3);
  padding: var(--space-lg);
  background: var(--color-fill-1);
  border-radius: var(--radius-md);
}

.extract-item {
  background: var(--color-fill-1);
  border: 1px solid var(--color-border-2);
  border-radius: var(--radius-md);
  padding: var(--space-md);
}

.extract-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-sm);
}

.extract-index {
  font-size: 12px;
  color: var(--color-text-3);
  font-weight: 500;
}

.extract-item :deep(.arco-form-item) {
  margin-bottom: 0;
}

.extract-item :deep(.arco-form-item-label) {
  font-size: 12px;
  color: var(--color-text-2);
}
</style>

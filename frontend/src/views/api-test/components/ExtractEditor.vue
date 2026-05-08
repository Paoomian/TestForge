<template>
  <div class="extract-editor">
    <div class="extract-list">
      <div v-for="(item, index) in extracts" :key="index" class="extract-item">
        <a-card :bordered="true" size="small">
          <template #extra>
            <a-button
              type="text"
              size="small"
              status="danger"
              @click="removeExtract(index)"
            >
              <template #icon><icon-delete /></template>
            </a-button>
          </template>

          <a-form :model="item" layout="vertical">
            <a-row :gutter="16">
              <a-col :span="6">
                <a-form-item label="变量名">
                  <a-input
                    v-model="item.name"
                    placeholder="例如: token"
                    size="small"
                    @change="emitChange"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="4">
                <a-form-item label="来源">
                  <a-select v-model="item.source" size="small" @change="emitChange">
                    <a-option value="jsonpath">JSONPath</a-option>
                    <a-option value="regex">正则</a-option>
                    <a-option value="header">响应头</a-option>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item :label="getExprLabel(item.source)">
                  <a-input
                    v-model="item.expression"
                    :placeholder="getExprPlaceholder(item.source)"
                    size="small"
                    @change="emitChange"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="4">
                <a-form-item label="默认值">
                  <a-input
                    v-model="item.default_value"
                    placeholder="可选"
                    size="small"
                    @change="emitChange"
                  />
                </a-form-item>
              </a-col>
            </a-row>
          </a-form>
        </a-card>
      </div>
    </div>

    <a-button type="dashed" long @click="addExtract" style="margin-top: 8px;">
      <template #icon><icon-plus /></template>
      添加变量提取
    </a-button>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { ExtractItem } from '@/api/apiTestCase'

const props = defineProps<{
  modelValue: ExtractItem[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: ExtractItem[]): void
}>()

const extracts = ref<ExtractItem[]>([])

// 监听props变化，同步到本地
watch(() => props.modelValue, (newValue) => {
  if (JSON.stringify(newValue) !== JSON.stringify(extracts.value)) {
    extracts.value = (newValue || []).map(e => ({ ...e }))
  }
}, { immediate: true })

function emitChange() {
  emit('update:modelValue', extracts.value.map((e, i) => ({ ...e, sort_order: i })))
}

function addExtract() {
  extracts.value.push({
    name: '',
    source: 'jsonpath',
    expression: '',
    default_value: '',
    description: '',
  })
  emitChange()
}

function removeExtract(index: number) {
  extracts.value.splice(index, 1)
  emitChange()
}

function getExprLabel(source: string) {
  const map: Record<string, string> = {
    jsonpath: 'JSONPath表达式',
    regex: '正则表达式',
    header: '响应头名称',
  }
  return map[source] || '表达式'
}

function getExprPlaceholder(source: string) {
  const map: Record<string, string> = {
    jsonpath: '$.data.access_token',
    regex: '"token":"([^"]+)"',
    header: 'X-Request-Id',
  }
  return map[source] || ''
}
</script>

<style scoped>
.extract-editor {
  width: 100%;
}

.extract-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.extract-item {
  width: 100%;
}
</style>

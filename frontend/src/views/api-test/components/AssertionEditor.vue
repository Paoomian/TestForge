<template>
  <div class="assertion-editor">
    <div class="assertion-list">
      <!-- 断言列表 -->
      <div v-for="(assertion, index) in assertions" :key="index" class="assertion-item">
        <a-card :bordered="true" size="small">
          <template #extra>
            <a-button
              type="text"
              size="small"
              status="danger"
              @click="removeAssertion(index)"
            >
              <template #icon><icon-delete /></template>
            </a-button>
          </template>

          <a-form :model="assertion" layout="vertical">
            <a-row :gutter="16">
              <a-col :span="8">
                <a-form-item label="断言类型">
                  <a-select
                    v-model="assertion.assertion_type"
                    placeholder="选择断言类型"
                    @change="handleTypeChange(assertion)"
                  >
                    <a-option value="status_code">状态码</a-option>
                    <a-option value="jsonpath">JSONPath</a-option>
                    <a-option value="header">响应头</a-option>
                    <a-option value="response_time">响应时间(ms)</a-option>
                    <a-option value="body_contains">Body包含</a-option>
                  </a-select>
                </a-form-item>
              </a-col>

              <a-col :span="8">
                <a-form-item label="比较方式">
                  <a-select v-model="assertion.operator" placeholder="选择比较方式" @change="emitChange()">
                    <a-option value="equals">等于</a-option>
                    <a-option value="not_equals">不等于</a-option>
                    <a-option value="contains">包含</a-option>
                    <a-option value="greater_than">大于</a-option>
                    <a-option value="less_than">小于</a-option>
                    <a-option value="regex">正则匹配</a-option>
                    <a-option value="exists">存在</a-option>
                  </a-select>
                </a-form-item>
              </a-col>

              <a-col :span="8">
                <a-form-item
                  v-if="needsField(assertion.assertion_type)"
                  :label="getFieldLabel(assertion.assertion_type)"
                >
                  <a-input
                    v-model="assertion.field"
                    :placeholder="getFieldPlaceholder(assertion.assertion_type)"
                    @input="emitChange()"
                  />
                </a-form-item>
              </a-col>
            </a-row>

            <a-row :gutter="16">
              <a-col :span="16">
                <a-form-item label="期望值">
                  <a-input
                    v-model="assertion.expected"
                    placeholder="输入期望值"
                    @input="emitChange()"
                  />
                </a-form-item>
              </a-col>

              <a-col :span="8">
                <a-form-item label="描述">
                  <a-input
                    v-model="assertion.description"
                    placeholder="断言描述（可选）"
                    @input="emitChange()"
                  />
                </a-form-item>
              </a-col>
            </a-row>
          </a-form>
        </a-card>
      </div>
    </div>

    <!-- 添加断言按钮 -->
    <a-button type="dashed" long @click="addAssertion" style="margin-top: 8px;">
      <template #icon><icon-plus /></template>
      添加断言
    </a-button>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { AssertionItem } from '@/api/apiTestCase'

const props = defineProps<{
  modelValue: AssertionItem[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: AssertionItem[]): void
}>()

const assertions = ref<AssertionItem[]>([])

// 监听props变化，同步到本地（仅在父组件主动设置时）
watch(() => props.modelValue, (newValue) => {
  if (JSON.stringify(newValue) !== JSON.stringify(assertions.value)) {
    assertions.value = (newValue || []).map(a => ({ ...a }))
  }
}, { immediate: true })

function emitChange() {
  emit('update:modelValue', assertions.value.map((a, i) => ({ ...a, sort_order: i })))
}

const addAssertion = () => {
  assertions.value.push({
    assertion_type: 'status_code',
    operator: 'equals',
    field: '',
    expected: '200',
    description: '',
  })
  emitChange()
}

const removeAssertion = (index: number) => {
  assertions.value.splice(index, 1)
  emitChange()
}

const handleTypeChange = (assertion: AssertionItem) => {
  if (assertion.assertion_type === 'status_code') {
    assertion.expected = '200'
    assertion.operator = 'equals'
    assertion.field = ''
  } else if (assertion.assertion_type === 'response_time') {
    assertion.expected = '1000'
    assertion.operator = 'less_than'
    assertion.field = ''
  } else if (assertion.assertion_type === 'jsonpath') {
    assertion.field = '$.data'
    assertion.operator = 'exists'
    assertion.expected = ''
  } else if (assertion.assertion_type === 'header') {
    assertion.field = 'Content-Type'
    assertion.operator = 'contains'
    assertion.expected = 'application/json'
  } else if (assertion.assertion_type === 'body_contains') {
    assertion.field = ''
    assertion.operator = 'contains'
    assertion.expected = ''
  }
  emitChange()
}

const needsField = (type: string) => {
  return ['jsonpath', 'header'].includes(type)
}

const getFieldLabel = (type: string) => {
  const labels: Record<string, string> = {
    jsonpath: 'JSONPath表达式',
    header: '响应头名称',
  }
  return labels[type] || '字段'
}

const getFieldPlaceholder = (type: string) => {
  const placeholders: Record<string, string> = {
    jsonpath: '$.data.id',
    header: 'Content-Type',
  }
  return placeholders[type] || ''
}
</script>

<style scoped>
.assertion-editor {
  width: 100%;
}

.assertion-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.assertion-item {
  width: 100%;
}
</style>

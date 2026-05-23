<template>
  <div class="case-editor">
    <a-form :model="formData" layout="vertical">
      <!-- 基本信息 -->
      <a-row :gutter="16">
        <a-col :span="12">
          <a-form-item label="用例名称">
            <a-input v-model="formData.name" placeholder="输入用例名称" />
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="优先级">
            <a-select v-model="formData.priority">
              <a-option value="P0">P0 - 最高</a-option>
              <a-option value="P1">P1 - 高</a-option>
              <a-option value="P2">P2 - 中</a-option>
              <a-option value="P3">P3 - 低</a-option>
            </a-select>
          </a-form-item>
        </a-col>
      </a-row>

      <!-- 接口测试用例特有字段 -->
      <template v-if="isApiCase">
        <a-row :gutter="16">
          <a-col :span="6">
            <a-form-item label="请求方法">
              <a-select v-model="formData.method">
                <a-option value="GET">GET</a-option>
                <a-option value="POST">POST</a-option>
                <a-option value="PUT">PUT</a-option>
                <a-option value="DELETE">DELETE</a-option>
                <a-option value="PATCH">PATCH</a-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="18">
            <a-form-item label="请求 URL">
              <a-input v-model="formData.url" placeholder="输入请求 URL" />
            </a-form-item>
          </a-col>
        </a-row>

        <!-- Headers -->
        <a-form-item label="请求头">
          <div v-for="(header, index) in formData.headers" :key="index" class="key-value-row">
            <a-input v-model="header.key" placeholder="Key" style="width: 200px" />
            <a-input v-model="header.value" placeholder="Value" style="flex: 1" />
            <a-button type="text" status="danger" @click="removeHeader(index)">
              <template #icon><icon-delete /></template>
            </a-button>
          </div>
          <a-button type="dashed" @click="addHeader">
            <template #icon><icon-plus /></template>
            添加请求头
          </a-button>
        </a-form-item>

        <!-- 断言 -->
        <a-form-item label="断言">
          <div v-for="(assertion, index) in formData.assertions" :key="index" class="assertion-row">
            <a-select v-model="assertion.assertion_type" style="width: 150px">
              <a-option value="status_code">状态码</a-option>
              <a-option value="jsonpath">JSONPath</a-option>
              <a-option value="body_contains">响应体包含</a-option>
            </a-select>
            <a-select v-model="assertion.operator" style="width: 120px">
              <a-option value="equals">等于</a-option>
              <a-option value="not_equals">不等于</a-option>
              <a-option value="contains">包含</a-option>
            </a-select>
            <a-input v-model="assertion.expected" placeholder="期望值" style="flex: 1" />
            <a-button type="text" status="danger" @click="removeAssertion(index)">
              <template #icon><icon-delete /></template>
            </a-button>
          </div>
          <a-button type="dashed" @click="addAssertion">
            <template #icon><icon-plus /></template>
            添加断言
          </a-button>
        </a-form-item>
      </template>

      <!-- 描述 -->
      <a-form-item label="描述">
        <a-textarea v-model="formData.description" placeholder="输入用例描述" :rows="4" />
      </a-form-item>

      <!-- 前置条件 -->
      <a-form-item label="前置条件">
        <a-textarea v-model="formData.preconditions" placeholder="输入前置条件" :rows="3" />
      </a-form-item>
    </a-form>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  modelValue: any
}>()

const emit = defineEmits<{
  'update:modelValue': [value: any]
}>()

const formData = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const isApiCase = computed(() => {
  return formData.value.method !== undefined
})

// Headers 操作
const addHeader = () => {
  if (!formData.value.headers) {
    formData.value.headers = []
  }
  formData.value.headers.push({ key: '', value: '' })
}

const removeHeader = (index: number) => {
  formData.value.headers.splice(index, 1)
}

// 断言操作
const addAssertion = () => {
  if (!formData.value.assertions) {
    formData.value.assertions = []
  }
  formData.value.assertions.push({
    assertion_type: 'status_code',
    operator: 'equals',
    expected: ''
  })
}

const removeAssertion = (index: number) => {
  formData.value.assertions.splice(index, 1)
}
</script>

<style scoped>
.case-editor {
  max-height: 60vh;
  overflow-y: auto;
}

.key-value-row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  align-items: center;
}

.assertion-row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  align-items: center;
}
</style>

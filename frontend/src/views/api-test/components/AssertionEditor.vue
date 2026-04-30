<template>
  <div class="assertion-editor">
    <a-space direction="vertical" fill>
      <!-- 断言逻辑关系 -->
      <a-form-item label="断言逻辑">
        <a-radio-group v-model="logic">
          <a-radio value="and">全部满足（AND）</a-radio>
          <a-radio value="or">任一满足（OR）</a-radio>
        </a-radio-group>
      </a-form-item>

      <!-- 断言列表 -->
      <div v-for="(assertion, index) in assertions" :key="assertion.id" class="assertion-item">
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

          <a-form layout="vertical">
            <a-row :gutter="16">
              <a-col :span="8">
                <a-form-item label="断言类型">
                  <a-select
                    v-model="assertion.type"
                    placeholder="选择断言类型"
                    @change="handleTypeChange(assertion)"
                  >
                    <a-option value="status_code">状态码</a-option>
                    <a-option value="jsonpath">JSONPath</a-option>
                    <a-option value="xpath">XPath</a-option>
                    <a-option value="header">响应头</a-option>
                    <a-option value="response_time">响应时间</a-option>
                    <a-option value="schema">Schema校验</a-option>
                  </a-select>
                </a-form-item>
              </a-col>

              <a-col :span="8">
                <a-form-item label="比较方式">
                  <a-select v-model="assertion.operator" placeholder="选择比较方式">
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
                  v-if="needsField(assertion.type)"
                  :label="getFieldLabel(assertion.type)"
                >
                  <a-input
                    v-model="assertion.field"
                    :placeholder="getFieldPlaceholder(assertion.type)"
                  />
                </a-form-item>
              </a-col>
            </a-row>

            <a-row :gutter="16">
              <a-col :span="16">
                <a-form-item label="期望值">
                  <a-input
                    v-if="assertion.type !== 'schema'"
                    v-model="assertion.expected"
                    placeholder="输入期望值"
                  />
                  <a-textarea
                    v-else
                    v-model="assertion.expected"
                    placeholder="输入JSON Schema"
                    :auto-size="{ minRows: 3, maxRows: 6 }"
                  />
                </a-form-item>
              </a-col>

              <a-col :span="8">
                <a-form-item label="描述">
                  <a-input
                    v-model="assertion.description"
                    placeholder="断言描述（可选）"
                  />
                </a-form-item>
              </a-col>
            </a-row>
          </a-form>
        </a-card>
      </div>

      <!-- 添加断言按钮 -->
      <a-button type="dashed" long @click="addAssertion">
        <template #icon><icon-plus /></template>
        添加断言
      </a-button>
    </a-space>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Assertion } from '@/api/apiTestCase'

interface Props {
  modelValue: Assertion[]
  assertionLogic?: 'and' | 'or'
}

const props = withDefaults(defineProps<Props>(), {
  assertionLogic: 'and'
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: Assertion[]): void
  (e: 'update:assertionLogic', value: 'and' | 'or'): void
}>()

const assertions = ref<Assertion[]>([...props.modelValue])
const logic = ref<'and' | 'or'>(props.assertionLogic)

watch(() => props.modelValue, (newValue) => {
  assertions.value = [...newValue]
}, { deep: true })

watch(() => props.assertionLogic, (newValue) => {
  logic.value = newValue
})

watch(assertions, (newValue) => {
  emit('update:modelValue', newValue)
}, { deep: true })

watch(logic, (newValue) => {
  emit('update:assertionLogic', newValue)
})

const generateId = () => {
  return `assertion-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

const addAssertion = () => {
  assertions.value.push({
    id: generateId(),
    type: 'status_code',
    operator: 'equals',
    expected: 200
  })
}

const removeAssertion = (index: number) => {
  assertions.value.splice(index, 1)
}

const handleTypeChange = (assertion: Assertion) => {
  // 根据类型设置默认值
  if (assertion.type === 'status_code') {
    assertion.expected = 200
    assertion.operator = 'equals'
    delete assertion.field
  } else if (assertion.type === 'response_time') {
    assertion.expected = 1000
    assertion.operator = 'less_than'
    delete assertion.field
  } else if (assertion.type === 'jsonpath') {
    assertion.field = '$.data'
    assertion.operator = 'exists'
  } else if (assertion.type === 'xpath') {
    assertion.field = '//root/data'
    assertion.operator = 'exists'
  } else if (assertion.type === 'header') {
    assertion.field = 'Content-Type'
    assertion.operator = 'contains'
  } else if (assertion.type === 'schema') {
    assertion.expected = '{}'
    assertion.operator = 'equals'
    delete assertion.field
  }
}

const needsField = (type: string) => {
  return ['jsonpath', 'xpath', 'header'].includes(type)
}

const getFieldLabel = (type: string) => {
  const labels: Record<string, string> = {
    jsonpath: 'JSONPath表达式',
    xpath: 'XPath表达式',
    header: '响应头名称'
  }
  return labels[type] || '字段'
}

const getFieldPlaceholder = (type: string) => {
  const placeholders: Record<string, string> = {
    jsonpath: '例如: $.data.id',
    xpath: '例如: //root/data',
    header: '例如: Content-Type'
  }
  return placeholders[type] || ''
}
</script>

<style scoped>
.assertion-editor {
  width: 100%;
}

.assertion-item {
  margin-bottom: 12px;
}
</style>

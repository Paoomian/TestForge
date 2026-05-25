<template>
  <div class="case-editor">
    <a-form :model="formData" layout="vertical">
      <!-- 基本信息 -->
      <div class="section-card">
        <div class="section-title">基本信息</div>
        <a-row :gutter="16">
          <a-col :span="16">
            <a-form-item label="用例名称">
              <a-input v-model="formData.name" placeholder="输入用例名称" allow-clear />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="优先级">
              <a-select v-model="formData.priority" placeholder="选择优先级">
                <a-option value="P0">
                  <a-tag color="red" size="small">P0</a-tag> 最高
                </a-option>
                <a-option value="P1">
                  <a-tag color="orange" size="small">P1</a-tag> 高
                </a-option>
                <a-option value="P2">
                  <a-tag color="blue" size="small">P2</a-tag> 中
                </a-option>
                <a-option value="P3">
                  <a-tag color="green" size="small">P3</a-tag> 低
                </a-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
      </div>

      <!-- 接口测试用例特有字段 -->
      <template v-if="isApiCase">
        <div class="section-card">
          <div class="section-title">请求配置</div>
          <a-row :gutter="16">
            <a-col :span="6">
              <a-form-item label="请求方法">
                <a-select v-model="formData.method" placeholder="选择方法">
                  <a-option value="GET">
                    <a-tag color="blue" size="small">GET</a-tag>
                  </a-option>
                  <a-option value="POST">
                    <a-tag color="green" size="small">POST</a-tag>
                  </a-option>
                  <a-option value="PUT">
                    <a-tag color="orange" size="small">PUT</a-tag>
                  </a-option>
                  <a-option value="DELETE">
                    <a-tag color="red" size="small">DELETE</a-tag>
                  </a-option>
                  <a-option value="PATCH">
                    <a-tag color="purple" size="small">PATCH</a-tag>
                  </a-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :span="18">
              <a-form-item label="请求 URL">
                <a-input v-model="formData.url" placeholder="输入请求 URL" allow-clear />
              </a-form-item>
            </a-col>
          </a-row>

          <!-- Headers -->
          <a-form-item>
            <template #label>
              <div class="label-with-btn">
                <span>请求头</span>
                <a-button type="text" size="mini" @click="addHeader">
                  <template #icon><icon-plus /></template>
                </a-button>
              </div>
            </template>
            <div class="kv-list">
              <div v-for="(header, index) in formData.headers" :key="index" class="kv-item">
                <a-input v-model="header.key" placeholder="Key" class="kv-key" />
                <a-input v-model="header.value" placeholder="Value" class="kv-value" />
                <a-button type="text" status="danger" size="small" @click="removeHeader(index)">
                  <template #icon><icon-delete /></template>
                </a-button>
              </div>
            </div>
          </a-form-item>

          <!-- 断言 -->
          <a-form-item>
            <template #label>
              <div class="label-with-btn">
                <span>断言规则</span>
                <a-button type="text" size="mini" @click="addAssertion">
                  <template #icon><icon-plus /></template>
                </a-button>
              </div>
            </template>
            <div class="assertion-list">
              <div v-for="(assertion, index) in formData.assertions" :key="index" class="assertion-item">
                <a-select v-model="assertion.assertion_type" class="assertion-type" placeholder="断言类型">
                  <a-option value="status_code">状态码</a-option>
                  <a-option value="jsonpath">JSONPath</a-option>
                  <a-option value="body_contains">响应体包含</a-option>
                </a-select>
                <a-select v-model="assertion.operator" class="assertion-operator" placeholder="运算符">
                  <a-option value="equals">等于</a-option>
                  <a-option value="not_equals">不等于</a-option>
                  <a-option value="contains">包含</a-option>
                </a-select>
                <a-input v-model="assertion.expected" placeholder="期望值" class="assertion-expected" />
                <a-button type="text" status="danger" size="small" @click="removeAssertion(index)">
                  <template #icon><icon-delete /></template>
                </a-button>
              </div>
            </div>
          </a-form-item>
        </div>
      </template>

      <!-- 功能测试用例特有字段 -->
      <template v-if="!isApiCase">
        <div class="section-card">
          <div class="section-header">
            <div class="section-title">操作步骤</div>
            <a-button type="outline" size="mini" @click="addStep">
              <template #icon><icon-plus /></template>
              添加
            </a-button>
          </div>
          <div class="step-list">
            <div v-for="(step, index) in formData.steps" :key="index" class="step-item">
              <div class="step-badge">{{ index + 1 }}</div>
              <a-textarea
                v-model="formData.steps[index]"
                placeholder="描述操作步骤..."
                :auto-size="{ minRows: 1, maxRows: 4 }"
                class="step-content"
              />
              <a-button type="text" status="danger" size="small" @click="removeStep(index)">
                <template #icon><icon-delete /></template>
              </a-button>
            </div>
          </div>
        </div>

        <div class="section-card">
          <div class="section-header">
            <div class="section-title">预期结果</div>
            <a-button type="outline" size="mini" @click="addExpectedResult">
              <template #icon><icon-plus /></template>
              添加
            </a-button>
          </div>
          <div class="step-list">
            <div v-for="(result, index) in formData.expected_results" :key="index" class="step-item expected-item">
              <div class="step-badge expected-badge">{{ index + 1 }}</div>
              <a-textarea
                v-model="formData.expected_results[index]"
                placeholder="描述预期结果..."
                :auto-size="{ minRows: 1, maxRows: 4 }"
                class="step-content"
              />
              <a-button type="text" status="danger" size="small" @click="removeExpectedResult(index)">
                <template #icon><icon-delete /></template>
              </a-button>
            </div>
          </div>
        </div>
      </template>

      <!-- 补充信息 -->
      <div class="section-card">
        <div class="section-title">补充信息</div>
        <a-form-item label="前置条件" :style="{ marginBottom: 0 }">
          <a-textarea v-model="formData.preconditions" placeholder="输入执行用例前的前置条件..." :rows="3" />
        </a-form-item>
      </div>
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

// 操作步骤操作
const addStep = () => {
  if (!formData.value.steps) {
    formData.value.steps = []
  }
  formData.value.steps.push('')
}

const removeStep = (index: number) => {
  formData.value.steps.splice(index, 1)
}

// 预期结果操作
const addExpectedResult = () => {
  if (!formData.value.expected_results) {
    formData.value.expected_results = []
  }
  formData.value.expected_results.push('')
}

const removeExpectedResult = (index: number) => {
  formData.value.expected_results.splice(index, 1)
}

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
  max-height: 65vh;
  overflow-y: auto;
  padding: 4px;
}

/* 分区卡片 */
.section-card {
  background: var(--color-bg-2);
  border-radius: var(--radius-md);
  padding: var(--space-lg);
  margin-bottom: var(--space-lg);
  border-left: 3px solid var(--primary-500);
  transition: all 0.2s ease;
}

.section-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-md);
  padding-bottom: var(--space-sm);
  border-bottom: 1px solid var(--color-border-2);
}

.section-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-2);
}

/* 标签右侧按钮 */
.label-with-btn {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.label-with-btn :deep(.arco-btn) {
  margin-left: auto;
}

/* 键值对列表 */
.kv-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.kv-item {
  display: flex;
  gap: var(--space-sm);
  align-items: center;
  transition: all 0.2s ease;
}

.kv-item:hover {
  background: var(--color-fill-1);
  border-radius: var(--radius-sm);
  padding: var(--space-xs);
  margin: calc(var(--space-xs) * -1);
}

.kv-key {
  width: 180px;
}

.kv-value {
  flex: 1;
}

/* 断言列表 */
.assertion-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.assertion-item {
  display: flex;
  gap: var(--space-sm);
  align-items: center;
  background: var(--color-fill-1);
  padding: var(--space-sm);
  border-radius: var(--radius-sm);
  transition: all 0.2s ease;
}

.assertion-item:hover {
  background: var(--color-fill-2);
}

.assertion-type {
  width: 140px;
}

.assertion-operator {
  width: 120px;
}

.assertion-expected {
  flex: 1;
}

/* 步骤列表 */
.step-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.step-item {
  display: flex;
  gap: var(--space-sm);
  align-items: flex-start;
  padding: var(--space-sm);
  background: var(--color-fill-1);
  border-radius: var(--radius-sm);
  transition: all 0.2s ease;
}

.step-item:hover {
  background: var(--color-fill-2);
}

.expected-item {
  border-left: 2px solid var(--color-success-light-4);
}

.step-badge {
  min-width: 24px;
  height: 24px;
  line-height: 24px;
  text-align: center;
  background: var(--primary-500);
  color: white;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 500;
  margin-top: 4px;
}

.expected-badge {
  background: var(--color-success);
}

.step-content {
  flex: 1;
}

/* 移除默认的 margin-bottom */
:deep(.arco-form-item) {
  margin-bottom: 0;
}

:deep(.arco-form-item:last-child) {
  margin-bottom: 0;
}

/* 优化 textarea 样式 */
:deep(.arco-textarea) {
  border-radius: var(--radius-sm);
  transition: all 0.2s ease;
}

:deep(.arco-textarea:focus) {
  box-shadow: 0 0 0 2px var(--primary-300);
}

/* 优化按钮样式 */
:deep(.arco-btn-dashed) {
  border-color: var(--color-border-3);
  color: var(--color-text-3);
  transition: all 0.2s ease;
}

:deep(.arco-btn-dashed:hover) {
  border-color: var(--primary-500);
  color: var(--primary-500);
}
</style>

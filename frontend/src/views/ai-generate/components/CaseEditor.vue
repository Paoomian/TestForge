<template>
  <div class="case-editor">
    <a-form :model="formData" layout="vertical">
      <!-- 基本信息 -->
      <div class="section-card">
        <div class="section-title">基本信息</div>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="用例名称">
              <a-input v-model="formData.name" placeholder="输入用例名称" allow-clear />
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="所属模块">
              <a-input v-model="formData.module" placeholder="输入模块名称" allow-clear />
            </a-form-item>
          </a-col>
          <a-col :span="6">
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
        <a-form-item label="用例描述" style="margin-top: 8px;">
          <a-textarea v-model="formData.description" placeholder="输入用例描述..." :auto-size="{ minRows: 2, maxRows: 4 }" />
        </a-form-item>
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
              <div v-for="(header, index) in headersList" :key="index" class="kv-item">
                <a-input v-model="header.key" placeholder="Key" class="kv-key" />
                <a-input v-model="header.value" placeholder="Value" class="kv-value" />
                <a-button type="text" status="danger" size="small" @click="removeHeader(index)">
                  <template #icon><icon-delete /></template>
                </a-button>
              </div>
              <div v-if="!headersList.length" class="kv-empty">暂无请求头</div>
            </div>
          </a-form-item>

          <!-- Query Params -->
          <a-form-item>
            <template #label>
              <div class="label-with-btn">
                <span>查询参数</span>
                <a-button type="text" size="mini" @click="addQueryParam">
                  <template #icon><icon-plus /></template>
                </a-button>
              </div>
            </template>
            <div class="kv-list">
              <div v-for="(param, index) in queryParamsList" :key="index" class="kv-item">
                <a-input v-model="param.key" placeholder="Key" class="kv-key" />
                <a-input v-model="param.value" placeholder="Value" class="kv-value" />
                <a-button type="text" status="danger" size="small" @click="removeQueryParam(index)">
                  <template #icon><icon-delete /></template>
                </a-button>
              </div>
              <div v-if="!queryParamsList.length" class="kv-empty">暂无查询参数</div>
            </div>
          </a-form-item>

          <!-- Body -->
          <a-form-item label="请求体类型">
            <a-select v-model="formData.body_type" size="small" style="width: 180px;">
              <a-option value="none">none</a-option>
              <a-option value="form-data">form-data</a-option>
              <a-option value="x-www-form-urlencoded">x-www-form-urlencoded</a-option>
              <a-option value="raw-json">JSON</a-option>
              <a-option value="raw-xml">XML</a-option>
              <a-option value="raw-text">Text</a-option>
            </a-select>
          </a-form-item>
          <a-form-item label="请求体内容" v-if="formData.body_type && formData.body_type !== 'none'">
            <a-textarea
              v-model="formData.body_content"
              :placeholder="getBodyPlaceholder()"
              :auto-size="{ minRows: 4, maxRows: 10 }"
            />
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
              <div v-for="(assertion, index) in assertionsList" :key="index" class="assertion-item">
                <div class="assertion-row">
                  <a-select v-model="assertion.assertion_type" size="small" placeholder="断言类型">
                    <a-option value="status_code">状态码</a-option>
                    <a-option value="jsonpath">JSONPath</a-option>
                    <a-option value="header">响应头</a-option>
                    <a-option value="response_time">响应时间</a-option>
                    <a-option value="body_contains">响应体</a-option>
                  </a-select>
                  <a-select v-model="assertion.operator" size="small" placeholder="运算符">
                    <a-option value="equals">等于</a-option>
                    <a-option value="not_equals">不等于</a-option>
                    <a-option value="contains">包含</a-option>
                    <a-option value="not_contains">不包含</a-option>
                    <a-option value="greater_than">大于</a-option>
                    <a-option value="less_than">小于</a-option>
                    <a-option value="regex">正则</a-option>
                    <a-option value="exists">存在</a-option>
                    <a-option value="not_exists">不存在</a-option>
                  </a-select>
                  <a-button type="text" status="danger" size="small" @click="removeAssertion(index)" style="margin-left: auto;">
                    <template #icon><icon-delete /></template>
                  </a-button>
                </div>
                <a-input
                  v-if="assertion.assertion_type === 'jsonpath' || assertion.assertion_type === 'header'"
                  v-model="assertion.field"
                  size="small"
                  :placeholder="assertion.assertion_type === 'jsonpath' ? 'JSONPath: $.data.token' : 'Header: Content-Type'"
                />
                <a-input
                  v-if="assertion.operator !== 'exists' && assertion.operator !== 'not_exists'"
                  v-model="assertion.expected"
                  size="small"
                  placeholder="期望值"
                />
                <a-input v-model="assertion.description" size="small" placeholder="断言描述（可选）" />
              </div>
            </div>
          </a-form-item>

          <!-- 数据提取 -->
          <a-form-item>
            <template #label>
              <div class="label-with-btn">
                <span>数据提取</span>
                <a-button type="text" size="mini" @click="addDataExtract">
                  <template #icon><icon-plus /></template>
                </a-button>
              </div>
            </template>
            <div class="extract-list">
              <div v-for="(extract, index) in dataExtractList" :key="index" class="extract-item">
                <!-- 第一行：变量名 + 来源 + 删除 -->
                <div class="extract-row">
                  <a-input v-model="extract.name" size="small" placeholder="变量名" style="flex: 1;" />
                  <a-select v-model="extract.source" size="small" style="flex: 1;">
                    <a-option value="jsonpath">JSONPath</a-option>
                    <a-option value="regex">正则</a-option>
                    <a-option value="header">响应头</a-option>
                  </a-select>
                  <a-button type="text" status="danger" size="small" @click="removeDataExtract(index)" style="margin-left: auto;">
                    <template #icon><icon-delete /></template>
                  </a-button>
                </div>
                <!-- 第二行：提取表达式 -->
                <a-input v-model="extract.expression" size="small" placeholder="提取表达式：$.data.token 或正则表达式" />
                <!-- 第三行：描述 -->
                <a-input v-model="extract.description" size="small" placeholder="描述（可选）" />
              </div>
              <div v-if="!dataExtractList.length" class="kv-empty">暂无数据提取规则</div>
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
import { ref, computed, onUnmounted } from 'vue'

const props = defineProps<{
  modelValue: any
}>()

const emit = defineEmits<{
  'update:modelValue': [value: any]
}>()

// 将对象格式转为数组格式（用于 headers/query_params）
function toArray(data: any): { key: string; value: string }[] {
  if (Array.isArray(data)) return data
  if (data && typeof data === 'object') {
    return Object.entries(data).map(([key, value]) => ({ key, value: String(value) }))
  }
  return []
}

// 转换断言格式（type → assertion_type）
function normalizeAssertions(assertions: any[]): any[] {
  if (!Array.isArray(assertions)) return []
  return assertions.map(a => {
    if (!a.assertion_type && a.type) {
      a.assertion_type = a.type
    }
    if (!a.field) a.field = ''
    if (!a.description) a.description = ''
    return a
  })
}

// 使用本地 ref 深拷贝数据
const formData = ref(JSON.parse(JSON.stringify(props.modelValue)))

// 组件销毁前 emit 最终数据
onUnmounted(() => {
  emit('update:modelValue', JSON.parse(JSON.stringify(formData.value)))
})

// 暴露 getData 方法供父组件获取最新数据
defineExpose({
  getData: () => JSON.parse(JSON.stringify(formData.value))
})

const isApiCase = computed(() => {
  return formData.value?.method !== undefined
})

// 计算属性：确保 headers 是数组格式
const headersList = computed({
  get: () => toArray(formData.value.headers),
  set: (value) => { formData.value.headers = value }
})

// 计算属性：确保 query_params 是数组格式
const queryParamsList = computed({
  get: () => toArray(formData.value.query_params),
  set: (value) => { formData.value.query_params = value }
})

// 计算属性：确保 assertions 格式正确
const assertionsList = computed({
  get: () => normalizeAssertions(formData.value.assertions),
  set: (value) => { formData.value.assertions = value }
})

// 计算属性：数据提取规则
const dataExtractList = computed({
  get: () => formData.value.data_extract || [],
  set: (value) => { formData.value.data_extract = value }
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
  headersList.value = [...headersList.value, { key: '', value: '' }]
}

const removeHeader = (index: number) => {
  headersList.value = headersList.value.filter((_: any, i: number) => i !== index)
}

// Query Params 操作
const addQueryParam = () => {
  queryParamsList.value = [...queryParamsList.value, { key: '', value: '' }]
}

const removeQueryParam = (index: number) => {
  queryParamsList.value = queryParamsList.value.filter((_: any, i: number) => i !== index)
}

// Body 占位符
const getBodyPlaceholder = () => {
  const bodyType = formData.value.body_type
  if (bodyType === 'raw-json') return '{"key": "value"}'
  if (bodyType === 'raw-xml') return '<root><key>value</key></root>'
  if (bodyType === 'form-data' || bodyType === 'x-www-form-urlencoded') return 'key=value&key2=value2'
  return '输入请求体内容'
}

// 断言操作
const addAssertion = () => {
  assertionsList.value = [...assertionsList.value, {
    assertion_type: 'status_code',
    operator: 'equals',
    expected: ''
  }]
}

const removeAssertion = (index: number) => {
  assertionsList.value = assertionsList.value.filter((_: any, i: number) => i !== index)
}

// 数据提取操作
const addDataExtract = () => {
  dataExtractList.value = [...dataExtractList.value, {
    name: '',
    source: 'jsonpath',
    expression: '',
    description: ''
  }]
}

const removeDataExtract = (index: number) => {
  dataExtractList.value = dataExtractList.value.filter((_: any, i: number) => i !== index)
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

.kv-empty {
  color: var(--color-text-3);
  font-size: 12px;
  padding: 8px 0;
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
  gap: 8px;
  width: 100%;
}

.assertion-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  background: var(--color-fill-1);
  padding: 8px;
  border-radius: var(--radius-sm);
  transition: all 0.2s ease;
}

.assertion-item:hover {
  background: var(--color-fill-2);
}

.assertion-row {
  display: flex;
  gap: 6px;
  align-items: center;
}

.assertion-row :deep(.arco-select) {
  flex: 1;
}

/* 数据提取列表 */
.extract-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.extract-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  background: var(--color-fill-1);
  padding: 8px;
  border-radius: var(--radius-sm);
  transition: all 0.2s ease;
  width: 100%;
  box-sizing: border-box;
}

.extract-item:hover {
  background: var(--color-fill-2);
}

.extract-row {
  display: flex;
  gap: 6px;
  align-items: center;
  width: 100%;
}

.extract-item :deep(.arco-input-wrapper) {
  width: 100%;
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

/* 确保断言输入框内容可见 */
.assertion-item :deep(.arco-input-wrapper) {
  overflow: visible;
}

.assertion-item :deep(.arco-input) {
  text-overflow: ellipsis;
}
</style>

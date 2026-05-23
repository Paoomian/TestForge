<template>
  <a-modal
    v-model:visible="visible"
    title="导入Excel用例"
    :width="1360"
    :mask-closable="false"
    :body-style="{ padding: '16px' }"
    @cancel="handleClose"
  >
    <!-- Step 1: 上传区 -->
    <div v-if="step === 1" class="upload-section">
      <a-tabs v-model:active-key="step1Tab" type="rounded" size="small">
        <!-- Tab 1: 上传文件 -->
        <a-tab-pane key="upload" title="上传文件">
          <div class="template-download">
            <a-button type="text" size="small" @click="downloadTemplate">
              <template #icon><icon-download /></template>
              下载模板
            </a-button>
            <span class="template-hint">建议先下载模板，按格式填写用例数据</span>
          </div>

          <a-upload
            :auto-upload="false"
            :show-file-list="false"
            accept=".xlsx,.xls"
            @change="handleFileChange"
          >
            <template #upload-button>
              <div class="upload-area">
                <div class="upload-icon">
                  <icon-upload />
                </div>
                <div class="upload-text">点击或拖拽 Excel 文件到此处</div>
                <div class="upload-hint">支持 .xlsx / .xls 格式</div>
              </div>
            </template>
          </a-upload>

          <div v-if="file" class="file-info">
            <icon-file class="file-icon" />
            <span class="file-name">{{ file.name }}</span>
            <span class="file-size">{{ formatFileSize(file.size) }}</span>
            <a-button type="text" size="mini" status="danger" @click="clearFile">
              <template #icon><icon-delete /></template>
            </a-button>
          </div>

          <div v-if="parseError" class="parse-error">
            <icon-exclamation-circle />
            <span>{{ parseError }}</span>
          </div>
        </a-tab-pane>

        <!-- Tab 2: 填写规范 -->
        <a-tab-pane key="guide" title="填写规范">
          <div class="guide-content">
            <!-- 字段说明 -->
            <a-card title="字段说明" :bordered="true" size="small" class="guide-card">
              <a-table :data="fieldGuide" :pagination="false" :bordered="false">
                <template #columns>
                  <a-table-column title="字段" data-index="field" :width="120">
                    <template #cell="{ record }">
                      <span :class="{ required: record.required }">{{ record.field }}</span>
                    </template>
                  </a-table-column>
                  <a-table-column title="必填" data-index="required" :width="60" align="center">
                    <template #cell="{ record }">
                      <a-tag :color="record.required ? 'red' : 'gray'" size="small">
                        {{ record.required ? '是' : '否' }}
                      </a-tag>
                    </template>
                  </a-table-column>
                  <a-table-column title="说明" data-index="desc" :width="200" />
                  <a-table-column title="示例" data-index="example">
                    <template #cell="{ record }">
                      <code class="example-code">{{ record.example }}</code>
                    </template>
                  </a-table-column>
                </template>
              </a-table>
            </a-card>

            <!-- 断言规则 -->
            <a-card title="断言规则" :bordered="true" size="small" class="guide-card">
              <div class="assertion-guide">
                <div class="assertion-section">
                  <h4>断言类型 (type)</h4>
                  <a-table :data="assertionTypes" :pagination="false" :bordered="false" size="small">
                    <template #columns>
                      <a-table-column title="类型" data-index="type" :width="140">
                        <template #cell="{ record }">
                          <code>{{ record.type }}</code>
                        </template>
                      </a-table-column>
                      <a-table-column title="说明" data-index="desc" :width="150" />
                      <a-table-column title="需要field" data-index="needField" :width="90" align="center">
                        <template #cell="{ record }">
                          <a-tag :color="record.needField ? 'blue' : 'gray'" size="small">
                            {{ record.needField ? '是' : '否' }}
                          </a-tag>
                        </template>
                      </a-table-column>
                      <a-table-column title="expected示例" data-index="expectedExample" />
                    </template>
                  </a-table>
                </div>

                <div class="assertion-section">
                  <h4>比较方式 (operator)</h4>
                  <div class="operator-tags">
                    <a-tag v-for="op in assertionOperators" :key="op.value" color="arcoblue" size="small">
                      {{ op.value }} - {{ op.label }}
                    </a-tag>
                  </div>
                </div>

                <div class="assertion-section">
                  <h4>断言示例</h4>
                  <div class="assertion-examples">
                    <div v-for="example in assertionExamples" :key="example.title" class="assertion-example">
                      <div class="example-title">{{ example.title }}</div>
                      <code class="example-json">{{ example.json }}</code>
                    </div>
                  </div>
                </div>
              </div>
            </a-card>

            <!-- 请求方法与Body类型 -->
            <a-card title="请求方法与Body类型" :bordered="true" size="small" class="guide-card">
              <a-row :gutter="16">
                <a-col :span="12">
                  <h4>请求方法</h4>
                  <div class="method-tags">
                    <a-tag v-for="m in methods" :key="m" :color="getMethodColor(m)" size="small">{{ m }}</a-tag>
                  </div>
                </a-col>
                <a-col :span="12">
                  <h4>Body类型</h4>
                  <div class="body-type-list">
                    <div v-for="bt in bodyTypeOptions" :key="bt.value" class="body-type-item">
                      <code>{{ bt.value }}</code>
                      <span>{{ bt.desc }}</span>
                    </div>
                  </div>
                </a-col>
              </a-row>
            </a-card>

            <!-- 查询参数示例 -->
            <a-card title="查询参数示例" :bordered="true" size="small" class="guide-card">
              <div class="param-examples">
                <div class="param-example">
                  <div class="example-title">JSON对象格式</div>
                  <code class="example-json">{"page": "1", "size": "10", "keyword": "test"}</code>
                </div>
                <div class="param-example">
                  <div class="example-title">实际效果</div>
                  <span class="example-url">/api/v1/users?page=1&size=10&keyword=test</span>
                </div>
              </div>
            </a-card>

            <!-- 数据提取规则 -->
            <a-card title="数据提取规则" :bordered="true" size="small" class="guide-card">
              <div class="extract-guide">
                <div class="extract-section">
                  <h4>提取来源 (source)</h4>
                  <a-table :data="extractSources" :pagination="false" :bordered="false" size="small">
                    <template #columns>
                      <a-table-column title="来源" data-index="source" :width="100">
                        <template #cell="{ record }">
                          <code>{{ record.source }}</code>
                        </template>
                      </a-table-column>
                      <a-table-column title="说明" data-index="desc" :width="120" />
                      <a-table-column title="expression示例" data-index="expressionExample" :width="180">
                        <template #cell="{ record }">
                          <code class="example-code">{{ record.expressionExample }}</code>
                        </template>
                      </a-table-column>
                      <a-table-column title="用途" data-index="descExample" />
                    </template>
                  </a-table>
                </div>

                <div class="extract-section">
                  <h4>数据提取示例</h4>
                  <div class="extract-examples">
                    <div v-for="example in extractExamples" :key="example.title" class="extract-example">
                      <div class="example-title">{{ example.title }}</div>
                      <code class="example-json">{{ example.json }}</code>
                    </div>
                  </div>
                </div>
              </div>
            </a-card>
          </div>
        </a-tab-pane>
      </a-tabs>
    </div>

    <!-- Step 2: 预览编辑区 -->
    <div v-else-if="step === 2" class="preview-section">
      <div class="preview-toolbar">
        <div class="preview-info">
          <span class="info-label">共</span>
          <span class="info-count">{{ parsedCases.length }}</span>
          <span class="info-label">条用例</span>
          <template v-if="errorCount > 0">
            <span class="info-separator">·</span>
            <span class="info-error">
              <icon-exclamation-circle />
              {{ errorCount }} 条有误
            </span>
          </template>
        </div>
        <div class="preview-actions">
          <a-button size="small" status="danger" :disabled="selectedRows.length === 0" @click="deleteSelected">
            删除选中 ({{ selectedRows.length }})
          </a-button>
          <a-button size="small" @click="clearAll">清空</a-button>
          <a-button size="small" @click="reupload">重新上传</a-button>
        </div>
      </div>

      <div class="table-container">
        <a-table
          :data="parsedCases"
          :pagination="pagination"
          row-key="_id"
          :row-selection="{ type: 'checkbox' }"
          v-model:selectedKeys="selectedRows"
          :row-class="getRowClass"
          :bordered="false"
          :stripe="false"
        >
          <template #columns>
            <a-table-column title="" :width="40" align="center">
              <template #cell="{ record }">
                <span
                  class="expand-btn"
                  :class="{ expanded: isRowExpanded(record) }"
                  @click="toggleExpand(record)"
                >
                  <icon-right />
                </span>
              </template>
            </a-table-column>

            <a-table-column title="#" :width="46" align="center">
              <template #cell="{ rowIndex }">
                <span class="row-index">{{ rowIndex + 1 }}</span>
              </template>
            </a-table-column>

            <a-table-column title="用例名称" :width="180">
              <template #cell="{ record }">
                <a-input
                  v-model="record.name"
                  size="small"
                  placeholder="请输入"
                  :class="{ 'input-error': hasFieldError(record, 'name') }"
                />
              </template>
            </a-table-column>

            <a-table-column title="方法" :width="90" align="center">
              <template #cell="{ record }">
                <a-dropdown trigger="click" @select="(val: any) => record.method = val">
                  <a-tag
                    :color="getMethodColor(record.method)"
                    size="small"
                    class="clickable-tag"
                    :class="{ 'tag-error': hasFieldError(record, 'method') }"
                  >
                    {{ record.method }}
                  </a-tag>
                  <template #content>
                    <a-doption v-for="m in methods" :key="m" :value="m">
                      <a-tag :color="getMethodColor(m)" size="small">{{ m }}</a-tag>
                    </a-doption>
                  </template>
                </a-dropdown>
              </template>
            </a-table-column>

            <a-table-column title="请求URL">
              <template #cell="{ record }">
                <a-input
                  v-model="record.url"
                  size="small"
                  placeholder="请输入"
                  :class="{ 'input-error': hasFieldError(record, 'url') }"
                />
              </template>
            </a-table-column>

            <a-table-column title="模块" :width="140">
              <template #cell="{ record }">
                <a-input v-model="record.module" size="small" placeholder="可选" />
              </template>
            </a-table-column>

            <a-table-column title="优先级" :width="90" align="center">
              <template #cell="{ record }">
                <a-dropdown trigger="click" @select="(val: any) => record.priority = val">
                  <a-tag
                    :color="getPriorityColor(record.priority)"
                    size="small"
                    class="clickable-tag"
                  >
                    {{ record.priority }}
                  </a-tag>
                  <template #content>
                    <a-doption v-for="p in priorities" :key="p" :value="p">
                      <a-tag :color="getPriorityColor(p)" size="small">{{ p }}</a-tag>
                    </a-doption>
                  </template>
                </a-dropdown>
              </template>
            </a-table-column>

            <a-table-column title="状态" :width="70" align="center">
              <template #cell="{ record }">
                <a-tooltip v-if="record._errors.length > 0" :content="record._errors.join('\n')">
                  <a-tag color="red" size="small">
                    <icon-exclamation-circle />
                    {{ record._errors.length }}
                  </a-tag>
                </a-tooltip>
                <a-tag v-else color="green" size="small">
                  <icon-check />
                </a-tag>
              </template>
            </a-table-column>
          </template>
        </a-table>

        <!-- 展开详情面板（表格下方） -->
        <transition name="slide-fade">
          <div v-if="expandedRecord" class="expand-panel">
            <div class="expand-panel-header">
              <span class="expand-panel-title">
                <icon-expand /> 用例详情 #{{ getRecordIndex(expandedRecord) + 1 }}
              </span>
              <a-button type="text" size="mini" @click="expandedRecord = null">
                <template #icon><icon-close /></template>
                收起
              </a-button>
            </div>
            <div class="expand-panel-body">
              <!-- 请求头 -->
              <div class="expand-section">
                <div class="section-title">请求头</div>
                <KeyValueEditor
                  :model-value="headersKV"
                  @update:model-value="updateHeadersFromKV"
                  key-placeholder="Header Name"
                  value-placeholder="Header Value"
                  add-text="添加请求头"
                />
              </div>

              <!-- Query参数 -->
              <div class="expand-section">
                <div class="section-title">Query参数</div>
                <KeyValueEditor
                  :model-value="paramsKV"
                  @update:model-value="updateParamsFromKV"
                  key-placeholder="Parameter Name"
                  value-placeholder="Parameter Value"
                  add-text="添加参数"
                />
              </div>

              <!-- Body -->
              <div class="expand-section">
                <div class="section-title">
                  <span>Body</span>
                  <a-radio-group
                    v-model="expandedRecord.body_type"
                    size="mini"
                    type="button"
                  >
                    <a-radio value="none">none</a-radio>
                    <a-radio value="form-data">form-data</a-radio>
                    <a-radio value="x-www-form-urlencoded">urlencoded</a-radio>
                    <a-radio value="raw-json">JSON</a-radio>
                    <a-radio value="raw-xml">XML</a-radio>
                    <a-radio value="raw-text">Text</a-radio>
                  </a-radio-group>
                </div>

                <!-- form-data / urlencoded -->
                <KeyValueEditor
                  v-if="expandedRecord.body_type === 'form-data' || expandedRecord.body_type === 'x-www-form-urlencoded'"
                  :model-value="bodyFormKV"
                  @update:model-value="updateBodyFormFromKV"
                  key-placeholder="Parameter Name"
                  value-placeholder="Parameter Value"
                  add-text="添加参数"
                />

                <!-- raw-json -->
                <div v-else-if="expandedRecord.body_type === 'raw-json'" class="raw-body">
                  <a-textarea
                    v-model="expandedRecord.body_raw_content"
                    placeholder='{"key": "value"}'
                    :auto-size="{ minRows: 4, maxRows: 10 }"
                    size="small"
                    allow-clear
                  />
                  <a-button type="text" size="mini" class="format-btn" @click="formatBodyContent(expandedRecord)">
                    格式化
                  </a-button>
                </div>

                <!-- raw-xml / raw-text -->
                <a-textarea
                  v-else-if="expandedRecord.body_type === 'raw-xml' || expandedRecord.body_type === 'raw-text'"
                  v-model="expandedRecord.body_raw_content"
                  placeholder="请输入请求体内容"
                  :auto-size="{ minRows: 4, maxRows: 10 }"
                  size="small"
                  allow-clear
                />

                <!-- none -->
                <a-empty v-else description="无请求体" :image-style="{ height: '40px' }" />
              </div>

              <!-- 断言 -->
              <div class="expand-section">
                <div class="section-title">断言规则</div>
                <AssertionEditor
                  :model-value="assertionsList"
                  @update:model-value="updateAssertions"
                />
              </div>

              <!-- 数据规则 -->
              <div class="expand-section">
                <div class="section-title">数据规则</div>
                <DataRuleEditor
                  :model-value="dataRulesList"
                  @update:model-value="updateDataRules"
                />
              </div>

              <!-- 前置条件 & 备注 -->
              <div class="expand-row">
                <div class="expand-field">
                  <div class="field-label">前置条件</div>
                  <a-textarea
                    v-model="expandedRecord.preconditions"
                    placeholder="可选"
                    :auto-size="{ minRows: 1, maxRows: 3 }"
                    size="small"
                    allow-clear
                  />
                </div>

                <div class="expand-field">
                  <div class="field-label">备注</div>
                  <a-textarea
                    v-model="expandedRecord.remark"
                    placeholder="可选"
                    :auto-size="{ minRows: 1, maxRows: 3 }"
                    size="small"
                    allow-clear
                  />
                </div>
              </div>
            </div>
          </div>
        </transition>
      </div>
    </div>

    <!-- Step 3: 导入结果 -->
    <div v-else-if="step === 3" class="result-section">
      <div class="result-cards">
        <div class="result-card">
          <div class="result-card-value">{{ importResult?.total || 0 }}</div>
          <div class="result-card-label">总数</div>
        </div>
        <div class="result-card result-card-success">
          <div class="result-card-value">{{ importResult?.success || 0 }}</div>
          <div class="result-card-label">成功</div>
        </div>
        <div class="result-card result-card-error">
          <div class="result-card-value">{{ importResult?.failed || 0 }}</div>
          <div class="result-card-label">失败</div>
        </div>
      </div>

      <div v-if="importResult?.errors && importResult.errors.length > 0" class="error-list">
        <div class="error-list-header">
          <icon-exclamation-circle />
          <span>失败详情</span>
        </div>
        <a-table :data="importResult.errors" :pagination="false" size="small" :bordered="false">
          <template #columns>
            <a-table-column title="行号" data-index="row" :width="70" align="center" />
            <a-table-column title="用例名称" data-index="name" :width="180" :ellipsis="true" />
            <a-table-column title="错误原因" data-index="error" :ellipsis="true" />
          </template>
        </a-table>
      </div>
    </div>

    <template #footer>
      <div class="modal-footer">
        <a-button v-if="step > 1" @click="step--">
          上一步
        </a-button>
        <div class="footer-right">
          <a-button v-if="step === 1" type="primary" :disabled="!file" @click="handleParse">
            <template #icon><icon-right /></template>
            解析文件
          </a-button>
          <a-button v-if="step === 2" type="primary" :loading="importLoading" @click="handleImport">
            <template #icon><icon-import /></template>
            确认导入
          </a-button>
          <a-button v-if="step === 3" type="primary" @click="handleFinish">
            <template #icon><icon-check /></template>
            完成
          </a-button>
        </div>
      </div>
    </template>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { Message } from '@arco-design/web-vue'
import {
  IconUpload,
  IconDownload,
  IconExclamationCircle,
  IconFile,
  IconDelete,
  IconCheck,
  IconRight,
  IconImport,
  IconExpand,
  IconClose,
} from '@arco-design/web-vue/es/icon'
import { parseExcelFile, generateExcelTemplate, parseHeaders, parseQueryParams, parseAssertions, parseDataRules } from '@/utils/excelParser'
import type { ParsedCase } from '@/utils/excelParser'
import { importExcelCases } from '@/api/excelImport'
import type { ExcelImportResult } from '@/api/excelImport'
import KeyValueEditor from './KeyValueEditor.vue'
import type { KVRow } from './KeyValueEditor.vue'
import AssertionEditor from './AssertionEditor.vue'
import type { AssertionItem } from '@/api/apiTestCase'
import DataRuleEditor from './DataRuleEditor.vue'
import type { DataRuleItem } from '@/api/apiTestCase'

const props = defineProps<{
  projectId: number
}>()

const emit = defineEmits<{
  (e: 'success'): void
}>()

const visible = defineModel<boolean>('visible', { default: false })
const step = ref(1)
const step1Tab = ref('upload')
const file = ref<File | null>(null)
const parseError = ref('')
const parsedCases = ref<ParsedCase[]>([])
const selectedRows = ref<(string | number)[]>([])
const importLoading = ref(false)
const importResult = ref<ExcelImportResult | null>(null)

const methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
const priorities = ['P0', 'P1', 'P2', 'P3']

// 填写规范数据
const fieldGuide = [
  { field: '用例名称', required: true, desc: '用例的名称，最大200字符', example: '用户登录' },
  { field: '请求方法', required: true, desc: 'HTTP请求方法（大写）', example: 'GET / POST / PUT / DELETE' },
  { field: '请求URL', required: true, desc: '接口地址，支持相对路径', example: '/api/v1/auth/login' },
  { field: '所属模块', required: false, desc: '用例所属模块，用于分类', example: '认证模块' },
  { field: '优先级', required: false, desc: '默认P2', example: 'P0(致命) / P1(严重) / P2(一般) / P3(轻微)' },
  { field: '描述', required: false, desc: '用例的详细描述', example: '用户登录接口' },
  { field: '前置条件', required: false, desc: '执行前需要满足的条件', example: '已注册账号' },
  { field: 'Body类型', required: false, desc: '请求体类型，默认none', example: 'none / form-data / raw-json' },
  { field: 'Body内容', required: false, desc: '请求体内容，JSON格式', example: '{"username":"admin"}' },
  { field: '请求头', required: false, desc: 'JSON对象格式', example: '{"Content-Type":"application/json"}' },
  { field: '查询参数', required: false, desc: 'JSON对象格式，URL查询参数', example: '{"page":"1","size":"10"}' },
  { field: '断言', required: false, desc: 'JSON数组格式，详见断言规则', example: '[{"type":"status_code",...}]' },
  { field: '数据提取', required: false, desc: 'JSON数组格式，详见数据提取规则', example: '[{"name":"token","source":"jsonpath",...}]' },
  { field: '备注', required: false, desc: '备注信息', example: '需要验证码' },
]

const assertionTypes = [
  { type: 'status_code', desc: 'HTTP状态码', needField: false, expectedExample: '200' },
  { type: 'jsonpath', desc: 'JSONPath提取值', needField: true, expectedExample: '$.code → 0' },
  { type: 'header', desc: '响应头字段', needField: true, expectedExample: 'Content-Type → application/json' },
  { type: 'response_time', desc: '响应时间(毫秒)', needField: false, expectedExample: '1000' },
  { type: 'body_contains', desc: '响应体包含文本', needField: false, expectedExample: 'success' },
]

const extractSources = [
  { source: 'jsonpath', desc: 'JSONPath表达式', expressionExample: '$.data.token', descExample: '提取JSON响应中的字段' },
  { source: 'regex', desc: '正则表达式', expressionExample: '"token":"(.*?)"', descExample: '用正则捕获组提取' },
  { source: 'header', desc: '响应头', expressionExample: 'Content-Type', descExample: '提取响应头字段值' },
]

const extractExamples = [
  {
    title: 'JSONPath提取token',
    json: '[{"name":"token","source":"jsonpath","expression":"$.data.token","description":"提取登录token"}]',
  },
  {
    title: '正则提取状态码',
    json: '[{"name":"code","source":"regex","expression":"\\"code\\":(\\\\d+)","description":"提取状态码"}]',
  },
  {
    title: '响应头提取',
    json: '[{"name":"contentType","source":"header","expression":"Content-Type","description":"提取Content-Type"}]',
  },
]

const assertionOperators = [
  { value: 'equals', label: '等于' },
  { value: 'not_equals', label: '不等于' },
  { value: 'contains', label: '包含' },
  { value: 'greater_than', label: '大于' },
  { value: 'less_than', label: '小于' },
  { value: 'regex', label: '正则匹配' },
  { value: 'exists', label: '存在' },
]

const assertionExamples = [
  {
    title: '状态码断言',
    json: '[{"type":"status_code","operator":"equals","expected":"200"}]',
  },
  {
    title: 'JSON字段断言',
    json: '[{"type":"jsonpath","field":"$.code","operator":"equals","expected":"0"}]',
  },
  {
    title: '响应时间断言',
    json: '[{"type":"response_time","operator":"less_than","expected":"1000","description":"响应<1秒"}]',
  },
  {
    title: '响应头断言',
    json: '[{"type":"header","field":"Content-Type","operator":"contains","expected":"application/json"}]',
  },
  {
    title: '正文包含断言',
    json: '[{"type":"body_contains","operator":"contains","expected":"success"}]',
  },
  {
    title: '字段存在断言',
    json: '[{"type":"jsonpath","field":"$.data.token","operator":"exists","expected":""}]',
  },
]

const bodyTypeOptions = [
  { value: 'none', desc: '无请求体（GET/DELETE等）' },
  { value: 'form-data', desc: '表单数据，支持文件上传' },
  { value: 'x-www-form-urlencoded', desc: 'URL编码表单' },
  { value: 'raw-json', desc: 'JSON格式请求体' },
  { value: 'raw-xml', desc: 'XML格式请求体' },
  { value: 'raw-text', desc: '纯文本请求体' },
]

const getMethodColor = (method: string) => {
  const colors: Record<string, string> = {
    GET: 'blue', POST: 'green', PUT: 'orange', DELETE: 'red', PATCH: 'purple', HEAD: 'grayblue', OPTIONS: 'gray'
  }
  return colors[method] || 'gray'
}

const getPriorityColor = (priority: string) => {
  const colors: Record<string, string> = { P0: 'red', P1: 'orange', P2: 'blue', P3: 'green' }
  return colors[priority] || 'gray'
}

const errorCount = computed(() => parsedCases.value.filter(c => c._errors.length > 0).length)

const pagination = reactive({
  pageSize: 10,
  showTotal: true,
  showJumper: true,
})

// 展开详情面板
const expandedRecord = ref<ParsedCase | null>(null)

const isRowExpanded = (record: ParsedCase) => {
  return expandedRecord.value === record
}

const toggleExpand = (record: ParsedCase) => {
  if (expandedRecord.value === record) {
    expandedRecord.value = null
  } else {
    expandedRecord.value = record
  }
}

const getRecordIndex = (record: ParsedCase) => {
  return parsedCases.value.indexOf(record)
}

// JSON 字符串 ↔ 结构化数据 转换
const safeParseJsonObj = (str?: string): Record<string, any> => {
  if (!str?.trim()) return {}
  try {
    const obj = JSON.parse(str)
    return (typeof obj === 'object' && obj !== null && !Array.isArray(obj)) ? obj : {}
  } catch { return {} }
}

const safeParseJsonArr = (str?: string): any[] => {
  if (!str?.trim()) return []
  try {
    const arr = JSON.parse(str)
    return Array.isArray(arr) ? arr : []
  } catch { return [] }
}

// 请求头 JSON → KVRow[]
const headersKV = computed<KVRow[]>(() => {
  if (!expandedRecord.value) return []
  const obj = safeParseJsonObj(expandedRecord.value.headers_json)
  return Object.entries(obj).map(([key, value]) => ({
    enabled: true, key, value: String(value ?? ''), description: ''
  }))
})

// Query参数 JSON → KVRow[]
const paramsKV = computed<KVRow[]>(() => {
  if (!expandedRecord.value) return []
  const obj = safeParseJsonObj(expandedRecord.value.params_json)
  return Object.entries(obj).map(([key, value]) => ({
    enabled: true, key, value: String(value ?? ''), description: ''
  }))
})

// Body form-data JSON → KVRow[]
const bodyFormKV = computed<KVRow[]>(() => {
  if (!expandedRecord.value) return []
  const obj = safeParseJsonObj(expandedRecord.value.body_raw_content)
  return Object.entries(obj).map(([key, value]) => ({
    enabled: true, key, value: String(value ?? ''), description: ''
  }))
})

// 断言 JSON → AssertionItem[]
const assertionsList = computed<AssertionItem[]>(() => {
  if (!expandedRecord.value) return []
  const arr = safeParseJsonArr(expandedRecord.value.assertions_json)
  return arr.map((item: any) => ({
    assertion_type: String(item.assertion_type || item.type || 'status_code').trim().toLowerCase() as AssertionItem['assertion_type'],
    operator: String(item.operator || 'equals').trim().toLowerCase() as AssertionItem['operator'],
    field: String(item.field || '').trim(),
    expected: String(item.expected || '').trim(),
    description: String(item.description || '').trim(),
  }))
})

// 数据提取 JSON → DataRuleItem[]
const dataRulesList = computed<DataRuleItem[]>(() => {
  if (!expandedRecord.value) return []
  const arr = safeParseJsonArr(expandedRecord.value.extracts_json)
  return arr.map((item: any) => ({
    name: String(item.name || '').trim(),
    rule_type: 'extract',
    source: String(item.source || 'jsonpath').trim().toLowerCase() as DataRuleItem['source'],
    expression: String(item.expression || '').trim(),
    default_value: String(item.default_value || item.default || '').trim(),
    description: String(item.description || '').trim(),
    enabled: true,
  }))
})

// KVRow[] → JSON 字符串（同步回 expandedRecord）
const updateHeadersFromKV = (rows: KVRow[]) => {
  if (!expandedRecord.value) return
  const obj: Record<string, string> = {}
  rows.filter(r => r.enabled && r.key.trim()).forEach(r => { obj[r.key.trim()] = r.value })
  expandedRecord.value.headers_json = Object.keys(obj).length > 0 ? JSON.stringify(obj) : ''
}

const updateParamsFromKV = (rows: KVRow[]) => {
  if (!expandedRecord.value) return
  const obj: Record<string, string> = {}
  rows.filter(r => r.enabled && r.key.trim()).forEach(r => { obj[r.key.trim()] = r.value })
  expandedRecord.value.params_json = Object.keys(obj).length > 0 ? JSON.stringify(obj) : ''
}

const updateBodyFormFromKV = (rows: KVRow[]) => {
  if (!expandedRecord.value) return
  const obj: Record<string, string> = {}
  rows.filter(r => r.enabled && r.key.trim()).forEach(r => { obj[r.key.trim()] = r.value })
  expandedRecord.value.body_raw_content = Object.keys(obj).length > 0 ? JSON.stringify(obj) : ''
}

const updateAssertions = (items: AssertionItem[]) => {
  if (!expandedRecord.value) return
  const arr = items
    .filter(a => a.assertion_type && a.operator)
    .map(({ assertion_type, operator, field, expected, description }) => ({
      type: assertion_type, operator, field, expected, description
    }))
  expandedRecord.value.assertions_json = arr.length > 0 ? JSON.stringify(arr) : ''
}

const updateDataRules = (items: DataRuleItem[]) => {
  if (!expandedRecord.value) return
  const arr = items
    .filter(e => e.name && e.expression)
    .map(({ name, source, expression, default_value, description }) => ({
      name, source, expression, default_value, description
    }))
  expandedRecord.value.extracts_json = arr.length > 0 ? JSON.stringify(arr) : ''
}

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const clearFile = () => {
  file.value = null
  parseError.value = ''
}

const handleFileChange = (fileList: any) => {
  if (fileList.length > 0) {
    file.value = fileList[0].file
    parseError.value = ''
  }
}

const downloadTemplate = async () => {
  const blob = await generateExcelTemplate()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = '用例导入模板.xlsx'
  a.click()
  URL.revokeObjectURL(url)
}

const handleParse = async () => {
  if (!file.value) return

  try {
    parseError.value = ''
    const raw = await parseExcelFile(file.value)
    // 深拷贝并添加唯一 ID
    parsedCases.value = JSON.parse(JSON.stringify(raw)).map((item: any, index: number) => ({
      ...item,
      _id: index
    }))
    selectedRows.value = []
    step.value = 2
  } catch (error) {
    parseError.value = (error as Error).message
  }
}

const deleteSelected = () => {
  parsedCases.value = parsedCases.value.filter((record: any) => !selectedRows.value.includes(record._id))
  selectedRows.value = []
}

const clearAll = () => {
  parsedCases.value = []
  selectedRows.value = []
  expandedRecord.value = null
}

const reupload = () => {
  step.value = 1
  file.value = null
  parsedCases.value = []
  selectedRows.value = []
  expandedRecord.value = null
  parseError.value = ''
}

const getRowClass = (record: ParsedCase) => {
  return record._errors.length > 0 ? 'row-error' : ''
}

const hasFieldError = (record: ParsedCase, field: string) => {
  return record._errors.some(e => e.includes(field))
}

// 格式化Body内容
const formatBodyContent = (record: ParsedCase) => {
  if (!record.body_raw_content?.trim()) return
  try {
    const parsed = JSON.parse(record.body_raw_content)
    record.body_raw_content = JSON.stringify(parsed, null, 2)
  } catch {
    // 格式不合法，不做处理
  }
}

const handleImport = async () => {
  if (errorCount.value > 0) {
    Message.warning('请先修正所有错误再导入')
    return
  }

  importLoading.value = true

  try {
    const result = await importExcelCases({
      cases: parsedCases.value.map(c => {
        // 根据 body_type 处理 body 内容
        let bodyForm = c.body_form
        let bodyRawContent = c.body_raw_content

        if (c.body_type === 'form-data' || c.body_type === 'x-www-form-urlencoded') {
          // 从 body_raw_content 解析出 body_form
          try {
            const obj = JSON.parse(bodyRawContent || '{}')
            if (typeof obj === 'object' && !Array.isArray(obj)) {
              bodyForm = Object.entries(obj).map(([key, value]) => ({
                enabled: true,
                key,
                value: String(value ?? ''),
                param_type: 'text',
                description: ''
              }))
            }
          } catch {
            // 保持原始 body_form
          }
        }

        return {
          name: c.name,
          method: c.method,
          url: c.url,
          module: c.module,
          priority: c.priority,
          description: c.description,
          preconditions: c.preconditions,
          body_type: c.body_type,
          body_raw_content: bodyRawContent,
          remark: c.remark,
          headers: parseHeaders(c.headers_json),
          query_params: parseQueryParams(c.params_json),
          body_form: bodyForm,
          assertions: parseAssertions(c.assertions_json),
          data_rules: parseDataRules(c.extracts_json),
        }
      }),
      project_id: props.projectId,
    })

    importResult.value = result
    step.value = 3

    if (result.success > 0) {
      Message.success(`成功导入 ${result.success} 条用例`)
      emit('success')
    }
  } catch (error) {
    Message.error('导入失败：' + (error as Error).message)
  } finally {
    importLoading.value = false
  }
}

const handleClose = () => {
  step.value = 1
  file.value = null
  parsedCases.value = []
  selectedRows.value = []
  expandedRecord.value = null
  importResult.value = null
  parseError.value = ''
}

const handleFinish = () => {
  visible.value = false
  handleClose()
}
</script>

<style scoped>
.upload-section {
  padding: var(--space-md) 0;
}

/* 填写规范样式 */
.guide-content {
  max-height: 520px;
  overflow-y: auto;
  padding: var(--space-sm) 0;
}

.guide-card {
  margin-bottom: var(--space-md);
  border-left: 3px solid var(--color-primary);
}

.guide-card :deep(.arco-card-header) {
  background-color: var(--color-fill-2);
}

.guide-card :deep(.arco-table-td) {
  padding: 10px 12px;
  line-height: 1.6;
}

.guide-card h4 {
  margin: var(--space-md) 0 var(--space-sm);
  font-size: 13px;
  color: var(--color-text-1);
}

.required {
  color: var(--color-danger);
  font-weight: 500;
}

.example-code {
  background-color: var(--color-fill-2);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: var(--color-text-1);
  word-break: break-all;
}

.assertion-guide {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.assertion-section h4 {
  margin: 0 0 var(--space-sm);
  font-size: 13px;
  color: var(--color-text-1);
  font-weight: 500;
}

.operator-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.operator-tags :deep(.arco-tag) {
  font-size: 13px;
  padding: 4px 10px;
}

.assertion-examples {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.assertion-example {
  background-color: var(--color-fill-1);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
}

.extract-guide {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.extract-section h4 {
  margin: 0 0 var(--space-sm);
  font-size: 13px;
  color: var(--color-text-1);
  font-weight: 500;
}

.extract-examples {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.extract-example {
  background-color: var(--color-fill-1);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
}

.example-title {
  font-size: 12px;
  color: var(--color-text-2);
  margin-bottom: 4px;
}

.example-json {
  display: block;
  background-color: var(--color-fill-2);
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: var(--color-text-1);
  word-break: break-all;
  white-space: pre-wrap;
}

.method-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.body-type-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.body-type-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 13px;
}

.body-type-item code {
  background-color: var(--color-fill-2);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  min-width: 130px;
}

.param-examples {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.param-example {
  background-color: var(--color-fill-1);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
}

.example-url {
  color: var(--color-primary);
  font-size: 13px;
  word-break: break-all;
}

.template-download {
  margin-bottom: var(--space-lg);
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.template-hint {
  color: var(--color-text-3);
  font-size: 13px;
}

.upload-area {
  width: 100%;
  padding: 48px var(--space-xl);
  border: 2px dashed var(--color-border-3);
  border-radius: var(--radius-lg);
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: var(--color-fill-1);
}

.upload-area:hover {
  border-color: var(--color-primary);
  background: var(--color-primary-light-1);
}

.upload-icon {
  margin-bottom: var(--space-md);
  font-size: 48px;
  color: var(--color-text-3);
  transition: color 0.2s ease;
}

.upload-area:hover .upload-icon {
  color: var(--color-primary);
}

.upload-text {
  font-size: 15px;
  color: var(--color-text-2);
  margin-bottom: var(--space-xs);
}

.upload-hint {
  font-size: 13px;
  color: var(--color-text-3);
}

.file-info {
  margin-top: var(--space-lg);
  padding: var(--space-md) var(--space-lg);
  background: var(--color-fill-2);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  transition: all 0.2s ease;
}

.file-info:hover {
  background: var(--color-fill-3);
}

.file-icon {
  color: var(--color-primary);
  font-size: 18px;
}

.file-name {
  font-weight: 500;
  color: var(--color-text-1);
  flex: 1;
}

.file-size {
  color: var(--color-text-3);
  font-size: 13px;
}

.parse-error {
  margin-top: var(--space-lg);
  padding: var(--space-md) var(--space-lg);
  background: var(--color-danger-light-1);
  border-radius: var(--radius-md);
  color: var(--color-danger);
  display: flex;
  align-items: flex-start;
  gap: var(--space-sm);
}

.parse-error span {
  flex: 1;
}

/* 预览区域 */
.preview-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.preview-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-sm) 0;
}

.preview-info {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: 14px;
}

.info-label {
  color: var(--color-text-3);
}

.info-count {
  font-weight: 600;
  color: var(--color-text-1);
  font-size: 16px;
}

.info-separator {
  color: var(--color-text-4);
  margin: 0 var(--space-xs);
}

.info-error {
  color: var(--color-danger);
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
}

.preview-actions {
  display: flex;
  gap: var(--space-sm);
}

/* 展开按钮 */
.expand-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  color: var(--color-text-3);
  transition: all 0.2s ease;
}

.expand-btn:hover {
  background-color: var(--color-primary-light-1);
  color: var(--color-primary);
}

.expand-btn.expanded {
  transform: rotate(90deg);
  color: var(--color-primary);
}

/* 表格容器 */
.table-container {
  border: 1px solid var(--color-border-2);
  border-radius: var(--radius-md);
  overflow: visible;
}

.table-container :deep(.arco-table) {
  border: none;
}

.table-container :deep(.arco-table-th) {
  background-color: var(--color-fill-2);
  font-weight: 500;
  font-size: 13px;
  color: var(--color-text-2);
  border-bottom: 1px solid var(--color-border-3);
}

.table-container :deep(.arco-table-td) {
  padding: 6px 10px;
  font-size: 13px;
  border-bottom: 1px solid var(--color-border-1);
}

.table-container :deep(.arco-table-tr:hover .arco-table-td) {
  background-color: var(--color-fill-2);
}

.table-container :deep(.arco-table-body) {
  overflow-y: auto;
}

/* 可点击的 Tag */
.clickable-tag {
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.clickable-tag:hover {
  opacity: 0.8;
  transform: scale(1.05);
}

.clickable-tag.tag-error {
  outline: 2px solid var(--color-danger);
  outline-offset: 1px;
}

/* Popover 选项列表 */
.popover-options {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 80px;
}

.popover-option {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px 8px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.15s ease;
}

.popover-option:hover {
  background-color: var(--color-fill-2);
}

.popover-option.active {
  background-color: var(--color-primary-light-1);
}

/* 展开详情面板 */
.expand-panel {
  margin-top: var(--space-md);
  border: 1px solid var(--color-border-2);
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--color-white);
}

.expand-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-sm) var(--space-lg);
  background: var(--color-fill-2);
  border-bottom: 1px solid var(--color-border-2);
}

.expand-panel-title {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-weight: 500;
  font-size: 13px;
  color: var(--color-text-1);
}

.expand-panel-body {
  padding: var(--space-lg) var(--space-xl);
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

/* 展开区块 */
.expand-section {
  border: 1px solid var(--color-border-2);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  background: var(--color-fill-1);
}

.section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-1);
  margin-bottom: var(--space-sm);
}

.expand-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-md);
}

.expand-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.raw-body {
  position: relative;
}

.raw-body .format-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  z-index: 1;
}

.expand-field.full-width {
  grid-column: 1 / -1;
}

.field-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-2);
}

.field-label :deep(.arco-btn-text) {
  font-size: 12px;
  color: var(--color-primary);
  padding: 0 4px;
  height: 20px;
}

.expand-panel :deep(.arco-textarea-wrapper) {
  background-color: var(--color-white);
  border: 1px solid var(--color-border-2);
  transition: all 0.2s ease;
}

.expand-panel :deep(.arco-textarea-wrapper:hover) {
  border-color: var(--color-primary-light-3);
}

.expand-panel :deep(.arco-textarea-wrapper:focus-within) {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px var(--color-primary-light-1);
}

.expand-panel :deep(.arco-select) {
  width: 100%;
}

/* 滑入滑出动画 */
.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}

.slide-fade-leave-active {
  transition: all 0.2s ease-in;
}

.slide-fade-enter-from {
  transform: translateY(-10px);
  opacity: 0;
}

.slide-fade-leave-to {
  transform: translateY(-10px);
  opacity: 0;
}

.row-index {
  font-size: 12px;
  color: var(--color-text-3);
  font-weight: 500;
}

.row-error {
  background-color: var(--color-danger-light-1) !important;
}

.row-error:hover {
  background-color: var(--color-danger-light-2) !important;
}

.input-error {
  border-color: var(--color-danger) !important;
}

/* 结果区域 */
.result-section {
  padding: var(--space-lg) 0;
}

.result-cards {
  display: flex;
  gap: var(--space-lg);
  margin-bottom: var(--space-xl);
}

.result-card {
  flex: 1;
  padding: var(--space-lg);
  background: var(--color-fill-2);
  border-radius: var(--radius-md);
  text-align: center;
  transition: all 0.2s ease;
}

.result-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.result-card-success {
  background: linear-gradient(135deg, #e8f5e9, #c8e6c9);
  border-left: 4px solid var(--color-success);
}

.result-card-error {
  background: linear-gradient(135deg, #ffebee, #ffcdd2);
  border-left: 4px solid var(--color-danger);
}

.result-card-value {
  font-size: 32px;
  font-weight: 600;
  color: var(--color-text-1);
  line-height: 1.2;
}

.result-card-success .result-card-value {
  color: var(--color-success);
}

.result-card-error .result-card-value {
  color: var(--color-danger);
}

.result-card-label {
  font-size: 13px;
  color: var(--color-text-3);
  margin-top: var(--space-xs);
}

.error-list {
  margin-top: var(--space-lg);
  border: 1px solid var(--color-border-2);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.error-list-header {
  padding: var(--space-md) var(--space-lg);
  background: var(--color-fill-2);
  color: var(--color-text-1);
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  border-bottom: 1px solid var(--color-border-2);
}

.error-list-header .arco-icon {
  color: var(--color-danger);
}

/* 底部按钮 */
.modal-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.footer-right {
  display: flex;
  gap: var(--space-sm);
}
</style>

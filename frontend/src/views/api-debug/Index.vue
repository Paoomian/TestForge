<template>
  <div class="api-debug">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="page-header-info">
        <h2 class="page-title">接口调试</h2>
        <p class="page-desc">快速测试和调试API接口</p>
      </div>
    </div>

    <!-- 请求配置卡片 -->
    <a-card :bordered="false" class="request-card">
      <!-- 请求方法 + URL -->
      <div class="request-line">
        <HttpMethodSelect v-model="requestData.method" />
        <a-input
          v-model="requestData.url"
          placeholder="请输入请求URL，如：https://api.example.com/users"
          class="url-input"
          @keyup.enter="sendRequest"
        />
        <a-button type="primary" @click="sendRequest" :loading="loading">
          <template #icon><icon-send /></template>
          发送请求
        </a-button>
      </div>

      <!-- 参数配置 Tabs -->
      <a-tabs default-active-key="headers" size="small" class="config-tabs">
        <a-tab-pane key="headers">
          <template #title>
            Headers
            <a-badge v-if="enabledHeadersCount > 0" :count="enabledHeadersCount" :max="99" />
          </template>
          <KeyValueEditor
            v-model="headers"
            key-placeholder="Header Name"
            value-placeholder="Header Value"
            add-text="添加请求头"
          />
        </a-tab-pane>

        <a-tab-pane key="params">
          <template #title>
            Query Params
            <a-badge v-if="enabledParamsCount > 0" :count="enabledParamsCount" :max="99" />
          </template>
          <KeyValueEditor
            v-model="queryParams"
            key-placeholder="参数名"
            value-placeholder="参数值"
            add-text="添加查询参数"
          />
        </a-tab-pane>

        <a-tab-pane key="body">
          <template #title>Body</template>
          <BodyEditor
            :body-type="bodyType"
            :body-form="bodyForm"
            :raw-content="rawContent"
            @update:body-type="bodyType = $event"
            @update:body-form="bodyForm = $event"
            @update:raw-content="rawContent = $event"
          />
        </a-tab-pane>

        <a-tab-pane key="auth">
          <template #title>Auth</template>
          <AuthConfig
            :model-value="authData"
            @update:model-value="authData = $event"
          />
        </a-tab-pane>
      </a-tabs>
    </a-card>

    <!-- 响应结果卡片 -->
    <a-card v-if="response" :bordered="false" class="response-card">
      <template #title>
        <span class="card-title">响应结果</span>
      </template>
      <a-descriptions :column="2" bordered size="small">
        <a-descriptions-item label="状态码">
          <a-tag :color="response.status_code < 400 ? 'green' : 'red'">
            {{ response.status_code }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="耗时">
          <span class="time-highlight">{{ (response.elapsed * 1000).toFixed(0) }} ms</span>
        </a-descriptions-item>
      </a-descriptions>

      <div class="response-body-section">
        <h4 class="section-label">响应体</h4>
        <JsonViewer :content="response.body" max-height="600px" />
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { Message } from '@arco-design/web-vue'
import request from '@/utils/request'
import JsonViewer from '@/components/JsonViewer.vue'
import HttpMethodSelect from '@/views/api-test/components/HttpMethodSelect.vue'
import KeyValueEditor from '@/views/api-test/components/KeyValueEditor.vue'
import type { KVRow } from '@/views/api-test/components/KeyValueEditor.vue'
import BodyEditor from '@/views/api-test/components/BodyEditor.vue'
import AuthConfig from '@/views/api-test/components/AuthConfig.vue'
import type { BodyFormItem, AuthConfig as AuthConfigType } from '@/api/apiTestCase'

const loading = ref(false)

// 请求数据
const requestData = reactive({
  method: 'GET',
  url: ''
})

const headers = ref<KVRow[]>([{ enabled: true, key: '', value: '', description: '' }])
const queryParams = ref<KVRow[]>([{ enabled: true, key: '', value: '', description: '' }])
const bodyType = ref('none')
const bodyForm = ref<BodyFormItem[]>([])
const rawContent = ref('')
const authData = ref<AuthConfigType>({ auth_type: 'none' })

const response = ref<any>(null)

// 计算已启用的 key 数量
const enabledHeadersCount = computed(() =>
  headers.value.filter(h => h.enabled && h.key).length
)
const enabledParamsCount = computed(() =>
  queryParams.value.filter(p => p.enabled && p.key).length
)

// KVRow[] 转 {key: value} 对象
function kvToDict(rows: KVRow[]): Record<string, string> {
  const dict: Record<string, string> = {}
  for (const row of rows) {
    if (row.enabled && row.key) {
      dict[row.key] = row.value
    }
  }
  return dict
}

const sendRequest = async () => {
  if (!requestData.url) {
    Message.warning('请输入请求URL')
    return
  }

  loading.value = true
  try {
    const headersDict = kvToDict(headers.value)
    const paramsDict = kvToDict(queryParams.value)

    // 根据 bodyType 组装 body
    let bodyStr: string | null = null
    let sendBodyType = bodyType.value

    if (bodyType.value === 'raw-json') {
      bodyStr = rawContent.value
      sendBodyType = 'json'
    } else if (bodyType.value === 'raw-xml') {
      bodyStr = rawContent.value
      sendBodyType = 'xml'
    } else if (bodyType.value === 'raw-text') {
      bodyStr = rawContent.value
      sendBodyType = 'text'
    } else if (bodyType.value === 'form-data' || bodyType.value === 'x-www-form-urlencoded') {
      // 表单数据转为 JSON 字符串传递
      const formDict = kvToDict(bodyForm.value.map(f => ({ ...f })))
      bodyStr = JSON.stringify(formDict)
      sendBodyType = bodyType.value === 'form-data' ? 'form-data' : 'x-www-form-urlencoded'
    }

    const res = await request({
      url: '/api-cases/debug',
      method: 'post',
      data: {
        method: requestData.method,
        url: requestData.url,
        headers: headersDict,
        query_params: paramsDict,
        body: bodyStr,
        body_type: sendBodyType
      }
    })

    response.value = res
    Message.success('请求成功')
  } catch (error) {
    Message.error('请求失败')
  } finally {
    loading.value = false
  }
}

</script>

<style scoped>
.api-debug {
  width: 100%;
}

.page-header {
  margin-bottom: 20px;
}

.page-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--gray-800);
  margin: 0 0 4px 0;
}

.page-desc {
  font-size: var(--font-size-sm);
  color: var(--gray-500);
  margin: 0;
}

.request-card {
  margin-bottom: 20px;
}

.request-line {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  margin-bottom: 16px;
}

.url-input {
  flex: 1;
}

.config-tabs :deep(.arco-tabs-content) {
  padding-top: 12px;
}

.response-card {
  margin-top: 0;
}

.card-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--gray-800);
}

.time-highlight {
  color: var(--indigo-600);
  font-weight: var(--font-weight-semibold);
}

.response-body-section {
  margin-top: 20px;
}

.section-label {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--gray-700);
  margin: 0 0 12px 0;
}

</style>

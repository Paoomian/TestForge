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
      <a-form :model="requestData" layout="vertical">
        <a-form-item label="请求配置">
          <a-space style="width: 100%">
            <a-select v-model="requestData.method" style="width: 120px">
              <a-option value="GET">GET</a-option>
              <a-option value="POST">POST</a-option>
              <a-option value="PUT">PUT</a-option>
              <a-option value="DELETE">DELETE</a-option>
              <a-option value="PATCH">PATCH</a-option>
            </a-select>
            <a-input
              v-model="requestData.url"
              placeholder="请输入请求URL，如：https://api.example.com/users"
              style="flex: 1"
            />
            <a-button type="primary" @click="sendRequest" :loading="loading">
              <template #icon><icon-send /></template>
              发送请求
            </a-button>
          </a-space>
        </a-form-item>

        <a-tabs>
          <a-tab-pane key="headers" title="Headers">
            <a-textarea
              v-model="headersText"
              placeholder='{"Content-Type": "application/json"}'
              :auto-size="{ minRows: 3, maxRows: 8 }"
            />
          </a-tab-pane>
          <a-tab-pane key="params" title="Query Params">
            <a-textarea
              v-model="paramsText"
              placeholder='{"key": "value"}'
              :auto-size="{ minRows: 3, maxRows: 8 }"
            />
          </a-tab-pane>
          <a-tab-pane key="body" title="Body">
            <a-textarea
              v-model="requestData.body"
              placeholder='{"key": "value"}'
              :auto-size="{ minRows: 5, maxRows: 15 }"
            />
          </a-tab-pane>
        </a-tabs>
      </a-form>
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
        <a-textarea
          :model-value="formatResponse(response.body)"
          readonly
          :auto-size="{ minRows: 10, maxRows: 30 }"
        />
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { Message } from '@arco-design/web-vue'
import request from '@/utils/request'

const loading = ref(false)
const headersText = ref('{}')
const paramsText = ref('{}')

const requestData = reactive({
  method: 'GET',
  url: '',
  body: ''
})

const response = ref<any>(null)

const sendRequest = async () => {
  if (!requestData.url) {
    Message.warning('请输入请求URL')
    return
  }

  loading.value = true
  try {
    const headers = JSON.parse(headersText.value || '{}')
    const params = JSON.parse(paramsText.value || '{}')

    const res = await request({
      url: '/api-cases/debug',
      method: 'post',
      data: {
        method: requestData.method,
        url: requestData.url,
        headers,
        query_params: params,
        body: requestData.body,
        body_type: 'json'
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

const formatResponse = (body: string) => {
  try {
    return JSON.stringify(JSON.parse(body), null, 2)
  } catch {
    return body
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

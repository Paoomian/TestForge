<template>
  <div class="api-debug">
    <a-card title="接口调试" :bordered="false">
      <a-form layout="vertical">
        <a-form-item label="请求方法">
          <a-space>
            <a-select v-model="requestData.method" style="width: 120px">
              <a-option value="GET">GET</a-option>
              <a-option value="POST">POST</a-option>
              <a-option value="PUT">PUT</a-option>
              <a-option value="DELETE">DELETE</a-option>
              <a-option value="PATCH">PATCH</a-option>
            </a-select>
            <a-input
              v-model="requestData.url"
              placeholder="请输入请求URL"
              style="flex: 1"
            />
            <a-button type="primary" @click="sendRequest" :loading="loading">
              发送
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

      <a-divider />

      <div v-if="response">
        <h3>响应结果</h3>
        <a-descriptions :column="2" bordered>
          <a-descriptions-item label="状态码">
            <a-tag :color="response.status_code < 400 ? 'green' : 'red'">
              {{ response.status_code }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="耗时">
            {{ (response.elapsed * 1000).toFixed(0) }} ms
          </a-descriptions-item>
        </a-descriptions>

        <h4 style="margin-top: 16px">响应体</h4>
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
</style>

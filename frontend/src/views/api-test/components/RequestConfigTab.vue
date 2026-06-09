<template>
  <div class="request-config-tab">
    <!-- 环境选择 -->
    <div style="margin-bottom: 8px;">
      <EnvironmentSelect
        :model-value="selectedEnvId"
        :project-id="projectId"
        @update:model-value="handleEnvChange"
        @change="handleEnvSelect"
      />
    </div>

    <!-- 请求方法 + URL -->
    <div style="display: flex; gap: 8px; margin-bottom: 16px; align-items: flex-start;">
      <HttpMethodSelect
        :model-value="formData.method"
        @update:model-value="update('method', $event)"
      />
      <div style="flex: 1;">
        <UrlInput
          :model-value="formData.url"
          :base-url="selectedEnvBaseUrl"
          @update:model-value="update('url', $event)"
        />
      </div>
    </div>

    <!-- Tabs: Headers / Query / Body / Auth -->
    <a-tabs default-active-key="headers" size="small" :destroy-on-hide="false">
      <a-tab-pane key="headers">
        <template #title>
          Headers
          <a-badge v-if="enabledHeadersCount > 0" :count="enabledHeadersCount" :max="99" />
        </template>
        <KeyValueEditor
          :model-value="formData.headers"
          @update:model-value="update('headers', $event)"
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
          :model-value="formData.query_params"
          @update:model-value="update('query_params', $event)"
          key-placeholder="参数名"
          value-placeholder="参数值"
          add-text="添加查询参数"
        />
      </a-tab-pane>

      <a-tab-pane key="body">
        <template #title>Body</template>
        <BodyEditor
          :body-type="formData.body_type"
          :body-form="formData.body_form"
          :raw-content="rawContent"
          @update:body-type="update('body_type', $event)"
          @update:body-form="update('body_form', $event)"
          @update:raw-content="$emit('update:rawContent', $event)"
        />
      </a-tab-pane>

      <a-tab-pane key="auth">
        <template #title>Auth</template>
        <AuthConfig
          :model-value="formData.auth || { auth_type: 'none' }"
          @update:model-value="handleAuthChange"
        />
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import HttpMethodSelect from './HttpMethodSelect.vue'
import UrlInput from './UrlInput.vue'
import EnvironmentSelect from './EnvironmentSelect.vue'
import KeyValueEditor from './KeyValueEditor.vue'
import BodyEditor from './BodyEditor.vue'
import AuthConfig from './AuthConfig.vue'
import type { HeaderItem, QueryParamItem, BodyFormItem, AuthConfig as AuthConfigType, Environment } from '@/api/apiTestCase'

interface FormData {
  method: string
  url: string
  body_type: string
  environment_id?: number
  headers: HeaderItem[]
  query_params: QueryParamItem[]
  body_form: BodyFormItem[]
  auth?: AuthConfigType
}

const props = defineProps<{
  formData: FormData
  rawContent: string
  projectId?: number
}>()

const emit = defineEmits<{
  (e: 'update', field: string, value: any): void
  (e: 'update:rawContent', value: string): void
}>()

const selectedEnvId = ref<number | null>(props.formData.environment_id || null)
const selectedEnvBaseUrl = ref('')

// 监听formData中的environment_id变化（如加载编辑数据时）
watch(() => props.formData.environment_id, (newVal) => {
  if (newVal !== selectedEnvId.value) {
    selectedEnvId.value = newVal || null
  }
})

const enabledHeadersCount = computed(() =>
  (props.formData.headers || []).filter(h => h.enabled && h.key).length
)

const enabledParamsCount = computed(() =>
  (props.formData.query_params || []).filter(p => p.enabled && p.key).length
)

function update(field: string, value: any) {
  emit('update', field, value)
}

function handleEnvChange(envId: number | null) {
  selectedEnvId.value = envId
  // 同步到formData
  update('environment_id', envId || undefined)
  if (!envId) {
    selectedEnvBaseUrl.value = ''
  }
}

function handleEnvSelect(env: Environment | null) {
  selectedEnvBaseUrl.value = env?.base_url || ''
}

function handleAuthChange(auth: AuthConfigType) {
  update('auth', auth)
  update('auth_type', auth.auth_type)
}
</script>

<style scoped>
.request-config-tab :deep(.arco-tabs-content) {
  padding-top: 12px;
}
</style>

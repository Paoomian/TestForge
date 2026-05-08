<template>
  <div class="auth-config">
    <a-form :model="authData" layout="vertical">
      <a-form-item label="认证类型">
        <a-select
          :model-value="authData.auth_type"
          @update:model-value="handleTypeChange"
        >
          <a-option value="none">无认证</a-option>
          <a-option value="bearer">Bearer Token</a-option>
          <a-option value="basic">Basic Auth</a-option>
          <a-option value="api_key">API Key</a-option>
        </a-select>
      </a-form-item>

      <!-- Bearer Token -->
      <template v-if="authData.auth_type === 'bearer'">
        <a-form-item label="Token">
          <a-input-password
            v-model="authData.token"
            placeholder="输入Bearer Token"
            @change="emitChange"
          />
        </a-form-item>
      </template>

      <!-- Basic Auth -->
      <template v-if="authData.auth_type === 'basic'">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="用户名">
              <a-input
                v-model="authData.username"
                placeholder="用户名"
                @change="emitChange"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="密码">
              <a-input-password
                v-model="authData.password"
                placeholder="密码"
                @change="emitChange"
              />
            </a-form-item>
          </a-col>
        </a-row>
      </template>

      <!-- API Key -->
      <template v-if="authData.auth_type === 'api_key'">
        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="Key Name">
              <a-input
                v-model="authData.api_key_name"
                placeholder="例如: X-API-Key"
                @change="emitChange"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="Key Value">
              <a-input-password
                v-model="authData.api_key_value"
                placeholder="API Key值"
                @change="emitChange"
              />
            </a-form-item>
          </a-col>
          <a-col :span="4">
            <a-form-item label="添加到">
              <a-select
                v-model="authData.api_key_location"
                @change="emitChange"
              >
                <a-option value="header">Header</a-option>
                <a-option value="query">Query</a-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
      </template>
    </a-form>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { AuthConfig as AuthConfigType } from '@/api/apiTestCase'

const props = defineProps<{
  modelValue: AuthConfigType
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: AuthConfigType): void
}>()

const defaultAuth: AuthConfigType = {
  auth_type: 'none',
  token: '',
  username: '',
  password: '',
  api_key_name: '',
  api_key_value: '',
  api_key_location: 'header',
}

const authData = ref<AuthConfigType>({ ...defaultAuth, ...props.modelValue })

watch(() => props.modelValue, (val) => {
  authData.value = { ...defaultAuth, ...val }
}, { deep: true })

function handleTypeChange(value: string | number | boolean | Record<string, any> | (string | number | boolean | Record<string, any>)[]) {
  authData.value.auth_type = value as AuthConfigType['auth_type']
  emitChange()
}

function emitChange() {
  emit('update:modelValue', { ...authData.value })
}
</script>

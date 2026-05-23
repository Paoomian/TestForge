<template>
  <ToolLayout title="JWT解析" description="粘贴JWT Token，解析Header和Payload">
    <template #input>
      <a-textarea
        v-model="input"
        placeholder="粘贴JWT Token（如 eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.xxx）"
        :style="{ height: '100%' }"
      />
    </template>
    <template #output>
      <div class="jwt-output">
        <div class="jwt-section">
          <div class="jwt-section-header">
            <a-tag color="blue" size="small">Header</a-tag>
            <a-button type="text" size="mini" @click="copyJson(headerJson)">
              <template #icon><icon-copy /></template>
            </a-button>
          </div>
          <JsonViewer v-if="headerJson" :content="headerJson" max-height="150px" />
          <a-empty v-else description="无数据" :image-style="{ height: '40px' }" />
        </div>
        <div class="jwt-section">
          <div class="jwt-section-header">
            <a-tag color="green" size="small">Payload</a-tag>
            <a-button type="text" size="mini" @click="copyJson(payloadJson)">
              <template #icon><icon-copy /></template>
            </a-button>
          </div>
          <JsonViewer v-if="payloadJson" :content="payloadJson" max-height="300px" />
          <a-empty v-else description="无数据" :image-style="{ height: '40px' }" />
        </div>
        <div v-if="signatureInfo" class="jwt-signature">
          <a-tag :color="signatureInfo.valid ? 'green' : 'orange'" size="small">
            {{ signatureInfo.label }}
          </a-tag>
        </div>
      </div>
    </template>
    <template #actions>
      <a-button @click="clear">清空</a-button>
      <a-button type="primary" @click="decode">解析</a-button>
    </template>
  </ToolLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Message } from '@arco-design/web-vue'
import ToolLayout from './ToolLayout.vue'
import JsonViewer from '@/components/JsonViewer.vue'

const input = ref('')
const headerJson = ref<any>(null)
const payloadJson = ref<any>(null)
const signatureInfo = ref<{ valid: boolean; label: string } | null>(null)

function base64UrlDecode(str: string): string {
  let base64 = str.replace(/-/g, '+').replace(/_/g, '/')
  const pad = base64.length % 4
  if (pad) base64 += '='.repeat(4 - pad)
  return decodeURIComponent(escape(atob(base64)))
}

function decode() {
  if (!input.value.trim()) {
    Message.warning('请输入JWT Token')
    return
  }

  const parts = input.value.trim().split('.')
  if (parts.length < 2 || parts.length > 3) {
    Message.error('无效的JWT格式，应包含2或3个部分')
    return
  }

  try {
    headerJson.value = JSON.parse(base64UrlDecode(parts[0]))
  } catch {
    Message.error('Header解析失败')
    return
  }

  try {
    const payload = JSON.parse(base64UrlDecode(parts[1]))
    const friendly: any = {}
    for (const [key, value] of Object.entries(payload)) {
      if (typeof value === 'number' && (key === 'exp' || key === 'iat' || key === 'nbf')) {
        friendly[key] = `${value} (${new Date(value * 1000).toLocaleString()})`
      } else {
        friendly[key] = value
      }
    }
    payloadJson.value = friendly
  } catch {
    Message.error('Payload解析失败')
    return
  }

  if (parts.length === 3 && parts[2]) {
    signatureInfo.value = { valid: false, label: '签名未验证（仅解码）' }
  } else {
    signatureInfo.value = null
  }

  Message.success('解析完成')
}

function copyJson(obj: any) {
  if (!obj) return
  const text = JSON.stringify(obj, null, 2)
  if (navigator.clipboard?.writeText) {
    navigator.clipboard.writeText(text).then(() => Message.success('已复制'))
  } else {
    const ta = document.createElement('textarea')
    ta.value = text
    ta.style.cssText = 'position:fixed;left:-9999px'
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
    Message.success('已复制')
  }
}

function clear() {
  input.value = ''
  headerJson.value = null
  payloadJson.value = null
  signatureInfo.value = null
}
</script>

<style scoped>
.jwt-output {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.jwt-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.jwt-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.jwt-signature {
  display: flex;
  align-items: center;
}
</style>

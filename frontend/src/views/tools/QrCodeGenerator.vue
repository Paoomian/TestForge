<template>
  <ToolLayout title="二维码生成" description="将文本或URL转换为二维码图片">
    <template #input>
      <a-textarea
        v-model="input"
        placeholder="输入文本或URL"
        :style="{ height: '100%' }"
      />
    </template>
    <template #output>
      <div class="qrcode-output">
        <div v-if="qrDataUrl" class="qrcode-preview">
          <img :src="qrDataUrl" alt="二维码" class="qrcode-img" />
        </div>
        <a-empty v-else description="点击生成查看二维码" />
      </div>
    </template>
    <template #actions>
      <a-button @click="clear">清空</a-button>
      <a-button type="outline" :disabled="!qrDataUrl" @click="download">下载PNG</a-button>
      <a-button type="primary" @click="generate">生成</a-button>
    </template>
  </ToolLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Message } from '@arco-design/web-vue'
import QRCode from 'qrcode'
import ToolLayout from './ToolLayout.vue'

const input = ref('')
const qrDataUrl = ref('')

async function generate() {
  if (!input.value.trim()) {
    Message.warning('请输入内容')
    return
  }
  try {
    qrDataUrl.value = await QRCode.toDataURL(input.value, {
      width: 300,
      margin: 2,
      color: { dark: '#000000', light: '#ffffff' }
    })
  } catch (e: any) {
    Message.error('生成失败: ' + e.message)
  }
}

function download() {
  if (!qrDataUrl.value) return
  const link = document.createElement('a')
  link.download = 'qrcode.png'
  link.href = qrDataUrl.value
  link.click()
}

function clear() {
  input.value = ''
  qrDataUrl.value = ''
}
</script>

<style scoped>
.qrcode-output {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.qrcode-preview {
  padding: 16px;
  background: white;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
}

.qrcode-img {
  display: block;
  max-width: 300px;
}
</style>

<template>
  <ToolLayout title="哈希计算" description="计算文本的MD5、SHA1、SHA256哈希值">
    <template #input>
      <a-textarea
        v-model="input"
        placeholder="输入要计算哈希的文本"
        :style="{ height: '100%' }"
      />
    </template>
    <template #output>
      <div class="hash-results">
        <div class="hash-item">
          <div class="hash-label">MD5</div>
          <a-input :model-value="md5" readonly>
            <template #append>
              <a-button type="text" size="mini" @click="copy(md5)">
                <template #icon><icon-copy /></template>
              </a-button>
            </template>
          </a-input>
        </div>
        <div class="hash-item">
          <div class="hash-label">SHA1</div>
          <a-input :model-value="sha1" readonly>
            <template #append>
              <a-button type="text" size="mini" @click="copy(sha1)">
                <template #icon><icon-copy /></template>
              </a-button>
            </template>
          </a-input>
        </div>
        <div class="hash-item">
          <div class="hash-label">SHA256</div>
          <a-input :model-value="sha256" readonly>
            <template #append>
              <a-button type="text" size="mini" @click="copy(sha256)">
                <template #icon><icon-copy /></template>
              </a-button>
            </template>
          </a-input>
        </div>
      </div>
    </template>
    <template #actions>
      <a-button @click="clear">清空</a-button>
      <a-button type="primary" @click="calculate">计算</a-button>
    </template>
  </ToolLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Message } from '@arco-design/web-vue'
import CryptoJS from 'crypto-js'
import ToolLayout from './ToolLayout.vue'

const input = ref('')
const md5 = ref('')
const sha1 = ref('')
const sha256 = ref('')

function calculate() {
  if (!input.value) {
    Message.warning('请输入内容')
    return
  }
  md5.value = CryptoJS.MD5(input.value).toString()
  sha1.value = CryptoJS.SHA1(input.value).toString()
  sha256.value = CryptoJS.SHA256(input.value).toString()
  Message.success('计算完成')
}

function copy(text: string) {
  if (!text) return
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
  md5.value = ''
  sha1.value = ''
  sha256.value = ''
}
</script>

<style scoped>
.hash-results {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hash-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.hash-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-2);
}
</style>

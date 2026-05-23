<template>
  <ToolLayout title="AES/DES加解密" description="对称加密与解密工具">
    <template #input>
      <div class="aes-input-area">
        <a-textarea
          v-model="input"
          placeholder="输入要加密或解密的文本"
          :style="{ height: '100%' }"
        />
        <div class="aes-config">
          <a-input v-model="secretKey" placeholder="密钥" style="width: 200px" />
          <a-select v-model="mode" style="width: 100px">
            <a-option value="AES">AES</a-option>
            <a-option value="DES">DES</a-option>
          </a-select>
          <a-select v-model="outputFormat" style="width: 100px">
            <a-option value="Base64">Base64</a-option>
            <a-option value="Hex">Hex</a-option>
          </a-select>
        </div>
      </div>
    </template>
    <template #output>
      <a-textarea
        v-model="output"
        placeholder="结果"
        :style="{ height: '100%' }"
        readonly
      />
    </template>
    <template #actions>
      <a-button @click="clear">清空</a-button>
      <a-button type="outline" @click="decrypt">解密</a-button>
      <a-button type="primary" @click="encrypt">加密</a-button>
    </template>
  </ToolLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Message } from '@arco-design/web-vue'
import CryptoJS from 'crypto-js'
import ToolLayout from './ToolLayout.vue'

const input = ref('')
const output = ref('')
const secretKey = ref('')
const mode = ref('AES')
const outputFormat = ref('Base64')

function encrypt() {
  if (!input.value) {
    Message.warning('请输入内容')
    return
  }
  if (!secretKey.value) {
    Message.warning('请输入密钥')
    return
  }

  try {
    const cipher = mode.value === 'AES'
      ? CryptoJS.AES.encrypt(input.value, secretKey.value)
      : CryptoJS.DES.encrypt(input.value, secretKey.value)

    output.value = outputFormat.value === 'Base64'
      ? cipher.toString()
      : cipher.ciphertext.toString(CryptoJS.enc.Hex)
  } catch (e: any) {
    Message.error('加密失败: ' + e.message)
  }
}

function decrypt() {
  if (!input.value) {
    Message.warning('请输入内容')
    return
  }
  if (!secretKey.value) {
    Message.warning('请输入密钥')
    return
  }

  try {
    let decrypted
    if (mode.value === 'AES') {
      decrypted = CryptoJS.AES.decrypt(input.value, secretKey.value)
    } else {
      decrypted = CryptoJS.DES.decrypt(input.value, secretKey.value)
    }

    const result = decrypted.toString(CryptoJS.enc.Utf8)
    if (!result) {
      Message.error('解密失败，请检查密钥或密文格式')
      return
    }
    output.value = result
  } catch (e: any) {
    Message.error('解密失败: ' + e.message)
  }
}

function clear() {
  input.value = ''
  output.value = ''
}
</script>

<style scoped>
.aes-input-area {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
}

.aes-config {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>

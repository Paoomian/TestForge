<template>
  <ToolLayout title="Unicode编解码" description="中文与Unicode互相转换">
    <template #input>
      <a-textarea
        v-model="input"
        placeholder="输入中文或Unicode（如 \\u4f60\\u597d）"
        :style="{ height: '100%' }"
      />
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
      <a-button type="outline" @click="decode">Unicode→中文</a-button>
      <a-button type="primary" @click="encode">中文→Unicode</a-button>
    </template>
  </ToolLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Message } from '@arco-design/web-vue'
import ToolLayout from './ToolLayout.vue'

const input = ref('')
const output = ref('')

function encode() {
  if (!input.value) {
    Message.warning('请输入内容')
    return
  }
  output.value = Array.from(input.value)
    .map(c => '\\u' + c.charCodeAt(0).toString(16).padStart(4, '0'))
    .join('')
}

function decode() {
  if (!input.value) {
    Message.warning('请输入内容')
    return
  }
  try {
    output.value = input.value.replace(/\\u[\da-fA-F]{4}/g, match =>
      String.fromCharCode(parseInt(match.substring(2), 16))
    )
  } catch (e: any) {
    Message.error('解码失败: ' + e.message)
  }
}

function clear() {
  input.value = ''
  output.value = ''
}
</script>

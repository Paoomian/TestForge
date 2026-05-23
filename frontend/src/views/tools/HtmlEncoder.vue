<template>
  <ToolLayout title="HTML编解码" description="HTML实体编码与解码">
    <template #input>
      <a-textarea
        v-model="input"
        placeholder="输入要编码或解码的HTML内容"
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
      <a-button type="outline" @click="decode">解码</a-button>
      <a-button type="primary" @click="encode">编码</a-button>
    </template>
  </ToolLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Message } from '@arco-design/web-vue'
import ToolLayout from './ToolLayout.vue'

const input = ref('')
const output = ref('')

const encodeMap: Record<string, string> = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;',
}

const decodeMap: Record<string, string> = {
  '&amp;': '&',
  '&lt;': '<',
  '&gt;': '>',
  '&quot;': '"',
  '&#39;': "'",
}

function encode() {
  if (!input.value) {
    Message.warning('请输入内容')
    return
  }
  output.value = input.value.replace(/[&<>"']/g, c => encodeMap[c])
}

function decode() {
  if (!input.value) {
    Message.warning('请输入内容')
    return
  }
  output.value = input.value.replace(/&amp;|&lt;|&gt;|&quot;|&#39;/g, c => decodeMap[c])
}

function clear() {
  input.value = ''
  output.value = ''
}
</script>

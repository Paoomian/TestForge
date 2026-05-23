<template>
  <ToolLayout title="URL编解码" description="URL编码与解码转换">
    <template #input>
      <a-textarea
        v-model="input"
        placeholder="输入要编码或解码的URL"
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

function encode() {
  if (!input.value) {
    Message.warning('请输入内容')
    return
  }
  output.value = encodeURIComponent(input.value)
}

function decode() {
  if (!input.value) {
    Message.warning('请输入内容')
    return
  }
  try {
    output.value = decodeURIComponent(input.value)
  } catch (e: any) {
    Message.error('解码失败，请确认输入的是有效URL编码')
  }
}

function clear() {
  input.value = ''
  output.value = ''
}
</script>

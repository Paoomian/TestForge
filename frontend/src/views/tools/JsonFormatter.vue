<template>
  <ToolLayout title="JSON格式化" description="粘贴JSON字符串，自动格式化高亮输出">
    <template #input>
      <div class="editor-wrapper">
        <JsonEditor v-model="input" language="json" height="100%" />
      </div>
    </template>
    <template #output>
      <div class="output-wrapper">
        <JsonViewer v-if="output" :content="output" max-height="100%" />
        <a-empty v-else description="点击格式化查看结果" />
      </div>
    </template>
    <template #actions>
      <a-button @click="clear">清空</a-button>
      <a-button type="outline" @click="compress">压缩</a-button>
      <a-button type="primary" @click="format">格式化</a-button>
    </template>
  </ToolLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Message } from '@arco-design/web-vue'
import ToolLayout from './ToolLayout.vue'
import JsonEditor from '@/components/JsonEditor.vue'
import JsonViewer from '@/components/JsonViewer.vue'

const input = ref('')
const output = ref<any>(null)

function format() {
  if (!input.value.trim()) {
    Message.warning('请输入JSON内容')
    return
  }
  try {
    output.value = JSON.parse(input.value)
  } catch (e: any) {
    Message.error(`JSON解析错误: ${e.message}`)
  }
}

function compress() {
  if (!input.value.trim()) {
    Message.warning('请输入JSON内容')
    return
  }
  try {
    output.value = JSON.stringify(JSON.parse(input.value))
  } catch (e: any) {
    Message.error(`JSON解析错误: ${e.message}`)
  }
}

function clear() {
  input.value = ''
  output.value = null
}
</script>

<style scoped>
.editor-wrapper,
.output-wrapper {
  flex: 1;
  min-height: 0;
}
</style>

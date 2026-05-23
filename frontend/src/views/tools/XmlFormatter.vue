<template>
  <ToolLayout title="XML格式化" description="粘贴XML字符串，格式化并高亮输出">
    <template #input>
      <div class="editor-wrapper">
        <JsonEditor v-model="input" language="xml" height="100%" />
      </div>
    </template>
    <template #output>
      <div class="output-wrapper">
        <pre v-if="output" class="code-output"><code>{{ output }}</code></pre>
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

const input = ref('')
const output = ref('')

function formatXml(xml: string, indent: string = '  '): string {
  let formatted = ''
  let level = 0
  const parts = xml.replace(/>\s*</g, '><').split(/(<[^>]+>)/)

  for (const part of parts) {
    if (!part.trim()) continue
    if (part.startsWith('</')) {
      level--
      formatted += indent.repeat(Math.max(level, 0)) + part + '\n'
    } else if (part.startsWith('<?') || part.startsWith('<!')) {
      formatted += part + '\n'
    } else if (part.endsWith('/>')) {
      formatted += indent.repeat(level) + part + '\n'
    } else if (part.startsWith('<')) {
      formatted += indent.repeat(level) + part + '\n'
      level++
    } else {
      formatted += indent.repeat(level) + part.trim() + '\n'
    }
  }
  return formatted.trim()
}

function format() {
  if (!input.value.trim()) {
    Message.warning('请输入XML内容')
    return
  }
  try {
    output.value = formatXml(input.value)
  } catch (e: any) {
    Message.error(`XML格式化错误: ${e.message}`)
  }
}

function compress() {
  if (!input.value.trim()) {
    Message.warning('请输入XML内容')
    return
  }
  output.value = input.value.replace(/>\s+</g, '><').replace(/\n\s*/g, '').trim()
}

function clear() {
  input.value = ''
  output.value = ''
}
</script>

<style scoped>
.editor-wrapper,
.output-wrapper {
  flex: 1;
  min-height: 0;
}

.code-output {
  margin: 0;
  padding: 16px;
  background: #1e1e1e;
  border-radius: 8px;
  color: #d4d4d4;
  font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.6;
  overflow: auto;
  flex: 1;
  min-height: 0;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>

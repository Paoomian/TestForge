<template>
  <ToolLayout title="YAML格式化" description="粘贴YAML字符串，格式化输出">
    <template #input>
      <div class="editor-wrapper">
        <JsonEditor v-model="input" language="yaml" height="100%" />
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
      <a-button type="outline" @click="toJson">转JSON</a-button>
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

function formatYaml(yaml: string): string {
  const lines = yaml.split('\n')
  const result: string[] = []
  for (const line of lines) {
    const trimmed = line.trimEnd()
    if (trimmed === '') {
      result.push('')
    } else {
      result.push(trimmed)
    }
  }
  return result.join('\n').replace(/\n{3,}/g, '\n\n')
}

function format() {
  if (!input.value.trim()) {
    Message.warning('请输入YAML内容')
    return
  }
  output.value = formatYaml(input.value)
  Message.success('格式化完成')
}

function parseSimpleYaml(yaml: string): any {
  const lines = yaml.split('\n').filter(l => l.trim() && !l.trim().startsWith('#'))
  const root: any = {}
  const stack: any[] = [root]

  for (const line of lines) {
    const indent = line.search(/\S/)
    const level = Math.floor(indent / 2)
    const trimmed = line.trim()

    while (stack.length > level + 1) stack.pop()

    const colonIdx = trimmed.indexOf(':')
    if (colonIdx > 0) {
      const key = trimmed.substring(0, colonIdx).trim()
      const val = trimmed.substring(colonIdx + 1).trim()
      const current = stack[stack.length - 1]

      if (val === '' || val === '|' || val === '>') {
        current[key] = {}
        stack.push(current[key])
      } else if (val === '[]') {
        current[key] = []
      } else if (val === '{}') {
        current[key] = {}
      } else if (val === 'true') {
        current[key] = true
      } else if (val === 'false') {
        current[key] = false
      } else if (val === 'null') {
        current[key] = null
      } else if (/^-?\d+$/.test(val)) {
        current[key] = parseInt(val)
      } else if (/^-?\d+\.\d+$/.test(val)) {
        current[key] = parseFloat(val)
      } else {
        current[key] = val.replace(/^["']|["']$/g, '')
      }
    } else if (trimmed.startsWith('- ')) {
      const current = stack[stack.length - 1]
      const lastKey = Object.keys(current).pop()
      if (lastKey && !Array.isArray(current[lastKey])) {
        current[lastKey] = []
      }
      if (lastKey) {
        current[lastKey].push(trimmed.substring(2).trim())
      }
    }
  }

  return root
}

function toJson() {
  if (!input.value.trim()) {
    Message.warning('请输入YAML内容')
    return
  }
  try {
    const obj = parseSimpleYaml(input.value)
    output.value = JSON.stringify(obj, null, 2)
    Message.success('转换完成')
  } catch (e: any) {
    Message.error(`YAML解析错误: ${e.message}`)
  }
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

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

/**
 * 预处理 JSON 字符串，修复常见格式问题
 * - Infinity / -Infinity / NaN → null
 * - 修复字符串中的未转义引号和反斜杠
 */
function preprocessJson(str: string): string {
  // 1. 替换 Infinity 和 NaN 为 null
  let result = str
    .replace(/\bInfinity\b/g, 'null')
    .replace(/-Infinity\b/g, 'null')
    .replace(/\bNaN\b/g, 'null')

  // 2. 尝试直接解析，如果成功则直接返回
  try {
    JSON.parse(result)
    return result
  } catch {
    // 解析失败，尝试修复
  }

  // 3. 逐字符状态机修复字符串中的特殊字符
  const fixed: string[] = []
  let inString = false
  let i = 0

  while (i < result.length) {
    const ch = result[i]

    if (ch === '"') {
      if (!inString) {
        // 进入字符串
        inString = true
        fixed.push(ch)
        i++
        continue
      }

      // 在字符串内遇到引号，判断是否真正结束
      const next = result[i + 1]
      if (next === ',' || next === '}' || next === ']' || next === ':' ||
          next === ' ' || next === '\n' || next === '\r' || next === '\t' ||
          next === undefined) {
        // 真正结束字符串
        inString = false
        fixed.push(ch)
      } else {
        // 字符串内的未转义引号，转义它
        fixed.push('\\"')
      }
      i++
      continue
    }

    // 字符串内的反斜杠处理
    if (ch === '\\' && inString) {
      const next = result[i + 1]
      // 检查是否是有效的转义字符
      const validEscapes = ['"', '\\', '/', 'b', 'f', 'n', 'r', 't', 'u']
      if (next && validEscapes.includes(next)) {
        // 有效转义，保留原样
        fixed.push(ch)
        fixed.push(next)
        i += 2
      } else {
        // 无效转义，将反斜杠转义为 \\
        fixed.push('\\\\')
        i++
      }
      continue
    }

    fixed.push(ch)
    i++
  }

  return fixed.join('')
}

function format() {
  if (!input.value.trim()) {
    Message.warning('请输入JSON内容')
    return
  }
  try {
    output.value = JSON.parse(preprocessJson(input.value))
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
    output.value = JSON.stringify(JSON.parse(preprocessJson(input.value)))
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

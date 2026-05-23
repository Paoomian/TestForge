<template>
  <div class="json-viewer" :style="{ maxHeight }">
    <div v-if="showCopy && hasContent" class="jv-toolbar">
      <a-button type="text" size="mini" @click="handleCopy">
        <template #icon><icon-copy /></template>
        复制
      </a-button>
    </div>
    <pre v-if="html" class="jv-pre" v-html="html" />
    <div v-else class="jv-empty">暂无数据</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Message } from '@arco-design/web-vue'

const props = withDefaults(defineProps<{
  content: any
  maxHeight?: string
  showCopy?: boolean
}>(), {
  maxHeight: '400px',
  showCopy: true
})

const hasContent = computed(() => props.content != null && props.content !== '')

const html = computed(() => {
  const c = props.content
  if (c == null || c === '') return ''

  // 对象直接格式化
  if (typeof c === 'object') {
    try { return colorize(JSON.stringify(c, null, 2)) } catch { return '' }
  }

  const raw = String(c).trim()
  if (!raw) return ''

  // 清理控制字符
  const cleaned = raw.replace(/[\x00-\x08\x0b\x0c\x0e-\x1f]/g, '')

  // 优先 JSON.parse 格式化
  try {
    return colorize(JSON.stringify(JSON.parse(cleaned), null, 2))
  } catch {
    // JSON.parse 失败，用正则做基本格式化
    return colorize(fallbackFormat(cleaned))
  }
})

/** JSON.parse 失败时的兜底格式化：正则加缩进换行 */
function fallbackFormat(json: string): string {
  let result = ''
  let indent = 0
  let inString = false
  let escape = false

  for (let i = 0; i < json.length; i++) {
    const ch = json[i]

    if (escape) {
      result += ch
      escape = false
      continue
    }

    if (inString) {
      if (ch === '\\') {
        escape = true
        result += ch
        continue
      }
      if (ch === '"') {
        inString = false
        result += ch
        continue
      }
      result += ch
      continue
    }

    // 不在字符串内
    if (ch === '"') {
      inString = true
      result += ch
      continue
    }

    if (ch === '{' || ch === '[') {
      result += ch
      indent++
      result += '\n' + '  '.repeat(indent)
      continue
    }

    if (ch === '}' || ch === ']') {
      indent--
      result += '\n' + '  '.repeat(indent) + ch
      continue
    }

    if (ch === ',') {
      result += ch + '\n' + '  '.repeat(indent)
      continue
    }

    if (ch === ':') {
      result += ch + ' '
      continue
    }

    if (ch === ' ' || ch === '\n' || ch === '\r' || ch === '\t') {
      // 跳过原有空白（我们会自己加缩进）
      continue
    }

    result += ch
  }

  return result
}

function esc(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

function colorize(json: string): string {
  return json.replace(
    /("(\\u[\da-fA-F]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)/g,
    (match) => {
      let cls = 'jv-num'
      if (/^"/.test(match)) {
        cls = /:$/.test(match) ? 'jv-key' : 'jv-str'
      } else if (/true|false/.test(match)) {
        cls = 'jv-bool'
      } else if (/null/.test(match)) {
        cls = 'jv-null'
      }
      return `<span class="${cls}">${esc(match)}</span>`
    }
  )
}

function handleCopy() {
  const c = props.content
  if (!c) return
  const text = typeof c === 'string' ? c : JSON.stringify(c, null, 2)
  // navigator.clipboard 需要 HTTPS/localhost，局域网 IP 下用 fallback
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
</script>

<style>
.json-viewer {
  position: relative;
  background: #1e1e1e;
  border-radius: 8px;
  overflow: auto;
  height: 100%;
}
.jv-toolbar {
  position: sticky;
  top: 0;
  z-index: 1;
  display: flex;
  justify-content: flex-end;
  padding: 4px 8px;
  background: #2d2d2d;
  border-bottom: 1px solid #404040;
}
.jv-pre {
  margin: 0;
  padding: 16px;
  font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #d4d4d4;
  white-space: pre-wrap;
  word-break: break-all;
}
.jv-empty {
  padding: 24px;
  text-align: center;
  color: #6b7280;
}
.jv-key { color: #9cdcfe; }
.jv-str { color: #ce9178; }
.jv-num { color: #b5cea8; }
.jv-bool { color: #569cd6; }
.jv-null { color: #569cd6; }
</style>

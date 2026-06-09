<template>
  <div class="json-editor" :style="{ height: height }">
    <div class="editor-toolbar">
      <a-button size="mini" type="text" @click="formatCode">
        <template #icon><icon-code /></template>
        格式化
      </a-button>
    </div>
    <div ref="editorContainer" class="editor-container"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import * as monaco from 'monaco-editor'
import editorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker'
import jsonWorker from 'monaco-editor/esm/vs/language/json/json.worker?worker'
import tsWorker from 'monaco-editor/esm/vs/language/typescript/ts.worker?worker'

// 配置 Monaco Editor Worker
self.MonacoEnvironment = {
  getWorker(_: any, label: string) {
    if (label === 'json') {
      return new jsonWorker()
    }
    if (label === 'typescript' || label === 'javascript') {
      return new tsWorker()
    }
    return new editorWorker()
  }
}

interface Props {
  modelValue: string
  language?: string
  height?: string
  readonly?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  language: 'json',
  height: '300px',
  readonly: false
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const editorContainer = ref<HTMLDivElement>()
let editor: monaco.editor.IStandaloneCodeEditor | null = null

onMounted(() => {
  if (!editorContainer.value) return

  editor = monaco.editor.create(editorContainer.value, {
    value: props.modelValue,
    language: props.language,
    theme: 'vs-dark',
    automaticLayout: true,
    minimap: { enabled: false },
    readOnly: props.readonly,
    fontSize: 14,
    lineNumbers: 'on',
    scrollBeyondLastLine: false,
    wordWrap: 'on'
  })

  editor.onDidChangeModelContent(() => {
    if (editor) {
      emit('update:modelValue', editor.getValue())
    }
  })
})

watch(() => props.modelValue, (newValue) => {
  if (editor && editor.getValue() !== newValue) {
    editor.setValue(newValue)
  }
})

watch(() => props.readonly, (newValue) => {
  if (editor) {
    editor.updateOptions({ readOnly: newValue })
  }
})

onBeforeUnmount(() => {
  if (editor) {
    editor.dispose()
  }
})

// 格式化代码
function formatCode() {
  if (!editor) return
  const value = editor.getValue()
  if (props.language === 'json') {
    try {
      // 处理包含 {{变量}} 的 JSON
      const varMap = new Map<string, string>()
      let processed = value
      let counter = 0

      // 将 {{xxx}} 替换为占位符
      processed = processed.replace(/\{\{[^}]+\}\}/g, (match) => {
        const placeholder = `"__VAR_${counter++}__"`
        varMap.set(placeholder, match)
        return placeholder
      })

      // 格式化 JSON
      const formatted = JSON.stringify(JSON.parse(processed), null, 2)

      // 将占位符替换回变量
      let result = formatted
      varMap.forEach((varExpr, placeholder) => {
        // 占位符带引号，需要去掉引号
        result = result.replace(`"${placeholder.replace(/"/g, '')}"`, varExpr)
        // 也处理不带引号的情况（理论上不应该出现）
        result = result.replace(placeholder.replace(/"/g, ''), varExpr)
      })

      editor.setValue(result)
    } catch (e) {
      // JSON 解析失败，不处理
    }
  } else {
    // 使用 Monaco 内置格式化
    editor.getAction('editor.action.formatDocument')?.run()
  }
}
</script>

<style scoped>
.json-editor {
  border: 1px solid var(--color-border);
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.editor-toolbar {
  display: flex;
  justify-content: flex-end;
  padding: 4px 8px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-fill-2);
}

.editor-container {
  flex: 1;
  min-height: 0;
  width: 100%;
}
</style>

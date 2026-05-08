import type * as Monaco from 'monaco-editor'

/**
 * 为Monaco编辑器注册自定义变量提示
 * 在URL、Body等字段中输入 ${ 时自动提示可用变量
 */

const COMMON_VARIABLES = [
  { label: '${timestamp}', detail: '当前时间戳（毫秒）', insertText: '${timestamp}' },
  { label: '${timestamp_sec}', detail: '当前时间戳（秒）', insertText: '${timestamp_sec}' },
  { label: '${random_int}', detail: '随机整数', insertText: '${random_int}' },
  { label: '${random_uuid}', detail: '随机UUID', insertText: '${random_uuid}' },
  { label: '${date}', detail: '当前日期 YYYY-MM-DD', insertText: '${date}' },
  { label: '${datetime}', detail: '当前日期时间', insertText: '${datetime}' },
]

export function registerVariableCompletion(monaco: typeof Monaco, variables: string[] = []) {
  const allVars = [
    ...COMMON_VARIABLES,
    ...variables.map(v => ({
      label: `\${${v}}`,
      detail: `自定义变量: ${v}`,
      insertText: `\${${v}}`,
    })),
  ]

  return monaco.languages.registerCompletionItemProvider('plaintext', {
    triggerCharacters: ['$', '{'],
    provideCompletionItems(model, position) {
      const line = model.getLineContent(position.lineNumber)
      const textBefore = line.substring(0, position.column - 1)

      if (!textBefore.endsWith('${') && !textBefore.endsWith('$')) {
        return { suggestions: [] }
      }

      const range = {
        startLineNumber: position.lineNumber,
        startColumn: position.column - 2,
        endLineNumber: position.lineNumber,
        endColumn: position.column,
      }

      return {
        suggestions: allVars.map(v => ({
          label: v.label,
          kind: monaco.languages.CompletionItemKind.Variable,
          detail: v.detail,
          insertText: v.insertText.substring(2), // 去掉 ${
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.None,
          range,
        })),
      }
    },
  })
}

/**
 * 为JSON编辑器注册变量提示
 */
export function registerJsonVariableCompletion(monaco: typeof Monaco, variables: string[] = []) {
  const allVars = [
    ...COMMON_VARIABLES,
    ...variables.map(v => ({
      label: `\${${v}}`,
      detail: `自定义变量: ${v}`,
      insertText: `\${${v}}`,
    })),
  ]

  return monaco.languages.registerCompletionItemProvider('json', {
    triggerCharacters: ['$', '{'],
    provideCompletionItems(model, position) {
      const line = model.getLineContent(position.lineNumber)
      const textBefore = line.substring(0, position.column - 1)

      if (!textBefore.endsWith('${') && !textBefore.endsWith('$')) {
        return { suggestions: [] }
      }

      const range = {
        startLineNumber: position.lineNumber,
        startColumn: position.column - 2,
        endLineNumber: position.lineNumber,
        endColumn: position.column,
      }

      return {
        suggestions: allVars.map(v => ({
          label: v.label,
          kind: monaco.languages.CompletionItemKind.Variable,
          detail: v.detail,
          insertText: v.insertText.substring(2),
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.None,
          range,
        })),
      }
    },
  })
}

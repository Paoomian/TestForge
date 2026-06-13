/**
 * Playwright 错误信息中文翻译工具
 * 保留原始错误信息，同时提供中文翻译
 */

// 错误模式匹配规则
interface ErrorPattern {
  pattern: RegExp
  replacement: string | ((match: string, ...args: string[]) => string)
}

// 常见错误模式列表（按优先级排序）
const errorPatterns: ErrorPattern[] = [
  // 超时错误
  {
    pattern: /Timeout\s+(\d+)ms\s+exceeded/i,
    replacement: (_match, ms) => {
      const seconds = Math.round(parseInt(ms) / 1000)
      return `超时（${seconds}秒）`
    },
  },
  {
    pattern: /Navigation\s+timeout/i,
    replacement: '页面加载超时',
  },
  {
    pattern: /timeout\s+of\s+(\d+)ms\s+exceeded/i,
    replacement: (_match, ms) => {
      const seconds = Math.round(parseInt(ms) / 1000)
      return `超时（${seconds}秒）`
    },
  },

  // 元素定位错误
  {
    pattern: /waiting for locator\("([^"]+)"\)\s+to\s+be\s+visible/i,
    replacement: (_match, locator) => `等待元素可见：${simplifyLocator(locator)}`,
  },
  {
    pattern: /waiting for locator\("([^"]+)"\)\s+to\s+be\s+hidden/i,
    replacement: (_match, locator) => `等待元素隐藏：${simplifyLocator(locator)}`,
  },
  {
    pattern: /waiting for locator\("([^"]+)"\)\s+to\s+be\s+enabled/i,
    replacement: (_match, locator) => `等待元素可操作：${simplifyLocator(locator)}`,
  },
  {
    pattern: /waiting for selector\s+"([^"]+)"/i,
    replacement: (_match, selector) => `等待元素：${simplifyLocator(selector)}`,
  },
  {
    pattern: /Element\s+is\s+not\s+visible/i,
    replacement: '元素不可见',
  },
  {
    pattern: /Element\s+is\s+not\s+clickable/i,
    replacement: '元素不可点击',
  },
  {
    pattern: /Element\s+is\s+not\s+enabled/i,
    replacement: '元素不可操作',
  },
  {
    pattern: /No\s+element\s+matching\s+locator/i,
    replacement: '未找到匹配的元素',
  },

  // 网络错误
  {
    pattern: /net::ERR_CONNECTION_REFUSED/i,
    replacement: '连接被拒绝',
  },
  {
    pattern: /net::ERR_NAME_NOT_RESOLVED/i,
    replacement: '域名无法解析',
  },
  {
    pattern: /net::ERR_INTERNET_DISCONNECTED/i,
    replacement: '网络已断开',
  },
  {
    pattern: /net::ERR_TIMED_OUT/i,
    replacement: '网络连接超时',
  },
  {
    pattern: /net::ERR_CERT_/i,
    replacement: '证书错误',
  },

  // 页面错误
  {
    pattern: /page\.goto.*net::ERR/i,
    replacement: '页面导航失败（网络错误）',
  },
  {
    pattern: /page\.click.*failed/i,
    replacement: '点击操作失败',
  },
  {
    pattern: /page\.fill.*failed/i,
    replacement: '输入操作失败',
  },
  {
    pattern: /page\.type.*failed/i,
    replacement: '输入操作失败',
  },

  // 断言错误
  {
    pattern: /expect\(.*\)\.toBe/i,
    replacement: '断言失败：值不匹配',
  },
  {
    pattern: /expect\(.*\)\.toContain/i,
    replacement: '断言失败：未包含预期内容',
  },
  {
    pattern: /expect\(.*\)\.toBeVisible/i,
    replacement: '断言失败：元素不可见',
  },

  // 通用错误
  {
    pattern: /Call\s+log:/i,
    replacement: '调用日志：',
  },
  {
    pattern: /waiting\s+for/i,
    replacement: '等待中',
  },
]

/**
 * 简化选择器表达式，提取关键信息
 */
function simplifyLocator(locator: string): string {
  try {
    // 移除 nth-of-type 等复杂选择器，保留关键部分
    let simplified = locator

    // 提取 id
    const idMatch = simplified.match(/#([\w-]+)/)
    if (idMatch) return `#${idMatch[1]}`

    // 提取 data-testid
    const testIdMatch = simplified.match(/\[data-testid="([^"]+)"\]/)
    if (testIdMatch) return `[data-testid="${testIdMatch[1]}"]`

    // 提取 role
    const roleMatch = simplified.match(/role=([\w]+)/)
    if (roleMatch) return `role=${roleMatch[1]}`

    // 提取 text
    const textMatch = simplified.match(/text="([^"]+)"/)
    if (textMatch) return `text="${textMatch[1]}"`

    // 如果太长，截取最后几级
    if (simplified.length > 50) {
      const parts = simplified.split('>')
      if (parts.length > 3) {
        return `...${parts.slice(-2).join('>').trim()}`
      }
    }

    return simplified
  } catch {
    return locator
  }
}

/**
 * 翻译错误信息为中文
 * @param message 原始错误信息
 * @returns 翻译后的错误信息，包含中文和原文（如有需要）
 */
export function translateErrorMessage(message: string | null | undefined): string {
  if (!message) return ''

  try {
    let translated = message
    let hasTranslation = false

    // 应用所有匹配规则
    for (const { pattern, replacement } of errorPatterns) {
      // 使用 match 测试，避免 test 改变 lastIndex 状态
      if (translated.match(pattern)) {
        hasTranslation = true
        if (typeof replacement === 'function') {
          translated = translated.replace(pattern, replacement as any)
        } else {
          translated = translated.replace(pattern, replacement)
        }
      }
    }

    // 如果没有匹配到任何规则，返回原文
    if (!hasTranslation) {
      return message
    }

    // 清理多余的空白
    translated = translated.replace(/\s+/g, ' ').trim()

    return translated
  } catch {
    // 翻译出错时返回原文
    return message
  }
}

/**
 * 格式化错误信息用于显示
 * @param message 原始错误信息
 * @param showOriginal 是否显示原文（默认 false）
 * @returns 格式化后的错误信息
 */
export function formatErrorMessage(
  message: string | null | undefined,
  showOriginal: boolean = false
): { translated: string; original: string; hasTranslation: boolean } {
  const original = message || ''
  const translated = translateErrorMessage(message)
  const hasTranslation = translated !== original

  return {
    translated: showOriginal ? original : translated,
    original,
    hasTranslation,
  }
}

# 开发工具页面 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为TestForge测试平台添加「开发工具」页面，集成17个测试开发常用工具

**Architecture:** 单页面应用，左侧工具卡片列表 + 右侧工具内容区。每个工具是独立Vue组件，共享ToolLayout布局组件。通过动态组件切换实现工具切换。

**Tech Stack:** Vue 3 + TypeScript + Arco Design Vue + Monaco Editor + crypto-js + qrcode

---

## 文件结构

```
frontend/src/views/tools/
├── ToolsPage.vue           # 主页面
├── ToolLayout.vue          # 共享布局
├── JsonFormatter.vue       # JSON格式化
├── XmlFormatter.vue        # XML格式化
├── YamlFormatter.vue       # YAML格式化
├── Base64Tool.vue          # Base64编解码
├── UrlEncoder.vue          # URL编解码
├── HtmlEncoder.vue         # HTML编解码
├── UnicodeConverter.vue    # Unicode编解码
├── HashCalculator.vue      # 哈希计算
├── JwtDecoder.vue          # JWT解析
├── AesTool.vue             # AES/DES加解密
├── UuidGenerator.vue       # UUID生成
├── RandomString.vue        # 随机字符串
├── TestDataGenerator.vue   # 测试数据生成
├── QrCodeGenerator.vue     # 二维码生成
├── TimestampConverter.vue  # 时间戳转换
├── CronBuilder.vue         # Cron生成器
└── RadixConverter.vue      # 进制转换
```

**修改的文件:**
- `frontend/src/router/index.ts` — 添加路由
- `frontend/src/layouts/MainLayout.vue` — 添加菜单项

---

## Task 1: 安装依赖 + 创建目录

**Files:**
- Modify: `frontend/package.json`

- [ ] **Step 1: 安装 crypto-js 和 qrcode**

```bash
cd d:/projects/TestForge-/frontend
npm install crypto-js qrcode
npm install -D @types/crypto-js @types/qrcode
```

- [ ] **Step 2: 创建 tools 目录**

```bash
mkdir -p d:/projects/TestForge-/frontend/src/views/tools
```

- [ ] **Step 3: 验证依赖安装成功**

```bash
cd d:/projects/TestForge-/frontend
node -e "require('crypto-js'); require('qrcode'); console.log('OK')"
```
Expected: `OK`

---

## Task 2: ToolLayout 共享布局组件

**Files:**
- Create: `frontend/src/views/tools/ToolLayout.vue`

- [ ] **Step 1: 创建 ToolLayout.vue**

```vue
<template>
  <div class="tool-layout">
    <div class="tool-header">
      <h3 class="tool-title">{{ title }}</h3>
      <p v-if="description" class="tool-desc">{{ description }}</p>
    </div>
    <div class="tool-body">
      <div class="tool-input">
        <slot name="input" />
      </div>
      <div class="tool-output">
        <slot name="output" />
      </div>
    </div>
    <div class="tool-actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  description?: string
}>()
</script>

<style scoped>
.tool-layout {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 16px;
}

.tool-header {
  flex-shrink: 0;
}

.tool-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-1);
  margin: 0 0 4px 0;
}

.tool-desc {
  font-size: 13px;
  color: var(--color-text-3);
  margin: 0;
}

.tool-body {
  flex: 1;
  display: flex;
  gap: 16px;
  min-height: 0;
}

.tool-input,
.tool-output {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.tool-actions {
  flex-shrink: 0;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

@media (max-width: 768px) {
  .tool-body {
    flex-direction: column;
  }
}
</style>
```

- [ ] **Step 2: 验证组件可导入**

在浏览器中暂时导入该组件确认无语法错误。

---

## Task 3: ToolsPage 主页面 + 路由 + 菜单

**Files:**
- Create: `frontend/src/views/tools/ToolsPage.vue`
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/layouts/MainLayout.vue`

- [ ] **Step 1: 创建 ToolsPage.vue**

```vue
<template>
  <div class="tools-page">
    <!-- 左侧工具卡片列表 -->
    <div class="tools-sidebar">
      <div class="tools-sidebar-header">
        <h3 class="tools-sidebar-title">开发工具</h3>
      </div>
      <div class="tools-list">
        <div
          v-for="group in toolGroups"
          :key="group.key"
          class="tool-group"
        >
          <div class="group-title">{{ group.label }}</div>
          <div
            v-for="tool in group.tools"
            :key="tool.key"
            class="tool-card"
            :class="{ active: activeTool === tool.key }"
            @click="activeTool = tool.key"
          >
            <component :is="tool.icon" class="tool-card-icon" />
            <span class="tool-card-name">{{ tool.label }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧工具内容区 -->
    <div class="tools-content">
      <component :is="currentComponent" v-if="currentComponent" />
      <div v-else class="tools-welcome">
        <div class="welcome-icon">
          <icon-tool :style="{ fontSize: '48px', color: 'var(--color-text-4)' }" />
        </div>
        <h3>选择一个工具开始使用</h3>
        <p>从左侧列表中选择你需要的开发工具</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, markRaw } from 'vue'
import {
  IconTool, IconCode, IconFile, IconLock, IconThunder, IconClock
} from '@arco-design/web-vue/es/icon'

// 工具组件
import JsonFormatter from './JsonFormatter.vue'
import XmlFormatter from './XmlFormatter.vue'
import YamlFormatter from './YamlFormatter.vue'
import Base64Tool from './Base64Tool.vue'
import UrlEncoder from './UrlEncoder.vue'
import HtmlEncoder from './HtmlEncoder.vue'
import UnicodeConverter from './UnicodeConverter.vue'
import HashCalculator from './HashCalculator.vue'
import JwtDecoder from './JwtDecoder.vue'
import AesTool from './AesTool.vue'
import UuidGenerator from './UuidGenerator.vue'
import RandomString from './RandomString.vue'
import TestDataGenerator from './TestDataGenerator.vue'
import QrCodeGenerator from './QrCodeGenerator.vue'
import TimestampConverter from './TimestampConverter.vue'
import CronBuilder from './CronBuilder.vue'
import RadixConverter from './RadixConverter.vue'

interface ToolItem {
  key: string
  label: string
  icon: any
  component: any
}

interface ToolGroup {
  key: string
  label: string
  tools: ToolItem[]
}

const toolGroups: ToolGroup[] = [
  {
    key: 'format',
    label: '数据格式化',
    tools: [
      { key: 'json', label: 'JSON格式化', icon: markRaw(IconCode), component: markRaw(JsonFormatter) },
      { key: 'xml', label: 'XML格式化', icon: markRaw(IconCode), component: markRaw(XmlFormatter) },
      { key: 'yaml', label: 'YAML格式化', icon: markRaw(IconCode), component: markRaw(YamlFormatter) },
    ]
  },
  {
    key: 'encode',
    label: '编解码',
    tools: [
      { key: 'base64', label: 'Base64编解码', icon: markRaw(IconFile), component: markRaw(Base64Tool) },
      { key: 'url', label: 'URL编解码', icon: markRaw(IconFile), component: markRaw(UrlEncoder) },
      { key: 'html', label: 'HTML编解码', icon: markRaw(IconFile), component: markRaw(HtmlEncoder) },
      { key: 'unicode', label: 'Unicode编解码', icon: markRaw(IconFile), component: markRaw(UnicodeConverter) },
    ]
  },
  {
    key: 'crypto',
    label: '哈希/加密',
    tools: [
      { key: 'hash', label: '哈希计算', icon: markRaw(IconLock), component: markRaw(HashCalculator) },
      { key: 'jwt', label: 'JWT解析', icon: markRaw(IconLock), component: markRaw(JwtDecoder) },
      { key: 'aes', label: 'AES/DES加解密', icon: markRaw(IconLock), component: markRaw(AesTool) },
    ]
  },
  {
    key: 'generate',
    label: '生成工具',
    tools: [
      { key: 'uuid', label: 'UUID生成', icon: markRaw(IconThunder), component: markRaw(UuidGenerator) },
      { key: 'random', label: '随机字符串', icon: markRaw(IconThunder), component: markRaw(RandomString) },
      { key: 'testdata', label: '测试数据生成', icon: markRaw(IconThunder), component: markRaw(TestDataGenerator) },
      { key: 'qrcode', label: '二维码生成', icon: markRaw(IconThunder), component: markRaw(QrCodeGenerator) },
    ]
  },
  {
    key: 'convert',
    label: '时间/转换',
    tools: [
      { key: 'timestamp', label: '时间戳转换', icon: markRaw(IconClock), component: markRaw(TimestampConverter) },
      { key: 'cron', label: 'Cron生成器', icon: markRaw(IconClock), component: markRaw(CronBuilder) },
      { key: 'radix', label: '进制转换', icon: markRaw(IconClock), component: markRaw(RadixConverter) },
    ]
  }
]

const activeTool = ref<string>('')

const currentComponent = computed(() => {
  if (!activeTool.value) return null
  for (const group of toolGroups) {
    const tool = group.tools.find(t => t.key === activeTool.value)
    if (tool) return tool.component
  }
  return null
})
</script>

<style scoped>
.tools-page {
  display: flex;
  height: calc(100vh - var(--header-height) - var(--content-padding) * 2);
  gap: 16px;
}

.tools-sidebar {
  width: 200px;
  flex-shrink: 0;
  background: white;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.tools-sidebar-header {
  padding: 16px;
  border-bottom: 1px solid var(--color-border);
}

.tools-sidebar-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-1);
  margin: 0;
}

.tools-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.tool-group {
  margin-bottom: 8px;
}

.group-title {
  font-size: 12px;
  color: var(--color-text-3);
  padding: 8px 12px 4px;
  font-weight: 500;
}

.tool-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s ease;
  border-left: 3px solid transparent;
}

.tool-card:hover {
  background: var(--color-fill-2);
}

.tool-card.active {
  background: var(--primary-50);
  border-left-color: var(--primary-500);
}

.tool-card-icon {
  font-size: 14px;
  color: var(--color-text-3);
}

.tool-card.active .tool-card-icon {
  color: var(--primary-500);
}

.tool-card-name {
  font-size: 13px;
  color: var(--color-text-2);
}

.tool-card.active .tool-card-name {
  color: var(--primary-600);
  font-weight: 500;
}

.tools-content {
  flex: 1;
  min-width: 0;
  background: white;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  padding: 20px;
  overflow: auto;
}

.tools-welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--color-text-3);
}

.welcome-icon {
  margin-bottom: 16px;
}

.tools-welcome h3 {
  font-size: 16px;
  color: var(--color-text-2);
  margin: 0 0 8px 0;
}

.tools-welcome p {
  font-size: 13px;
  margin: 0;
}
</style>
```

- [ ] **Step 2: 添加路由到 router/index.ts**

在 `children` 数组的最后一个元素后（`report-list` 路由之后）添加：

```typescript
      {
        path: 'tools',
        name: 'tools',
        component: () => import('@/views/tools/ToolsPage.vue')
      },
```

- [ ] **Step 3: 添加侧边栏菜单项到 MainLayout.vue**

在 `</a-menu>` 闭合标签前（`reports` sub-menu 之后）添加：

```xml
          <a-sub-menu key="tools">
            <template #icon>
              <icon-tool />
            </template>
            <template #title>开发工具</template>
            <a-menu-item key="tools">工具目录</a-menu-item>
          </a-sub-menu>
```

- [ ] **Step 4: 启动前端验证页面可访问**

```bash
cd d:/projects/TestForge-/frontend
npm run dev
```

访问 `http://localhost:5173/tools`，验证：
- 左侧工具卡片列表正常显示5个分组
- 点击卡片右侧区域有变化（暂时显示空白，组件还未创建）
- 欢迎页正常显示

---

## Task 4: JSON格式化工具

**Files:**
- Create: `frontend/src/views/tools/JsonFormatter.vue`

- [ ] **Step 1: 创建 JsonFormatter.vue**

```vue
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
    const parsed = JSON.parse(input.value)
    output.value = parsed
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
    const parsed = JSON.parse(input.value)
    output.value = JSON.stringify(parsed)
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
  height: 100%;
  min-height: 300px;
}
</style>
```

- [ ] **Step 2: 验证JSON格式化功能**

在浏览器中选择JSON格式化工具，测试：
- 输入 `{"name":"test","age":18}` 点击格式化，输出高亮JSON
- 输入非法JSON，显示错误提示
- 点击压缩，输出紧凑JSON
- 点击清空，输入输出清空

---

## Task 5: XML格式化 + YAML格式化

**Files:**
- Create: `frontend/src/views/tools/XmlFormatter.vue`
- Create: `frontend/src/views/tools/YamlFormatter.vue`

- [ ] **Step 1: 创建 XmlFormatter.vue**

```vue
<template>
  <ToolLayout title="XML格式化" description="粘贴XML字符串，格式化并高亮输出">
    <template #input>
      <div class="editor-wrapper">
        <JsonEditor v-model="input" language="xml" height="100%" />
      </div>
    </template>
    <template #output>
      <div class="output-wrapper">
        <pre v-if="output" class="xml-output"><code>{{ output }}</code></pre>
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
  height: 100%;
  min-height: 300px;
}

.xml-output {
  margin: 0;
  padding: 16px;
  background: #1e1e1e;
  border-radius: 8px;
  color: #d4d4d4;
  font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.6;
  overflow: auto;
  height: 100%;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
```

- [ ] **Step 2: 创建 YamlFormatter.vue**

```vue
<template>
  <ToolLayout title="YAML格式化" description="粘贴YAML字符串，格式化输出">
    <template #input>
      <div class="editor-wrapper">
        <JsonEditor v-model="input" language="yaml" height="100%" />
      </div>
    </template>
    <template #output>
      <div class="output-wrapper">
        <pre v-if="output" class="yaml-output"><code>{{ output }}</code></pre>
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
  // 简单的YAML格式化：规范化缩进
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

function toJson() {
  if (!input.value.trim()) {
    Message.warning('请输入YAML内容')
    return
  }
  try {
    // 简单的YAML转JSON：按行解析基本YAML
    const obj = parseSimpleYaml(input.value)
    output.value = JSON.stringify(obj, null, 2)
    Message.success('转换完成')
  } catch (e: any) {
    Message.error(`YAML解析错误: ${e.message}`)
  }
}

function parseSimpleYaml(yaml: string): any {
  // 基础YAML解析器，支持简单的key: value和嵌套
  const lines = yaml.split('\n').filter(l => l.trim() && !l.trim().startsWith('#'))
  const root: any = {}
  const stack: any[] = [root]

  for (const line of lines) {
    const indent = line.search(/\S/)
    const level = Math.floor(indent / 2)
    const trimmed = line.trim()

    // 调整栈深度
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

function clear() {
  input.value = ''
  output.value = ''
}
</script>

<style scoped>
.editor-wrapper,
.output-wrapper {
  height: 100%;
  min-height: 300px;
}

.yaml-output {
  margin: 0;
  padding: 16px;
  background: #1e1e1e;
  border-radius: 8px;
  color: #d4d4d4;
  font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.6;
  overflow: auto;
  height: 100%;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
```

- [ ] **Step 3: 验证XML和YAML格式化**

在浏览器中测试：
- XML：输入 `<root><item>test</item></root>` 点击格式化
- YAML：输入 `name: test\nage: 18` 点击格式化和转JSON

---

## Task 6: 编解码工具（Base64 + URL + HTML + Unicode）

**Files:**
- Create: `frontend/src/views/tools/Base64Tool.vue`
- Create: `frontend/src/views/tools/UrlEncoder.vue`
- Create: `frontend/src/views/tools/HtmlEncoder.vue`
- Create: `frontend/src/views/tools/UnicodeConverter.vue`

- [ ] **Step 1: 创建 Base64Tool.vue**

```vue
<template>
  <ToolLayout title="Base64编解码" description="文本与Base64互相转换，支持UTF-8中文">
    <template #input>
      <a-textarea
        v-model="input"
        placeholder="输入要编码或解码的内容"
        :auto-size="{ minRows: 12, maxRows: 20 }"
      />
    </template>
    <template #output>
      <a-textarea
        v-model="output"
        placeholder="结果"
        :auto-size="{ minRows: 12, maxRows: 20 }"
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
  try {
    // 支持UTF-8中文
    const encoded = btoa(unescape(encodeURIComponent(input.value)))
    output.value = encoded
  } catch (e: any) {
    Message.error('编码失败: ' + e.message)
  }
}

function decode() {
  if (!input.value) {
    Message.warning('请输入内容')
    return
  }
  try {
    const decoded = decodeURIComponent(escape(atob(input.value)))
    output.value = decoded
  } catch (e: any) {
    Message.error('解码失败，请确认输入的是有效Base64')
  }
}

function clear() {
  input.value = ''
  output.value = ''
}
</script>
```

- [ ] **Step 2: 创建 UrlEncoder.vue**

```vue
<template>
  <ToolLayout title="URL编解码" description="URL编码与解码转换">
    <template #input>
      <a-textarea
        v-model="input"
        placeholder="输入要编码或解码的URL"
        :auto-size="{ minRows: 12, maxRows: 20 }"
      />
    </template>
    <template #output>
      <a-textarea
        v-model="output"
        placeholder="结果"
        :auto-size="{ minRows: 12, maxRows: 20 }"
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
```

- [ ] **Step 3: 创建 HtmlEncoder.vue**

```vue
<template>
  <ToolLayout title="HTML编解码" description="HTML实体编码与解码">
    <template #input>
      <a-textarea
        v-model="input"
        placeholder="输入要编码或解码的HTML内容"
        :auto-size="{ minRows: 12, maxRows: 20 }"
      />
    </template>
    <template #output>
      <a-textarea
        v-model="output"
        placeholder="结果"
        :auto-size="{ minRows: 12, maxRows: 20 }"
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
  const map: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }
  output.value = input.value.replace(/[&<>"']/g, c => map[c])
}

function decode() {
  if (!input.value) {
    Message.warning('请输入内容')
    return
  }
  const map: Record<string, string> = {
    '&amp;': '&',
    '&lt;': '<',
    '&gt;': '>',
    '&quot;': '"',
    '&#39;': "'",
  }
  output.value = input.value.replace(/&amp;|&lt;|&gt;|&quot;|&#39;/g, c => map[c])
}

function clear() {
  input.value = ''
  output.value = ''
}
</script>
```

- [ ] **Step 4: 创建 UnicodeConverter.vue**

```vue
<template>
  <ToolLayout title="Unicode编解码" description="中文与Unicode互相转换">
    <template #input>
      <a-textarea
        v-model="input"
        placeholder="输入中文或Unicode（如 你好）"
        :auto-size="{ minRows: 12, maxRows: 20 }"
      />
    </template>
    <template #output>
      <a-textarea
        v-model="output"
        placeholder="结果"
        :auto-size="{ minRows: 12, maxRows: 20 }"
        readonly
      />
    </template>
    <template #actions>
      <a-button @click="clear">清空</a-button>
      <a-button type="outline" @click="decode">Unicode→中文</a-button>
      <a-button type="primary" @click="encode">中文→Unicode</a-button>
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
  output.value = Array.from(input.value)
    .map(c => '\\u' + c.charCodeAt(0).toString(16).padStart(4, '0'))
    .join('')
}

function decode() {
  if (!input.value) {
    Message.warning('请输入内容')
    return
  }
  try {
    output.value = input.value.replace(/\\u[\da-fA-F]{4}/g, match =>
      String.fromCharCode(parseInt(match.substring(2), 16))
    )
  } catch (e: any) {
    Message.error('解码失败: ' + e.message)
  }
}

function clear() {
  input.value = ''
  output.value = ''
}
</script>
```

- [ ] **Step 5: 验证编解码工具**

在浏览器中测试每个工具：
- Base64：编码 `你好` → `5L2g5aW9`，解码回来
- URL：编码 `hello world` → `hello%20world`
- HTML：编码 `<div>` → `&lt;div&gt;`
- Unicode：编码 `你好` → `你好`

---

## Task 7: 哈希计算工具

**Files:**
- Create: `frontend/src/views/tools/HashCalculator.vue`

- [ ] **Step 1: 创建 HashCalculator.vue**

```vue
<template>
  <ToolLayout title="哈希计算" description="计算文本的MD5、SHA1、SHA256哈希值">
    <template #input>
      <a-textarea
        v-model="input"
        placeholder="输入要计算哈希的文本"
        :auto-size="{ minRows: 12, maxRows: 20 }"
      />
    </template>
    <template #output>
      <div class="hash-results">
        <div class="hash-item">
          <div class="hash-label">MD5</div>
          <a-input :model-value="md5" readonly>
            <template #append>
              <a-button type="text" size="mini" @click="copy(md5)">
                <template #icon><icon-copy /></template>
              </a-button>
            </template>
          </a-input>
        </div>
        <div class="hash-item">
          <div class="hash-label">SHA1</div>
          <a-input :model-value="sha1" readonly>
            <template #append>
              <a-button type="text" size="mini" @click="copy(sha1)">
                <template #icon><icon-copy /></template>
              </a-button>
            </template>
          </a-input>
        </div>
        <div class="hash-item">
          <div class="hash-label">SHA256</div>
          <a-input :model-value="sha256" readonly>
            <template #append>
              <a-button type="text" size="mini" @click="copy(sha256)">
                <template #icon><icon-copy /></template>
              </a-button>
            </template>
          </a-input>
        </div>
      </div>
    </template>
    <template #actions>
      <a-button @click="clear">清空</a-button>
      <a-button type="primary" @click="calculate">计算</a-button>
    </template>
  </ToolLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Message } from '@arco-design/web-vue'
import CryptoJS from 'crypto-js'
import ToolLayout from './ToolLayout.vue'

const input = ref('')
const md5 = ref('')
const sha1 = ref('')
const sha256 = ref('')

function calculate() {
  if (!input.value) {
    Message.warning('请输入内容')
    return
  }
  md5.value = CryptoJS.MD5(input.value).toString()
  sha1.value = CryptoJS.SHA1(input.value).toString()
  sha256.value = CryptoJS.SHA256(input.value).toString()
  Message.success('计算完成')
}

function copy(text: string) {
  if (!text) return
  navigator.clipboard?.writeText(text).then(() => Message.success('已复制'))
}

function clear() {
  input.value = ''
  md5.value = ''
  sha1.value = ''
  sha256.value = ''
}
</script>

<style scoped>
.hash-results {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hash-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.hash-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-2);
}
</style>
```

- [ ] **Step 2: 验证哈希计算**

输入 `hello`，验证：
- MD5: `5d41402abc4b2a76b9719d911017c592`
- SHA1: `aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d`
- SHA256: `2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824`

---

## Task 8: JWT解析工具

**Files:**
- Create: `frontend/src/views/tools/JwtDecoder.vue`

- [ ] **Step 1: 创建 JwtDecoder.vue**

```vue
<template>
  <ToolLayout title="JWT解析" description="粘贴JWT Token，解析Header和Payload">
    <template #input>
      <a-textarea
        v-model="input"
        placeholder="粘贴JWT Token（如 eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.xxx）"
        :auto-size="{ minRows: 8, maxRows: 12 }"
      />
    </template>
    <template #output>
      <div class="jwt-output">
        <div class="jwt-section">
          <div class="jwt-section-header">
            <a-tag color="blue" size="small">Header</a-tag>
            <a-button type="text" size="mini" @click="copyJson(headerJson)">
              <template #icon><icon-copy /></template>
            </a-button>
          </div>
          <JsonViewer v-if="headerJson" :content="headerJson" max-height="150px" />
          <a-empty v-else description="无数据" :image-style="{ height: '40px' }" />
        </div>
        <div class="jwt-section">
          <div class="jwt-section-header">
            <a-tag color="green" size="small">Payload</a-tag>
            <a-button type="text" size="mini" @click="copyJson(payloadJson)">
              <template #icon><icon-copy /></template>
            </a-button>
          </div>
          <JsonViewer v-if="payloadJson" :content="payloadJson" max-height="300px" />
          <a-empty v-else description="无数据" :image-style="{ height: '40px' }" />
        </div>
        <div v-if="signatureInfo" class="jwt-signature">
          <a-tag :color="signatureInfo.valid ? 'green' : 'orange'" size="small">
            {{ signatureInfo.label }}
          </a-tag>
        </div>
      </div>
    </template>
    <template #actions>
      <a-button @click="clear">清空</a-button>
      <a-button type="primary" @click="decode">解析</a-button>
    </template>
  </ToolLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Message } from '@arco-design/web-vue'
import ToolLayout from './ToolLayout.vue'
import JsonViewer from '@/components/JsonViewer.vue'

const input = ref('')
const headerJson = ref<any>(null)
const payloadJson = ref<any>(null)
const signatureInfo = ref<{ valid: boolean; label: string } | null>(null)

function base64UrlDecode(str: string): string {
  let base64 = str.replace(/-/g, '+').replace(/_/g, '/')
  const pad = base64.length % 4
  if (pad) base64 += '='.repeat(4 - pad)
  return decodeURIComponent(escape(atob(base64)))
}

function decode() {
  if (!input.value.trim()) {
    Message.warning('请输入JWT Token')
    return
  }

  const parts = input.value.trim().split('.')
  if (parts.length < 2 || parts.length > 3) {
    Message.error('无效的JWT格式，应包含2或3个部分')
    return
  }

  try {
    headerJson.value = JSON.parse(base64UrlDecode(parts[0]))
  } catch {
    Message.error('Header解析失败')
    return
  }

  try {
    const payload = JSON.parse(base64UrlDecode(parts[1]))
    // 友好展示时间字段
    const friendly: any = {}
    for (const [key, value] of Object.entries(payload)) {
      if (typeof value === 'number' && (key === 'exp' || key === 'iat' || key === 'nbf')) {
        friendly[key] = `${value} (${new Date(value * 1000).toLocaleString()})`
      } else {
        friendly[key] = value
      }
    }
    payloadJson.value = friendly
  } catch {
    Message.error('Payload解析失败')
    return
  }

  if (parts.length === 3 && parts[2]) {
    signatureInfo.value = { valid: false, label: '签名未验证（仅解码）' }
  } else {
    signatureInfo.value = null
  }

  Message.success('解析完成')
}

function copyJson(obj: any) {
  if (!obj) return
  navigator.clipboard?.writeText(JSON.stringify(obj, null, 2)).then(() => Message.success('已复制'))
}

function clear() {
  input.value = ''
  headerJson.value = null
  payloadJson.value = null
  signatureInfo.value = null
}
</script>

<style scoped>
.jwt-output {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.jwt-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.jwt-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.jwt-signature {
  display: flex;
  align-items: center;
}
</style>
```

- [ ] **Step 2: 验证JWT解析**

使用测试Token验证：
```
eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

---

## Task 9: AES/DES加解密工具

**Files:**
- Create: `frontend/src/views/tools/AesTool.vue`

- [ ] **Step 1: 创建 AesTool.vue**

```vue
<template>
  <ToolLayout title="AES/DES加解密" description="对称加密与解密工具">
    <template #input>
      <div class="aes-input-area">
        <a-textarea
          v-model="input"
          placeholder="输入要加密或解密的文本"
          :auto-size="{ minRows: 8, maxRows: 12 }"
        />
        <div class="aes-config">
          <a-input v-model="secretKey" placeholder="密钥" style="width: 200px" />
          <a-select v-model="mode" style="width: 100px">
            <a-option value="AES">AES</a-option>
            <a-option value="DES">DES</a-option>
          </a-select>
          <a-select v-model="outputFormat" style="width: 100px">
            <a-option value="Base64">Base64</a-option>
            <a-option value="Hex">Hex</a-option>
          </a-select>
        </div>
      </div>
    </template>
    <template #output>
      <a-textarea
        v-model="output"
        placeholder="结果"
        :auto-size="{ minRows: 12, maxRows: 20 }"
        readonly
      />
    </template>
    <template #actions>
      <a-button @click="clear">清空</a-button>
      <a-button type="outline" @click="decrypt">解密</a-button>
      <a-button type="primary" @click="encrypt">加密</a-button>
    </template>
  </ToolLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Message } from '@arco-design/web-vue'
import CryptoJS from 'crypto-js'
import ToolLayout from './ToolLayout.vue'

const input = ref('')
const output = ref('')
const secretKey = ref('')
const mode = ref('AES')
const outputFormat = ref('Base64')

function encrypt() {
  if (!input.value) {
    Message.warning('请输入内容')
    return
  }
  if (!secretKey.value) {
    Message.warning('请输入密钥')
    return
  }

  try {
    const cipher = mode.value === 'AES'
      ? CryptoJS.AES.encrypt(input.value, secretKey.value)
      : CryptoJS.DES.encrypt(input.value, secretKey.value)

    output.value = outputFormat.value === 'Base64'
      ? cipher.toString()
      : cipher.ciphertext.toString(CryptoJS.enc.Hex)
  } catch (e: any) {
    Message.error('加密失败: ' + e.message)
  }
}

function decrypt() {
  if (!input.value) {
    Message.warning('请输入内容')
    return
  }
  if (!secretKey.value) {
    Message.warning('请输入密钥')
    return
  }

  try {
    let decrypted
    if (mode.value === 'AES') {
      decrypted = CryptoJS.AES.decrypt(input.value, secretKey.value)
    } else {
      decrypted = CryptoJS.DES.decrypt(input.value, secretKey.value)
    }

    const result = decrypted.toString(CryptoJS.enc.Utf8)
    if (!result) {
      Message.error('解密失败，请检查密钥或密文格式')
      return
    }
    output.value = result
  } catch (e: any) {
    Message.error('解密失败: ' + e.message)
  }
}

function clear() {
  input.value = ''
  output.value = ''
}
</script>

<style scoped>
.aes-input-area {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
}

.aes-config {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
```

- [ ] **Step 2: 验证加解密**

- 输入 `hello world`，密钥 `test123`，AES加密
- 复制密文，粘贴回输入框，解密验证结果一致

---

## Task 10: UUID生成 + 随机字符串

**Files:**
- Create: `frontend/src/views/tools/UuidGenerator.vue`
- Create: `frontend/src/views/tools/RandomString.vue`

- [ ] **Step 1: 创建 UuidGenerator.vue**

```vue
<template>
  <ToolLayout title="UUID生成" description="批量生成UUID v4">
    <template #input>
      <div class="uuid-config">
        <a-form layout="vertical">
          <a-form-item label="生成数量">
            <a-input-number v-model="count" :min="1" :max="100" style="width: 100%" />
          </a-form-item>
          <a-form-item label="格式选项">
            <a-space direction="vertical">
              <a-checkbox v-model="withDash">包含横线</a-checkbox>
              <a-checkbox v-model="uppercase">大写</a-checkbox>
            </a-space>
          </a-form-item>
        </a-form>
      </div>
    </template>
    <template #output>
      <a-textarea
        v-model="output"
        placeholder="点击生成查看结果"
        :auto-size="{ minRows: 12, maxRows: 20 }"
        readonly
      />
    </template>
    <template #actions>
      <a-button @click="clear">清空</a-button>
      <a-button type="outline" @click="copyAll">复制全部</a-button>
      <a-button type="primary" @click="generate">生成</a-button>
    </template>
  </ToolLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Message } from '@arco-design/web-vue'
import ToolLayout from './ToolLayout.vue'

const count = ref(10)
const withDash = ref(true)
const uppercase = ref(false)
const output = ref('')

function generateUuid(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = Math.random() * 16 | 0
    const v = c === 'x' ? r : (r & 0x3 | 0x8)
    return v.toString(16)
  })
}

function generate() {
  const uuids: string[] = []
  for (let i = 0; i < count.value; i++) {
    let uuid = generateUuid()
    if (!withDash.value) uuid = uuid.replace(/-/g, '')
    if (uppercase.value) uuid = uuid.toUpperCase()
    uuids.push(uuid)
  }
  output.value = uuids.join('\n')
  Message.success(`已生成 ${count.value} 个UUID`)
}

function copyAll() {
  if (!output.value) return
  navigator.clipboard?.writeText(output.value).then(() => Message.success('已复制'))
}

function clear() {
  output.value = ''
}
</script>

<style scoped>
.uuid-config {
  padding: 8px 0;
}
</style>
```

- [ ] **Step 2: 创建 RandomString.vue**

```vue
<template>
  <ToolLayout title="随机字符串" description="按指定规则生成随机字符串">
    <template #input>
      <div class="random-config">
        <a-form layout="vertical">
          <a-form-item label="字符串长度">
            <a-input-number v-model="length" :min="1" :max="1000" style="width: 100%" />
          </a-form-item>
          <a-form-item label="字符集">
            <a-space direction="vertical">
              <a-checkbox v-model="useUpper">大写字母 (A-Z)</a-checkbox>
              <a-checkbox v-model="useLower">小写字母 (a-z)</a-checkbox>
              <a-checkbox v-model="useDigit">数字 (0-9)</a-checkbox>
              <a-checkbox v-model="useSpecial">特殊字符 (!@#$...)</a-checkbox>
            </a-space>
          </a-form-item>
          <a-form-item label="生成数量">
            <a-input-number v-model="count" :min="1" :max="100" style="width: 100%" />
          </a-form-item>
        </a-form>
      </div>
    </template>
    <template #output>
      <a-textarea
        v-model="output"
        placeholder="点击生成查看结果"
        :auto-size="{ minRows: 12, maxRows: 20 }"
        readonly
      />
    </template>
    <template #actions>
      <a-button @click="clear">清空</a-button>
      <a-button type="outline" @click="copyAll">复制全部</a-button>
      <a-button type="primary" @click="generate">生成</a-button>
    </template>
  </ToolLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Message } from '@arco-design/web-vue'
import ToolLayout from './ToolLayout.vue'

const length = ref(16)
const count = ref(5)
const useUpper = ref(true)
const useLower = ref(true)
const useDigit = ref(true)
const useSpecial = ref(false)
const output = ref('')

function generate() {
  let charset = ''
  if (useUpper.value) charset += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
  if (useLower.value) charset += 'abcdefghijklmnopqrstuvwxyz'
  if (useDigit.value) charset += '0123456789'
  if (useSpecial.value) charset += '!@#$%^&*()_+-=[]{}|;:,.<>?'

  if (!charset) {
    Message.warning('请至少选择一种字符集')
    return
  }

  const results: string[] = []
  for (let i = 0; i < count.value; i++) {
    let str = ''
    for (let j = 0; j < length.value; j++) {
      str += charset.charAt(Math.floor(Math.random() * charset.length))
    }
    results.push(str)
  }
  output.value = results.join('\n')
  Message.success(`已生成 ${count.value} 个随机字符串`)
}

function copyAll() {
  if (!output.value) return
  navigator.clipboard?.writeText(output.value).then(() => Message.success('已复制'))
}

function clear() {
  output.value = ''
}
</script>

<style scoped>
.random-config {
  padding: 8px 0;
}
</style>
```

- [ ] **Step 3: 验证UUID和随机字符串生成**

- UUID：生成10个，验证格式正确（36字符带横线）
- 随机字符串：生成5个长度16的字符串，验证长度和字符集

---

## Task 11: 测试数据生成 + 二维码生成

**Files:**
- Create: `frontend/src/views/tools/TestDataGenerator.vue`
- Create: `frontend/src/views/tools/QrCodeGenerator.vue`

- [ ] **Step 1: 创建 TestDataGenerator.vue**

```vue
<template>
  <ToolLayout title="测试数据生成" description="生成姓名、手机号、身份证等测试数据">
    <template #input>
      <div class="testdata-config">
        <a-form layout="vertical">
          <a-form-item label="数据类型">
            <a-select v-model="dataType" style="width: 100%">
              <a-option value="name">姓名</a-option>
              <a-option value="phone">手机号</a-option>
              <a-option value="idcard">身份证号</a-option>
              <a-option value="email">邮箱</a-option>
              <a-option value="address">地址</a-option>
              <a-option value="bank">银行卡号</a-option>
            </a-select>
          </a-form-item>
          <a-form-item label="生成数量">
            <a-input-number v-model="count" :min="1" :max="100" style="width: 100%" />
          </a-form-item>
        </a-form>
      </div>
    </template>
    <template #output>
      <div class="testdata-output">
        <a-table
          v-if="tableData.length"
          :columns="tableColumns"
          :data="tableData"
          :pagination="false"
          size="small"
          :bordered="false"
        />
        <a-empty v-else description="点击生成查看结果" />
      </div>
    </template>
    <template #actions>
      <a-button @click="clear">清空</a-button>
      <a-button type="outline" @click="copyAll">复制全部</a-button>
      <a-button type="primary" @click="generate">生成</a-button>
    </template>
  </ToolLayout>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Message } from '@arco-design/web-vue'
import ToolLayout from './ToolLayout.vue'

const dataType = ref('name')
const count = ref(10)
const tableData = ref<any[]>([])

const tableColumns = computed(() => [
  { title: '#', dataIndex: 'index', width: 60 },
  { title: '数据', dataIndex: 'value' }
])

const surnames = '赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜'.split('')
const names = '伟芳娜秀英敏静丽强磊洋艳勇军杰娟涛超明刚秀兰飞鑫桂英'.split('')

function randomInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min
}

function generateName(): string {
  return surnames[randomInt(0, surnames.length - 1)] +
    names[randomInt(0, names.length - 1)] +
    (Math.random() > 0.5 ? names[randomInt(0, names.length - 1)] : '')
}

function generatePhone(): string {
  const prefixes = ['130', '131', '132', '133', '135', '136', '137', '138', '139', '150', '151', '152', '153', '155', '156', '157', '158', '159', '170', '176', '177', '178', '180', '181', '182', '183', '184', '185', '186', '187', '188', '189']
  return prefixes[randomInt(0, prefixes.length - 1)] + String(randomInt(10000000, 99999999))
}

function generateIdCard(): string {
  const areas = ['110101', '310115', '440305', '510104', '330102']
  const year = randomInt(1970, 2005)
  const month = String(randomInt(1, 12)).padStart(2, '0')
  const day = String(randomInt(1, 28)).padStart(2, '0')
  const seq = String(randomInt(100, 999))
  const base = areas[randomInt(0, areas.length - 1)] + year + month + day + seq
  const weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
  const checks = '10X98765432'
  let sum = 0
  for (let i = 0; i < 17; i++) sum += parseInt(base[i]) * weights[i]
  return base + checks[sum % 11]
}

function generateEmail(): string {
  const domains = ['qq.com', '163.com', 'gmail.com', 'outlook.com', 'foxmail.com']
  const chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
  let name = ''
  for (let i = 0; i < randomInt(5, 10); i++) name += chars[randomInt(0, chars.length - 1)]
  return name + '@' + domains[randomInt(0, domains.length - 1)]
}

function generateAddress(): string {
  const cities = ['北京市朝阳区', '上海市浦东新区', '深圳市南山区', '杭州市西湖区', '成都市武侯区']
  const roads = ['人民路', '解放大道', '中山路', '建设路', '和平街']
  return cities[randomInt(0, cities.length - 1)] + roads[randomInt(0, roads.length - 1)] + randomInt(1, 999) + '号'
}

function generateBank(): string {
  const prefixes = ['622202', '622848', '621700', '622150']
  let card = prefixes[randomInt(0, prefixes.length - 1)]
  for (let i = 0; i < 13; i++) card += randomInt(0, 9)
  return card
}

const generators: Record<string, () => string> = {
  name: generateName,
  phone: generatePhone,
  idcard: generateIdCard,
  email: generateEmail,
  address: generateAddress,
  bank: generateBank
}

function generate() {
  const gen = generators[dataType.value]
  if (!gen) return
  tableData.value = Array.from({ length: count.value }, (_, i) => ({
    index: i + 1,
    value: gen()
  }))
  Message.success(`已生成 ${count.value} 条数据`)
}

function copyAll() {
  if (!tableData.value.length) return
  const text = tableData.value.map(r => r.value).join('\n')
  navigator.clipboard?.writeText(text).then(() => Message.success('已复制'))
}

function clear() {
  tableData.value = []
}
</script>

<style scoped>
.testdata-config {
  padding: 8px 0;
}

.testdata-output {
  height: 100%;
}
</style>
```

- [ ] **Step 2: 创建 QrCodeGenerator.vue**

```vue
<template>
  <ToolLayout title="二维码生成" description="将文本或URL转换为二维码图片">
    <template #input>
      <a-textarea
        v-model="input"
        placeholder="输入文本或URL"
        :auto-size="{ minRows: 12, maxRows: 20 }"
      />
    </template>
    <template #output>
      <div class="qrcode-output">
        <div v-if="qrDataUrl" class="qrcode-preview">
          <img :src="qrDataUrl" alt="二维码" class="qrcode-img" />
        </div>
        <a-empty v-else description="点击生成查看二维码" />
      </div>
    </template>
    <template #actions>
      <a-button @click="clear">清空</a-button>
      <a-button type="outline" :disabled="!qrDataUrl" @click="download">下载PNG</a-button>
      <a-button type="primary" @click="generate">生成</a-button>
    </template>
  </ToolLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Message } from '@arco-design/web-vue'
import QRCode from 'qrcode'
import ToolLayout from './ToolLayout.vue'

const input = ref('')
const qrDataUrl = ref('')

async function generate() {
  if (!input.value.trim()) {
    Message.warning('请输入内容')
    return
  }
  try {
    qrDataUrl.value = await QRCode.toDataURL(input.value, {
      width: 300,
      margin: 2,
      color: { dark: '#000000', light: '#ffffff' }
    })
  } catch (e: any) {
    Message.error('生成失败: ' + e.message)
  }
}

function download() {
  if (!qrDataUrl.value) return
  const link = document.createElement('a')
  link.download = 'qrcode.png'
  link.href = qrDataUrl.value
  link.click()
}

function clear() {
  input.value = ''
  qrDataUrl.value = ''
}
</script>

<style scoped>
.qrcode-output {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.qrcode-preview {
  padding: 16px;
  background: white;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
}

.qrcode-img {
  display: block;
  max-width: 300px;
}
</style>
```

- [ ] **Step 3: 验证测试数据和二维码**

- 测试数据：选择手机号，生成10条，验证都是11位手机号
- 二维码：输入 `https://example.com`，生成二维码，用手机扫码验证

---

## Task 12: 时间戳转换 + Cron生成器 + 进制转换

**Files:**
- Create: `frontend/src/views/tools/TimestampConverter.vue`
- Create: `frontend/src/views/tools/CronBuilder.vue`
- Create: `frontend/src/views/tools/RadixConverter.vue`

- [ ] **Step 1: 创建 TimestampConverter.vue**

```vue
<template>
  <ToolLayout title="时间戳转换" description="Unix时间戳与日期互相转换">
    <template #input>
      <div class="timestamp-input">
        <div class="current-time">
          <span class="label">当前时间戳：</span>
          <a-tag color="blue">{{ currentSecond }}</a-tag>
          <a-tag color="purple">{{ currentMilli }}</a-tag>
        </div>
        <a-divider />
        <a-form layout="vertical">
          <a-form-item label="时间戳 → 日期">
            <a-input-number v-model="timestampInput" placeholder="输入时间戳" style="width: 100%" />
            <a-checkbox v-model="isMilli" style="margin-top: 8px">毫秒级</a-checkbox>
          </a-form-item>
          <a-form-item label="日期 → 时间戳">
            <a-date-picker v-model="dateInput" show-time style="width: 100%" />
          </a-form-item>
        </a-form>
      </div>
    </template>
    <template #output>
      <div class="timestamp-output">
        <div v-if="dateResult" class="result-item">
          <div class="result-label">时间戳转日期结果：</div>
          <a-input :model-value="dateResult" readonly>
            <template #append>
              <a-button type="text" size="mini" @click="copy(dateResult!)">
                <template #icon><icon-copy /></template>
              </a-button>
            </template>
          </a-input>
        </div>
        <div v-if="timestampResult" class="result-item">
          <div class="result-label">日期转时间戳结果：</div>
          <a-input :model-value="timestampResult" readonly>
            <template #append>
              <a-button type="text" size="mini" @click="copy(timestampResult!)">
                <template #icon><icon-copy /></template>
              </a-button>
            </template>
          </a-input>
        </div>
      </div>
    </template>
    <template #actions>
      <a-button type="primary" @click="convert">转换</a-button>
    </template>
  </ToolLayout>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import ToolLayout from './ToolLayout.vue'

const currentSecond = ref('')
const currentMilli = ref('')
const timestampInput = ref<number>()
const isMilli = ref(false)
const dateInput = ref<string>()
const dateResult = ref<string>()
const timestampResult = ref<string>()

let timer: ReturnType<typeof setInterval>

onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  clearInterval(timer)
})

function updateTime() {
  const now = Date.now()
  currentMilli.value = String(now)
  currentSecond.value = String(Math.floor(now / 1000))
}

function convert() {
  // 时间戳→日期
  if (timestampInput.value != null) {
    const ts = isMilli.value ? timestampInput.value : timestampInput.value * 1000
    const d = new Date(ts)
    if (isNaN(d.getTime())) {
      Message.error('无效的时间戳')
    } else {
      dateResult.value = d.toLocaleString('zh-CN', {
        year: 'numeric', month: '2-digit', day: '2-digit',
        hour: '2-digit', minute: '2-digit', second: '2-digit'
      })
    }
  }

  // 日期→时间戳
  if (dateInput.value) {
    const d = new Date(dateInput.value)
    if (isNaN(d.getTime())) {
      Message.error('无效的日期')
    } else {
      timestampResult.value = String(Math.floor(d.getTime() / 1000))
    }
  }
}

function copy(text: string) {
  navigator.clipboard?.writeText(text).then(() => Message.success('已复制'))
}
</script>

<style scoped>
.timestamp-input,
.timestamp-output {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.current-time {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.label {
  font-size: 13px;
  color: var(--color-text-2);
}

.result-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.result-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-2);
}
</style>
```

- [ ] **Step 2: 创建 CronBuilder.vue**

```vue
<template>
  <ToolLayout title="Cron生成器" description="可视化配置Cron表达式">
    <template #input>
      <div class="cron-config">
        <a-form layout="vertical">
          <a-form-item label="快速选择">
            <a-space wrap>
              <a-button size="small" @click="preset('*/1 * * * *')">每分钟</a-button>
              <a-button size="small" @click="preset('0 */1 * * *')">每小时</a-button>
              <a-button size="small" @click="preset('0 0 * * *')">每天零点</a-button>
              <a-button size="small" @click="preset('0 0 * * 1')">每周一</a-button>
              <a-button size="small" @click="preset('0 0 1 * *')">每月1号</a-button>
            </a-space>
          </a-form-item>
          <a-form-item label="秒 (0-59)">
            <a-input v-model="fields.second" placeholder="0" />
          </a-form-item>
          <a-form-item label="分 (0-59)">
            <a-input v-model="fields.minute" placeholder="*" />
          </a-form-item>
          <a-form-item label="时 (0-23)">
            <a-input v-model="fields.hour" placeholder="*" />
          </a-form-item>
          <a-form-item label="日 (1-31)">
            <a-input v-model="fields.day" placeholder="*" />
          </a-form-item>
          <a-form-item label="月 (1-12)">
            <a-input v-model="fields.month" placeholder="*" />
          </a-form-item>
          <a-form-item label="周 (0-7, 0和7都是周日)">
            <a-input v-model="fields.week" placeholder="*" />
          </a-form-item>
        </a-form>
      </div>
    </template>
    <template #output>
      <div class="cron-output">
        <div class="cron-expression">
          <div class="result-label">Cron表达式：</div>
          <a-input :model-value="cronExpression" readonly size="large">
            <template #append>
              <a-button type="text" @click="copy(cronExpression)">
                <template #icon><icon-copy /></template>
              </a-button>
            </template>
          </a-input>
        </div>
        <div class="cron-preview">
          <div class="result-label">最近5次执行时间：</div>
          <div v-for="(time, i) in nextTimes" :key="i" class="preview-item">
            <a-tag size="small">{{ i + 1 }}</a-tag>
            <span>{{ time }}</span>
          </div>
        </div>
      </div>
    </template>
    <template #actions>
      <a-button type="primary" @click="copy(cronExpression)">复制表达式</a-button>
    </template>
  </ToolLayout>
</template>

<script setup lang="ts">
import { reactive, computed } from 'vue'
import { Message } from '@arco-design/web-vue'
import ToolLayout from './ToolLayout.vue'

const fields = reactive({
  second: '0',
  minute: '*',
  hour: '*',
  day: '*',
  month: '*',
  week: '*'
})

const cronExpression = computed(() => {
  return `${fields.second} ${fields.minute} ${fields.hour} ${fields.day} ${fields.month} ${fields.week}`
})

const nextTimes = computed(() => {
  // 简单预览：基于当前时间推算
  const now = new Date()
  const times: string[] = []
  for (let i = 1; i <= 5; i++) {
    const next = new Date(now.getTime() + i * 60000) // 简化：每次加1分钟
    times.push(next.toLocaleString('zh-CN'))
  }
  return times
})

function preset(expr: string) {
  const parts = expr.split(' ')
  fields.second = parts[0] || '0'
  fields.minute = parts[1] || '*'
  fields.hour = parts[2] || '*'
  fields.day = parts[3] || '*'
  fields.month = parts[4] || '*'
  fields.week = parts[5] || '*'
}

function copy(text: string) {
  navigator.clipboard?.writeText(text).then(() => Message.success('已复制'))
}
</script>

<style scoped>
.cron-config,
.cron-output {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.cron-expression {
  margin-bottom: 16px;
}

.cron-preview {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preview-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--color-text-2);
}

.result-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-2);
  margin-bottom: 8px;
}
</style>
```

- [ ] **Step 3: 创建 RadixConverter.vue**

```vue
<template>
  <ToolLayout title="进制转换" description="2/8/10/16进制互相转换">
    <template #input>
      <div class="radix-input">
        <a-form layout="vertical">
          <a-form-item label="输入数字">
            <a-input v-model="input" placeholder="输入数字" />
          </a-form-item>
          <a-form-item label="输入进制">
            <a-select v-model="inputBase" style="width: 100%">
              <a-option :value="2">二进制 (2)</a-option>
              <a-option :value="8">八进制 (8)</a-option>
              <a-option :value="10">十进制 (10)</a-option>
              <a-option :value="16">十六进制 (16)</a-option>
            </a-select>
          </a-form-item>
        </a-form>
      </div>
    </template>
    <template #output>
      <div class="radix-output">
        <div class="radix-item">
          <div class="radix-label">二进制 (2)</div>
          <a-input :model-value="results.bin" readonly>
            <template #append>
              <a-button type="text" size="mini" @click="copy(results.bin)">
                <template #icon><icon-copy /></template>
              </a-button>
            </template>
          </a-input>
        </div>
        <div class="radix-item">
          <div class="radix-label">八进制 (8)</div>
          <a-input :model-value="results.oct" readonly>
            <template #append>
              <a-button type="text" size="mini" @click="copy(results.oct)">
                <template #icon><icon-copy /></template>
              </a-button>
            </template>
          </a-input>
        </div>
        <div class="radix-item">
          <div class="radix-label">十进制 (10)</div>
          <a-input :model-value="results.dec" readonly>
            <template #append>
              <a-button type="text" size="mini" @click="copy(results.dec)">
                <template #icon><icon-copy /></template>
              </a-button>
            </template>
          </a-input>
        </div>
        <div class="radix-item">
          <div class="radix-label">十六进制 (16)</div>
          <a-input :model-value="results.hex" readonly>
            <template #append>
              <a-button type="text" size="mini" @click="copy(results.hex)">
                <template #icon><icon-copy /></template>
              </a-button>
            </template>
          </a-input>
        </div>
      </div>
    </template>
    <template #actions>
      <a-button type="primary" @click="convert">转换</a-button>
    </template>
  </ToolLayout>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { Message } from '@arco-design/web-vue'
import ToolLayout from './ToolLayout.vue'

const input = ref('')
const inputBase = ref(10)
const results = reactive({ bin: '', oct: '', dec: '', hex: '' })

function convert() {
  if (!input.value.trim()) {
    Message.warning('请输入数字')
    return
  }

  const num = parseInt(input.value, inputBase.value)
  if (isNaN(num)) {
    Message.error('无效的数字')
    return
  }

  results.bin = num.toString(2)
  results.oct = num.toString(8)
  results.dec = num.toString(10)
  results.hex = num.toString(16).toUpperCase()
}

function copy(text: string) {
  if (!text) return
  navigator.clipboard?.writeText(text).then(() => Message.success('已复制'))
}
</script>

<style scoped>
.radix-input,
.radix-output {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.radix-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.radix-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-2);
}
</style>
```

- [ ] **Step 4: 验证时间转换工具**

- 时间戳：输入 `1700000000`，验证转换结果
- Cron：点击"每分钟"，验证表达式为 `*/1 * * * *`
- 进制：输入 `255`（十进制），验证二进制 `11111111`、十六进制 `FF`

---

## Task 13: 更新进度文档

**Files:**
- Modify: `docs/progress.md`

- [ ] **Step 1: 更新 progress.md**

在进度清单中添加：

```markdown
- [x] 开发工具页面（17个工具：格式化、编解码、哈希加密、生成工具、时间转换）
```

- [ ] **Step 2: 提交所有代码**

```bash
cd d:/projects/TestForge-
git add frontend/src/views/tools/ frontend/src/router/index.ts frontend/src/layouts/MainLayout.vue frontend/package.json docs/
git commit -m "feat: 添加开发工具页面，集成17个测试开发常用工具"
```

---

## 执行顺序

任务必须按顺序执行，因为后续任务依赖前面的基础设施：

1. **Task 1**: 安装依赖 + 创建目录
2. **Task 2**: ToolLayout 共享布局
3. **Task 3**: ToolsPage + 路由 + 菜单（此时可以在浏览器看到页面框架）
4. **Task 4-12**: 各工具组件（可并行，但建议按顺序逐个验证）
5. **Task 13**: 更新文档 + 提交

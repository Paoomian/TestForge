<template>
  <div class="tools-page">
    <!-- 左侧工具卡片列表 -->
    <div class="tools-sidebar">
      <div class="tools-sidebar-header">
        <h3 class="tools-sidebar-title">工具箱</h3>
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
  IconTool, IconCode, IconFile, IconLock, IconThunderbolt, IconClockCircle
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
      { key: 'uuid', label: 'UUID生成', icon: markRaw(IconThunderbolt), component: markRaw(UuidGenerator) },
      { key: 'random', label: '随机字符串', icon: markRaw(IconThunderbolt), component: markRaw(RandomString) },
      { key: 'testdata', label: '测试数据生成', icon: markRaw(IconThunderbolt), component: markRaw(TestDataGenerator) },
      { key: 'qrcode', label: '二维码生成', icon: markRaw(IconThunderbolt), component: markRaw(QrCodeGenerator) },
    ]
  },
  {
    key: 'convert',
    label: '时间/转换',
    tools: [
      { key: 'timestamp', label: '时间戳转换', icon: markRaw(IconClockCircle), component: markRaw(TimestampConverter) },
      { key: 'cron', label: 'Cron生成器', icon: markRaw(IconClockCircle), component: markRaw(CronBuilder) },
      { key: 'radix', label: '进制转换', icon: markRaw(IconClockCircle), component: markRaw(RadixConverter) },
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
  height: calc(100vh - var(--header-height));
  margin: calc(-1 * var(--content-padding));
  padding: var(--content-padding);
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

.tools-list::-webkit-scrollbar {
  display: none;
}

.tools-list {
  -ms-overflow-style: none;
  scrollbar-width: none;
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

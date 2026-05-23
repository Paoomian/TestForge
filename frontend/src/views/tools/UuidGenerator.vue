<template>
  <ToolLayout title="UUID生成" description="批量生成UUID v4">
    <template #input>
      <div class="uuid-config">
        <a-form :model="{}" layout="vertical">
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
        :style="{ height: '100%' }"
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
  if (navigator.clipboard?.writeText) {
    navigator.clipboard.writeText(output.value).then(() => Message.success('已复制'))
  } else {
    const ta = document.createElement('textarea')
    ta.value = output.value
    ta.style.cssText = 'position:fixed;left:-9999px'
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
    Message.success('已复制')
  }
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

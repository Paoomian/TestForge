<template>
  <ToolLayout title="随机字符串" description="按指定规则生成随机字符串">
    <template #input>
      <div class="random-config">
        <a-form :model="{}" layout="vertical">
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
.random-config {
  padding: 8px 0;
}
</style>

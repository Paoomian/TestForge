<template>
  <ToolLayout title="进制转换" description="2/8/10/16进制互相转换">
    <template #input>
      <div class="radix-input">
        <a-form :model="{}" layout="vertical">
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

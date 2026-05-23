<template>
  <ToolLayout title="时间戳转换" description="Unix时间戳与日期互相转换">
    <template #input>
      <div class="timestamp-input">
        <div class="current-time">
          <span class="label">当前时间戳：</span>
          <a-tag color="blue" class="clickable-tag" @click="copy(currentSecond)">
            <icon-copy /> {{ currentSecond }}
          </a-tag>
          <a-tag color="purple" class="clickable-tag" @click="copy(currentMilli)">
            <icon-copy /> {{ currentMilli }}
          </a-tag>
        </div>
        <a-divider />
        <a-form :model="{}" layout="vertical">
          <a-form-item label="时间戳 → 日期">
            <div class="ts-input-row">
              <a-input-number v-model="timestampInput" placeholder="输入时间戳" style="flex: 1" />
              <a-checkbox v-model="isMilli">毫秒级</a-checkbox>
            </div>
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
        <div v-if="timestampSec" class="result-item">
          <div class="result-label">日期转时间戳结果：</div>
          <div class="ts-results">
            <div class="ts-result-row">
              <a-tag color="blue">秒</a-tag>
              <a-input :model-value="timestampSec" readonly style="flex: 1">
                <template #append>
                  <a-button type="text" size="mini" @click="copy(timestampSec!)">
                    <template #icon><icon-copy /></template>
                  </a-button>
                </template>
              </a-input>
            </div>
            <div class="ts-result-row">
              <a-tag color="purple">毫秒</a-tag>
              <a-input :model-value="timestampMs" readonly style="flex: 1">
                <template #append>
                  <a-button type="text" size="mini" @click="copy(timestampMs!)">
                    <template #icon><icon-copy /></template>
                  </a-button>
                </template>
              </a-input>
            </div>
          </div>
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
const timestampSec = ref<string>()
const timestampMs = ref<string>()

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

  if (dateInput.value) {
    const d = new Date(dateInput.value)
    if (isNaN(d.getTime())) {
      Message.error('无效的日期')
    } else {
      timestampSec.value = String(Math.floor(d.getTime() / 1000))
      timestampMs.value = String(d.getTime())
    }
  }
}

function copy(text: string) {
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

.clickable-tag {
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.clickable-tag:hover {
  opacity: 0.85;
  filter: brightness(1.1);
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

.ts-input-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ts-results {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ts-result-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>

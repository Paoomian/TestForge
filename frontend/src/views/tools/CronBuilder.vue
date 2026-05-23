<template>
  <ToolLayout title="Cron生成器" description="可视化配置Cron表达式">
    <template #input>
      <div class="cron-config">
        <a-form :model="{}" layout="vertical">
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
  const now = new Date()
  const times: string[] = []
  for (let i = 1; i <= 5; i++) {
    const next = new Date(now.getTime() + i * 60000)
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

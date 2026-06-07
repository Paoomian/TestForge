<template>
  <div class="step-detail" v-if="step">
    <!-- 步骤截图 -->
    <div class="detail-screenshot" v-if="step.screenshot">
      <img :src="`data:image/jpeg;base64,${step.screenshot}`" alt="步骤截图" />
    </div>

    <!-- 步骤信息 -->
    <div class="detail-section">
      <div class="section-title">基本信息</div>
      <a-form :model="formData" layout="vertical" size="small">
        <a-form-item label="操作类型">
          <a-select v-model="formData.action" :options="actionOptions" />
        </a-form-item>

        <!-- 导航 URL -->
        <a-form-item v-if="step.action === 'navigate'" label="目标 URL">
          <a-input v-model="formData.url" placeholder="URL" />
        </a-form-item>

        <!-- 输入值 -->
        <a-form-item v-if="step.action === 'type'" label="输入内容">
          <a-input v-model="formData.value" placeholder="输入的文本" />
        </a-form-item>

        <!-- 按键 -->
        <a-form-item v-if="step.action === 'press'" label="按键">
          <a-input v-model="formData.key" placeholder="Enter / Tab / Escape..." />
        </a-form-item>

        <!-- 拖拽坐标 -->
        <a-form-item v-if="step.action === 'drag'" label="起始坐标">
          <a-input :model-value="step.from ? `(${step.from.x}, ${step.from.y})` : '-'" disabled />
        </a-form-item>
        <a-form-item v-if="step.action === 'drag'" label="目标坐标">
          <a-input :model-value="step.to ? `(${step.to.x}, ${step.to.y})` : '-'" disabled />
        </a-form-item>

        <!-- 滚动距离 -->
        <a-form-item v-if="step.action === 'scroll'" label="滚动距离">
          <a-input :model-value="`水平: ${step.deltaX || 0}, 垂直: ${step.deltaY || 0}`" disabled />
        </a-form-item>

        <!-- 断言信息 -->
        <template v-if="step.action === 'assert'">
          <a-form-item label="断言类型">
            <a-input :model-value="getAssertTypeLabel((step as any).type)" disabled />
          </a-form-item>
          <a-form-item v-if="(step as any).selector" label="元素选择器">
            <a-input :model-value="(step as any).selector" disabled />
          </a-form-item>
          <a-form-item v-if="(step as any).expected" label="期望值">
            <a-input :model-value="(step as any).expected" disabled />
          </a-form-item>
          <a-form-item v-if="(step as any).attributeName" label="属性名">
            <a-input :model-value="(step as any).attributeName" disabled />
          </a-form-item>
        </template>

        <!-- 等待时间 -->
        <a-form-item label="前置等待 (ms)">
          <a-input-number v-model="formData.waitBefore" :min="0" :step="100" />
        </a-form-item>
      </a-form>
    </div>

    <!-- 元素定位信息 -->
    <div class="detail-section" v-if="step.target">
      <div class="section-title">元素定位</div>
      <a-form layout="vertical" size="small">
        <a-form-item label="CSS 选择器">
          <a-input v-model="formData.selector" placeholder="CSS Selector" allow-clear />
        </a-form-item>
        <a-form-item label="XPath">
          <a-input v-model="formData.xpath" placeholder="XPath" allow-clear />
        </a-form-item>
        <a-form-item label="元素文本">
          <a-input :model-value="step.target.text" disabled />
        </a-form-item>
        <a-form-item label="标签名">
          <a-input :model-value="step.target.tagName" disabled />
        </a-form-item>
      </a-form>
    </div>

    <!-- 操作按钮 -->
    <div class="detail-actions">
      <a-button type="primary" size="small" @click="handleApply">
        应用修改
      </a-button>
    </div>
  </div>

  <!-- 未选中状态 -->
  <div class="step-detail-empty" v-else>
    <icon-info-circle style="font-size: 24px; color: #c9cdd4;" />
    <span>选择一个步骤查看详情</span>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { IconInfoCircle } from '@arco-design/web-vue/es/icon'
import type { UIStep } from '@/api/uiCase'

interface Props {
  step: UIStep | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  updateStep: [step: UIStep]
}>()

function getAssertTypeLabel(type: string): string {
  const map: Record<string, string> = {
    element_exists: '元素存在',
    element_not_exists: '元素不存在',
    text_equals: '文本等于',
    text_contains: '文本包含',
    url_equals: 'URL 等于',
    url_contains: 'URL 包含',
    title_equals: '标题等于',
    title_contains: '标题包含',
    value_equals: '值等于',
    attribute_equals: '属性等于',
  }
  return map[type] || type
}

// 表单数据
const formData = ref({
  action: '',
  url: '',
  value: '',
  key: '',
  waitBefore: 0,
  selector: '',
  xpath: '',
})

// 操作类型选项
const actionOptions = [
  { label: '导航', value: 'navigate' },
  { label: '点击', value: 'click' },
  { label: '双击', value: 'dblclick' },
  { label: '输入', value: 'type' },
  { label: '按键', value: 'press' },
  { label: '选择', value: 'select' },
  { label: '勾选', value: 'check' },
  { label: '取消勾选', value: 'uncheck' },
  { label: '悬停', value: 'hover' },
  { label: '滚动', value: 'scroll' },
  { label: '等待', value: 'wait' },
  { label: '断言', value: 'assert' },
]

// 监听步骤变化，更新表单
watch(() => props.step, (newStep) => {
  if (newStep) {
    const stepData = newStep as Record<string, unknown>
    formData.value = {
      action: newStep.action,
      url: newStep.url || '',
      value: newStep.value || '',
      key: newStep.key || '',
      waitBefore: (stepData.waitMs as number) || newStep.waitBefore || 0,
      selector: newStep.target?.selector || '',
      xpath: newStep.target?.xpath || '',
    }
  }
}, { immediate: true })

function handleApply() {
  if (!props.step) return

  const updatedStep: UIStep = {
    ...props.step,
    action: formData.value.action,
    url: formData.value.url || undefined,
    value: formData.value.value || undefined,
    key: formData.value.key || undefined,
    waitBefore: formData.value.waitBefore || undefined,
    target: props.step.target ? {
      ...props.step.target,
      selector: formData.value.selector || undefined,
      xpath: formData.value.xpath || undefined,
    } : undefined,
  }

  // 如果是等待步骤，设置 waitMs 字段
  if (formData.value.action === 'wait') {
    (updatedStep as Record<string, unknown>).waitMs = formData.value.waitBefore || 1000
  }

  emit('updateStep', updatedStep)
}
</script>

<style scoped>
.step-detail {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e5e6eb;
  overflow-y: auto;
}

.detail-screenshot {
  width: 100%;
  padding: 12px;
  border-bottom: 1px solid #e5e6eb;
}

.detail-screenshot img {
  width: 100%;
  border-radius: 6px;
  border: 1px solid #e5e6eb;
}

.detail-section {
  padding: 12px 16px;
  border-bottom: 1px solid #e5e6eb;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 12px;
}

.detail-actions {
  padding: 12px 16px;
  display: flex;
  justify-content: flex-end;
}

.step-detail-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  height: 100%;
  color: #c9cdd4;
  font-size: 13px;
}
</style>

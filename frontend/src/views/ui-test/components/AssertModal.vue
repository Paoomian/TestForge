<template>
  <a-modal
    :visible="visible"
    title="添加断言"
    @ok="handleOk"
    @cancel="handleCancel"
    :width="500"
  >
    <!-- 已选元素信息 -->
    <div v-if="selectedElement" class="selected-element">
      <div class="element-header">
        <a-tag color="blue">已选元素</a-tag>
        <a-button type="text" size="mini" @click="handleReselect">重新选择</a-button>
      </div>
      <div class="element-info">
        <div class="info-item">
          <span class="label">标签：</span>
          <a-tag size="small">{{ selectedElement.tagName }}</a-tag>
        </div>
        <div class="info-item" v-if="selectedElement.text">
          <span class="label">文本：</span>
          <span class="value">{{ selectedElement.text.substring(0, 50) }}</span>
        </div>
        <div class="info-item" v-if="selectedElement.selector">
          <span class="label">选择器：</span>
          <a-tag size="small" color="gray">{{ selectedElement.selector }}</a-tag>
        </div>
      </div>
    </div>

    <!-- 未选择元素提示 -->
    <div v-else class="no-element">
      <a-alert type="info" show-icon>
        <template #title>请在左侧页面中点击选择要断言的元素</template>
        <template #content>
          <p>点击"选择元素"按钮后，在页面中点击目标元素</p>
        </template>
      </a-alert>
      <a-button type="primary" @click="handleStartSelect" style="margin-top: 12px">
        <template #icon><icon-pen /></template>
        选择元素
      </a-button>
    </div>

    <a-form :model="formData" layout="vertical" style="margin-top: 16px">
      <a-form-item label="断言类型" required>
        <a-select v-model="formData.type" placeholder="选择断言类型">
          <a-option value="element_exists">元素存在</a-option>
          <a-option value="text_equals">文本等于</a-option>
          <a-option value="text_contains">文本包含</a-option>
          <a-option value="value_equals">输入框值等于</a-option>
          <a-option value="attribute_equals">属性值等于</a-option>
          <a-option value="url_contains">当前 URL 包含</a-option>
          <a-option value="title_contains">页面标题包含</a-option>
        </a-select>
      </a-form-item>

      <!-- 期望值 -->
      <a-form-item v-if="needExpected" label="期望值" required>
        <a-input v-model="formData.expected" :placeholder="expectedPlaceholder" />
      </a-form-item>

      <!-- 属性名（仅属性断言需要） -->
      <a-form-item v-if="formData.type === 'attribute_equals'" label="属性名" required>
        <a-select v-model="formData.attributeName" placeholder="选择属性">
          <a-option value="href">链接地址 (href)</a-option>
          <a-option value="src">图片地址 (src)</a-option>
          <a-option value="placeholder">占位文本 (placeholder)</a-option>
          <a-option value="disabled">是否禁用 (disabled)</a-option>
          <a-option value="class">样式类名 (class)</a-option>
        </a-select>
      </a-form-item>

      <a-form-item label="超时时间">
        <a-slider v-model="formData.timeout" :min="1000" :max="10000" :step="1000" show-input />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { IconPen } from '@arco-design/web-vue/es/icon'

interface ElementInfo {
  tagName: string
  text: string
  selector: string
  xpath: string
  attributes?: Record<string, string | undefined>
}

interface Props {
  visible: boolean
  selectedElement?: ElementInfo | null
}

const props = withDefaults(defineProps<Props>(), {
  selectedElement: null,
})

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'startSelect': []
  'reselect': []
  confirm: [assertion: Record<string, unknown>]
}>()

const formData = ref({
  type: 'text_equals',
  expected: '',
  attributeName: 'href',
  timeout: 5000,
})

const needExpected = computed(() => {
  return ['text_equals', 'text_contains', 'value_equals', 'attribute_equals',
    'url_contains', 'title_contains'].includes(formData.value.type)
})

const expectedPlaceholder = computed(() => {
  const map: Record<string, string> = {
    text_equals: '输入期望的文本，如：登录',
    text_contains: '输入期望包含的文本，如：欢迎',
    value_equals: '输入期望的值，如：admin',
    attribute_equals: '输入期望的属性值',
    url_contains: '输入 URL 中应包含的内容，如：dashboard',
    title_contains: '输入标题中应包含的内容，如：首页',
  }
  return map[formData.value.type] || '输入期望值'
})

watch(() => props.visible, (val) => {
  if (val) {
    // 每次打开弹窗都重置表单
    formData.value = {
      type: 'text_equals',
      expected: '',
      attributeName: 'href',
      timeout: 5000,
    }
  }
})

// 当选中元素变化时，自动设置断言类型
watch(() => props.selectedElement, (val) => {
  if (val) {
    // 如果元素有文本，默认使用 text_equals
    if (val.text) {
      formData.value.type = 'text_equals'
    } else {
      formData.value.type = 'element_exists'
    }
  }
})

function handleStartSelect() {
  emit('startSelect')
  emit('update:visible', false)
}

function handleReselect() {
  emit('reselect')
}

function handleOk() {
  if (!props.selectedElement && ['element_exists', 'text_equals', 'text_contains',
    'value_equals', 'attribute_equals'].includes(formData.value.type)) {
    return
  }

  const assertion: Record<string, unknown> = {
    type: formData.value.type,
    timeout: formData.value.timeout,
  }

  if (props.selectedElement) {
    assertion.selector = props.selectedElement.selector
    assertion.xpath = props.selectedElement.xpath
    assertion.elementText = props.selectedElement.text
  }

  if (needExpected.value) {
    assertion.expected = formData.value.expected
  }

  if (formData.value.type === 'attribute_equals') {
    assertion.attributeName = formData.value.attributeName
  }

  emit('confirm', assertion)
  emit('update:visible', false)
}

function handleCancel() {
  emit('update:visible', false)
}
</script>

<style scoped>
.selected-element {
  background: #f2f3f5;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 16px;
}

.element-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.element-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.info-item .label {
  color: #86909c;
  min-width: 50px;
}

.info-item .value {
  color: #4e5969;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.no-element {
  text-align: center;
  padding: 12px 0;
}
</style>

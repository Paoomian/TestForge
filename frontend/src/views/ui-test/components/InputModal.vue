<template>
  <a-modal
    :visible="visible"
    title="输入内容"
    @ok="handleOk"
    @cancel="handleCancel"
    :width="400"
  >
    <div class="input-modal">
      <div class="target-info" v-if="target">
        <a-tag color="blue">{{ target.tagName }}</a-tag>
        <span class="target-text">{{ target.text || target.selector }}</span>
      </div>

      <a-form :model="{ value: inputValue }" layout="vertical" style="margin-top: 16px">
        <a-form-item label="输入内容">
          <a-input
            v-model="inputValue"
            :placeholder="placeholder"
            @press-enter="handleOk"
            ref="inputRef"
          />
        </a-form-item>
      </a-form>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'

interface TargetInfo {
  tagName: string
  text: string
  selector: string
  xpath: string
  attributes?: Record<string, string | undefined>
}

interface Props {
  visible: boolean
  target?: TargetInfo | null
}

const props = withDefaults(defineProps<Props>(), {
  target: null,
})

const emit = defineEmits<{
  'update:visible': [value: boolean]
  confirm: [value: string]
}>()

const inputValue = ref('')
const inputRef = ref()

const placeholder = ref('请输入内容')

watch(() => props.visible, (val) => {
  if (val) {
    inputValue.value = ''
    // 根据输入框类型设置占位符
    if (props.target) {
      const inputType = props.target.attributes?.type
      const inputPlaceholder = props.target.attributes?.placeholder
      if (inputPlaceholder) {
        placeholder.value = inputPlaceholder
      } else if (inputType === 'password') {
        placeholder.value = '请输入密码'
      } else if (inputType === 'email') {
        placeholder.value = '请输入邮箱'
      } else if (inputType === 'tel') {
        placeholder.value = '请输入手机号'
      } else {
        placeholder.value = '请输入内容'
      }
    }
    // 自动聚焦输入框
    nextTick(() => {
      inputRef.value?.focus()
    })
  }
})

function handleOk() {
  if (inputValue.value) {
    emit('confirm', inputValue.value)
  }
  emit('update:visible', false)
}

function handleCancel() {
  emit('update:visible', false)
}
</script>

<style scoped>
.input-modal {
  padding: 8px 0;
}

.target-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f2f3f5;
  border-radius: 6px;
}

.target-text {
  font-size: 13px;
  color: #4e5969;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>

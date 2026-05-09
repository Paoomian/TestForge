<template>
  <div class="url-input-container">
    <span v-if="baseUrl" class="env-prefix" :title="baseUrl">{{ baseUrl }}</span>
    <input
      ref="inputRef"
      class="url-native-input"
      :value="modelValue"
      placeholder="例如: /api/v1/users 或完整URL https://api.example.com/users"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />
    <span v-if="showPreview && baseUrl && modelValue && !modelValue.startsWith('http')" class="url-preview" :title="fullUrl">
      <icon-link />
    </span>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

const props = defineProps<{
  modelValue: string
  baseUrl?: string
}>()

defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const inputRef = ref<HTMLInputElement>()

const showPreview = computed(() => props.baseUrl && props.modelValue)

const fullUrl = computed(() => {
  if (!props.baseUrl || !props.modelValue) return ''
  if (props.modelValue.startsWith('http')) return props.modelValue
  const base = props.baseUrl.replace(/\/+$/, '')
  const path = props.modelValue.startsWith('/') ? props.modelValue : `/${props.modelValue}`
  return `${base}${path}`
})
</script>

<style scoped>
.url-input-container {
  display: flex;
  align-items: center;
  border: 1px solid var(--color-border-2);
  border-radius: 4px;
  background: var(--color-bg-2);
  height: 32px;
  transition: border-color 0.2s;
}
.url-input-container:focus-within {
  border-color: var(--color-primary-6);
}
.env-prefix {
  flex-shrink: 0;
  padding: 0 8px;
  background: var(--color-fill-2);
  color: var(--color-text-3);
  font-size: 12px;
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  height: 100%;
  display: flex;
  align-items: center;
  border-right: 1px solid var(--color-border-2);
}
.url-native-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  padding: 0 12px;
  height: 100%;
  font-size: 14px;
  color: var(--color-text-1);
  min-width: 0;
}
.url-native-input::placeholder {
  color: var(--color-text-3);
}
.url-preview {
  flex-shrink: 0;
  padding: 0 8px;
  color: var(--color-text-3);
  cursor: pointer;
  height: 100%;
  display: flex;
  align-items: center;
}
.url-preview:hover {
  color: var(--color-primary-6);
}
</style>

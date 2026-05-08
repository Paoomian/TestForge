<template>
  <a-input
    :model-value="modelValue"
    placeholder="例如: /api/v1/users 或完整URL https://api.example.com/users"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <template #prefix v-if="baseUrl">
      <a-tooltip :content="baseUrl">
        <span style="color: var(--color-text-3); font-size: 12px; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
          {{ baseUrl }}
        </span>
      </a-tooltip>
    </template>
    <template #append v-if="showPreview && baseUrl && modelValue && !modelValue.startsWith('http')">
      <a-tooltip :content="fullUrl">
        <icon-link style="cursor: pointer;" />
      </a-tooltip>
    </template>
  </a-input>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  modelValue: string
  baseUrl?: string
}>()

defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const showPreview = computed(() => props.baseUrl && props.modelValue)

const fullUrl = computed(() => {
  if (!props.baseUrl || !props.modelValue) return ''
  if (props.modelValue.startsWith('http')) return props.modelValue
  const base = props.baseUrl.replace(/\/+$/, '')
  const path = props.modelValue.startsWith('/') ? props.modelValue : `/${props.modelValue}`
  return `${base}${path}`
})
</script>

<template>
  <a-select
    :model-value="modelValue"
    @update:model-value="handleChange"
    :style="{ width: '120px' }"
  >
    <a-option
      v-for="m in methods"
      :key="m.value"
      :value="m.value"
      :label="m.label"
    >
      <span :style="{ color: m.color, fontWeight: 'bold' }">{{ m.label }}</span>
    </a-option>
  </a-select>
</template>

<script setup lang="ts">
defineProps<{
  modelValue: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

function handleChange(value: string | number | boolean | Record<string, any> | (string | number | boolean | Record<string, any>)[]) {
  emit('update:modelValue', value as string)
}

const methods = [
  { value: 'GET', label: 'GET', color: '#00b42a' },
  { value: 'POST', label: 'POST', color: '#165dff' },
  { value: 'PUT', label: 'PUT', color: '#ff7d00' },
  { value: 'DELETE', label: 'DELETE', color: '#f53f3f' },
  { value: 'PATCH', label: 'PATCH', color: '#722ed1' },
  { value: 'HEAD', label: 'HEAD', color: '#86909c' },
  { value: 'OPTIONS', label: 'OPTIONS', color: '#86909c' },
]
</script>

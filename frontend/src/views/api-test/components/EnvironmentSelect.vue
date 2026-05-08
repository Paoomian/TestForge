<template>
  <a-select
    :model-value="modelValue || undefined"
    placeholder="选择环境"
    allow-clear
    :style="{ width: '200px' }"
    @update:model-value="handleChange"
  >
    <a-option v-for="env in environments" :key="env.id" :value="env.id">
      <span>{{ env.name }}</span>
      <span v-if="env.base_url" style="color: var(--color-text-3); margin-left: 8px; font-size: 12px;">
        {{ env.base_url }}
      </span>
    </a-option>
  </a-select>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { getEnvironments } from '@/api/environment'
import type { Environment } from '@/api/apiTestCase'

const props = defineProps<{
  modelValue?: number | null
  projectId?: number | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: number | null): void
}>()

const environments = ref<Environment[]>([])

function handleChange(value: string | number | boolean | Record<string, any> | (string | number | boolean | Record<string, any>)[] | undefined) {
  emit('update:modelValue', (value as number) || null)
}

watch(() => props.projectId, async (pid) => {
  if (pid) {
    environments.value = await getEnvironments(pid)
  } else {
    environments.value = []
  }
}, { immediate: true })
</script>

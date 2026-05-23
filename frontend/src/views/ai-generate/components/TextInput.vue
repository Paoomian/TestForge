<template>
  <div class="text-input">
    <a-textarea
      :model-value="modelValue"
      @update:model-value="$emit('update:modelValue', $event)"
      placeholder="请输入功能描述、需求说明或测试点..."
      :max-length="10000"
      show-word-limit
      :auto-size="{ minRows: 10, maxRows: 20 }"
    />
    <div class="input-hint">
      <p>提示：详细描述功能需求，AI 将根据描述生成测试用例</p>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  modelValue: string
}>()

defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>

<style scoped>
.text-input {
  width: 100%;
}

.input-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #86909c;
}
</style>

<template>
  <div class="assertion-extract-tab">
    <a-tabs default-active-key="assertions" size="small">
      <a-tab-pane key="assertions">
        <template #title>
          断言
          <a-badge v-if="assertions.length > 0" :count="assertions.length" :max="99" />
        </template>
        <AssertionEditor
          :model-value="assertions"
          @update:model-value="$emit('update:assertions', $event)"
        />
      </a-tab-pane>

      <a-tab-pane key="extracts">
        <template #title>
          变量提取
          <a-badge v-if="extracts.length > 0" :count="extracts.length" :max="99" />
        </template>
        <ExtractEditor
          :model-value="extracts"
          @update:model-value="$emit('update:extracts', $event)"
        />
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<script setup lang="ts">
import type { AssertionItem, ExtractItem } from '@/api/apiTestCase'
import AssertionEditor from './AssertionEditor.vue'
import ExtractEditor from './ExtractEditor.vue'

defineProps<{
  assertions: AssertionItem[]
  extracts: ExtractItem[]
}>()

defineEmits<{
  (e: 'update:assertions', value: AssertionItem[]): void
  (e: 'update:extracts', value: ExtractItem[]): void
}>()
</script>

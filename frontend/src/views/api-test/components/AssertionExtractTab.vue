<template>
  <div class="assertion-extract-tab">
    <a-tabs default-active-key="assertions" size="small" :destroy-on-hide="false">
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

      <a-tab-pane key="data-rules">
        <template #title>
          数据规则
          <a-badge v-if="dataRules.length > 0" :count="dataRules.length" :max="99" />
        </template>
        <DataRuleEditor
          :model-value="dataRules"
          @update:model-value="$emit('update:dataRules', $event)"
        />
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<script setup lang="ts">
import type { AssertionItem, DataRuleItem } from '@/api/apiTestCase'
import AssertionEditor from './AssertionEditor.vue'
import DataRuleEditor from './DataRuleEditor.vue'

defineProps<{
  assertions: AssertionItem[]
  dataRules: DataRuleItem[]
}>()

defineEmits<{
  (e: 'update:assertions', value: AssertionItem[]): void
  (e: 'update:dataRules', value: DataRuleItem[]): void
}>()
</script>

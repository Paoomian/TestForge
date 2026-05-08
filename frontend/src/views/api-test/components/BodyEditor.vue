<template>
  <div class="body-editor">
    <a-radio-group
      :model-value="bodyType"
      @update:model-value="handleTypeChange"
      size="small"
      type="button"
    >
      <a-radio value="none">none</a-radio>
      <a-radio value="form-data">form-data</a-radio>
      <a-radio value="x-www-form-urlencoded">x-www-form-urlencoded</a-radio>
      <a-radio value="raw-json">JSON</a-radio>
      <a-radio value="raw-xml">XML</a-radio>
      <a-radio value="raw-text">Text</a-radio>
    </a-radio-group>

    <div style="margin-top: 12px;">
      <!-- form-data -->
      <KeyValueEditor
        v-if="bodyType === 'form-data'"
        :model-value="bodyForm"
        @update:model-value="handleBodyFormChange"
        key-placeholder="参数名"
        value-placeholder="参数值"
        add-text="添加表单字段"
      />

      <!-- x-www-form-urlencoded -->
      <KeyValueEditor
        v-else-if="bodyType === 'x-www-form-urlencoded'"
        :model-value="bodyForm"
        @update:model-value="handleBodyFormChange"
        key-placeholder="参数名"
        value-placeholder="参数值"
        add-text="添加参数"
      />

      <!-- raw types -->
      <div v-else-if="bodyType.startsWith('raw-')">
        <JsonEditor
          v-if="bodyType === 'raw-json'"
          :model-value="rawContent"
          @update:model-value="$emit('update:rawContent', $event)"
          height="300px"
          language="json"
        />
        <div v-else>
          <a-textarea
            :model-value="rawContent"
            @update:model-value="$emit('update:rawContent', $event)"
            :placeholder="bodyType === 'raw-xml' ? '输入XML内容' : '输入文本内容'"
            :auto-size="{ minRows: 8, maxRows: 20 }"
          />
        </div>
      </div>

      <!-- none -->
      <a-empty v-else description="该请求没有Body" />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { BodyFormItem } from '@/api/apiTestCase'
import type { KVRow } from './KeyValueEditor.vue'
import KeyValueEditor from './KeyValueEditor.vue'
import JsonEditor from '@/components/JsonEditor.vue'

defineProps<{
  bodyType: string
  bodyForm: BodyFormItem[]
  rawContent: string
}>()

const emit = defineEmits<{
  (e: 'update:bodyType', value: string): void
  (e: 'update:bodyForm', value: BodyFormItem[]): void
  (e: 'update:rawContent', value: string): void
}>()

function handleTypeChange(value: string | number | boolean) {
  emit('update:bodyType', value as string)
}

// 将KVRow转换为BodyFormItem
function handleBodyFormChange(rows: KVRow[]) {
  const bodyFormItems: BodyFormItem[] = rows.map(row => ({
    ...row,
    param_type: 'text' as const
  }))
  emit('update:bodyForm', bodyFormItems)
}
</script>

<style scoped>
.body-editor {
  width: 100%;
}
</style>

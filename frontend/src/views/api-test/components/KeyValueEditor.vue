<template>
  <div class="kv-editor">
    <a-table
      :data="rows"
      :pagination="false"
      size="small"
      :bordered="false"
    >
      <template #columns>
        <a-table-column title="" :width="50">
          <template #cell="{ record }">
            <a-checkbox v-model="record.enabled" />
          </template>
        </a-table-column>
        <a-table-column title="Key" :width="200">
          <template #cell="{ record }">
            <a-input
              v-model="record.key"
              size="small"
              :placeholder="keyPlaceholder"
              @change="emitChange"
            />
          </template>
        </a-table-column>
        <a-table-column title="Value">
          <template #cell="{ record }">
            <a-input
              v-model="record.value"
              size="small"
              :placeholder="valuePlaceholder"
              @change="emitChange"
            />
          </template>
        </a-table-column>
        <a-table-column title="描述" :width="180">
          <template #cell="{ record }">
            <a-input
              v-model="record.description"
              size="small"
              placeholder="描述（可选）"
              @change="emitChange"
            />
          </template>
        </a-table-column>
        <a-table-column title="" :width="50">
          <template #cell="{ rowIndex }">
            <a-button
              type="text"
              size="mini"
              status="danger"
              @click="removeRow(rowIndex)"
            >
              <template #icon><icon-delete /></template>
            </a-button>
          </template>
        </a-table-column>
      </template>
    </a-table>
    <a-button type="dashed" size="small" long @click="addRow" style="margin-top: 8px">
      <template #icon><icon-plus /></template>
      {{ addButtonText }}
    </a-button>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

export interface KVRow {
  enabled: boolean
  key: string
  value: string
  description?: string
  sort_order?: number
}

interface Props {
  modelValue: KVRow[]
  keyPlaceholder?: string
  valuePlaceholder?: string
  addButtonText?: string
}

const props = withDefaults(defineProps<Props>(), {
  keyPlaceholder: 'Key',
  valuePlaceholder: 'Value',
  addButtonText: '添加'
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: KVRow[]): void
}>()

const rows = ref<KVRow[]>(cloneRows(props.modelValue))

watch(() => props.modelValue, (val) => {
  rows.value = cloneRows(val)
}, { deep: true })

function cloneRows(arr: KVRow[]): KVRow[] {
  return (arr || []).map(r => ({ ...r }))
}

function emitChange() {
  emit('update:modelValue', rows.value.map((r, i) => ({ ...r, sort_order: i })))
}

function addRow() {
  rows.value.push({ enabled: true, key: '', value: '', description: '' })
  emitChange()
}

function removeRow(index: number) {
  rows.value.splice(index, 1)
  emitChange()
}
</script>

<style scoped>
.kv-editor :deep(.arco-table-th) {
  background-color: var(--color-fill-2);
  font-size: 12px;
  padding: 6px 8px;
}
.kv-editor :deep(.arco-table-td) {
  padding: 4px 8px;
}
.kv-editor :deep(.arco-table) {
  --color-neutral-3: transparent;
}
</style>

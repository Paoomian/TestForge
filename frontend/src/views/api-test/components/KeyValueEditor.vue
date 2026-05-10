<template>
  <div class="kv-editor">
    <!-- 表头 -->
    <div class="kv-header">
      <div class="kv-col-check"></div>
      <div class="kv-col-key">Key</div>
      <div class="kv-col-value">Value</div>
      <div class="kv-col-desc">描述</div>
      <div class="kv-col-action"></div>
    </div>
    <!-- 行 -->
    <div v-for="(row, index) in rows" :key="index" class="kv-row">
      <div class="kv-col-check">
        <a-checkbox v-model="row.enabled" @change="emitChange" />
      </div>
      <div class="kv-col-key">
        <a-input
          v-model="row.key"
          size="small"
          :placeholder="keyPlaceholder"
          @change="emitChange"
        />
      </div>
      <div class="kv-col-value">
        <a-input
          v-model="row.value"
          size="small"
          :placeholder="valuePlaceholder"
          @change="emitChange"
        />
      </div>
      <div class="kv-col-desc">
        <a-input
          v-model="row.description"
          size="small"
          placeholder="描述（可选）"
          @change="emitChange"
        />
      </div>
      <div class="kv-col-action">
        <a-button
          type="text"
          size="mini"
          status="danger"
          @click="removeRow(index)"
        >
          <template #icon><icon-delete /></template>
        </a-button>
      </div>
    </div>
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
const isInternalUpdate = ref(false)

watch(() => props.modelValue, (val) => {
  if (isInternalUpdate.value) {
    isInternalUpdate.value = false
    return
  }
  rows.value = cloneRows(val)
}, { deep: true })

function cloneRows(arr: KVRow[]): KVRow[] {
  return (arr || []).map(r => ({ ...r }))
}

function emitChange() {
  isInternalUpdate.value = true
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
.kv-editor {
  width: 100%;
}

.kv-header {
  display: flex;
  align-items: center;
  padding: 6px 8px;
  background-color: var(--color-fill-2);
  border-bottom: 1px solid var(--color-neutral-3);
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-2);
}

.kv-row {
  display: flex;
  align-items: center;
  padding: 4px 8px;
  border-bottom: 1px solid var(--color-neutral-3);
}

.kv-row:last-of-type {
  border-bottom: none;
}

.kv-col-check {
  width: 40px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.kv-col-key {
  width: 200px;
  flex-shrink: 0;
  padding-right: 8px;
}

.kv-col-value {
  flex: 1;
  min-width: 0;
  padding-right: 8px;
}

.kv-col-desc {
  width: 180px;
  flex-shrink: 0;
  padding-right: 8px;
}

.kv-col-action {
  width: 40px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>

<template>
  <div class="data-rule-editor">
    <div class="rule-list">
      <div v-for="(item, index) in rules" :key="index" class="rule-item">
        <DataRuleCard
          :item="item"
          @update:name="updateField(index, 'name', $event)"
          @update:rule_type="handleRuleTypeChange(index, $event)"
          @update:enabled="updateField(index, 'enabled', $event)"
          @update:description="updateField(index, 'description', $event)"
          @update:default_value="updateField(index, 'default_value', $event)"
          @update:source="updateField(index, 'source', $event)"
          @update:expression="updateField(index, 'expression', $event)"
          @update:static_value="updateField(index, 'static_value', $event)"
          @update:generator="updateField(index, 'generator', $event)"
          @update:generator_params="updateParams(index, 'generator_params', $event)"
          @update:source_variable="updateField(index, 'source_variable', $event)"
          @update:transform_type="updateField(index, 'transform_type', $event)"
          @update:transform_params="updateParams(index, 'transform_params', $event)"
          @update:condition_variable="updateField(index, 'condition_variable', $event)"
          @update:condition_operator="updateField(index, 'condition_operator', $event)"
          @update:condition_value="updateField(index, 'condition_value', $event)"
          @update:true_value="updateField(index, 'true_value', $event)"
          @update:false_value="updateField(index, 'false_value', $event)"
          @remove="removeRule(index)"
        />
      </div>
    </div>

    <a-button type="dashed" long @click="addRule" style="margin-top: 8px;">
      <template #icon><icon-plus /></template>
      添加数据规则
    </a-button>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { DataRuleItem } from '@/api/apiTestCase'
import DataRuleCard from './DataRuleCard.vue'

const props = defineProps<{
  modelValue: DataRuleItem[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: DataRuleItem[]): void
}>()

const rules = ref<DataRuleItem[]>([])

// 监听props变化，同步到本地
watch(() => props.modelValue, (newValue) => {
  if (JSON.stringify(newValue) !== JSON.stringify(rules.value)) {
    rules.value = (newValue || []).map(r => ({ ...r }))
  }
}, { immediate: true })

function emitChange() {
  emit('update:modelValue', rules.value.map((r, i) => ({ ...r, sort_order: i })))
}

function updateField(index: number, field: string, value: any) {
  ;(rules.value[index] as any)[field] = value
  emitChange()
}

function updateParams(index: number, field: 'generator_params' | 'transform_params', params: Record<string, any>) {
  const existing = rules.value[index][field] || {}
  rules.value[index][field] = { ...existing, ...params }
  emitChange()
}

function handleRuleTypeChange(index: number, ruleType: string) {
  const rule = rules.value[index]
  rule.rule_type = ruleType as DataRuleItem['rule_type']
  // 切换类型时重置相关字段
  rule.source = undefined
  rule.expression = undefined
  rule.static_value = undefined
  rule.generator = undefined
  rule.generator_params = undefined
  rule.source_variable = undefined
  rule.transform_type = undefined
  rule.transform_params = undefined
  rule.condition_variable = undefined
  rule.condition_operator = undefined
  rule.condition_value = undefined
  rule.true_value = undefined
  rule.false_value = undefined
  // 设置默认值
  if (ruleType === 'extract') {
    rule.source = 'jsonpath'
  } else if (ruleType === 'generate') {
    rule.generator = 'timestamp'
  } else if (ruleType === 'transform') {
    rule.transform_type = 'substring'
  } else if (ruleType === 'conditional') {
    rule.condition_operator = 'equals'
  }
  emitChange()
}

function addRule() {
  rules.value.push({
    name: '',
    rule_type: 'extract',
    enabled: true,
    description: '',
    default_value: '',
    source: 'jsonpath',
    expression: '',
  })
  emitChange()
}

function removeRule(index: number) {
  rules.value.splice(index, 1)
  emitChange()
}
</script>

<style scoped>
.data-rule-editor {
  width: 100%;
}

.rule-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rule-item {
  width: 100%;
}
</style>

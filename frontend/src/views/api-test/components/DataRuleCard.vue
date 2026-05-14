<template>
  <a-card :bordered="true" size="small">
    <template #extra>
      <a-space>
        <a-switch
          :model-value="item.enabled !== false"
          size="small"
          @change="$emit('update:enabled', $event)"
        />
        <a-button
          type="text"
          size="small"
          status="danger"
          @click="$emit('remove')"
        >
          <template #icon><icon-delete /></template>
        </a-button>
      </a-space>
    </template>

    <a-form :model="item" layout="vertical">
      <!-- 第一行：规则类型 + 变量名 -->
      <a-row :gutter="16">
        <a-col :span="6">
          <a-form-item label="规则类型">
            <a-select
              :model-value="item.rule_type"
              size="small"
              @change="$emit('update:rule_type', $event)"
            >
              <a-option value="extract">从响应提取</a-option>
              <a-option value="static">设置静态值</a-option>
              <a-option value="generate">生成数据</a-option>
              <a-option value="transform">数据变换</a-option>
              <a-option value="conditional">条件赋值</a-option>
            </a-select>
          </a-form-item>
        </a-col>
        <a-col :span="6">
          <a-form-item label="变量名">
            <a-input
              :model-value="item.name"
              placeholder="例如: token"
              size="small"
              @input="$emit('update:name', $event)"
            />
          </a-form-item>
        </a-col>
        <a-col :span="8">
          <a-form-item label="描述">
            <a-input
              :model-value="item.description || ''"
              placeholder="可选，说明此规则用途"
              size="small"
              @input="$emit('update:description', $event)"
            />
          </a-form-item>
        </a-col>
        <a-col :span="4">
          <a-form-item label="默认值">
            <a-input
              :model-value="item.default_value || ''"
              placeholder="可选"
              size="small"
              @input="$emit('update:default_value', $event)"
            />
          </a-form-item>
        </a-col>
      </a-row>

      <!-- 从响应提取 -->
      <template v-if="item.rule_type === 'extract'">
        <a-row :gutter="16">
          <a-col :span="4">
            <a-form-item label="来源">
              <a-select
                :model-value="item.source || 'jsonpath'"
                size="small"
                @change="$emit('update:source', $event)"
              >
                <a-option value="jsonpath">JSONPath</a-option>
                <a-option value="regex">正则</a-option>
                <a-option value="header">响应头</a-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item :label="getExprLabel(item.source || 'jsonpath')">
              <a-input
                :model-value="item.expression || ''"
                :placeholder="getExprPlaceholder(item.source || 'jsonpath')"
                size="small"
                @input="$emit('update:expression', $event)"
              />
            </a-form-item>
          </a-col>
        </a-row>
      </template>

      <!-- 设置静态值 -->
      <template v-if="item.rule_type === 'static'">
        <a-row :gutter="16">
          <a-col :span="16">
            <a-form-item label="值">
              <a-input
                :model-value="item.static_value || ''"
                placeholder="输入静态值，支持 {{变量}} 引用"
                size="small"
                @input="$emit('update:static_value', $event)"
              />
            </a-form-item>
          </a-col>
        </a-row>
      </template>

      <!-- 生成数据 -->
      <template v-if="item.rule_type === 'generate'">
        <a-row :gutter="16">
          <a-col :span="6">
            <a-form-item label="生成器类型">
              <a-select
                :model-value="item.generator || 'timestamp'"
                size="small"
                @change="$emit('update:generator', $event)"
              >
                <a-option value="timestamp">时间戳</a-option>
                <a-option value="uuid">UUID</a-option>
                <a-option value="random_int">随机整数</a-option>
                <a-option value="random_string">随机字符串</a-option>
                <a-option value="now">当前时间</a-option>
              </a-select>
            </a-form-item>
          </a-col>
          <!-- 随机整数参数 -->
          <template v-if="item.generator === 'random_int'">
            <a-col :span="4">
              <a-form-item label="最小值">
                <a-input-number
                  :model-value="(item.generator_params || {}).min ?? 1"
                  size="small"
                  style="width: 100%"
                  @change="updateGeneratorParam('min', $event)"
                />
              </a-form-item>
            </a-col>
            <a-col :span="4">
              <a-form-item label="最大值">
                <a-input-number
                  :model-value="(item.generator_params || {}).max ?? 999999"
                  size="small"
                  style="width: 100%"
                  @change="updateGeneratorParam('max', $event)"
                />
              </a-form-item>
            </a-col>
          </template>
          <!-- 随机字符串参数 -->
          <template v-if="item.generator === 'random_string'">
            <a-col :span="4">
              <a-form-item label="长度">
                <a-input-number
                  :model-value="(item.generator_params || {}).length ?? 16"
                  :min="1"
                  :max="256"
                  size="small"
                  style="width: 100%"
                  @change="updateGeneratorParam('length', $event)"
                />
              </a-form-item>
            </a-col>
          </template>
          <!-- 当前时间参数 -->
          <template v-if="item.generator === 'now'">
            <a-col :span="8">
              <a-form-item label="日期格式">
                <a-input
                  :model-value="(item.generator_params || {}).format || ''"
                  placeholder="留空则输出ISO格式，如 %Y-%m-%d %H:%M:%S"
                  size="small"
                  @input="updateGeneratorParam('format', $event)"
                />
              </a-form-item>
            </a-col>
          </template>
        </a-row>
      </template>

      <!-- 数据变换 -->
      <template v-if="item.rule_type === 'transform'">
        <a-row :gutter="16">
          <a-col :span="6">
            <a-form-item label="源变量">
              <a-input
                :model-value="item.source_variable || ''"
                placeholder="变量名或 {{变量名}}"
                size="small"
                @input="$emit('update:source_variable', $event)"
              />
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="变换类型">
              <a-select
                :model-value="item.transform_type || 'substring'"
                size="small"
                @change="$emit('update:transform_type', $event)"
              >
                <a-option value="substring">截取</a-option>
                <a-option value="concat">拼接</a-option>
                <a-option value="replace">替换</a-option>
                <a-option value="upper">转大写</a-option>
                <a-option value="lower">转小写</a-option>
                <a-option value="trim">去空格</a-option>
                <a-option value="to_int">转整数</a-option>
                <a-option value="to_string">转字符串</a-option>
                <a-option value="format_date">日期格式化</a-option>
              </a-select>
            </a-form-item>
          </a-col>
          <!-- substring 参数 -->
          <template v-if="item.transform_type === 'substring'">
            <a-col :span="3">
              <a-form-item label="起始位置">
                <a-input-number
                  :model-value="(item.transform_params || {}).start ?? 0"
                  size="small"
                  style="width: 100%"
                  @change="updateTransformParam('start', $event)"
                />
              </a-form-item>
            </a-col>
            <a-col :span="3">
              <a-form-item label="结束位置">
                <a-input-number
                  :model-value="(item.transform_params || {}).end"
                  placeholder="留空到末尾"
                  size="small"
                  style="width: 100%"
                  @change="updateTransformParam('end', $event)"
                />
              </a-form-item>
            </a-col>
          </template>
          <!-- concat 参数 -->
          <template v-if="item.transform_type === 'concat'">
            <a-col :span="6">
              <a-form-item label="拼接内容">
                <a-input
                  :model-value="(item.transform_params || {}).append || ''"
                  placeholder="字符串或 {{变量}}"
                  size="small"
                  @input="updateTransformParam('append', $event)"
                />
              </a-form-item>
            </a-col>
          </template>
          <!-- replace 参数 -->
          <template v-if="item.transform_type === 'replace'">
            <a-col :span="3">
              <a-form-item label="查找">
                <a-input
                  :model-value="(item.transform_params || {}).old || ''"
                  placeholder="被替换"
                  size="small"
                  @input="updateTransformParam('old', $event)"
                />
              </a-form-item>
            </a-col>
            <a-col :span="3">
              <a-form-item label="替换为">
                <a-input
                  :model-value="(item.transform_params || {}).new || ''"
                  placeholder="替换为"
                  size="small"
                  @input="updateTransformParam('new', $event)"
                />
              </a-form-item>
            </a-col>
          </template>
          <!-- format_date 参数 -->
          <template v-if="item.transform_type === 'format_date'">
            <a-col :span="3">
              <a-form-item label="输入格式">
                <a-input
                  :model-value="(item.transform_params || {}).input_format || ''"
                  placeholder="%Y-%m-%d"
                  size="small"
                  @input="updateTransformParam('input_format', $event)"
                />
              </a-form-item>
            </a-col>
            <a-col :span="3">
              <a-form-item label="输出格式">
                <a-input
                  :model-value="(item.transform_params || {}).output_format || ''"
                  placeholder="%Y/%m/%d"
                  size="small"
                  @input="updateTransformParam('output_format', $event)"
                />
              </a-form-item>
            </a-col>
          </template>
        </a-row>
      </template>

      <!-- 条件赋值 -->
      <template v-if="item.rule_type === 'conditional'">
        <a-row :gutter="16">
          <a-col :span="5">
            <a-form-item label="条件变量">
              <a-input
                :model-value="item.condition_variable || ''"
                placeholder="变量名或 {{变量名}}"
                size="small"
                @input="$emit('update:condition_variable', $event)"
              />
            </a-form-item>
          </a-col>
          <a-col :span="4">
            <a-form-item label="运算符">
              <a-select
                :model-value="item.condition_operator || 'equals'"
                size="small"
                @change="$emit('update:condition_operator', $event)"
              >
                <a-option value="equals">等于</a-option>
                <a-option value="not_equals">不等于</a-option>
                <a-option value="contains">包含</a-option>
                <a-option value="is_empty">为空</a-option>
                <a-option value="is_not_empty">不为空</a-option>
                <a-option value="greater_than">大于</a-option>
                <a-option value="less_than">小于</a-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="5" v-if="!['is_empty', 'is_not_empty'].includes(item.condition_operator || '')">
            <a-form-item label="条件值">
              <a-input
                :model-value="item.condition_value || ''"
                placeholder="比较的值"
                size="small"
                @input="$emit('update:condition_value', $event)"
              />
            </a-form-item>
          </a-col>
          <a-col :span="5">
            <a-form-item label="条件为真时">
              <a-input
                :model-value="item.true_value || ''"
                placeholder="值或 {{变量}}"
                size="small"
                @input="$emit('update:true_value', $event)"
              />
            </a-form-item>
          </a-col>
          <a-col :span="5">
            <a-form-item label="条件为假时">
              <a-input
                :model-value="item.false_value || ''"
                placeholder="值或 {{变量}}"
                size="small"
                @input="$emit('update:false_value', $event)"
              />
            </a-form-item>
          </a-col>
        </a-row>
      </template>
    </a-form>
  </a-card>
</template>

<script setup lang="ts">
import type { DataRuleItem } from '@/api/apiTestCase'

defineProps<{
  item: DataRuleItem
}>()

const emit = defineEmits<{
  (e: 'update:name', value: string): void
  (e: 'update:rule_type', value: string): void
  (e: 'update:enabled', value: boolean): void
  (e: 'update:description', value: string): void
  (e: 'update:default_value', value: string): void
  (e: 'update:source', value: string): void
  (e: 'update:expression', value: string): void
  (e: 'update:static_value', value: string): void
  (e: 'update:generator', value: string): void
  (e: 'update:generator_params', value: Record<string, any>): void
  (e: 'update:source_variable', value: string): void
  (e: 'update:transform_type', value: string): void
  (e: 'update:transform_params', value: Record<string, any>): void
  (e: 'update:condition_variable', value: string): void
  (e: 'update:condition_operator', value: string): void
  (e: 'update:condition_value', value: string): void
  (e: 'update:true_value', value: string): void
  (e: 'update:false_value', value: string): void
  (e: 'remove'): void
}>()

function updateGeneratorParam(key: string, value: any) {
  emit('update:generator_params', { [key]: value })
}

function updateTransformParam(key: string, value: any) {
  emit('update:transform_params', { [key]: value })
}

function getExprLabel(source: string) {
  const map: Record<string, string> = {
    jsonpath: 'JSONPath表达式',
    regex: '正则表达式',
    header: '响应头名称',
  }
  return map[source] || '表达式'
}

function getExprPlaceholder(source: string) {
  const map: Record<string, string> = {
    jsonpath: '$.data.access_token',
    regex: '"token":"([^"]+)"',
    header: 'X-Request-Id',
  }
  return map[source] || ''
}
</script>

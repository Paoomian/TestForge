<template>
  <div class="script-tab">
    <a-tabs default-active-key="pre" size="small" :destroy-on-hide="false">
      <a-tab-pane key="pre" title="前置脚本">
        <p style="color: var(--color-text-3); font-size: 12px; margin-bottom: 8px;">
          在请求发送前执行的JavaScript脚本，可用于动态修改请求参数
        </p>
        <JsonEditor
          :model-value="setupScript"
          @update:model-value="$emit('update:setupScript', $event)"
          height="250px"
          language="javascript"
        />
      </a-tab-pane>

      <a-tab-pane key="post" title="后置脚本">
        <p style="color: var(--color-text-3); font-size: 12px; margin-bottom: 8px;">
          在请求完成后执行的JavaScript脚本，可用于提取响应数据或执行自定义断言
        </p>
        <JsonEditor
          :model-value="teardownScript"
          @update:model-value="$emit('update:teardownScript', $event)"
          height="250px"
          language="javascript"
        />
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<script setup lang="ts">
import JsonEditor from '@/components/JsonEditor.vue'

defineProps<{
  setupScript: string
  teardownScript: string
}>()

defineEmits<{
  (e: 'update:setupScript', value: string): void
  (e: 'update:teardownScript', value: string): void
}>()
</script>

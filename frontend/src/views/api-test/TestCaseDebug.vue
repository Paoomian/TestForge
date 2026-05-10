<template>
  <div class="test-case-debug">
    <!-- 顶部导航 -->
    <div class="debug-header">
      <a-button type="text" @click="goBack">
        <template #icon><icon-left /></template>
        返回
      </a-button>
      <div class="header-info" v-if="caseData">
        <span class="case-number">{{ caseData.case_number }}</span>
        <span class="case-name">{{ caseData.name }}</span>
        <a-tag :color="methodColor" size="small">{{ caseData.method }}</a-tag>
      </div>
    </div>

    <!-- 主体 -->
    <div class="debug-body" v-if="caseData">
      <div class="left-panel">
        <CaseConfigPanel :case-data="caseData" />
      </div>
      <div class="right-panel">
        <DebugResultPanel :case-data="caseData" />
      </div>
    </div>

    <!-- 加载中 -->
    <div v-else-if="loading" class="debug-loading">
      <a-spin :size="32" />
      <p>加载用例数据...</p>
    </div>

    <!-- 加载失败 -->
    <div v-else class="debug-error">
      <a-result status="404" subtitle="用例不存在或加载失败">
        <template #extra>
          <a-button type="primary" @click="goBack">返回列表</a-button>
        </template>
      </a-result>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { getTestCase } from '@/api/apiTestCase'
import type { APITestCase } from '@/api/apiTestCase'
import CaseConfigPanel from './components/CaseConfigPanel.vue'
import DebugResultPanel from './components/DebugResultPanel.vue'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const caseData = ref<APITestCase | null>(null)

const methodColors: Record<string, string> = {
  GET: 'blue', POST: 'green', PUT: 'orange', DELETE: 'red', PATCH: 'purple'
}
const methodColor = computed(() => caseData.value ? (methodColors[caseData.value.method] || 'gray') : 'gray')

const goBack = () => {
  router.push({ name: 'api-test-manage' })
}

onMounted(async () => {
  const caseId = Number(route.params.caseId)
  if (!caseId) {
    loading.value = false
    return
  }

  try {
    caseData.value = await getTestCase(caseId)
  } catch (e: any) {
    Message.error('加载用例失败')
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.test-case-debug {
  height: calc(100vh - var(--header-height));
  display: flex;
  flex-direction: column;
  background: var(--gray-50);
  margin: calc(-1 * var(--content-padding));
}

.debug-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: white;
  border-bottom: 1px solid var(--gray-200);
  flex-shrink: 0;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.case-number {
  color: var(--gray-500);
  font-size: var(--font-size-sm);
}

.case-name {
  font-weight: var(--font-weight-semibold);
  color: var(--gray-800);
}

.debug-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.left-panel {
  width: 42%;
  min-width: 360px;
  border-right: 1px solid var(--gray-200);
  background: white;
  overflow-y: auto;
}

.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.debug-loading, .debug-error {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--gray-400);
}

.debug-loading p {
  margin-top: 12px;
}
</style>

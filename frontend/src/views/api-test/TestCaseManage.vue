<template>
  <div class="test-case-manage">
    <a-layout style="height: 100%">
      <!-- 左侧项目树 -->
      <a-layout-sider
        :width="300"
        class="tree-sider"
      >
        <div class="tree-header">
          <h3 class="tree-title">项目与模块</h3>
        </div>
        <div class="tree-content">
          <ProjectModuleTree
            ref="treeRef"
            @select="handleTreeSelect"
          />
        </div>
      </a-layout-sider>

      <!-- 右侧用例列表 -->
      <a-layout-content class="list-content">
        <TestCaseList
          ref="listRef"
          :project-id="selectedProjectId"
          :module="selectedModule"
          @create="handleCreate"
          @edit="handleEdit"
          @batch-run="handleBatchRun"
        />
      </a-layout-content>
    </a-layout>

    <!-- 用例编辑抽屉 -->
    <TestCaseDrawer
      v-model:visible="drawerVisible"
      :edit-data="editingCase"
      :default-project-id="selectedProjectId"
      @success="handleDrawerSuccess"
    />

    <!-- 批量执行抽屉 -->
    <BatchRunDrawer
      v-model:visible="batchRunDrawerVisible"
      :cases="batchRunCases"
      :project-id="selectedProjectId"
      @success="handleBatchRunSuccess"
    />
  </div>
</template>

<script lang="ts">
export default {
  name: 'TestCaseManage'
}
</script>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import ProjectModuleTree from './components/ProjectModuleTree.vue'
import TestCaseList from './components/TestCaseList.vue'
import TestCaseDrawer from './components/TestCaseDrawer.vue'
import BatchRunDrawer from './components/BatchRunDrawer.vue'
import type { APITestCase } from '@/api/apiTestCase'

const router = useRouter()
const treeRef = ref()
const listRef = ref()

const selectedProjectId = ref<number>()
const selectedModule = ref<string>()

const drawerVisible = ref(false)
const editingCase = ref<APITestCase | null>(null)

// 批量执行
const batchRunDrawerVisible = ref(false)
const batchRunCases = ref<APITestCase[]>([])

const handleTreeSelect = (data: { projectId?: number; module?: string }) => {
  selectedProjectId.value = data.projectId
  selectedModule.value = data.module || undefined
}

const handleCreate = () => {
  editingCase.value = null
  drawerVisible.value = true
}

const handleEdit = (record: APITestCase) => {
  editingCase.value = record
  drawerVisible.value = true
}

const handleDrawerSuccess = () => {
  if (listRef.value) {
    listRef.value.refresh()
  }
  if (treeRef.value) {
    treeRef.value.refresh()
  }
}

const handleBatchRun = (cases: APITestCase[]) => {
  batchRunCases.value = cases
  batchRunDrawerVisible.value = true
}

const handleBatchRunSuccess = (runId: number) => {
  // 跳转到任务详情页
  router.push({ name: 'api-batch-task-detail', params: { taskId: runId } })
}
</script>

<style scoped>
.test-case-manage {
  height: calc(100vh - var(--header-height));
  background: var(--gray-50);
  margin: calc(-1 * var(--content-padding));
}

.tree-sider {
  background: white !important;
  border-right: 1px solid rgba(224, 212, 252, 0.25) !important;
  box-shadow: 2px 0 8px rgba(99, 102, 241, 0.03);
}

.tree-header {
  padding: 20px 16px 12px;
  border-bottom: 1px solid rgba(224, 212, 252, 0.2);
}

.tree-title {
  margin: 0;
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--gray-800);
}

.tree-content {
  padding: 12px 8px;
  overflow-y: auto;
  height: calc(100% - 60px);
}

.list-content {
  padding: var(--content-padding);
  background: var(--gray-50);
  display: flex;
  flex-direction: column;
}
</style>

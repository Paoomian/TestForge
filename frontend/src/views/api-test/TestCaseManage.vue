<template>
  <div class="test-case-manage">
    <a-layout style="height: 100%">
      <!-- 左侧项目树 -->
      <a-layout-sider
        :width="300"
        :style="{ background: 'var(--color-bg-2)', borderRight: '1px solid var(--color-border)' }"
      >
        <div style="padding: 16px">
          <h3 style="margin-bottom: 16px">项目与模块</h3>
          <ProjectModuleTree
            ref="treeRef"
            @select="handleTreeSelect"
          />
        </div>
      </a-layout-sider>

      <!-- 右侧用例列表 -->
      <a-layout-content style="padding: 16px">
        <TestCaseList
          ref="listRef"
          :project-id="selectedProjectId"
          :module="selectedModule"
          @create="handleCreate"
          @edit="handleEdit"
          @view-history="handleViewHistory"
        />
      </a-layout-content>
    </a-layout>

    <!-- 用例编辑抽屉 -->
    <TestCaseDrawer
      v-model:visible="drawerVisible"
      :edit-data="editingCase"
      @success="handleDrawerSuccess"
    />

    <!-- 历史版本弹窗 -->
    <a-modal
      v-model:visible="historyVisible"
      title="历史版本"
      width="800px"
      :footer="false"
    >
      <a-table
        :columns="historyColumns"
        :data="historyData"
        :loading="historyLoading"
        :pagination="false"
      >
        <template #version="{ record }">
          <a-tag>v{{ record.version }}</a-tag>
        </template>
        <template #actions="{ record }">
          <a-space>
            <a-button type="text" size="small" @click="handleViewSnapshot(record)">
              查看
            </a-button>
            <a-popconfirm
              content="确定要回滚到此版本吗？"
              @ok="handleRollback(record)"
            >
              <a-button type="text" size="small">
                回滚
              </a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </a-table>
    </a-modal>

    <!-- 快照查看弹窗 -->
    <a-modal
      v-model:visible="snapshotVisible"
      title="版本快照"
      width="800px"
      :footer="false"
    >
      <JsonEditor
        v-model="snapshotJson"
        height="500px"
        :readonly="true"
      />
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Message } from '@arco-design/web-vue'
import ProjectModuleTree from './components/ProjectModuleTree.vue'
import TestCaseList from './components/TestCaseList.vue'
import TestCaseDrawer from './components/TestCaseDrawer.vue'
import JsonEditor from '@/components/JsonEditor.vue'
import { getHistories, rollbackVersion } from '@/api/apiTestCase'
import type { APITestCase, APITestCaseHistory } from '@/api/apiTestCase'

const treeRef = ref()
const listRef = ref()

const selectedProjectId = ref<number>()
const selectedModule = ref<string>()

const drawerVisible = ref(false)
const editingCase = ref<APITestCase | null>(null)

const historyVisible = ref(false)
const historyLoading = ref(false)
const historyData = ref<APITestCaseHistory[]>([])
const currentHistoryCase = ref<APITestCase | null>(null)

const snapshotVisible = ref(false)
const snapshotJson = ref('{}')

const historyColumns = [
  { title: '版本', dataIndex: 'version', slotName: 'version', width: 100 },
  { title: '变更说明', dataIndex: 'change_description', width: 200 },
  { title: '变更时间', dataIndex: 'created_at', width: 180 },
  { title: '操作', slotName: 'actions', width: 150 }
]

const handleTreeSelect = (data: { projectId?: number; module?: string }) => {
  selectedProjectId.value = data.projectId
  selectedModule.value = data.module
  if (listRef.value) {
    listRef.value.refresh()
  }
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

const handleViewHistory = async (record: APITestCase) => {
  currentHistoryCase.value = record
  historyVisible.value = true
  historyLoading.value = true

  try {
    historyData.value = await getHistories(record.id)
  } catch (error) {
    Message.error('加载历史版本失败')
  } finally {
    historyLoading.value = false
  }
}

const handleViewSnapshot = (record: APITestCaseHistory) => {
  snapshotJson.value = JSON.stringify(record.snapshot, null, 2)
  snapshotVisible.value = true
}

const handleRollback = async (record: APITestCaseHistory) => {
  if (!currentHistoryCase.value) return

  try {
    await rollbackVersion(currentHistoryCase.value.id, record.version)
    Message.success('回滚成功')
    historyVisible.value = false
    if (listRef.value) {
      listRef.value.refresh()
    }
  } catch (error) {
    Message.error('回滚失败')
  }
}
</script>

<style scoped>
.test-case-manage {
  height: calc(100vh - 60px);
  background: var(--color-bg-1);
}
</style>

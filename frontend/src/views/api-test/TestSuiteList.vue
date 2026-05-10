<template>
  <div class="test-suite-list">
    <!-- 搜索栏 -->
    <a-card :bordered="false" style="margin-bottom: 16px">
      <a-space wrap>
        <a-input
          v-model="searchForm.keyword"
          placeholder="搜索任务名称"
          style="width: 200px"
          allow-clear
          @press-enter="handleSearch"
        >
          <template #prefix><icon-search /></template>
        </a-input>
        <a-button type="primary" @click="handleSearch">
          <template #icon><icon-search /></template>
          搜索
        </a-button>
        <a-button @click="handleReset">
          <template #icon><icon-refresh /></template>
          重置
        </a-button>
      </a-space>
    </a-card>

    <!-- 操作栏 -->
    <a-card :bordered="false" style="margin-bottom: 16px">
      <a-button type="primary" @click="handleCreate">
        <template #icon><icon-plus /></template>
        新建任务
      </a-button>
    </a-card>

    <!-- 卡片列表 -->
    <div class="suite-cards">
      <a-row :gutter="[12, 12]">
        <a-col :span="6" v-for="item in tableData" :key="item.id">
          <a-card hoverable class="suite-card" size="small">
            <div class="card-header">
              <a-tag size="small" color="arcoblue">{{ item.project_name || '未分类' }}</a-tag>
              <a-dropdown>
                <a-button type="text" size="mini">
                  <template #icon><icon-more /></template>
                </a-button>
                <template #content>
                  <a-doption @click="handleEdit(item)">编辑</a-doption>
                  <a-doption @click="handleCopy(item)">复制</a-doption>
                  <a-doption class="danger" @click="handleDelete(item)">删除</a-doption>
                </template>
              </a-dropdown>
            </div>

            <div class="card-body">
              <div class="suite-name">{{ item.name }}</div>
              <p v-if="item.description" class="suite-desc">{{ item.description }}</p>

              <div class="suite-meta">
                <span class="meta-item">
                  <icon-file /> {{ item.case_count }}
                </span>
                <span class="meta-item" v-if="item.environment_name">
                  <icon-desktop /> {{ item.environment_name }}
                </span>
                <span class="meta-item">
                  <icon-swap /> {{ item.concurrency === 1 ? '串行' : `${item.concurrency}并发` }}
                </span>
              </div>

              <div class="suite-tags" v-if="item.tags?.length">
                <a-tag v-for="tag in item.tags" :key="tag" size="small" color="gray">{{ tag }}</a-tag>
              </div>
            </div>

            <template #actions>
              <a-button type="primary" size="mini" @click="handleRun(item)">
                <template #icon><icon-play-arrow /></template>
                运行
              </a-button>
              <a-button size="mini" @click="handleEdit(item)">
                <template #icon><icon-edit /></template>
              </a-button>
            </template>
          </a-card>
        </a-col>
      </a-row>

      <!-- 空状态 -->
      <a-empty v-if="!loading && tableData.length === 0" description="暂无任务配置">
        <a-button type="primary" @click="handleCreate">新建任务</a-button>
      </a-empty>
    </div>

    <!-- 分页 -->
    <div v-if="pagination.total > pagination.pageSize" class="pagination-wrapper">
      <a-pagination
        v-model:current="pagination.current"
        :total="pagination.total"
        :page-size="pagination.pageSize"
        show-total
        @change="handlePageChange"
      />
    </div>

    <!-- 编辑抽屉 -->
    <TestSuiteDrawer
      v-model:visible="drawerVisible"
      :edit-data="editingSuite"
      :project-id="selectedProjectId"
      @success="handleDrawerSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { getTestSuites, deleteTestSuite, copyTestSuite, runTestSuite } from '@/api/testSuite'
import type { TestSuiteListItem } from '@/api/testSuite'
import TestSuiteDrawer from './components/TestSuiteDrawer.vue'

const router = useRouter()
const loading = ref(false)
const tableData = ref<TestSuiteListItem[]>([])

// 从父组件或路由获取项目ID
const selectedProjectId = ref<number>()

const searchForm = reactive({
  keyword: ''
})

const pagination = reactive({
  current: 1,
  pageSize: 9,
  total: 0
})

const drawerVisible = ref(false)
const editingSuite = ref<TestSuiteListItem | null>(null)

const loadData = async () => {
  loading.value = true
  try {
    const res = await getTestSuites({
      project_id: selectedProjectId.value,
      keyword: searchForm.keyword || undefined,
      page: pagination.current,
      page_size: pagination.pageSize
    })
    tableData.value = res.items
    pagination.total = res.total
  } catch (e) {
    Message.error('加载任务列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.current = 1
  loadData()
}

const handleReset = () => {
  searchForm.keyword = ''
  handleSearch()
}

const handlePageChange = (page: number) => {
  pagination.current = page
  loadData()
}

const handleCreate = () => {
  editingSuite.value = null
  drawerVisible.value = true
}

const handleEdit = (record: TestSuiteListItem) => {
  editingSuite.value = record
  drawerVisible.value = true
}

const handleCopy = async (record: TestSuiteListItem) => {
  try {
    await copyTestSuite(record.id)
    Message.success('复制成功')
    loadData()
  } catch (e) {
    Message.error('复制失败')
  }
}

const handleDelete = async (record: TestSuiteListItem) => {
  try {
    await deleteTestSuite(record.id)
    Message.success('删除成功')
    loadData()
  } catch (e) {
    Message.error('删除失败')
  }
}

const handleRun = async (record: TestSuiteListItem) => {
  try {
    const res = await runTestSuite(record.id)
    Message.success('执行任务已创建')
    // 跳转到任务详情
    router.push({ name: 'api-batch-task-detail', params: { taskId: res.id } })
  } catch (e: any) {
    Message.error(e?.message || '执行失败')
  }
}

const handleDrawerSuccess = () => {
  loadData()
}

onMounted(() => {
  loadData()
})

defineExpose({
  refresh: loadData,
  setProjectId: (id: number) => {
    selectedProjectId.value = id
    loadData()
  }
})
</script>

<style scoped>
.test-suite-list {
  height: 100%;
}

.suite-cards {
  min-height: 200px;
}

.suite-card {
  height: 100%;
  transition: all 0.2s;
}

.suite-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.card-body {
  min-height: 60px;
}

.suite-name {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.suite-desc {
  color: var(--color-text-3);
  font-size: 12px;
  margin-bottom: 8px;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.suite-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 8px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--color-text-3);
}

.suite-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

:deep(.danger) {
  color: var(--color-danger-6);
}
</style>

<template>
  <div class="project-list">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="page-header-info">
        <h2 class="page-title">项目列表</h2>
        <p class="page-desc">管理和组织您的测试项目</p>
      </div>
      <a-button type="primary" @click="showCreateModal = true">
        <template #icon>
          <icon-plus />
        </template>
        创建项目
      </a-button>
    </div>

    <!-- 项目表格 -->
    <a-card :bordered="false" class="table-card">
      <a-table :columns="columns" :data="projects" :loading="loading" :bordered="false">
        <template #name="{ record }">
          <a-link class="project-name-link">{{ record.name }}</a-link>
        </template>
        <template #description="{ record }">
          <span class="desc-text">{{ record.description || '-' }}</span>
        </template>
        <template #created_at="{ record }">
          <span class="time-text">{{ record.created_at }}</span>
        </template>
        <template #actions="{ record }">
          <a-space>
            <a-button type="text" size="small" @click="openEnvironmentDrawer(record)">
              <template #icon><icon-settings /></template>
              环境管理
            </a-button>
            <a-button type="text" size="small">编辑</a-button>
            <a-button type="text" size="small" status="danger" @click="handleDelete(record)">删除</a-button>
          </a-space>
        </template>
      </a-table>
    </a-card>

    <!-- 创建项目弹窗 -->
    <a-modal
      v-model:visible="showCreateModal"
      title="创建项目"
      @ok="handleCreate"
      @cancel="showCreateModal = false"
    >
      <a-form :model="formData" layout="vertical">
        <a-form-item label="项目名称" required>
          <a-input v-model="formData.name" placeholder="请输入项目名称" />
        </a-form-item>
        <a-form-item label="项目描述">
          <a-textarea v-model="formData.description" placeholder="请输入项目描述" />
        </a-form-item>
      </a-form>
    </a-modal>

    <EnvironmentDrawer
      v-model:visible="envDrawerVisible"
      :project-id="selectedProjectId"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import { getProjects, createProject, deleteProject } from '@/api/project'
import type { Project } from '@/api/project'
import EnvironmentDrawer from './EnvironmentDrawer.vue'

const loading = ref(false)
const showCreateModal = ref(false)
const projects = ref<Project[]>([])
const envDrawerVisible = ref(false)
const selectedProjectId = ref<number | null>(null)

const formData = reactive({
  name: '',
  description: ''
})

const columns = [
  { title: 'ID', dataIndex: 'id', width: 80 },
  { title: '项目名称', dataIndex: 'name', slotName: 'name', width: 200 },
  { title: '描述', dataIndex: 'description', slotName: 'description' },
  { title: '创建时间', dataIndex: 'created_at', slotName: 'created_at', width: 180 },
  { title: '操作', slotName: 'actions', width: 260, align: 'center' as const }
]

const loadProjects = async () => {
  loading.value = true
  try {
    projects.value = await getProjects()
  } catch (error) {
    Message.error('加载项目列表失败')
  } finally {
    loading.value = false
  }
}

const handleCreate = async () => {
  if (!formData.name) {
    Message.warning('请输入项目名称')
    return
  }

  try {
    await createProject({
      name: formData.name,
      description: formData.description
    })
    Message.success('项目创建成功')
    showCreateModal.value = false
    formData.name = ''
    formData.description = ''
    loadProjects()
  } catch (error) {
    Message.error('项目创建失败')
  }
}

const handleDelete = async (record: Project) => {
  try {
    await deleteProject(record.id)
    Message.success('项目删除成功')
    loadProjects()
  } catch (error) {
    Message.error('项目删除失败')
  }
}

const openEnvironmentDrawer = (record: Project) => {
  selectedProjectId.value = record.id
  envDrawerVisible.value = true
}

onMounted(() => {
  loadProjects()
})
</script>

<style scoped>
.project-list {
  width: 100%;
}

/* 页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.page-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--gray-800);
  margin: 0 0 4px 0;
}

.page-desc {
  font-size: var(--font-size-sm);
  color: var(--gray-500);
  margin: 0;
}

/* 表格卡片 */
.table-card {
  margin-top: 0;
}

.project-name-link {
  font-weight: var(--font-weight-medium) !important;
  color: var(--indigo-600) !important;
}

.desc-text {
  color: var(--gray-600);
}

.time-text {
  color: var(--gray-500);
  font-size: var(--font-size-sm);
}
</style>

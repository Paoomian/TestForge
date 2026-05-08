<template>
  <div class="project-list">
    <a-card title="项目列表" :bordered="false">
      <template #extra>
        <a-button type="primary" @click="showCreateModal = true">
          <template #icon>
            <icon-plus />
          </template>
          创建项目
        </a-button>
      </template>

      <a-table :columns="columns" :data="projects" :loading="loading">
        <template #name="{ record }">
          <a-link>{{ record.name }}</a-link>
        </template>
        <template #actions="{ record }">
          <a-space>
            <a-button type="text" size="small" @click="openEnvironmentDrawer(record)">环境管理</a-button>
            <a-button type="text" size="small">编辑</a-button>
            <a-button type="text" size="small" status="danger" @click="handleDelete(record)">删除</a-button>
          </a-space>
        </template>
      </a-table>
    </a-card>

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
  { title: 'ID', dataIndex: 'id' },
  { title: '项目名称', dataIndex: 'name', slotName: 'name' },
  { title: '描述', dataIndex: 'description' },
  { title: '创建时间', dataIndex: 'created_at' },
  { title: '操作', slotName: 'actions' }
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

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
            <a-button type="text" size="small">编辑</a-button>
            <a-button type="text" size="small" status="danger">删除</a-button>
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'

const loading = ref(false)
const showCreateModal = ref(false)
const projects = ref([])

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

const handleCreate = () => {
  Message.success('项目创建成功')
  showCreateModal.value = false
}

onMounted(() => {
  // 加载项目列表
})
</script>

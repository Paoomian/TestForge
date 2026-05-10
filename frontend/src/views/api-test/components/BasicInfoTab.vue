<template>
  <a-form :model="formData" layout="vertical">
    <!-- 所属项目 -->
    <a-form-item label="所属项目" required>
      <a-select
        :model-value="formData.project_id"
        placeholder="请选择项目"
        :disabled="isEdit"
        @update:model-value="handleProjectChange"
      >
        <a-option
          v-for="project in projects"
          :key="project.id"
          :value="project.id"
        >
          {{ project.name }}
        </a-option>
      </a-select>
    </a-form-item>

    <!-- 所属模块 -->
    <a-form-item label="所属模块">
      <a-tree-select
        :model-value="formData.module || undefined"
        :data="moduleTreeData"
        placeholder="选择模块（可选）"
        allow-clear
        allow-search
        :filter-tree-node="filterModuleTree"
        @update:model-value="update('module', $event || '')"
      />
    </a-form-item>

    <a-row :gutter="16">
      <a-col :span="16">
        <a-form-item label="用例名称" required>
          <a-input
            :model-value="formData.name"
            placeholder="请输入用例名称"
            @update:model-value="update('name', $event)"
          />
        </a-form-item>
      </a-col>
      <a-col :span="8">
        <a-form-item label="用例编号">
          <a-input
            :model-value="formData.case_number || '保存后自动生成'"
            disabled
            style="color: var(--color-text-3);"
          />
        </a-form-item>
      </a-col>
    </a-row>

    <a-row :gutter="16">
      <a-col :span="12">
        <a-form-item label="优先级">
          <a-select
            :model-value="formData.priority"
            @update:model-value="update('priority', $event)"
          >
            <a-option value="P0">
              <a-tag color="red" size="small">P0</a-tag> 致命
            </a-option>
            <a-option value="P1">
              <a-tag color="orange" size="small">P1</a-tag> 严重
            </a-option>
            <a-option value="P2">
              <a-tag color="blue" size="small">P2</a-tag> 一般
            </a-option>
            <a-option value="P3">
              <a-tag color="green" size="small">P3</a-tag> 轻微
            </a-option>
          </a-select>
        </a-form-item>
      </a-col>
      <a-col :span="12">
        <a-form-item label="用例状态">
          <a-select
            :model-value="formData.status"
            @update:model-value="update('status', $event)"
          >
            <a-option value="draft">草稿</a-option>
            <a-option value="reviewed">已评审</a-option>
            <a-option value="deprecated">已废弃</a-option>
          </a-select>
        </a-form-item>
      </a-col>
    </a-row>

    <a-form-item label="用例描述">
      <a-textarea
        :model-value="formData.description"
        placeholder="请输入用例描述"
        :auto-size="{ minRows: 2, maxRows: 4 }"
        @update:model-value="update('description', $event)"
      />
    </a-form-item>

    <a-form-item label="前置条件">
      <a-textarea
        :model-value="formData.preconditions"
        placeholder="执行该用例前需要满足的条件，例如：用户已登录、数据库中存在某条记录"
        :auto-size="{ minRows: 2, maxRows: 4 }"
        @update:model-value="update('preconditions', $event)"
      />
    </a-form-item>

    <a-form-item label="备注">
      <a-textarea
        :model-value="formData.remark"
        placeholder="补充说明"
        :auto-size="{ minRows: 2, maxRows: 4 }"
        @update:model-value="update('remark', $event)"
      />
    </a-form-item>
  </a-form>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Project } from '@/api/project'
import type { ModuleTree } from '@/api/apiTestCase'

interface FormData {
  project_id: number
  module: string
  name: string
  case_number?: string
  priority: string
  status: string
  description: string
  preconditions: string
  remark: string
}

interface ModuleTreeNode {
  key: string
  title: string
  children?: ModuleTreeNode[]
}

const props = defineProps<{
  formData: FormData
  projects: Project[]           // 项目列表
  moduleTreeRaw: ModuleTree[]   // 原始模块树数据
  isEdit: boolean               // 是否编辑模式（编辑时不可改项目）
}>()

const emit = defineEmits<{
  (e: 'update', field: string, value: any): void
}>()

function update(field: string, value: any) {
  emit('update', field, value)
}

// 切换项目时清空模块
function handleProjectChange(value: string | number | boolean | Record<string, any> | (string | number | boolean | Record<string, any>)[]) {
  update('project_id', value as number)
  update('module', '')
}

// 根据选中项目构建模块树
const moduleTreeData = computed(() => {
  const projectId = props.formData.project_id
  if (!projectId) return []

  const projectModules = props.moduleTreeRaw.find(m => m.project_id === projectId)
  if (!projectModules || projectModules.modules.length === 0) return []

  const nodes: ModuleTreeNode[] = []
  const nodeMap = new Map<string, ModuleTreeNode>()

  projectModules.modules.forEach(modulePath => {
    const parts = modulePath.split('/')
    let currentPath = ''

    parts.forEach((part, index) => {
      const parentPath = currentPath
      currentPath = currentPath ? `${currentPath}/${part}` : part

      if (!nodeMap.has(currentPath)) {
        const node: ModuleTreeNode = {
          key: currentPath,
          title: part,
          children: []
        }
        nodeMap.set(currentPath, node)

        if (index === 0) {
          nodes.push(node)
        } else {
          const parentNode = nodeMap.get(parentPath)
          if (parentNode) {
            parentNode.children!.push(node)
          }
        }
      }
    })
  })

  return nodes
})

// 模糊搜索模块
function filterModuleTree(searchValue: string, nodeData: any) {
  return nodeData.title.toLowerCase().includes(searchValue.toLowerCase())
}
</script>

<template>
  <div class="project-module-tree">
    <div class="tree-toolbar">
      <a-input-search
        v-model="searchKey"
        placeholder="搜索项目或模块"
        style="flex: 1"
      />
      <div class="tree-toolbar-buttons">
        <a-tooltip content="在选中的项目/模块下新建模块（请先选中节点）">
          <a-button
            size="mini"
            type="primary"
            :disabled="!selectedNodeForAdd"
            @click="handleAddModuleClick"
          >
            <template #icon><icon-plus /></template>
            新建模块
          </a-button>
        </a-tooltip>
        <a-tooltip content="删除选中的模块（请先选中模块节点）">
          <a-popconfirm
            :content="`确定要删除模块 ${selectedNodeForDelete?.module || ''} 吗？该模块下的所有用例也会被删除。`"
            :disabled="!selectedNodeForDelete"
            @ok="handleDeleteModule"
          >
            <a-button
              size="mini"
              status="danger"
              :disabled="!selectedNodeForDelete"
            >
              <template #icon><icon-delete /></template>
              删除模块
            </a-button>
          </a-popconfirm>
        </a-tooltip>
        <a-tooltip content="重命名选中的模块（请先选中模块节点）">
          <a-button
            size="mini"
            :disabled="!selectedNodeForDelete"
            @click="handleRenameModuleClick"
          >
            <template #icon><icon-edit /></template>
            重命名
          </a-button>
        </a-tooltip>
      </div>
    </div>
    <a-tree
      :data="treeData"
      :show-line="true"
      :default-expand-all="false"
      :selected-keys="selectedKeys"
      @select="handleSelect"
    />

    <!-- 新建模块弹窗 -->
    <a-modal
      v-model:visible="addModuleVisible"
      :title="addModuleParent ? `新建子模块 - ${addModuleParent}` : '新建模块'"
      @ok="handleConfirmAddModule"
      @cancel="addModuleVisible = false"
    >
      <a-form :model="{ name: newModuleName }" layout="vertical">
        <a-form-item label="模块名称" required>
          <a-input
            v-model="newModuleName"
            placeholder="请输入模块名称"
          />
        </a-form-item>
        <a-form-item label="完整路径" v-if="addModuleParent">
          <a-input :model-value="`${addModuleParent}/${newModuleName}`" disabled />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 重命名模块弹窗 -->
    <a-modal
      v-model:visible="renameModuleVisible"
      title="重命名模块"
      @ok="handleConfirmRenameModule"
      @cancel="renameModuleVisible = false"
    >
      <a-form :model="{}" layout="vertical">
        <a-form-item label="当前名称">
          <a-input :model-value="renameModuleOldName" disabled />
        </a-form-item>
        <a-form-item label="新名称" required>
          <a-input
            v-model="renameModuleNewName"
            placeholder="请输入新的模块名称"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onActivated } from 'vue'
import { Message } from '@arco-design/web-vue'
import { getProjects } from '@/api/project'
import { getModuleTree, createModule, deleteModule, renameModule } from '@/api/apiTestCase'
import type { Project } from '@/api/project'
import type { ModuleTree } from '@/api/apiTestCase'

interface TreeNode {
  key: string
  title: string
  isProject?: boolean
  projectId?: number
  module?: string
  children?: TreeNode[]
}

const emit = defineEmits<{
  (e: 'select', data: { projectId?: number; module?: string }): void
}>()

const searchKey = ref('')
const selectedKeys = ref<string[]>([])
const projects = ref<Project[]>([])
const moduleTree = ref<ModuleTree[]>([])

const addModuleVisible = ref(false)
const addModuleProjectId = ref<number>()
const addModuleParent = ref('')
const newModuleName = ref('')

const renameModuleVisible = ref(false)
const renameModuleProjectId = ref<number>()
const renameModuleOldName = ref('')
const renameModuleNewName = ref('')

const selectedNode = ref<TreeNode | null>(null)

const selectedNodeForAdd = computed(() => {
  return selectedNode.value
})

const selectedNodeForDelete = computed(() => {
  return selectedNode.value?.module ? selectedNode.value : null
})

const treeData = computed<TreeNode[]>(() => {
  const tree: TreeNode[] = []

  projects.value.forEach(project => {
    const projectNode: TreeNode = {
      key: `project-${project.id}`,
      title: project.name,
      isProject: true,
      projectId: project.id,
      children: []
    }

    // 查找该项目的模块
    const projectModules = moduleTree.value.find(m => m.project_id === project.id)
    if (projectModules && projectModules.modules.length > 0) {
      // 构建模块树
      const moduleMap = new Map<string, TreeNode>()

      projectModules.modules.forEach(modulePath => {
        const parts = modulePath.split('/')
        let currentPath = ''

        parts.forEach((part, index) => {
          const parentPath = currentPath
          currentPath = currentPath ? `${currentPath}/${part}` : part
          const nodeKey = `module-${project.id}-${currentPath}`

          if (!moduleMap.has(nodeKey)) {
            const node: TreeNode = {
              key: nodeKey,
              title: part,
              projectId: project.id,
              module: currentPath,
              children: []
            }
            moduleMap.set(nodeKey, node)

            if (index === 0) {
              projectNode.children!.push(node)
            } else {
              const parentKey = `module-${project.id}-${parentPath}`
              const parentNode = moduleMap.get(parentKey)
              if (parentNode) {
                parentNode.children!.push(node)
              }
            }
          }
        })
      })
    }

    tree.push(projectNode)
  })

  // 搜索过滤
  if (searchKey.value) {
    return filterTree(tree, searchKey.value)
  }

  return tree
})

const filterTree = (nodes: TreeNode[], keyword: string): TreeNode[] => {
  const result: TreeNode[] = []

  nodes.forEach(node => {
    if (node.title.toLowerCase().includes(keyword.toLowerCase())) {
      result.push(node)
    } else if (node.children && node.children.length > 0) {
      const filteredChildren = filterTree(node.children, keyword)
      if (filteredChildren.length > 0) {
        result.push({
          ...node,
          children: filteredChildren
        })
      }
    }
  })

  return result
}

const handleSelect = (_keys: (string | number)[], data: any) => {
  const node = data.node as TreeNode
  selectedNode.value = node
  selectedKeys.value = _keys.map(String)
  if (node.isProject) {
    emit('select', { projectId: node.projectId })
  } else {
    emit('select', { projectId: node.projectId, module: node.module })
  }
}

const handleAddModuleClick = () => {
  if (selectedNode.value) {
    handleAddModule(selectedNode.value)
  }
}

const handleAddModule = (node: any) => {
  addModuleProjectId.value = node.projectId
  addModuleParent.value = node.isProject ? '' : (node.module || '')
  newModuleName.value = ''
  addModuleVisible.value = true
}

const handleDeleteModule = async () => {
  if (!selectedNode.value?.projectId || !selectedNode.value?.module) return

  const projectId = selectedNode.value.projectId
  const moduleName = selectedNode.value.module

  console.log('[DEBUG] Deleting module:', { projectId, moduleName })

  try {
    await deleteModule(projectId, moduleName)
    Message.success('模块已删除')
    selectedNode.value = null
    selectedKeys.value = []
    emit('select', {})

    console.log('[DEBUG] Reloading tree data...')
    await loadData()
    console.log('[DEBUG] Tree data reloaded')
  } catch (error) {
    console.error('[DEBUG] Delete failed:', error)
    Message.error('删除模块失败')
  }
}

const handleConfirmAddModule = async () => {
  if (!newModuleName.value.trim()) {
    Message.warning('请输入模块名称')
    return
  }
  if (!addModuleProjectId.value) return

  const modulePath = addModuleParent.value
    ? `${addModuleParent.value}/${newModuleName.value.trim()}`
    : newModuleName.value.trim()

  try {
    await createModule(addModuleProjectId.value, modulePath)
    Message.success('模块创建成功')
    addModuleVisible.value = false
    await loadData()
  } catch (error) {
    Message.error('模块创建失败')
  }
}

const handleRenameModuleClick = () => {
  if (!selectedNode.value?.projectId || !selectedNode.value?.module) return
  renameModuleProjectId.value = selectedNode.value.projectId
  renameModuleOldName.value = selectedNode.value.module
  // 默认填充当前模块名的最后一段作为新名称
  const parts = selectedNode.value.module.split('/')
  renameModuleNewName.value = parts[parts.length - 1]
  renameModuleVisible.value = true
}

const handleConfirmRenameModule = async () => {
  if (!renameModuleNewName.value.trim()) {
    Message.warning('请输入新的模块名称')
    return
  }
  if (!renameModuleProjectId.value) return

  // 构建新的完整模块路径：替换最后一段
  const oldParts = renameModuleOldName.value.split('/')
  oldParts[oldParts.length - 1] = renameModuleNewName.value.trim()
  const newModulePath = oldParts.join('/')

  if (newModulePath === renameModuleOldName.value) {
    renameModuleVisible.value = false
    return
  }

  try {
    await renameModule(renameModuleProjectId.value, renameModuleOldName.value, newModulePath)
    Message.success('模块重命名成功')
    renameModuleVisible.value = false
    selectedNode.value = null
    selectedKeys.value = []
    emit('select', {})
    await loadData()
  } catch (error) {
    Message.error('模块重命名失败')
  }
}

const loadData = async () => {
  try {
    projects.value = await getProjects()
    moduleTree.value = await getModuleTree()
  } catch (error) {
    console.error('Failed to load tree data:', error)
  }
}

onMounted(() => {
  loadData()
})

// keep-alive 组件被激活时刷新数据
onActivated(() => {
  loadData()
})

defineExpose({
  refresh: loadData
})
</script>

<style scoped>
.project-module-tree {
  height: 100%;
  overflow-y: auto;
}

.tree-toolbar {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.tree-toolbar-buttons {
  display: flex;
  gap: 8px;
}

:deep(.arco-tree-node-title) {
  flex: 1;
}
</style>

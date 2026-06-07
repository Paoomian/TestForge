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
    <a-spin :loading="loading" style="width: 100%">
      <a-empty v-if="!loading && treeData.length === 0" description="暂无数据" style="margin-top: 40px" />
      <a-tree
        v-else
        ref="treeRef"
        :data="treeData"
        :show-line="true"
        :show-icon="true"
        :default-expand-all="false"
        :selected-keys="selectedKeys"
        :expanded-keys="expandedKeys"
        @select="handleSelect"
        @expand="handleExpand"
      >
        <template #icon="{ node }">
          <span
            class="custom-icon-wrapper"
            @click.stop="handleIconClick(node)"
          >
            <icon-folder v-if="node.isProject" />
            <icon-file v-else />
          </span>
        </template>
        <template #title="nodeData">
          <span class="tree-node-title">
            <span>{{ nodeData.title }}</span>
            <a-tag
              v-if="nodeData.isProject"
              size="small"
              color="arcoblue"
              class="case-count-tag"
            >
              {{ getProjectCaseCount(nodeData.projectId) }}
            </a-tag>
          </span>
        </template>
      </a-tree>
    </a-spin>

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
import {
  IconFolder,
  IconFile,
} from '@arco-design/web-vue/es/icon'
import { getProjects } from '@/api/project'
import { getModuleTree, createModule, deleteModule, renameModule, getTestCases } from '@/api/apiTestCase'
import type { Project } from '@/api/project'
import type { ModuleTree } from '@/api/apiTestCase'

const loading = ref(false)
const projectCaseCounts = ref<Record<number, number>>({})

function getProjectCaseCount(projectId: number): number {
  return projectCaseCounts.value[projectId] || 0
}

async function loadProjectCaseCounts() {
  // 加载每个项目的用例数
  for (const p of projects.value) {
    try {
      const res = await getTestCases({ project_id: p.id, skip: 0, limit: 1000 })
      projectCaseCounts.value[p.id] = res?.length || 0
    } catch {
      projectCaseCounts.value[p.id] = 0
    }
  }
}

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

const treeRef = ref()
const expandedKeys = ref<string[]>([])

const handleIconClick = (node: any) => {
  // 切换节点的展开/折叠状态
  if (treeRef.value) {
    const isExpanded = expandedKeys.value.includes(node.key)
    treeRef.value.expandNode(node.key, !isExpanded)
    if (isExpanded) {
      expandedKeys.value = expandedKeys.value.filter(k => k !== node.key)
    } else {
      expandedKeys.value.push(node.key)
    }
  }
}

const handleExpand = (keys: string[]) => {
  expandedKeys.value = keys
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
  loading.value = true
  try {
    // 并行请求，提升加载速度
    const [projectsData, moduleTreeData] = await Promise.all([
      getProjects(),
      getModuleTree()
    ])
    projects.value = projectsData
    moduleTree.value = moduleTreeData
    // 加载每个项目的用例数
    await loadProjectCaseCounts()
  } catch (error) {
    console.error('Failed to load tree data:', error)
  } finally {
    loading.value = false
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

/* 美化树节点样式 */
:deep(.arco-tree-node) {
  padding: 6px 8px;
  border-radius: 6px;
  margin: 2px 0;
  transition: all 0.2s ease;
}

:deep(.arco-tree-node:hover) {
  background: var(--gray-100);
}

:deep(.arco-tree-node-selected) {
  background: #e8f3ff !important;
}

:deep(.arco-tree-node-selected .arco-tree-node-title) {
  color: #165DFF;
  font-weight: 500;
}

/* 项目节点样式 */
:deep(.arco-tree-node-level-1) {
  font-weight: 500;
}

/* 模块节点样式 */
:deep(.arco-tree-node-level-2),
:deep(.arco-tree-node-level-3) {
  font-size: 13px;
}

/* 图标样式 */
:deep(.arco-tree-node-switcher-icon) {
  color: #86909c;
}

:deep(.arco-tree-node-selected .arco-tree-node-switcher-icon) {
  color: #165DFF;
}

/* 隐藏展开/折叠图标和默认图标 */
:deep(.arco-tree-node-switcher) {
  display: none !important;
}

:deep(.arco-tree-node-icon) {
  display: none !important;
}

:deep(.arco-tree-node-custom-icon) {
  display: inline-flex !important;
  margin-right: 4px;
}

.custom-icon-wrapper {
  display: inline-flex;
  align-items: center;
  color: #86909c;
  font-size: 16px;
  cursor: pointer;
  transition: color 0.2s ease;
}

.custom-icon-wrapper:hover {
  color: #165DFF;
}

:deep(.arco-tree-node-selected) .custom-icon-wrapper {
  color: #165DFF;
}

/* 用例数标签 */
:deep(.arco-tree-node-title) {
  display: flex !important;
  align-items: center !important;
  width: 100% !important;
}

:deep(.arco-tree-node-title-text) {
  display: flex !important;
  align-items: center !important;
  width: 100% !important;
  flex: 1;
  min-width: 0;
}

.tree-node-title {
  display: flex !important;
  align-items: center !important;
  width: 100% !important;
  gap: 8px;
}

.tree-node-title span:first-child {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.case-count-tag {
  font-size: 11px;
  flex-shrink: 0;
  margin-left: auto !important;
}
</style>

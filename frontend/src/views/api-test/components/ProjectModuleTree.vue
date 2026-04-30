<template>
  <div class="project-module-tree">
    <a-input-search
      v-model="searchKey"
      placeholder="搜索项目或模块"
      style="margin-bottom: 12px"
    />
    <a-tree
      :data="treeData"
      :show-line="true"
      :default-expand-all="false"
      :selected-keys="selectedKeys"
      @select="handleSelect"
    >
      <template #icon="{ node }">
        <icon-folder v-if="node.isProject" />
        <icon-file v-else />
      </template>
    </a-tree>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getProjects } from '@/api/project'
import { getModuleTree } from '@/api/apiTestCase'
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

const handleSelect = (selectedKeys: string[], data: any) => {
  const node = data.node as TreeNode
  if (node.isProject) {
    emit('select', { projectId: node.projectId })
  } else {
    emit('select', { projectId: node.projectId, module: node.module })
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

defineExpose({
  refresh: loadData
})
</script>

<style scoped>
.project-module-tree {
  height: 100%;
  overflow-y: auto;
}
</style>

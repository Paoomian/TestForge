<template>
  <div class="ai-generate-page">
    <div class="page-header">
      <h2>AI 生成测试用例</h2>
      <a-space>
        <a-button @click="showSkillModal = true">
          <template #icon><icon-code /></template>
          管理技能
        </a-button>
        <a-button type="primary" @click="showConfigModal = true">
          <template #icon><icon-settings /></template>
          AI 配置
        </a-button>
      </a-space>
    </div>

    <div class="page-content">
      <!-- 输入区域 -->
      <div class="input-section">
        <a-card title="输入配置">
          <!-- 输入类型选择 -->
          <a-tabs v-model:activeKey="inputType" type="card">
            <a-tab-pane key="prd" title="PRD 文档">
              <FileUpload
                accept=".docx,.pdf,.md"
                @upload="handlePRDUpload"
              />
            </a-tab-pane>
            <a-tab-pane key="swagger" title="接口文档">
              <FileUpload
                accept=".json,.yaml,.yml"
                @upload="handleSwaggerUpload"
              />
            </a-tab-pane>
            <a-tab-pane key="text" title="文本输入">
              <TextInput v-model="textContent" />
            </a-tab-pane>
          </a-tabs>

          <!-- 生成配置 -->
          <div class="generate-config">
            <a-form :model="{}" layout="vertical">
              <a-row :gutter="16">
                <a-col :span="8">
                  <a-form-item label="生成类型">
                    <a-select v-model="generateType" @change="handleTypeChange">
                      <a-option value="functional">功能测试用例</a-option>
                      <a-option value="api">接口测试用例</a-option>
                    </a-select>
                  </a-form-item>
                </a-col>
                <a-col :span="8">
                  <a-form-item label="选择技能">
                    <a-select v-model="selectedSkill" placeholder="选择 Prompt 技能">
                      <a-option
                        v-for="skill in skills"
                        :key="skill.id"
                        :value="skill.id"
                      >
                        {{ skill.name }}
                      </a-option>
                    </a-select>
                  </a-form-item>
                </a-col>
                <a-col :span="8">
                  <a-form-item label="AI 模型">
                    <a-select v-model="selectedConfig" placeholder="选择 AI 配置">
                      <a-option
                        v-for="config in aiConfigs"
                        :key="config.id"
                        :value="config.id"
                      >
                        {{ config.provider }} - {{ config.model_name }}
                      </a-option>
                    </a-select>
                  </a-form-item>
                </a-col>
              </a-row>
            </a-form>
          </div>

          <!-- 生成按钮 -->
          <div class="generate-actions">
            <a-button
              type="primary"
              size="large"
              :loading="generating"
              :disabled="!canGenerate"
              @click="handleGenerate"
            >
              开始生成
            </a-button>
          </div>
        </a-card>
      </div>

      <!-- 任务列表 -->
      <div class="task-section">
        <a-card title="生成任务">
          <TaskList
            :tasks="tasks"
            @refresh="loadTasks"
            @view="handleViewTask"
            @delete="handleDeleteTask"
            @retry="handleRetryTask"
            @cancel="handleCancelTask"
          />
        </a-card>
      </div>
    </div>

    <!-- AI 配置弹窗 -->
    <a-modal
      v-model:visible="showConfigModal"
      title="AI 配置管理"
      :width="1000"
      :footer="false"
      :body-style="{ maxHeight: '70vh', overflow: 'auto' }"
    >
      <AIConfig />
    </a-modal>

    <!-- 技能管理弹窗 -->
    <a-modal
      v-model:visible="showSkillModal"
      title="技能管理"
      :width="1100"
      :footer="false"
      :body-style="{ maxHeight: '80vh', overflow: 'auto' }"
      @close="loadSkills"
    >
      <SkillManager />
    </a-modal>

    <!-- 任务详情弹窗 -->
    <a-modal
      v-model:visible="showTaskDetail"
      title="任务详情"
      :width="1200"
      :footer="false"
      @cancel="handleDetailClose"
    >
      <TaskDetail
        v-if="currentTask"
        :task="currentTask"
        :projects="projects"
        @save="handleSaveCases"
      />
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { Message } from '@arco-design/web-vue'
import FileUpload from './components/FileUpload.vue'
import TextInput from './components/TextInput.vue'
import TaskList from './components/TaskList.vue'
import TaskDetail from './components/TaskDetail.vue'
import AIConfig from './components/AIConfig.vue'
import SkillManager from './components/SkillManager.vue'
import {
  getAIConfigs,
  uploadPRD,
  uploadSwagger,
  createGenerateTask,
  getGenerateTasks,
  deleteGenerateTask,
  retryGenerateTask,
  cancelGenerateTask,
  saveCasesToProject
} from '@/api/aiGenerate'
import { getAISkills, initDefaultSkills } from '@/api/aiSkill'
import { getProjects } from '@/api/project'
import type {
  AIProviderConfig,
  AIGenerateTask,
  AIGenerateTaskCreate
} from '@/api/aiGenerate'
import type { AISkill } from '@/api/aiSkill'

// 状态
const inputType = ref<'prd' | 'swagger' | 'text'>('text')
const textContent = ref('')
const generateType = ref<'functional' | 'api'>('api')
const selectedConfig = ref<number | undefined>()
const selectedProject = ref<number | undefined>()
const selectedSkill = ref<number | undefined>()
const generating = ref(false)
const showConfigModal = ref(false)
const showSkillModal = ref(false)
const showTaskDetail = ref(false)
const currentTask = ref<AIGenerateTask | undefined>(undefined)
let refreshTimer: number | null = null

// 数据
const aiConfigs = ref<AIProviderConfig[]>([])
const skills = ref<AISkill[]>([])
const tasks = ref<AIGenerateTask[]>([])
const projects = ref<{ id: number; name: string }[]>([])

// 上传的文件信息
const uploadedFile = ref<{
  path: string
  name: string
  content: any
} | undefined>(undefined)

// 计算属性
const canGenerate = computed(() => {
  if (!selectedConfig.value) return false
  if (inputType.value === 'text') {
    return textContent.value.trim()
  }
  return uploadedFile.value
})

// 加载数据
const loadProjects = async () => {
  try {
    projects.value = await getProjects()
  } catch (error) {
    console.error('加载项目列表失败:', error)
  }
}

const loadConfigs = async () => {
  try {
    aiConfigs.value = await getAIConfigs()
    // 自动选择默认配置
    const defaultConfig = aiConfigs.value.find(c => c.is_default)
    if (defaultConfig) {
      selectedConfig.value = defaultConfig.id
    }
  } catch (error) {
    console.error('加载 AI 配置失败:', error)
  }
}

const loadSkills = async () => {
  try {
    skills.value = await getAISkills(generateType.value)
    // 自动选择默认技能
    const defaultSkill = skills.value.find(s => s.is_default)
    if (defaultSkill) {
      selectedSkill.value = defaultSkill.id
    } else if (skills.value.length) {
      selectedSkill.value = skills.value[0].id
    } else {
      selectedSkill.value = undefined
    }
  } catch (error) {
    console.error('加载技能列表失败:', error)
  }
}

const handleTypeChange = () => {
  loadSkills()
}

const loadTasks = async () => {
  try {
    tasks.value = await getGenerateTasks({ limit: 100 })
    // 检查是否需要自动刷新
    checkAutoRefresh()
  } catch (error) {
    console.error('加载任务列表失败:', error)
  }
}

// 检查是否有进行中的任务，决定是否自动刷新
const checkAutoRefresh = () => {
  // 详情弹窗打开时，暂停列表刷新
  if (showTaskDetail.value) {
    stopAutoRefresh()
    return
  }

  const hasActiveTasks = tasks.value.some(
    t => t.status === 'pending' || t.status === 'processing'
  )
  if (hasActiveTasks && !refreshTimer) {
    // 启动定时刷新（每3秒）
    refreshTimer = window.setInterval(loadTasks, 3000)
  } else if (!hasActiveTasks && refreshTimer) {
    // 所有任务完成，停止刷新
    stopAutoRefresh()
  }
}

// 停止自动刷新
const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// 事件处理
const handlePRDUpload = async (file: File) => {
  try {
    const result = await uploadPRD(file)
    uploadedFile.value = {
      path: result.file_path,
      name: result.file_name,
      content: result.parsed_content
    }
    Message.success('PRD 文档上传成功')
  } catch (error) {
    Message.error('PRD 文档上传失败')
  }
}

const handleSwaggerUpload = async (file: File) => {
  try {
    const result = await uploadSwagger(file)
    uploadedFile.value = {
      path: result.file_path,
      name: result.file_name,
      content: result.parsed_content
    }
    Message.success('接口文档上传成功')
  } catch (error) {
    Message.error('接口文档上传失败')
  }
}

const handleGenerate = async () => {
  if (!canGenerate.value) {
    Message.warning('请完善输入配置')
    return
  }

  generating.value = true

  try {
    const taskData: AIGenerateTaskCreate = {
      project_id: selectedProject.value,
      input_type: inputType.value,
      generate_type: generateType.value,
      config_id: selectedConfig.value,
      skill_id: selectedSkill.value
    }

    if (inputType.value === 'text') {
      taskData.input_content = textContent.value
    } else if (uploadedFile.value) {
      taskData.input_file_path = uploadedFile.value.path
      taskData.input_file_name = uploadedFile.value.name
      taskData.input_content = JSON.stringify(uploadedFile.value.content)
    }

    await createGenerateTask(taskData)
    Message.success('生成任务已创建')

    // 刷新任务列表
    await loadTasks()

    // 清空输入
    textContent.value = ''
    uploadedFile.value = undefined
  } catch (error) {
    Message.error('创建生成任务失败')
  } finally {
    generating.value = false
  }
}

const handleViewTask = async (task: AIGenerateTask) => {
  // 先关闭弹窗，销毁旧组件实例
  showTaskDetail.value = false
  currentTask.value = undefined
  await nextTick()
  // 停止列表刷新，避免重复请求
  stopAutoRefresh()
  // 再打开新任务详情
  currentTask.value = task
  showTaskDetail.value = true
}

// 关闭详情弹窗时恢复列表刷新
const handleDetailClose = () => {
  showTaskDetail.value = false
  // 延迟清空 currentTask，确保弹窗动画完成后再销毁组件
  setTimeout(() => {
    currentTask.value = undefined
    checkAutoRefresh()
  }, 300)
}

const handleDeleteTask = async (taskId: number) => {
  try {
    await deleteGenerateTask(taskId)
    Message.success('任务已删除')
    await loadTasks()
  } catch (error) {
    Message.error('删除任务失败')
  }
}

const handleRetryTask = async (taskId: number) => {
  try {
    await retryGenerateTask(taskId)
    Message.success('任务已重新提交')
    await loadTasks()
  } catch (error) {
    Message.error('重试任务失败')
  }
}

const handleCancelTask = async (taskId: number) => {
  try {
    await cancelGenerateTask(taskId)
    Message.success('任务已取消')
    await loadTasks()
  } catch (error) {
    Message.error('取消任务失败')
  }
}

const handleSaveCases = async (taskId: number, caseIndices: number[], projectId: number) => {
  try {
    const result = await saveCasesToProject(taskId, {
      case_indices: caseIndices,
      project_id: projectId
    })
    Message.success(result.message)
    showTaskDetail.value = false
  } catch (error) {
    Message.error('保存用例失败')
  }
}

// 初始化
onMounted(async () => {
  loadProjects()
  loadConfigs()
  // 初始化默认技能（如果没有的话）
  try {
    await initDefaultSkills()
  } catch (e) {
    // 忽略错误，可能已经初始化过
  }
  loadSkills()
  loadTasks()
})

// 清理定时器
onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.ai-generate-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.input-section,
.task-section {
  width: 100%;
}

.generate-config {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e5e6eb;
}

.generate-actions {
  margin-top: 20px;
  text-align: center;
}
</style>

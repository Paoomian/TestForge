<template>
  <div class="ai-config">
    <!-- 配置列表 -->
    <div class="config-list">
      <div class="config-header">
        <h3>AI 模型配置</h3>
        <a-button type="primary" @click="showAddModal = true">
          <template #icon><icon-plus /></template>
          添加配置
        </a-button>
      </div>

      <a-table :columns="columns" :data="configs" :pagination="false">
        <template #provider="{ record }">
          <a-tag :color="getProviderColor(record.provider)">
            {{ getProviderName(record.provider) }}
          </a-tag>
        </template>

        <template #api_base_url="{ record }">
          <span v-if="record.api_base_url" class="url-text">
            {{ record.api_base_url }}
          </span>
          <span v-else class="default-text">官方默认</span>
        </template>

        <template #is_default="{ record }">
          <a-tag v-if="record.is_default" color="green">默认</a-tag>
        </template>

        <template #actions="{ record }">
          <a-space>
            <a-button type="text" size="small" @click="handleTest(record)">
              测试
            </a-button>
            <a-button type="text" size="small" @click="handleEdit(record)">
              编辑
            </a-button>
            <a-button type="text" size="small" status="danger" @click="handleDelete(record.id)">
              删除
            </a-button>
          </a-space>
        </template>
      </a-table>
    </div>

    <!-- 添加/编辑配置弹窗 -->
    <a-modal
      v-model:visible="showAddModal"
      :title="editingConfig ? '编辑配置' : '添加配置'"
      :width="600"
      @ok="handleSave"
      @cancel="resetForm"
    >
      <a-form :model="formData" layout="vertical">
        <!-- 提供商选择 -->
        <a-form-item label="AI 提供商" required>
          <a-select v-model="formData.provider" @change="handleProviderChange">
            <a-option value="openai">OpenAI</a-option>
            <a-option value="claude">Claude (Anthropic)</a-option>
            <a-option value="deepseek">DeepSeek</a-option>
            <a-option value="custom">自定义（兼容 OpenAI 接口）</a-option>
          </a-select>
        </a-form-item>

        <!-- API Key -->
        <a-form-item label="API Key" :required="!editingConfig">
          <a-input-password
            v-model="formData.api_key"
            :placeholder="editingConfig ? '留空则保持原有 Key 不变' : '输入 API Key'"
          />
        </a-form-item>

        <!-- 自定义 API 端点 -->
        <a-form-item
          v-if="formData.provider === 'custom' || showCustomUrl"
          label="API 端点地址"
        >
          <a-input
            v-model="formData.api_base_url"
            :placeholder="apiUrlPlaceholder"
          />
          <div class="form-help">
            支持中转站或自建服务，如：
            <ul>
              <li>OpenAI 中转站：<code>https://api.example.com/v1</code></li>
              <li>本地 Ollama：<code>http://localhost:11434</code></li>
            </ul>
          </div>
        </a-form-item>

        <!-- 高级选项：自定义官方 API 地址 -->
        <a-form-item v-if="formData.provider !== 'custom'">
          <a-checkbox v-model="showCustomUrl">
            自定义 API 端点（使用中转站）
          </a-checkbox>
        </a-form-item>

        <!-- 模型名称 -->
        <a-form-item label="模型名称" required>
          <div class="model-select-row">
            <a-select
              v-model="formData.model_name"
              :options="modelOptions"
              placeholder="选择或输入模型名称"
              allow-search
              allow-create
              :loading="fetchingModels"
              :trigger-props="{ autoFitPopupMinWidth: true }"
              :dropdown-style="{ minWidth: '350px', maxWidth: '500px' }"
              style="flex: 1"
            />
            <a-button
              type="outline"
              :loading="fetchingModels"
              :disabled="!canFetchModels"
              @click="handleFetchModels"
            >
              <template #icon><icon-refresh /></template>
              获取模型
            </a-button>
          </div>
          <div class="form-help">
            点击「获取模型」从端点拉取可用模型列表，也可手动输入模型名称
          </div>
        </a-form-item>

        <!-- 设为默认 -->
        <a-form-item>
          <a-checkbox v-model="formData.is_default">设为默认配置</a-checkbox>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import {
  getAIConfigs,
  createAIConfig,
  updateAIConfig,
  deleteAIConfig,
  testAIConfig,
  fetchModels
} from '@/api/aiGenerate'
import type { AIProviderConfig, AIProviderConfigCreate } from '@/api/aiGenerate'

// 状态
const configs = ref<AIProviderConfig[]>([])
const showAddModal = ref(false)
const editingConfig = ref<AIProviderConfig | null>(null)
const showCustomUrl = ref(false)
const fetchingModels = ref(false)
const remoteModels = ref<{ label: string; value: string }[]>([])

// 表单数据
const formData = ref<AIProviderConfigCreate>({
  provider: 'openai',
  api_key: '',
  model_name: '',
  api_base_url: '',
  is_default: false
})

// 表格列配置
const columns = [
  { title: '提供商', dataIndex: 'provider', slotName: 'provider', width: 120 },
  { title: '模型', dataIndex: 'model_name', width: 180 },
  { title: 'API 端点', dataIndex: 'api_base_url', slotName: 'api_base_url', width: 250 },
  { title: '默认', dataIndex: 'is_default', slotName: 'is_default', width: 80 },
  { title: '操作', slotName: 'actions', width: 180 }
]

// 模型选项（优先使用远程获取的，否则使用默认的）
const modelOptions = computed(() => {
  if (remoteModels.value.length > 0) {
    return remoteModels.value
  }
  const models: Record<string, { label: string; value: string }[]> = {
    openai: [
      { label: 'GPT-4 Turbo', value: 'gpt-4-turbo' },
      { label: 'GPT-4', value: 'gpt-4' },
      { label: 'GPT-3.5 Turbo', value: 'gpt-3.5-turbo' }
    ],
    claude: [
      { label: 'Claude 3 Opus', value: 'claude-3-opus-20240229' },
      { label: 'Claude 3 Sonnet', value: 'claude-3-sonnet-20240229' },
      { label: 'Claude 3 Haiku', value: 'claude-3-haiku-20240307' }
    ],
    deepseek: [
      { label: 'DeepSeek Chat', value: 'deepseek-chat' },
      { label: 'DeepSeek Coder', value: 'deepseek-coder' }
    ]
  }
  return models[formData.value.provider] || []
})

// 是否可以获取模型
const canFetchModels = computed(() => {
  // 编辑模式下，可以使用已保存的配置获取模型
  if (editingConfig.value) return true
  // 新建模式下，需要输入 API Key
  if (!formData.value.api_key) return false
  if (formData.value.provider === 'custom') return !!formData.value.api_base_url
  return true
})

// API 端点占位符
const apiUrlPlaceholder = computed(() => {
  const placeholders: Record<string, string> = {
    openai: 'https://api.openai.com/v1',
    claude: 'https://api.anthropic.com',
    deepseek: 'https://api.deepseek.com/v1',
    custom: '输入 API 端点地址'
  }
  return placeholders[formData.value.provider] || ''
})

// 辅助函数
const getProviderColor = (provider: string) => {
  const colors: Record<string, string> = {
    openai: 'green',
    claude: 'purple',
    deepseek: 'blue',
    custom: 'gray'
  }
  return colors[provider] || 'gray'
}

const getProviderName = (provider: string) => {
  const names: Record<string, string> = {
    openai: 'OpenAI',
    claude: 'Claude',
    deepseek: 'DeepSeek',
    custom: '自定义'
  }
  return names[provider] || provider
}

// 事件处理
const handleProviderChange = () => {
  formData.value.model_name = ''
  formData.value.api_base_url = ''
  showCustomUrl.value = false
  remoteModels.value = []
}

// 获取模型列表
const handleFetchModels = async () => {
  // 新建模式下需要 API Key
  if (!editingConfig.value && !formData.value.api_key) {
    Message.warning('请先输入 API Key')
    return
  }

  fetchingModels.value = true
  try {
    const requestData: any = {
      provider: formData.value.provider,
      api_base_url: formData.value.api_base_url || undefined
    }

    // 编辑模式下使用配置 ID（使用后端存储的 Key）
    if (editingConfig.value) {
      requestData.config_id = editingConfig.value.id
      // 如果用户输入了新 Key，则使用新 Key
      if (formData.value.api_key) {
        requestData.api_key = formData.value.api_key
      }
    } else {
      requestData.api_key = formData.value.api_key
    }

    const result = await fetchModels(requestData)
    remoteModels.value = result.models.map(m => ({
      label: m.name,
      value: m.id
    }))
    if (remoteModels.value.length > 0) {
      Message.success(`获取到 ${remoteModels.value.length} 个模型`)
    } else {
      Message.info('未获取到可用模型')
    }
  } catch (error: any) {
    Message.error(error?.message || '获取模型列表失败')
  } finally {
    fetchingModels.value = false
  }
}

const handleSave = async () => {
  // 验证表单
  if (!editingConfig.value && !formData.value.api_key) {
    Message.warning('请输入 API Key')
    return
  }
  if (!formData.value.model_name) {
    Message.warning('请选择或输入模型名称')
    return
  }
  if (formData.value.provider === 'custom' && !formData.value.api_base_url) {
    Message.warning('自定义提供商必须输入 API 端点地址')
    return
  }

  try {
    if (editingConfig.value) {
      // 编辑模式：如果 api_key 为空，则不更新（保留原有的）
      const updateData = { ...formData.value }
      if (!updateData.api_key) {
        delete updateData.api_key
      }
      await updateAIConfig(editingConfig.value.id, updateData)
      Message.success('配置已更新')
    } else {
      await createAIConfig(formData.value)
      Message.success('配置已添加')
    }
    showAddModal.value = false
    resetForm()
    await loadConfigs()
  } catch (error) {
    Message.error('保存配置失败')
  }
}

const handleEdit = (config: AIProviderConfig) => {
  editingConfig.value = config
  formData.value = {
    provider: config.provider,
    api_key: '', // 不回显 API Key
    model_name: config.model_name,
    api_base_url: config.api_base_url || '',
    is_default: config.is_default
  }
  showCustomUrl.value = !!config.api_base_url
  showAddModal.value = true
}

const handleDelete = async (id: number) => {
  Modal.confirm({
    title: '确认删除',
    content: '确定要删除这个配置吗？',
    onOk: async () => {
      try {
        await deleteAIConfig(id)
        Message.success('配置已删除')
        await loadConfigs()
      } catch (error) {
        Message.error('删除配置失败')
      }
    }
  })
}

const handleTest = async (config: AIProviderConfig) => {
  try {
    const result = await testAIConfig(config.id)
    if (result.success) {
      Message.success('配置有效')
    } else {
      Message.error(`配置无效: ${result.message}`)
    }
  } catch (error) {
    Message.error('测试配置失败')
  }
}

const resetForm = () => {
  formData.value = {
    provider: 'openai',
    api_key: '',
    model_name: '',
    api_base_url: '',
    is_default: false
  }
  editingConfig.value = null
  showCustomUrl.value = false
}

// 加载配置
const loadConfigs = async () => {
  try {
    configs.value = await getAIConfigs()
  } catch (error) {
    console.error('加载配置失败:', error)
  }
}

// 初始化
onMounted(() => {
  loadConfigs()
})
</script>

<style scoped>
.ai-config {
  padding: 16px 0;
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.config-header h3 {
  margin: 0;
}

.url-text {
  font-size: 12px;
  color: #86909c;
  word-break: break-all;
}

.default-text {
  color: #c9cdd4;
  font-style: italic;
}

.form-help {
  font-size: 12px;
  color: #86909c;
  margin-top: 4px;
}

.form-help ul {
  margin: 4px 0;
  padding-left: 16px;
}

.form-help code {
  background: #f2f3f5;
  padding: 2px 4px;
  border-radius: 2px;
  font-size: 11px;
}

.model-select-row {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  width: 100%;
}

.model-select-row .arco-select {
  flex: 1;
  min-width: 0;
}

/* 模型下拉框样式 */
:deep(.arco-select-dropdown-list) {
  min-width: 350px;
}

:deep(.arco-select-dropdown .arco-select-option) {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>

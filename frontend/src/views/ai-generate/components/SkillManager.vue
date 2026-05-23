<template>
  <div class="skill-manager">
    <div class="skill-header">
      <a-select
        v-model="filterType"
        placeholder="选择类型"
        style="width: 160px"
        allow-clear
        @change="loadSkills"
      >
        <a-option value="functional">功能测试</a-option>
        <a-option value="api">接口测试</a-option>
      </a-select>
      <a-button type="primary" @click="handleAdd">
        <template #icon><icon-plus /></template>
        新建技能
      </a-button>
    </div>

    <div class="skill-content">
      <!-- 技能列表 -->
      <div class="skill-list">
        <div
          v-for="skill in skills"
          :key="skill.id"
          class="skill-item"
          :class="{ active: selectedSkill?.id === skill.id }"
          @click="handleSelectSkill(skill)"
        >
          <div class="skill-item-info">
            <div class="skill-item-name">
              {{ skill.name }}
              <a-tag v-if="skill.is_default" color="green" size="small">默认</a-tag>
            </div>
            <a-tag :color="skill.generate_type === 'functional' ? 'blue' : 'orange'" size="small">
              {{ skill.generate_type === 'functional' ? '功能测试' : '接口测试' }}
            </a-tag>
          </div>
          <div class="skill-item-desc">{{ skill.description || '暂无描述' }}</div>
        </div>
        <a-empty v-if="!skills.length" description="暂无技能，点击右上角新建" />
      </div>

      <!-- 编辑区 -->
      <div class="skill-editor" v-if="selectedSkill">
        <a-form :model="selectedSkill" layout="vertical">
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="技能名称" required>
                <a-input v-model="selectedSkill.name" placeholder="如：电商场景测试专家" />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="生成类型" required>
                <a-select v-model="selectedSkill.generate_type">
                  <a-option value="functional">功能测试</a-option>
                  <a-option value="api">接口测试</a-option>
                </a-select>
              </a-form-item>
            </a-col>
          </a-row>

          <a-form-item label="技能描述">
            <a-input v-model="selectedSkill.description" placeholder="简要描述该技能的用途和特点" />
          </a-form-item>

          <a-form-item label="Prompt 模板" required>
            <a-textarea
              v-model="promptTemplate"
              placeholder="定义 AI 的角色、规则和要求。在需要插入需求文档的位置写 {input_content}"
              :auto-size="{ minRows: 12, maxRows: 50 }"
            />
            <div class="form-help">
              用 <code>{'{input_content}'}</code> 标记需求插入位置。输出格式、Pairwise示例、backend_ui示例由系统自动附加。
            </div>
          </a-form-item>

          <a-form-item label="设为默认">
            <a-switch v-model="selectedSkill.is_default" />
          </a-form-item>

          <a-space>
            <a-button type="primary" @click="handleSave" :loading="saving">保存</a-button>
            <a-button v-if="isNew" @click="cancelEdit">取消</a-button>
            <a-button v-if="!isNew" status="danger" @click="handleDelete(selectedSkill!.id)">删除</a-button>
          </a-space>
        </a-form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import {
  getAISkills,
  createAISkill,
  updateAISkill,
  deleteAISkill,
  type AISkill
} from '@/api/aiSkill'

const emit = defineEmits<{
  close: []
}>()

const skills = ref<AISkill[]>([])
const selectedSkill = ref<AISkill | null>(null)
const filterType = ref<string | undefined>(undefined)
const isNew = ref(false)
const saving = ref(false)

// 合并后的 Prompt 模板（只编辑这一个字段）
const promptTemplate = ref('')

const loadSkills = async () => {
  try {
    skills.value = await getAISkills(filterType.value)
  } catch (error) {
    console.error('加载技能列表失败:', error)
  }
}

const handleSelectSkill = (skill: AISkill) => {
  selectedSkill.value = { ...skill }
  // 从数据库中读取：优先用 system_prompt（新格式），兼容旧格式
  promptTemplate.value = skill.system_prompt || ''
}

const handleAdd = () => {
  isNew.value = true
  selectedSkill.value = {
    id: 0,
    user_id: 0,
    name: '',
    description: '',
    generate_type: filterType.value as any || 'functional',
    system_prompt: '',
    user_prompt: '',
    is_default: false,
    created_at: '',
  }
  promptTemplate.value = ''
}

const cancelEdit = () => {
  isNew.value = false
  selectedSkill.value = null
}

const handleSave = async () => {
  if (!selectedSkill.value) return
  if (!selectedSkill.value.name) {
    Message.warning('请输入技能名称')
    return
  }
  if (!promptTemplate.value.trim()) {
    Message.warning('请输入 Prompt 模板')
    return
  }

  saving.value = true
  try {
    const data = {
      name: selectedSkill.value.name,
      description: selectedSkill.value.description,
      generate_type: selectedSkill.value.generate_type,
      system_prompt: promptTemplate.value,
      user_prompt: '',  // 新格式：user_prompt 留空，由后端自动生成
      is_default: selectedSkill.value.is_default,
    }

    if (isNew.value) {
      await createAISkill(data)
      Message.success('创建成功')
    } else {
      await updateAISkill(selectedSkill.value.id, data)
      Message.success('保存成功')
    }
    isNew.value = false
    await loadSkills()
  } catch (error) {
    Message.error('保存失败')
    console.error('保存技能失败:', error)
  } finally {
    saving.value = false
  }
}

const handleDelete = (id: number) => {
  Modal.confirm({
    title: '确认删除',
    content: '确定要删除这个技能吗？',
    onOk: async () => {
      try {
        await deleteAISkill(id)
        Message.success('已删除')
        selectedSkill.value = null
        await loadSkills()
      } catch (error) {
        Message.error('删除失败')
      }
    }
  })
}

onMounted(loadSkills)
</script>

<style scoped>
.skill-manager {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 600px;
}

.skill-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.skill-content {
  display: flex;
  gap: 16px;
  flex: 1;
}

.skill-list {
  width: 220px;
  min-width: 220px;
  border: 1px solid var(--color-border-2);
  border-radius: 6px;
  overflow-y: auto;
  max-height: 700px;
}

.skill-item {
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid var(--color-border-2);
  transition: background 0.2s;
}

.skill-item:hover {
  background: var(--color-fill-1);
}

.skill-item.active {
  background: var(--color-primary-light-1);
  border-left: 3px solid var(--color-primary-6);
}

.skill-item-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  gap: 8px;
}

.skill-item-name {
  font-weight: 500;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}

.skill-item-desc {
  font-size: 12px;
  color: var(--color-text-3);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.skill-editor {
  flex: 1;
  border: 1px solid var(--color-border-2);
  border-radius: 6px;
  padding: 16px;
  overflow-y: auto;
  max-height: 700px;
}

.form-help {
  font-size: 12px;
  color: var(--color-text-3);
  margin-top: 2px;
  line-height: 1.4;
}

.form-help code {
  background: var(--color-fill-2);
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 12px;
}
</style>

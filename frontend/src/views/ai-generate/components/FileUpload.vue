<template>
  <div class="file-upload">
    <a-upload
      :accept="accept"
      :show-file-list="false"
      :before-upload="handleBeforeUpload"
      :custom-request="handleUpload as any"
    >
      <template #upload-button>
        <div class="upload-area">
          <div v-if="!uploadedFile" class="upload-placeholder">
            <icon-upload :size="40" />
            <p>点击或拖拽文件到此处上传</p>
            <p class="upload-hint">支持格式：{{ accept }}</p>
          </div>
          <div v-else class="upload-success">
            <icon-file :size="40" />
            <p>{{ uploadedFile.name }}</p>
            <a-button size="small" @click.stop="handleRemove">重新选择</a-button>
          </div>
        </div>
      </template>
    </a-upload>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Message } from '@arco-design/web-vue'

defineProps<{
  accept: string
}>()

const emit = defineEmits<{
  upload: [file: File]
}>()

const uploadedFile = ref<File | undefined>(undefined)

const handleBeforeUpload = (file: File) => {
  // 验证文件大小（最大 10MB）
  if (file.size > 10 * 1024 * 1024) {
    Message.error('文件大小不能超过 10MB')
    return false
  }
  return true
}

const handleUpload = (option: any) => {
  uploadedFile.value = option.fileItem.file
  emit('upload', option.fileItem.file)
}

const handleRemove = () => {
  uploadedFile.value = undefined
}
</script>

<style scoped>
.file-upload {
  width: 100%;
}

.file-upload :deep(.arco-upload) {
  width: 100%;
}

.upload-area {
  width: 100%;
  min-height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-area:hover {
  background: var(--primary-50);
}

.upload-placeholder,
.upload-success {
  text-align: center;
  color: #86909c;
}

.upload-placeholder p,
.upload-success p {
  margin: 8px 0;
}

.upload-hint {
  font-size: 12px;
  color: #c9cdd4;
}
</style>

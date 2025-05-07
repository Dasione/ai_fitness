<template>
  <el-dialog
    v-model="dialogVisible"
    title="上传视频"
    width="500px"
    :close-on-click-modal="false"
    :append-to-body="appendToBody"
    :destroy-on-close="destroyOnClose"
    @close="handleClose"
  >
    <div v-if="initialFile" class="pre-selected-file">
      <el-icon><VideoCamera /></el-icon>
      <span>已选择录制的视频文件：{{ initialFile.name }}</span>
    </div>
    <el-form
      ref="uploadForm"
      :model="formData"
      :rules="rules"
      label-position="top"
    >
      <el-form-item label="视频标题" prop="title">
        <el-input v-model="formData.title" placeholder="请输入视频标题" />
      </el-form-item>

      <el-form-item label="视频描述" prop="description">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="3"
          placeholder="请输入视频描述"
        />
      </el-form-item>

      <el-form-item label="选择视频" prop="file" v-if="!initialFile">
        <el-upload
          ref="upload"
          class="video-upload"
          drag
          :auto-upload="false"
          :on-change="handleFileChange"
          :limit="1"
          accept="video/*"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将视频拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持mp4、mov等格式视频文件，单个文件不超过500MB
            </div>
          </template>
        </el-upload>
      </el-form-item>
    </el-form>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="uploading"
          @click="handleUpload"
        >
          上传
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useVideoStore } from '@/store/modules/video'
import { ElMessage } from 'element-plus'
import { UploadFilled, VideoCamera } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  },
  initialFile: {
    type: File,
    default: null
  },
  initialTitle: {
    type: String,
    default: ''
  },
  appendToBody: {
    type: Boolean,
    default: false
  },
  destroyOnClose: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const videoStore = useVideoStore()
const uploadForm = ref(null)
const upload = ref(null)
const uploading = ref(false)

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const formData = reactive({
  title: props.initialTitle,
  description: '',
  file: props.initialFile
})

const rules = {
  title: [
    { required: true, message: '请输入视频标题', trigger: 'blur' },
    { min: 2, max: 50, message: '标题长度在2-50个字符之间', trigger: 'blur' }
  ],
  description: [
    { max: 200, message: '描述不能超过200个字符', trigger: 'blur' }
  ],
  file: [
    { required: true, message: '请选择要上传的视频文件', trigger: 'change' }
  ]
}

const handleFileChange = (file) => {
  // 检查文件大小（500MB）
  const maxSize = 500 * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过500MB')
    upload.value.clearFiles()
    return false
  }
  
  formData.file = file.raw
}

const handleUpload = async () => {
  if (!uploadForm.value) return
  
  try {
    await uploadForm.value.validate()
    uploading.value = true
    
    await videoStore.uploadVideo(formData)
    ElMessage.success('上传成功')
    emit('success')
    dialogVisible.value = false
  } catch (error) {
    ElMessage.error(error.message || '上传失败')
  } finally {
    uploading.value = false
  }
}

const handleClose = () => {
  uploadForm.value?.resetFields()
  upload.value?.clearFiles()
  Object.assign(formData, {
    title: '',
    description: '',
    file: null
  })
}

// 监听对话框关闭
watch(dialogVisible, (val) => {
  if (!val) {
    handleClose()
  }
})

// 监听初始文件变化
watch(() => props.initialFile, (newFile) => {
  if (newFile) {
    formData.file = newFile
  }
})

// 监听初始标题变化
watch(() => props.initialTitle, (newTitle) => {
  if (newTitle) {
    formData.title = newTitle
  }
})
</script>

<style lang="scss" scoped>
.video-upload {
  :deep(.el-upload) {
    width: 100%;
  }
  
  :deep(.el-upload-dragger) {
    width: 100%;
    height: 200px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    
    .el-icon--upload {
      font-size: 48px;
      color: var(--el-color-primary);
      margin-bottom: 16px;
    }
    
    .el-upload__text {
      font-size: 14px;
      color: var(--el-text-color-regular);
      
      em {
        color: var(--el-color-primary);
        font-style: normal;
      }
    }
  }
  
  :deep(.el-upload__tip) {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    margin-top: 8px;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

:deep(.el-dialog) {
  position: fixed !important;
  top: 50% !important;
  left: 50% !important;
  transform: translate(-50%, -50%) !important;
  margin: 0 !important;
  max-height: 90vh;
  overflow-y: auto;
}

:deep(.el-dialog__wrapper) {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 2000;
}

.pre-selected-file {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 20px;
  
  .el-icon {
    font-size: 20px;
    color: #409EFF;
  }
  
  span {
    color: #606266;
    font-size: 14px;
  }
}
</style> 
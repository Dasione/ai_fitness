<template>
  <el-dialog
    v-model="dialogVisible"
    title="录制视频"
    width="800px"
    :close-on-click-modal="false"
    :before-close="handleBeforeClose"
    append-to-body
    destroy-on-close
  >
    <div class="record-container">
      <div class="camera-container">
        <WebcamComponent
          ref="webcam"
          :height="480"
          :width="640"
          :device-id="deviceId"
          @cameras="handleCameras"
          @error="handleError"
        />
        
        <div class="camera-controls">
          <el-select
            v-model="deviceId"
            placeholder="选择摄像头"
            @change="handleDeviceChange"
          >
            <el-option
              v-for="device in cameras"
              :key="device.deviceId"
              :label="device.label"
              :value="device.deviceId"
            />
          </el-select>
          
          <div class="record-controls">
            <el-button
              v-if="!isRecording"
              type="primary"
              :icon="VideoCamera"
              @click="startRecording"
            >
              开始录制
            </el-button>
            <el-button
              v-else
              type="danger"
              :icon="VideoCameraFilled"
              @click="stopRecording"
            >
              停止录制 ({{ recordingTime }}s)
            </el-button>
          </div>
        </div>
      </div>

      <div v-if="previewUrl" class="preview-container">
        <h3>预览</h3>
        <video
          ref="preview"
          :src="previewUrl"
          controls
          class="preview-video"
        />
        
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
              rows="3"
              placeholder="请输入视频描述"
            />
          </el-form-item>
        </el-form>
      </div>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button
          v-if="previewUrl"
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
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useVideoStore } from '@/store/modules/video'
import { ElMessage, ElMessageBox } from 'element-plus'
import { VideoCamera, VideoCameraFilled } from '@element-plus/icons-vue'
import WebcamComponent from './WebcamComponent.vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const videoStore = useVideoStore()
const webcam = ref(null)
const preview = ref(null)
const uploadForm = ref(null)
const mediaRecorder = ref(null)
const recordedChunks = ref([])
const isRecording = ref(false)
const recordingTime = ref(0)
const recordingTimer = ref(null)
const uploading = ref(false)
const cameras = ref([])
const deviceId = ref('')
const previewUrl = ref('')

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const formData = reactive({
  title: '',
  description: ''
})

const rules = {
  title: [
    { required: true, message: '请输入视频标题', trigger: 'blur' },
    { min: 2, max: 50, message: '标题长度在2-50个字符之间', trigger: 'blur' }
  ],
  description: [
    { max: 200, message: '描述不能超过200个字符', trigger: 'blur' }
  ]
}

const handleCameras = (devices) => {
  cameras.value = devices
  if (devices.length > 0 && !deviceId.value) {
    deviceId.value = devices[0].deviceId
  }
}

const handleError = (error) => {
  ElMessage.error('摄像头访问失败：' + error.message)
}

const handleDeviceChange = (id) => {
  deviceId.value = id
}

const startRecording = async () => {
  try {
    const stream = webcam.value.getStream()
    if (!stream) {
      throw new Error('未获取到视频流')
    }

    mediaRecorder.value = new MediaRecorder(stream)
    recordedChunks.value = []
    
    mediaRecorder.value.ondataavailable = (e) => {
      if (e.data.size > 0) {
        recordedChunks.value.push(e.data)
      }
    }
    
    mediaRecorder.value.onstop = () => {
      const blob = new Blob(recordedChunks.value, { type: 'video/webm' })
      previewUrl.value = URL.createObjectURL(blob)
    }
    
    mediaRecorder.value.start()
    isRecording.value = true
    recordingTime.value = 0
    recordingTimer.value = setInterval(() => {
      recordingTime.value++
    }, 1000)
  } catch (error) {
    ElMessage.error('开始录制失败：' + error.message)
  }
}

const stopRecording = () => {
  if (mediaRecorder.value && isRecording.value) {
    mediaRecorder.value.stop()
    isRecording.value = false
    clearInterval(recordingTimer.value)
  }
}

const handleUpload = async () => {
  if (!uploadForm.value || !recordedChunks.value.length) return
  
  try {
    await uploadForm.value.validate()
    uploading.value = true
    
    const blob = new Blob(recordedChunks.value, { type: 'video/webm' })
    const file = new File([blob], 'recorded-video.webm', { type: 'video/webm' })
    
    await videoStore.uploadVideo({
      ...formData,
      file
    })
    
    ElMessage.success('上传成功')
    emit('success')
    dialogVisible.value = false
  } catch (error) {
    ElMessage.error(error.message || '上传失败')
  } finally {
    uploading.value = false
  }
}

const handleBeforeClose = (done) => {
  if (isRecording.value) {
    ElMessageBox.confirm(
      '正在录制中，确定要关闭吗？',
      '提示',
      {
        type: 'warning'
      }
    )
      .then(() => {
        stopRecording()
        done()
      })
      .catch(() => {})
  } else {
    done()
  }
}

const cleanup = () => {
  if (isRecording.value) {
    stopRecording()
  }
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = ''
  }
  formData.title = ''
  formData.description = ''
  recordedChunks.value = []
}

watch(dialogVisible, (val) => {
  if (!val) {
    cleanup()
  }
})

onBeforeUnmount(() => {
  cleanup()
})
</script>

<style scoped>
.record-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.camera-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.camera-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  max-width: 640px;
}

.record-controls {
  display: flex;
  gap: 12px;
}

.preview-container {
  padding: 16px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.preview-container h3 {
  margin-top: 0;
  margin-bottom: 16px;
  color: #606266;
}

.preview-video {
  width: 100%;
  max-width: 640px;
  margin-bottom: 20px;
  border-radius: 4px;
}

:deep(.el-form-item__label) {
  padding-bottom: 4px;
}
</style> 
<template>
  <div class="training-container">
    <el-card class="page-header-card" shadow="hover">
      <div class="page-header">
        <div class="header-content">
          <h2>训练指导</h2>
          <p class="subtitle">观看规范动作示范，跟随视频进行训练</p>
        </div>
      </div>
    </el-card>

    <el-row :gutter="24">
      <!-- 左侧：规范视频播放 -->
      <el-col :span="12">
        <el-card class="reference-video" shadow="hover">
          <template #header>
            <div class="card-header">
              <h3>规范动作示范</h3>
              <div class="header-actions">
                <el-button 
                  type="primary" 
                  link
                  @click="showVideoSelector = true"
                >
                  <el-icon><Switch /></el-icon>替换视频
                </el-button>
              </div>
            </div>
          </template>
          <div class="video-container">
            <VideoPlayer
              ref="referencePlayerRef"
              :src="referenceVideo.url"
              :poster="referenceVideo.thumbnail"
              :controls="true"
              :autoplay="false"
              preload="auto"
              @error="handleReferenceError"
            />
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：实时训练 -->
      <el-col :span="12">
        <el-card class="camera-section" shadow="hover">
          <template #header>
            <div class="card-header">
              <h3>实时训练</h3>
              <el-button-group>
                <el-button 
                  type="primary" 
                  :disabled="isRecording"
                  @click="showHandSelector = true"
                >
                  <el-icon><VideoPlay /></el-icon>开始录制
                </el-button>
                <el-button 
                  type="danger" 
                  :disabled="!isRecording"
                  @click="stopRecording"
                >
                  <el-icon><VideoPause /></el-icon>停止录制
                </el-button>
              </el-button-group>
            </div>
          </template>
          <RealTimeTraining 
            ref="realTimeTrainingRef"
            v-model:isRecording="isRecording"
            v-model:recordedVideoFile="recordedVideoFile"
          />
        </el-card>
      </el-col>
    </el-row>

    <!-- 动作要点和训练小贴士 -->
    <el-row :gutter="24" class="mt-4">
      <!-- 左侧：动作要点 -->
      <el-col :span="12">
        <el-card shadow="hover" class="info-card">
          <template #header>
            <div class="card-header">
              <h3>动作要点</h3>
            </div>
          </template>
          <el-collapse v-model="activeCollapse">
            <el-collapse-item title="1. 基本姿势" name="1">
              <p>保持脊柱挺直，肩膀放松，目视前方</p>
            </el-collapse-item>
            <el-collapse-item title="2. 动作节奏" name="2">
              <p>控制呼吸，保持均匀稳定的节奏</p>
            </el-collapse-item>
          </el-collapse>
        </el-card>
      </el-col>

      <!-- 右侧：训练小贴士 -->
      <el-col :span="12">
        <el-card shadow="hover" class="info-card">
          <template #header>
            <div class="card-header">
              <h3>训练小贴士</h3>
            </div>
          </template>
          <el-row :gutter="20">
            <el-col :span="8" v-for="(tip, index) in trainingTips" :key="index">
              <div class="tip-item">
                <el-icon :size="24" :color="tip.color">
                  <component :is="tip.icon" />
                </el-icon>
                <h4>{{ tip.title }}</h4>
                <p>{{ tip.content }}</p>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>

    <!-- 视频上传对话框 -->
    <upload-dialog
      v-model="uploadDialogVisible"
      :initial-file="recordedVideoFile"
      :initial-title="generateUploadTitle()"
      append-to-body
      destroy-on-close
      @success="handleUploadSuccess"
    />

    <!-- 视频选择对话框 -->
    <el-dialog
      v-model="showVideoSelector"
      title="选择标准视频"
      width="60%"
      :close-on-click-modal="false"
    >
      <div class="video-selector">
        <el-input
          v-model="searchQuery"
          placeholder="搜索视频"
          clearable
          @clear="handleSearch"
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <div class="video-list">
          <el-scrollbar height="400px">
            <div 
              v-for="video in filteredVideos" 
              :key="video.id"
              class="video-item"
              :class="{ active: selectedVideo?.id === video.id }"
              @click="selectVideo(video)"
            >
              <el-image
                :src="video.thumbnail"
                fit="cover"
                class="video-thumbnail"
              >
                <template #placeholder>
                  <div class="image-slot">加载中...</div>
                </template>
              </el-image>
              <div class="video-info">
                <div class="video-title">{{ video.title }}</div>
                <div class="video-meta">
                  <span>{{ formatDuration(video.duration) }}</span>
                  <span>{{ formatDate(video.createdAt) }}</span>
                </div>
              </div>
            </div>
          </el-scrollbar>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showVideoSelector = false">取消</el-button>
          <el-button 
            type="primary" 
            :disabled="!selectedVideo"
            @click="confirmVideoSelection"
          >
            确认
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 选择手的对话框 -->
    <el-dialog
      v-model="showHandSelector"
      title="选择要分析的手"
      width="30%"
      :close-on-click-modal="false"
    >
      <div class="hand-selector">
        <el-radio-group v-model="selectedHand">
          <el-radio label="left">左手</el-radio>
          <el-radio label="right">右手</el-radio>
        </el-radio-group>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showHandSelector = false">取消</el-button>
          <el-button 
            type="primary" 
            :disabled="!selectedHand"
            @click="confirmHandSelection"
          >
            确认
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, nextTick, computed, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { VideoPlay, VideoPause, Timer, Lightning, Star, Switch, Search } from '@element-plus/icons-vue'
import VideoPlayer from '@/components/video/VideoPlayer.vue'
import RealTimeTraining from '@/components/RealTimeTraining.vue'
import UploadDialog from '@/components/video/UploadDialog.vue'
import { useVideoStore } from '@/store/modules/video'
import dayjs from 'dayjs'

// 常量定义
const ERROR_MESSAGES = {
  404: '视频文件不存在，请选择其他视频',
  401: '登录已过期，请重新登录',
  500: '服务器错误，请稍后重试',
  default: '操作失败，请重试'
}

const DEFAULT_VIDEO = {
  url: '/uploads/reference/standard-exercise.mp4',
  thumbnail: '/uploads/reference/standard-exercise-thumb.jpg',
  id: 'standard-exercise-video'
}

// Store
const videoStore = useVideoStore()

// 响应式状态
const referenceVideo = ref({ ...DEFAULT_VIDEO })
const referencePlayerRef = ref(null)
const realTimeTrainingRef = ref(null)
const activeCollapse = ref(['1'])
const isRecording = ref(false)
const uploadDialogVisible = ref(false)
const recordedVideoFile = ref(null)
const showVideoSelector = ref(false)
const searchQuery = ref('')
const selectedVideo = ref(null)
const showHandSelector = ref(false)
const selectedHand = ref('')

// 生成带时间戳的标题
const generateUploadTitle = () => {
  const timestamp = dayjs().format('YYYY-MM-DD_HH-mm-ss')
  return `训练视频_${timestamp}`
}

// 训练小贴士数据
const trainingTips = [
  {
    icon: Timer,
    color: '#409EFF',
    title: '合理安排时间',
    content: '建议每次训练20-30分钟，每周3-4次'
  },
  {
    icon: Lightning,
    color: '#E6A23C',
    title: '循序渐进',
    content: '从基础动作开始，逐步增加难度和强度'
  },
  {
    icon: Star,
    color: '#67C23A',
    title: '保持专注',
    content: '集中注意力，保持正确的动作形态'
  }
]

// 计算属性
const filteredVideos = computed(() => {
  if (!searchQuery.value) return videoStore.videos
  const query = searchQuery.value.toLowerCase()
  return videoStore.videos.filter(video => 
    video.title.toLowerCase().includes(query)
  )
})

// 工具函数
const formatDuration = (seconds) => {
  if (!seconds) return '0:00'
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

const formatDate = (date) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

const handleError = (error, customMessage = '') => {
  console.error(error)
  const message = error.response?.data?.message || 
                 ERROR_MESSAGES[error.response?.status] || 
                 customMessage || 
                 ERROR_MESSAGES.default
  ElMessage.error(message)
}

// 视频相关方法
const selectVideo = (video) => {
  selectedVideo.value = video
}

const confirmVideoSelection = async () => {
  if (!selectedVideo.value) return
  
  try {
    referenceVideo.value = {
      url: selectedVideo.value.url,
      thumbnail: selectedVideo.value.thumbnail,
      id: selectedVideo.value.id
    }
    
    await nextTick()
    if (referencePlayerRef.value) {
      referencePlayerRef.value.load()
    }
    
    ElMessage.success('视频替换成功')
    showVideoSelector.value = false
  } catch (error) {
    handleError(error)
  }
}

const initVideoPlayer = async () => {
  try {
    if (referencePlayerRef.value) {
      await nextTick()
      
      if (referencePlayerRef.value.player) {
        referencePlayerRef.value.player.on('loadeddata', () => {
          console.log('规范视频加载完成')
        })
        referencePlayerRef.value.load()
      }
    }
  } catch (error) {
    handleError(error, '初始化视频播放器失败')
  }
}

// 录制相关方法
const startRecording = async () => {
  if (!selectedHand.value) {
    ElMessage.warning('请先选择要分析的手')
    return
  }
  
  if (realTimeTrainingRef.value) {
    await realTimeTrainingRef.value.startRecording(selectedHand.value)
  }
}

const stopRecording = async () => {
  if (realTimeTrainingRef.value) {
    await realTimeTrainingRef.value.stopRecording()
  }
}

const confirmHandSelection = () => {
  showHandSelector.value = false
  startRecording()
}

// 上传相关方法
const handleUploadSuccess = () => {
  uploadDialogVisible.value = false
  recordedVideoFile.value = null
  if (realTimeTrainingRef.value) {
    realTimeTrainingRef.value.handleUploadSuccess()
  }
}

// 事件处理
const handleReferenceError = (error) => {
  handleError(error, '视频加载失败，请检查网络连接或刷新页面重试')
}

const handleSearch = () => {
  // 搜索逻辑已经在computed的filteredVideos中实现
}

// 监听器
watch(recordedVideoFile, (newFile) => {
  if (newFile) {
    uploadDialogVisible.value = true
  }
})

// 生命周期钩子
onMounted(async () => {
  try {
    await videoStore.fetchVideos({ page: 1, pageSize: 1000 })
    setTimeout(initVideoPlayer, 100)
  } catch (error) {
    handleError(error, '获取视频列表失败，请刷新页面重试')
  }
})

onUnmounted(() => {
  if (referencePlayerRef.value?.player) {
    referencePlayerRef.value.player.dispose()
  }
})
</script>

<style lang="scss" scoped>
.training-container {
  padding: 24px;
  background-color: var(--el-bg-color-page);
  min-height: 100vh;
  position: fixed;
  top: 64px;
  left: 200px;
  right: 0;
  bottom: 0;
  overflow-y: auto;

  .page-header-card {
    margin-bottom: 24px;
    border-radius: 12px;
    transition: all 0.3s ease;
    border: none;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);

    &:hover {
      transform: translateY(-5px);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
    }

    :deep(.el-card__body) {
      padding: 20px;
    }

    .page-header {
      .header-content {
        h2 {
          margin: 0;
          font-size: 24px;
          font-weight: 600;
          color: var(--el-text-color-primary);
        }

        .subtitle {
          margin: 8px 0 0;
          font-size: 14px;
          color: var(--el-text-color-secondary);
        }
      }
    }
  }

  .el-card {
    margin-bottom: 20px;
    border-radius: 12px;
    transition: all 0.3s ease;
    border: none;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);

    &:hover {
      transform: translateY(-5px);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
    }

    :deep(.el-card__header) {
      padding: 16px 20px;
      border-bottom: 1px solid var(--el-border-color-light);
      background-color: var(--el-bg-color);
      border-radius: 12px 12px 0 0;
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      h3 {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }
    }
  }

  .reference-video,
  .camera-section {
    height: auto;
    margin-bottom: 24px;

    :deep(.el-card__body) {
      padding: 0;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .video-container {
      width: 100%;
      aspect-ratio: 16/9;
      background-color: var(--el-bg-color-page);
      border-radius: 0 0 12px 12px;
      overflow: hidden;

      :deep(.video-js) {
        width: 100% !important;
        height: 100% !important;
        background-color: var(--el-bg-color-page);

        .vjs-poster {
          background-size: contain;
          background-color: var(--el-bg-color-page);
        }
      }
    }
  }

  .info-card {
    height: auto;
    margin-bottom: 0;

    :deep(.el-card__body) {
      padding: 20px;
    }

    .el-collapse {
      --el-collapse-header-font-size: 14px;
      --el-collapse-content-font-size: 14px;
      border: none;

      .el-collapse-item {
        background-color: var(--el-bg-color-page);
        border-radius: 8px;
        margin-bottom: 8px;
        overflow: hidden;

        &:last-child {
          margin-bottom: 0;
        }

        :deep(.el-collapse-item__header) {
          padding: 12px 16px;
          font-weight: 500;
          border-bottom: none;
        }

        :deep(.el-collapse-item__content) {
          padding: 12px 16px;
          color: var(--el-text-color-regular);
        }
      }
    }

    .tip-item {
      text-align: center;
      padding: 16px;
      background-color: var(--el-bg-color-page);
      border-radius: 8px;
      transition: all 0.3s ease;

      &:hover {
        transform: translateY(-5px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      }

      .el-icon {
        margin-bottom: 12px;
      }

      h4 {
        margin: 8px 0;
        font-size: 16px;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }

      p {
        margin: 0;
        font-size: 14px;
        color: var(--el-text-color-secondary);
        line-height: 1.5;
      }
    }
  }
}

.video-selector {
  .video-list {
    margin-top: 16px;

    .video-item {
      display: flex;
      align-items: center;
      padding: 12px;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.3s ease;
      background-color: var(--el-bg-color-page);

      &:hover {
        background-color: var(--el-color-primary-light-9);
      }

      &.active {
        background-color: var(--el-color-primary-light-8);
      }

      .video-thumbnail {
        width: 160px;
        height: 90px;
        border-radius: 4px;
        margin-right: 16px;
      }

      .video-info {
        flex: 1;

        .video-title {
          font-size: 14px;
          font-weight: 500;
          color: var(--el-text-color-primary);
          margin-bottom: 8px;
        }

        .video-meta {
          font-size: 12px;
          color: var(--el-text-color-secondary);

          span {
            margin-right: 16px;
          }
        }
      }
    }
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.hand-selector {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}
</style> 
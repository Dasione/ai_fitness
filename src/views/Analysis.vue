<template>
  <div class="analysis-container">
    <el-dialog
      v-model="handSelectionVisible"
      title="请选择分析的动作是左手还是右手"
      width="30%"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <div class="hand-selection">
        <el-radio-group v-model="selectedHand">
          <el-radio label="left">左手</el-radio>
          <el-radio label="right">右手</el-radio>
        </el-radio-group>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handSelectionVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmHandSelection">
            确认
          </el-button>
        </span>
      </template>
    </el-dialog>

    <el-row :gutter="20">
      <el-col :span="16">
        <el-card class="video-card">
          <template #header>
            <div class="card-header">
              <span>视频播放</span>
              <el-button
                type="primary"
                :disabled="!currentVideo || isAnalyzing"
                @click="startAnalysis"
              >
                {{ isAnalyzing ? '分析中...' : analysisResults ? '再次分析' : '开始分析' }}
              </el-button>
            </div>
          </template>
          <div class="video-player">
            <video-player
              v-if="currentVideo"
              :src="currentVideo.url"
              :poster="currentVideo.thumbnail"
              @timeupdate="handleTimeUpdate"
            />
            <div v-else class="empty-player">
              请选择要分析的视频
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="video-list">
          <template #header>
            <div class="card-header">
              <span>运动视频列表</span>
              <el-input
                v-model="searchQuery"
                placeholder="输入视频标题"
                clearable
                @clear="handleSearch"
                @input="handleSearch"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </div>
          </template>
          <div class="video-list-container">
            <el-scrollbar>
              <div class="video-items">
                <div class="video-item" 
                  v-for="video in filteredVideos" 
                  :key="video.id"
                  :class="{ active: currentVideo?.id === video.id }"
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
              </div>
            </el-scrollbar>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row class="mt-4">
      <el-col :span="24">
        <el-card class="analysis-results">
          <template #header>
            <div class="card-header">
              <span>分析结果</span>
            </div>
          </template>
          <div v-if="currentVideo && analysisResults" class="results-content">
            <el-tabs v-model="activeTab">
              <el-tab-pane label="动作评分" name="scores">
                <div class="scores-section">
                  <el-row :gutter="20">
                    <el-col :span="8" v-for="(score, index) in processScores(analysisResults?.scores)" :key="index">
                      <el-card shadow="hover" class="score-card">
                        <div class="score-title">动作 {{ index + 1 }}</div>
                        <div class="score-value">{{ Number(score).toFixed(3) }}</div>
                        <div class="error-type">
                          动作类别：{{ getErrorTypeText(analysisResults?.cases[index]) }}
                        </div>
                      </el-card>
                    </el-col>
                  </el-row>
                </div>
              </el-tab-pane>
              <el-tab-pane label="动作建议" name="suggestions">
                <div class="suggestions-section">
                  <template v-if="analysisResults?.suggestions">
                    <div class="suggestions-content">
                      <div class="suggestion-text">
                        <template v-for="(line, index) in processedSuggestions" :key="index">
                          <template v-if="line.type === 'title'">
                            <h3 class="suggestion-title">{{ line.content }}</h3>
                          </template>
                          <template v-else-if="line.type === 'item'">
                            <div class="suggestion-item">
                              <span class="bullet">•</span>
                              <span class="item-text">{{ line.content }}</span>
                            </div>
                          </template>
                          <template v-else>
                            <p class="suggestion-paragraph">{{ line.content }}</p>
                          </template>
                        </template>
                      </div>
                    </div>
                  </template>
                  <div v-else class="empty-suggestions">
                    暂无动作建议
                  </div>
                </div>
              </el-tab-pane>
              <el-tab-pane label="问题片段" name="keyframes">
                <div class="video-segments-section">
                  <div v-if="analysisResults.videos.length > 0" class="video-segment full-analysis">
                    <h3>完整分析视频</h3>
                    <video-player
                      :src="processedFullVideo"
                      title="完整分析视频"
                    />
                  </div>
                  <div class="segments-title">问题片段分析</div>
                  <div v-for="(video, index) in processedVideos" :key="index" class="video-segment">
                    <div class="segment-header">
                      <h4>问题片段 {{ index + 1 }}</h4>
                      <div class="segment-info">
                        <span class="error-type">动作类别：{{ getErrorTypeText(analysisResults.cases[errorSegmentsMap[index]]) }}</span>
                        <span class="score">评分：{{ Number(analysisResults.scores[errorSegmentsMap[index]]).toFixed(3) }}</span>
                      </div>
                    </div>
                    <video-player
                      :src="video.url"
                      :title="`问题片段 ${index + 1}`"
                      :error-type="analysisResults.cases[errorSegmentsMap[index]]"
                      :score="analysisResults.scores[errorSegmentsMap[index]]"
                    />
                  </div>
                </div>
              </el-tab-pane>
            </el-tabs>
          </div>
          <div v-else-if="isAnalyzing" class="analyzing">
            <el-progress type="circle" :percentage="analysisProgress" />
            <div class="progress-text">正在分析中，请稍候...</div>
          </div>
          <div v-else-if="analysisResults?.status === 'error'" class="error-results">
            <el-alert
              :title="analysisResults.error_message || '分析失败'"
              type="error"
              :closable="false"
              show-icon
            />
          </div>
          <div v-else class="empty-results">
            暂无分析结果
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useVideoStore } from '@/store/modules/video'
import { Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRoute } from 'vue-router'
import VideoPlayer from '@/components/video/VideoPlayer.vue'
import dayjs from 'dayjs'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

// 常量定义
const ERROR_MESSAGES = {
  404: '视频文件不存在，请选择其他视频',
  401: '登录已过期，请重新登录',
  500: '服务器错误，请稍后重试',
  default: '操作失败，请重试'
}

const ERROR_TYPES = {
  'case0': '标准动作',
  'case1': '手臂复原不足',
  'case2': '手臂下放过直',
  'case3': '手肘抬起'
}

const POLLING_INTERVAL = 1000
const MAX_PROGRESS = 95
const PROGRESS_INCREMENT = 2
const INITIAL_PROGRESS = 5

// Store
const videoStore = useVideoStore()
const route = useRoute()

// 响应式状态
const currentVideo = ref(null)
const searchQuery = ref('')
const activeTab = ref('scores')
const isAnalyzing = ref(false)
const analysisProgress = ref(0)
const analysisResults = ref(null)
const handSelectionVisible = ref(false)
const selectedHand = ref('left')
const analysisPollingInterval = ref(null)

// 计算属性
const videos = computed(() => videoStore.videos)
const filteredVideos = computed(() => {
  if (!searchQuery.value) return videos.value
  const query = searchQuery.value.toLowerCase()
  return videos.value.filter(video => 
    video.title.toLowerCase().includes(query)
  )
})

const processedVideos = computed(() => {
  if (!analysisResults.value?.videos) return []
  return analysisResults.value.videos.slice(0, -1).map(video => ({
    url: video.replace('./', '/').replace(/\\/g, '/')
  }))
})

const processedFullVideo = computed(() => {
  if (!analysisResults.value?.videos || analysisResults.value.videos.length === 0) return ''
  const fullVideo = analysisResults.value.videos[analysisResults.value.videos.length - 1]
  return fullVideo.replace('./', '/').replace(/\\/g, '/')
})

const processedSuggestions = computed(() => {
  if (!analysisResults.value?.suggestions) return []
  
  const lines = Array.isArray(analysisResults.value.suggestions) 
    ? analysisResults.value.suggestions 
    : analysisResults.value.suggestions.split('\n')

  return lines.map(line => {
    const trimmedLine = line.trim()
    // 移除 markdown 标记
    if (trimmedLine.startsWith('```markdown')) {
      return null
    }
    // 移除末尾的 ``` 标记
    if (trimmedLine === '```') {
      return null
    }
    // 处理标题（移除 # 和 ** 标记）
    if (trimmedLine.startsWith('#')) {
      return {
        type: 'title',
        content: trimmedLine.replace(/^#+\s*/, '').replace(/\*\*/g, '')
      }
    }
    // 处理列表项（移除 - 和 ** 标记）
    if (trimmedLine.startsWith('-')) {
      return {
        type: 'item',
        content: trimmedLine.replace(/^-\s*/, '').replace(/\*\*/g, '')
      }
    }
    // 处理普通文本（移除 ** 标记）
    if (trimmedLine) {
      return {
        type: 'text',
        content: trimmedLine.replace(/\*\*/g, '')
      }
    }
    return null
  }).filter(Boolean)
})

// 添加新的计算属性来获取错误片段的索引映射
const errorSegmentsMap = computed(() => {
  if (!analysisResults.value?.cases || !analysisResults.value?.scores) return []
  
  // 找出所有错误片段（分数低于80或不是标准动作）
  return analysisResults.value.cases.reduce((acc, caseType, index) => {
    const score = analysisResults.value.scores[index]
    if (score < 80 || caseType !== 'category:case0') {
      acc.push(index)
    }
    return acc
  }, [])
})

// 添加新的计算属性来获取错误片段的数量
const errorSegmentsCount = computed(() => {
  if (!analysisResults.value?.cases || !analysisResults.value?.scores) return 0
  
  return analysisResults.value.cases.reduce((count, caseType, index) => {
    const score = analysisResults.value.scores[index]
    if (score < 80 || caseType !== 'case0') {
      return count + 1
    }
    return count
  }, 0)
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

const processScores = (scores) => {
  if (!Array.isArray(scores)) return []
  return scores.map(score => Number(score).toFixed(3))
}

const getErrorTypeText = (caseType) => {
  if (!caseType) return ''
  const caseValue = caseType.replace('category:', '').trim().toLowerCase()
  return ERROR_TYPES[caseValue] || caseValue
}

const renderMarkdown = (text) => {
  if (!text) return ''
  const rawHtml = marked.parse(text)
  return DOMPurify.sanitize(rawHtml)
}

// 视频相关方法
const selectVideo = async (video) => {
  currentVideo.value = video
  analysisResults.value = null
  isAnalyzing.value = false
  analysisProgress.value = 0
  handSelectionVisible.value = true
}

const startAnalysis = async () => {
  if (!currentVideo.value) {
    ElMessage.warning('请先选择要分析的视频')
    return
  }

  // 检查是否有正在进行的分析
  if (isAnalyzing.value) {
    try {
      await ElMessageBox.confirm(
        '低性能设备不建议同时进行多个分析',
        '警告',
        {
          confirmButtonText: '继续分析',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
    } catch (error) {
      return
    }
  }

  try {
    await handleAnalysis()
  } catch (error) {
    if (error !== 'cancel') {
      handleError(error)
    }
  }
}

const handleAnalysis = async () => {
  try {
    const result = await videoStore.getAnalysisResult(currentVideo.value.id, selectedHand.value)
    
    if (result) {
      if (result.status === 'completed') {
        const confirmed = await ElMessageBox.confirm(
          '该视频已有分析结果，是否重新分析？',
          '提示',
          {
            confirmButtonText: '重新分析',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        if (!confirmed) return
      }
      
      await startNewAnalysis()
    } else {
      await startNewAnalysis()
    }
  } catch (error) {
    if (error.response?.status !== 404) {
      handleError(error, '获取分析结果失败')
      return
    }
    await startNewAnalysis()
  }
}

const startNewAnalysis = async () => {
  try {
    isAnalyzing.value = true
    analysisProgress.value = INITIAL_PROGRESS
    analysisResults.value = null

    // 先清除可能存在的轮询
    if (analysisPollingInterval.value) {
      clearInterval(analysisPollingInterval.value)
      analysisPollingInterval.value = null
    }

    // 启动分析
    const response = await videoStore.startAnalysis(currentVideo.value.id, selectedHand.value)
    console.log('分析开始响应:', response)  // 添加日志

    // 立即开始轮询
    startPolling(currentVideo.value.id, selectedHand.value)
    
    // 显示提示信息
    ElMessage.info('视频正在分析中，请稍候...')
  } catch (error) {
    console.error('启动分析失败:', error)  // 添加错误日志
    handleError(error, '分析失败')
    isAnalyzing.value = false
    analysisProgress.value = 0
  }
}

const confirmHandSelection = async () => {
  handSelectionVisible.value = false
  ElMessage.info('正在查询分析结果...')
  
  try {
    const result = await videoStore.getAnalysisResult(currentVideo.value.id, selectedHand.value)
    if (result) {
      if (result.status === 'processing') {
        isAnalyzing.value = true
        analysisProgress.value = 0
        startPolling(currentVideo.value.id, selectedHand.value)
        ElMessage.info('视频正在分析中，请稍候...')
      } else if (result.status === 'completed') {
        analysisResults.value = {
          scores: result.score_arr,
          cases: result.case_arr,
          videos: result.output_arr,
          suggestions: result.suggestions ? result.suggestions.split('\n') : []
        }
        ElMessage.success('分析结果已显示')
      } else if (result.status === 'error') {
        ElMessage.error('分析失败：' + (result.error_message || '未知错误'))
      }
    } else {
      ElMessage.warning('暂无分析结果，请点击"开始分析"按钮')
    }
  } catch (error) {
    handleError(error)
  }
}

// 轮询相关方法
const startPolling = (videoId, hand) => {
  console.log('开始轮询:', { videoId, hand })  // 添加日志

  // 确保清除之前的轮询
  if (analysisPollingInterval.value) {
    clearInterval(analysisPollingInterval.value)
    analysisPollingInterval.value = null
  }

  let lastProgress = analysisProgress.value
  let stableCount = 0
  let pollCount = 0  // 添加轮询计数器

  // 立即执行一次查询
  const checkAnalysisStatus = async () => {
    try {
      console.log('轮询次数:', ++pollCount)  // 添加日志
      const result = await videoStore.getAnalysisResult(videoId, hand)
      console.log('轮询结果:', result)  // 添加日志
      
      if (result.status === 'completed') {
        clearInterval(analysisPollingInterval.value)
        analysisPollingInterval.value = null
        
        analysisResults.value = {
          scores: result.score_arr,
          cases: result.case_arr,
          videos: result.output_arr,
          suggestions: result.suggestions ? result.suggestions.split('\n') : []
        }
        isAnalyzing.value = false
        analysisProgress.value = 100
        ElMessage.success('分析完成')
      } else if (result.status === 'error') {
        clearInterval(analysisPollingInterval.value)
        analysisPollingInterval.value = null
        isAnalyzing.value = false
        analysisProgress.value = 0
        ElMessage.error('分析失败：' + (result.error_message || '未知错误'))
      } else if (result.status === 'processing') {
        // 检查进度是否停滞
        if (analysisProgress.value === lastProgress) {
          stableCount++
          if (stableCount >= 3) {
            analysisProgress.value = Math.min(MAX_PROGRESS, analysisProgress.value + PROGRESS_INCREMENT)
            stableCount = 0
          }
        } else {
          stableCount = 0
        }
        
        if (analysisProgress.value < MAX_PROGRESS) {
          analysisProgress.value = Math.min(MAX_PROGRESS, analysisProgress.value + PROGRESS_INCREMENT)
        }
        
        lastProgress = analysisProgress.value
      }
    } catch (error) {
      console.error('轮询出错:', error)  // 添加错误日志
      if (error.response?.status === 404) {
        console.log('分析记录不存在，继续轮询')  // 添加日志
        return
      }
      handleError(error)
      clearInterval(analysisPollingInterval.value)
      analysisPollingInterval.value = null
      isAnalyzing.value = false
      analysisProgress.value = 0
    }
  }

  // 立即执行一次
  checkAnalysisStatus()

  // 设置定时轮询
  analysisPollingInterval.value = setInterval(checkAnalysisStatus, POLLING_INTERVAL)
}

// 事件处理
const handleTimeUpdate = (currentTime) => {
  // 处理视频播放进度更新
  if (analysisResults.value?.suggestions) {
    // 可以根据当前时间显示相应的建议
  }
}

const handleSearch = () => {
  // 搜索逻辑已经在computed的filteredVideos中实现
}

// 监听器
watch(
  () => route.query,
  async (newQuery) => {
    if (newQuery.videoId) {
      const video = videos.value.find(v => v.id === newQuery.videoId)
      if (video) {
        currentVideo.value = video
        selectedHand.value = newQuery.hand || 'left'
        try {
          const result = await videoStore.getAnalysisResult(video.id, selectedHand.value)
          if (result && result.status === 'completed') {
            analysisResults.value = {
              scores: result.score_arr,
              cases: result.case_arr,
              videos: result.output_arr,
              suggestions: result.suggestions ? result.suggestions.split('\n') : []
            }
          }
        } catch (error) {
          if (error.response?.status === 404) return
          handleError(error)
        }
      }
    }
  },
  { immediate: true }
)

// 生命周期钩子
onMounted(async () => {
  try {
    await videoStore.fetchVideos({ page: 1, pageSize: 1000 })
    
    const videoId = route.query.videoId
    if (videoId) {
      await nextTick()
      const video = videos.value.find(v => v.id === videoId)
      
      if (video) {
        currentVideo.value = video
        await nextTick()
        handSelectionVisible.value = true
      } else {
        ElMessage.warning('未找到指定的视频')
      }
    }
  } catch (error) {
    handleError(error, '获取视频列表失败')
  }
})

onUnmounted(() => {
  if (analysisPollingInterval.value) {
    clearInterval(analysisPollingInterval.value)
  }
})
</script>

<style lang="scss" scoped>
.analysis-container {
  padding: 24px;
  background-color: var(--el-bg-color-page);
  min-height: 100vh;
  position: fixed;
  top: 64px;
  left: 200px;
  right: 0;
  bottom: 0;
  overflow-y: auto;
  
  :deep(.el-card) {
    border-radius: 12px;
    transition: all 0.3s ease;
    border: none;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);

    &:hover {
      transform: translateY(-5px);
      box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.1);
    }

    .el-card__header {
      padding: 16px 20px;
      border-bottom: 1px solid var(--el-border-color-light);
      background-color: var(--el-bg-color);
      border-radius: 12px 12px 0 0;
    }
  }

  .video-card {
    margin-bottom: 24px;
    height: calc(69vh);

    .video-player {
      width: 100%;
      aspect-ratio: 16/9;
      background-color: #000;
      border-radius: 0 0 12px 12px;
      overflow: hidden;
    }

    .empty-player {
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--el-text-color-secondary);
      font-size: 16px;
      background-color: var(--el-bg-color-page);
      border-radius: 0 0 12px 12px;
    }
  }

  .video-list {
    height: calc(69vh);

    :deep(.el-card__body) {
      height: calc(100% - 60px);
      padding: 0;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .video-list-container {
      flex: 1;
      overflow: hidden;

      .el-scrollbar {
        height: 100%;
      }

      .video-items {
        padding: 16px;
      }
    }

    .card-header :deep(.el-input) {
      width: 50%;
    }

    .video-item {
      display: flex;
      padding: 16px;
      cursor: pointer;
      transition: all 0.3s ease;
      border-bottom: 1px solid var(--el-border-color-light);
      background-color: var(--el-bg-color);

      &:hover {
        background-color: var(--el-color-primary-light-9);
      }

      &.active {
        background-color: var(--el-color-primary-light-8);
      }

      .video-thumbnail {
        width: 160px;
        height: 90px;
        border-radius: 8px;
        margin-right: 16px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      }

      .video-info {
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: space-between;

        .video-title {
          font-size: 14px;
          color: var(--el-text-color-primary);
          margin-bottom: 8px;
          display: -webkit-box;
          -webkit-box-orient: vertical;
          overflow: hidden;
          font-weight: 500;
        }

        .video-meta {
          font-size: 12px;
          color: var(--el-text-color-secondary);
          display: flex;
          justify-content: space-between;
        }
      }
    }
  }

  .analysis-results {
    margin-top: 24px;
    border-radius: 12px;
    transition: all 0.3s ease;
    border: none;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);

    &:hover {
      transform: translateY(-5px);
      box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.1);
    }

    :deep(.el-card__header) {
      padding: 16px 20px;
      border-bottom: 1px solid var(--el-border-color-light);
      background-color: var(--el-bg-color);
      border-radius: 12px 12px 0 0;
    }

    .scores-section {
      padding: 24px;
    }

    .score-card {
      margin-bottom: 24px;
      text-align: center;
      border-radius: 12px;
      transition: all 0.3s ease;
      border: none;
      box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);

      &:hover {
        transform: translateY(-5px);
        box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.1);
      }

      .score-title {
        font-size: 16px;
        color: #303133;
        margin-bottom: 12px;
        font-weight: 500;
      }

      .score-value {
        font-size: 28px;
        color: #409eff;
        margin-bottom: 12px;
        font-weight: 600;
        font-family: 'DIN Alternate', sans-serif;
      }

      .error-type {
        font-size: 14px;
        color: #909399;
      }
    }

    .suggestions-section {
      padding: 24px;

      .suggestions-content {
        line-height: 1.6;
        padding: 24px;
        background-color: #fff;
        border-radius: 12px;
        box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);

        .suggestion-title {
          font-size: 18px;
          font-weight: 600;
          color: #303133;
          margin: 20px 0 16px;
          padding-bottom: 8px;
          border-bottom: 2px solid #409EFF;

          &:first-child {
            margin-top: 0;
          }
        }

        .suggestion-item {
          display: flex;
          align-items: flex-start;
          margin: 8px 0;
          padding: 8px 16px;

          .bullet {
            color: #409EFF;
            margin-right: 8px;
            font-size: 16px;
          }

          .item-text {
            color: #606266;
            flex: 1;
            line-height: 1.6;
          }
        }

        .suggestion-paragraph {
          margin: 12px 0;
          color: #606266;
          line-height: 1.6;
        }
      }

      .empty-suggestions {
        text-align: center;
        color: #909399;
        padding: 48px 0;
        font-size: 14px;
      }
    }

    .video-segments-section {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 24px;
      padding: 24px;

      .full-analysis {
        grid-column: 1 / -1;
        width: 100%;
        
        :deep(.video-js) {
          width: 100% !important;
          height: auto !important;
          aspect-ratio: 16/9;
        }
      }
    }

    .video-segment {
      margin-bottom: 0;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
      transition: all 0.3s ease;

      &:hover {
        transform: translateY(-5px);
        box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.1);
      }
    }

    .segments-title {
      grid-column: 1 / -1;
      font-size: 18px;
      font-weight: 600;
      color: #303133;
      margin: 24px 0 16px;
      padding-bottom: 16px;
      border-bottom: 1px solid #ebeef5;
    }

    .segment-header {
      padding: 16px;
      background-color: #fafafa;
      border-bottom: 1px solid #ebeef5;

      h4 {
        margin: 0 0 8px;
        font-size: 16px;
        color: #303133;
        font-weight: 500;
      }

      .segment-info {
        display: flex;
        flex-direction: column;
        gap: 8px;
        font-size: 14px;
        color: #606266;

        .error-type {
          color: #409eff;
        }

        .score {
          color: #67c23a;
          font-weight: 600;
        }
      }
    }

    .analyzing {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 48px 0;
    }

    .progress-text {
      margin-top: 24px;
      color: #909399;
      font-size: 14px;
    }

    .error-results {
      padding: 24px;
      text-align: center;
      
      :deep(.el-alert) {
        max-width: 600px;
        margin: 0 auto;
      }
    }

    .empty-results {
      text-align: center;
      color: #909399;
      padding: 48px 0;
      font-size: 14px;
    }
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    span {
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }
  }
}

@media screen and (max-width: 768px) {
  .analysis-container {
    left: 0;
    top: 56px;
    padding: 16px;
    .video-segments-section {
      grid-template-columns: 1fr;
      gap: 16px;
      padding: 16px;
    }

    .video-item {
      padding: 12px;

      .video-thumbnail {
        width: 120px;
        height: 68px;
      }
    }
  }
}

:deep(.el-dialog) {
  border-radius: 12px;
  overflow: hidden;

  .el-dialog__header {
    margin: 0;
    padding: 20px;
    background-color: #fafafa;
    border-bottom: 1px solid #ebeef5;
  }

  .el-dialog__body {
    padding: 24px;
  }

  .el-dialog__footer {
    padding: 16px 20px;
    border-top: 1px solid #ebeef5;
  }
}

.hand-selection {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}
</style> 
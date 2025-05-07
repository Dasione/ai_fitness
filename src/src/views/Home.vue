<template>
  <div class="home-container">
    <!-- 欢迎卡片 -->
    <el-card class="welcome-card" shadow="hover">
      <div class="welcome-content">
        <div class="welcome-text">
          <h2>欢迎回来，{{ userStore.userInfo?.username || '用户' }}</h2>
          <p class="subtitle">今天也要坚持训练哦！</p>
        </div>
        <div class="quick-stats">
          <div v-for="stat in statsList" :key="stat.label" class="stat-item">
            <el-icon :size="24" :color="stat.color">
              <component :is="stat.icon" />
            </el-icon>
            <div class="stat-info">
              <span class="stat-value">{{ stat.value }}</span>
              <span class="stat-label">{{ stat.label }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 功能卡片网格 -->
    <el-row :gutter="0" class="feature-grid">
      <!-- 左侧：最近训练视频 -->
      <el-col :span="16">
        <el-card class="video-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <h3>最近训练视频</h3>
              <el-button type="primary" link @click="router.push('/training')">
                查看全部
              </el-button>
            </div>
          </template>
          <div class="video-container">
            <VideoPlayer
              v-if="latestTraining"
              :src="latestTraining.url"
              :poster="latestTraining.thumbnail"
              :controls="true"
              :autoplay="false"
              preload="auto"
              @error="handleVideoError"
            />
            <el-empty v-else description="暂无训练视频" />
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：功能卡片 -->
      <el-col :span="8">
        <el-row :gutter="16" class="feature-cards">
          <el-col v-for="feature in features" :key="feature.title" :span="24">
            <el-card class="feature-card" shadow="hover" @click="router.push(feature.route)">
              <div class="feature-content">
                <el-icon :size="feature.iconSize" :color="feature.color">
                  <component :is="feature.icon" />
                </el-icon>
                <div class="feature-info">
                  <h3>{{ feature.title }}</h3>
                  <p>{{ feature.description }}</p>
                </div>
                <el-button type="primary" link>{{ feature.buttonText }}</el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-col>
    </el-row>

    <!-- 最近训练记录 -->
    <el-card class="recent-card" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>最近分析</span>
        </div>
      </template>
      <el-table :data="recentTrainings.slice(0, 4)" style="width: 100%">
        <el-table-column prop="videoTitle" label="视频标题" />
        <el-table-column prop="date" label="分析时间" width="200">
          <template #default="scope">
            {{ formatDate(scope.row.date) }}
          </template>
        </el-table-column>
        <el-table-column prop="score" label="评分" width="100">
          <template #default="scope">
            <el-tag :type="getScoreType(scope.row.score)">
              {{ scope.row.score ? scope.row.score.toFixed(2) : '暂无评分' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column fixed="right" label="操作" width="130">
          <template #default="scope">
            <el-button link type="primary" @click="viewAnalysis(scope.row)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/modules/user'
import { useVideoStore } from '@/store/modules/video'
import { VideoPlay, Timer, Star, Search, Folder } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import VideoPlayer from '@/components/video/VideoPlayer.vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const videoStore = useVideoStore()

// 统计数据
const stats = ref({
  totalVideos: 0,
  totalDuration: 0,
  averageScore: 0
})

// 最近训练记录
const recentTrainings = ref([])
const latestTraining = ref(null)
const loading = ref(false)

// 功能卡片配置
const features = [
  {
    title: '训练指导',
    description: '观看规范动作示范，跟随视频进行训练',
    icon: 'VideoPlay',
    iconSize: 60,
    color: '#409EFF',
    route: '/training',
    buttonText: '开始训练'
  },
  {
    title: '动作分析',
    description: '分析训练视频，获取专业建议',
    icon: 'Search',
    iconSize: 50,
    color: '#67C23A',
    route: '/analysis',
    buttonText: '查看分析'
  },
  {
    title: '视频管理',
    description: '管理您的训练视频和标准动作视频',
    icon: 'Folder',
    iconSize: 50,
    color: '#E6A23C',
    route: '/videos',
    buttonText: '管理视频'
  }
]

// 统计数据列表
const statsList = computed(() => [
  {
    icon: 'VideoPlay',
    value: stats.value.totalVideos || 0,
    label: '训练次数',
    color: '#409EFF'
  },
  {
    icon: 'Timer',
    value: formatDuration(stats.value.totalDuration || 0),
    label: '训练时长',
    color: '#67C23A'
  },
  {
    icon: 'Star',
    value: stats.value.averageScore || 0,
    label: '平均得分',
    color: '#E6A23C'
  }
])

// 工具函数
const formatDuration = (seconds) => {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

const formatDate = (date) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

const getScoreType = (score) => {
  if (!score) return 'info'  
  if (score >= 90) return 'success'
  if (score >= 80) return 'warning'
  return 'danger'
}

const getStatusType = (status) => {
  const types = {
    completed: 'success',
    processing: 'warning',
    error: 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    completed: '已完成',
    processing: '处理中',
    error: '失败'
  }
  return texts[status] || status
}

// 业务函数
const viewAnalysis = (analysis) => {
  router.push({
    path: '/analysis',
    query: {
      videoId: analysis.videoId,
      hand: analysis.hand || 'left'
    }
  })
}

const handleVideoError = (error) => {
  console.error('视频加载错误:', error)
  ElMessage.error('视频加载失败，请稍后重试')
}

// 数据获取
const fetchStats = async () => {
  loading.value = true
  try {
    // 获取仪表盘统计数据
    const data = await videoStore.fetchDashboardStats()
    stats.value = {
      totalVideos: data.totalVideos || 0,
      totalDuration: data.totalDuration || 0,
      averageScore: data.recentAnalysis?.length > 0 
        ? (data.recentAnalysis.reduce((sum, item) => sum + (item.score || 0), 0) / data.recentAnalysis.length).toFixed(1)
        : 0
    }
    // 设置最近训练记录
    recentTrainings.value = data.recentAnalysis || []

    // 获取最新的训练视频
    const { videos } = await videoStore.fetchVideos({ page: 1, pageSize: 1 })
    if (videos && videos.length > 0) {
      const latestVideo = videos[0]
      latestTraining.value = {
        url: latestVideo.url,
        thumbnail: latestVideo.thumbnail,
        title: latestVideo.title
      }
    }
  } catch (error) {
    console.error('获取数据失败:', error)
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

// 生命周期钩子
onMounted(async () => {
  await fetchStats()
})
</script>

<style lang="scss" scoped>
.home-container {
  padding: 24px;
  background-color: #f5f7fa;
  min-height: 100vh;
  position: fixed;
  top: 64px;
  left: 200px;
  right: 0;
  bottom: 0;
  overflow-y: auto;

  .welcome-card {
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
      padding: 24px;
    }

    .welcome-content {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .welcome-text {
        h2 {
          margin: 0;
          font-size: 24px;
          font-weight: 600;
          color: #303133;
        }

        .subtitle {
          margin: 8px 0 0;
          font-size: 14px;
          color: #909399;
        }
      }

      .quick-stats {
        display: flex;
        gap: 24px;
        margin-top: 24px;

        .stat-item {
          display: flex;
          align-items: center;
          gap: 12px;

          .stat-info {
            display: flex;
            flex-direction: column;

            .stat-value {
              font-size: 20px;
              font-weight: 600;
              color: var(--el-text-color-primary);
            }

            .stat-label {
              font-size: 12px;
              color: var(--el-text-color-secondary);
            }
          }
        }
      }
    }
  }

  .feature-grid {
    margin-bottom: 24px;
    width: 100%;

    :deep(.el-row) {
      margin-left: 0 !important;
      margin-right: 0 !important;
      width: 100%;
    }

    :deep(.el-col) {
      padding-left: 0 !important;
      padding-right: 0 !important;
    }

    .video-card {
      height: 100%;
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
        border-bottom: 1px solid #ebeef5;
        background-color: #fafafa;
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
          color: #303133;
        }
      }

      .video-container {
        width: 100%;
        aspect-ratio: 16/9;
        background-color: #f5f7fa;
        border-radius: 0 0 12px 12px;
        overflow: hidden;

        :deep(.video-js) {
          width: 100% !important;
          height: 100% !important;
          background-color: #f5f7fa;

          .vjs-poster {
            background-size: contain;
            background-color: #f5f7fa;
          }
        }
      }
    }

    .feature-cards {
      height: 100%;
      display: flex;
      flex-direction: column;
      gap: 12px;
      padding-left: 24px;

      .el-col {
        flex: 1;
        min-height: 0;
      }

      .feature-card {
        flex: 1;
        min-height: 0;
        height: calc((310% - 25px) / 3);
        border-radius: 12px;
        transition: all 0.3s ease;
        border: none;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
        cursor: pointer;

        &:hover {
          transform: translateY(-5px);
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
        }

        :deep(.el-card__body) {
          height: 100%;
          padding: 16px;
          display: flex;
          align-items: center;
        }

        .feature-content {
          width: 100%;
          display: flex;
          align-items: center;
          gap: 24px;

          .el-icon {
            font-size: 60px;
          }

          .feature-info {
            flex: 1;

            h3 {
              margin: 0 0 8px;
              font-size: 18px;
              font-weight: 600;
              color: #303133;
            }

            p {
              margin: 0;
              font-size: 14px;
              color: #909399;
              line-height: 1.5;
            }
          }
        }
      }
    }
  }

  .recent-card {
    margin-bottom: 24px;
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
      border-bottom: 1px solid #ebeef5;
      background-color: #fafafa;
      border-radius: 12px 12px 0 0;
    }

    :deep(.el-table) {
      border-radius: 0 0 12px 12px;
      overflow: hidden;

      th {
        background-color: #f5f7fa;
        color: #606266;
        font-weight: 600;
        padding: 12px 0;
      }

      td {
        padding: 12px 0;
      }

      .el-tag {
        border-radius: 4px;
        padding: 0 8px;
        height: 24px;
        line-height: 24px;
      }

      .el-button {
        padding: 4px 8px;
        font-size: 13px;
      }
    }
  }
}

@media screen and (max-width: 768px) {
  .home-container {
    left: 0;
    top: 56px;
    padding: 16px;

    .welcome-card {
      margin-bottom: 16px;

      :deep(.el-card__body) {
        padding: 16px;
      }

      .welcome-content {
        flex-direction: column;
        align-items: flex-start;
        gap: 16px;

        .welcome-text {
          h2 {
            font-size: 20px;
          }
        }

        .quick-stats {
          width: 100%;
          justify-content: space-between;
          gap: 16px;
        }
      }
    }

    .feature-grid {
      flex-direction: column;

      .el-col {
        width: 100%;
        margin-bottom: 16px;
      }

      .feature-cards {
        .feature-card {
          height: auto;
        }
      }
    }
  }
}
</style> 
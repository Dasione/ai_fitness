<template>
  <div class="ranking-container">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card class="ranking-card" v-loading="loading">
          <template #header>
            <div class="card-header">
              <span>用户锻炼排行榜</span>
              <el-button @click="refreshRanking" :disabled="loading" type="primary" plain>
                <el-icon><Refresh /></el-icon> 刷新排行榜
              </el-button>
            </div>
          </template>
          <el-table :data="userRanking" style="width: 100%">
            <el-table-column type="index" label="排名" width="80">
              <template #default="scope">
                <div class="ranking-number" :class="getRankClass(scope.$index)">
                  {{ scope.$index + 1 }}
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="username" label="用户名">
              <template #default="scope">
                <div class="user-info">
                  <el-avatar :size="40" :src="formatAvatarUrl(scope.row.avatar)">
                    {{ getInitial(scope.row.username) }}
                  </el-avatar>
                  <span class="username">{{ scope.row.username }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="totalDuration" label="训练时长" width="180">
              <template #default="scope">
                <div class="duration-info">
                  <el-icon><Timer /></el-icon>
                  <span>{{ formatDuration(scope.row.totalDuration) }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="videoCount" label="训练视频数" width="120">
              <template #default="scope">
                <div class="video-count">
                  <el-icon><VideoCamera /></el-icon>
                  <span>{{ scope.row.videoCount || 0 }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="averageScore" label="平均评分" width="120">
              <template #default="scope">
                <el-progress 
                  :percentage="scope.row.averageScore" 
                  :color="getScoreColor(scope.row.averageScore)"
                  :format="formatScore"
                />
              </template>
            </el-table-column>
            <el-table-column prop="lastActivity" label="最近活动时间" width="180">
              <template #default="scope">
                <div class="activity-time">
                  <el-icon><Calendar /></el-icon>
                  <span>{{ formatDate(scope.row.lastActivity) }}</span>
                </div>
              </template>
            </el-table-column>
          </el-table>
          
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 30, 50]"
              layout="total, sizes, prev, pager, next, jumper"
              :total="totalUsers"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <el-card class="chart-card" v-loading="loading">
          <template #header>
            <div class="card-header">
              <span>训练时长排行</span>
            </div>
          </template>
          <div ref="durationChart" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="chart-card" v-loading="loading">
          <template #header>
            <div class="card-header">
              <span>评分排行</span>
            </div>
          </template>
          <div ref="scoreChart" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { VideoCamera, Timer, Calendar, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { useVideoStore } from '@/store/modules/video'
import dayjs from 'dayjs'

// 常量定义
const ERROR_MESSAGES = {
  401: '登录已过期，请重新登录',
  500: '服务器错误，请稍后重试',
  default: '获取排行榜失败，请重试'
}

const PAGE_SIZES = [10, 20, 30, 50]
const CHART_COLORS = {
  duration: {
    gradient: [
      { offset: 0, color: '#83bff6' },
      { offset: 0.5, color: '#188df0' },
      { offset: 1, color: '#188df0' }
    ],
    emphasis: [
      { offset: 0, color: '#2378f7' },
      { offset: 0.7, color: '#2378f7' },
      { offset: 1, color: '#83bff6' }
    ]
  },
  score: {
    excellent: '#67C23A',
    good: '#E6A23C',
    fair: '#F56C6C',
    poor: '#909399'
  }
}

// Store
const videoStore = useVideoStore()

// 响应式状态
const currentPage = ref(1)
const pageSize = ref(10)
const totalUsers = ref(0)
const userRanking = ref([])
const loading = ref(false)
const durationChart = ref(null)
const scoreChart = ref(null)

// 图表实例
let durationChartInstance = null
let scoreChartInstance = null

// 计算属性
const topUsers = computed(() => userRanking.value.slice(0, 10))

// 工具函数
const formatDuration = (seconds) => {
  if (!seconds) return '0:00'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const remainingSeconds = seconds % 60
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
  }
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

const formatDate = (date) => {
  if (!date) return '暂无数据'
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

const formatScore = (percentage) => {
  return percentage.toFixed(1)
}

const getRankClass = (index) => {
  if (index === 0) return 'rank-first'
  if (index === 1) return 'rank-second'
  if (index === 2) return 'rank-third'
  return ''
}

const getScoreColor = (score) => {
  if (score >= 90) return CHART_COLORS.score.excellent
  if (score >= 80) return CHART_COLORS.score.good
  if (score >= 70) return CHART_COLORS.score.fair
  return CHART_COLORS.score.poor
}

const formatAvatarUrl = (avatar) => {
  if (!avatar) return ''
  if (avatar.startsWith('http://') || avatar.startsWith('https://')) return avatar
  if (avatar.startsWith('/')) return avatar
  if (avatar.startsWith('uploads/')) return '/' + avatar
  return `/uploads/avatars/${avatar}`
}

const getInitial = (username) => {
  if (!username) return '?'
  return username.charAt(0).toUpperCase()
}

const handleError = (error, customMessage = '') => {
  console.error(error)
  const message = error.response?.data?.message || 
                 ERROR_MESSAGES[error.response?.status] || 
                 customMessage || 
                 ERROR_MESSAGES.default
  ElMessage.error(message)
}

// 图表相关方法
const initDurationChart = () => {
  if (!durationChart.value) return
  
  if (durationChartInstance) {
    durationChartInstance.dispose()
  }
  
  durationChartInstance = echarts.init(durationChart.value)
  
  const usernames = topUsers.value.map(user => user.username)
  const durations = topUsers.value.map(user => Math.round(user.totalDuration / 60))
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: '{b}: {c} 分钟'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: '时长(分钟)',
      axisLabel: { formatter: '{value} 分钟' }
    },
    yAxis: {
      type: 'category',
      data: usernames.reverse(),
      axisLabel: {
        interval: 0,
        width: 100,
        overflow: 'truncate'
      }
    },
    series: [
      {
        name: '训练时长',
        type: 'bar',
        data: durations.reverse(),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, CHART_COLORS.duration.gradient)
        },
        emphasis: {
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 1, 0, CHART_COLORS.duration.emphasis)
          }
        }
      }
    ]
  }
  
  durationChartInstance.setOption(option)
}

const initScoreChart = () => {
  if (!scoreChart.value) return
  
  if (scoreChartInstance) {
    scoreChartInstance.dispose()
  }
  
  scoreChartInstance = echarts.init(scoreChart.value)
  
  const topScorers = [...userRanking.value]
    .sort((a, b) => b.averageScore - a.averageScore)
    .slice(0, 10)
  
  const usernames = topScorers.map(user => user.username)
  const scores = topScorers.map(user => user.averageScore)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: '{b}: {c} 分'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: '评分',
      min: 0,
      max: 100,
      axisLabel: { formatter: '{value} 分' }
    },
    yAxis: {
      type: 'category',
      data: usernames.reverse(),
      axisLabel: {
        interval: 0,
        width: 100,
        overflow: 'truncate'
      }
    },
    series: [
      {
        name: '平均评分',
        type: 'bar',
        data: scores.reverse(),
        itemStyle: {
          color: params => getScoreColor(params.data)
        }
      }
    ]
  }
  
  scoreChartInstance.setOption(option)
}

// 数据获取相关方法
const fetchUserRanking = async () => {
  loading.value = true
  try {
    const result = await videoStore.fetchUserRanking({
      page: currentPage.value,
      pageSize: pageSize.value
    })
    
    userRanking.value = result.data.map(user => ({
      ...user,
      videoCount: user.videoCount || 0,
      lastActivity: user.lastActivity || new Date().toISOString()
    }))
    
    totalUsers.value = result.totalCount
    
    await nextTick()
    initDurationChart()
    initScoreChart()
  } catch (error) {
    handleError(error)
  } finally {
    loading.value = false
  }
}

// 事件处理方法
const handleSizeChange = (val) => {
  pageSize.value = val
  fetchUserRanking()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  fetchUserRanking()
}

const refreshRanking = () => {
  fetchUserRanking()
}

const handleResize = () => {
  durationChartInstance?.resize()
  scoreChartInstance?.resize()
}

// 生命周期钩子
onMounted(() => {
  fetchUserRanking()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  durationChartInstance?.dispose()
  scoreChartInstance?.dispose()
})
</script>

<style lang="scss" scoped>
.ranking-container {
  padding: 24px;
  background-color: var(--el-bg-color-page);
  min-height: 100vh;
  position: fixed;
  top: 64px;
  left: 200px;
  right: 0;
  bottom: 0;
  overflow-y: auto;

  .ranking-card {
    margin-bottom: 24px;
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

    :deep(.el-table) {
      border-radius: 0 0 12px 12px;
      overflow: hidden;

      th {
        background-color: var(--el-bg-color-page);
        color: var(--el-text-color-regular);
        font-weight: 600;
        padding: 12px 0;
      }

      td {
        padding: 12px 0;
      }
    }

    .ranking-number {
      width: 36px;
      height: 36px;
      line-height: 36px;
      text-align: center;
      border-radius: 50%;
      margin: 0 auto;
      font-weight: bold;
      
      &.rank-first {
        background-color: var(--el-color-danger);
        color: var(--el-color-white);
        font-size: 18px;
      }
      
      &.rank-second {
        background-color: var(--el-color-warning);
        color: var(--el-color-white);
        font-size: 16px;
      }
      
      &.rank-third {
        background-color: var(--el-color-primary);
        color: var(--el-color-white);
        font-size: 14px;
      }
    }

    .user-info {
      display: flex;
      align-items: center;
      
      .username {
        margin-left: 12px;
        font-weight: 500;
        color: var(--el-text-color-primary);
      }
    }

    .duration-info,
    .video-count,
    .activity-time {
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--el-text-color-regular);

      .el-icon {
        font-size: 16px;
      }
    }
  }

  .chart-row {
    margin-top: 24px;
  }

  .chart-card {
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

    .chart-container {
      height: 400px;
      padding: 20px;
    }
  }

  .pagination-container {
    margin-top: 20px;
    display: flex;
    justify-content: center;
    padding: 16px;
    background-color: var(--el-bg-color);
    border-radius: 0 0 12px 12px;
  }
}

// 响应式布局
@media screen and (max-width: 768px) {
  .ranking-container {
    left: 0;
    top: 56px;
    padding: 16px;

    .chart-row {
      .el-col {
        width: 100%;
        margin-bottom: 16px;
      }
    }

    .chart-card {
      .chart-container {
        height: 300px;
        padding: 10px;
      }
    }

    .ranking-number {
      width: 32px;
      height: 32px;
      line-height: 32px;
      font-size: 14px;

      &.rank-first {
        font-size: 16px;
      }

      &.rank-second {
        font-size: 14px;
      }

      &.rank-third {
        font-size: 12px;
      }
    }

    .user-info {
      .username {
        font-size: 14px;
      }
    }
  }
}
</style> 
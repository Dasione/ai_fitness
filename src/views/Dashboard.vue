<template>
  <div class="dashboard-container">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card class="stat-card" v-loading="loading">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon><VideoCamera /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.totalVideos }}</div>
              <div class="stat-label">训练视频总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card" v-loading="loading">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon><Timer /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatDuration(stats.totalDuration) }}</div>
              <div class="stat-label">训练总时长（分钟）</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card" v-loading="loading">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon><DataAnalysis /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.totalAnalysis }}</div>
              <div class="stat-label">训练分析次数</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <el-card class="chart-card" v-loading="loading">
          <template #header>
            <div class="card-header">
              <span>最近一周训练统计</span>
              <el-button type="primary" plain size="small" @click="openGoalSettings">
                <el-icon><Setting /></el-icon> 设置目标
              </el-button>
            </div>
          </template>
          <div class="weekly-stats">
            <div class="stats-header">
              <div class="date-range">{{ getLastWeekDateRange() }}</div>
            </div>
            
            <div class="stats-grid">
              <div class="stat-card-mini">
                <div class="stat-icon-wrapper duration-icon">
                  <el-icon><Timer /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ formatDurationHours(stats.weeklyDuration || 0) }}</div>
                  <div class="stat-label">训练时长(小时)</div>
                </div>
                <el-progress 
                  :percentage="getDurationPercentage()" 
                  :color="getProgressColor(getDurationPercentage())"
                  :show-text="false"
                  :striped="true"
                  :striped-flow="true"
                />
                <div class="stat-comparison">
                  <span :class="getComparisonClass(stats.weeklyDuration, trainingGoals.duration * 3600)">
                    <el-icon v-if="stats.weeklyDuration >= trainingGoals.duration * 3600"><ArrowUp /></el-icon>
                    <el-icon v-else><ArrowDown /></el-icon>
                    {{ formatDurationHours(Math.abs(stats.weeklyDuration - trainingGoals.duration * 3600)) }}
                  </span>
                  <span class="comparison-label">vs 目标({{ trainingGoals.duration }}小时)</span>
                </div>
              </div>
              
              <div class="stat-card-mini">
                <div class="stat-icon-wrapper score-icon">
                  <el-icon><DataAnalysis /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ (stats.weeklyAverageScore || 0).toFixed(1) }}</div>
                  <div class="stat-label">平均评分</div>
                </div>
                <el-progress 
                  :percentage="stats.weeklyAverageScore || 0" 
                  :color="getScoreColor(stats.weeklyAverageScore)"
                  :show-text="false"
                />
                <div class="stat-comparison">
                  <span :class="getComparisonClass(stats.weeklyAverageScore, trainingGoals.score)">
                    <el-icon v-if="stats.weeklyAverageScore >= trainingGoals.score"><ArrowUp /></el-icon>
                    <el-icon v-else><ArrowDown /></el-icon>
                    {{ Math.abs((stats.weeklyAverageScore || 0) - trainingGoals.score).toFixed(1) }}
                  </span>
                  <span class="comparison-label">vs 目标({{ trainingGoals.score }}分)</span>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="chart-card" v-loading="loading">
          <template #header>
            <div class="card-header">
              <span>评分分布</span>
            </div>
          </template>
          <div ref="scoreDistributionChart" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :span="24">
        <el-card class="chart-card" v-loading="loading">
          <template #header>
            <div class="card-header">
              <span>评分趋势</span>
            </div>
          </template>
          <div ref="scoreTrendChart" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :span="24">
        <el-card class="recent-card" v-loading="loading">
          <template #header>
            <div class="card-header">
              <span>最近分析</span>
            </div>
          </template>
          <el-table :data="recentAnalysis.slice(0, 4)" style="width: 100%">
            <el-table-column prop="videoTitle" label="视频标题" />
            <el-table-column prop="date" label="分析时间" width="200">
              <template #default="scope">
                {{ formatDate(scope.row.date) }}
              </template>
            </el-table-column>
            <el-table-column prop="score" label="评分" width="100">
              <template #default="scope">
                <el-tag :type="getScoreType(scope.row.score)">
                  {{ scope.row.score.toFixed(2) }}
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
                <el-button
                  link
                  type="primary"
                  @click="viewAnalysis(scope.row)"
                >
                  查看详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>

  <!-- 目标设置对话框 -->
  <el-dialog
    v-model="goalDialogVisible"
    title="设置训练目标"
    width="500px"
  >
    <el-form :model="goalForm" label-width="120px">
      <el-form-item label="每周训练时长">
        <el-input-number v-model="goalForm.duration" :min="0.5" :max="20" :step="0.5" :precision="1" />
        <span class="unit-label">小时</span>
      </el-form-item>
      <el-form-item label="目标评分">
        <el-slider v-model="goalForm.score" :min="60" :max="100" :step="5" show-stops show-input />
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="goalDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveGoals">保存目标</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useVideoStore } from '@/store/modules/video'
import { VideoCamera, Timer, DataAnalysis, VideoPlay, ArrowUp, ArrowDown, Trophy, Setting } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const router = useRouter()
const videoStore = useVideoStore()

// 常量定义
const CHART_COLORS = {
  excellent: '#24b4f2',
  good: '#00fa60',
  fair: '#effa11',
  poor: '#e31717'
}

const STATUS_TYPES = {
  completed: 'success',
  processing: 'warning',
  error: 'danger'
}

const STATUS_TEXTS = {
  completed: '已完成',
  processing: '处理中',
  error: '失败'
}

// 响应式状态
const loading = ref(false)
const stats = ref({
  totalVideos: 0,
  totalDuration: 0,
  totalAnalysis: 0,
  weeklyTrainings: 0,
  weeklyDuration: 0,
  weeklyAverageScore: 0,
  scoreDistribution: {
    excellent: 0,
    good: 0,
    fair: 0,
    poor: 0
  },
  scoreTrend: [],
  uploadTrend: []
})

const recentAnalysis = ref([])
const trainingGoals = ref({
  duration: 2,
  score: 80
})

const goalDialogVisible = ref(false)
const goalForm = ref({
  duration: 2,
  score: 80
})

// 图表引用
const scoreDistributionChart = ref(null)
const scoreTrendChart = ref(null)
let distributionChart = null
let trendChart = null

// 工具函数
const formatDuration = (seconds) => {
  if (!seconds) return '0:00'
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

const formatDate = (date) => {
  return new Date(date).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
}

const formatDurationHours = (seconds) => {
  if (!seconds) return '0'
  return (seconds / 3600).toFixed(1)
}

const getScoreType = (score) => {
  if (score >= 90) return 'success'
  if (score >= 80) return 'warning'
  return 'danger'
}

const getStatusType = (status) => STATUS_TYPES[status] || 'info'
const getStatusText = (status) => STATUS_TEXTS[status] || status

const getDurationPercentage = () => {
  return Math.min(100, ((stats.value.weeklyDuration || 0) / (trainingGoals.value.duration * 3600)) * 100)
}

const getScoreColor = (score) => {
  if (score >= 90) return '#67C23A'
  if (score >= 80) return '#E6A23C'
  if (score >= 70) return '#F56C6C'
  return '#909399'
}

const getComparisonClass = (current, target) => {
  return current >= target ? 'comparison-positive' : 'comparison-negative'
}

const getProgressColor = (percentage) => {
  if (percentage < 30) return '#909399'
  if (percentage < 70) return '#E6A23C'
  return '#67C23A'
}

const getLastWeekDateRange = () => {
  const today = new Date()
  const lastWeekStart = new Date(today)
  lastWeekStart.setDate(today.getDate() - 7)
  return `${lastWeekStart.getMonth()+1}月${lastWeekStart.getDate()}日 - ${today.getMonth()+1}月${today.getDate()}日`
}

// 图表初始化函数
const initDistributionChart = () => {
  if (!scoreDistributionChart.value) return

  const container = scoreDistributionChart.value
  if (container.clientWidth === 0 || container.clientHeight === 0) return

  if (distributionChart) {
    distributionChart.dispose()
  }

  distributionChart = echarts.init(container)
  
  const data = [
    { value: stats.value.scoreDistribution.excellent, name: '优秀 (90-100)', itemStyle: { color: CHART_COLORS.excellent } },
    { value: stats.value.scoreDistribution.good, name: '良好 (80-89)', itemStyle: { color: CHART_COLORS.good } },
    { value: stats.value.scoreDistribution.fair, name: '一般 (70-79)', itemStyle: { color: CHART_COLORS.fair } },
    { value: stats.value.scoreDistribution.poor, name: '较差 (0-69)', itemStyle: { color: CHART_COLORS.poor } }
  ]

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}个动作 ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: true,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: true,
        position: 'outside',
        formatter: '{b}: {d}%'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: '14',
          fontWeight: 'bold'
        }
      },
      labelLine: {
        show: true
      },
      data: data,
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }
  
  distributionChart.setOption(option)
}

const initTrendChart = () => {
  if (!scoreTrendChart.value) return

  const container = scoreTrendChart.value
  if (container.clientWidth === 0 || container.clientHeight === 0) return

  if (trendChart) {
    trendChart.dispose()
  }

  trendChart = echarts.init(container)
  
  const scores = stats.value.scoreTrend.map(item => item.score)
  const averageScore = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: '{b}<br/>评分: {c}'
    },
    xAxis: {
      type: 'category',
      name: '视频标题',
      nameLocation: 'middle',
      nameGap: 35,
      data: stats.value.scoreTrend.map(item => item.title),
      axisLabel: {
        interval: 0,
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: '评分',
      nameLocation: 'middle',
      nameGap: 40,
      min: 0,
      max: 100,
      splitLine: {
        lineStyle: {
          type: 'dashed'
        }
      }
    },
    series: [
      {
        data: stats.value.scoreTrend.map(item => item.score),
        type: 'line',
        smooth: true,
        lineStyle: {
          width: 3
        },
        itemStyle: {
          color: '#409EFF'
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            {
              offset: 0,
              color: 'rgba(64,158,255,0.3)'
            },
            {
              offset: 1,
              color: 'rgba(64,158,255,0.1)'
            }
          ])
        }
      },
      {
        name: '平均分',
        type: 'line',
        markLine: {
          silent: true,
          data: [
            {
              yAxis: averageScore,
              lineStyle: {
                color: '#F56C6C',
                type: 'dashed',
                width: 2
              },
              label: {
                formatter: `平均分: ${averageScore.toFixed(1)}`,
                position: 'end',
                color: '#F56C6C',
                fontSize: 12,
                backgroundColor: '#fff',
                padding: [4, 8],
                borderRadius: 4
              }
            }
          ]
        }
      }
    ]
  }
  
  trendChart.setOption(option)
}

// 数据获取函数
const fetchDashboardData = async () => {
  loading.value = true
  try {
    const data = await videoStore.fetchDashboardStats()
    
    // 处理统计数据
    stats.value = {
      totalVideos: data.totalVideos || 0,
      totalDuration: data.totalDuration || 0,
      totalAnalysis: data.totalAnalysis || 0,
      weeklyTrainings: data.weeklyTrainings || 0,
      weeklyDuration: data.weeklyDuration || 0,
      weeklyAverageScore: data.weeklyAverageScore || 0,
      scoreDistribution: data.scoreDistribution || {
        excellent: 0,
        good: 0,
        fair: 0,
        poor: 0
      },
      scoreTrend: Array.isArray(data.scoreTrend) ? data.scoreTrend.map(item => ({
        ...item,
        score: typeof item.score === 'number' ? item.score : 0,
        title: item.title || '未命名视频'
      })) : []
    }
    
    // 处理最近分析数据
    recentAnalysis.value = Array.isArray(data.recentAnalysis) ? data.recentAnalysis.map(item => ({
      ...item,
      videoTitle: item.videoTitle || '未命名视频',
      score: typeof item.score === 'number' ? item.score : null,
      status: item.status || 'unknown',
      date: item.date || new Date().toISOString()
    })) : []
    
    // 等待 DOM 更新后初始化图表
    await nextTick()
    requestAnimationFrame(() => {
      if (scoreDistributionChart.value && scoreTrendChart.value) {
        const distributionContainer = scoreDistributionChart.value
        const trendContainer = scoreTrendChart.value
        
        if (distributionContainer.clientWidth > 0 && distributionContainer.clientHeight > 0 &&
            trendContainer.clientWidth > 0 && trendContainer.clientHeight > 0) {
          initDistributionChart()
          initTrendChart()
        } else {
          setTimeout(() => {
            if (distributionContainer.clientWidth > 0 && distributionContainer.clientHeight > 0 &&
                trendContainer.clientWidth > 0 && trendContainer.clientHeight > 0) {
              initDistributionChart()
              initTrendChart()
            }
          }, 100)
        }
      }
    })
  } catch (error) {
    console.error('获取仪表盘数据失败:', error)
    ElMessage.error('获取仪表盘数据失败，请稍后重试')
    
    // 重置数据为默认值
    stats.value = {
      totalVideos: 0,
      totalDuration: 0,
      totalAnalysis: 0,
      scoreDistribution: {
        excellent: 0,
        good: 0,
        fair: 0,
        poor: 0
      },
      scoreTrend: []
    }
    recentAnalysis.value = []
  } finally {
    loading.value = false
  }
}

// 目标设置相关函数
const openGoalSettings = () => {
  goalForm.value = { ...trainingGoals.value }
  goalDialogVisible.value = true
}

const saveGoals = () => {
  trainingGoals.value = { ...goalForm.value }
  localStorage.setItem('trainingGoals', JSON.stringify(trainingGoals.value))
  goalDialogVisible.value = false
  ElMessage.success('训练目标设置成功')
}

const loadUserGoals = () => {
  const savedGoals = localStorage.getItem('trainingGoals')
  if (savedGoals) {
    try {
      const parsedGoals = JSON.parse(savedGoals)
      trainingGoals.value = {
        ...trainingGoals.value,
        ...parsedGoals
      }
    } catch (error) {
      console.error('解析训练目标失败:', error)
    }
  }
}

// 路由相关函数
const viewAnalysis = (analysis) => {
  router.push({
    path: '/analysis',
    query: {
      videoId: analysis.videoId,
      hand: analysis.hand || 'left'
    }
  })
}

// 生命周期钩子
onMounted(async () => {
  loading.value = true
  try {
    loadUserGoals()
    await fetchDashboardData()
  } catch (error) {
    console.error('获取数据失败:', error)
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  distributionChart?.dispose()
  trendChart?.dispose()
})

// 事件处理函数
const handleResize = () => {
  distributionChart?.resize()
  trendChart?.resize()
}
</script>

<style lang="scss" scoped>
.dashboard-container {
  padding: 24px;
  background-color: #f5f7fa;
  min-height: 100vh;
  position: fixed;
  top: 64px;
  left: 200px;
  right: 0;
  bottom: 0;
  overflow-y: auto;

  .stat-card {
    margin-bottom: 24px;
    border-radius: 12px;
    transition: all 0.3s ease;
    border: none;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);

    &:hover {
      transform: translateY(-5px);
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
    }

    .stat-content {
      display: flex;
      align-items: center;
      gap: 20px;
      padding: 10px 0;

      .stat-icon {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        background: var(--el-color-primary-light-9);
        display: flex;
        align-items: center;
        justify-content: center;

        .el-icon {
          font-size: 24px;
          color: var(--el-color-primary);
        }
      }

      .stat-info {
        flex: 1;

        .stat-value {
          font-size: 24px;
          font-weight: 600;
          color: var(--el-text-color-primary);
          line-height: 1.2;
        }

        .stat-label {
          font-size: 14px;
          color: var(--el-text-color-secondary);
          margin-top: 4px;
        }
      }
    }
  }

  .chart-row {
    margin-bottom: 24px;
  }

  .chart-card {
    border-radius: 12px;
    transition: all 0.3s ease;
    border: none;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
    height: 100%;

    &:hover {
      transform: translateY(-5px);
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0;
      border-bottom: none;

      span {
        font-size: 16px;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }
    }

    .chart-container {
      height: 300px;
      width: 100%;
    }

    .weekly-stats {
      height: 300px;
      display: flex;
      flex-direction: column;

      .stats-header {
        margin-bottom: 20px;
        text-align: center;

        .date-range {
          font-size: 14px;
          color: var(--el-text-color-secondary);
        }
      }

      .stats-grid {
        flex: 1;
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 20px;
        align-items: center;

        .stat-card-mini {
          background: var(--el-bg-color);
          border-radius: 8px;
          padding: 16px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
          height: 100%;
          display: flex;
          flex-direction: column;
          justify-content: space-between;

          .stat-icon-wrapper {
            width: 40px;
            height: 40px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 12px;

            &.duration-icon {
              background: var(--el-color-primary-light-9);
              color: var(--el-color-primary);
            }

            &.score-icon {
              background: var(--el-color-success-light-9);
              color: var(--el-color-success);
            }

            .el-icon {
              font-size: 20px;
            }
          }

          .stat-info {
            margin-bottom: 12px;

            .stat-value {
              font-size: 20px;
              font-weight: 600;
              color: var(--el-text-color-primary);
              line-height: 1.2;
            }

            .stat-label {
              font-size: 12px;
              color: var(--el-text-color-secondary);
              margin-top: 4px;
            }
          }

          .el-progress {
            margin: 12px 0;
          }

          .stat-comparison {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;

            .comparison-positive {
              color: var(--el-color-success);
            }

            .comparison-negative {
              color: var(--el-color-danger);
            }

            .comparison-label {
              color: var(--el-text-color-secondary);
            }
          }
        }
      }
    }
  }

  .recent-card {
    border-radius: 12px;
    transition: all 0.3s ease;
    border: none;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);

    &:hover {
      transform: translateY(-5px);
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0;
      border-bottom: none;

      span {
        font-size: 16px;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }
    }
  }
}

.unit-label {
  margin-left: 8px;
  color: var(--el-text-color-secondary);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style> 
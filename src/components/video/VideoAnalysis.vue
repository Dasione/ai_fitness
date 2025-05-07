<template>
  <div class="video-analysis">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="动作评分" name="score">
        <div class="score-panel">
          <div class="overall-score">
            <h3>总体评分</h3>
            <div class="score-value">{{ analysis.overallScore || '暂无' }}</div>
          </div>
          
          <div class="detail-scores">
            <el-row :gutter="20">
              <el-col :span="8" v-for="(score, key) in analysis.detailScores" :key="key">
                <el-card shadow="hover">
                  <template #header>
                    <div class="score-header">
                      {{ getScoreTitle(key) }}
                    </div>
                  </template>
                  <div class="score-content">
                    <el-progress
                      type="dashboard"
                      :percentage="score"
                      :color="getScoreColor(score)"
                    />
                    <div class="score-description">
                      {{ getScoreDescription(key, score) }}
                    </div>
                  </div>
                </el-card>
              </el-col>
            </el-row>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="动作建议" name="suggestions">
        <div class="suggestions-panel">
          <template v-if="analysis.suggestions && analysis.suggestions.length">
            <el-timeline>
              <el-timeline-item
                v-for="(suggestion, index) in analysis.suggestions"
                :key="index"
                :timestamp="suggestion.timestamp"
                :type="getSuggestionType(suggestion.level)"
              >
                <h4>{{ getSuggestionTitle(suggestion.level) }}</h4>
                <p>{{ suggestion.content }}</p>
              </el-timeline-item>
            </el-timeline>
          </template>
          <el-empty v-else description="暂无动作建议" />
        </div>
      </el-tab-pane>

      <el-tab-pane label="关键帧" name="keyframes">
        <div class="keyframes-panel">
          <template v-if="analysis.keyframes && analysis.keyframes.length">
            <el-carousel :interval="4000" type="card" height="300px">
              <el-carousel-item v-for="(frame, index) in analysis.keyframes" :key="index">
                <div class="keyframe-item">
                  <el-image
                    :src="frame.image"
                    fit="contain"
                    :preview-src-list="[frame.image]"
                  />
                  <div class="keyframe-info">
                    <p class="time">时间点：{{ formatTime(frame.timestamp) }}</p>
                    <p class="description">{{ frame.description }}</p>
                  </div>
                </div>
              </el-carousel-item>
            </el-carousel>
          </template>
          <el-empty v-else description="暂无关键帧" />
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  analysis: {
    type: Object,
    required: true,
    default: () => ({
      overallScore: null,
      detailScores: {},
      suggestions: [],
      keyframes: []
    })
  }
})

const activeTab = ref('score')

const getScoreTitle = (key) => {
  const titles = {
    posture: '姿势标准度',
    stability: '稳定性',
    rhythm: '动作节奏',
    range: '动作幅度',
    coordination: '协调性'
  }
  return titles[key] || key
}

const getScoreColor = (score) => {
  if (score >= 90) return '#67C23A'
  if (score >= 70) return '#E6A23C'
  return '#F56C6C'
}

const getScoreDescription = (key, score) => {
  if (score >= 90) return '优秀'
  if (score >= 70) return '良好'
  if (score >= 60) return '及格'
  return '需要改进'
}

const getSuggestionType = (level) => {
  const types = {
    error: 'danger',
    warning: 'warning',
    info: 'info'
  }
  return types[level] || 'info'
}

const getSuggestionTitle = (level) => {
  const titles = {
    error: '严重问题',
    warning: '需要注意',
    info: '小建议'
  }
  return titles[level] || '建议'
}

const formatTime = (seconds) => {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}
</script>

<style lang="scss" scoped>
.video-analysis {
  padding: 20px;

  .score-panel {
    .overall-score {
      text-align: center;
      margin-bottom: 30px;

      h3 {
        margin: 0 0 10px;
        color: #606266;
      }

      .score-value {
        font-size: 48px;
        font-weight: bold;
        color: #409EFF;
      }
    }

    .detail-scores {
      .score-header {
        font-size: 16px;
        font-weight: bold;
        color: #303133;
      }

      .score-content {
        display: flex;
        flex-direction: column;
        align-items: center;
        
        .score-description {
          margin-top: 10px;
          color: #606266;
        }
      }
    }
  }

  .suggestions-panel {
    padding: 20px 0;

    h4 {
      margin: 0;
      font-size: 16px;
    }

    p {
      margin: 5px 0 0;
      color: #606266;
    }
  }

  .keyframes-panel {
    .keyframe-item {
      height: 100%;
      display: flex;
      flex-direction: column;

      .el-image {
        height: 220px;
        display: flex;
        justify-content: center;
        align-items: center;
      }

      .keyframe-info {
        padding: 10px;
        background: rgba(0, 0, 0, 0.5);
        color: #fff;

        p {
          margin: 5px 0;
          
          &.time {
            font-size: 14px;
            opacity: 0.8;
          }
          
          &.description {
            font-size: 16px;
          }
        }
      }
    }
  }
}
</style> 
<template>
  <div class="videos-container">
    <el-card class="page-header-card" shadow="hover">
      <div class="page-header">
        <div class="header-content">
          <h2>视频管理</h2>
          <p class="subtitle">管理您的训练视频，查看分析结果</p>
        </div>
        <div class="actions">
          <el-button type="primary" @click="showUploadDialog" class="action-button">
            <el-icon><Upload /></el-icon>上传视频
          </el-button>
          <el-button 
            type="danger" 
            :disabled="!selectedVideos.length"
            @click="handleBatchDelete"
            class="action-button"
          >
            <el-icon><Delete /></el-icon>批量删除
          </el-button>
        </div>
      </div>
    </el-card>

    <el-card class="video-list">
      <div class="table-container">
        <el-table
          v-loading="videoStore.Loading"
          :data="paginatedData"
          style="width: 100%"
          @selection-change="handleSelectionChange"
          height="calc(100vh - 350px)"
        >
          <el-table-column prop="title" label="视频标题" min-width="200">
            <template #default="{ row }">
              <div class="video-title">
                <el-image
                  :src="row.thumbnail"
                  fit="cover"
                  class="video-thumbnail"
                />
                <div class="title-content">
                  <span>{{ row.title }}</span>
                  <span v-if="row.description" class="description">{{ row.description }}</span>
                  <span class="timestamp">{{ formatDate(row.createdAt) }}</span>
                </div>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column prop="duration" label="视频时长（分钟）" width="180">
            <template #default="{ row }">
              {{ formatDuration(row.duration) }}
            </template>
          </el-table-column>
          
          <el-table-column prop="status" label="处理状态" width="140">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="createdAt" label="上传时间" width="190">
            <template #default="{ row }">
              {{ formatDate(row.createdAt) }}
            </template>
          </el-table-column>
          
          <el-table-column label="操作" width="220" fixed="right">
            <template #default="{ row }">
      <div class="action-buttons">
        <div class="button-row">
          <el-button
            type="primary"
            :icon="VideoPlay"
            @click="handlePlay(row)"
            class="action-button"
          >
            播放
          </el-button>
          <el-button
            type="success"
            :icon="Search"
            @click="handleAnalyze(row)"
            class="action-button"
          >
            分析
          </el-button>
        </div>
        <div class="button-row">
          <el-button
            type="warning"
            :icon="Edit"
            @click="handleEdit(row)"
            class="action-button"
          >
            编辑
          </el-button>
          <el-button
            type="danger"
            :icon="Delete"
            @click="handleDelete(row)"
            class="action-button"
          >
            删除
          </el-button>
        </div>
      </div>
    </template>
          </el-table-column>

          <el-table-column type="selection" width="80" fixed="right" />
        </el-table>
      </div>
    </el-card>

    <!-- 分页控制卡片 -->
    <el-card class="pagination-card" shadow="hover">
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="totalItems"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 上传视频对话框 -->
    <upload-dialog
      v-model="uploadDialogVisible"
      append-to-body
      destroy-on-close
      @success="handleUploadSuccess"
      @error="handleUploadError"
    />

    <!-- 视频播放对话框 -->
    <el-dialog
      v-model="playDialog.visible"
      :show-close="true"
      :close-on-click-modal="true"
      width="80%"
      destroy-on-close
      @close="handleDialogClose"
      @before-close="handleDialogBeforeClose"
      class="video-dialog"
    >
      <VideoPlayer
        v-if="playDialog.visible"
        ref="videoPlayerRef"
        :src="playDialog.video?.url"
        :poster="playDialog.video?.thumbnail"
        @error="handlePlayError"
      />
    </el-dialog>

    <!-- 编辑视频对话框 -->
    <el-dialog
      v-model="editDialog.visible"
      title="编辑视频信息"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="editFormRef"
        :model="editDialog.form"
        :rules="editDialog.rules"
        label-width="80px"
      >
        <el-form-item label="标题" prop="title">
          <el-input v-model="editDialog.form.title" placeholder="请输入视频标题" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="editDialog.form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入视频描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialog.visible = false">取消</el-button>
          <el-button type="primary" @click="confirmEdit" :loading="editDialog.loading">
            确认
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed, watch, onUnmounted } from 'vue'
import { useVideoStore } from '@/store/modules/video'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, VideoPlay, Delete, Search, Edit } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import UploadDialog from '@/components/video/UploadDialog.vue'
import VideoPlayer from '@/components/video/VideoPlayer.vue'
import VideoAnalysis from '@/components/video/VideoAnalysis.vue'
import dayjs from 'dayjs'

// 常量定义
const ERROR_MESSAGES = {
  404: '视频文件不存在，请选择其他视频',
  401: '登录已过期，请重新登录',
  500: '服务器错误，请稍后重试',
  413: '视频文件过大，请选择更小的文件',
  default: '操作失败，请重试'
}

const STATUS_TYPES = {
  unprocessed: 'info',
  processing: 'warning',
  processed: 'success',
  error: 'danger'
}

const STATUS_TEXTS = {
  unprocessed: '待处理',
  processing: '处理中',
  processed: '已完成',
  error: '处理失败'
}

const PAGE_SIZES = [10, 20, 50]

// Store
const videoStore = useVideoStore()
const router = useRouter()

// 响应式状态
const uploadDialogVisible = ref(false)
const selectedVideos = ref([])
const videoPlayerRef = ref(null)
const editFormRef = ref(null)
const currentPage = ref(1)
const pageSize = ref(10)
const totalItems = ref(0)

// 对话框状态
const playDialog = reactive({
  visible: false,
  video: null
})

const editDialog = reactive({
  visible: false,
  loading: false,
  form: {
    id: null,
    title: '',
    description: ''
  },
  rules: {
    title: [
      { required: true, message: '请输入视频标题', trigger: 'blur' },
      { min: 1, max: 100, message: '标题长度在1到100个字符之间', trigger: 'blur' }
    ],
    description: [
      { max: 500, message: '描述长度不能超过500个字符', trigger: 'blur' }
    ]
  }
})

// 计算属性
const paginatedData = computed(() => {
  if (!videoStore.videos) return []
  return videoStore.videos.map(video => ({
    ...video,
    id: video.id,
    title: video.title || '未命名视频',
    url: `/uploads/videos/${video.file_path.split(/[/\\]/).pop()}`,
    thumbnail: video.thumbnail_path ? `/${video.thumbnail_path.replace(/^public[\\/]/, '')}` : null,
    duration: video.duration || 0,
    status: video.status || 'unprocessed',
    createdAt: video.created_at || new Date().toISOString()
  }))
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

const getStatusType = (status) => {
  return STATUS_TYPES[status] || 'info'
}

const getStatusText = (status) => {
  return STATUS_TEXTS[status] || '未知'
}

const handleError = (error, customMessage = '') => {
  console.error(error)
  const message = error.response?.data?.message || 
                 ERROR_MESSAGES[error.response?.status] || 
                 customMessage || 
                 ERROR_MESSAGES.default
  ElMessage.error(message)
}

// 视频列表相关方法
const fetchPageData = async () => {
  try {
    const response = await videoStore.fetchVideos({
      page: currentPage.value,
      limit: pageSize.value
    })
    totalItems.value = response.total
  } catch (error) {
    handleError(error, '获取视频列表失败')
  }
}

// 视频操作相关方法
const showUploadDialog = () => {
  uploadDialogVisible.value = true
}

const handleUploadSuccess = () => {
  ElMessage.success('视频上传成功')
  fetchPageData()
}

const handleUploadError = (error) => {
  handleError(error)
}

const handlePlay = (video) => {
  playDialog.video = video
  playDialog.visible = true
}

const handleDelete = async (video) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个视频吗？此操作不可恢复。',
      '删除确认',
      {
        type: 'warning'
      }
    )
    
    await videoStore.deleteVideo(video.id)
    ElMessage.success('删除成功')
    
    if (videoStore.videos.length === 0 && currentPage.value > 1) {
      currentPage.value--
    } else {
      fetchPageData()
    }
  } catch (error) {
    if (error !== 'cancel') {
      handleError(error, '删除失败')
    }
  }
}

const handleAnalyze = (video) => {
  router.push({
    path: '/analysis',
    query: { videoId: video.id }
  })
}

// 对话框相关方法
const handleDialogBeforeClose = () => {
  if (videoPlayerRef.value) {
    videoPlayerRef.value.stop()
  }
}

const handleDialogClose = () => {
  if (videoPlayerRef.value) {
    videoPlayerRef.value.stop()
  }
  playDialog.video = null
  playDialog.visible = false
}

const handlePlayError = (error) => {
  if (playDialog.visible) {
    if (error.message?.includes('ended')) {
      handleDialogClose()
      return
    }
    handleError(error, '视频播放失败')
  }
  handleDialogClose()
}

// 编辑相关方法
const handleEdit = (video) => {
  editDialog.form = {
    id: video.id,
    title: video.title,
    description: video.description || ''
  }
  editDialog.visible = true
}

const confirmEdit = async () => {
  if (!editFormRef.value) return
  
  try {
    await editFormRef.value.validate()
    editDialog.loading = true
    
    const apiUrl = `${import.meta.env.VITE_API_BASE_URL}/api/videos/${editDialog.form.id}`
    const token = localStorage.getItem('token')
    
    if (!token) {
      throw new Error('未登录或登录已过期')
    }
    
    const response = await fetch(apiUrl, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        title: editDialog.form.title,
        description: editDialog.form.description
      })
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: '更新失败' }))
      throw new Error(errorData.message || '更新失败')
    }
    
    const data = await response.json()
    ElMessage.success(data.message || '更新成功')
    editDialog.visible = false
    await fetchPageData()
  } catch (error) {
    handleError(error, '更新失败')
  } finally {
    editDialog.loading = false
  }
}

// 批量操作相关方法
const handleSelectionChange = (selection) => {
  selectedVideos.value = selection
}

const handleBatchDelete = async () => {
  if (!selectedVideos.value.length) {
    ElMessage.warning('请选择要删除的视频')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedVideos.value.length} 个视频吗？`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const videoIds = selectedVideos.value.map(video => video.id)
    await videoStore.deleteVideos(videoIds)
    
    ElMessage.success('视频删除成功')
    selectedVideos.value = []
    fetchPageData()
  } catch (error) {
    if (error !== 'cancel') {
      handleError(error, '删除视频失败')
    }
  }
}

// 分页相关方法
const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val) => {
  currentPage.value = val
}

// 监听器
watch([currentPage, pageSize], () => {
  fetchPageData()
})

// 生命周期钩子
onMounted(async () => {
  try {
    await fetchPageData()
  } catch (error) {
    handleError(error, '获取视频列表失败')
  }
})

onUnmounted(() => {
  if (videoPlayerRef.value) {
    videoPlayerRef.value.stop()
  }
})
</script>

<style lang="scss" scoped>
.videos-container {
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
    margin-top: -15px;
    margin-bottom: 15px;
    border-radius: 12px;
    transition: all 0.3s ease;
    border: none;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);

    &:hover {
      transform: translateY(-5px);
      box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.1);
    }

    :deep(.el-card__body) {
      padding: 20px;
    }

    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

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

      .actions {
        display: flex;
        gap: 6px;

        .action-button {
          border-radius: 8px;
          transition: all 0.3s ease;
          padding: 20px 10px;
          font-weight: 500;
          
          &:hover {
            transform: translateY(-2px);
          }

          .el-icon {
            margin-right: 6px;
          }
        }
      }
    }
  }

  .video-list {
    border-radius: 16px;
    transition: all 0.3s ease;
    border: none;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
    margin-bottom: 16px;
    display: flex;
    flex-direction: column;
    height: calc(100vh - 350px);

    &:hover {
      transform: translateY(-5px);
      box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.1);
    }

    :deep(.el-card__body) {
      padding: 0;
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .table-container {
      flex: 1;
      overflow: hidden;
    }

    :deep(.el-table) {
      height: 100%;

      .el-table__body-wrapper {
        overflow-y: auto;
        overflow-x: hidden;
      }

      .el-table__row {
        height: 80px;
        transition: all 0.3s ease;

        &:hover {
          background-color: var(--el-color-primary-light-9);
        }
      }

      .el-table__cell {
        padding: 12px 16px;
        vertical-align: middle;
      }
    }

    :deep(.el-table th) {
      background-color: var(--el-bg-color) !important;
      color: var(--el-text-color-regular);
      font-weight: 600;
      padding: 16px;
      border-bottom: 1px solid var(--el-border-color-light);
      height: 60px;
    }

    :deep(.el-table td) {
      padding: 16px;
    }

    .video-title {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 8px 0;

      .video-thumbnail {
        width: 128px;
        height: 72px;
        border-radius: 8px;
        object-fit: cover;
        background-color: var(--el-bg-color-page);
        transition: all 0.3s ease;

        &:hover {
          transform: scale(1.05);
        }
      }

      .title-content {
        display: flex;
        flex-direction: column;
        gap: 8px;
        flex: 1;

        span:first-child {
          font-size: 16px;
          font-weight: 500;
          color: var(--el-text-color-primary);
        }

        .description {
          font-size: 13px;
          color: var(--el-text-color-secondary);
          display: -webkit-box;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }

        .timestamp {
          font-size: 12px;
          color: var(--el-text-color-secondary);
          opacity: 0.8;
        }
      }
    }

    .action-buttons {
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding: 4px 0;

      .button-row {
        display: flex;
        gap: 8px;
      }

      .action-button {
        flex: 1;
        padding: 8px 12px;
        border-radius: 6px;
        transition: all 0.3s ease;
        font-size: 13px;
        height: 32px;

        &:hover {
          transform: translateY(-2px);
        }
      }
    }
  }

  .pagination-card {
    border-radius: 16px;
    transition: all 0.3s ease;
    border: none;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
    margin-bottom: 24px;

    &:hover {
      transform: translateY(-5px);
      box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.1);
    }

    :deep(.el-card__body) {
      padding: 16px;
    }

    .pagination-container {
      display: flex;
      justify-content: center;
      align-items: center;
      background-color: var(--el-bg-color);
      border-radius: 12px;

      :deep(.el-pagination) {
        .el-pagination__sizes {
          margin-right: 16px;
        }

        .el-pagination__total {
          margin-right: 16px;
        }

        button {
          background-color: var(--el-bg-color);
          border: 1px solid var(--el-border-color);
          border-radius: 4px;
          padding: 0 4px;
          margin: 0 4px;
          min-width: 32px;
          height: 32px;
          line-height: 32px;
          
          &:hover {
            color: var(--el-color-primary);
            border-color: var(--el-color-primary);
          }
          
          &:disabled {
            background-color: var(--el-bg-color-page);
            border-color: var(--el-border-color-lighter);
            color: var(--el-text-color-placeholder);
          }
        }

        .el-pager li {
          background-color: var(--el-bg-color);
          border: 1px solid var(--el-border-color);
          border-radius: 4px;
          padding: 0 4px;
          margin: 0 4px;
          min-width: 32px;
          height: 32px;
          line-height: 32px;

          &:hover {
            color: var(--el-color-primary);
            border-color: var(--el-color-primary);
          }

          &.active {
            background-color: var(--el-color-primary);
            border-color: var(--el-color-primary);
            color: var(--el-color-white);
          }
        }
      }
    }
  }
}

:deep(.video-dialog) {
  .el-dialog {
    background: var(--el-bg-color);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.1);
  }

  .el-dialog__body {
    padding: 0;
  }

  .video-player {
    width: 100%;
    aspect-ratio: 16/9;
    background-color: var(--el-bg-color-page);
    border-radius: 8px;
    overflow: hidden;
  }
}

:deep(.el-dialog) {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.1);

  .el-dialog__header {
    padding: 20px;
    border-bottom: 1px solid var(--el-border-color-light);
    margin: 0;

    .el-dialog__title {
      font-size: 18px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }
  }

  .el-dialog__body {
    padding: 24px;
  }

  .el-dialog__footer {
    padding: 16px 20px;
    border-top: 1px solid var(--el-border-color-light);
    background-color: var(--el-bg-color-page);
  }
}

// 响应式布局
@media screen and (max-width: 768px) {
  .videos-container {
    left: 0;
    top: 56px;
    padding: 16px;

    .page-header-card {
      margin-bottom: 16px;

      :deep(.el-card__body) {
        padding: 16px;
      }

      .page-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 16px;

        .header-content {
          h2 {
            font-size: 20px;
          }
        }

        .actions {
          width: 100%;
          justify-content: flex-start;

          .action-button {
            flex: 1;
            padding: 8px 16px;
          }
        }
      }
    }

    .video-title {
      .video-thumbnail {
        width: 80px;
        height: 45px;
      }

      .title-content {
        gap: 4px;

        span:first-child {
          font-size: 14px;
        }

        .description {
          font-size: 12px;
        }
      }
    }

    :deep(.el-table) {
      th, td {
        padding: 12px;
      }
    }

    .action-buttons {
      gap: 4px;

      .button-row {
        gap: 4px;
      }

      .action-button {
        padding: 4px 8px;
        font-size: 12px;
      }
    }

    .pagination-container {
      padding: 12px;
      flex-wrap: wrap;
      gap: 8px;
      justify-content: center;

      :deep(.el-pagination) {
        .el-pagination__sizes {
          margin-right: 8px;
        }
      }
    }
  }
}
</style>
import express from 'express'
import { verifyToken } from '../middleware/auth.js'
import {
    getVideos,
    getVideo,
    uploadVideo,
    updateVideo,
    deleteVideo,
    getDashboardStats,
    deleteVideos,
    startVideoService,
    stopVideoService
} from '../controllers/videoController.js'
import {
    startAnalysis,
    getAnalysisResult,
    deleteAnalysis
} from '../controllers/videoAnalysis.js'

const router = express.Router()

// 所有路由都需要认证
router.use(verifyToken)

// 获取仪表盘统计数据
router.get('/dashboard', getDashboardStats)

// 获取视频列表
router.get('/', getVideos)

// 获取单个视频
router.get('/:id', getVideo)

// 上传视频
router.post('/', uploadVideo)

// 更新视频信息
router.put('/:id', updateVideo)

// 删除视频
router.delete('/:id', deleteVideo)

// 批量删除视频
router.post('/batch-delete', deleteVideos)

// 开始视频分析
router.post('/:id/analyze', startAnalysis)

// 获取分析结果
router.get('/:id/analysis', getAnalysisResult)

// 删除分析记录
router.delete('/:id/analysis', deleteAnalysis)

// 视频服务控制路由
router.post('/start-service', startVideoService)
router.post('/stop-service', stopVideoService)

export default router
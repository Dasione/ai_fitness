import express from 'express'
import { verifyToken } from '../middleware/auth.js'
import {
    getUserProfile,
    updateUserProfile,
    uploadAvatar,
    changePassword
} from '../controllers/userController.js'
import multer from 'multer'
import path from 'path'
import { fileURLToPath } from 'url'
import { dirname } from 'path'
import fs from 'fs/promises'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const router = express.Router()

// 配置文件上传
const storage = multer.diskStorage({
    destination: async (req, file, cb) => {
        const uploadDir = path.join(__dirname, '../../public/uploads/avatars')
        try {
            await fs.mkdir(uploadDir, { recursive: true })
            cb(null, uploadDir)
        } catch (error) {
            cb(error)
        }
    },
    filename: (req, file, cb) => {
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9)
        cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname))
    }
})

const upload = multer({
    storage: storage,
    limits: {
        fileSize: 5 * 1024 * 1024 // 限制5MB
    },
    fileFilter: (req, file, cb) => {
        const allowedTypes = ['image/jpeg', 'image/png', 'image/gif']
        if (allowedTypes.includes(file.mimetype)) {
            cb(null, true)
        } else {
            cb(new Error('不支持的文件类型'))
        }
    }
})

// 所有路由都需要认证
router.use(verifyToken)

// 获取用户信息
router.get('/profile', getUserProfile)

// 更新用户信息
router.patch('/profile', updateUserProfile)

// 上传头像
router.post('/avatar', upload.single('avatar'), uploadAvatar)

// 修改密码
router.post('/password', changePassword)

export default router
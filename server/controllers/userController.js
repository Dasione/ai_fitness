import { User } from '../models/index.js'
import { createError } from '../utils/error.js'
import path from 'path'
import { fileURLToPath } from 'url'
import { dirname } from 'path'
import fs from 'fs/promises'
import { Op } from 'sequelize'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

/**
 * 获取用户信息
 */
export const getUserProfile = async (req, res, next) => {
    try {
        const user = await User.findByPk(req.user.id, {
            attributes: ['id', 'username', 'email', 'avatar', 'created_at', 'updated_at']
        })
        
        if (!user) {
            return next(createError(404, '用户不存在'))
        }

        res.json(user)
    } catch (error) {
        console.error('获取用户信息失败:', error)
        next(error)
    }
}

/**
 * 更新用户信息
 */
export const updateUserProfile = async (req, res, next) => {
    try {
        const { username, email } = req.body
        const userId = req.user.id

        // 验证用户名是否已存在
        if (username) {
            const existingUser = await User.findOne({
                where: {
                    username,
                    id: { [Op.ne]: userId }
                }
            })
            if (existingUser) {
                return next(createError(400, '用户名已存在'))
            }
        }

        // 验证邮箱是否已存在
        if (email) {
            const existingEmail = await User.findOne({
                where: {
                    email,
                    id: { [Op.ne]: userId }
                }
            })
            if (existingEmail) {
                return next(createError(400, '邮箱已被使用'))
            }
        }

        // 更新用户信息
        const user = await User.findByPk(userId)
        if (!user) {
            return next(createError(404, '用户不存在'))
        }

        await user.update({
            username: username || user.username,
            email: email || user.email
        })

        res.json({
            message: '用户信息更新成功',
            user: {
                id: user.id,
                username: user.username,
                email: user.email,
                avatar: user.avatar
            }
        })
    } catch (error) {
        console.error('更新用户信息失败:', error)
        next(error)
    }
}

/**
 * 上传头像
 */
export const uploadAvatar = async (req, res, next) => {
    try {
        if (!req.file) {
            return next(createError(400, '没有上传文件'))
        }

        const user = await User.findByPk(req.user.id)
        if (!user) {
            return next(createError(404, '用户不存在'))
        }

        // 删除旧头像
        if (user.avatar) {
            const oldAvatarPath = path.join(__dirname, '../../public', user.avatar)
            try {
                await fs.unlink(oldAvatarPath)
            } catch (error) {
                console.error('删除旧头像失败:', error)
            }
        }

        // 更新用户头像
        const avatarPath = `/uploads/avatars/${req.file.filename}`
        await user.update({ avatar: avatarPath })

        res.json({
            message: '头像上传成功',
            avatar: avatarPath
        })
    } catch (error) {
        console.error('上传头像失败:', error)
        next(error)
    }
}

/**
 * 修改密码
 */
export const changePassword = async (req, res, next) => {
    try {
        const { currentPassword, newPassword } = req.body
        const user = await User.findByPk(req.user.id)

        if (!user) {
            return next(createError(404, '用户不存在'))
        }

        // 验证当前密码
        const isMatch = await user.verifyPassword(currentPassword)
        if (!isMatch) {
            return next(createError(400, '当前密码错误'))
        }

        // 更新密码
        await user.changePassword(newPassword)

        res.json({
            message: '密码修改成功'
        })
    } catch (error) {
        console.error('修改密码失败:', error)
        next(error)
    }
} 
import jwt from 'jsonwebtoken';
import { createError } from '../utils/error.js';
import { User } from '../models/index.js';

const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';

export const verifyToken = async (req, res, next) => {
    try {
        const token = req.headers.authorization?.split(' ')[1];
        
        if (!token) {
            return next(createError(401, '未提供认证令牌'));
        }

        const decoded = jwt.verify(token, JWT_SECRET);
        const user = await User.findByPk(decoded.id);

        if (!user) {
            return next(createError(401, '用户不存在'));
        }

        // 将用户信息添加到请求对象中
        req.user = user;
        next();
    } catch (error) {
        if (error.name === 'JsonWebTokenError') {
            return next(createError(401, '无效的认证令牌'));
        }
        if (error.name === 'TokenExpiredError') {
            return next(createError(401, '认证令牌已过期'));
        }
        next(error);
    }
}; 
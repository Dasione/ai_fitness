import { User } from '../models/index.js';
import { createError } from '../utils/error.js';
import jwt from 'jsonwebtoken';

const JWT_SECRET = process.env.JWT_SECRET

// 生成JWT token
const generateToken = (user) => {
    return jwt.sign(
        { id: user.id, username: user.username },
        JWT_SECRET,
        { expiresIn: '7d' }
    );
};

// 用户注册
export const register = async (req, res, next) => {
    try {
        const { username, password, email } = req.body;

        // 验证必要字段
        if (!username || !password || !email) {
            return next(createError(400, '用户名、密码和邮箱不能为空'));
        }

        // 验证用户名长度
        if (username.length < 3) {
            return next(createError(400, '用户名长度不能小于3个字符'));
        }

        // 验证密码长度
        if (password.length < 5) {
            return next(createError(400, '密码长度不能小于6个字符'));
        }

        // 验证邮箱格式
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            return next(createError(400, '邮箱格式不正确'));
        }

        // 检查用户名是否已存在
        const existingUser = await User.findOne({ where: { username } });
        if (existingUser) {
            return next(createError(400, '用户名已存在'));
        }

        // 检查邮箱是否已存在
        const existingEmail = await User.findOne({ where: { email } });
        if (existingEmail) {
            return next(createError(400, '邮箱已被注册'));
        }

        // 创建新用户
        const user = await User.create({
            username,
            password,
            email
        });

        const token = generateToken(user);

        console.log('用户注册成功:', { username, email });

        res.status(201).json({
            user: user.toJSON(),
            token
        });
    } catch (error) {
        console.error('注册失败:', error);
        next(error);
    }
};

// 用户登录
export const login = async (req, res, next) => {
    try {
        const { username, password } = req.body;

        // 验证必要字段
        if (!username || !password) {
            return next(createError(400, '用户名和密码不能为空'));
        }

        console.log('尝试登录:', { username });

        // 查找用户
        const user = await User.findOne({ where: { username } });
        if (!user) {
            console.log('用户不存在:', { username });
            return next(createError(401, '用户名或密码错误'));
        }

        // 验证密码
        const isMatch = await user.verifyPassword(password);
        if (!isMatch) {
            console.log('密码错误:', { username });
            return next(createError(401, '用户名或密码错误'));
        }

        const token = generateToken(user);
        console.log('登录成功:', { username });

        res.json({
            user: user.toJSON(),
            token
        });
    } catch (error) {
        console.error('登录失败:', error);
        next(error);
    }
};

// 验证 token
export const validateToken = async (req, res, next) => {
    try {
        // 用户信息已经在 verifyToken 中间件中被添加到 req.user
        const user = req.user;
        
        // 返回用户信息（不包含敏感信息）
        res.json({
            id: user.id,
            username: user.username,
            email: user.email,
            avatar: user.avatar,
            exp: Date.now() + 24 * 60 * 60 * 1000 // 更新过期时间
        });
    } catch (error) {
        console.error('Token 验证失败:', error);
        next(error);
    }
}; 
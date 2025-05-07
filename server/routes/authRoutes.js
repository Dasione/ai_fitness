import express from 'express';
import { register, login, validateToken } from '../controllers/authController.js';
import { verifyToken } from '../middleware/auth.js';

const router = express.Router();

// 用户注册
router.post('/register', register);

// 用户登录
router.post('/login', login);

// 验证 token
router.get('/validate', verifyToken, validateToken);

export default router; 
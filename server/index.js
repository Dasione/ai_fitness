import express from 'express';
import cors from 'cors';
import bodyParser from 'body-parser';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';
import { initStorage } from './utils/fileStorage.js';
import { syncDatabase } from './models/index.js';
import authRoutes from './routes/authRoutes.js';
import userRoutes from './routes/userRoutes.js';
import videoRoutes from './routes/videoRoutes.js';
import statsRoutes from './routes/statsRoutes.js';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// 配置
process.env.TZ = 'Asia/Shanghai';
const PORT = process.env.PORT || 3000;

// 创建Express应用
const app = express();

// 配置CORS
app.use(cors({
    origin: ['http://localhost', 'http://localhost:5173', 'http://localhost:80', 'http://localhost:81'],
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
    allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'],
    exposedHeaders: ['Content-Range', 'X-Content-Range']
}));

// 配置中间件
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// 配置静态文件服务
const staticOptions = {
    setHeaders: (res, path) => {
        if (path.endsWith('.avi')) {
            res.set('Content-Type', 'video/x-msvideo');
        } else if (path.endsWith('.mp4')) {
            res.set('Content-Type', 'video/mp4');
        } else if (path.endsWith('.jpg') || path.endsWith('.jpeg')) {
            res.set('Content-Type', 'image/jpeg');
        } else if (path.endsWith('.png')) {
            res.set('Content-Type', 'image/png');
        } else if (path.endsWith('.gif')) {
            res.set('Content-Type', 'image/gif');
        }
        // 添加CORS头
        res.set('Access-Control-Allow-Origin', '*');
        // 添加缓存控制
        res.set('Cache-Control', 'public, max-age=31536000');
    }
};

// 确保上传目录存在
const uploadsDir = path.join(__dirname, '../public/uploads');
const runsDir = path.join(__dirname, '../runs');
if (!fs.existsSync(uploadsDir)) {
    fs.mkdirSync(uploadsDir, { recursive: true });
}
if (!fs.existsSync(runsDir)) {
    fs.mkdirSync(runsDir, { recursive: true });
}

app.use('/uploads', express.static(path.join(__dirname, '../public/uploads'), staticOptions));
app.use('/public/uploads', express.static(path.join(__dirname, '../public/uploads'), staticOptions));
app.use('/runs', express.static(path.join(__dirname, '../runs'), staticOptions));

// 请求日志中间件
app.use((req, res, next) => {
    console.log(`${new Date().toISOString()} ${req.method} ${req.url}`);
    console.log('Headers:', req.headers);
    if (req.method === 'POST' || req.method === 'PUT') {
        console.log('Body:', req.body);
    }
    next();
});

// 注册API路由
app.use('/api/auth', authRoutes);
app.use('/api/user', userRoutes);
app.use('/api/videos', videoRoutes);
app.use('/api/stats', statsRoutes);

// 错误处理
app.use((req, res) => {
    console.log(`404 Not Found: ${req.method} ${req.url}`);
    res.status(404).json({ error: { message: '请求的资源不存在' } });
});

app.use((err, req, res, next) => {
    console.error('Error:', err);
    res.status(err.status || 500).json({ error: { message: err.message || '服务器内部错误' } });
});

// 启动服务器
const start = async () => {
    try {
        await initStorage();
        await syncDatabase();
        app.listen(PORT, () => {
            console.log(`服务器运行在 http://localhost:${PORT}`);
            console.log('已注册的路由:');
            console.log('- POST /api/auth/register');
            console.log('- POST /api/auth/login');
            console.log('- GET /api/user/profile');
            console.log('- PUT /api/user/profile');
            console.log('- POST /api/user/avatar');
            console.log('- PUT /api/user/password');
            console.log('- GET /api/videos');
            console.log('- GET /api/videos/:id');
            console.log('- POST /api/videos');
            console.log('- PUT /api/videos/:id');
            console.log('- DELETE /api/videos/:id');
        });
    } catch (error) {
        console.error('服务器启动失败:', error);
        process.exit(1);
    }
};

start(); 
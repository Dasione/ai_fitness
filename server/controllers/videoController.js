import { Video, User, VideoAnalysis } from '../models/index.js';
import { createError } from '../utils/error.js';
import multer from 'multer';
import { generateUniqueFileName, saveFile, deleteFile, getProjectRoot } from '../utils/fileStorage.js';
import { processVideo } from '../utils/videoProcessor.js';
import path from 'path';
import fs from 'fs';
import { v4 as uuidv4 } from 'uuid';
import { fileURLToPath } from 'url';
import { dirname } from 'path';
import { Op } from 'sequelize';
import { spawn } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

let videoProcessorProcess = null;

// 配置文件上传
const upload = multer({
    storage: multer.memoryStorage(),
    limits: {
        fileSize: 500 * 1024 * 1024 // 限制500MB
    },
    fileFilter: (req, file, cb) => {
        const allowedTypes = ['video/mp4', 'video/webm'];
        if (allowedTypes.includes(file.mimetype)) {
            cb(null, true);
        } else {
            cb(new Error('不支持的文件类型'));
        }
    }
});

// 获取视频列表
export const getVideos = async (req, res, next) => {
    try {
        const { page = 1, limit = 10 } = req.query;
        const offset = (page - 1) * limit;

        const videos = await Video.findAndCountAll({
            where: {
                user_id: req.user.id  // 只返回当前用户的视频
            },
            include: [{
                model: User,
                as: 'owner',
                attributes: ['id', 'username', 'avatar']
            }],
            order: [['created_at', 'DESC']],
            limit: parseInt(limit),
            offset: parseInt(offset)
        });

        res.json({
            videos: videos.rows.map(video => video.toJSON()),
            total: videos.count,
            page: parseInt(page),
            totalPages: Math.ceil(videos.count / limit)
        });
    } catch (error) {
        next(error);
    }
};

// 获取单个视频
export const getVideo = async (req, res, next) => {
    try {
        const video = await Video.findByPk(req.params.id, {
            include: [{
                model: User,
                as: 'owner',
                attributes: ['id', 'username', 'avatar']
            }]
        });

        if (!video) {
            return next(createError(404, '视频不存在'));
        }

        res.json(video.toJSON());
    } catch (error) {
        next(error);
    }
};

// 处理视频的辅助函数
async function handleVideoProcessing(videoId, videoPath) {
    const video = await Video.findByPk(videoId);
    if (!video) {
        console.error('找不到视频记录:', videoId);
        return;
    }

    try {
        console.log('开始处理视频:', {
            videoId,
            videoPath,
            fileSize: video.file_size
        });

        // 处理视频并生成缩略图
        const thumbnailDir = path.join(getProjectRoot(), 'public', 'uploads', 'thumbnails');
        const { thumbnailPath, duration } = await processVideo(videoPath, thumbnailDir);

        // 更新视频记录，确保 duration 是有效的数值
        const videoDuration = duration && !isNaN(duration) ? Math.round(duration) : 0;
        
        await video.update({
            duration: videoDuration,
            thumbnail_path: path.relative(path.join(getProjectRoot(), 'public'), thumbnailPath),
            status: 'unprocessed'
        });

        console.log('视频处理完成:', {
            videoId,
            duration: videoDuration,
            thumbnailPath,
            status: 'unprocessed'
        });
    } catch (error) {
        console.error('视频处理失败:', {
            videoId,
            status: 'error',
            error: error.message,
            stack: error.stack
        });
        await video.update({ 
            duration: 0 // 设置默认时长为 0
        });
    }
}

// 上传视频
export const uploadVideo = [
    upload.single('video'),
    async (req, res, next) => {
        try {
            if (!req.file) {
                return next(createError(400, '请选择要上传的视频'));
            }

            const { title, description } = req.body;
            if (!title) {
                return next(createError(400, '视频标题不能为空'));
            }

            // 生成唯一文件名
            const fileName = generateUniqueFileName(req.file.originalname);

            // 保存视频文件
            const { path: filePath } = await saveFile('public/uploads/videos', fileName, req.file.buffer);

            // 创建视频记录
            const video = await Video.create({
                id: uuidv4(),
                title,
                description,
                file_path: filePath,
                file_size: req.file.size,
                duration: 0,
                status: 'unprocessed',
                user_id: req.user.id
            });

            // 异步处理视频（获取时长和生成缩略图）
            handleVideoProcessing(video.id, path.join(getProjectRoot(), filePath))
                .catch(error => {
                    console.error('视频处理失败:', error);
                });

            // 返回初始视频信息
            const videoData = video.toJSON();
            res.status(201).json({
                ...videoData,
                status: 'unprocessed',
                message: '视频上传成功，正在处理中'
            });
        } catch (error) {
            next(error);
        }
    }
];

// 更新视频信息
export const updateVideo = async (req, res) => {
    try {
        const { id } = req.params;
        const { title, description } = req.body;

        console.log('收到更新视频请求:', {
            id,
            title,
            description,
            body: req.body,
            params: req.params
        });

        // 验证输入
        if (!title) {
            console.log('标题为空，返回400错误');
            return res.status(400).json({ message: '视频标题不能为空' });
        }

        // 查找视频
        console.log('开始查找视频:', id);
        const video = await Video.findByPk(id);
        if (!video) {
            console.log('视频不存在，返回404错误');
            return res.status(404).json({ message: '视频不存在' });
        }
        console.log('找到视频:', video.toJSON());

        // 更新视频信息
        console.log('开始更新视频信息');
        await video.update({
            title,
            description: description || null
        });
        console.log('视频信息更新完成');

        // 重新获取更新后的视频信息
        console.log('重新获取更新后的视频信息');
        const updatedVideo = await Video.findByPk(id);
        console.log('获取到更新后的视频:', updatedVideo.toJSON());

        const response = {
            message: '视频信息更新成功',
            video: {
                id: updatedVideo.id,
                title: updatedVideo.title,
                description: updatedVideo.description,
                file_path: updatedVideo.file_path,
                thumbnail_path: updatedVideo.thumbnail_path,
                duration: updatedVideo.duration,
                status: updatedVideo.status,
                created_at: updatedVideo.created_at,
                updated_at: updatedVideo.updated_at
            }
        };
        console.log('发送响应:', response);
        return res.json(response);
    } catch (error) {
        console.error('更新视频信息失败:', {
            error: error.message,
            stack: error.stack,
            params: req.params,
            body: req.body
        });
        return res.status(500).json({ message: '更新视频信息失败' });
    }
};

// 删除视频
export const deleteVideo = async (req, res, next) => {
    try {
        console.log('开始删除视频，视频ID:', req.params.id);
        
        const video = await Video.findByPk(req.params.id);
        if (!video) {
            console.log('视频不存在，ID:', req.params.id);
            return next(createError(404, '视频不存在'));
        }

        console.log('找到视频记录:', {
            id: video.id,
            file_path: video.file_path,
            thumbnail_path: video.thumbnail_path,
            user_id: video.user_id,
            current_user_id: req.user.id
        });

        // 检查是否是视频所有者
        if (video.user_id !== req.user.id) {
            console.log('权限检查失败:', {
                video_user_id: video.user_id,
                current_user_id: req.user.id
            });
            return next(createError(403, '没有权限删除此视频'));
        }

        // 先删除相关的分析记录
        console.log('删除相关的分析记录');
        await VideoAnalysis.destroy({
            where: {
                video_id: video.id
            }
        });

        // 删除视频文件
        const videoFileName = video.file_path.split(/[/\\]/).pop();
        console.log('准备删除视频文件:', {
            full_path: video.file_path,
            file_name: videoFileName,
            directory: 'public/uploads/videos'
        });

        // 删除分析视频片段
        const baseFileName = path.parse(videoFileName).name;
        const runsDir = path.join(getProjectRoot(), 'runs');
        console.log('准备删除分析视频片段:', {
            base_file_name: baseFileName,
            runs_directory: runsDir
        });

        try {
            // 读取runs目录
            const files = fs.readdirSync(runsDir);
            // 删除所有相关的分析视频片段
            for (const file of files) {
                if (file.startsWith(baseFileName)) {
                    const filePath = path.join(runsDir, file);
                    fs.unlinkSync(filePath);
                    console.log('删除分析视频片段:', filePath);
                }
            }
        } catch (error) {
            console.error('删除分析视频片段失败:', error);
            // 继续执行，不中断删除流程
        }

        try {
            await deleteFile('public/uploads/videos', videoFileName);
            console.log('视频文件删除成功');
        } catch (error) {
            console.error('视频文件删除失败:', {
                error: error.message,
                code: error.code,
                path: video.file_path
            });
            // 继续执行，因为文件可能已经不存在
        }

        // 删除缩略图文件（如果存在）
        if (video.thumbnail_path) {
            const thumbnailFileName = video.thumbnail_path.split(/[/\\]/).pop();
            try {
                await deleteFile('public/uploads/thumbnails', thumbnailFileName);
                console.log('缩略图文件删除成功');
            } catch (error) {
                console.error('缩略图文件删除失败:', {
                    error: error.message,
                    code: error.code,
                    path: video.thumbnail_path
                });
                // 继续执行，因为文件可能已经不存在
            }
        }

        // 删除视频记录
        await video.destroy();
        console.log('视频记录删除成功');

        res.json({ message: '视频删除成功' });
    } catch (error) {
        console.error('删除视频过程中发生错误:', error);
        next(error);
    }
};

// 批量删除视频
export const deleteVideos = async (req, res, next) => {
    try {
        const { videoIds } = req.body;
        
        if (!Array.isArray(videoIds) || videoIds.length === 0) {
            return next(createError(400, '请选择要删除的视频'));
        }

        // 查找所有要删除的视频
        const videos = await Video.findAll({
            where: {
                id: videoIds,
                user_id: req.user.id // 确保只能删除自己的视频
            }
        });

        if (videos.length === 0) {
            return next(createError(404, '未找到要删除的视频'));
        }

        // 删除视频文件
        for (const video of videos) {
            try {
                // 删除视频文件
                const videoPath = path.join(getProjectRoot(), video.file_path);
                if (fs.existsSync(videoPath)) {
                    await fs.promises.unlink(videoPath);
                }

                // 删除缩略图
                if (video.thumbnail_path) {
                    const thumbnailPath = path.join(getProjectRoot(), video.thumbnail_path);
                    if (fs.existsSync(thumbnailPath)) {
                        await fs.promises.unlink(thumbnailPath);
                    }
                }

                // 删除分析记录
                await VideoAnalysis.destroy({
                    where: { video_id: video.id }
                });

                // 删除视频记录
                await video.destroy();
            } catch (error) {
                console.error(`删除视频 ${video.id} 失败:`, error);
                // 继续处理其他视频，不中断整个流程
            }
        }

        res.json({ message: '视频删除成功' });
    } catch (error) {
        next(error);
    }
};

// 获取仪表盘统计数据
export const getDashboardStats = async (req, res, next) => {
    try {
        console.log('开始获取仪表盘数据，用户ID:', req.user.id);

        // 获取视频总数
        const totalVideos = await Video.count({
            where: {
                user_id: req.user.id
            }
        });
        console.log('视频总数:', totalVideos);

        // 获取总时长
        const totalDuration = await Video.sum('duration', {
            where: {
                user_id: req.user.id
            }
        });
        console.log('总时长:', totalDuration);

        // 获取分析次数
        const totalAnalysis = await VideoAnalysis.count({
            include: [{
                model: Video,
                as: 'video',
                where: {
                    user_id: req.user.id
                }
            }]
        });
        console.log('分析次数:', totalAnalysis);

        // 获取本周的开始日期
        const today = new Date();
        const startOfLastWeek = new Date(today);
        // 设置为过去7天
        startOfLastWeek.setDate(today.getDate() - 7);
        startOfLastWeek.setHours(0, 0, 0, 0);
        
        console.log('最近一周开始日期:', startOfLastWeek.toISOString());

        // 获取最近一周的训练视频
        const weeklyVideos = await Video.findAll({
            where: {
                user_id: req.user.id,
                created_at: {
                    [Op.gte]: startOfLastWeek
                }
            },
            include: [{
                model: VideoAnalysis,
                as: 'analyses'
            }]
        });

        // 计算最近一周训练数据
        const weeklyTrainings = weeklyVideos.length;
        
        // 计算最近一周训练总时长（单位：秒）
        const weeklyDuration = weeklyVideos.reduce((sum, video) => {
            return sum + (video.duration || 0);
        }, 0);
        
        // 计算最近一周平均评分
        const weeklyScores = weeklyVideos.flatMap(video => 
            video.analyses.map(analysis => analysis.average_score)
        ).filter(score => score !== null && score !== undefined && !isNaN(score));
        
        const weeklyAverageScore = weeklyScores.length > 0 
            ? weeklyScores.reduce((sum, score) => sum + score, 0) / weeklyScores.length 
            : 0;
            
        console.log('最近一周训练统计:', {
            weeklyTrainings,
            weeklyDuration,
            weeklyAverageScore,
            weeklyVideosCount: weeklyVideos.length,
            weeklyScoresCount: weeklyScores.length
        });

        // 获取所有分析记录用于评分分布和趋势
        const allAnalysis = await VideoAnalysis.findAll({
            include: [{
                model: Video,
                as: 'video',
                where: {
                    user_id: req.user.id
                },
                attributes: ['title']
            }],
            order: [['created_at', 'ASC']]
        });

        // 计算评分分布（使用所有动作的评分）
        const scoreDistribution = {
            excellent: 0, // 90-100
            good: 0,      // 80-89
            fair: 0,      // 70-79
            poor: 0       // 0-69
        };


        // 统计所有动作的评分
        allAnalysis.forEach((analysis, index) => {
            try {
                if (analysis.score_arr && Array.isArray(analysis.score_arr)) {
                    analysis.score_arr.forEach((scoreItem, scoreIndex) => {
                        // 处理嵌套数组的情况
                        const score = Array.isArray(scoreItem) ? scoreItem[0] : scoreItem;
                        
                        if (typeof score === 'number' && !isNaN(score)) {
                            if (score >= 90) scoreDistribution.excellent++;
                            else if (score >= 80) scoreDistribution.good++;
                            else if (score >= 70) scoreDistribution.fair++;
                            else scoreDistribution.poor++;

                            ;
                        }
                    });
                } else {
                    console.warn(`第 ${index + 1} 条分析记录没有 score_arr 或不是数组:`, analysis);
                }
            } catch (error) {
                console.error(`处理第 ${index + 1} 条分析记录时出错:`, error);
            }
        });

        console.log('评分分布统计结果:', scoreDistribution);

        // 计算评分趋势
        const scoreTrend = allAnalysis.map(analysis => ({
            title: analysis.video?.title || '未知视频',
            score: analysis.average_score || 0,
            date: analysis.created_at
        }));

        // 获取本周上传视频数量
        const weeklyUploads = await Video.count({
            where: {
                user_id: req.user.id,
                created_at: {
                    [Op.gte]: startOfLastWeek
                }
            }
        });

        // 获取最近7天每天的上传数量
        const dailyUploads = await Video.findAll({
            where: {
                user_id: req.user.id,
                created_at: {
                    [Op.gte]: startOfLastWeek
                }
            },
            attributes: [
                [Video.sequelize.fn('DATE', Video.sequelize.col('created_at')), 'date'],
                [Video.sequelize.fn('COUNT', Video.sequelize.col('id')), 'count']
            ],
            group: [Video.sequelize.fn('DATE', Video.sequelize.col('created_at'))],
            order: [[Video.sequelize.fn('DATE', Video.sequelize.col('created_at')), 'ASC']]
        });

        // 格式化最近7天每天的上传数量
        const uploadTrend = [];
        for(let i = 0; i < 7; i++) {
            const date = new Date(today);
            date.setDate(date.getDate() - (6 - i)); // 计算过去7天中的每一天
            const dateStr = date.toISOString().split('T')[0];
            const upload = dailyUploads.find(d => d.getDataValue('date') === dateStr);
            uploadTrend.push({
                day: `${date.getMonth()+1}/${date.getDate()}`,
                count: upload ? parseInt(upload.getDataValue('count')) : 0
            });
        }

        // 获取最近的分析记录
        const recentAnalysis = await VideoAnalysis.findAll({
            include: [{
                model: Video,
                as: 'video',
                where: {
                    user_id: req.user.id
                },
                attributes: ['title']
            }],
            order: [['created_at', 'DESC']],
            limit: 10
        });

        // 格式化最近分析记录
        const formattedRecentAnalysis = recentAnalysis.map(analysis => {
            try {
                return {
                    videoId: analysis.video_id,
                    videoTitle: analysis.video?.title || '未知视频',
                    date: analysis.created_at,
                    score: analysis.average_score || 0,
                    status: analysis.status || 'unknown',
                    hand: analysis.hand_choice || 'unknown'
                };
            } catch (error) {
                console.error('格式化分析记录时出错:', error);
                return {
                    videoId: analysis.video_id,
                    videoTitle: '未知视频',
                    date: analysis.created_at,
                    score: 0,
                    status: 'unknown',
                    hand: 'unknown'
                };
            }
        });

        console.log('Dashboard data fetched successfully:', {
            userId: req.user.id,
            totalVideos,
            totalDuration,
            totalAnalysis,
            weeklyTrainings,
            weeklyDuration,
            weeklyAverageScore,
            weeklyUploads,
            uploadTrend,
            scoreDistribution,
            recentAnalysisCount: formattedRecentAnalysis.length
        });

        res.json({
            totalVideos,
            totalDuration: totalDuration || 0,
            totalAnalysis,
            weeklyTrainings,
            weeklyDuration,
            weeklyAverageScore,
            weeklyUploads,
            uploadTrend,
            scoreDistribution,
            scoreTrend,
            recentAnalysis: formattedRecentAnalysis
        });
    } catch (error) {
        console.error('获取仪表盘数据失败:', {
            error: error.message,
            stack: error.stack,
            userId: req.user.id
        });
        next(error);
    }
};

// 启动视频处理服务
const startVideoService = async (req, res) => {
    try {
        if (videoProcessorProcess) {
            return res.status(400).json({ message: '视频处理服务已在运行中' });
        }

        // 更新Python脚本路径
        const scriptPath = path.join(__dirname, '../../src/utils/video_processor.py');
        videoProcessorProcess = spawn('python', [scriptPath]);

        videoProcessorProcess.stdout.on('data', (data) => {
            console.log(`视频处理服务输出: ${data}`);
        });

        videoProcessorProcess.stderr.on('data', (data) => {
            console.error(`视频处理服务错误: ${data}`);
        });

        videoProcessorProcess.on('close', (code) => {
            console.log(`视频处理服务退出，代码: ${code}`);
            videoProcessorProcess = null;
        });

        // 等待服务启动
        await new Promise(resolve => setTimeout(resolve, 2000));

        res.json({ message: '视频处理服务已启动' });
    } catch (error) {
        console.error('启动视频处理服务失败:', error);
        res.status(500).json({ message: '启动视频处理服务失败' });
    }
};

// 停止视频处理服务
const stopVideoService = async (req, res) => {
    try {
        if (!videoProcessorProcess) {
            return res.status(400).json({ message: '视频处理服务未运行' });
        }

        // 发送终止信号
        videoProcessorProcess.kill();
        videoProcessorProcess = null;

        res.json({ message: '视频处理服务已停止' });
    } catch (error) {
        console.error('停止视频处理服务失败:', error);
        res.status(500).json({ message: '停止视频处理服务失败' });
    }
};

// 修改导出方式
export {
    startVideoService,
    stopVideoService
};
import express from 'express';
import { Video, User, VideoAnalysis } from '../models/index.js';
import { Op } from 'sequelize';

const router = express.Router();

// 获取用户排行榜
router.get('/user-ranking', async (req, res) => {
  try {
    console.log('开始获取用户排行榜数据...');
    
    // 获取所有用户的训练数据
    const users = await User.findAll({
      attributes: ['id', 'username', 'avatar'],
      include: [{
        model: Video,
        as: 'videos',
        attributes: ['duration', 'created_at'],
        include: [{
          model: VideoAnalysis,
          as: 'analyses',
          attributes: ['average_score']
        }]
      }]
    });
    
    // 计算每个用户的训练时长和平均评分
    const userStats = users.map(user => {
      const videos = user.videos || [];
      const totalDuration = videos.reduce((sum, video) => {
        return sum + (video.duration || 0);
      }, 0);
      
      // 计算平均评分
      const allScores = videos.flatMap(video => {
        return (video.analyses || []).map(analysis => {
          return analysis.average_score;
        });
      });
      
      const averageScore = allScores.length > 0 
        ? allScores.reduce((sum, score) => sum + score, 0) / allScores.length 
        : 0;

      // 确定最近的活动时间
      let lastActivity = null;
      if (videos.length > 0) {
        // 找出最新的视频创建时间
        const latestVideo = videos.reduce((latest, video) => {
          return !latest || (video.created_at && new Date(video.created_at) > new Date(latest.created_at)) 
            ? video 
            : latest;
        }, null);
        
        if (latestVideo && latestVideo.created_at) {
          lastActivity = latestVideo.created_at;
        }
      }

      return {
        username: user.username,
        avatar: user.avatar,
        totalDuration,
        averageScore,
        videoCount: videos.length,
        lastActivity: lastActivity || new Date().toISOString()
      };
    });

    // 过滤掉没有训练数据的用户（总时长为0且平均分为0的用户）
    const validUserStats = userStats.filter(stat => {
      const hasData = stat.totalDuration > 0 || stat.averageScore > 0;
      return hasData;
    });

    // 按训练时长降序排序
    const ranking = validUserStats
      .sort((a, b) => b.totalDuration - a.totalDuration);

    // 分页处理
    const page = parseInt(req.query.page) || 1;
    const pageSize = parseInt(req.query.pageSize) || 10;
    const start = (page - 1) * pageSize;
    const end = start + pageSize;
    const paginatedRanking = ranking.slice(start, end);

    // 设置总数量头
    res.set('X-Total-Count', ranking.length.toString());
    res.json(paginatedRanking);
  } catch (error) {
    console.error('获取用户排行榜失败:', error);
    
    res.status(500).json({ 
      error: '获取用户排行榜失败',
      message: error.message
    });
  }
});

export default router; 
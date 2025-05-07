const express = require('express');
const router = express.Router();
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const { Video } = require('../models');
const { generateThumbnail } = require('../utils/video');

// 确保上传目录存在
const uploadDir = path.join(__dirname, '../../public/uploads');
const referenceDir = path.join(uploadDir, 'reference');
fs.mkdirSync(uploadDir, { recursive: true });
fs.mkdirSync(referenceDir, { recursive: true });

// 初始化标准视频
router.post('/init-standard-video', async (req, res) => {
  try {
    // 检查标准视频是否已存在
    const existingVideo = await Video.findOne({
      where: { id: 'standard-exercise-video' }
    });

    if (existingVideo) {
      return res.json({ message: '标准视频已存在' });
    }

    // 源文件路径
    const sourceVideoPath = path.join(__dirname, '../../public/uploads/reference/standard-exercise.mp4');
    const sourceThumbPath = path.join(__dirname, '../../public/uploads/reference/standard-exercise-thumb.jpg');

    // 检查源文件是否存在
    if (!fs.existsSync(sourceVideoPath)) {
      return res.status(404).json({ error: '标准视频文件不存在' });
    }

    // 创建标准视频记录
    const video = await Video.create({
      id: 'standard-exercise-video',
      title: '标准动作示范',
      url: '/uploads/reference/standard-exercise.mp4',
      thumbnail: '/uploads/reference/standard-exercise-thumb.jpg',
      duration: 0, // 这里可以添加获取视频时长的逻辑
      status: 'completed',
      userId: null, // 设置为 null 表示所有用户可用
      isPublic: true
    });

    res.json({ message: '标准视频初始化成功', video });
  } catch (error) {
    console.error('初始化标准视频失败:', error);
    res.status(500).json({ error: '初始化标准视频失败' });
  }
});

// ... existing code ...

module.exports = router; 
import ffmpeg from 'fluent-ffmpeg';
import ffmpegInstaller from '@ffmpeg-installer/ffmpeg';
import ffprobeInstaller from '@ffprobe-installer/ffprobe';
import { promises as fs } from 'fs';
import path from 'path';

// 配置 FFmpeg 和 FFprobe 路径
ffmpeg.setFfmpegPath(ffmpegInstaller.path);
ffmpeg.setFfprobePath(ffprobeInstaller.path);

// 处理视频并生成缩略图
export const processVideo = async (videoPath, outputDir) => {
  // 确保输出目录存在
  await fs.mkdir(outputDir, { recursive: true });

  const fileName = path.basename(videoPath, path.extname(videoPath));
  const thumbnailPath = path.join(outputDir, `thumbnail-${fileName}.jpg`);

  // 获取视频信息
  const getVideoInfo = () => {
    return new Promise((resolve, reject) => {
      ffmpeg.ffprobe(videoPath, {
        select_streams: 'v:0',
        show_entries: 'stream=duration,format=duration',
        v: 'quiet',
        of: 'json'
      }, (err, data) => {
        if (err) {
          console.error('获取视频信息失败:', err);
          reject(err);
          return;
        }
        resolve(data);
      });
    });
  };

  // 生成缩略图
  const generateThumbnail = () => {
    return new Promise((resolve, reject) => {
      ffmpeg(videoPath)
        .screenshots({
          timestamps: [0],
          filename: `thumbnail-${fileName}.jpg`,
          folder: outputDir,
          size: '640x360'
        })
        .on('end', resolve)
        .on('error', reject);
    });
  };

  try {
    // 并行执行获取视频信息和生成缩略图
    const [videoInfo, _] = await Promise.all([
      getVideoInfo(),
      generateThumbnail()
    ]);

    // 从视频信息中提取时长
    let duration = 0;
    try {
      duration = videoInfo.format?.duration || 
                 videoInfo.streams?.[0]?.duration || 
                 0;
    } catch (error) {
      console.error('解析视频信息失败:', error);
    }

    return {
      thumbnailPath,
      duration: parseFloat(duration) || 0
    };
  } catch (error) {
    console.error('视频处理失败:', error);
    throw error;
  }
};

// 转换视频格式（如果需要）
export const convertVideo = async (inputPath, outputPath) => {
  return new Promise((resolve, reject) => {
    ffmpeg(inputPath)
      .toFormat('mp4')
      .on('end', resolve)
      .on('error', reject)
      .save(outputPath);
  });
}; 
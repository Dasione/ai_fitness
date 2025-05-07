import ffmpeg from 'fluent-ffmpeg';
import ffmpegInstaller from '@ffmpeg-installer/ffmpeg';
import ffprobeInstaller from '@ffprobe-installer/ffprobe';

// 设置 ffmpeg 和 ffprobe 路径
ffmpeg.setFfmpegPath(ffmpegInstaller.path);
ffmpeg.setFfprobePath(ffprobeInstaller.path);

// 添加调试日志
console.log('FFmpeg 配置:', {
    ffmpegPath: ffmpegInstaller.path,
    ffprobePath: ffprobeInstaller.path
});

export default ffmpeg; 
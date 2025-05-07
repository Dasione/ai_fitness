import sequelize from '../config/database.js';
import User from './user.js';
import Video from './video.js';
import VideoAnalysis from './videoAnalysis.js';

// 同步所有模型到数据库
const syncDatabase = async () => {
    try {
        // 启用 SQL 日志
        sequelize.options.logging = console.log;
        
        await sequelize.sync();
        console.log('数据库同步成功');
        
        // 恢复默认日志设置
        sequelize.options.logging = false;
    } catch (error) {
        console.error('数据库同步失败:', error);
        throw error;
    }
};

export { User, Video, VideoAnalysis, syncDatabase }; 
import { DataTypes } from 'sequelize';
import sequelize from '../config/database.js';
import Video from './video.js';

const VideoAnalysis = sequelize.define('VideoAnalysis', {
    id: {
        type: DataTypes.UUID,
        defaultValue: DataTypes.UUIDV4,
        primaryKey: true
    },
    video_id: {
        type: DataTypes.UUID,
        allowNull: false,
        references: {
            model: Video,
            key: 'id'
        }
    },
    hand_choice: {
        type: DataTypes.ENUM('left', 'right'),
        allowNull: false
    },
    case_arr: {
        type: DataTypes.JSON,
        comment: '错误种类数组'
    },
    score_arr: {
        type: DataTypes.JSON,
        comment: '分数数组'
    },
    output_arr: {
        type: DataTypes.JSON,
        comment: '视频片段地址数组'
    },
    average_score: {
        type: DataTypes.FLOAT,
        validate: {
            min: 0,
            max: 100
        }
    },
    suggestions: {
        type: DataTypes.JSON,
        comment: 'LLM生成的运动建议',
        defaultValue: null
    },
    status: {
        type: DataTypes.ENUM('completed', 'processing', 'error'),
        defaultValue: 'processing'
    },
    error_message: {
        type: DataTypes.TEXT,
        allowNull: true
    }
}, {
    tableName: 'video_analyses',
    timestamps: true,
    createdAt: 'created_at',
    updatedAt: 'updated_at',
    indexes: [
        {
            fields: ['video_id', 'hand_choice'],
            unique: true,
            name: 'unique_video_hand'
        }
    ]
});

// 定义与视频的关联关系
VideoAnalysis.belongsTo(Video, {
    foreignKey: 'video_id',
    as: 'video'
});

Video.hasMany(VideoAnalysis, {
    foreignKey: 'video_id',
    as: 'analyses'
});

export default VideoAnalysis; 
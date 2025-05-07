import { DataTypes } from 'sequelize';
import sequelize from '../config/database.js';
import User from './user.js';

const Video = sequelize.define('Video', {
    id: {
        type: DataTypes.UUID,
        defaultValue: DataTypes.UUIDV4,
        primaryKey: true
    },
    title: {
        type: DataTypes.STRING(255),
        allowNull: false,
        validate: {
            len: [1, 255]
        }
    },
    description: {
        type: DataTypes.TEXT,
        validate: {
            len: [0, 1000]
        }
    },
    file_path: {
        type: DataTypes.STRING(255),
        allowNull: false
    },
    thumbnail_path: {
        type: DataTypes.STRING(255)
    },
    duration: {
        type: DataTypes.INTEGER,
        comment: '视频时长（秒）',
        validate: {
            min: 0
        }
    },
    file_size: {
        type: DataTypes.BIGINT,
        comment: '文件大小（字节）',
        validate: {
            min: 0
        }
    },
    status: {
        type: DataTypes.ENUM('unprocessed', 'processing', 'processed', 'error'),
        defaultValue: 'unprocessed'
    },
    user_id: {
        type: DataTypes.UUID,
        allowNull: false,
        references: {
            model: User,
            key: 'id'
        }
    }
}, {
    tableName: 'videos',
    timestamps: true,
    createdAt: 'created_at',
    updatedAt: 'updated_at',
    indexes: [
        {
            fields: ['user_id', 'status', 'created_at'],
            name: 'videos_user_status_date'
        }
    ]
});

// 定义与用户的关联关系
Video.belongsTo(User, {
    foreignKey: 'user_id',
    as: 'owner'
});

User.hasMany(Video, {
    foreignKey: 'user_id',
    as: 'videos'
});

export default Video; 
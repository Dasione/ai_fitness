import { Sequelize } from 'sequelize';
import dotenv from 'dotenv';

dotenv.config();

const sequelize = new Sequelize(
    process.env.DB_NAME,
    process.env.DB_USER,
    process.env.DB_PASSWORD,
    {
        host: process.env.DB_HOST,
        dialect: 'mysql',
        logging: process.env.NODE_ENV === 'development',
        timezone: '+08:00',
        pool: {
            max: 5, // 连接池最大连接数
            min: 0, // 连接池最小连接数
            acquire: 30000, // 获取连接最大等待时间
            idle: 10000 // 连接最大空闲时间
        },
        define: {
            charset: 'utf8mb4',
            collate: 'utf8mb4_unicode_ci',
            timestamps: true,
            underscored: true
        }
    }
);

// 测试数据库连接
const testConnection = async () => {
    try {
        await sequelize.authenticate();
        console.log('数据库连接成功');
    } catch (error) {
        console.error('数据库连接失败:', error);
        process.exit(1);
    }
};

testConnection();

export default sequelize; 
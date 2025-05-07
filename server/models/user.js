import { DataTypes } from 'sequelize';
import sequelize from '../config/database.js';
import bcrypt from 'bcryptjs';

const User = sequelize.define('User', {
    id: {
        type: DataTypes.UUID,
        defaultValue: DataTypes.UUIDV4,
        primaryKey: true
    },
    username: {
        type: DataTypes.STRING(50),
        allowNull: false,
        unique: true,
        validate: {
            len: [3, 50]
        }
    },
    password: {
        type: DataTypes.STRING(255),
        allowNull: false,
        validate: {
            len: [6, 255]
        }
    },
    email: {
        type: DataTypes.STRING(100),
        unique: true,
        validate: {
            isEmail: true
        }
    },
    avatar: {
        type: DataTypes.STRING(255),
        allowNull: true
    }
}, {
    tableName: 'users',
    timestamps: true,
    createdAt: 'created_at',
    updatedAt: 'updated_at'
});

// 密码加密中间件
User.beforeCreate(async (user) => {
    if (user.password) {
        const salt = await bcrypt.genSalt(10);
        user.password = await bcrypt.hash(user.password, salt);
    }
});

// 验证密码方法
User.prototype.verifyPassword = async function(password) {
    return bcrypt.compare(password, this.password);
};

// 修改密码方法
User.prototype.changePassword = async function(newPassword) {
    if (!newPassword) {
        throw new Error('新密码不能为空');
    }
    if (newPassword.length < 6) {
        throw new Error('密码长度不能小于6个字符');
    }
    const salt = await bcrypt.genSalt(10);
    this.password = await bcrypt.hash(newPassword, salt);
    await this.save();
};

// 转换为JSON时排除密码
User.prototype.toJSON = function() {
    const values = { ...this.get() };
    delete values.password;
    return values;
};

export default User;
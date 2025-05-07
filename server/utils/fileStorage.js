import { promises as fs } from 'fs';
import path from 'path';
import crypto from 'crypto';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// 获取项目根目录
export const getProjectRoot = () => {
  return path.join(__dirname, '..', '..');
};

// 初始化存储目录
export const initStorage = async () => {
  const uploadDirs = [
    'public/uploads/videos',
    'public/uploads/thumbnails',
    'public/uploads/avatars',
    'public/temp'
  ];

  for (const dir of uploadDirs) {
    try {
      const fullPath = path.join(getProjectRoot(), dir);
      await fs.mkdir(fullPath, { recursive: true });
      console.log(`创建目录成功: ${fullPath}`);
    } catch (error) {
      console.error(`创建目录失败: ${dir}`, error);
      throw error;
    }
  }
}

// 生成唯一文件名
export const generateUniqueFileName = (originalName) => {
  const timestamp = Date.now();
  const random = crypto.randomBytes(8).toString('hex');
  const ext = path.extname(originalName);
  return `${timestamp}-${random}${ext}`;
}

// 保存文件
export const saveFile = async (directory, fileName, buffer) => {
  const fullDir = path.join(getProjectRoot(), directory);
  const filePath = path.join(fullDir, fileName);
  
  // 确保目录存在
  await fs.mkdir(fullDir, { recursive: true });
  
  // 保存文件
  await fs.writeFile(filePath, buffer);
  
  // 返回相对路径
  const relativePath = path.join(directory, fileName);
  
  return {
    fileName,
    path: relativePath
  }
}

// 删除文件
export const deleteFile = async (directory, filename) => {
  const filePath = path.join(getProjectRoot(), directory, filename);
  try {
    await fs.unlink(filePath);
    return true;
  } catch (error) {
    if (error.code === 'ENOENT') {
      return false;
    }
    throw error;
  }
}
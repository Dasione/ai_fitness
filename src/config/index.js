// API配置
console.log('环境变量:', {
    VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
    MODE: import.meta.env.MODE,
    DEV: import.meta.env.DEV,
    PROD: import.meta.env.PROD
});

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000'
console.log('最终使用的API基础URL:', API_BASE_URL);

// 上传配置
export const UPLOAD_CONFIG = {
  maxSize: 2, // MB
  allowedTypes: ['image/jpeg', 'image/png', 'image/gif']
}

// 分页配置
export const PAGINATION_CONFIG = {
  pageSize: 10,
  pageSizes: [10, 20, 50, 100]
}

// 路由配置
export const ROUTE_CONFIG = {
  home: '/',
  login: '/login',
  profile: '/profile',
  training: '/training',
  analysis: '/analysis',
  videos: '/videos',
  ranking: '/ranking',
  dashboard: '/dashboard'
}

// 主题配置
export const THEME_CONFIG = {
  primaryColor: '#409EFF',
  successColor: '#67C23A',
  warningColor: '#E6A23C',
  dangerColor: '#F56C6C',
  infoColor: '#909399'
} 
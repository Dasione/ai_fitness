import axios from 'axios';
import { API_BASE_URL } from '@/config';

console.log('API配置:', {
    baseURL: `${API_BASE_URL}/api`,
    env: import.meta.env.MODE,
    viteApiBaseUrl: import.meta.env.VITE_API_BASE_URL
});

// 创建 axios 实例
const api = axios.create({
    baseURL: `${API_BASE_URL}/api`, // 使用环境变量中的基础URL
    timeout: 300000, // 请求超时时间设置为 5 分钟
    headers: {
        'Content-Type': 'application/json'
    }
});

// 请求拦截器
api.interceptors.request.use(
    config => {
        // 从 localStorage 获取 token
        const token = localStorage.getItem('token');
        console.log('请求详情:', {
            url: `${config.baseURL}${config.url}`,
            method: config.method,
            baseURL: config.baseURL,
            headers: config.headers,
            token: token ? '存在' : '不存在',
            data: config.data
        });

        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
            console.log('添加认证头:', {
                Authorization: `Bearer ${token.substring(0, 10)}...`
            });
        } else {
            console.warn('未找到认证 token，请求可能会被拒绝');
        }
        return config;
    },
    error => {
        console.error('请求拦截器错误:', error);
        return Promise.reject(error);
    }
);

// 响应拦截器
api.interceptors.response.use(
    response => {
        console.log('响应详情:', {
            url: response.config.url,
            status: response.status,
            statusText: response.statusText,
            data: response.data,
            headers: response.headers
        });
        return response;
    },
    error => {
        console.error('响应错误详情:', {
            url: error.config?.url,
            baseURL: error.config?.baseURL,
            method: error.config?.method,
            message: error.message,
            status: error.response?.status,
            data: error.response?.data,
            headers: error.response?.headers,
            config: error.config
        });

        if (error.response) {
            switch (error.response.status) {
                case 401:
                    console.warn('认证失败，清除 token 并跳转到登录页');
                    // 清除认证信息
                    localStorage.removeItem('token');
                    localStorage.removeItem('user');
                    // 使用 router 进行导航
                    if (window.$router) {
                        window.$router.push({
                            path: '/auth/login',
                            query: { redirect: window.$router.currentRoute.value.fullPath }
                        });
                    }
                    break;
                case 403:
                    console.error('权限不足，请确认是否有权限访问该资源');
                    break;
                case 404:
                    // 检查是否是分析结果的请求
                    if (error.config.url.includes('/analysis')) {
                        console.debug('视频尚未进行分析');
                    } else {
                        console.error('请求的资源不存在，请检查 URL 是否正确');
                    }
                    break;
                case 500:
                    console.error('服务器错误，请检查服务器日志');
                    break;
                default:
                    console.error(`请求失败，状态码: ${error.response.status}`);
            }
        } else if (error.request) {
            console.error('未收到响应，网络请求详情:', {
                url: error.config?.url,
                baseURL: error.config?.baseURL,
                method: error.config?.method,
                headers: error.config?.headers
            });
        } else {
            console.error('请求配置错误:', error.message);
        }
        return Promise.reject(error);
    }
);

export default api; 
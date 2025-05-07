/**
 * index.js
 * 路由配置模块
 * 功能：
 * - 定义应用的路由规则
 * - 配置路由组件映射
 * - 处理路由导航
 */

import { createRouter, createWebHistory } from 'vue-router';
import { useUserStore } from '@/store/modules/user';

// 需要认证的路由配置
const authRoutes = [
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile.vue')
  },
  {
    path: '/videos',
    name: 'Videos',
    component: () => import('@/views/Videos.vue')
  },
  {
    path: '/analysis',
    name: 'Analysis',
    component: () => import('@/views/Analysis.vue')
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue')
  },
  {
    path: '/ranking',
    name: 'Ranking',
    component: () => import('@/views/Ranking.vue')
  },
  {
    path: '/training',
    name: 'Training',
    component: () => import('@/views/Training.vue')
  }
].map(route => ({ ...route, meta: { requiresAuth: true } }));

// 路由配置
const routes = [
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('@/views/Home.vue')
      },
      ...authRoutes
    ]
  },
  {
    path: '/auth',
    name: 'Auth',
    component: () => import('@/layouts/MainLayout.vue'),
    children: [
      {
        path: 'login',
        name: 'Login',
        component: () => import('@/views/Auth.vue')
      },
      {
        path: 'register',
        name: 'Register',
        component: () => import('@/views/Auth.vue')
      }
    ]
  }
];

// 创建路由实例
const router = createRouter({
  history: createWebHistory(),
  routes
});

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore();
  
  // 如果访问的是登录或注册页面
  if (to.path.startsWith('/auth/')) {
    if (userStore.isAuthenticated) {
      // 如果已登录，重定向到首页
      next('/');
    } else {
      next();
    }
    return;
  }

  // 如果访问需要认证的页面
  if (to.meta.requiresAuth) {
    // 初始化用户状态（包括验证 token）
    if (!userStore.isInitialized) {
      await userStore.initializeUser();
    }

    if (!userStore.isAuthenticated) {
      // 保存用户要访问的页面路径
      next({
        path: '/auth/login',
        query: { redirect: to.fullPath }
      });
    } else {
      next();
    }
  } else {
    next();
  }
});

export default router; 
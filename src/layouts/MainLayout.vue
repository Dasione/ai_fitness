<template>
  <el-container class="layout-container">
    <el-header class="header">
      <div class="logo">
        <span class="logo-text">智能健身</span>
      </div>
      <div class="header-right">
        <el-dropdown @command="handleCommand">
          <span class="user-info">
            <el-avatar :size="32" :src="userInfo?.avatar || ''">
              {{ userInfo?.username?.charAt(0) || 'U' }}
            </el-avatar>
            <span>{{ userInfo?.username || '用户' }}</span>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">账户管理</el-dropdown-item>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>

    <el-container>
      <el-aside width="170px">
        <el-menu
          :default-active="activeMenu"
          class="side-menu"
          router
        >
          <el-menu-item index="/">
            <el-icon><House /></el-icon>
            <span>首页</span>
          </el-menu-item>
          <el-menu-item index="/training">
            <el-icon><Monitor /></el-icon>
            <span>智能训练</span>
          </el-menu-item>
          <el-menu-item index="/videos">
            <el-icon><VideoCamera /></el-icon>
            <span>训练视频管理</span>
          </el-menu-item>
          <el-menu-item index="/analysis">
            <el-icon><DataAnalysis /></el-icon>
            <span>AI动作评估</span>
          </el-menu-item>
          <el-menu-item index="/dashboard">
            <el-icon><TrendCharts /></el-icon>
            <span>训练数据</span>
          </el-menu-item>
          <el-menu-item index="/ranking">
            <el-icon><Medal /></el-icon>
            <span>排行榜</span>
          </el-menu-item>
          <el-menu-item index="/profile">
            <el-icon><User /></el-icon>
            <span>个人中心</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-main>
        <router-view v-slot="{ Component }">
          <component :is="Component" />
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/store/modules/user'
import { House, VideoCamera, DataAnalysis, TrendCharts, User, Monitor, Medal } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const userInfo = computed(() => userStore.getUserInfo)
const activeMenu = computed(() => route.path)

const handleCommand = async (command) => {
  if (command === 'logout') {
    try {
      await userStore.logoutUser()
      ElMessage.success('退出成功')
      router.replace('/auth/login')
    } catch (error) {
      console.error('退出登录失败:', error)
      ElMessage.error('退出失败')
    }
  } else if (command === 'profile') {
    router.push('/profile')
  }
}
</script>

<style lang="scss" scoped>
.layout-container {
  height: 100vh;
  
  .header {
    background: #fff;
    border-bottom: 1px solid #dcdfe6;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 20px;

    .logo {
      display: flex;
      align-items: center;
      
      .logo-text {
        font-size: 20px;
        font-weight: bold;
        color: #409eff;
      }
    }

    .header-right {
      .user-info {
        display: flex;
        align-items: center;
        cursor: pointer;
        
        span {
          margin-left: 8px;
        }
      }
    }
  }

  .side-menu {
    height: calc(100vh - 60px);
    border-right: none;
  }

  .el-main {
    background: #f5f7fa;
    padding: 20px;
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style> 
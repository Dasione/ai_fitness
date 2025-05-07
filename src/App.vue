<!--
  App.vue
  应用程序根组件
  功能：
  - 提供应用程序的基础布局
  - 配置路由视图
-->
<script setup>
import { onMounted, ref } from 'vue'
import { useUserStore } from '@/store/modules/user'

const userStore = useUserStore()
const isInitialized = ref(false)

onMounted(async () => {
  // 初始化用户状态（包括验证 token）
  await userStore.initializeUser()
  isInitialized.value = true
})
</script>

<template>
  <router-view v-if="isInitialized" />
</template>

<style>
/* 全局样式 */
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
}

#app {
  height: 100%;
  font-family: var(--el-font-family);
}

/* 页面过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

<style scoped>
/* 应用容器样式 */
.app-container {
  height: 100vh;
  width: 100vw;
  background-color: var(--el-bg-color-page);
}
</style>

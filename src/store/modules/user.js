import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/utils/api'
import { register, login } from '@/services/auth'
import router from '@/router'

export const useUserStore = defineStore('user', () => {
  console.log('初始化用户 store')
  
  const token = ref(null)
  const userInfo = ref(null)
  const isInitialized = ref(false)

  // 验证 token 是否有效
  async function validateToken() {
    if (!token.value) {
      console.log('没有 token，清除认证信息')
      logoutUser()
      return false
    }

    try {
      // 调用后端验证接口
      const response = await api.get('/auth/validate')
      userInfo.value = response.data
      return true
    } catch (error) {
      console.error('Token 验证失败:', error)
      logoutUser()
      return false
    }
  }

  // 初始化用户信息
  async function initializeUser() {
    if (isInitialized.value) return

    try {
      // 从 localStorage 获取 token
      const storedToken = localStorage.getItem('token')
      if (storedToken) {
        token.value = storedToken
        // 设置 axios 默认请求头
        api.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`
        
        // 验证 token
        const isValid = await validateToken()
        if (!isValid) {
          logoutUser()
        }
      } else {
        // 如果没有 token，清除所有认证信息
        logoutUser()
      }
      isInitialized.value = true
    } catch (error) {
      console.error('初始化用户信息失败:', error)
      logoutUser()
    }
  }

  // 检查 token 是否过期
  const isTokenExpired = (exp) => {
    if (!exp) return true
    // 添加 8 小时的时区偏移
    const now = Date.now() + 8 * 60 * 60 * 1000
    return exp < now
  }
  
  const isAuthenticated = computed(() => {
    if (!token.value || !userInfo.value) return false
    // 检查 token 是否过期
    if (userInfo.value.exp && isTokenExpired(userInfo.value.exp)) {
      logoutUser()
      return false
    }
    return true
  })

  const getUserInfo = computed(() => userInfo.value)

  async function loginUser(credentials) {
    console.log('调用 loginUser 方法')
    try {
      const response = await login(credentials)
      // 添加过期时间（例如 24 小时），使用东八区时间
      const userData = {
        ...response.user,
        exp: Date.now() + 24 * 60 * 60 * 1000
      }
      token.value = response.token
      userInfo.value = userData
      localStorage.setItem('token', response.token)
      localStorage.setItem('user', JSON.stringify(userData))
      // 设置 axios 默认请求头
      api.defaults.headers.common['Authorization'] = `Bearer ${response.token}`
      return true
    } catch (error) {
      console.error('loginUser 错误:', error)
      throw error
    }
  }
  
  async function registerUser(userData) {
    console.log('调用 registerUser 方法，参数:', userData)
    try {
      const response = await register(userData)
      console.log('注册响应:', response)
      // 添加过期时间（例如 24 小时），使用东八区时间
      const userInfoData = {
        ...response.user,
        exp: Date.now() + 24 * 60 * 60 * 1000
      }
      token.value = response.token
      userInfo.value = userInfoData
      localStorage.setItem('token', response.token)
      localStorage.setItem('user', JSON.stringify(userInfoData))
      // 设置 axios 默认请求头
      api.defaults.headers.common['Authorization'] = `Bearer ${response.token}`
      return true
    } catch (error) {
      console.error('registerUser 错误:', error)
      throw error
    }
  }
  
  async function logoutUser() {
    console.log('调用 logoutUser 方法')
    try {
      // 清除状态
      token.value = null
      userInfo.value = null
      isInitialized.value = false
      
      // 清除本地存储
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      
      // 清除 axios 默认请求头中的 token
      delete api.defaults.headers.common['Authorization']
      
      console.log('退出登录成功')
      
      // 重定向到登录页面
      router.push('/auth/login')
    } catch (error) {
      console.error('退出登录失败:', error)
      throw error
    }
  }
  
  async function updateUserInfo(profileData) {
    console.log('调用 updateUserInfo 方法')
    try {
      const response = await api.patch('/user/profile', profileData)
      // 保持原有的过期时间
      const userData = {
        ...response.data,
        exp: userInfo.value?.exp
      }
      userInfo.value = userData
      localStorage.setItem('user', JSON.stringify(userData))
      return response.data
    } catch (error) {
      console.error('updateUserInfo 错误:', error)
      throw error
    }
  }

  async function updateAvatar(formData) {
    console.log('调用 updateAvatar 方法')
    try {
      const response = await api.post('/user/avatar', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      // 保持原有的过期时间
      const userData = {
        ...userInfo.value,
        avatar: response.data.avatar,
        exp: userInfo.value?.exp
      }
      userInfo.value = userData
      localStorage.setItem('user', JSON.stringify(userData))
      return response.data
    } catch (error) {
      console.error('updateAvatar 错误:', error)
      throw error
    }
  }

  async function changePassword(passwordData) {
    console.log('调用 changePassword 方法')
    try {
      const response = await api.put('/user/password', passwordData)
      return response.data
    } catch (error) {
      console.error('changePassword 错误:', error)
      throw error
    }
  }

  // 直接返回所有方法和状态
  return {
    // 状态
    token,
    userInfo,
    isInitialized,
    // getters
    isAuthenticated,
    getUserInfo,
    // actions
    loginUser,
    registerUser,
    logoutUser,
    updateUserInfo,
    updateAvatar,
    changePassword,
    initializeUser,
    validateToken
  }
}) 
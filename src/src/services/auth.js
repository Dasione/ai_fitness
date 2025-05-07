import api from '@/utils/api'

export const register = async (userData) => {
  console.log('开始注册请求，数据:', userData)
  try {
    const response = await api.post('/auth/register', userData)
    console.log('注册请求成功，响应:', response.data)
    return response.data
  } catch (error) {
    console.error('注册请求失败:', error)
    console.error('错误详情:', {
      message: error.message,
      response: error.response,
      request: error.request
    })
    throw error
  }
}

export const login = async (credentials) => {
  console.log('开始登录请求，数据:', credentials)
  try {
    const response = await api.post('/auth/login', credentials)
    console.log('登录请求成功，响应:', response.data)
    return response.data
  } catch (error) {
    console.error('登录请求失败:', error)
    console.error('错误详情:', {
      message: error.message,
      response: error.response,
      request: error.request
    })
    throw error
  }
}

export const logout = async () => {
  console.log('执行登出操作')
  localStorage.removeItem('token')
  localStorage.removeItem('user')
} 
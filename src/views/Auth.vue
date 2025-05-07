<template>
  <div class="auth-container">
    <el-card class="main-card" shadow="hover">
      <div class="main-card-content">
        <div class="logo-section">
          <img src="/uploads/reference/LOGO.jpg" alt="Logo" class="logo">
          <h1>智能哑铃健身分析系统</h1>
        </div>
        
        <div class="cards-container">
          <!-- 左侧功能卡片 -->
          <el-card class="feature-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <h2>系统功能</h2>
              </div>
            </template>
            <div class="feature-list">
              <div class="feature-item">
                <el-icon :size="24" color="#409EFF"><VideoPlay /></el-icon>
                <div class="feature-info">
                  <h3>智能训练指导</h3>
                  <p>提供专业的哑铃训练视频指导</p>
                </div>
              </div>
              <div class="feature-item">
                <el-icon :size="24" color="#67C23A"><Search /></el-icon>
                <div class="feature-info">
                  <h3>动作分析</h3>
                  <p>实时分析训练动作，提供专业建议</p>
                </div>
              </div>
              <div class="feature-item">
                <el-icon :size="24" color="#E6A23C"><DataLine /></el-icon>
                <div class="feature-info">
                  <h3>数据追踪</h3>
                  <p>记录训练数据，追踪训练进度</p>
                </div>
              </div>
              <div class="feature-item">
                <el-icon :size="24" color="#909399"><User /></el-icon>
                <div class="feature-info">
                  <h3>个性化体验</h3>
                  <p>根据个人情况定制训练计划</p>
                </div>
              </div>
            </div>
          </el-card>

          <!-- 右侧认证卡片 -->
          <el-card class="auth-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <h2>{{ isLogin ? '登录' : '注册' }}</h2>
              </div>
            </template>
            <el-form
              ref="formRef"
              :model="formData"
              :rules="rules"
              label-position="top"
              @submit.prevent="handleSubmit"
            >
              <el-form-item label="用户名" prop="username">
                <el-input
                  v-model="formData.username"
                  placeholder="请输入用户名"
                  prefix-icon="User"
                />
              </el-form-item>

              <el-form-item v-if="!isLogin" label="邮箱" prop="email">
                <el-input
                  v-model="formData.email"
                  placeholder="请输入邮箱"
                  prefix-icon="Message"
                />
              </el-form-item>

              <el-form-item label="密码" prop="password">
                <el-input
                  v-model="formData.password"
                  type="password"
                  placeholder="请输入密码"
                  prefix-icon="Lock"
                  show-password
                />
              </el-form-item>

              <el-form-item v-if="!isLogin" label="确认密码" prop="confirmPassword">
                <el-input
                  v-model="formData.confirmPassword"
                  type="password"
                  placeholder="请再次输入密码"
                  prefix-icon="Lock"
                  show-password
                />
              </el-form-item>

              <div class="form-footer">
                <el-button
                  type="primary"
                  native-type="submit"
                  :loading="loading"
                  class="submit-btn"
                >
                  {{ isLogin ? '登录' : '注册' }}
                </el-button>
                <div class="links">
                  <el-button link @click="toggleMode">
                    {{ isLogin ? '没有账号？立即注册' : '已有账号？立即登录' }}
                  </el-button>
                </div>
              </div>
            </el-form>
          </el-card>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/store/modules/user'
import { ElMessage } from 'element-plus'
import { User, Lock, Message, VideoPlay, Search, DataLine } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const formRef = ref(null)
const loading = ref(false)

// 根据路由判断是登录还是注册模式
const isLogin = computed(() => route.path === '/auth/login')

const formData = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

// 验证函数
const validatePass = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请输入密码'))
  } else {
    if (formData.confirmPassword !== '') {
      formRef.value?.validateField('confirmPassword')
    }
    callback()
  }
}

const validatePass2 = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== formData.password) {
    callback(new Error('两次输入密码不一致!'))
  } else {
    callback()
  }
}

const validateEmail = (rule, value, callback) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (value === '') {
    callback(new Error('请输入邮箱'))
  } else if (!emailRegex.test(value)) {
    callback(new Error('请输入有效的邮箱地址'))
  } else {
    callback()
  }
}

// 表单验证规则
const rules = computed(() => ({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在 3 到 50 个字符之间', trigger: 'blur' }
  ],
  email: isLogin.value ? [] : [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { validator: validateEmail, trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 255, message: '密码长度在 6 到 255 个字符之间', trigger: 'blur' }
  ],
  confirmPassword: isLogin.value ? [] : [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validatePass2, trigger: 'blur' }
  ]
}))

// 切换登录/注册模式
const toggleMode = () => {
  const targetPath = isLogin.value ? '/auth/register' : '/auth/login'
  router.push(targetPath)
}

// 处理表单提交
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    loading.value = true
    
    if (isLogin.value) {
      // 登录逻辑
      await userStore.loginUser({
        username: formData.username,
        password: formData.password
      })
      ElMessage.success('登录成功')
      
      // 获取重定向路径，如果没有则跳转到首页
      const redirectPath = route.query.redirect || '/'
      await router.push(redirectPath)
    } else {
      // 注册逻辑
      const { confirmPassword, ...userData } = formData
      await userStore.registerUser(userData)
      ElMessage.success('注册成功')
      router.push('/auth/login')
    }
  } catch (error) {
    console.error('操作失败:', error)
    handleError(error)
  } finally {
    loading.value = false
  }
}

// 错误处理
const handleError = (error) => {
  if (error.response?.data?.message) {
    ElMessage.error(error.response.data.message)
  } else if (error.response?.status === 400) {
    if (isLogin.value) {
      ElMessage.error('用户名或密码不能为空')
    } else {
      if (error.response.data.includes('用户名已存在')) {
        ElMessage.error('用户名已被使用')
      } else if (error.response.data.includes('邮箱已被注册')) {
        ElMessage.error('邮箱已被注册')
      } else {
        ElMessage.error('注册信息有误，请检查后重试')
      }
    }
  } else if (error.response?.status === 401) {
    ElMessage.error('用户名或密码错误')
  } else if (error.response?.status === 500) {
    ElMessage.error('服务器错误，请稍后重试')
  } else {
    ElMessage.error('操作失败，请稍后重试')
  }
}
</script>

<style lang="scss" scoped>
.auth-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: var(--el-bg-color-page);
  padding: 20px;

  .main-card {
    width: 100%;
    max-width: 1200px;
    margin: 0 auto;
    border-radius: 8px;
    transition: all 0.3s ease;

    &:hover {
      transform: translateY(-5px);
      box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
    }

    .main-card-content {
      .logo-section {
        text-align: center;
        margin-bottom: 40px;
        padding: 20px 0;

        .logo {
          width: 180px;
          height: 180px;
          margin-bottom: 16px;
          object-fit: contain;
          border-radius: 8px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          transition: transform 0.3s ease;
          
          &:hover {
            transform: scale(1.05);
          }
        }

        h1 {
          font-size: 28px;
          color: var(--el-text-color-primary);
          margin: 0;
          font-weight: 600;
        }
      }

      .cards-container {
        display: flex;
        gap: 24px;
        flex-wrap: wrap;

        .feature-card,
        .auth-card {
          flex: 1;
          min-width: 300px;
          border-radius: 8px;

          :deep(.el-card__header) {
            padding: 16px 20px;
            border-bottom: 1px solid var(--el-border-color-light);
            background-color: var(--el-bg-color);
            border-radius: 8px 8px 0 0;

            h2 {
              margin: 0;
              font-size: 18px;
              color: var(--el-text-color-primary);
            }
          }
        }

        .feature-card {
          .feature-list {
            .feature-item {
              display: flex;
              align-items: flex-start;
              margin-bottom: 24px;

              &:last-child {
                margin-bottom: 0;
              }

              .el-icon {
                margin-right: 12px;
                margin-top: 4px;
              }

              .feature-info {
                h3 {
                  margin: 0 0 4px;
                  font-size: 16px;
                  color: var(--el-text-color-primary);
                }

                p {
                  margin: 0;
                  font-size: 14px;
                  color: var(--el-text-color-secondary);
                }
              }
            }
          }
        }

        .auth-card {
          .el-form {
            .el-form-item {
              margin-bottom: 20px;

              &:last-child {
                margin-bottom: 0;
              }
            }

            .form-footer {
              margin-top: 24px;
              text-align: center;

              .submit-btn {
                width: 100%;
                margin-bottom: 16px;
              }

              .links {
                .el-button {
                  font-size: 14px;
                }
              }
            }
          }
        }
      }
    }
  }
}

// 响应式布局
@media screen and (max-width: 768px) {
  .auth-container {
    padding: 16px;

    .main-card {
      .main-card-content {
        .logo-section {
          margin-bottom: 24px;

          .logo {
            width: 120px;
            height: 120px;
          }

          h1 {
            font-size: 22px;
          }
        }

        .cards-container {
          gap: 16px;

          .feature-card,
          .auth-card {
            min-width: 100%;
          }
        }
      }
    }
  }
}
</style> 
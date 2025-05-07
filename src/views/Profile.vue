<template>
  <div class="profile-container">
    <el-card class="profile-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>个人信息</span>
          <el-button v-if="!isEditing" type="primary" @click="handleEdit">编辑</el-button>
        </div>
      </template>
      
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        class="profile-form"
      >
        <div class="profile-content">
          <div class="avatar-section">
            <el-avatar :size="100" :src="avatarUrl">
              {{ userInfo.username?.charAt(0) || 'U' }}
            </el-avatar>
            <el-upload
              v-if="isEditing"
              class="avatar-uploader"
              :action="uploadUrl"
              :show-file-list="false"
              :on-success="handleAvatarSuccess"
              :before-upload="beforeAvatarUpload"
              :headers="uploadHeaders"
              name="avatar"
            >
              <el-button size="small" type="primary">更换头像</el-button>
            </el-upload>
          </div>

          <div class="form-section">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="form.username" :disabled="!isEditing" />
            </el-form-item>
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="form.email" disabled />
            </el-form-item>
            
            <el-form-item v-if="isEditing">
              <el-button type="primary" @click="handleSubmit">保存</el-button>
              <el-button @click="handleCancel">取消</el-button>
            </el-form-item>
          </div>
        </div>
      </el-form>
    </el-card>

    <el-card class="password-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>修改密码</span>
        </div>
      </template>
      
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-width="100px"
        class="password-form"
      >
        <el-form-item label="当前密码" prop="currentPassword">
          <el-input v-model="passwordForm.currentPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="passwordForm.newPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="passwordForm.confirmPassword" type="password" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handlePasswordSubmit">修改密码</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useUserStore } from '@/store/modules/user'
import { ElMessage } from 'element-plus'
import { API_BASE_URL, UPLOAD_CONFIG } from '@/config'

// Store
const userStore = useUserStore()
const userInfo = computed(() => userStore.userInfo || {})

// 表单引用
const formRef = ref(null)
const passwordFormRef = ref(null)

// 状态
const isEditing = ref(false)

// 表单数据
const form = reactive({
  username: '',
  email: ''
})

const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 计算属性
const avatarUrl = computed(() => {
  if (!userInfo.value?.avatar) return ''
  return `${API_BASE_URL}${userInfo.value.avatar}`
})

const uploadUrl = computed(() => `${API_BASE_URL}/api/user/avatar`)
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${userStore.token}`
}))

// 表单验证规则
const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ]
}

const validatePass = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请输入新密码'))
  } else if (value === passwordForm.currentPassword) {
    callback(new Error('新密码不能与当前密码相同'))
  } else {
    if (passwordForm.confirmPassword !== '') {
      passwordFormRef.value?.validateField('confirmPassword')
    }
    callback()
  }
}

const validatePass2 = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入新密码'))
  } else if (value !== passwordForm.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  currentPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, validator: validatePass, trigger: 'blur' },
    { min: 6, message: '密码长度不能小于6个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, validator: validatePass2, trigger: 'blur' }
  ]
}

// 监听器
watch(() => userInfo.value, (newValue) => {
  if (newValue) {
    form.username = newValue.username || ''
    form.email = newValue.email || ''
  }
}, { immediate: true })

// 方法
const handleEdit = () => {
  isEditing.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    await userStore.updateUserInfo({
      username: form.username,
      email: form.email
    })
    ElMessage.success('个人信息更新成功')
    // 刷新页面
    window.location.reload()
  } catch (error) {
    console.error('表单验证失败:', error)
    ElMessage.error(error.response?.data?.message || '更新失败，请重试')
  }
}

const handleCancel = () => {
  isEditing.value = false
  Object.assign(form, {
    username: userInfo.value?.username || '',
    email: userInfo.value?.email || ''
  })
}

const beforeAvatarUpload = (file) => {
  const isImage = UPLOAD_CONFIG.allowedTypes.includes(file.type)
  const isLt2M = file.size / 1024 / 1024 < UPLOAD_CONFIG.maxSize

  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }
  if (!isLt2M) {
    ElMessage.error(`图片大小不能超过 ${UPLOAD_CONFIG.maxSize}MB!`)
    return false
  }
  return true
}

const handleAvatarSuccess = (response) => {
  userStore.updateAvatar(response.avatar)
  ElMessage.success('头像上传成功')
}

const handlePasswordSubmit = async () => {
  try {
    await passwordFormRef.value.validate()
    await userStore.changePassword({
      currentPassword: passwordForm.currentPassword,
      newPassword: passwordForm.newPassword
    })
    ElMessage.success('密码修改成功，请重新登录')
    await userStore.logoutUser()
  } catch (error) {
    console.error('密码修改失败:', error)
    ElMessage.error(error.response?.data?.message || '密码修改失败，请重试')
  }
}
</script>

<style lang="scss" scoped>
.profile-container {
  max-width: 800px;
  margin: 20px auto;
  padding: 0 20px;

  .profile-card,
  .password-card {
    margin-bottom: 20px;
    border-radius: 12px;
    transition: all 0.3s ease;
    border: none;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);

    &:hover {
      transform: translateY(-5px);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
    }

    :deep(.el-card__header) {
      padding: 16px 20px;
      border-bottom: 1px solid #ebeef5;
      background-color: #fafafa;
      border-radius: 12px 12px 0 0;
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      span {
        font-size: 16px;
        font-weight: 600;
        color: #303133;
      }
    }
  }

  .profile-content {
    display: flex;
    gap: 40px;

    .avatar-section {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 16px;

      .avatar-uploader {
        text-align: center;
      }
    }

    .form-section {
      flex: 1;
    }
  }

  .password-form {
    max-width: 400px;
  }
}

@media screen and (max-width: 768px) {
  .profile-container {
    padding: 0 16px;

    .profile-content {
      flex-direction: column;
      gap: 24px;
    }
  }
}
</style> 
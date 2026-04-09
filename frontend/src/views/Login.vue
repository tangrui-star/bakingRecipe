<template>
  <div class="login-container">
    <!-- 几何背景 -->
    <div class="geometric-bg"></div>
    
    <!-- 左侧装饰区域 -->
    <div class="left-section">
      <div class="brand-area">
        <div class="logo-wrapper">
          <div class="hexagon-logo"></div>
          <h1 class="brand-title">烘焙配方</h1>
          <p class="brand-subtitle">Baking Recipe System</p>
        </div>
        
        <div class="feature-list">
          <div class="feature-item" v-for="(feature, index) in features" :key="index">
            <div class="feature-icon">{{ feature.icon }}</div>
            <div class="feature-text">{{ feature.text }}</div>
          </div>
        </div>
      </div>
      
      <!-- 装饰性几何图形 -->
      <div class="decoration-shapes">
        <div class="shape shape-1"></div>
        <div class="shape shape-2"></div>
        <div class="shape shape-3"></div>
      </div>
    </div>
    
    <!-- 右侧登录表单 -->
    <div class="right-section">
      <div class="login-card">
        <div class="card-header">
          <h2 class="card-title">欢迎回来</h2>
          <p class="card-subtitle">登录您的账户</p>
        </div>
        
        <el-form :model="loginForm" :rules="rules" ref="loginFormRef" class="login-form">
          <el-form-item prop="username">
            <div class="input-wrapper">
              <el-icon class="input-icon"><User /></el-icon>
              <el-input
                v-model="loginForm.username"
                placeholder="用户名或邮箱"
                size="large"
                class="custom-input"
              />
            </div>
          </el-form-item>
          
          <el-form-item prop="password">
            <div class="input-wrapper">
              <el-icon class="input-icon"><Lock /></el-icon>
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="密码"
                size="large"
                class="custom-input"
                show-password
              />
            </div>
          </el-form-item>
          
          <el-form-item prop="captcha">
            <div class="captcha-wrapper">
              <div class="input-wrapper flex-1">
                <el-icon class="input-icon"><Key /></el-icon>
                <el-input
                  v-model="loginForm.captcha"
                  placeholder="图片验证码（4位数字）"
                  size="large"
                  class="custom-input"
                  maxlength="4"
                />
              </div>
              <div class="captcha-image" @click="refreshCaptcha">
                <img v-if="captchaUrl" :src="captchaUrl" alt="验证码" />
                <div v-else class="captcha-loading">
                  <el-icon class="is-loading"><Loading /></el-icon>
                </div>
              </div>
            </div>
          </el-form-item>
          
          <div class="form-footer">
            <el-checkbox v-model="rememberMe">记住我</el-checkbox>
            <a href="#" class="forgot-link">忘记密码？</a>
          </div>
          
          <el-button
            type="primary"
            size="large"
            class="login-btn"
            :loading="loading"
            @click="handleLogin"
          >
            <span v-if="!loading">登录</span>
            <span v-else>登录中...</span>
          </el-button>
          
          <div class="register-link">
            还没有账户？
            <router-link to="/register" class="link">立即注册</router-link>
          </div>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Key, Loading } from '@element-plus/icons-vue'
import api from '@/api'

const router = useRouter()
const loginFormRef = ref(null)
const loading = ref(false)
const rememberMe = ref(false)
const captchaUrl = ref('')
const captchaId = ref('')

const loginForm = ref({
  username: '',
  password: '',
  captcha: ''
})

const features = [
  { icon: '📝', text: '配方管理' },
  { icon: '🔄', text: '版本控制' },
  { icon: '🧮', text: '智能计算' },
  { icon: '🔥', text: '热量统计' }
]

const rules = {
  username: [
    { required: true, message: '请输入用户名或邮箱', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码长度至少8位', trigger: 'blur' }
  ],
  captcha: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { len: 4, message: '验证码为4位数字', trigger: 'blur' }
  ]
}

const refreshCaptcha = async () => {
  try {
    const response = await fetch('/api/auth/captcha')
    captchaId.value = response.headers.get('X-Captcha-ID')
    const blob = await response.blob()
    captchaUrl.value = URL.createObjectURL(blob)
  } catch (error) {
    ElMessage.error('获取验证码失败')
  }
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      const response = await api.auth.login({
        username_or_email: loginForm.value.username,
        password: loginForm.value.password,
        captcha_id: captchaId.value,
        captcha_code: loginForm.value.captcha
      })
      
      // 保存token
      localStorage.setItem('access_token', response.access_token)
      localStorage.setItem('refresh_token', response.refresh_token)
      localStorage.setItem('user_info', JSON.stringify(response.user))
      
      ElMessage.success('登录成功！')
      router.push('/dashboard')
    } catch (error) {
      // 优先显示后端返回的具体错误信息
      const detail = error.response?.data?.detail
      if (detail) {
        ElMessage.error(detail)
      } else if (error.message) {
        ElMessage.error(error.message)
      } else {
        ElMessage.error('登录失败，请稍后重试')
      }
      refreshCaptcha()
      loginForm.value.captcha = ''
    } finally {
      loading.value = false
    }
  })
}

onMounted(() => {
  refreshCaptcha()
})
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  overflow-x: hidden;
  width: 100%;
  max-width: 100vw;
  position: relative;
}

/* 左侧区域 */
.left-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-2xl);
  position: relative;
  overflow: hidden;
}

.brand-area {
  position: relative;
  z-index: 2;
  text-align: center;
}

.logo-wrapper {
  margin-bottom: var(--spacing-2xl);
}

.hexagon-logo {
  width: 80px;
  height: 46px;
  background: var(--gradient-primary);
  margin: 23px auto;
  position: relative;
  box-shadow: var(--shadow-md);
}

.hexagon-logo::before,
.hexagon-logo::after {
  content: "";
  position: absolute;
  width: 0;
  border-left: 40px solid transparent;
  border-right: 40px solid transparent;
}

.hexagon-logo::before {
  bottom: 100%;
  border-bottom: 23px solid #3b82f6;
}

.hexagon-logo::after {
  top: 100%;
  border-top: 23px solid #8b5cf6;
}

.brand-title {
  font-size: 48px;
  font-weight: 700;
  background: var(--gradient-primary);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: var(--spacing-sm);
}

.brand-subtitle {
  font-size: 16px;
  color: var(--text-secondary);
  letter-spacing: 2px;
  text-transform: uppercase;
}

.feature-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-lg);
  margin-top: var(--spacing-2xl);
}

.feature-item {
  background: var(--bg-card);
  padding: var(--spacing-lg);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  transition: all var(--transition-base);
}

.feature-item:hover {
  border-color: var(--primary-blue);
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
}

.feature-icon {
  font-size: 32px;
  margin-bottom: var(--spacing-sm);
}

.feature-text {
  font-size: 14px;
  color: var(--text-secondary);
}

/* 装饰图形 */
.decoration-shapes {
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  z-index: 1;
  pointer-events: none;
}

.shape {
  position: absolute;
  border: 2px solid var(--primary-blue);
  opacity: 0.15;
}

.shape-1 {
  width: 200px;
  height: 200px;
  top: 10%;
  left: 10%;
  border-radius: 50%;
  animation: float 6s ease-in-out infinite;
}

.shape-2 {
  width: 150px;
  height: 150px;
  bottom: 20%;
  right: 15%;
  transform: rotate(45deg);
  animation: float 8s ease-in-out infinite reverse;
}

.shape-3 {
  width: 100px;
  height: 100px;
  top: 60%;
  left: 20%;
  clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%);
  background: var(--gradient-primary);
  opacity: 0.1;
  animation: float 10s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-20px); }
}

/* 右侧区域 */
.right-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-2xl);
  /* background: var(--bg-secondary); */
}

.login-card {
  width: 100%;
  max-width: 450px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  padding: var(--spacing-2xl);
  box-shadow: var(--shadow-lg);
}

.card-header {
  text-align: center;
  margin-bottom: var(--spacing-2xl);
}

.card-title {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: var(--spacing-sm);
}

.card-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
}

.login-form {
  margin-top: var(--spacing-xl);
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
}

.input-icon {
  position: absolute;
  left: 16px;
  color: var(--text-muted);
  font-size: 18px;
  z-index: 1;
}

.custom-input {
  width: 100%;
}

.custom-input :deep(.el-input__wrapper) {
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  box-shadow: none;
  padding-left: 45px;
  height: var(--input-height);
  width: 100%;
  transition: all var(--transition-base);
}

.custom-input :deep(.el-input__wrapper:hover) {
  border-color: var(--border-focus);
  background: var(--bg-secondary);
}

.custom-input :deep(.el-input__wrapper.is-focus) {
  border-color: var(--border-focus);
  background: var(--bg-secondary);
  box-shadow: var(--shadow-focus);
}

.custom-input :deep(.el-input__inner) {
  color: var(--text-primary);
  font-size: var(--input-font-size);
  /* 防止iOS Safari在字体小于16px时自动缩放页面 */
  font-size: max(16px, var(--input-font-size));
}

.captcha-wrapper {
  display: flex;
  gap: var(--spacing-md);
  width: 100%;
}

.flex-1 {
  flex: 1;
  min-width: 0;
}

.captcha-image {
  width: 120px;
  height: 44px;
  flex-shrink: 0;
  border-radius: var(--radius-md);
  overflow: hidden;
  cursor: pointer;
  border: 1px solid var(--border-color);
  background: var(--bg-input);
  transition: all var(--transition-base);
}

.captcha-image:hover {
  border-color: var(--border-focus);
  box-shadow: var(--shadow-focus);
}

.captcha-image img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.captcha-loading {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
}

.form-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
}

.forgot-link {
  color: var(--primary-blue);
  text-decoration: none;
  font-size: 14px;
  transition: color var(--transition-fast);
}

.forgot-link:hover {
  color: var(--primary-purple);
}

.login-btn {
  width: 100%;
  height: 48px;
  background: var(--gradient-primary);
  border: none;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: var(--spacing-lg);
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.register-link {
  text-align: center;
  font-size: 14px;
  color: var(--text-secondary);
}

.link {
  color: var(--primary-blue);
  text-decoration: none;
  font-weight: 600;
  transition: color var(--transition-fast);
}

.link:hover {
  color: var(--primary-purple);
}

/* 响应式 */
@media (max-width: 1024px) {
  .left-section {
    display: none;
  }
  
  .right-section {
    flex: 1;
  }
}

@media (max-width: 768px) {
  .login-container {
    padding: 0;
    flex-direction: column;
  }
  
  .left-section {
    display: none; /* 移动端隐藏左侧装饰 */
  }
  
  .right-section {
    width: 100%;
    padding: 20px 16px;
    min-height: 100vh;
    display: flex;
    align-items: center;
  }
  
  .login-card {
    padding: 24px 20px;
    width: 100%;
    max-width: 100%;
    box-shadow: none;
    border: none;
    background: transparent;
  }
  
  .brand-title {
    font-size: 28px;
    margin-bottom: 8px;
  }
  
  .brand-subtitle {
    font-size: 13px;
  }
  
  .card-title {
    font-size: 22px;
    margin-bottom: 24px;
  }
  
  .form-item {
    margin-bottom: 16px;
  }
  
  .form-label {
    font-size: 14px;
    margin-bottom: 6px;
  }
  
  .captcha-wrapper {
    flex-direction: column;
    gap: 12px;
  }
  
  .flex-1 {
    width: 100%;
  }
  
  .captcha-image {
    width: 100%;
    height: 50px;
  }
  
  .submit-btn {
    height: 48px;
    font-size: 16px;
    margin-top: 24px;
  }
  
  .register-link {
    margin-top: 20px;
    font-size: 14px;
  }
  
  .feature-list {
    display: none; /* 移动端隐藏特性列表 */
  }
}

</style>

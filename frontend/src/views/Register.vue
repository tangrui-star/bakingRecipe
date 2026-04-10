<template>
  <div class="register-container">
    <div class="geometric-bg"></div>
    
    <div class="register-wrapper">
      <div class="register-card">
        <!-- 头部 -->
        <div class="card-header">
          <router-link to="/login" class="back-btn">
            <el-icon><ArrowLeft /></el-icon>
            返回登录
          </router-link>
          <h2 class="card-title">创建账户</h2>
          <p class="card-subtitle">开始您的烘焙配方管理之旅</p>
        </div>
        
        <!-- 步骤指示器 -->
        <div class="steps-indicator">
          <div
            v-for="(step, index) in steps"
            :key="index"
            class="step-item"
            :class="{ active: currentStep === index, completed: currentStep > index }"
          >
            <div class="step-number">
              <el-icon v-if="currentStep > index"><Check /></el-icon>
              <span v-else>{{ index + 1 }}</span>
            </div>
            <div class="step-label">{{ step }}</div>
          </div>
        </div>

        <!-- 表单内容 -->
        <el-form :model="registerForm" :rules="rules" ref="registerFormRef" class="register-form">
          <!-- 步骤1: 基本信息 -->
          <div v-show="currentStep === 0" class="form-step">
            <el-form-item prop="username">
              <div class="input-wrapper">
                <el-icon class="input-icon"><User /></el-icon>
                <el-input v-model="registerForm.username" placeholder="用户名（3-20位，字母开头）" size="large" class="custom-input" />
              </div>
            </el-form-item>
            <el-form-item prop="email">
              <div class="input-wrapper">
                <el-icon class="input-icon"><Message /></el-icon>
                <el-input v-model="registerForm.email" placeholder="邮箱地址" size="large" class="custom-input" />
              </div>
            </el-form-item>
            <el-form-item prop="password">
              <div class="input-wrapper">
                <el-icon class="input-icon"><Lock /></el-icon>
                <el-input v-model="registerForm.password" type="password" placeholder="密码（8位+大小写+数字）" size="large" class="custom-input" show-password />
              </div>
            </el-form-item>
            <el-form-item prop="confirmPassword">
              <div class="input-wrapper">
                <el-icon class="input-icon"><Lock /></el-icon>
                <el-input v-model="registerForm.confirmPassword" type="password" placeholder="确认密码" size="large" class="custom-input" show-password />
              </div>
            </el-form-item>
          </div>

          <!-- 步骤2: 验证码 + 协议 -->
          <div v-show="currentStep === 1" class="form-step">
            <el-form-item prop="captcha">
              <div class="captcha-wrapper">
                <div class="input-wrapper flex-1">
                  <el-icon class="input-icon"><Key /></el-icon>
                  <el-input v-model="registerForm.captcha" placeholder="图片验证码（4位数字）" size="large" class="custom-input" maxlength="4" />
                </div>
                <div class="captcha-image" @click="refreshCaptcha">
                  <img v-if="captchaUrl" :src="captchaUrl" alt="验证码" />
                  <div v-else class="captcha-loading">
                    <el-icon class="is-loading"><Loading /></el-icon>
                  </div>
                </div>
              </div>
            </el-form-item>

            <el-form-item prop="emailCode">
              <div class="email-code-wrapper">
                <div class="input-wrapper flex-1">
                  <el-icon class="input-icon"><Message /></el-icon>
                  <el-input v-model="registerForm.emailCode" placeholder="邮箱验证码（6位）" size="large" class="custom-input" maxlength="6" />
                </div>
                <el-button class="send-code-btn" :disabled="countdown > 0" :loading="sendingCode" @click="sendEmailCode">
                  {{ countdown > 0 ? `${countdown}秒后重试` : '发送验证码' }}
                </el-button>
              </div>
            </el-form-item>

            <div class="tip-box">
              <el-icon><InfoFilled /></el-icon>
              <span>验证码有效期5分钟，请尽快完成注册。</span>
            </div>

            <el-form-item style="margin-top: 16px;">
              <el-checkbox v-model="agreeTerms">
                我已阅读并同意
                <a href="#" class="link">用户协议</a>
                和
                <a href="#" class="link">隐私政策</a>
              </el-checkbox>
            </el-form-item>
          </div>
        </el-form>

        <!-- 按钮组 -->
        <div class="button-group">
          <el-button v-if="currentStep > 0" size="large" class="prev-btn" @click="prevStep">
            上一步
          </el-button>
          <el-button v-if="currentStep === 0" type="primary" size="large" class="next-btn" @click="nextStep">
            下一步
          </el-button>
          <el-button
            v-if="currentStep === 1"
            type="primary"
            size="large"
            class="submit-btn"
            :loading="loading"
            @click="handleRegister"
          >
            {{ loading ? '注册中...' : '完成注册' }}
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft, User, Message, Lock, Key,
  Check, Loading, InfoFilled
} from '@element-plus/icons-vue'
import api from '@/api'

const router = useRouter()
const registerFormRef = ref(null)
const loading = ref(false)
const sendingCode = ref(false)
const countdown = ref(0)
const captchaUrl = ref('')
const captchaId = ref('')
const currentStep = ref(0)
const agreeTerms = ref(false)

const steps = ['基本信息', '验证码']

const registerForm = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  captcha: '',
  emailCode: '',
  phone: '',
  gender: 'male',
  shopName: ''
})

const validatePassword = (_rule, value, callback) => {
  if (value !== registerForm.value.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度3-20位', trigger: 'blur' },
    { pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/, message: '用户名必须以字母开头，只能包含字母、数字、下划线', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码长度至少8位', trigger: 'blur' },
    { pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$/, message: '密码必须包含大小写字母和数字', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validatePassword, trigger: 'blur' }
  ],
  captcha: [
    { required: true, message: '请输入图片验证码', trigger: 'blur' },
    { len: 4, message: '验证码为4位数字', trigger: 'blur' }
  ],
  emailCode: [
    { required: true, message: '请输入邮箱验证码', trigger: 'blur' },
    { len: 6, message: '验证码为6位', trigger: 'blur' }
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

const sendEmailCode = async () => {
  if (!registerForm.value.email) {
    ElMessage.warning('请先输入邮箱')
    return
  }
  
  if (!registerForm.value.captcha) {
    ElMessage.warning('请先输入图片验证码')
    return
  }
  
  sendingCode.value = true
  try {
    await api.auth.sendEmailCode({
      email: registerForm.value.email,
      captcha_id: captchaId.value,
      captcha_code: registerForm.value.captcha
    })
    
    ElMessage.success('验证码已发送，请查收邮件')
    
    // 开始倒计时
    countdown.value = 60
    const timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) {
        clearInterval(timer)
      }
    }, 1000)
    
    // 不刷新图片验证码，因为图片验证码是用来保护邮箱验证码接口的
    // refreshCaptcha()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '发送失败')
    // 发送失败时才刷新图片验证码
    refreshCaptcha()
    registerForm.value.captcha = ''
  } finally {
    sendingCode.value = false
  }
}

const nextStep = async () => {
  if (!registerFormRef.value) return

  if (currentStep.value === 0) {
    try {
      await registerFormRef.value.validateField(['username', 'email', 'password', 'confirmPassword'])
      currentStep.value++
    } catch (error) {
      // 收集未通过的字段给出汇总提示
      const missing = []
      if (!registerForm.value.username) missing.push('用户名')
      if (!registerForm.value.email) missing.push('邮箱')
      if (!registerForm.value.password) missing.push('密码')
      if (!registerForm.value.confirmPassword) missing.push('确认密码')
      else if (registerForm.value.confirmPassword !== registerForm.value.password) missing.push('两次密码不一致')
      if (missing.length) {
        ElMessage.warning(`请完善以下信息：${missing.join('、')}`)
      }
    }
  }
}

const prevStep = () => {
  currentStep.value--
  // 不刷新验证码，保持验证码ID和图片不变
}

const handleRegister = async () => {
  // 先触发验证码字段校验，显示具体错误
  try {
    await registerFormRef.value.validateField(['captcha', 'emailCode'])
  } catch (error) {
    const missing = []
    if (!registerForm.value.captcha || registerForm.value.captcha.length !== 4) missing.push('图片验证码')
    if (!registerForm.value.emailCode || registerForm.value.emailCode.length !== 6) missing.push('邮箱验证码')
    if (missing.length) {
      ElMessage.warning(`请完善以下信息：${missing.join('、')}`)
    }
    return
  }

  if (!agreeTerms.value) {
    ElMessage.warning('请勾选同意用户协议和隐私政策后再注册')
    return
  }

  loading.value = true
  try {
    const response = await api.auth.register({
      username: registerForm.value.username,
      email: registerForm.value.email,
      password: registerForm.value.password,
      phone: registerForm.value.phone || null,
      gender: registerForm.value.gender,
      shop_name: registerForm.value.shopName || null,
      email_code: registerForm.value.emailCode,
      captcha_id: captchaId.value,
      captcha_code: registerForm.value.captcha
    })
    
    // 保存token
    localStorage.setItem('access_token', response.access_token)
    localStorage.setItem('refresh_token', response.refresh_token)
    localStorage.setItem('user_info', JSON.stringify(response.user))
    
    ElMessage.success('注册成功！')
    
    // 延迟跳转到登录页
    setTimeout(() => {
      router.push('/login')
    }, 1500)
  } catch (error) {
    const errorMsg = error.response?.data?.detail || '注册失败'
    ElMessage.error(errorMsg)
    
    // 如果是验证码错误，提示用户返回第二步重新获取
    if (errorMsg.includes('验证码')) {
      ElMessage.warning('验证码已过期，请返回上一步重新获取')
      // 可选：自动返回第二步
      // currentStep.value = 1
      // refreshCaptcha()
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  refreshCaptcha()
})
</script>

<style scoped>
.register-container {
  min-height: 100vh;
  display: flex;
  overflow-x: hidden;
  width: 100%;
  max-width: 100vw;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-lg);
  position: relative;
}

.register-wrapper {
  width: 100%;
  max-width: 600px;
  position: relative;
  z-index: 2;
}

.register-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  padding: var(--spacing-2xl);
  box-shadow: var(--shadow-lg);
}

.card-header {
  text-align: center;
  margin-bottom: var(--spacing-xl);
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-sm);
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  margin-bottom: var(--spacing-lg);
  transition: color var(--transition-fast);
}

.back-btn:hover {
  color: var(--primary-blue);
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

/* 步骤指示器 */
.steps-indicator {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--spacing-2xl);
  position: relative;
}

.steps-indicator::before {
  content: '';
  position: absolute;
  top: 20px;
  left: 10%;
  right: 10%;
  height: 2px;
  background: var(--border-color);
  z-index: 0;
}

.step-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  z-index: 1;
}

.step-number {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--bg-secondary);
  border: 2px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  margin-bottom: var(--spacing-sm);
  transition: all var(--transition-base);
}

.step-item.active .step-number {
  background: var(--gradient-primary);
  border-color: var(--primary-blue);
  box-shadow: var(--shadow-md);
}

.step-item.completed .step-number {
  background: var(--primary-green);
  border-color: var(--primary-green);
}

.step-label {
  font-size: 12px;
  color: var(--text-muted);
}

.step-item.active .step-label {
  color: var(--primary-blue);
  font-weight: 600;
}

/* 表单样式 */
.form-step {
  min-height: 300px;
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
  font-size: max(16px, var(--input-font-size));
}

.captcha-wrapper,
.email-code-wrapper {
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

.send-code-btn {
  min-width: 120px;
  width: 120px;
  flex-shrink: 0;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
}

.send-code-btn:hover:not(:disabled) {
  border-color: var(--primary-blue);
  color: var(--primary-blue);
}

.tip-box {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: var(--radius-md);
  font-size: 13px;
  color: var(--primary-blue);
  margin-top: var(--spacing-md);
}

.gender-group {
  width: 100%;
  display: flex;
  gap: var(--spacing-lg);
}

.link {
  color: var(--primary-blue);
  text-decoration: none;
}

.link:hover {
  color: var(--primary-purple);
}

/* 按钮组 */
.button-group {
  display: flex;
  gap: var(--spacing-md);
  margin-top: var(--spacing-xl);
}

.prev-btn,
.next-btn,
.submit-btn {
  flex: 1;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
}

.next-btn,
.submit-btn {
  background: var(--gradient-primary);
  border: none;
}

.next-btn:hover,
.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

/* 响应式 */
@media (max-width: 768px) {
  .register-container {
    padding: 0;
  }
  
  .register-card {
    padding: 20px 16px;
    max-width: 100%;
    box-shadow: none;
    border: none;
    min-height: 100vh;
  }
  
  .card-header {
    margin-bottom: 24px;
  }
  
  .card-title {
    font-size: 22px;
  }
  
  .card-subtitle {
    font-size: 13px;
  }
  
  .steps-indicator {
    margin-bottom: 24px;
    padding: 0 8px;
  }
  
  .step-item {
    flex: 1;
  }
  
  .step-number {
    width: 36px;
    height: 36px;
    font-size: 16px;
  }
  
  .step-label {
    font-size: 12px;
    margin-top: 4px;
  }
  
  .step-line {
    top: 18px;
  }
  
  .form-step {
    min-height: auto;
    padding: 0;
  }
  
  .form-item {
    margin-bottom: 16px;
  }
  
  .form-label {
    font-size: 14px;
    margin-bottom: 6px;
  }
  
  .captcha-wrapper,
  .email-code-wrapper {
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
  
  .send-code-btn {
    width: 100%;
    min-width: 100%;
    height: 44px;
  }
  
  .gender-group {
    gap: 12px;
  }
  
  .form-actions {
    margin-top: 24px;
    flex-direction: column-reverse;
    gap: 12px;
  }
  
  .form-actions .el-button {
    width: 100%;
    height: 48px;
    font-size: 16px;
  }
  
  .login-link {
    margin-top: 20px;
    font-size: 14px;
  }
}

</style>

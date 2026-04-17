<template>
  <div class="settings-container">
    <div class="geometric-bg"></div>
    
    <!-- 移动端顶部 -->
    <header class="mobile-header">
      <div class="header-content">
        <el-button size="small" @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <div class="header-title">设置</div>
        <div style="width: 60px"></div>
      </div>
    </header>
    
    <!-- 主要内容 -->
    <div class="settings-content">
      <!-- 修改密码 -->
      <div class="settings-section">
        <div class="section-title">修改密码</div>
        <div class="settings-card">
          <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef">
            <el-form-item prop="oldPassword">
              <el-input 
                v-model="passwordForm.oldPassword" 
                type="password" 
                show-password
                placeholder="请输入当前密码"
              />
            </el-form-item>
            
            <el-form-item prop="newPassword">
              <el-input 
                v-model="passwordForm.newPassword" 
                type="password" 
                show-password
                placeholder="请输入新密码（至少8位，含大小写字母和数字）"
              />
            </el-form-item>
            
            <el-form-item prop="confirmPassword">
              <el-input 
                v-model="passwordForm.confirmPassword" 
                type="password" 
                show-password
                placeholder="请再次输入新密码"
              />
            </el-form-item>
            
            <el-button 
              type="primary" 
              @click="handleChangePassword" 
              :loading="loading"
              style="width: 100%"
            >
              修改密码
            </el-button>
          </el-form>
        </div>
      </div>
      
      <!-- 关于系统 -->
      <div class="settings-section">
        <div class="section-title">关于系统</div>
        <div class="settings-card">
          <div class="info-item">
            <span class="info-label">系统名称</span>
            <span class="info-value">Aitbake</span>
          </div>
          <div class="info-item">
            <span class="info-label">版本号</span>
            <span class="info-value">v2.0.0</span>
          </div>
          <div class="info-item">
            <span class="info-label">更新时间</span>
            <span class="info-value">2026-03-29</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import api from '@/api'

const passwordFormRef = ref(null)
const loading = ref(false)

const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.value.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  oldPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码至少8个字符', trigger: 'blur' },
    { pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$/, message: '密码必须包含大小写字母和数字', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const handleChangePassword = async () => {
  try {
    await passwordFormRef.value.validate()
    loading.value = true
    
    await api.auth.changePassword({
      old_password: passwordForm.value.oldPassword,
      new_password: passwordForm.value.newPassword
    })
    
    ElMessage.success('密码修改成功，请重新登录')
    
    // 清除登录信息并跳转到登录页
    setTimeout(() => {
      localStorage.clear()
      window.location.href = '/login'
    }, 1500)
  } catch (error) {
    if (error !== false) {
      ElMessage.error('密码修改失败')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.settings-container {
  min-height: 100vh;
  background: var(--bg-primary);
  overflow-x: hidden;
  width: 100%;
  max-width: 100vw;
  position: relative;
  padding-bottom: 70px;
}

/* 移动端顶部 */
.mobile-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  height: 48px;
}

.header-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
}

/* 主要内容 */
.settings-content {
  padding: 12px;
  padding-top: 60px;
}

/* 设置区块 */
.settings-section {
  margin-bottom: 16px;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  padding: 0 4px 8px;
}

.settings-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px;
}

/* 信息项 */
.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-color);
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.info-value {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
}

/* 桌面版样式 */
@media (min-width: 769px) {
  .settings-container {
    padding-bottom: 0;
  }

  .mobile-header {
    display: flex;
  }

  .header-content {
    max-width: 600px;
    margin: 0 auto;
    width: 100%;
    padding: 12px 20px;
  }

  .settings-content {
    max-width: 600px;
    margin: 0 auto;
    padding: 20px;
    padding-top: 68px;
  }
}
</style>

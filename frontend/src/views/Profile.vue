<template>
  <div class="profile-container">
    <div class="geometric-bg"></div>
    
    <!-- 移动端顶部 -->
    <header class="mobile-header">
      <div class="header-content">
        <div class="header-title">我的</div>
      </div>
    </header>
    
    <!-- 主要内容 -->
    <div class="profile-content">
      <!-- 用户信息卡片 -->
      <div class="user-card">
        <div class="user-avatar-section">
          <el-avatar :size="64">
            {{ form.username?.charAt(0).toUpperCase() }}
          </el-avatar>
          <div class="user-basic-info">
            <div class="user-name">{{ form.username }}</div>
            <div class="user-email">{{ form.email }}</div>
          </div>
        </div>
      </div>
      
      <!-- 店铺信息 -->
      <div class="info-section">
        <div class="section-title">店铺信息</div>
        <div class="info-card">
          <div class="info-item">
            <span class="info-label">店铺名称</span>
            <span class="info-value">{{ shopName || '未设置' }}</span>
          </div>
        </div>
      </div>
      
      <!-- 个人信息 -->
      <div class="info-section">
        <div class="section-title">个人信息</div>
        <div class="info-card">
          <div class="info-item clickable" @click="showPhoneDialog = true">
            <span class="info-label">手机号</span>
            <div class="info-right">
              <span class="info-value">{{ form.phone || '未设置' }}</span>
              <el-icon><ArrowRight /></el-icon>
            </div>
          </div>
          
          <div class="info-item clickable" @click="showGenderDialog = true">
            <span class="info-label">性别</span>
            <div class="info-right">
              <span class="info-value">{{ genderText }}</span>
              <el-icon><ArrowRight /></el-icon>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 快捷操作 -->
      <div class="info-section">
        <div class="section-title">快捷操作</div>
        <div class="info-card">
          <div class="info-item clickable" @click="$router.push('/settings')">
            <span class="info-label">
              <el-icon><Setting /></el-icon>
              设置
            </span>
            <el-icon><ArrowRight /></el-icon>
          </div>
          
          <div class="info-item clickable" @click="handleLogout">
            <span class="info-label danger">
              <el-icon><SwitchButton /></el-icon>
              退出登录
            </span>
            <el-icon><ArrowRight /></el-icon>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 手机号编辑对话框 -->
    <el-dialog v-model="showPhoneDialog" title="修改手机号" width="90%">
      <el-form :model="form" :rules="rules" ref="phoneFormRef">
        <el-form-item prop="phone">
          <el-input 
            v-model="form.phone" 
            placeholder="请输入手机号"
            maxlength="11"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPhoneDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSavePhone" :loading="loading">
          保存
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 性别选择对话框 -->
    <el-dialog v-model="showGenderDialog" title="选择性别" width="90%">
      <el-radio-group v-model="form.gender" style="width: 100%">
        <div class="gender-option" @click="form.gender = 'male'">
          <el-radio value="male">男</el-radio>
        </div>
        <div class="gender-option" @click="form.gender = 'female'">
          <el-radio value="female">女</el-radio>
        </div>
        <div class="gender-option" @click="form.gender = 'other'">
          <el-radio value="other">其他</el-radio>
        </div>
      </el-radio-group>
      <template #footer>
        <el-button @click="showGenderDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveGender" :loading="loading">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowRight, Setting, SwitchButton } from '@element-plus/icons-vue'
import api from '@/api'

const router = useRouter()
const phoneFormRef = ref(null)
const loading = ref(false)
const shopName = ref('')
const showPhoneDialog = ref(false)
const showGenderDialog = ref(false)

const form = ref({
  username: '',
  email: '',
  phone: '',
  gender: ''
})

const rules = {
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ]
}

const genderText = computed(() => {
  const genderMap = {
    male: '男',
    female: '女',
    other: '其他'
  }
  return genderMap[form.value.gender] || '未设置'
})

onMounted(async () => {
  try {
    const user = await api.auth.getCurrentUser()
    form.value = {
      username: user.username,
      email: user.email,
      phone: user.phone || '',
      gender: user.gender || ''
    }
    
    if (user.shop_id) {
      const shop = await api.shops.get(user.shop_id)
      shopName.value = shop.name
    }
  } catch (error) {
    ElMessage.error('加载用户信息失败')
  }
})

const handleSavePhone = async () => {
  try {
    await phoneFormRef.value.validate()
    loading.value = true
    
    await api.auth.updateUser({
      phone: form.value.phone,
      gender: form.value.gender
    })
    
    // 更新本地存储
    const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}')
    userInfo.phone = form.value.phone
    localStorage.setItem('user_info', JSON.stringify(userInfo))
    
    ElMessage.success('保存成功')
    showPhoneDialog.value = false
  } catch (error) {
    if (error !== false) {
      ElMessage.error('保存失败')
    }
  } finally {
    loading.value = false
  }
}

const handleSaveGender = async () => {
  try {
    loading.value = true
    
    await api.auth.updateUser({
      phone: form.value.phone,
      gender: form.value.gender
    })
    
    // 更新本地存储
    const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}')
    userInfo.gender = form.value.gender
    localStorage.setItem('user_info', JSON.stringify(userInfo))
    
    ElMessage.success('保存成功')
    showGenderDialog.value = false
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    loading.value = false
  }
}

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    localStorage.clear()
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch {
    // 取消操作
  }
}
</script>

<style scoped>
.profile-container {
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
.profile-content {
  padding: 12px;
  padding-top: 60px;
}

/* 用户卡片 */
.user-card {
  background: var(--gradient-primary);
  border-radius: 16px;
  padding: 24px 16px;
  margin-bottom: 16px;
  color: white;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
}

.user-avatar-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-basic-info {
  flex: 1;
}

.user-name {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 6px;
}

.user-email {
  font-size: 13px;
  opacity: 0.9;
}

/* 信息区块 */
.info-section {
  margin-bottom: 16px;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  padding: 0 4px 8px;
}

.info-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-color);
  transition: all 0.3s ease;
}

.info-item:last-child {
  border-bottom: none;
}

.info-item.clickable {
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

.info-item.clickable:active {
  background: var(--bg-hover);
}

.info-label {
  font-size: 15px;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-label .el-icon {
  flex-shrink: 0;
}

.info-label.danger {
  color: var(--danger-color);
}

.info-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-right .el-icon {
  flex-shrink: 0;
}

.info-value {
  font-size: 14px;
  color: var(--text-secondary);
}

/* 性别选项 */
.gender-option {
  padding: 14px;
  border-bottom: 1px solid var(--border-color);
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

.gender-option:last-child {
  border-bottom: none;
}

.gender-option:active {
  background: var(--bg-hover);
}

/* 桌面版样式 */
@media (min-width: 769px) {
  .profile-container {
    padding-bottom: 0;
  }
  
  .mobile-header {
    display: none;
  }
  
  .profile-content {
    max-width: 600px;
    margin: 0 auto;
    padding: 20px;
  }
  
  .user-card {
    padding: 32px 24px;
  }
  
  .info-item:hover {
    background: var(--bg-hover);
  }
}
</style>

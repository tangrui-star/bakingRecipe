<template>
  <div class="admin-dashboard">
    <div class="page-header">
      <div class="header-content">
        <div class="header-title">管理员后台</div>
        <el-button size="small" @click="$router.push('/dashboard')">返回首页</el-button>
      </div>
    </div>

    <div class="content">
      <!-- 统计卡片 -->
      <div v-loading="loading">
        <!-- 用户黑名单统计 -->
        <div class="section-title-bar">全平台用户黑名单</div>
        <div class="stats-grid" style="margin-bottom:16px">
          <div class="stat-card clickable" @click="$router.push('/admin/user-blacklist')">
            <div class="stat-icon" style="background:linear-gradient(135deg,#667eea,#764ba2)">
              <el-icon :size="22"><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.user_blacklist_total }}</div>
              <div class="stat-label">用户黑名单总数</div>
            </div>
          </div>
          <div class="stat-card clickable" @click="$router.push('/admin/user-blacklist?risk_level=HIGH')">
            <div class="stat-icon" style="background:linear-gradient(135deg,#ff6b6b,#ee5a52)">
              <el-icon :size="22"><CircleClose /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.user_blacklist_high }}</div>
              <div class="stat-label">高风险</div>
            </div>
          </div>
          <div class="stat-card clickable" @click="$router.push('/admin/user-blacklist?risk_level=MEDIUM')">
            <div class="stat-icon" style="background:linear-gradient(135deg,#ffa940,#fa8c16)">
              <el-icon :size="22"><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.user_blacklist_medium }}</div>
              <div class="stat-label">中风险</div>
            </div>
          </div>
          <div class="stat-card clickable" @click="$router.push('/admin/user-blacklist?risk_level=LOW')">
            <div class="stat-icon" style="background:linear-gradient(135deg,#43e97b,#38f9d7)">
              <el-icon :size="22"><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.user_blacklist_low }}</div>
              <div class="stat-label">低风险</div>
            </div>
          </div>
        </div>

        <!-- 系统黑名单统计 -->
        <div class="section-title-bar">系统黑名单</div>
        <div class="stats-grid" style="margin-bottom:24px">
          <div class="stat-card clickable" @click="$router.push('/admin/system-blacklist')">
            <div class="stat-icon" style="background:linear-gradient(135deg,#4facfe,#00f2fe)">
              <el-icon :size="22"><DataAnalysis /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.system_blacklist_total }}</div>
              <div class="stat-label">系统黑名单总数</div>
            </div>
          </div>
          <div class="stat-card clickable" @click="$router.push('/admin/system-blacklist?risk_level=HIGH')">
            <div class="stat-icon" style="background:linear-gradient(135deg,#ff6b6b,#ee5a52)">
              <el-icon :size="22"><CircleClose /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.system_blacklist_high }}</div>
              <div class="stat-label">高风险</div>
            </div>
          </div>
          <div class="stat-card clickable" @click="$router.push('/admin/system-blacklist?risk_level=MEDIUM')">
            <div class="stat-icon" style="background:linear-gradient(135deg,#ffa940,#fa8c16)">
              <el-icon :size="22"><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.system_blacklist_medium }}</div>
              <div class="stat-label">中风险</div>
            </div>
          </div>
          <div class="stat-card clickable" @click="$router.push('/admin/system-blacklist?risk_level=LOW')">
            <div class="stat-icon" style="background:linear-gradient(135deg,#43e97b,#38f9d7)">
              <el-icon :size="22"><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.system_blacklist_low }}</div>
              <div class="stat-label">低风险</div>
            </div>
          </div>
        </div>

        <!-- 待审核 -->
        <div class="stats-grid" style="grid-template-columns:1fr;margin-bottom:24px">
          <div class="stat-card">
            <div class="stat-icon" style="background:linear-gradient(135deg,#f093fb,#f5576c)">
              <el-icon :size="22"><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.pending_push_requests }}</div>
              <div class="stat-label">待审核推送申请</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 功能导航 -->
      <div class="nav-section">
        <div class="nav-card" @click="$router.push('/admin/push-requests')">
          <el-icon :size="28"><Document /></el-icon>
          <div class="nav-label">推送申请审核</div>
          <el-tag v-if="stats.pending_push_requests > 0" type="danger" size="small">
            {{ stats.pending_push_requests }} 待审
          </el-tag>
        </div>
        <div class="nav-card" @click="$router.push('/admin/system-blacklist')">
          <el-icon :size="28"><Warning /></el-icon>
          <div class="nav-label">系统黑名单管理</div>
        </div>
        <div class="nav-card" @click="$router.push('/admin/users')">
          <el-icon :size="28"><User /></el-icon>
          <div class="nav-label">用户管理</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Warning, Document, CircleClose, CircleCheck, DataAnalysis, User } from '@element-plus/icons-vue'
import axios from 'axios'

const loading = ref(false)
const stats = ref({
  system_blacklist_total: 0, system_blacklist_high: 0,
  system_blacklist_medium: 0, system_blacklist_low: 0,
  user_blacklist_total: 0, user_blacklist_high: 0,
  user_blacklist_medium: 0, user_blacklist_low: 0,
  pending_push_requests: 0
})

const api = () => {
  const token = localStorage.getItem('access_token')
  return axios.create({ baseURL: '/api', headers: { Authorization: `Bearer ${token}` } })
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await api().get('/admin/statistics')
    stats.value = res.data
  } catch { ElMessage.error('加载统计失败') }
  finally { loading.value = false }
})
</script>

<style scoped>
.admin-dashboard { min-height: 100vh; background: var(--bg-primary); padding-bottom: 40px; }
.page-header {
  position: fixed; top: 0; left: 0; right: 0; z-index: 100;
  background: var(--bg-card); border-bottom: 1px solid var(--border-color);
}
.header-content {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 20px; height: 48px; max-width: 1200px; margin: 0 auto;
}
.header-title { font-size: 17px; font-weight: 600; color: var(--text-primary); }
.content { padding: 20px; padding-top: 68px; max-width: 1200px; margin: 0 auto; }
.stats-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 24px; }
@media (min-width: 768px) { .stats-grid { grid-template-columns: repeat(4, 1fr); } }
.stat-card {
  background: var(--bg-card); border-radius: 12px; padding: 16px;
  display: flex; align-items: center; gap: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,.06);
}
.stat-icon {
  width: 48px; height: 48px; min-width: 48px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center; color: #fff;
}
.stat-value { font-size: 24px; font-weight: 700; color: var(--text-primary); }
.stat-label { font-size: 12px; color: var(--text-secondary); }
.nav-section { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.nav-card {
  background: var(--bg-card); border-radius: 12px; padding: 20px 16px;
  text-align: center; cursor: pointer; transition: all .2s;
  box-shadow: 0 2px 8px rgba(0,0,0,.06); display: flex;
  flex-direction: column; align-items: center; gap: 10px;
}
.nav-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,.1); }
.nav-label { font-size: 14px; font-weight: 500; color: var(--text-primary); }

.section-title-bar {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  padding: 0 4px 8px;
  margin-bottom: 8px;
}

.stat-card.clickable {
  cursor: pointer;
  transition: all .2s;
}

.stat-card.clickable:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,.12);
}
</style>

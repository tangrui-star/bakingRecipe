<template>
  <div class="dashboard-container">
    <!-- 移动端顶部 -->
    <header class="mobile-header">
      <div class="header-content">
        <div class="header-title">烘焙助手</div>
        <el-dropdown trigger="click" @command="handleCommand">
          <div class="user-avatar">
            <el-avatar :size="32">
              {{ userInfo.username?.charAt(0).toUpperCase() }}
            </el-avatar>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">
                <el-icon><User /></el-icon>
                个人资料
              </el-dropdown-item>
              <el-dropdown-item command="settings">
                <el-icon><Setting /></el-icon>
                设置
              </el-dropdown-item>
              <el-dropdown-item divided command="logout">
                <el-icon><SwitchButton /></el-icon>
                退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>
    
    <!-- 主要内容区 -->
    <div class="dashboard-content">
      <!-- 欢迎卡片 -->
      <div class="welcome-card">
        <div class="welcome-content">
          <h1 class="welcome-title">
            {{ greeting }}，{{ userInfo.username }}
          </h1>
          <p class="welcome-subtitle">
            今天也要加油哦 🎉
          </p>
        </div>
      </div>
      
      <!-- 功能工具区 -->
      <div class="tools-section">
        <div class="section-header">
          <h2 class="section-title">功能工具</h2>
        </div>
        <div class="tools-grid">
          <div
            v-for="(tool, index) in tools"
            :key="index"
            class="tool-card"
            @click="handleToolClick(tool.action)"
          >
            <div class="tool-icon" :style="{ background: tool.gradient }">
              <el-icon :size="28">
                <component :is="tool.icon" />
              </el-icon>
            </div>
            <div class="tool-content">
              <div class="tool-label">{{ tool.label }}</div>
              <div class="tool-desc">{{ tool.desc }}</div>
            </div>
            <el-icon class="tool-arrow"><ArrowRight /></el-icon>
          </div>
        </div>
      </div>

      <!-- 数据维护区 -->
      <div class="maintenance-section">
        <div class="section-header">
          <h2 class="section-title">数据维护</h2>
        </div>
        <div class="maintenance-grid">
          <div
            v-for="(item, index) in maintenanceItems"
            :key="index"
            class="maintenance-card"
            @click="handleMaintenanceClick(item.action)"
          >
            <div class="maintenance-icon">
              <el-icon :size="24">
                <component :is="item.icon" />
              </el-icon>
            </div>
            <div class="maintenance-label">{{ item.label }}</div>
            <div class="maintenance-count">{{ item.count }}</div>
          </div>
        </div>
      </div>
      
      <!-- 数据统计卡片 -->
      <div class="stats-section">
        <div class="section-header">
          <h2 class="section-title">数据概览</h2>
        </div>
        <div class="stats-grid">
          <div
            v-for="(stat, index) in stats"
            :key="index"
            class="stat-card"
          >
            <div class="stat-icon" :style="{ background: stat.gradient }">
              <el-icon :size="20">
                <component :is="stat.icon" />
              </el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-label">{{ stat.label }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, markRaw } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User, Setting, SwitchButton, ArrowRight,
  DataAnalysis, Document, TrendCharts, Shop,
  Operation, Warning, Dish, Box
} from '@element-plus/icons-vue'
import api from '@/api'

const router = useRouter()
const userInfo = ref(JSON.parse(localStorage.getItem('user_info') || '{}'))

// 功能工具
const tools = ref([
  {
    icon: markRaw(Operation),
    label: '配方计算',
    desc: '快速计算配方用量',
    action: 'calculator',
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
  },
  {
    icon: markRaw(Warning),
    label: '订单检查',
    desc: '检查订单黑名单',
    action: 'screening',
    gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
  },
  {
    icon: markRaw(Box),
    label: '订单处理',
    desc: '备料计算、备注提取、打印单号',
    action: 'order-process',
    gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'
  },
  {
    icon: markRaw(TrendCharts),
    label: '中通快递',
    desc: '上传物流Excel生成快递表',
    action: 'logistics-process',
    gradient: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)'
  }
])

// 数据维护
const maintenanceItems = ref([
  {
    icon: markRaw(Dish),
    label: '配方管理',
    action: 'recipes',
    count: '0'
  },
  {
    icon: markRaw(Warning),
    label: '黑名单',
    action: 'blacklist',
    count: '0'
  }
])

// 数据统计
const stats = ref([
  {
    icon: markRaw(Document),
    label: '配方总数',
    value: '0',
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
  },
  {
    icon: markRaw(TrendCharts),
    label: '本月新增',
    value: '0',
    gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
  },
  {
    icon: markRaw(DataAnalysis),
    label: '品类数',
    value: '0',
    gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'
  },
  {
    icon: markRaw(Shop),
    label: '原料数',
    value: '0',
    gradient: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)'
  }
])

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 9) return '早上好'
  if (hour < 12) return '上午好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

// 加载统计数据
const loadStats = async () => {
  try {
    if (!userInfo.value.shop_id) return
    const shopId = userInfo.value.shop_id
    const token = localStorage.getItem('access_token')

    // 并发请求所有数据
    const [recipesRes, categoriesRes, ingredientsRes, blacklistRes] = await Promise.allSettled([
      api.recipes.list(shopId),
      api.categories.list(),
      api.ingredients.list(),
      fetch(`/api/blacklist?shop_id=${shopId}&page=1&page_size=1`, {
        headers: { 'Authorization': `Bearer ${token}` }
      }).then(r => r.json())
    ])

    // 配方数量
    if (recipesRes.status === 'fulfilled') {
      const recipes = recipesRes.value
      const count = Array.isArray(recipes) ? recipes.length : 0
      stats.value[0].value = count.toString()
      maintenanceItems.value[0].count = count.toString()

      // 本月新增
      const thisMonth = (Array.isArray(recipes) ? recipes : []).filter(r => {
        const created = new Date(r.created_at)
        const now = new Date()
        return created.getMonth() === now.getMonth() && created.getFullYear() === now.getFullYear()
      })
      stats.value[1].value = thisMonth.length.toString()
    }

    // 品类数量
    if (categoriesRes.status === 'fulfilled') {
      const cats = categoriesRes.value
      stats.value[2].value = (Array.isArray(cats) ? cats.length : 0).toString()
    }

    // 原料数量
    if (ingredientsRes.status === 'fulfilled') {
      const ings = ingredientsRes.value
      stats.value[3].value = (Array.isArray(ings) ? ings.length : 0).toString()
    }

    // 黑名单数量
    if (blacklistRes.status === 'fulfilled') {
      const bl = blacklistRes.value
      const blCount = bl?.total ?? 0
      maintenanceItems.value[1].count = blCount.toString()
    }

  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const handleCommand = (command) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      handleLogout()
      break
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

const handleToolClick = (action) => {
  switch (action) {
    case 'calculator':
      router.push('/calculator')
      break
    case 'screening':
      router.push('/screening')
      break
    case 'order-process':
      router.push('/order-process')
      break
    case 'logistics-process':
      router.push('/logistics-process')
      break
  }
}

const handleMaintenanceClick = (action) => {
  switch (action) {
    case 'recipes':
      router.push('/recipes')
      break
    case 'blacklist':
      router.push('/blacklist')
      break
  }
}

onMounted(async () => {
  await loadStats()
})
</script>

<style scoped>
.dashboard-container {
  min-height: 100vh;
  background: #f7f8fa;
  padding-bottom: 70px;
}

/* 移动端顶部 */
.mobile-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  backdrop-filter: blur(10px);
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
  color: #303133;
}

.user-avatar {
  cursor: pointer;
}

/* 主要内容区 */
.dashboard-content {
  padding: 12px;
}

/* 欢迎卡片 */
.welcome-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 24px 20px;
  margin-bottom: 16px;
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.welcome-title {
  font-size: 22px;
  font-weight: 600;
  margin-bottom: 6px;
}

.welcome-subtitle {
  font-size: 14px;
  opacity: 0.9;
}

/* 功能工具区 */
.tools-section {
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 0 4px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.tools-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tool-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 14px;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.tool-card:active {
  transform: scale(0.98);
}

.tool-icon {
  width: 52px;
  height: 52px;
  min-width: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.tool-content {
  flex: 1;
  min-width: 0;
}

.tool-label {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.tool-desc {
  font-size: 13px;
  color: #909399;
}

.tool-arrow {
  color: #c0c4cc;
  font-size: 16px;
}

/* 数据维护区 */
.maintenance-section {
  margin-bottom: 20px;
}

.maintenance-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.maintenance-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px 16px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.maintenance-card:active {
  transform: scale(0.95);
}

.maintenance-icon {
  width: 48px;
  height: 48px;
  margin: 0 auto 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.maintenance-label {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 6px;
}

.maintenance-count {
  font-size: 20px;
  font-weight: 600;
  color: #667eea;
}

/* 数据统计 */
.stats-section {
  margin-bottom: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px 12px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.stat-icon {
  width: 44px;
  height: 44px;
  min-width: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-content {
  flex: 1;
  min-width: 0;
}

.stat-value {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 2px;
  color: #303133;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}
</style>

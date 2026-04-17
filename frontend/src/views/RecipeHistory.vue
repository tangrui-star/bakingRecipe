<template>
  <div class="history-container">
    <div class="geometric-bg"></div>
    
    <!-- 移动端顶部 -->
    <header class="mobile-header">
      <div class="header-content">
        <el-button size="small" @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <div class="header-title">历史版本</div>
        <div style="width: 60px"></div>
      </div>
    </header>
    
    <!-- 主要内容 -->
    <div class="history-content">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-container">
        <el-icon class="is-loading" :size="40"><Loading /></el-icon>
        <p>加载历史版本中...</p>
      </div>
      
      <div v-else-if="!recipeId" class="empty-state">
        <el-icon :size="60"><Document /></el-icon>
        <p>未指定配方ID</p>
        <el-button @click="$router.back()">返回</el-button>
      </div>
      
      <div v-else>
        <!-- 配方信息卡片 -->
        <div class="info-card">
          <div class="recipe-title">{{ recipeName }}</div>
          <div class="recipe-meta">
            <el-tag type="info">共 {{ versions.length }} 个版本</el-tag>
            <el-tag type="success">当前 v{{ currentVersion }}</el-tag>
          </div>
        </div>
        
        <!-- 版本列表 -->
        <div class="versions-list">
          <div
            v-for="version in versions"
            :key="version.id"
            class="version-card"
            :class="{ latest: version.version === currentVersion }"
            @click="viewVersion(version)"
          >
            <div class="version-header">
              <div class="version-number">
                v{{ version.version }}
                <el-tag v-if="version.version === currentVersion" type="success" size="small">
                  当前
                </el-tag>
              </div>
              <div class="version-time">{{ formatDate(version.created_at) }}</div>
            </div>
            
            <div class="version-name">{{ version.name }}</div>
            
            <div class="version-meta">
              <span class="meta-item">
                <el-icon><Box /></el-icon>
                数量 {{ version.base_quantity }}
              </span>
              <span class="meta-item">
                <el-icon><ScaleToOriginal /></el-icon>
                重量 {{ version.base_weight }}g
              </span>
              <span class="meta-item">
                <el-icon><Dish /></el-icon>
                {{ version.ingredients?.length || 0 }} 种原料
              </span>
            </div>
            
            <div v-if="version.notes" class="version-notes">
              <el-icon><Document /></el-icon>
              {{ version.notes }}
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 版本详情对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="`v${selectedVersion?.version} - ${selectedVersion?.name}`"
      width="95%"
      style="max-width: 640px; margin: auto;"
      :show-close="true"
      align-center
    >
      <div v-if="selectedVersion" class="version-detail">
        <!-- 基本信息 -->
        <div class="detail-section">
          <h3 class="section-title">基本信息</h3>
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">版本号</span>
              <span class="info-value">{{ selectedVersion.version }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">配方名称</span>
              <span class="info-value">{{ selectedVersion.name }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">基础数量</span>
              <span class="info-value">{{ selectedVersion.base_quantity }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">基础重量</span>
              <span class="info-value">{{ selectedVersion.base_weight }}g</span>
            </div>
            <div class="info-item">
              <span class="info-label">总热量</span>
              <span class="info-value">{{ selectedVersion.total_calories }} kcal</span>
            </div>
            <div class="info-item">
              <span class="info-label">创建时间</span>
              <span class="info-value">{{ formatDate(selectedVersion.created_at) }}</span>
            </div>
          </div>
          
          <div v-if="selectedVersion.calculation_rule" class="info-note">
            <span class="note-label">计算规则：</span>
            <span class="note-text">{{ selectedVersion.calculation_rule }}</span>
          </div>
          
          <div v-if="selectedVersion.notes" class="info-note">
            <span class="note-label">备注：</span>
            <span class="note-text">{{ selectedVersion.notes }}</span>
          </div>
        </div>
        
        <!-- 原料列表 -->
        <div class="detail-section">
          <h3 class="section-title">原料配方</h3>
          <div class="ingredients-list">
            <div
              v-for="(item, index) in selectedVersion.ingredients"
              :key="index"
              class="ingredient-item"
            >
              <div class="ingredient-header">
                <span class="ingredient-number">{{ index + 1 }}</span>
                <span class="ingredient-name">{{ item.ingredient?.name || '未知原料' }}</span>
              </div>
              <div class="ingredient-details">
                <span class="detail-item">用量：{{ item.weight }}g</span>
                <span class="detail-item">热量：{{ calculateCalories(item) }} kcal</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 制作步骤 -->
        <div v-if="selectedVersion.steps && selectedVersion.steps.length > 0" class="detail-section">
          <h3 class="section-title">制作步骤</h3>
          <div class="steps-list">
            <div v-for="step in selectedVersion.steps" :key="step.id" class="step-item">
              <div class="step-number">步骤 {{ step.step_number }}</div>
              <div class="step-content">
                <p class="step-description">{{ step.description }}</p>
                <div v-if="step.duration_minutes || step.temperature" class="step-meta">
                  <span v-if="step.duration_minutes" class="meta-tag">
                    <el-icon><Timer /></el-icon>
                    {{ step.duration_minutes }} 分钟
                  </span>
                  <span v-if="step.temperature" class="meta-tag">
                    <el-icon><Sunny /></el-icon>
                    {{ step.temperature }} ℃
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">关闭</el-button>
          <el-button type="primary" @click="useVersion(selectedVersion)">
            基于此版本创建
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft, Loading, Box, ScaleToOriginal, Dish, Document,
  Timer, Sunny
} from '@element-plus/icons-vue'
import api from '@/api'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const recipeId = ref('')
const recipeName = ref('')
const currentVersion = ref(1)
const versions = ref([])
const dialogVisible = ref(false)
const selectedVersion = ref(null)

const isMobile = computed(() => window.innerWidth <= 768)

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '未知时间'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 计算单个原料热量
const calculateCalories = (ingredient) => {
  if (!ingredient.ingredient?.calories_per_100g || !ingredient.weight) {
    return 0
  }
  return (ingredient.ingredient.calories_per_100g * ingredient.weight / 100).toFixed(2)
}

// 加载配方历史
const loadHistory = async () => {
  loading.value = true
  try {
    // 获取配方基本信息
    const recipeData = await api.recipes.get(recipeId.value)
    recipeName.value = recipeData.current_name
    currentVersion.value = recipeData.current_version
    
    // 获取所有版本
    const versionsData = await api.recipes.versions(recipeId.value)
    versions.value = versionsData
    
    if (versions.value.length === 0) {
      ElMessage.warning('该配方暂无历史版本')
    }
  } catch (error) {
    ElMessage.error('加载历史版本失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 查看版本详情
const viewVersion = (version) => {
  selectedVersion.value = version
  dialogVisible.value = true
}

// 基于版本创建新配方
const useVersion = (version) => {
  ElMessage.info('功能开发中：将基于此版本创建新配方')
  // TODO: 跳转到编辑页面，预填充数据
}

// 初始化
onMounted(() => {
  recipeId.value = route.params.id
  if (recipeId.value) {
    loadHistory()
  }
})
</script>

<style scoped>
.history-container {
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
.history-content {
  padding: 12px;
  padding-top: 60px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  gap: 16px;
  color: var(--text-secondary);
}

.loading-container p {
  font-size: 14px;
  margin: 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--text-secondary);
  gap: 16px;
}

.empty-state p {
  font-size: 14px;
  margin: 0;
}

/* 配方信息卡片 */
.info-card {
  background: var(--gradient-primary);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
  color: white;
}

.recipe-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 10px;
}

.recipe-meta {
  display: flex;
  gap: 8px;
}

/* 版本列表 */
.versions-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.version-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
  -webkit-tap-highlight-color: transparent;
}

.version-card:active {
  transform: scale(0.98);
  background: var(--bg-hover);
}

.version-card.latest {
  border-color: var(--primary-green);
  background: linear-gradient(135deg, rgba(67, 233, 123, 0.05) 0%, rgba(56, 249, 215, 0.05) 100%);
}

.version-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.version-number {
  font-size: 16px;
  font-weight: 600;
  color: var(--primary-blue);
  display: flex;
  align-items: center;
  gap: 8px;
}

.version-time {
  font-size: 12px;
  color: var(--text-muted);
}

.version-name {
  font-size: 15px;
  font-weight: 500;
  margin-bottom: 10px;
  color: var(--text-primary);
}

.version-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.meta-item .el-icon {
  flex-shrink: 0;
}

.version-notes {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 10px;
  background: var(--bg-primary);
  border-radius: 8px;
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 8px;
}

/* 版本详情 */
.version-detail {
  max-height: 60vh;
  overflow-y: auto;
  padding-right: 4px;
}

.detail-section {
  margin-bottom: 20px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--primary-blue);
}

/* 信息网格 */
.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 12px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px;
  background: var(--bg-primary);
  border-radius: 8px;
}

.info-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.info-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.info-note {
  padding: 10px;
  background: var(--bg-primary);
  border-radius: 8px;
  margin-bottom: 8px;
  font-size: 13px;
}

.info-note:last-child {
  margin-bottom: 0;
}

.note-label {
  color: var(--text-secondary);
  margin-right: 6px;
}

.note-text {
  color: var(--text-primary);
}

/* 原料列表 */
.ingredients-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ingredient-item {
  padding: 12px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

.ingredient-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.ingredient-number {
  width: 24px;
  height: 24px;
  min-width: 24px;
  min-height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--gradient-primary);
  color: white;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.ingredient-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.ingredient-details {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--text-secondary);
}

.detail-item {
  display: flex;
  align-items: center;
}

/* 步骤列表 */
.steps-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.step-item {
  padding: 12px;
  background: var(--bg-primary);
  border-radius: 8px;
}

.step-number {
  font-weight: 600;
  color: var(--primary-blue);
  margin-bottom: 8px;
  font-size: 13px;
}

.step-description {
  margin: 0 0 8px 0;
  line-height: 1.6;
  font-size: 14px;
}

.step-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.meta-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 12px;
  color: var(--text-secondary);
}

/* 对话框底部 */
.dialog-footer {
  display: flex;
  gap: 12px;
}

.dialog-footer .el-button {
  flex: 1;
}

/* 桌面版样式 */
@media (min-width: 769px) {
  .history-container {
    padding-bottom: 0;
  }

  .mobile-header {
    display: flex;
  }

  .header-content {
    max-width: 800px;
    margin: 0 auto;
    width: 100%;
    padding: 12px 20px;
  }

  .history-content {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    padding-top: 68px;
  }
  
  .versions-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 16px;
  }
  
  .version-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
}
</style>

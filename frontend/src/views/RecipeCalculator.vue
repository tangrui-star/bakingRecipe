<template>
  <div class="calculator-container">
    <div class="geometric-bg"></div>
    
    <!-- 移动端顶部 -->
    <header class="mobile-header">
      <div class="header-content">
        <div class="header-title">配方计算</div>
        <el-button 
          v-if="selectedRecipe" 
          size="small" 
          @click="handleExport"
        >
          <el-icon><Download /></el-icon>
          导出
        </el-button>
      </div>
    </header>
    
    <!-- 主要内容 -->
    <div class="calculator-content">
      <!-- 配方选择 -->
      <div v-if="!selectedRecipe" class="recipe-selector">
        <div class="selector-header">
          <h2>选择配方</h2>
        </div>
        
        <!-- 搜索和筛选 -->
        <div class="search-bar">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索配方名称"
            :prefix-icon="Search"
            clearable
          />
        </div>
        
        <div class="filter-bar">
          <el-select
            v-model="selectedCategory"
            placeholder="全部品类"
            clearable
            style="width: 100%"
          >
            <el-option label="全部品类" value="" />
            <el-option
              v-for="category in categories"
              :key="category.id"
              :label="category.name"
              :value="category.id"
            />
          </el-select>
        </div>
        
        <!-- 配方列表 -->
        <div class="recipe-list">
          <div
            v-for="recipe in filteredRecipes"
            :key="recipe.id"
            class="recipe-item"
            @click="selectRecipe(recipe)"
          >
            <div class="recipe-info">
              <div class="recipe-name">{{ recipe.current_name }}</div>
              <div class="recipe-meta">
                <span class="meta-tag">{{ getCategoryName(recipe.category_id) }}</span>
              </div>
            </div>
            <el-icon class="recipe-arrow"><ArrowRight /></el-icon>
          </div>
          
          <div v-if="filteredRecipes.length === 0" class="empty-state">
            <el-icon :size="60"><Operation /></el-icon>
            <p>没有找到配方</p>
          </div>
        </div>
      </div>
      
      <!-- 计算器面板 -->
      <div v-else class="calculator-panel">
        <!-- 配方信息卡片 -->
        <div class="info-card">
          <div class="card-header">
            <div class="card-title-row">
              <el-button size="small" @click="selectedRecipe = null">
                <el-icon><ArrowLeft /></el-icon>
                返回
              </el-button>
              <h2 class="card-title">{{ selectedRecipe.current_name }}</h2>
            </div>
          </div>
          
          <div class="card-body">
            <div class="info-grid">
              <div class="info-item">
                <span class="info-label">基础数量</span>
                <span class="info-value">{{ recipeDetail.base_quantity }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">基础重量</span>
                <span class="info-value">{{ recipeDetail.base_weight }}g</span>
              </div>
            </div>
            
            <div v-if="recipeDetail.calculation_rule" class="info-note">
              <span class="note-label">计算规则：</span>
              <span class="note-text">{{ recipeDetail.calculation_rule }}</span>
            </div>
            
            <div v-if="recipeDetail.notes" class="info-note">
              <span class="note-label">备注：</span>
              <span class="note-text">{{ recipeDetail.notes }}</span>
            </div>
          </div>
        </div>
        
        <!-- 目标数量输入 -->
        <div class="input-card">
          <div class="card-header">
            <h2 class="card-title">目标数量</h2>
          </div>
          
          <div class="card-body">
            <el-input-number
              v-model="targetQuantity"
              :min="1"
              :max="10000"
              :step="1"
              size="large"
              style="width: 100%"
              @change="calculate"
            />
            <div class="ratio-display">
              比例：{{ targetQuantity }} ÷ {{ recipeDetail.base_quantity }} = {{ ratio.toFixed(2) }}
            </div>
          </div>
        </div>
        
        <!-- 原料用量表 -->
        <div class="result-card">
          <div class="card-header">
            <h2 class="card-title">原料用量</h2>
          </div>
          
          <div class="card-body">
            <div class="ingredients-list">
              <div
                v-for="(item, index) in calculatedIngredients"
                :key="index"
                class="ingredient-item"
              >
                <div class="ingredient-header">
                  <span class="ingredient-number">{{ index + 1 }}</span>
                  <span class="ingredient-name">{{ item.name }}</span>
                </div>
                <div class="ingredient-weights">
                  <div class="weight-item">
                    <span class="weight-label">基础</span>
                    <span class="weight-value">{{ item.baseWeight }}g</span>
                  </div>
                  <el-icon class="arrow-icon"><ArrowRight /></el-icon>
                  <div class="weight-item highlight">
                    <span class="weight-label">计算</span>
                    <span class="weight-value">{{ item.calculatedWeight }}g</span>
                  </div>
                </div>
                <div class="ingredient-calories">
                  热量：{{ item.calories }} kcal
                </div>
              </div>
            </div>
            
            <!-- 汇总信息 -->
            <div class="summary-card">
              <div class="summary-item">
                <span class="summary-label">原料总数</span>
                <span class="summary-value">{{ calculatedIngredients.length }} 种</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">总重量</span>
                <span class="summary-value">{{ totalWeight }}g</span>
              </div>
              <div class="summary-item highlight">
                <span class="summary-label">总热量</span>
                <span class="summary-value">{{ totalCalories }} kcal</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowLeft, ArrowRight, Search, Operation, Download } from '@element-plus/icons-vue'
import api from '@/api'

// 数据
const searchKeyword = ref('')
const selectedCategory = ref('')
const categories = ref([])
const recipes = ref([])
const selectedRecipe = ref(null)
const recipeDetail = ref({})
const targetQuantity = ref(1)
const calculatedIngredients = ref([])

// 加载品类列表
const loadCategories = async () => {
  try {
    const data = await api.categories.list()
    categories.value = data
  } catch (error) {
    ElMessage.error('加载品类列表失败')
  }
}

// 加载配方列表
const loadRecipes = async () => {
  try {
    const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}')
    const shopId = userInfo.shop_id
    
    if (!shopId) {
      ElMessage.error('未找到店铺信息')
      return
    }
    
    const data = await api.recipes.list(shopId)
    recipes.value = data
  } catch (error) {
    ElMessage.error('加载配方列表失败')
  }
}

// 获取品类名称
const getCategoryName = (categoryId) => {
  const category = categories.value.find(c => c.id === categoryId)
  return category ? category.name : '未分类'
}

// 筛选配方
const filteredRecipes = computed(() => {
  let result = recipes.value
  
  // 品类筛选
  if (selectedCategory.value) {
    result = result.filter(r => r.category_id === selectedCategory.value)
  }
  
  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(r => 
      r.current_name.toLowerCase().includes(keyword)
    )
  }
  
  return result
})

// 选择配方
const selectRecipe = async (recipe) => {
  selectedRecipe.value = recipe
  
  try {
    const data = await api.recipes.get(recipe.id)
    
    // 获取最新版本
    if (data.versions && data.versions.length > 0) {
      const latestVersion = data.versions[data.versions.length - 1]
      recipeDetail.value = latestVersion
      targetQuantity.value = latestVersion.base_quantity || 1
      calculate()
    }
  } catch (error) {
    ElMessage.error('加载配方详情失败')
  }
}

// 计算比例
const ratio = computed(() => {
  if (!recipeDetail.value.base_quantity) return 1
  return targetQuantity.value / recipeDetail.value.base_quantity
})

// 计算原料用量
const calculate = () => {
  if (!recipeDetail.value.ingredients) {
    calculatedIngredients.value = []
    return
  }
  
  calculatedIngredients.value = recipeDetail.value.ingredients.map(item => {
    const baseWeight = parseFloat(item.weight)
    const calculatedWeight = (baseWeight * ratio.value).toFixed(1)
    const ingredient = item.ingredient
    
    // 计算热量
    let calories = 0
    if (ingredient.calories_per_100g) {
      calories = (ingredient.calories_per_100g * calculatedWeight / 100).toFixed(2)
    }
    
    return {
      name: ingredient.name,
      baseWeight: baseWeight.toFixed(1),
      calculatedWeight,
      calories
    }
  })
}

// 总重量
const totalWeight = computed(() => {
  return calculatedIngredients.value
    .reduce((sum, item) => sum + parseFloat(item.calculatedWeight), 0)
    .toFixed(0)
})

// 总热量
const totalCalories = computed(() => {
  return calculatedIngredients.value
    .reduce((sum, item) => sum + parseFloat(item.calories), 0)
    .toFixed(2)
})

// 导出
const handleExport = () => {
  ElMessage.info('导出功能开发中...')
}

// 初始化
onMounted(async () => {
  await Promise.all([
    loadCategories(),
    loadRecipes()
  ])
})
</script>

<style scoped>
.calculator-container {
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
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
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
  color: var(--text-primary);
}

/* 主要内容 */
.calculator-content {
  padding: 12px;
}

/* 配方选择器 */
.recipe-selector {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
}

.selector-header {
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
}

.selector-header h2 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

.search-bar {
  padding: 12px 16px 0;
}

.filter-bar {
  padding: 12px 16px;
}

.recipe-list {
  max-height: calc(100vh - 280px);
  overflow-y: auto;
}

.recipe-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-top: 1px solid var(--border-color);
  cursor: pointer;
  transition: all 0.3s ease;
  -webkit-tap-highlight-color: transparent;
}

.recipe-item:active {
  background: var(--bg-hover);
}

.recipe-info {
  flex: 1;
}

.recipe-name {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 6px;
  color: var(--text-primary);
}

.recipe-meta {
  display: flex;
  gap: 8px;
}

.meta-tag {
  font-size: 12px;
  padding: 2px 8px;
  background: var(--bg-primary);
  border-radius: 4px;
  color: var(--text-secondary);
}

.recipe-arrow {
  font-size: 18px;
  color: var(--text-muted);
  flex-shrink: 0;
  min-width: 18px;
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

/* 计算器面板 */
.calculator-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 卡片样式 */
.info-card,
.input-card,
.result-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
}

.card-header {
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-secondary);
}

.card-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  flex: 1;
}

.card-body {
  padding: 16px;
}

/* 信息网格 */
.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 12px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  background: var(--bg-primary);
  border-radius: 8px;
}

.info-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.info-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.info-note {
  padding: 12px;
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
  margin-right: 8px;
}

.note-text {
  color: var(--text-primary);
}

/* 比例显示 */
.ratio-display {
  margin-top: 12px;
  padding: 12px;
  background: var(--gradient-primary);
  border-radius: 8px;
  text-align: center;
  color: white;
  font-size: 14px;
  font-weight: 500;
}

/* 原料列表 */
.ingredients-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.ingredient-item {
  padding: 14px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

.ingredient-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
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
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.ingredient-weights {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.weight-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px;
  background: var(--bg-card);
  border-radius: 6px;
}

.weight-item.highlight {
  background: var(--gradient-primary);
  color: white;
}

.weight-label {
  font-size: 11px;
  color: var(--text-muted);
}

.weight-item.highlight .weight-label {
  color: rgba(255, 255, 255, 0.8);
}

.weight-value {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}

.weight-item.highlight .weight-value {
  color: white;
}

.arrow-icon {
  font-size: 16px;
  color: var(--text-muted);
  flex-shrink: 0;
  min-width: 16px;
}

.ingredient-calories {
  font-size: 12px;
  color: var(--text-secondary);
  text-align: right;
}

/* 汇总卡片 */
.summary-card {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 8px;
  background: var(--bg-primary);
  border-radius: 8px;
}

.summary-item.highlight {
  background: var(--gradient-primary);
  color: white;
}

.summary-label {
  font-size: 11px;
  color: var(--text-secondary);
}

.summary-item.highlight .summary-label {
  color: rgba(255, 255, 255, 0.9);
}

.summary-value {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}

.summary-item.highlight .summary-value {
  color: white;
}

/* 桌面版样式 */
@media (min-width: 769px) {
  .calculator-container {
    padding-bottom: 0;
  }
  
  .mobile-header {
    display: none;
  }
  
  .calculator-content {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
  }
  
  .recipe-selector {
    max-width: 600px;
    margin: 0 auto;
  }
  
  .calculator-panel {
    max-width: 800px;
    margin: 0 auto;
  }
  
  .summary-card {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>

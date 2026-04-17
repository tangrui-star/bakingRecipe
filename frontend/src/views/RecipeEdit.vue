<template>
  <div class="recipe-edit-container">
    <div class="geometric-bg"></div>
    
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="header-left">
        <el-button @click="handleBack" :icon="ArrowLeft">返回</el-button>
        <h1 class="page-title">{{ isEditMode ? '编辑配方' : '新建配方' }}</h1>
      </div>
      <div class="header-right">
        <el-button @click="handleSave" type="primary" :loading="saving" :icon="Check">
          {{ saving ? '保存中...' : '保存配方' }}
        </el-button>
      </div>
    </header>
    
    <!-- 主要内容 -->
    <main class="page-content">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-container">
        <el-icon class="is-loading" :size="40"><Loading /></el-icon>
        <p>加载配方数据中...</p>
      </div>
      
      <div v-else class="form-container">
        <el-form
          ref="formRef"
          :model="recipeForm"
          :rules="rules"
          label-width="100px"
          class="recipe-form"
        >
          <!-- 基本信息卡片 -->
          <div class="form-card">
            <div class="card-header">
              <h2 class="card-title">基本信息</h2>
            </div>
            
            <div class="card-body">
              <el-form-item label="配方名称" prop="name">
                <el-input
                  v-model="recipeForm.name"
                  placeholder="请输入配方名称，例如：芝士番茄肉松贝果"
                  clearable
                />
              </el-form-item>
              
              <el-form-item label="所属品类" prop="category_id">
                <el-select
                  v-model="recipeForm.category_id"
                  placeholder="请选择品类"
                  style="width: 100%"
                  :loading="loadingCategories"
                >
                  <el-option
                    v-for="category in categories"
                    :key="category.id"
                    :label="category.name"
                    :value="category.id"
                  />
                </el-select>
              </el-form-item>
              
              <el-row :gutter="20">
                <el-col :xs="24" :sm="12">
                  <el-form-item label="基础数量" prop="base_quantity">
                    <el-input-number
                      v-model="recipeForm.base_quantity"
                      :min="1"
                      :max="1000"
                      placeholder="基础数量"
                      style="width: 100%"
                    />
                    <div class="form-tip">用于配方计算的基础数量</div>
                  </el-form-item>
                </el-col>

                <el-col :xs="24" :sm="12">
                  <el-form-item label="基础重量" prop="base_weight">
                    <el-input-number
                      v-model="recipeForm.base_weight"
                      :min="1"
                      :max="10000"
                      :precision="0"
                      placeholder="基础重量"
                      style="width: 100%"
                    />
                    <div class="form-tip">单位：克（g）</div>
                  </el-form-item>
                </el-col>
              </el-row>
              
              <el-form-item label="计算规则" prop="calculation_rule">
                <el-input
                  v-model="recipeForm.calculation_rule"
                  placeholder="例如：除以2向上取整+1"
                  clearable
                />
                <div class="form-tip">可选，用于特殊的配方计算规则</div>
              </el-form-item>
              
              <el-form-item label="备注说明" prop="notes">
                <el-input
                  v-model="recipeForm.notes"
                  type="textarea"
                  :rows="4"
                  placeholder="请输入配方备注，例如：容易炸口，注意温度控制"
                  maxlength="500"
                  show-word-limit
                />
              </el-form-item>
            </div>
          </div>
          
          <!-- 原料管理卡片 -->
          <div class="form-card">
            <div class="card-header">
              <div class="card-header-content">
                <h2 class="card-title">原料配方</h2>
                <el-button type="primary" :icon="Plus" @click="addIngredient" size="small">
                  添加原料
                </el-button>
              </div>
            </div>
            
            <div class="card-body">
              <div v-if="recipeIngredients.length === 0" class="empty-state">
                <p>还没有添加原料</p>
                <el-button type="primary" :icon="Plus" @click="addIngredient">
                  添加第一个原料
                </el-button>
              </div>
              
              <div v-else class="ingredients-list">
                <div
                  v-for="(item, index) in recipeIngredients"
                  :key="index"
                  class="ingredient-item"
                >
                  <div class="ingredient-number">{{ index + 1 }}</div>
                  
                  <div class="ingredient-select">
                    <el-select
                      v-model="item.ingredient_id"
                      placeholder="选择原料"
                      filterable
                      :loading="loadingIngredients"
                      style="width: 100%"
                    >
                      <el-option
                        v-for="ingredient in ingredients"
                        :key="ingredient.id"
                        :label="ingredient.name"
                        :value="ingredient.id"
                      >
                        <span>{{ ingredient.name }}</span>
                        <span style="float: right; color: var(--text-muted); font-size: 12px">
                          {{ ingredient.calories_per_100g ? `${ingredient.calories_per_100g}kcal/100g` : '无热量数据' }}
                        </span>
                      </el-option>
                    </el-select>
                  </div>
                  
                  <div class="ingredient-weight">
                    <el-input-number
                      v-model="item.weight"
                      :min="0.1"
                      :max="10000"
                      :precision="1"
                      :step="10"
                      placeholder="重量"
                      style="width: 100%"
                    />
                    <span class="unit">克</span>
                  </div>
                  
                  <div class="ingredient-calories">
                    <span v-if="item.ingredient_id && item.weight" class="calories-value">
                      {{ calculateIngredientCalories(item.ingredient_id, item.weight) }} kcal
                    </span>
                    <span v-else class="calories-placeholder">-</span>
                  </div>
                  
                  <div class="ingredient-actions">
                    <el-button
                      type="danger"
                      :icon="Delete"
                      circle
                      @click="removeIngredient(index)"
                      size="small"
                    />
                  </div>
                </div>
                
                <!-- 汇总信息 -->
                <div class="ingredients-summary">
                  <div class="summary-item">
                    <span class="summary-label">原料总数：</span>
                    <span class="summary-value">{{ recipeIngredients.length }} 种</span>
                  </div>
                  <div class="summary-item">
                    <span class="summary-label">总重量：</span>
                    <span class="summary-value">{{ totalWeight }} 克</span>
                  </div>
                  <div class="summary-item highlight">
                    <span class="summary-label">总热量：</span>
                    <span class="summary-value">{{ totalCalories }} kcal</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 制作步骤卡片 -->
          <div class="form-card">
            <div class="card-header">
              <div class="card-header-content">
                <h2 class="card-title">制作步骤</h2>
                <el-button type="primary" :icon="Plus" @click="addStep" size="small">
                  添加步骤
                </el-button>
              </div>
            </div>
            
            <div class="card-body">
              <div v-if="recipeSteps.length === 0" class="empty-state">
                <p>还没有添加制作步骤</p>
                <el-button type="primary" :icon="Plus" @click="addStep">
                  添加第一个步骤
                </el-button>
              </div>
              
              <div v-else class="steps-list">
                <div
                  v-for="(step, index) in recipeSteps"
                  :key="index"
                  class="step-item"
                >
                  <div class="step-header">
                    <div class="step-number">步骤 {{ index + 1 }}</div>
                    <el-button
                      type="danger"
                      :icon="Delete"
                      circle
                      @click="removeStep(index)"
                      size="small"
                    />
                  </div>
                  
                  <div class="step-content">
                    <el-input
                      v-model="step.description"
                      type="textarea"
                      :rows="3"
                      placeholder="请输入步骤描述，例如：将面团分割成40克一个，滚圆后松弛15分钟"
                      maxlength="500"
                    />
                    
                    <div class="step-meta">
                      <div class="meta-item">
                        <label>时长（分钟）</label>
                        <el-input-number
                          v-model="step.duration_minutes"
                          :min="0"
                          :max="1440"
                          placeholder="时长"
                          size="small"
                        />
                      </div>
                      
                      <div class="meta-item">
                        <label>温度（℃）</label>
                        <el-input-number
                          v-model="step.temperature"
                          :min="0"
                          :max="300"
                          placeholder="温度"
                          size="small"
                        />
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- 步骤统计 -->
                <div class="steps-summary">
                  <div class="summary-item">
                    <span class="summary-label">总步骤数：</span>
                    <span class="summary-value">{{ recipeSteps.length }} 步</span>
                  </div>
                  <div class="summary-item" v-if="totalDuration > 0">
                    <span class="summary-label">预计总时长：</span>
                    <span class="summary-value">{{ totalDuration }} 分钟</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-form>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Check, Plus, Delete, Loading } from '@element-plus/icons-vue'
import api from '@/api'

const router = useRouter()
const route = useRoute()
const formRef = ref(null)
const saving = ref(false)
const loading = ref(false)
const loadingCategories = ref(false)
const loadingIngredients = ref(false)

// 判断是否为编辑模式
const isEditMode = ref(false)
const recipeId = ref(null)

// 品类列表
const categories = ref([])

// 原料列表
const ingredients = ref([])

// 配方原料列表
const recipeIngredients = ref([])

// 制作步骤列表
const recipeSteps = ref([])

// 表单数据
const recipeForm = ref({
  name: '',
  category_id: '',
  base_quantity: 1,
  base_weight: null,
  calculation_rule: '',
  notes: ''
})

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入配方名称', trigger: 'blur' },
    { min: 2, max: 50, message: '配方名称长度为2-50个字符', trigger: 'blur' }
  ],
  category_id: [
    { required: true, message: '请选择品类', trigger: 'change' }
  ],
  base_quantity: [
    { required: true, message: '请输入基础数量', trigger: 'blur' }
  ]
}

// 加载品类列表
const loadCategories = async () => {
  loadingCategories.value = true
  try {
    const data = await api.categories.list()
    categories.value = data
  } catch (error) {
    ElMessage.error('加载品类列表失败')
    console.error(error)
  } finally {
    loadingCategories.value = false
  }
}

// 加载原料列表
const loadIngredients = async () => {
  loadingIngredients.value = true
  try {
    const data = await api.ingredients.list()
    ingredients.value = data
  } catch (error) {
    ElMessage.error('加载原料列表失败')
    console.error(error)
  } finally {
    loadingIngredients.value = false
  }
}

// 添加原料
const addIngredient = () => {
  recipeIngredients.value.push({
    ingredient_id: '',
    weight: null,
    sort_order: recipeIngredients.value.length
  })
}

// 删除原料
const removeIngredient = async (index) => {
  try {
    await ElMessageBox.confirm('确定要删除这个原料吗？', '提示', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
      confirmButtonClass: 'el-button--danger'
    })
    recipeIngredients.value.splice(index, 1)
    recipeIngredients.value.forEach((item, idx) => {
      item.sort_order = idx
    })
  } catch {
    // 用户取消
  }
}

// 获取原料信息
const getIngredientInfo = (ingredientId) => {
  return ingredients.value.find(ing => ing.id === ingredientId)
}

// 计算单个原料的热量
const calculateIngredientCalories = (ingredientId, weight) => {
  const ingredient = getIngredientInfo(ingredientId)
  if (!ingredient || !weight || !ingredient.calories_per_100g) {
    return 0
  }
  return (ingredient.calories_per_100g * weight / 100).toFixed(2)
}

// 计算总热量
const totalCalories = computed(() => {
  let total = 0
  recipeIngredients.value.forEach(item => {
    if (item.ingredient_id && item.weight) {
      const calories = parseFloat(calculateIngredientCalories(item.ingredient_id, item.weight))
      total += calories
    }
  })
  return total.toFixed(2)
})

// 计算总重量
const totalWeight = computed(() => {
  let total = 0
  recipeIngredients.value.forEach(item => {
    if (item.weight) {
      total += parseFloat(item.weight)
    }
  })
  return total.toFixed(0)
})

// 添加步骤
const addStep = () => {
  recipeSteps.value.push({
    step_number: recipeSteps.value.length + 1,
    description: '',
    duration_minutes: null,
    temperature: null
  })
}

// 删除步骤
const removeStep = async (index) => {
  try {
    await ElMessageBox.confirm('确定要删除这个步骤吗？', '提示', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
      confirmButtonClass: 'el-button--danger'
    })
    recipeSteps.value.splice(index, 1)
    recipeSteps.value.forEach((step, idx) => {
      step.step_number = idx + 1
    })
  } catch {
    // 用户取消
  }
}

// 计算总时长
const totalDuration = computed(() => {
  let total = 0
  recipeSteps.value.forEach(step => {
    if (step.duration_minutes) {
      total += step.duration_minutes
    }
  })
  return total
})

// 返回
const handleBack = async () => {
  // 检查是否有未保存的更改
  const hasChanges = recipeForm.value.name || 
                     recipeForm.value.category_id || 
                     recipeIngredients.value.length > 0 || 
                     recipeSteps.value.length > 0
  
  if (hasChanges && !isEditMode.value) {
    try {
      await ElMessageBox.confirm(
        '您有未保存的更改，确定要离开吗？',
        '提示',
        {
          confirmButtonText: '离开',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
      router.back()
    } catch {
      // 用户取消
    }
  } else {
    router.back()
  }
}

// 保存配方
const handleSave = async () => {
  if (!formRef.value) return
  
  try {
    // 验证表单
    await formRef.value.validate()
    
    saving.value = true
    
    // 获取用户信息
    const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}')
    const shopId = userInfo.shop_id
    
    if (!shopId) {
      ElMessage.error('未找到店铺信息，请重新登录')
      return
    }
    
    // 验证原料列表
    if (recipeIngredients.value.length === 0) {
      ElMessage.warning('请至少添加一个原料')
      return
    }
    
    // 验证原料是否都已填写
    const hasEmptyIngredient = recipeIngredients.value.some(
      item => !item.ingredient_id || !item.weight
    )
    if (hasEmptyIngredient) {
      ElMessage.warning('请完善所有原料信息')
      return
    }
    
    // 验证步骤（可选，但如果有步骤必须填写描述）
    const hasEmptyStep = recipeSteps.value.some(
      step => !step.description || step.description.trim() === ''
    )
    if (hasEmptyStep) {
      ElMessage.warning('请完善所有步骤描述')
      return
    }
    
    // 构建请求数据
    const requestData = {
      shop_id: shopId,
      category_id: recipeForm.value.category_id,
      current_name: recipeForm.value.name,
      version_data: {
        name: recipeForm.value.name,
        base_quantity: recipeForm.value.base_quantity,
        base_weight: recipeForm.value.base_weight,
        calculation_rule: recipeForm.value.calculation_rule || null,
        notes: recipeForm.value.notes || null,
        created_by: userInfo.username,
        ingredients: recipeIngredients.value.map(item => ({
          ingredient_id: item.ingredient_id,
          weight: item.weight,
          sort_order: item.sort_order
        })),
        steps: recipeSteps.value.map(step => ({
          step_number: step.step_number,
          description: step.description,
          duration_minutes: step.duration_minutes,
          temperature: step.temperature
        }))
      }
    }
    
    if (isEditMode.value) {
      // 更新配方（生成新版本） - 只发送version_data
      await api.recipes.update(recipeId.value, requestData.version_data)
      ElMessage.success('配方更新成功，已生成新版本')
    } else {
      // 创建配方 - 发送完整的requestData
      await api.recipes.create(requestData)
      ElMessage.success('配方创建成功')
    }
    
    // 跳转回配方列表
    router.push('/recipes')
  } catch (error) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else if (error !== 'cancel') {
      ElMessage.error('保存失败，请重试')
    }
    console.error(error)
  } finally {
    saving.value = false
  }
}

// 初始化
onMounted(async () => {
  // 加载品类列表和原料列表
  await Promise.all([
    loadCategories(),
    loadIngredients()
  ])
  
  // 检查是否为编辑模式
  if (route.params.id) {
    isEditMode.value = true
    recipeId.value = route.params.id
    await loadRecipe(recipeId.value)
  } else {
    // 新建模式，默认添加一个空原料行和一个空步骤
    addIngredient()
    addStep()
  }
})

// 加载配方数据
const loadRecipe = async (id) => {
  loading.value = true
  try {
    const data = await api.recipes.get(id)
    
    // 填充基本信息
    recipeForm.value.name = data.current_name
    recipeForm.value.category_id = data.category_id
    
    // 获取最新版本数据
    if (data.versions && data.versions.length > 0) {
      const latestVersion = data.versions[data.versions.length - 1]
      
      recipeForm.value.base_quantity = latestVersion.base_quantity || 1
      recipeForm.value.base_weight = latestVersion.base_weight
      recipeForm.value.calculation_rule = latestVersion.calculation_rule || ''
      recipeForm.value.notes = latestVersion.notes || ''
      
      // 填充原料列表
      if (latestVersion.ingredients && latestVersion.ingredients.length > 0) {
        recipeIngredients.value = latestVersion.ingredients.map(item => ({
          ingredient_id: item.ingredient.id,
          weight: item.weight,
          sort_order: item.sort_order
        }))
      } else {
        addIngredient()
      }
      
      // 填充步骤列表
      if (latestVersion.steps && latestVersion.steps.length > 0) {
        recipeSteps.value = latestVersion.steps.map(step => ({
          step_number: step.step_number,
          description: step.description,
          duration_minutes: step.duration_minutes,
          temperature: step.temperature
        }))
      } else {
        addStep()
      }
    } else {
      // 没有版本数据，添加默认空行
      addIngredient()
      addStep()
    }
    
    ElMessage.success('配方加载成功')
  } catch (error) {
    ElMessage.error('加载配方失败')
    console.error(error)
    router.back()
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.recipe-edit-container {
  min-height: 100vh;
  background: var(--bg-primary);
  position: relative;
  overflow-x: hidden;
  width: 100%;
  max-width: 100vw;
}

/* 顶部导航 */
.page-header {
  height: 64px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--spacing-xl);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

/* 主要内容 */
.page-content {
  padding: var(--spacing-xl);
  padding-top: calc(64px + var(--spacing-xl));
  max-width: 1200px;
  margin: 0 auto;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  gap: var(--spacing-lg);
  color: var(--text-secondary);
}

.form-container {
  position: relative;
  z-index: 2;
}

/* 表单卡片 */
.form-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  margin-bottom: var(--spacing-lg);
  overflow: hidden;
}

.card-header {
  padding: var(--spacing-lg) var(--spacing-xl);
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-secondary);
}

.card-header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.card-body {
  padding: var(--spacing-xl);
}

/* 表单样式 */
.recipe-form :deep(.el-form-item__label) {
  font-weight: 500;
  color: var(--text-primary);
}

.recipe-form :deep(.el-input__wrapper) {
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  box-shadow: none;
  transition: all var(--transition-base);
}

.recipe-form :deep(.el-input__wrapper:hover) {
  border-color: var(--border-focus);
}

.recipe-form :deep(.el-input__wrapper.is-focus) {
  border-color: var(--border-focus);
  box-shadow: var(--shadow-focus);
}

.recipe-form :deep(.el-textarea__inner) {
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  box-shadow: none;
  transition: all var(--transition-base);
}

.recipe-form :deep(.el-textarea__inner:hover) {
  border-color: var(--border-focus);
}

.recipe-form :deep(.el-textarea__inner:focus) {
  border-color: var(--border-focus);
  box-shadow: var(--shadow-focus);
}

.form-tip {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}

/* 原料列表样式 */
.empty-state {
  text-align: center;
  padding: var(--spacing-2xl);
  color: var(--text-secondary);
}

.empty-state p {
  margin-bottom: var(--spacing-lg);
  font-size: 14px;
}

.ingredients-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.ingredient-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  transition: all var(--transition-base);
}

.ingredient-item:hover {
  border-color: var(--primary-blue);
  box-shadow: var(--shadow-sm);
}

.ingredient-number {
  width: 32px;
  height: 32px;
  min-width: 32px;
  min-height: 32px;
  background: var(--gradient-primary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
}

.ingredient-select {
  flex: 2;
  min-width: 200px;
}

.ingredient-weight {
  flex: 1;
  min-width: 150px;
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.unit {
  color: var(--text-secondary);
  font-size: 14px;
  white-space: nowrap;
}

.ingredient-calories {
  flex: 1;
  min-width: 120px;
  text-align: right;
}

.calories-value {
  color: var(--primary-green);
  font-weight: 600;
  font-size: 14px;
}

.calories-placeholder {
  color: var(--text-muted);
}

.ingredient-actions {
  flex-shrink: 0;
}

/* 汇总信息 */
.ingredients-summary {
  margin-top: var(--spacing-lg);
  padding: var(--spacing-lg);
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  display: flex;
  justify-content: space-around;
  gap: var(--spacing-lg);
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xs);
}

.summary-item.highlight {
  padding: var(--spacing-sm) var(--spacing-lg);
  background: var(--gradient-primary);
  border-radius: var(--radius-md);
  color: white;
}

.summary-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.summary-item.highlight .summary-label {
  color: rgba(255, 255, 255, 0.9);
}

.summary-value {
  font-size: 18px;
  font-weight: 700;
}

/* 制作步骤样式 */
.steps-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.step-item {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  overflow: hidden;
  transition: all var(--transition-base);
}

.step-item:hover {
  border-color: var(--primary-blue);
  box-shadow: var(--shadow-sm);
}

.step-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
}

.step-number {
  font-size: 16px;
  font-weight: 600;
  color: var(--primary-blue);
}

.step-content {
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.step-meta {
  display: flex;
  gap: var(--spacing-lg);
}

.meta-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.meta-item label {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.steps-summary {
  margin-top: var(--spacing-md);
  padding: var(--spacing-lg);
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  display: flex;
  justify-content: space-around;
  gap: var(--spacing-lg);
}

/* 响应式 */
@media (max-width: 768px) {
  .page-header {
    padding: 0 var(--spacing-md);
    width: 100%;
    max-width: 100vw;
  }
  
  .header-left {
    gap: var(--spacing-sm);
    overflow: hidden;
  }
  
  .page-content {
    padding: var(--spacing-md);
    padding-top: calc(64px + var(--spacing-md));
    padding-bottom: 70px;
    width: 100%;
    max-width: 100vw;
  }
  
  .card-body {
    padding: var(--spacing-md);
  }
  
  .page-title {
    font-size: 16px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .form-card {
    width: 100%;
    max-width: 100%;
  }
  
  .ingredient-item {
    flex-wrap: wrap;
    width: 100%;
  }
  
  .ingredient-select,
  .ingredient-weight,
  .ingredient-calories {
    flex: 1 1 100%;
    min-width: 0;
    max-width: 100%;
  }
  
  .ingredient-calories {
    text-align: left;
  }
  
  .ingredients-summary {
    flex-direction: column;
    width: 100%;
  }
  
  .step-meta {
    flex-direction: column;
    width: 100%;
  }
  
  .meta-item {
    width: 100%;
    max-width: 100%;
  }
  
  .steps-summary {
    flex-direction: column;
    width: 100%;
  }
  
  /* 确保所有输入框不超出 */
  .recipe-form :deep(.el-input),
  .recipe-form :deep(.el-select),
  .recipe-form :deep(.el-input-number) {
    max-width: 100%;
  }
  
  .recipe-form :deep(.el-row) {
    margin-left: 0 !important;
    margin-right: 0 !important;
  }
  
  .recipe-form :deep(.el-col) {
    padding-left: 0 !important;
    padding-right: 0 !important;
  }
}
</style>

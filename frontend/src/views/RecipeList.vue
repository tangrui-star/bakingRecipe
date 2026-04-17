<template>
  <div class="recipe-list-container">
    <div class="geometric-bg"></div>
    
    <!-- 移动端顶部 -->
    <header class="mobile-header">
      <div class="header-content">
        <div class="header-title">配方管理</div>
        <el-button type="primary" size="small" @click="$router.push('/recipes/create')">
          <el-icon><Plus /></el-icon>
          新建
        </el-button>
      </div>
    </header>
    
    <!-- 主要内容 -->
    <div class="recipe-content">
      <!-- 筛选和操作栏 -->
      <div class="filter-bar">
        <el-select 
          v-model="selectedCategory" 
          placeholder="全部品类" 
          clearable 
          @change="loadRecipes"
          size="default"
        >
          <el-option label="全部品类" value="" />
          <el-option
            v-for="cat in categories"
            :key="cat.id"
            :label="cat.name"
            :value="cat.id"
          />
        </el-select>
        <el-button @click="handleExport" :loading="exporting" size="default">
          <el-icon><Download /></el-icon>
          导出
        </el-button>
      </div>
      
      <!-- 配方列表 -->
      <div class="recipes-list" v-loading="loading">
        <div v-if="recipes.length === 0" class="empty-state">
          <el-icon :size="60"><Document /></el-icon>
          <p>暂无配方数据</p>
          <el-button type="primary" @click="$router.push('/recipes/create')">
            <el-icon><Plus /></el-icon>
            创建第一个配方
          </el-button>
        </div>
        
        <div 
          v-for="recipe in recipes" 
          :key="recipe.id" 
          class="recipe-card"
        >
          <div class="recipe-header">
            <div class="recipe-name">{{ recipe.current_name }}</div>
            <div class="recipe-version">v{{ recipe.current_version }}</div>
          </div>
          <div class="recipe-meta">
            <span class="meta-item">
              <el-icon><Dish /></el-icon>
              {{ getCategoryName(recipe.category_id) }}
            </span>
            <span class="meta-item">
              <el-icon><Clock /></el-icon>
              {{ formatDate(recipe.updated_at) }}
            </span>
          </div>
          <div class="recipe-actions">
            <el-button size="small" @click="viewHistory(recipe.id)">
              <el-icon><Clock /></el-icon>
              历史
            </el-button>
            <el-button size="small" type="primary" @click="editRecipe(recipe.id)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button size="small" type="danger" @click="deleteRecipe(recipe.id)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Download, Document, Dish, Clock, Edit, Delete } from '@element-plus/icons-vue'
import api from '@/api'

const router = useRouter()
const recipes = ref([])
const categories = ref([])
const selectedCategory = ref('')
const loading = ref(false)
const exporting = ref(false)
const currentShopId = ref(null)
const currentUser = ref(null)

onMounted(async () => {
  await loadUserInfo()
  await loadCategories()
  await loadRecipes()
})

const loadUserInfo = async () => {
  try {
    currentUser.value = await api.auth.getCurrentUser()
    currentShopId.value = currentUser.value.shop_id
    
    if (!currentShopId.value) {
      ElMessage.warning('未找到店铺信息，请联系管理员')
    }
  } catch (error) {
    console.error('获取用户信息失败:', error)
    ElMessage.error('获取用户信息失败')
  }
}

const loadCategories = async () => {
  try {
    categories.value = await api.categories.list()
  } catch (error) {
    ElMessage.error('加载品类失败')
  }
}

const loadRecipes = async () => {
  if (!currentShopId.value) {
    console.log('loadRecipes: 没有shop_id，跳过加载')
    return
  }
  
  loading.value = true
  try {
    console.log('loadRecipes: 开始加载配方', {
      shopId: currentShopId.value,
      category: selectedCategory.value
    })
    const result = await api.recipes.list(currentShopId.value, selectedCategory.value)
    console.log('loadRecipes: API返回数据', {
      count: result.length,
      data: result
    })
    recipes.value = result
  } catch (error) {
    console.error('加载配方失败:', error)
    ElMessage.error('加载配方失败')
  } finally {
    loading.value = false
  }
}

const getCategoryName = (categoryId) => {
  const cat = categories.value.find(c => c.id === categoryId)
  return cat ? cat.name : '-'
}

const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

const viewHistory = (id) => {
  router.push(`/recipes/${id}/history`)
}

const editRecipe = (id) => {
  router.push(`/recipes/${id}/edit`)
}

const deleteRecipe = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这个配方吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await api.recipes.delete(id)
    ElMessage.success('删除成功')
    loadRecipes()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleExport = async () => {
  try {
    if (!currentShopId.value) {
      ElMessage.warning('未找到店铺信息')
      return
    }
    
    exporting.value = true
    ElMessage.info('正在导出数据...')
    
    // 使用fetch直接下载文件
    const token = localStorage.getItem('access_token')
    const response = await fetch(`/api/recipes/export/${currentShopId.value}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (!response.ok) {
      throw new Error('导出失败')
    }
    
    // 获取文件名
    const contentDisposition = response.headers.get('Content-Disposition')
    let filename = 'recipes_export.json'
    if (contentDisposition) {
      const matches = /filename=(.+)/.exec(contentDisposition)
      if (matches && matches[1]) {
        filename = matches[1]
      }
    }
    
    // 下载文件
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    
    ElMessage.success('导出成功！')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败，请重试')
  } finally {
    exporting.value = false
  }
}
</script>

<style scoped>
.recipe-list-container {
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
  width: 100%;
  max-width: 100vw;
  background: var(--bg-primary);
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
.recipe-content {
  padding: 12px;
  padding-top: 60px; /* header高度48px + 间距 */
}

/* 筛选栏 */
.filter-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.filter-bar .el-select {
  flex: 1;
}

/* 配方列表 */
.recipes-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
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

.recipe-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 14px;
  transition: all 0.3s ease;
  -webkit-tap-highlight-color: transparent;
}

.recipe-card:active {
  transform: scale(0.98);
  background: var(--bg-hover);
}

.recipe-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.recipe-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  flex: 1;
}

.recipe-version {
  font-size: 11px;
  color: var(--text-muted);
  background: var(--bg-primary);
  padding: 3px 8px;
  border-radius: 4px;
  margin-left: 8px;
}

.recipe-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  font-size: 12px;
  color: var(--text-secondary);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.meta-item .el-icon {
  flex-shrink: 0;
}

.recipe-actions {
  display: flex;
  gap: 8px;
}

.recipe-actions .el-button {
  flex: 1;
  font-size: 13px;
}

/* 桌面版样式 */
@media (min-width: 769px) {
  .recipe-list-container {
    padding: 0;
    padding-bottom: 20px;
  }

  .mobile-header {
    display: flex;
  }

  .header-content {
    max-width: 1200px;
    margin: 0 auto;
    width: 100%;
    padding: 12px 20px;
  }

  .recipe-content {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
  }
  
  .recipes-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 16px;
  }
  
  .recipe-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
}
</style>

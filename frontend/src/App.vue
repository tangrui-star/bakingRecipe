<template>
  <el-config-provider :locale="locale">
    <router-view />
    <TabBar v-if="showTabBar" />
  </el-config-provider>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import TabBar from './components/TabBar.vue'

const locale = zhCn
const route = useRoute()

// 不显示TabBar的页面
const hideTabBarPages = ['/login', '/register']

// 显示TabBar的条件（依赖route.path，确保响应式）
const showTabBar = computed(() => {
  // 通过访问 route.path 确保 computed 依赖路由变化
  const currentPath = route.path
  
  // 检查是否登录（每次路由变化都会重新检查）
  const hasToken = !!localStorage.getItem('access_token')
  
  // 未登录时不显示TabBar
  if (!hasToken) {
    return false
  }
  
  // 登录/注册页面不显示TabBar
  if (hideTabBarPages.includes(currentPath)) {
    return false
  }
  
  return true
})
</script>

<style>
/* 全局样式已在 main.js 中导入 */
</style>

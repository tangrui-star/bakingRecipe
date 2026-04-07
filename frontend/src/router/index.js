import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/recipes',
    name: 'RecipeList',
    component: () => import('@/views/RecipeList.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/recipes/create',
    name: 'RecipeCreate',
    component: () => import('@/views/RecipeEdit.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/recipes/:id/edit',
    name: 'RecipeEdit',
    component: () => import('@/views/RecipeEdit.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/recipes/:id/history',
    name: 'RecipeHistory',
    component: () => import('@/views/RecipeHistory.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/calculator',
    name: 'RecipeCalculator',
    component: () => import('@/views/RecipeCalculator.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/analytics',
    name: 'Analytics',
    component: () => import('@/views/RecipeCalculator.vue'), // 临时使用计算器页面
    meta: { requiresAuth: true }
  },
  {
    path: '/shop',
    name: 'Shop',
    component: () => import('@/views/RecipeCalculator.vue'), // 临时使用计算器页面
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/blacklist',
    name: 'BlacklistManage',
    component: () => import('@/views/BlacklistManage.vue'),
    meta: { requiresAuth: true, title: '黑名单管理' }
  },
  {
    path: '/blacklist/edit/:id?',
    name: 'BlacklistEdit',
    component: () => import('@/views/BlacklistEdit.vue'),
    meta: { requiresAuth: true, title: '编辑黑名单' }
  },
  {
    path: '/screening',
    name: 'OrderScreening',
    component: () => import('@/views/OrderScreening.vue'),
    meta: { requiresAuth: true, title: '订单检查' }
  },
  {
    path: '/screening-history',
    name: 'ScreeningHistory',
    component: () => import('@/views/ScreeningHistory.vue'),
    meta: { requiresAuth: true, title: '检查历史' }
  },
  {
    path: '/screening-detail/:id',
    name: 'ScreeningDetail',
    component: () => import('@/views/ScreeningDetail.vue'),
    meta: { requiresAuth: true, title: '检查详情' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  
  if (requiresAuth && !token) {
    // 需要认证但没有token，跳转登录
    next('/login')
  } else if (!requiresAuth && token && (to.path === '/login' || to.path === '/register')) {
    // 已登录用户访问登录/注册页，跳转仪表盘
    next('/dashboard')
  } else {
    next()
  }
})

export default router

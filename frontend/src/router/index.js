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
  },
  {
    path: '/order-process',
    name: 'OrderProcess',
    component: () => import('@/views/OrderProcess.vue'),
    meta: { requiresAuth: true, title: '订单数据处理' }
  },
  {
    path: '/logistics-process',
    name: 'LogisticsProcess',
    component: () => import('@/views/LogisticsProcess.vue'),
    meta: { requiresAuth: true, title: '中通快递表生成' }
  },
  // 通知中心
  {
    path: '/notifications',
    name: 'Notifications',
    component: () => import('@/views/Notifications.vue'),
    meta: { requiresAuth: true, title: '通知中心' }
  },
  // 推送申请
  {
    path: '/push-request/:id',
    name: 'PushRequest',
    component: () => import('@/views/PushRequest.vue'),
    meta: { requiresAuth: true, title: '申请推送' }
  },
  {
    path: '/my-push-requests',
    name: 'MyPushRequests',
    component: () => import('@/views/MyPushRequests.vue'),
    meta: { requiresAuth: true, title: '我的推送申请' }
  },
  // 管理员后台
  {
    path: '/admin',
    name: 'AdminDashboard',
    component: () => import('@/views/admin/AdminDashboard.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, title: '管理员后台' }
  },
  {
    path: '/admin/system-blacklist',
    name: 'SystemBlacklist',
    component: () => import('@/views/admin/SystemBlacklist.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, title: '系统黑名单管理' }
  },
  {
    path: '/admin/push-requests',
    name: 'PushRequestReview',
    component: () => import('@/views/admin/PushRequestReview.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, title: '推送申请审核' }
  },
  {
    path: '/admin/users',
    name: 'UserManagement',
    component: () => import('@/views/admin/UserManagement.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, title: '用户管理' }
  },
  {
    path: '/admin/user-blacklist',
    name: 'AdminUserBlacklist',
    component: () => import('@/views/admin/AdminUserBlacklist.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, title: '全平台用户黑名单' }
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

  // 检查token是否存在且未过期
  const isTokenValid = () => {
    if (!token) return false
    try {
      // JWT payload是base64编码的第二段
      const payload = JSON.parse(atob(token.split('.')[1]))
      // exp是秒级时间戳
      return payload.exp * 1000 > Date.now()
    } catch {
      return false
    }
  }

  if (requiresAuth && !isTokenValid()) {
    // token不存在或已过期，清除并跳转登录
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_info')
    next('/login')
  } else if (!requiresAuth && isTokenValid() && (to.path === '/login' || to.path === '/register')) {
    next('/dashboard')
  } else if (to.matched.some(r => r.meta.requiresAdmin)) {
    // 需要管理员权限
    const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}')
    if (!userInfo.is_admin) {
      next('/dashboard')
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router

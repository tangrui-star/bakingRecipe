import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// 请求拦截器 - 添加token
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理token过期
api.interceptors.response.use(
  response => response.data,
  async error => {
    const originalRequest = error.config

    // auth接口本身的401（登录失败、验证码错误等）直接透传，不触发刷新逻辑
    const isAuthRequest = originalRequest.url?.includes('/auth/login') ||
      originalRequest.url?.includes('/auth/register') ||
      originalRequest.url?.includes('/auth/refresh-token')

    // Token过期，尝试刷新（排除auth接口）
    if (error.response?.status === 401 && !originalRequest._retry && !isAuthRequest) {
      originalRequest._retry = true

      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const response = await axios.post('/api/auth/refresh-token', {
            refresh_token: refreshToken
          })

          localStorage.setItem('access_token', response.data.access_token)
          originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`

          return api(originalRequest)
        } catch (refreshError) {
          // 刷新失败，清除token并用router跳转（避免页面整体重载闪动）
          localStorage.clear()
          ElMessage.error('登录已过期，请重新登录')
          // 延迟跳转，让ElMessage显示出来
          setTimeout(() => { window.location.href = '/login' }, 1500)
          return Promise.reject(refreshError)
        }
      } else {
        localStorage.clear()
        setTimeout(() => { window.location.href = '/login' }, 100)
      }
    }

    return Promise.reject(error)
  }
)

export default {
  // 认证相关
  auth: {
    login: (data) => api.post('/auth/login', data),
    register: (data) => api.post('/auth/register', data),
    logout: () => api.post('/auth/logout'),
    sendEmailCode: (data) => api.post('/auth/email-code', data),
    getCurrentUser: () => api.get('/auth/me'),
    updateUser: (data) => api.put('/auth/me', data),
    changePassword: (data) => api.post('/auth/change-password', data),
    refreshToken: (data) => api.post('/auth/refresh-token', data)
  },
  
  // 配方相关
  recipes: {
    list: (shopId, categoryId) => api.get(`/recipes/shop/${shopId}`, { params: { category_id: categoryId } }),
    get: (id) => api.get(`/recipes/${id}`),
    create: (data) => api.post('/recipes/', data),
    update: (id, data) => api.put(`/recipes/${id}`, data),
    delete: (id) => api.delete(`/recipes/${id}`),
    versions: (id) => api.get(`/recipes/${id}/versions`),
    calculate: (data) => api.post('/recipes/calculate', data),
    export: (shopId) => {
      // 导出需要特殊处理，直接下载文件
      const token = localStorage.getItem('access_token')
      const url = `/api/recipes/export/${shopId}`
      window.open(`${url}?token=${token}`, '_blank')
    }
  },
  
  // 品类相关
  categories: {
    list: () => api.get('/categories/'),
    create: (data) => api.post('/categories/', data)
  },
  
  // 原料相关
  ingredients: {
    list: () => api.get('/ingredients/'),
    create: (data) => api.post('/ingredients/', data),
    update: (id, data) => api.put(`/ingredients/${id}`, data)
  },
  
  // 店铺相关
  shops: {
    list: () => api.get('/shops/'),
    get: (id) => api.get(`/shops/${id}`),
    create: (data) => api.post('/shops/', data)
  }
}

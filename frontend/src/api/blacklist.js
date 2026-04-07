import axios from 'axios'

// 使用空字符串让Vite代理处理API请求
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
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

// 响应拦截器 - 处理错误
api.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response?.status === 401) {
      // Token过期，跳转到登录页
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

/**
 * 黑名单API
 */
export const blacklistAPI = {
  /**
   * 创建黑名单条目
   */
  create(data) {
    return api.post('/api/blacklist', data)
  },

  /**
   * 获取黑名单列表
   */
  getList(params) {
    return api.get('/api/blacklist', { params })
  },

  /**
   * 获取黑名单详情
   */
  getDetail(id) {
    return api.get(`/api/blacklist/${id}`)
  },

  /**
   * 更新黑名单条目
   */
  update(id, data) {
    return api.put(`/api/blacklist/${id}`, data)
  },

  /**
   * 删除黑名单条目
   */
  delete(id) {
    return api.delete(`/api/blacklist/${id}`)
  }
}

export default blacklistAPI

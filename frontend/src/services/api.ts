import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器 - 添加token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器 - 处理错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api

// 认证API
export const authApi = {
  login: (username: string, password: string) => 
    api.post('/auth/login', new URLSearchParams({ username, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }),
  register: (data: { email: string; username: string; password: string }) =>
    api.post('/auth/register', data),
  getMe: () => api.get('/auth/me'),
}

// 任务API
export const taskApi = {
  list: (params?: { page?: number; page_size?: number; status?: string }) =>
    api.get('/tasks', { params }),
  get: (id: string) => api.get(`/tasks/${id}`),
  create: (data: any) => api.post('/tasks', data),
  update: (id: string, data: any) => api.patch(`/tasks/${id}`, data),
  delete: (id: string) => api.delete(`/tasks/${id}`),
  getLogs: (id: string) => api.get(`/tasks/${id}/logs`),
}

// 资产API
export const assetApi = {
  list: (params?: { page?: number; page_size?: number; asset_type?: string }) =>
    api.get('/assets', { params }),
  get: (id: string) => api.get(`/assets/${id}`),
  create: (data: any) => api.post('/assets', data),
  update: (id: string, data: any) => api.patch(`/assets/${id}`, data),
}

// 资源API
export const resourceApi = {
  list: (params?: { page?: number; page_size?: number; resource_type?: string }) =>
    api.get('/resources', { params }),
  get: (id: string) => api.get(`/resources/${id}`),
  create: (data: any) => api.post('/resources', data),
}

// 计费API
export const billingApi = {
  getBalance: () => api.get('/billing/balance'),
  getOrders: (params?: { page?: number; page_size?: number }) =>
    api.get('/billing/orders', { params }),
  recharge: (data: { amount: number; payment_method: string }) =>
    api.post('/billing/recharge', data),
  getInvoices: (params?: { page?: number; page_size?: number }) =>
    api.get('/billing/invoices', { params }),
  getPrices: () => api.get('/billing/prices'),
}

// 社区API
export const communityApi = {
  getPosts: (params?: { page?: number; page_size?: number; category?: string; tag?: string }) =>
    api.get('/community/posts', { params }),
  getPost: (id: string) => api.get(`/community/posts/${id}`),
  createPost: (data: any) => api.post('/community/posts', data),
  getCategories: () => api.get('/community/categories'),
  getTags: () => api.get('/community/tags'),
  getComments: (postId: string, params?: { page?: number; page_size?: number }) =>
    api.get(`/community/posts/${postId}/comments`, { params }),
}

// 用户管理API
export const userApi = {
  list: (params?: { page?: number; page_size?: number }) =>
    api.get('/users', { params }),
  get: (id: string) => api.get(`/users/${id}`),
  create: (data: any) => api.post('/users', data),
  update: (id: string, data: any) => api.patch(`/users/${id}`, data),
  delete: (id: string) => api.delete(`/users/${id}`),
}
import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 120000,
})

api.interceptors.response.use(
  (response) => response.data,
  (error) => Promise.reject(new Error(error.response?.data?.message || error.message || '请求失败')),
)

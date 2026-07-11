import { api } from './client'

export const logApi = {
  list: (lines) => api.get('/logs', { params: { lines } }),
}

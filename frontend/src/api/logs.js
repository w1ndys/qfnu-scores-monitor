import { api } from './client'

export const logApi = {
  list: () => api.get('/logs'),
  content: (name, lines) => api.get(`/logs/${encodeURIComponent(name)}`, { params: { lines } }),
}

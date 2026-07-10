import { api } from './client'

export const userApi = {
  list: () => api.get('/users'),
  import: (text) => api.post('/import', { text }),
  remove: (account) => api.delete(`/users/${encodeURIComponent(account)}`),
  toggle: (account) => api.post(`/users/${encodeURIComponent(account)}/toggle`),
  check: (account) => api.post(`/users/${encodeURIComponent(account)}/check`),
  checkAll: () => api.post('/check'),
}

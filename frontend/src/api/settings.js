import { api } from './client'

export const settingsApi = {
  get: () => api.get('/settings'),
  update: (settings) => api.put('/settings', settings),
}

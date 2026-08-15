import axios from 'axios'

const API_BASE_URL = '/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

export const healthAPI = {
  check: () => api.get('/health'),
  checkDatabase: () => api.get('/health/database')
}

export const schemaAPI = {
  getSchemas: () => api.get('/schema/schemas'),
  getSchema: (schema = 'public') => api.get('/schema', { params: { schema } }),
  getTables: (schema = 'public') => api.get('/schema/tables', { params: { schema } }),
  getTableSchema: (tableName, schema = 'public') =>
    api.get(`/schema/tables/${tableName}`, { params: { schema } }),
  analyzeSchema: (data) => api.post('/schema/analyze', data)
}

export const maskingAPI = {
  getStrategies: () => api.get('/masking/strategies'),
  getPolicies: () => api.get('/masking/policies'),
  getPolicy: (id) => api.get(`/masking/policies/${id}`),
  createPolicy: (data) => api.post('/masking/policies', data),
  deletePolicy: (id) => api.delete(`/masking/policies/${id}`),
  getRecommendations: (params) => api.get('/masking/recommendations', { params }),
  approveRecommendation: (id) => api.post(`/masking/recommendations/${id}/approve`),
  rejectRecommendation: (id) => api.post(`/masking/recommendations/${id}/reject`),
  applyMasking: (data) => api.post('/masking/apply', data)
}

export const queryAPI = {
  execute: (data) => api.post('/query', data),
  validate: (query) => api.post('/query/validate', { query }),
  getHistory: (limit) => api.get('/query/history', { params: { limit } })
}

export default api

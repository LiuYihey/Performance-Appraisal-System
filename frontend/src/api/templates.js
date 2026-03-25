import request from './request'

export function getTemplates(params) {
  return request.get('/api/templates', { params })
}

export function createTemplate(data) {
  return request.post('/api/templates', data)
}

export function updateTemplate(id, data) {
  return request.put(`/api/templates/${id}`, data)
}

export function deleteTemplate(id) {
  return request.delete(`/api/templates/${id}`)
}

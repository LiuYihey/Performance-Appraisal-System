import request from './request'

export function getEmployees(params) {
  return request.get('/api/employees', { params })
}

export function getSubordinates(params) {
  return request.get('/api/employees/subordinates', { params })
}

export function syncDepartments() {
  return request.post('/api/sync/departments')
}

export function syncEmployees() {
  return request.post('/api/sync/employees')
}

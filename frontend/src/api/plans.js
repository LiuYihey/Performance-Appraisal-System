import request from './request'

export function getPlans(params) {
  return request.get('/api/plans', { params })
}

export function createPlan(data) {
  return request.post('/api/plans', data)
}

export function getCurrentStage() {
  return request.get('/api/stage/current')
}

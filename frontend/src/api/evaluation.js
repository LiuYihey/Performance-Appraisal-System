import request from './request'

export function getMyAssessments(params) {
  return request.get('/api/my/assessments', { params })
}

export function submitSelfEval(data) {
  return request.post('/api/eval/self', data)
}

export function submitManagerEval(data) {
  return request.post('/api/eval/manager', data)
}

export function submitHRFinal(data) {
  return request.post('/api/eval/hr-final', data)
}

export function submitVpApprove(data) {
  return request.post('/api/eval/vp', data)
}

export function getEvalRecord(id) {
  return request.get(`/api/eval/record/${id}`)
}

export function getEvalLogs(id) {
  return request.get(`/api/eval/record/${id}/logs`)
}

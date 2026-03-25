import request from './request'

export function getUserInfo() {
  return request.get('/auth/me')
}

export function login() {
  window.location.href = '/auth/login'
}

export function logout() {
  return request.post('/auth/logout')
}

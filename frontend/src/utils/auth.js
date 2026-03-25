export function getToken() {
  const match = document.cookie.match(/(?:^|; )token=([^;]*)/)
  return match ? decodeURIComponent(match[1]) : null
}

export function setToken(token) {
  const expires = new Date()
  expires.setTime(expires.getTime() + 7 * 24 * 60 * 60 * 1000)
  document.cookie = `token=${encodeURIComponent(token)};expires=${expires.toUTCString()};path=/`
}

export function removeToken() {
  document.cookie = 'token=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/'
}

export function redirectToLogin() {
  window.location.href = '/auth/login'
}

import axios from 'axios'
import { getToken, redirectToLogin } from '../utils/auth'
import { showToast } from 'vant'

const request = axios.create({
  baseURL: '',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

request.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

request.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response) {
      const status = error.response.status
      if (status === 401) {
        redirectToLogin()
        return Promise.reject(error)
      }
      if (status === 403) {
        showToast('没有权限访问')
      } else if (status === 500) {
        showToast('服务器内部错误')
      } else {
        showToast(error.response.data?.detail || '请求失败')
      }
    } else if (error.code === 'ECONNABORTED') {
      showToast('请求超时')
    } else {
      showToast('网络连接失败')
    }
    return Promise.reject(error)
  }
)

export default request

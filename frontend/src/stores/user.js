import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getUserInfo } from '../api/auth'
import { getToken, setToken, removeToken } from '../utils/auth'
import router from '../router'

export const useUserStore = defineStore('user', () => {
  const userInfo = ref(null)
  const loading = ref(false)

  const isLoggedIn = computed(() => !!getToken())
  const role = computed(() => userInfo.value?.role || 'employee')
  const isAdmin = computed(() => role.value === 'admin')
  const isHR = computed(() => role.value === 'hr')
  const isManager = computed(() => role.value === 'manager')

  const displayName = computed(() => {
    if (!userInfo.value) return ''
    return userInfo.value.name || ''
  })

  const department = computed(() => {
    return userInfo.value?.dept_name || ''
  })

  async function checkAuth() {
    const token = getToken()
    if (!token) {
      router.replace('/login')
      return false
    }
    loading.value = true
    try {
      const res = await getUserInfo()
      userInfo.value = res || res.data
      return true
    } catch (err) {
      removeToken()
      router.replace('/login')
      return false
    } finally {
      loading.value = false
    }
  }

  function logout() {
    removeToken()
    userInfo.value = null
    router.replace('/login')
  }

  function setUserInfo(info) {
    userInfo.value = info
  }

  return {
    userInfo,
    loading,
    isLoggedIn,
    role,
    isAdmin,
    isHR,
    isManager,
    displayName,
    department,
    checkAuth,
    logout,
    setUserInfo
  }
})

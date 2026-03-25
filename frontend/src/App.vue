<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from './stores/user'
import { setToken } from './utils/auth'

const router = useRouter()
const userStore = useUserStore()

onMounted(() => {
  // 检查 URL 中是否有 token 参数（企业微信登录回调）
  const urlParams = new URLSearchParams(window.location.search)
  const token = urlParams.get('token')

  if (token) {
    // 保存 token 到 cookie
    setToken(token)
    // 清除 URL 中的 token 参数
    window.history.replaceState({}, document.title, window.location.pathname)
    // 重新加载用户信息
    userStore.checkAuth()
  } else {
    userStore.checkAuth()
  }
})
</script>

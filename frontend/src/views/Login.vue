<template>
  <div class="login-page">
    <div class="login-bg">
      <div class="login-card">
        <div class="logo-area">
          <div class="logo-icon">📊</div>
          <h1 class="app-title">绩效管理系统</h1>
          <p class="app-subtitle">企业绩效评估平台</p>
        </div>
        <div class="login-actions">
          <van-button type="primary" block round size="large" @click="handleLogin" :loading="loading">
            🏢 企业微信登录
          </van-button>
        </div>
        <div class="login-tip">
          <p>请使用企业微信扫码或在企业微信中打开</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { setToken } from '../utils/auth'
import { useUserStore } from '../stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const loading = ref(false)

onMounted(() => {
  // 检查 URL 中是否有 token 参数（OAuth 回调后重定向过来的）
  const token = route.query.token
  if (token) {
    setToken(token)
    // 获取用户信息
    userStore.checkAuth().then((ok) => {
      if (ok) {
        router.replace('/')
      } else {
        // 如果 token 无效，清除并停留在登录页
        loading.value = false
      }
    })
  }
})

function handleLogin() {
  loading.value = true
  window.location.href = '/auth/login'
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}
.login-bg {
  width: 100%;
  padding: 20px;
}
.login-card {
  background: #fff;
  border-radius: 16px;
  padding: 48px 24px 32px;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0,0,0,0.15);
}
.logo-area {
  margin-bottom: 40px;
}
.logo-icon {
  font-size: 64px;
  margin-bottom: 16px;
}
.app-title {
  font-size: 24px;
  font-weight: 700;
  color: #333;
  margin-bottom: 8px;
}
.app-subtitle {
  font-size: 14px;
  color: #999;
}
.login-actions {
  margin-bottom: 24px;
}
.login-tip {
  margin-top: 20px;
}
.login-tip p {
  font-size: 12px;
  color: #bbb;
}
</style>

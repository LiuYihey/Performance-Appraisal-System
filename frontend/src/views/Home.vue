<template>
  <div class="page-container">
    <!-- 顶部导航 -->
    <van-nav-bar :title="userStore.displayName || '绩效管理'" fixed placeholder>
      <template #right>
        <van-icon name="setting-o" size="22" color="#fff" @click="showMenu = true" class="nav-icon" />
      </template>
    </van-nav-bar>

    <!-- 用户信息卡片 -->
    <div class="page-content">
      <div class="user-card card" v-if="userStore.userInfo">
        <div class="user-avatar">{{ userStore.displayName?.charAt(0) || '?' }}</div>
        <div class="user-info">
          <div class="user-name">{{ userStore.displayName }}</div>
          <div class="user-dept">{{ userStore.department }} · {{ roleLabel }}</div>
        </div>
        <div class="user-badge" v-if="pendingCount > 0">
          <van-badge :content="pendingCount" />
        </div>
      </div>

      <!-- 快捷入口 -->
      <div class="quick-grid">
        <div class="quick-item" @click="$router.push('/employee/assessments')">
          <div class="quick-icon">📋</div>
          <span>我的考核</span>
        </div>
        <div class="quick-item" @click="$router.push('/employee/history')">
          <div class="quick-icon">📅</div>
          <span>历史记录</span>
        </div>
        <div class="quick-item" v-if="userStore.isManager || userStore.isAdmin" @click="$router.push('/manager/approvals')">
          <div class="quick-icon">✅</div>
          <span>待审批</span>
        </div>
        <div class="quick-item" v-if="userStore.isHR || userStore.isAdmin" @click="$router.push('/hr/dashboard')">
          <div class="quick-icon">📈</div>
          <span>数据概览</span>
        </div>
      </div>

      <!-- 当前考核提醒 -->
      <div class="card" v-if="currentAssessment">
        <div class="section-title">进行中的考核</div>
        <div class="assess-info">
          <div class="assess-name">{{ currentAssessment.plan_name }}</div>
          <div class="assess-status">
            <span :class="`status-tag ${getStatusClass(currentAssessment.status)}`">
              {{ getStatusLabel(currentAssessment.status) }}
            </span>
          </div>
          <div class="assess-step">{{ getStepLabel(currentAssessment.current_step) }}</div>
        </div>
        <van-button
          type="primary"
          size="small"
          round
          class="btn-primary"
          @click="goToAssessment(currentAssessment)"
        >
          {{ getActionButton(currentAssessment) }}
        </van-button>
      </div>

      <!-- 最近考核列表 -->
      <div class="card">
        <div class="section-title">最近考核</div>
        <div v-if="assessments.length === 0" class="empty-wrapper">
          <van-empty description="暂无考核记录" />
        </div>
        <div
          v-for="item in assessments.slice(0, 5)"
          :key="item.id"
          class="assess-list-item"
          @click="goToAssessment(item)"
        >
          <div class="assess-list-left">
            <div class="assess-list-name">{{ item.plan_name }}</div>
            <div class="assess-list-meta">{{ item.cycle_type }}</div>
          </div>
          <div class="assess-list-right">
            <span :class="`status-tag ${getStatusClass(item.status)}`">
              {{ getStatusLabel(item.status) }}
            </span>
            <van-icon name="arrow" color="#999" />
          </div>
        </div>
      </div>
    </div>

    <!-- 底部弹出菜单 -->
    <van-action-sheet
      v-model:show="showMenu"
      :actions="menuActions"
      cancel-text="取消"
      close-on-click-action
      @select="onMenuSelect"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { getMyAssessments } from '../api/evaluation'
import { showToast } from 'vant'

const router = useRouter()
const userStore = useUserStore()
const assessments = ref([])
const loading = ref(false)
const showMenu = ref(false)

const roleLabel = computed(() => {
  const map = { admin: '管理员', hr: 'HR', manager: '管理者', employee: '员工' }
  return map[userStore.role] || '员工'
})

const currentAssessment = computed(() => {
  return assessments.value.find(a =>
    a.status !== 'locked' && a.status !== 'archived' && a.status !== 'not_submitted'
  )
})

const pendingCount = computed(() => {
  // 只统计需要自己操作的考核：待自评、已退回
  return assessments.value.filter(a =>
    a.status === 'pending' || a.status === 'returned'
  ).length
})

const menuActions = computed(() => {
  const actions = [
    { name: '我的考核', path: '/employee/assessments' },
    { name: '历史记录', path: '/employee/history' }
  ]
  if (userStore.isManager || userStore.isAdmin) {
    actions.push(
      { name: '管理考核计划', path: '/manager/plans' },
      { name: '审批列表', path: '/manager/approvals' },
      { name: '下属管理', path: '/manager/subordinates' }
    )
  }
  if (userStore.isHR || userStore.isAdmin) {
    actions.push(
      { name: '模板管理', path: '/hr/templates' },
      { name: 'HR终审', path: '/hr/review' },
      { name: '数据概览', path: '/hr/dashboard' },
      { name: '数据导出', path: '/hr/export' }
    )
  }
  if (userStore.isAdmin) {
    actions.push(
      { name: '组织架构同步', path: '/admin/org-sync' }
    )
  }
  actions.push({ name: '退出登录', color: '#ee0a24' })
  return actions
})

const statusMap = {
  pending: '待自评',
  returned: '已退回',
  self_eval_submitted: '待上级评估',
  manager_eval_submitted: '待VP审批',
  vp_approved: '待HR终审',
  hr_approved: '已发布',
  locked: '已锁定',
  not_submitted: '未提交'
}

const stepMap = {
  self_eval: '自评阶段',
  manager_eval: '上级评估阶段',
  vp_approval: 'VP审批阶段',
  hr_final: 'HR终审阶段',
  done: '已完成'
}

function getStatusLabel(status) {
  return statusMap[status] || status
}

function getStepLabel(step) {
  return stepMap[step] || step
}

function getStatusClass(status) {
  if (status === 'pending' || status === 'returned') return 'status-pending'
  if (status === 'self_eval_submitted') return 'status-self-eval'
  if (status === 'manager_eval_submitted') return 'status-manager-eval'
  if (status === 'hr_approved') return 'status-completed'
  if (status === 'locked') return 'status-completed'
  return 'status-pending'
}

function getActionButton(item) {
  if (item.status === 'pending' || item.status === 'returned') return '去自评'
  if (item.status === 'self_eval_submitted') return '查看详情'
  if (item.status === 'locked' || item.status === 'hr_approved') return '查看结果'
  return '查看详情'
}

function goToAssessment(item) {
  if (item.status === 'locked' || item.status === 'hr_approved') {
    router.push(`/employee/result/${item.id}`)
  } else if (item.status === 'pending' || item.status === 'returned') {
    router.push(`/employee/self-eval/${item.id}`)
  } else {
    router.push(`/employee/result/${item.id}`)
  }
}

function onMenuSelect(action) {
  if (action.color === '#ee0a24') {
    userStore.logout()
    return
  }
  if (action.path) {
    router.push(action.path)
  }
}

onMounted(async () => {
  if (!userStore.isLoggedIn) return
  try {
    const res = await getMyAssessments()
    assessments.value = res || []
  } catch (e) {
    // ignore
  }
})
</script>

<style scoped>
.user-card {
  display: flex;
  align-items: center;
  gap: 12px;
}
.user-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 700;
  flex-shrink: 0;
}
.user-info {
  flex: 1;
}
.user-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}
.user-dept {
  font-size: 13px;
  color: #999;
  margin-top: 2px;
}
.quick-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-bottom: 12px;
}
.quick-item {
  background: #fff;
  border-radius: 12px;
  padding: 16px 8px;
  text-align: center;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
  cursor: pointer;
}
.quick-item:active {
  background: #f5f5f5;
}
.quick-icon {
  font-size: 28px;
  margin-bottom: 6px;
}
.quick-item span {
  font-size: 12px;
  color: #666;
}
.assess-info {
  margin-bottom: 12px;
}
.assess-name {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin-bottom: 6px;
}
.assess-step {
  font-size: 13px;
  color: #999;
  margin-top: 4px;
}
.assess-list-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
}
.assess-list-item:last-child {
  border-bottom: none;
}
.assess-list-left {
  flex: 1;
}
.assess-list-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}
.assess-list-meta {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}
.assess-list-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.nav-icon {
  padding: 4px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s;
}
.nav-icon:active {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(0.95);
}
</style>

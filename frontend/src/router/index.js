import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '../utils/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { title: '登录', noAuth: true }
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue'),
    meta: { title: '首页' }
  },
  {
    path: '/employee/assessments',
    name: 'AssessmentList',
    component: () => import('../views/employee/AssessmentList.vue'),
    meta: { title: '我的考核' }
  },
  {
    path: '/employee/self-eval/:id',
    name: 'SelfEval',
    component: () => import('../views/employee/SelfEval.vue'),
    meta: { title: '自评填写' }
  },
  {
    path: '/employee/result/:id',
    name: 'ResultView',
    component: () => import('../views/employee/ResultView.vue'),
    meta: { title: '考核结果' }
  },
  {
    path: '/employee/history',
    name: 'History',
    component: () => import('../views/employee/History.vue'),
    meta: { title: '历史记录' }
  },
  {
    path: '/manager/plans',
    name: 'PlanManage',
    component: () => import('../views/manager/PlanManage.vue'),
    meta: { title: '考核计划', roles: ['admin', 'manager'] }
  },
  {
    path: '/manager/approvals',
    name: 'ApprovalList',
    component: () => import('../views/manager/ApprovalList.vue'),
    meta: { title: '审批列表', roles: ['admin', 'manager'] }
  },
  {
    path: '/manager/eval/:id',
    name: 'ManagerEval',
    component: () => import('../views/manager/ManagerEval.vue'),
    meta: { title: '下属评估', roles: ['admin', 'manager'] }
  },
  {
    path: '/manager/subordinates',
    name: 'SubordinateList',
    component: () => import('../views/manager/SubordinateList.vue'),
    meta: { title: '下属列表', roles: ['admin', 'manager'] }
  },
  {
    path: '/hr/templates',
    name: 'TemplateManage',
    component: () => import('../views/hr/TemplateManage.vue'),
    meta: { title: '模板管理', roles: ['admin', 'hr'] }
  },
  {
    path: '/hr/review',
    name: 'HRReview',
    component: () => import('../views/hr/HRReview.vue'),
    meta: { title: 'HR终审', roles: ['admin', 'hr'] }
  },
  {
    path: '/hr/dashboard',
    name: 'Dashboard',
    component: () => import('../views/hr/Dashboard.vue'),
    meta: { title: '数据概览', roles: ['admin', 'hr'] }
  },
  {
    path: '/hr/export',
    name: 'DataExport',
    component: () => import('../views/hr/DataExport.vue'),
    meta: { title: '数据导出', roles: ['admin', 'hr'] }
  },
  {
    path: '/admin/org-sync',
    name: 'OrgSync',
    component: () => import('../views/admin/OrgSync.vue'),
    meta: { title: '组织架构同步', roles: ['admin'] }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title || '绩效管理系统'

  // 如果 URL 中有 token 参数，允许通过（App.vue 会处理）
  const urlParams = new URLSearchParams(window.location.search)
  if (urlParams.get('token')) {
    next()
    return
  }

  const token = getToken()
  if (!to.meta.noAuth && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router

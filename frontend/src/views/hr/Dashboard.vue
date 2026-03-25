<template>
  <div class="page-container">
    <van-nav-bar title="数据概览" left-arrow @click-left="$router.back()" fixed placeholder />

    <div class="page-content" v-if="overview">
      <div class="stat-grid">
        <div class="stat-item card">
          <div class="stat-value">{{ overview.total_employees || 0 }}</div>
          <div class="stat-label">在职员工</div>
        </div>
        <div class="stat-item card">
          <div class="stat-value">{{ overview.total_departments || 0 }}</div>
          <div class="stat-label">部门数</div>
        </div>
        <div class="stat-item card">
          <div class="stat-value accent">{{ overview.active_plans || 0 }}</div>
          <div class="stat-label">进行中考核</div>
        </div>
        <div class="stat-item card">
          <div class="stat-value success">{{ overview.submitted_count || 0 }}</div>
          <div class="stat-label">已提交自评</div>
        </div>
      </div>

      <div class="card">
        <div class="section-title">考核完成进度</div>
        <div class="progress-section" v-if="planStats.length > 0">
          <div v-for="ps in planStats" :key="ps.name" class="progress-item">
            <div class="progress-header">
              <span class="progress-name">{{ ps.name }}</span>
              <span class="progress-pct">{{ ps.percent }}%</span>
            </div>
            <van-progress :percentage="ps.percent" :color="ps.percent >= 80 ? '#07c160' : '#1890ff'" stroke-width="8" />
            <div class="progress-meta">
              <span>已评 {{ ps.done }} 人</span>
              <span>共 {{ ps.total }} 人</span>
            </div>
          </div>
        </div>
        <div v-else class="empty-wrapper">
          <p style="color:#999;font-size:13px;">暂无考核数据</p>
        </div>
      </div>

      <div class="card">
        <div class="section-title">部门评分概览</div>
        <div v-for="dept in deptStats" :key="dept.name" class="dept-row">
          <div class="dept-name">{{ dept.name }}</div>
          <div class="dept-right">
            <span class="dept-avg">{{ dept.avg_score || '-' }}</span>
            <span class="dept-count">{{ dept.count }} 人</span>
          </div>
        </div>
        <div v-if="deptStats.length === 0" class="empty-wrapper">
          <p style="color:#999;font-size:13px;">暂无数据</p>
        </div>
      </div>

      <div class="card">
        <div class="section-title">最近动态</div>
        <div v-for="(log, idx) in recentLogs" :key="idx" class="timeline-item">
          <div class="timeline-content">{{ log.content }}</div>
          <div class="timeline-time">{{ log.time }}</div>
        </div>
        <div v-if="recentLogs.length === 0" class="empty-wrapper">
          <p style="color:#999;font-size:13px;">暂无动态</p>
        </div>
      </div>
    </div>

    <van-loading v-if="loading" class="page-loading" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getDashboardOverview } from '../../api/dashboard'
import request from '../../api/request'

const loading = ref(false)
const overview = ref(null)
const planStats = ref([])
const deptStats = ref([])
const recentLogs = ref([])

onMounted(async () => {
  loading.value = true
  try {
    const res = await getDashboardOverview()
    overview.value = res || {}
    try {
      const detail = await request.get('/api/dashboard/detail')
      planStats.value = (detail?.plan_stats || []).map(p => ({
        ...p,
        percent: p.total > 0 ? Math.round(p.done / p.total * 100) : 0
      }))
      deptStats.value = detail?.dept_stats || []
      recentLogs.value = detail?.recent_logs || []
    } catch {
      // detail API not ready
    }
  } catch {
    overview.value = { total_employees: 0, total_departments: 0, active_plans: 0, submitted_count: 0 }
  }
  loading.value = false
})
</script>

<style scoped>
.stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px; }
.stat-item { text-align: center; padding: 16px 8px; }
.stat-value { font-size: 28px; font-weight: 700; color: var(--primary-color); }
.stat-value.accent { color: #fa8c16; }
.stat-value.success { color: #07c160; }
.stat-label { font-size: 12px; color: #999; margin-top: 4px; }
.progress-item { margin-bottom: 14px; }
.progress-item:last-child { margin-bottom: 0; }
.progress-header { display: flex; justify-content: space-between; margin-bottom: 6px; }
.progress-name { font-size: 14px; font-weight: 500; color: #333; }
.progress-pct { font-size: 14px; font-weight: 600; color: var(--primary-color); }
.progress-meta { display: flex; justify-content: space-between; font-size: 12px; color: #bbb; margin-top: 4px; }
.dept-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #f5f5f5; }
.dept-row:last-child { border-bottom: none; }
.dept-name { font-size: 14px; color: #333; }
.dept-right { display: flex; gap: 12px; align-items: center; }
.dept-avg { font-size: 16px; font-weight: 600; color: var(--primary-color); }
.dept-count { font-size: 12px; color: #999; }
.page-loading { display: flex; justify-content: center; padding: 40px; }
</style>

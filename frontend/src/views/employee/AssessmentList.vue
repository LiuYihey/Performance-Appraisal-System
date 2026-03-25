<template>
  <div class="page-container">
    <van-nav-bar title="我的考核" left-arrow @click-left="$router.back()" fixed placeholder />

    <div class="page-content">
      <van-tabs v-model:active="activeTab" sticky>
        <van-tab title="进行中" name="active">
          <div v-if="activeList.length === 0" class="empty-wrapper">
            <van-empty description="暂无进行中的考核" />
          </div>
          <div v-for="item in activeList" :key="item.id" class="card assess-card" @click="goDetail(item)">
            <div class="assess-header">
              <span class="assess-title">{{ item.plan_name }}</span>
              <span :class="`status-tag ${getStatusClass(item.status)}`">
                {{ getStatusLabel(item.status) }}
              </span>
            </div>
            <div class="assess-meta">
              <span>周期：{{ item.cycle_type }}</span>
              <span v-if="item.final_score">得分：{{ item.final_score }}</span>
            </div>
            <div class="assess-action-text">{{ getActionText(item) }} →</div>
          </div>
        </van-tab>
        <van-tab title="已完成" name="completed">
          <div v-if="completedList.length === 0" class="empty-wrapper">
            <van-empty description="暂无已完成的考核" />
          </div>
          <div v-for="item in completedList" :key="item.id" class="card assess-card" @click="goResult(item)">
            <div class="assess-header">
              <span class="assess-title">{{ item.plan_name }}</span>
              <span class="status-tag status-completed">{{ getStatusLabel(item.status) }}</span>
            </div>
            <div class="assess-meta">
              <span>周期：{{ item.cycle_type }}</span>
              <span v-if="item.final_score" class="final-score">最终得分：{{ item.final_score }}</span>
            </div>
          </div>
        </van-tab>
      </van-tabs>
    </div>

    <van-loading v-if="loading" class="page-loading" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getMyAssessments } from '../../api/evaluation'

const router = useRouter()
const activeTab = ref('active')
const assessments = ref([])
const loading = ref(false)

const activeList = computed(() =>
  assessments.value.filter(a => a.status !== 'locked' && a.status !== 'hr_approved')
)
const completedList = computed(() =>
  assessments.value.filter(a => a.status === 'locked' || a.status === 'hr_approved')
)

const statusMap = {
  pending: '待自评', returned: '已退回', self_eval_submitted: '待上级评估',
  manager_eval_submitted: '待审批', vp_approved: '待HR终审',
  hr_approved: '已发布', locked: '已锁定', not_submitted: '未提交'
}

function getStatusLabel(s) { return statusMap[s] || s }
function getStatusClass(s) {
  if (s === 'pending' || s === 'returned') return 'status-pending'
  if (s === 'self_eval_submitted' || s === 'manager_eval_submitted') return 'status-self-eval'
  return 'status-completed'
}
function getActionText(item) {
  if (item.status === 'pending' || item.status === 'returned') return '去填写自评'
  return '查看详情'
}
function goDetail(item) {
  if (item.status === 'pending' || item.status === 'returned') {
    router.push(`/employee/self-eval/${item.id}`)
  } else {
    router.push(`/employee/result/${item.id}`)
  }
}
function goResult(item) {
  router.push(`/employee/result/${item.id}`)
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await getMyAssessments()
    assessments.value = res || []
  } catch (e) { /* ignore */ }
  loading.value = false
})
</script>

<style scoped>
.assess-card { cursor: pointer; }
.assess-card:active { background: #f9f9f9; }
.assess-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.assess-title { font-size: 15px; font-weight: 600; color: #333; }
.assess-meta { display: flex; gap: 16px; font-size: 13px; color: #999; }
.final-score { color: var(--primary-color); font-weight: 600; }
.assess-action-text { margin-top: 10px; font-size: 13px; color: var(--primary-color); }
.page-loading { display: flex; justify-content: center; padding: 40px; }
</style>

<template>
  <div class="page-container">
    <van-nav-bar title="审批列表" left-arrow @click-left="$router.back()" fixed placeholder />

    <div class="page-content">
      <van-tabs v-model:active="activeTab">
        <van-tab title="待处理" name="pending">
          <div v-if="pendingList.length === 0" class="empty-wrapper">
            <van-empty description="暂无待处理事项" />
          </div>
          <div v-for="item in pendingList" :key="item.id" class="card approval-card" @click="goAction(item)">
            <div class="approval-header">
              <span class="approval-name">{{ item.employee_name || '员工' }}</span>
              <span class="status-tag status-pending">{{ item.status_label }}</span>
            </div>
            <div class="approval-body">
              <div class="approval-row"><span class="label">考核计划</span><span>{{ item.plan_name }}</span></div>
              <div class="approval-row"><span class="label">当前步骤</span><span>{{ item.step_label }}</span></div>
            </div>
            <div class="approval-action-text">去处理 →</div>
          </div>
        </van-tab>
        <van-tab title="已处理" name="done">
          <div v-if="doneList.length === 0" class="empty-wrapper">
            <van-empty description="暂无已处理事项" />
          </div>
          <div v-for="item in doneList" :key="item.id" class="card approval-card" @click="goDetail(item)">
            <div class="approval-header">
              <span class="approval-name">{{ item.employee_name || '员工' }}</span>
              <span class="status-tag status-completed">{{ item.status_label }}</span>
            </div>
            <div class="approval-body">
              <div class="approval-row"><span class="label">考核计划</span><span>{{ item.plan_name }}</span></div>
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
import request from '../../api/request'

const router = useRouter()
const activeTab = ref('pending')
const loading = ref(false)
const approvals = ref([])

const statusLabelMap = {
  pending: '待处理', self_eval_submitted: '待上级评估',
  manager_eval_submitted: '待审批', returned: '已退回',
  vp_approved: '待HR终审', hr_approved: '已发布', locked: '已锁定'
}
const stepLabelMap = {
  self_eval: '自评阶段', manager_eval: '上级评估阶段',
  vp_approval: 'VP审批阶段', hr_final: 'HR终审阶段', done: '已完成'
}

const pendingList = computed(() =>
  approvals.value.filter(a => a.status === 'self_eval_submitted' || a.status === 'pending')
)
const doneList = computed(() =>
  approvals.value.filter(a => a.status !== 'self_eval_submitted' && a.status !== 'pending')
)

function goAction(item) {
  if (item.current_step === 'manager_eval') {
    router.push(`/manager/eval/${item.id}`)
  } else {
    router.push(`/employee/result/${item.id}`)
  }
}

function goDetail(item) {
  router.push(`/employee/result/${item.id}`)
}

onMounted(async () => {
  loading.value = true
  try {
    // 获取我需要审批的记录（上级视角：下属已提交自评的）
    const res = await request.get('/api/manager/pending-evals')
    approvals.value = (res || []).map(a => ({
      ...a,
      status_label: statusLabelMap[a.status] || a.status,
      step_label: stepLabelMap[a.current_step] || a.current_step
    }))
  } catch (e) {
    // 接口可能还没实现，显示空
    approvals.value = []
  }
  loading.value = false
})
</script>

<style scoped>
.approval-card { cursor: pointer; }
.approval-card:active { background: #f9f9f9; }
.approval-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.approval-name { font-size: 15px; font-weight: 600; color: #333; }
.approval-row { display: flex; justify-content: space-between; font-size: 13px; color: #666; padding: 3px 0; }
.approval-row .label { color: #999; }
.approval-action-text { margin-top: 10px; font-size: 13px; color: var(--primary-color); }
.page-loading { display: flex; justify-content: center; padding: 40px; }
</style>

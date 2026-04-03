<template>
  <div class="page-container">
    <van-nav-bar title="考核计划" left-arrow @click-left="$router.back()" fixed placeholder>
      <template #right>
        <van-icon name="plus" size="22" color="#fff" @click="showCreate = true" class="nav-icon" />
      </template>
    </van-nav-bar>

    <div class="page-content">
      <van-tabs v-model:active="tab">
        <van-tab title="进行中" name="running">
          <div v-for="p in runningPlans" :key="p.id" class="card plan-card">
            <div class="plan-header">
              <span class="plan-name">{{ p.name }}</span>
              <span class="status-tag status-self-eval">进行中</span>
            </div>
            <div class="plan-body">
              <div class="plan-row"><span class="label">周期</span><span>{{ cycleLabel(p.cycle_type) }}</span></div>
              <div class="plan-row"><span class="label">创建者</span><span>{{ p.created_by_name || '未知' }}</span></div>
              <div class="plan-row"><span class="label">自评截止</span><span>{{ p.self_eval_end || '未设置' }}</span></div>
              <div class="plan-row"><span class="label">开始日期</span><span>{{ p.start_date?.split('T')[0] }}</span></div>
            </div>
          </div>
          <div v-if="runningPlans.length === 0" class="empty-wrapper">
            <van-empty description="暂无进行中的计划" />
          </div>
        </van-tab>
        <van-tab title="全部" name="all">
          <div v-for="p in allPlans" :key="p.id" class="card plan-card">
            <div class="plan-header">
              <span class="plan-name">{{ p.name }}</span>
              <span :class="`status-tag ${getStatusClass(p.status)}`">{{ p.status }}</span>
            </div>
            <div class="plan-body">
              <div class="plan-row"><span class="label">周期</span><span>{{ cycleLabel(p.cycle_type) }}</span></div>
              <div class="plan-row"><span class="label">创建者</span><span>{{ p.created_by_name || '未知' }}</span></div>
              <div class="plan-row"><span class="label">开始</span><span>{{ p.start_date?.split('T')[0] }}</span></div>
              <div class="plan-row"><span class="label">结束</span><span>{{ p.end_date?.split('T')[0] }}</span></div>
            </div>
          </div>
          <div v-if="allPlans.length === 0" class="empty-wrapper">
            <van-empty description="暂无考核计划" />
          </div>
        </van-tab>
      </van-tabs>
    </div>

    <!-- 创建计划弹窗 -->
    <van-popup v-model:show="showCreate" position="bottom" round :style="{ maxHeight: '85%' }">
      <div class="popup-content">
        <div class="popup-title">创建考核计划</div>
        <van-form @submit="onCreatePlan">
          <van-field v-model="form.name" label="计划名称" placeholder="如：2026年Q1绩效考核" required />
          <van-field label="周期类型" required>
            <template #input>
              <van-radio-group v-model="form.cycle_type" direction="horizontal">
                <van-radio name="monthly">月度</van-radio>
                <van-radio name="quarterly">季度</van-radio>
                <van-radio name="yearly">年度</van-radio>
              </van-radio-group>
            </template>
          </van-field>
          <van-field v-model="form.start_date" label="开始日期" type="date" required />
          <van-field v-model="form.end_date" label="结束日期" type="date" required />
          <van-field v-model="form.self_eval_start" label="自评开始" type="date" />
          <van-field v-model="form.self_eval_end" label="自评截止" type="date" />
          <van-field v-model="form.manager_eval_end" label="上级评截止" type="date" />

          <div class="section-title" style="padding:16px 16px 8px;">审批链</div>
          <van-checkbox-group v-model="form.approval_chain">
            <van-cell-group>
              <van-cell>
                <template #title>
                  <van-checkbox name="direct_leader" shape="square">直属上级</van-checkbox>
                </template>
              </van-cell>
              <van-cell>
                <template #title>
                  <van-checkbox name="vp" shape="square">VP 审批</van-checkbox>
                </template>
              </van-cell>
              <van-cell>
                <template #title>
                  <van-checkbox name="hr" shape="square">HR 终审</van-checkbox>
                </template>
              </van-cell>
            </van-cell-group>
          </van-checkbox-group>

          <!-- 选择模板 -->
          <van-field label="评估模板" required>
            <template #input>
              <select v-model="form.template_id" style="border:1px solid #eee;padding:4px 8px;border-radius:4px;width:100%;">
                <option v-for="t in templates" :key="t.id" :value="t.id">{{ t.name }}</option>
              </select>
            </template>
          </van-field>

          <div class="popup-actions">
            <van-button block type="primary" native-type="submit" round :loading="creating">创建计划</van-button>
          </div>
        </van-form>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getPlans, createPlan } from '../../api/plans'
import { getTemplates } from '../../api/templates'
import { showToast } from 'vant'

const tab = ref('running')
const plans = ref([])
const templates = ref([])
const showCreate = ref(false)
const creating = ref(false)

const form = ref({
  name: '', cycle_type: 'quarterly', start_date: '', end_date: '',
  self_eval_start: '', self_eval_end: '', manager_eval_end: '',
  template_id: null, approval_chain: ['direct_leader', 'hr']
})

const runningPlans = computed(() => plans.value.filter(p => p.status === 'running'))
const allPlans = computed(() => plans.value)

const cycleLabel = (c) => ({ monthly: '月度', quarterly: '季度', yearly: '年度' }[c] || c)
function getStatusClass(s) {
  if (s === 'running') return 'status-self-eval'
  if (s === 'published' || s === 'archived') return 'status-completed'
  return 'status-pending'
}

async function onCreatePlan() {
  if (!form.value.name || !form.value.start_date || !form.value.end_date) {
    showToast('请填写必填项')
    return
  }
  creating.value = true
  try {
    await createPlan(form.value)
    showToast({ message: '创建成功', type: 'success' })
    showCreate.value = false
    form.value = { name: '', cycle_type: 'quarterly', start_date: '', end_date: '', self_eval_start: '', self_eval_end: '', manager_eval_end: '', template_id: null, approval_chain: ['direct_leader', 'hr'] }
    await loadPlans()
  } catch (e) {
    showToast(e.response?.data?.detail || '创建失败')
  }
  creating.value = false
}

async function loadPlans() {
  try {
    const res = await getPlans()
    plans.value = res || []
  } catch (e) { /* ignore */ }
}

onMounted(async () => {
  await Promise.all([loadPlans(), (async () => {
    try {
      const res = await getTemplates()
      templates.value = res || []
      if (templates.value.length > 0) form.value.template_id = templates.value[0].id
    } catch (e) { /* ignore */ }
  })()])
})
</script>

<style scoped>
.plan-card:active { background: #f9f9f9; }
.plan-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.plan-name { font-size: 15px; font-weight: 600; color: #333; }
.plan-row { display: flex; justify-content: space-between; font-size: 13px; color: #666; padding: 3px 0; }
.plan-row .label { color: #999; }
.popup-content { padding: 16px; }
.popup-title { font-size: 16px; font-weight: 600; text-align: center; margin-bottom: 16px; }
.popup-actions { padding: 16px 0; }
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

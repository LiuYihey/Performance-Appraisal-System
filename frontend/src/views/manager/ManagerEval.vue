<template>
  <div class="page-container">
    <van-nav-bar title="下属评估" left-arrow @click-left="$router.back()" fixed placeholder />

    <div class="page-content" v-if="detail">
      <!-- 员工信息 -->
      <div class="card">
        <div class="emp-info">
          <div class="emp-avatar">{{ (detail.employee_name || '?').charAt(0) }}</div>
          <div class="emp-text">
            <div class="emp-name">{{ detail.employee_name }}</div>
            <div class="emp-meta">{{ detail.plan_name }} · {{ detail.current_step }}</div>
          </div>
        </div>
      </div>

      <!-- 员工自评（只读） -->
      <div class="card" v-if="selfEvals.length > 0">
        <div class="section-title">员工自评</div>
        <div v-for="(ev, idx) in selfEvals" :key="idx" class="dim-item">
          <div class="dim-header">
            <span class="dim-name">{{ ev.dimension }} <span class="dim-weight">权重{{ ev.weight }}%</span></span>
            <span class="dim-score">{{ ev.score }}</span>
          </div>
          <div class="dim-comment" v-if="ev.comment">{{ ev.comment }}</div>
        </div>
      </div>

      <!-- 上级评分 -->
      <div class="card">
        <div class="section-title">上级评分</div>
        <div v-for="(dim, idx) in dimensions" :key="idx" class="dim-form-item">
          <div class="dim-form-header">
            <span class="dim-form-name">{{ dim.name }}</span>
            <span class="dim-weight">权重 {{ dim.weight }}%</span>
          </div>
          <van-field v-model="dim.score" type="number" label="评分" placeholder="0 - 100" />
          <van-field v-model="dim.comment" type="textarea" label="评语" placeholder="请填写评语..." rows="2" autosize />
        </div>
      </div>

      <!-- 整体评语 -->
      <div class="card">
        <div class="section-title">整体评语</div>
        <van-field v-model="overallComment" type="textarea" placeholder="请填写对该员工的综合评价..." rows="3" autosize maxlength="500" show-word-limit />
      </div>

      <!-- 退回原因 -->
      <div class="card" v-if="action === 'return'">
        <div class="section-title">退回原因</div>
        <van-field v-model="returnComment" type="textarea" placeholder="请填写退回原因..." rows="2" autosize required />
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="floating-bottom" v-if="detail">
      <div class="btn-row">
        <van-button plain type="danger" round :loading="submitting" @click="action = 'return'">
          退回
        </van-button>
        <van-button type="primary" round :loading="submitting" @click="action = 'approve'; handleSubmit()">
          通过
        </van-button>
      </div>
    </div>

    <van-loading v-if="loading" class="page-loading" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getEvalRecord, submitManagerEval } from '../../api/evaluation'
import { showToast, showConfirmDialog } from 'vant'

const route = useRoute()
const router = useRouter()
const recordId = parseInt(route.params.id)

const loading = ref(false)
const submitting = ref(false)
const detail = ref(null)
const dimensions = ref([])
const overallComment = ref('')
const returnComment = ref('')
const action = ref('approve')

const selfEvals = computed(() =>
  (detail.value?.evaluations || []).filter(e => e.evaluator_role === 'self')
)

onMounted(async () => {
  loading.value = true
  try {
    const res = await getEvalRecord(recordId)
    detail.value = res
    // 用员工自评的维度初始化上级评分表单
    const selfDims = selfEvals.value
    if (selfDims.length > 0) {
      dimensions.value = selfDims.map(d => ({
        name: d.dimension,
        weight: d.weight,
        score: '',
        comment: ''
      }))
    } else {
      dimensions.value = [
        { name: '目标达成', weight: 40, score: '', comment: '' },
        { name: '能力发展', weight: 30, score: '', comment: '' },
        { name: '价值观', weight: 30, score: '', comment: '' }
      ]
    }
  } catch (e) {
    showToast('加载失败')
  }
  loading.value = false
})

async function handleSubmit() {
  if (action.value === 'return') {
    if (!returnComment.value) {
      showToast('请填写退回原因')
      return
    }
    try {
      await showConfirmDialog({ title: '确认退回', message: '确认退回给员工重新填写？' })
    } catch { return }
  } else {
    const valid = dimensions.value.every(d => d.score && d.score >= 0 && d.score <= 100)
    if (!valid) { showToast('请为所有维度评分（0-100）'); return }
    try {
      await showConfirmDialog({ title: '确认提交', message: '确认提交上级评估？' })
    } catch { return }
  }

  submitting.value = true
  try {
    const body = {
      record_id: recordId,
      action: action.value,
      return_comment: returnComment.value || undefined,
      scores: action.value === 'approve' ? dimensions.value.map(d => ({
        dimension_name: d.name, weight: d.weight, score: parseFloat(d.score), comment: d.comment
      })) : []
    }
    const res = await submitManagerEval(body)
    showToast({ message: action.value === 'return' ? '已退回' : '评估已提交', type: 'success' })
    setTimeout(() => router.replace('/manager/approvals'), 1000)
  } catch (e) {
    showToast(e.response?.data?.detail || '操作失败')
  }
  submitting.value = false
}
</script>

<style scoped>
.emp-info { display: flex; align-items: center; gap: 12px; }
.emp-avatar { width: 44px; height: 44px; border-radius: 50%; background: linear-gradient(135deg, #52c41a, #73d13d); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: 700; }
.emp-name { font-size: 16px; font-weight: 600; color: #333; }
.emp-meta { font-size: 13px; color: #999; margin-top: 2px; }
.dim-comment { font-size: 13px; color: #666; margin-top: 4px; line-height: 1.5; padding-left: 12px; border-left: 2px solid #ebedf0; }
.btn-row { display: flex; gap: 12px; }
.btn-row .van-button { flex: 1; }
.page-loading { display: flex; justify-content: center; padding: 40px; }
</style>

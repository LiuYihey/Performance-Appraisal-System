<template>
  <div class="page-container">
    <van-nav-bar title="HR终审" left-arrow @click-left="$router.back()" fixed placeholder />

    <div class="page-content">
      <van-tabs v-model:active="activeTab">
        <van-tab title="待终审" name="pending">
          <div v-if="pendingList.length === 0" class="empty-wrapper">
            <van-empty description="暂无待终审记录" />
          </div>
          <div v-for="item in pendingList" :key="item.id" class="card review-card" @click="goReview(item)">
            <div class="review-header">
              <span class="review-name">{{ item.employee_name || '员工' }}</span>
              <span class="status-tag status-hr-review">待终审</span>
            </div>
            <div class="review-body">
              <div class="review-row"><span class="label">考核计划</span><span>{{ item.plan_name }}</span></div>
              <div class="review-row" v-if="item.final_score !== null && item.final_score !== undefined">
                <span class="label">综合得分</span><span class="score-text">{{ item.final_score }}</span>
              </div>
            </div>
            <div class="review-action-text">去终审</div>
          </div>
        </van-tab>
        <van-tab title="已终审" name="done">
          <div v-if="doneList.length === 0" class="empty-wrapper">
            <van-empty description="暂无已终审记录" />
          </div>
          <div v-for="item in doneList" :key="item.id" class="card review-card">
            <div class="review-header">
              <span class="review-name">{{ item.employee_name || '员工' }}</span>
              <span class="status-tag status-completed">已终审</span>
            </div>
            <div class="review-body">
              <div class="review-row"><span class="label">考核计划</span><span>{{ item.plan_name }}</span></div>
              <div class="review-row" v-if="item.final_score">
                <span class="label">最终得分</span><span class="score-text">{{ item.final_score }}</span>
              </div>
            </div>
          </div>
        </van-tab>
      </van-tabs>
    </div>

    <van-popup v-model:show="showReview" position="bottom" round :style="{ maxHeight: '80%' }">
      <div class="popup-content" v-if="currentRecord">
        <div class="popup-title">HR终审 - {{ currentRecord.employee_name }}</div>
        <div class="card" style="margin-bottom:12px;">
          <div class="section-title">评估详情</div>
          <div v-for="(ev, idx) in currentRecord.evaluations" :key="idx" class="dim-item">
            <div class="dim-header">
              <span class="dim-name">{{ ev.dimension }}</span>
              <span class="dim-score">{{ ev.score }}</span>
            </div>
            <div class="dim-comment" v-if="ev.comment">{{ ev.evaluator_role }}：{{ ev.comment }}</div>
          </div>
          <div v-if="!currentRecord.evaluations || currentRecord.evaluations.length === 0" class="empty-wrapper">
            <p style="color:#999;font-size:13px;">暂无评分</p>
          </div>
        </div>
        <van-field v-model="finalScore" type="number" label="最终得分" placeholder="0 - 100" />
        <van-field v-model="finalComment" type="textarea" label="终审评语" placeholder="请填写终审意见..." rows="3" autosize maxlength="500" show-word-limit />
        <div class="popup-actions">
          <div class="btn-row">
            <van-button plain type="danger" round @click="handleFinal('return')" :loading="submitting">退回</van-button>
            <van-button type="primary" round @click="handleFinal('approve')" :loading="submitting">通过并发布</van-button>
          </div>
        </div>
      </div>
    </van-popup>

    <van-loading v-if="loading" class="page-loading" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import request from '../../api/request'
import { submitHRFinal } from '../../api/evaluation'
import { showToast, showConfirmDialog } from 'vant'

const activeTab = ref('pending')
const loading = ref(false)
const submitting = ref(false)
const records = ref([])
const showReview = ref(false)
const currentRecord = ref(null)
const finalScore = ref('')
const finalComment = ref('')

const pendingList = computed(() =>
  records.value.filter(r => r.status === 'vp_approved' || r.status === 'manager_eval_submitted')
)
const doneList = computed(() =>
  records.value.filter(r => r.status === 'locked' || r.status === 'hr_approved')
)

function goReview(item) {
  currentRecord.value = item
  finalScore.value = item.final_score ? String(item.final_score) : ''
  finalComment.value = item.final_comment || ''
  showReview.value = true
}

async function handleFinal(action) {
  if (action === 'return') {
    if (!finalComment.value) { showToast('退回请填写原因'); return }
    try { await showConfirmDialog({ title: '确认退回' }) } catch { return }
  } else {
    if (!finalScore.value) { showToast('请填写最终得分'); return }
    const score = parseFloat(finalScore.value)
    if (score < 0 || score > 100) { showToast('得分范围 0-100'); return }
    try { await showConfirmDialog({ title: '确认发布', message: '发布后员工将收到结果通知' }) } catch { return }
  }
  submitting.value = true
  try {
    await submitHRFinal({
      record_id: currentRecord.value.id,
      action,
      final_score: action === 'approve' ? parseFloat(finalScore.value) : null,
      final_comment: finalComment.value || undefined
    })
    showToast({ message: action === 'approve' ? '已发布' : '已退回', type: 'success' })
    showReview.value = false
    await loadRecords()
  } catch (e) {
    showToast(e.response?.data?.detail || '操作失败')
  }
  submitting.value = false
}

async function loadRecords() {
  loading.value = true
  try {
    const res = await request.get('/api/hr/pending-reviews')
    records.value = res || []
  } catch {
    records.value = []
  }
  loading.value = false
}

onMounted(loadRecords)
</script>

<style scoped>
.review-card { cursor: pointer; }
.review-card:active { background: #f9f9f9; }
.review-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.review-name { font-size: 15px; font-weight: 600; color: #333; }
.review-row { display: flex; justify-content: space-between; font-size: 13px; color: #666; padding: 3px 0; }
.review-row .label { color: #999; }
.score-text { color: var(--primary-color); font-weight: 600; }
.review-action-text { margin-top: 8px; font-size: 13px; color: var(--primary-color); }
.popup-content { padding: 16px; }
.popup-title { font-size: 16px; font-weight: 600; text-align: center; margin-bottom: 12px; }
.popup-actions { padding: 12px 0; }
.btn-row { display: flex; gap: 12px; }
.btn-row .van-button { flex: 1; }
.dim-comment { font-size: 13px; color: #666; margin-top: 2px; }
.page-loading { display: flex; justify-content: center; padding: 40px; }
</style>

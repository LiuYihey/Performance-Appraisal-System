<template>
  <div class="page-container">
    <van-nav-bar title="考核结果" left-arrow @click-left="$router.back()" fixed placeholder />

    <div class="page-content" v-if="detail">
      <!-- 得分展示 -->
      <div class="card">
        <div class="score-display">
          <div class="score-value" v-if="detail.final_score">{{ detail.final_score }}</div>
          <div class="score-value pending" v-else>待公布</div>
          <div class="score-label">最终得分</div>
        </div>
        <div class="score-comment" v-if="detail.final_comment">
          <div class="section-title">综合评语</div>
          <p>{{ detail.final_comment }}</p>
        </div>
      </div>

      <!-- 评分明细 -->
      <div class="card">
        <div class="section-title">评分明细</div>
        <div v-for="(ev, idx) in detail.evaluations" :key="idx" class="dim-item">
          <div class="dim-header">
            <div>
              <span class="dim-name">{{ ev.dimension }}</span>
              <span class="dim-weight ml-8">权重 {{ ev.weight }}%</span>
            </div>
            <div>
              <span class="role-tag" :class="`role-${ev.evaluator_role}`">{{ getRoleLabel(ev.evaluator_role) }}</span>
              <span class="dim-score ml-8" v-if="ev.score !== null">{{ ev.score }}</span>
            </div>
          </div>
          <div class="dim-comment" v-if="ev.comment">{{ ev.comment }}</div>
        </div>
        <div v-if="!detail.evaluations || detail.evaluations.length === 0" class="empty-wrapper">
          <van-empty description="暂无评分数据" :image-size="60" />
        </div>
      </div>

      <!-- 审批流程 -->
      <div class="card">
        <div class="section-title">审批流程</div>
        <div v-for="(log, idx) in logs" :key="idx" class="timeline-item">
          <div class="timeline-content">{{ getActionText(log.action) }}：{{ log.comment || '-' }}</div>
          <div class="timeline-user">{{ log.approver }} · {{ log.from || '' }} → {{ log.to || '' }}</div>
          <div class="timeline-time">{{ formatTime(log.created_at) }}</div>
        </div>
        <div v-if="logs.length === 0" class="empty-wrapper">
          <p style="color:#999;font-size:13px;">暂无流程记录</p>
        </div>
      </div>
    </div>

    <van-loading v-if="loading" class="page-loading" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getEvalRecord, getEvalLogs } from '../../api/evaluation'

const route = useRoute()
const recordId = parseInt(route.params.id)
const loading = ref(false)
const detail = ref(null)
const logs = ref([])

const roleMap = { self: '自评', manager: '上级评', vp: 'VP评', hr: 'HR评', peer: '同事评' }
function getRoleLabel(r) { return roleMap[r] || r }
function getActionText(a) { return { submit: '提交', approve: '通过', return: '退回' }[a] || a }
function formatTime(t) {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

onMounted(async () => {
  loading.value = true
  try {
    const [d, l] = await Promise.all([getEvalRecord(recordId), getEvalLogs(recordId)])
    detail.value = d
    logs.value = l || []
  } catch (e) { /* ignore */ }
  loading.value = false
})
</script>

<style scoped>
.score-comment { margin-top: 16px; }
.score-comment p { font-size: 14px; color: #666; line-height: 1.6; }
.ml-8 { margin-left: 8px; }
.role-tag { display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 11px; }
.role-self { background: #e6f7ff; color: #1890ff; }
.role-manager { background: #f6ffed; color: #52c41a; }
.role-vp { background: #fff1f0; color: #f5222d; }
.role-hr { background: #f9f0ff; color: #722ed1; }
.dim-comment { font-size: 13px; color: #999; margin-top: 4px; line-height: 1.5; }
.page-loading { display: flex; justify-content: center; padding: 40px; }
</style>

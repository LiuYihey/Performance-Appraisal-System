<template>
  <div class="page-container">
    <van-nav-bar title="自评填写" left-arrow @click-left="$router.back()" fixed placeholder />

    <div class="page-content" v-if="record && plan">
      <!-- 考核信息 -->
      <div class="card">
        <div class="plan-name">{{ plan.name }}</div>
        <div class="plan-meta">{{ plan.cycle_type }} · 截止：{{ plan.self_eval_end || '未设置' }}</div>
      </div>

      <!-- 评分维度 -->
      <div class="card">
        <div class="section-title">评分维度</div>
        <div v-for="(dim, idx) in dimensions" :key="idx" class="dim-form-item">
          <div class="dim-form-header">
            <span class="dim-form-name">{{ dim.name }}</span>
            <span class="dim-weight">权重 {{ dim.weight }}%</span>
          </div>
          <van-field
            v-model="dim.score"
            type="number"
            label="评分"
            placeholder="0 - 100"
            :rules="[{ required: true, message: '请输入评分' }]"
          />
          <van-field
            v-model="dim.comment"
            type="textarea"
            label="评语"
            placeholder="请填写该维度的自我评价..."
            rows="2"
            autosize
          />
        </div>
      </div>

      <!-- 整体自评 -->
      <div class="card">
        <div class="section-title">整体自评</div>
        <van-field
          v-model="overallComment"
          type="textarea"
          placeholder="请填写本期工作总结和自我评价..."
          rows="4"
          autosize
          maxlength="1000"
          show-word-limit
        />
      </div>
    </div>

    <!-- 提交按钮 -->
    <div class="floating-bottom" v-if="record">
      <van-button
        type="primary"
        block
        round
        :loading="submitting"
        :disabled="!canSubmit"
        @click="handleSubmit"
      >
        提交自评
      </van-button>
    </div>

    <van-loading v-if="loading" class="page-loading" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getEvalRecord, submitSelfEval } from '../../api/evaluation'
import { showToast, showConfirmDialog } from 'vant'

const route = useRoute()
const router = useRouter()
const recordId = parseInt(route.params.id)

const loading = ref(false)
const submitting = ref(false)
const record = ref(null)
const plan = ref(null)
const dimensions = ref([])
const overallComment = ref('')

const canSubmit = computed(() => {
  return dimensions.value.every(d => d.score && d.score >= 0 && d.score <= 100)
})

onMounted(async () => {
  loading.value = true
  try {
    const res = await getEvalRecord(recordId)
    record.value = res
    plan.value = res.plan || {}
    // 从模板获取维度
    const templateDims = res.template?.dimensions_json || res.template?.dimensions || []
    if (templateDims.length > 0) {
      dimensions.value = templateDims.map(d => ({
        name: d.name,
        weight: d.weight,
        type: d.type,
        score: '',
        comment: ''
      }))
    } else {
      // 默认维度
      dimensions.value = [
        { name: '目标达成', weight: 40, type: 'kpi', score: '', comment: '' },
        { name: '能力发展', weight: 30, type: '360', score: '', comment: '' },
        { name: '价值观', weight: 30, type: 'okr', score: '', comment: '' }
      ]
    }
  } catch (e) {
    showToast('加载失败')
  }
  loading.value = false
})

async function handleSubmit() {
  try {
    await showConfirmDialog({
      title: '确认提交',
      message: '提交后不可修改（除非被退回），确认提交自评？'
    })
  } catch {
    return
  }

  submitting.value = true
  try {
    const scores = dimensions.value.map(d => ({
      dimension_name: d.name,
      weight: d.weight,
      type: d.type,
      score: parseFloat(d.score),
      comment: d.comment
    }))
    const response = await submitSelfEval({ record_id: recordId, scores })
    showToast({ message: response.message || '自评已提交', type: 'success' })
    setTimeout(() => router.replace('/employee/assessments'), 1500)
  } catch (e) {
    showToast(e.response?.data?.detail || '提交失败')
  }
  submitting.value = false
}
</script>

<style scoped>
.plan-name { font-size: 16px; font-weight: 600; color: #333; margin-bottom: 4px; }
.plan-meta { font-size: 13px; color: #999; }
.page-loading { display: flex; justify-content: center; padding: 40px; }
</style>

<template>
  <div class="page-container">
    <van-nav-bar title="Data Export" left-arrow @click-left="$router.back()" fixed placeholder />
    <div class="page-content">
      <div class="card">
        <div class="section-title">Export Scope</div>
        <van-field label="Plan" placeholder="Select plan" readonly clickable @click="showPlanPicker = true" :model-value="selectedPlanName" />
        <van-field label="Dept" placeholder="All" readonly clickable @click="showDeptPicker = true" :model-value="selectedDeptName || 'All'" />
      </div>
      <div class="card">
        <div class="section-title">Fields</div>
        <van-checkbox-group v-model="exportFields">
          <van-cell-group>
            <van-cell title="Basic Info" clickable @click="toggleCheck('basic')">
              <template #right-icon><van-checkbox name="basic" shape="square" /></template>
            </van-cell>
            <van-cell title="Self Score" clickable @click="toggleCheck('self_score')">
              <template #right-icon><van-checkbox name="self_score" shape="square" /></template>
            </van-cell>
            <van-cell title="Manager Score" clickable @click="toggleCheck('manager_score')">
              <template #right-icon><van-checkbox name="manager_score" shape="square" /></template>
            </van-cell>
            <van-cell title="Final Score" clickable @click="toggleCheck('final_score')">
              <template #right-icon><van-checkbox name="final_score" shape="square" /></template>
            </van-cell>
          </van-cell-group>
        </van-checkbox-group>
      </div>
      <div class="card">
        <div class="section-title">Format</div>
        <van-radio-group v-model="exportFormat" direction="horizontal" style="padding:8px 0;">
          <van-radio name="xlsx">Excel</van-radio>
          <van-radio name="csv">CSV</van-radio>
        </van-radio-group>
      </div>
      <div v-if="previewData" class="card">
        <div class="section-title">Preview (top 5)</div>
        <div v-for="(row, idx) in previewData.slice(0, 5)" :key="idx" style="padding:4px 0;font-size:13px;color:#666;">
          {{ JSON.stringify(row) }}
        </div>
        <div style="text-align:right;font-size:12px;color:#999;margin-top:8px;">Total: {{ previewData.length }}</div>
      </div>
      <div style="padding:16px;">
        <van-button type="primary" block round size="large" :loading="exporting" @click="handleExport">Export</van-button>
      </div>
    </div>
    <van-popup v-model:show="showPlanPicker" position="bottom" round>
      <van-picker :columns="planColumns" @confirm="onPlanConfirm" @cancel="showPlanPicker = false" />
    </van-popup>
    <van-popup v-model:show="showDeptPicker" position="bottom" round>
      <van-picker :columns="deptColumns" @confirm="onDeptConfirm" @cancel="showDeptPicker = false" />
    </van-popup>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getPlans } from '../../api/plans'
import request from '../../api/request'
import { showToast } from 'vant'

const plans = ref([])
const depts = ref([])
const selectedPlanId = ref(null)
const selectedDeptId = ref(null)
const showPlanPicker = ref(false)
const showDeptPicker = ref(false)
const exportFields = ref(['basic', 'self_score', 'manager_score', 'final_score'])
const exportFormat = ref('csv')
const exporting = ref(false)
const previewData = ref(null)

const selectedPlanName = computed(() => {
  const p = plans.value.find(p => p.id === selectedPlanId.value)
  return p ? p.name : ''
})
const selectedDeptName = computed(() => {
  const d = depts.value.find(d => d.id === selectedDeptId.value)
  return d ? d.name : ''
})
const planColumns = computed(() => plans.value.map(p => ({ text: p.name, value: p.id })))
const deptColumns = computed(() => {
  const items = [{ text: 'All', value: null }]
  depts.value.forEach(d => items.push({ text: d.name, value: d.id }))
  return items
})

function toggleCheck(val) {
  const idx = exportFields.value.indexOf(val)
  if (idx >= 0) exportFields.value.splice(idx, 1)
  else exportFields.value.push(val)
}
function onPlanConfirm({ selectedValues }) {
  selectedPlanId.value = selectedValues[0]
  showPlanPicker.value = false
  loadPreview()
}
function onDeptConfirm({ selectedValues }) {
  selectedDeptId.value = selectedValues[0]
  showDeptPicker.value = false
}

async function loadPreview() {
  if (!selectedPlanId.value) return
  try {
    const res = await request.get('/api/hr/export/preview', { params: { plan_id: selectedPlanId.value, dept_id: selectedDeptId.value } })
    previewData.value = res || []
  } catch { previewData.value = null }
}

async function handleExport() {
  if (!selectedPlanId.value) { showToast('Select a plan'); return }
  exporting.value = true
  try {
    const res = await request.get('/api/hr/export', {
      params: { plan_id: selectedPlanId.value, dept_id: selectedDeptId.value, fields: exportFields.value.join(','), format: exportFormat.value },
      responseType: 'blob'
    })
    const url = window.URL.createObjectURL(new Blob([res]))
    const link = document.createElement('a')
    link.href = url
    link.download = 'perf_export.' + exportFormat.value
    link.click()
    window.URL.revokeObjectURL(url)
    showToast({ message: 'OK', type: 'success' })
  } catch { showToast('Export failed') }
  exporting.value = false
}

onMounted(async () => {
  try {
    const pRes = await getPlans()
    plans.value = (pRes || []).filter(p => p.status === 'running' || p.status === 'published')
  } catch { /* ignore */ }
})
</script>

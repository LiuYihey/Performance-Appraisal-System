<template>
  <div class="page-container">
    <van-nav-bar title="历史记录" left-arrow @click-left="$router.back()" fixed placeholder />

    <div class="page-content">
      <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
        <van-list v-model:loading="listLoading" :finished="finished" finished-text="没有更多了" @load="loadMore">
          <div v-for="item in list" :key="item.id" class="card history-card" @click="$router.push(`/employee/result/${item.id}`)">
            <div class="history-header">
              <span class="history-title">{{ item.plan_name }}</span>
              <span class="status-tag status-completed">已结束</span>
            </div>
            <div class="history-meta">
              <span>{{ item.cycle_type }}</span>
              <span class="history-score" v-if="item.final_score !== null">
                得分：<b>{{ item.final_score }}</b>
              </span>
              <span v-else class="history-score">未评分</span>
            </div>
          </div>
          <div v-if="list.length === 0 && !listLoading" class="empty-wrapper">
            <van-empty description="暂无历史记录" />
          </div>
        </van-list>
      </van-pull-refresh>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getMyAssessments } from '../../api/evaluation'

const list = ref([])
const listLoading = ref(false)
const finished = ref(false)
const refreshing = ref(false)
const allData = ref([])

async function fetchData() {
  try {
    const res = await getMyAssessments()
    allData.value = (res || []).filter(a => a.status === 'locked' || a.status === 'hr_approved')
  } catch (e) { /* ignore */ }
}

async function loadMore() {
  if (list.value.length < allData.value.length) {
    list.value.push(...allData.value.slice(list.value.length, list.value.length + 10))
  }
  listLoading.value = false
  finished.value = true
}

async function onRefresh() {
  await fetchData()
  list.value = allData.value.slice(0, 10)
  finished.value = list.value.length >= allData.value.length
  refreshing.value = false
}

onMounted(async () => {
  await fetchData()
  list.value = allData.value.slice(0, 10)
  finished.value = list.value.length >= allData.value.length
})
</script>

<style scoped>
.history-card { cursor: pointer; }
.history-card:active { background: #f9f9f9; }
.history-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.history-title { font-size: 15px; font-weight: 500; color: #333; }
.history-meta { display: flex; justify-content: space-between; font-size: 13px; color: #999; }
.history-score { color: var(--primary-color); }
.history-score b { font-size: 16px; }
</style>

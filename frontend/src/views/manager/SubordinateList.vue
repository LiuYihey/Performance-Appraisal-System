<template>
  <div class="page-container">
    <van-nav-bar title="下属列表" left-arrow @click-left="$router.back()" fixed placeholder />

    <div class="page-content">
      <van-search v-model="keyword" placeholder="搜索员工姓名" shape="round" />

      <div v-if="filteredEmployees.length === 0" class="empty-wrapper">
        <van-empty description="暂无下属" />
      </div>

      <div v-for="emp in filteredEmployees" :key="emp.id" class="card emp-card" @click="goDetail(emp)">
        <div class="emp-card-left">
          <div class="emp-avatar">{{ (emp.name || '?').charAt(0) }}</div>
          <div class="emp-text">
            <div class="emp-name">{{ emp.name }}</div>
            <div class="emp-dept">{{ emp.dept_name || '未分配部门' }} · {{ emp.position || '-' }}</div>
          </div>
        </div>
        <div class="emp-card-right">
          <span :class="'status-tag ' + (emp.status === 'active' ? 'status-completed' : 'status-pending')">
            {{ emp.status === 'active' ? '在职' : '离职' }}
          </span>
          <van-icon name="arrow" color="#999" />
        </div>
      </div>
    </div>

    <van-loading v-if="loading" class="page-loading" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import request from '../../api/request'

const router = useRouter()
const loading = ref(false)
const employees = ref([])
const keyword = ref('')

const filteredEmployees = computed(() => {
  if (!keyword.value) return employees.value
  return employees.value.filter(e => (e.name || '').includes(keyword.value))
})

function goDetail(emp) {
  router.push('/employee/result/' + emp.id)
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await request.get('/api/employees/subordinates')
    employees.value = res || []
  } catch {
    employees.value = []
  }
  loading.value = false
})
</script>

<style scoped>
.emp-card { cursor: pointer; display: flex; align-items: center; justify-content: space-between; }
.emp-card:active { background: #f9f9f9; }
.emp-card-left { display: flex; align-items: center; gap: 10px; flex: 1; }
.emp-avatar { width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #1890ff, #40a9ff); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 16px; font-weight: 600; flex-shrink: 0; }
.emp-name { font-size: 15px; font-weight: 500; color: #333; }
.emp-dept { font-size: 12px; color: #999; margin-top: 2px; }
.emp-card-right { display: flex; align-items: center; gap: 6px; }
.page-loading { display: flex; justify-content: center; padding: 40px; }
</style>

<template>
  <div class="page-container">
    <van-nav-bar title="组织架构同步" left-arrow @click-left="$router.back()" fixed placeholder />

    <div class="page-content">
      <!-- 同步状态 -->
      <div class="card">
        <div class="section-title">当前状态</div>
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-value">{{ stats.departments || 0 }}</div>
            <div class="stat-label">部门数</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ stats.employees || 0 }}</div>
            <div class="stat-label">员工总数</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ stats.active_employees || 0 }}</div>
            <div class="stat-label">在职员工</div>
          </div>
        </div>
      </div>

      <!-- 同步操作 -->
      <div class="card">
        <div class="section-title">同步操作</div>

        <van-cell-group>
          <van-cell title="同步部门" is-link @click="syncDepartments">
            <template #label>
              <span style="color: #999; font-size: 12px;">从企业微信同步所有部门信息</span>
            </template>
          </van-cell>

          <van-cell title="同步所有员工" is-link @click="syncAllEmployees">
            <template #label>
              <span style="color: #999; font-size: 12px;">从企业微信同步所有部门的员工信息（后台执行）</span>
            </template>
          </van-cell>

          <van-cell title="更新上下级关系" is-link @click="updateLeaderRelationships">
            <template #label>
              <span style="color: #999; font-size: 12px;">根据部门负责人更新员工的直属上级</span>
            </template>
          </van-cell>
        </van-cell-group>
      </div>

      <!-- 说明 -->
      <div class="card">
        <div class="section-title">使用说明</div>
        <div class="tips">
          <p>1. <strong>同步部门</strong>：从企业微信获取所有部门结构</p>
          <p>2. <strong>同步员工</strong>：遍历所有部门，获取员工详细信息（包括姓名、职位、头像等）</p>
          <p>3. <strong>更新关系</strong>：根据部门负责人自动建立上下级关系</p>
          <p style="margin-top: 12px; color: #ff976a;">⚠️ 首次使用建议按顺序执行：部门 → 员工 → 关系</p>
          <p style="color: #999;">💡 同步员工会在后台执行，可能需要几分钟时间</p>
        </div>
      </div>

      <!-- 同步日志 -->
      <div class="card" v-if="logs.length > 0">
        <div class="section-title">同步日志</div>
        <div class="log-list">
          <div v-for="(log, idx) in logs" :key="idx" class="log-item">
            <van-icon :name="log.success ? 'success' : 'info-o'" :color="log.success ? '#07c160' : '#1890ff'" />
            <span>{{ log.message }}</span>
            <span class="log-time">{{ log.time }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { showToast, showLoadingToast, showConfirmDialog } from 'vant'
import request from '../../api/request'

const stats = ref({})
const logs = ref([])

async function loadStats() {
  try {
    const res = await request.get('/api/admin/sync/status')
    stats.value = res
  } catch (e) {
    // ignore
  }
}

function addLog(message, success = true) {
  logs.value.unshift({
    message,
    success,
    time: new Date().toLocaleTimeString()
  })
  if (logs.value.length > 10) {
    logs.value.pop()
  }
}

async function syncDepartments() {
  try {
    await showConfirmDialog({
      title: '确认同步',
      message: '确定要从企业微信同步部门信息吗？'
    })

    const toast = showLoadingToast({ message: '同步中...', forbidClick: true, duration: 0 })
    const res = await request.post('/api/admin/sync/departments')
    toast.close()

    showToast({ message: res.message, type: 'success' })
    addLog(res.message)
    await loadStats()
  } catch (e) {
    if (e === 'cancel') return
    showToast(e.response?.data?.detail || '同步失败')
    addLog('同步部门失败', false)
  }
}

async function syncAllEmployees() {
  try {
    await showConfirmDialog({
      title: '确认同步',
      message: '确定要同步所有员工吗？此操作会在后台执行，可能需要几分钟。'
    })

    const toast = showLoadingToast({ message: '启动同步...', forbidClick: true })
    const res = await request.post('/api/admin/sync/employees')
    toast.close()

    showToast({ message: res.message, type: 'success' })
    addLog(res.message)

    // 10秒后刷新统计
    setTimeout(async () => {
      await loadStats()
      addLog('统计数据已更新')
    }, 10000)
  } catch (e) {
    if (e === 'cancel') return
    showToast(e.response?.data?.detail || '启动失败')
    addLog('启动同步失败', false)
  }
}

async function updateLeaderRelationships() {
  try {
    await showConfirmDialog({
      title: '确认更新',
      message: '确定要更新所有员工的上下级关系吗？'
    })

    const toast = showLoadingToast({ message: '更新中...', forbidClick: true, duration: 0 })
    const res = await request.post('/api/admin/sync/leader-relationships')
    toast.close()

    showToast({ message: res.message, type: 'success' })
    addLog(res.message)
  } catch (e) {
    if (e === 'cancel') return
    showToast(e.response?.data?.detail || '更新失败')
    addLog('更新关系失败', false)
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-top: 12px;
}
.stat-item {
  text-align: center;
  padding: 12px;
  background: #f5f6fa;
  border-radius: 8px;
}
.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--primary-color);
  margin-bottom: 4px;
}
.stat-label {
  font-size: 12px;
  color: #999;
}
.tips {
  font-size: 13px;
  color: #666;
  line-height: 1.8;
}
.tips p {
  margin: 6px 0;
}
.log-list {
  max-height: 300px;
  overflow-y: auto;
}
.log-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 13px;
}
.log-item:last-child {
  border-bottom: none;
}
.log-time {
  margin-left: auto;
  color: #999;
  font-size: 12px;
}
</style>

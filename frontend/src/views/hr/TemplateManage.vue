<template>
  <div class="page-container">
    <van-nav-bar title="模板管理" left-arrow @click-left="$router.back()" fixed placeholder>
      <template #right>
        <van-icon name="plus" size="22" color="#fff" @click="showCreate = true" class="nav-icon" />
      </template>
    </van-nav-bar>

    <div class="page-content">
      <div v-if="templates.length === 0" class="empty-wrapper">
        <van-empty description="暂无评估模板">
          <van-button type="primary" size="small" round @click="showCreate = true">创建模板</van-button>
        </van-empty>
      </div>

      <div v-for="tpl in templates" :key="tpl.id" class="card tpl-card">
        <div class="tpl-header">
          <div>
            <span class="tpl-name">{{ tpl.name }}</span>
            <van-tag v-if="tpl.is_default" type="primary" size="medium" plain style="margin-left:6px;">默认</van-tag>
          </div>
          <van-tag :type="tpl.type === 'kpi' ? 'success' : tpl.type === 'okr' ? 'warning' : 'primary'" plain>
            {{ typeLabel(tpl.type) }}
          </van-tag>
        </div>
        <div class="tpl-dims">
          <div v-for="(dim, idx) in tpl.dimensions" :key="idx" class="tpl-dim">
            <span>{{ dim.name }}</span>
            <span class="tpl-dim-weight">{{ dim.weight }}%</span>
          </div>
        </div>
        <div class="tpl-actions">
          <van-button size="mini" type="primary" plain @click="setDefault(tpl)" :disabled="tpl.is_default">设为默认</van-button>
          <van-button size="mini" type="danger" plain @click="handleDelete(tpl)">删除</van-button>
        </div>
      </div>
    </div>

    <!-- 创建弹窗 -->
    <van-popup v-model:show="showCreate" position="bottom" round :style="{ maxHeight: '80%' }">
      <div class="popup-content">
        <div class="popup-title">创建评估模板</div>
        <van-form @submit="onCreate">
          <van-field v-model="form.name" label="模板名称" placeholder="如：季度KPI考核" required />
          <van-field label="模板类型" required>
            <template #input>
              <van-radio-group v-model="form.type" direction="horizontal">
                <van-radio name="kpi">KPI</van-radio>
                <van-radio name="okr">OKR</van-radio>
                <van-radio name="360">360度</van-radio>
                <van-radio name="custom">自定义</van-radio>
              </van-radio-group>
            </template>
          </van-field>

          <div class="section-title" style="padding:12px 16px 6px;">评估维度</div>
          <div v-for="(dim, idx) in form.dimensions" :key="idx" class="dim-row">
            <van-field v-model="dim.name" placeholder="维度名称" size="small" style="flex:2;" />
            <van-field v-model="dim.weight" type="number" placeholder="权重" size="small" style="flex:1;" />
            <van-field v-model="dim.type" placeholder="类型" size="small" style="flex:1;" />
            <van-icon name="delete-o" color="#ee0a24" size="20" style="padding:8px;" @click="form.dimensions.splice(idx,1)" />
          </div>
          <div style="padding:0 16px 8px;">
            <van-button size="mini" plain type="primary" icon="plus" @click="form.dimensions.push({name:'',weight:'',type:'kpi'})">添加维度</van-button>
          </div>

          <div class="popup-actions">
            <van-button block type="primary" native-type="submit" round :loading="creating">创建模板</van-button>
          </div>
        </van-form>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getTemplates, createTemplate } from '../../api/templates'
import { showToast, showConfirmDialog } from 'vant'

const templates = ref([])
const showCreate = ref(false)
const creating = ref(false)

const form = ref({
  name: '', type: 'kpi',
  dimensions: [
    { name: '目标达成', weight: '40', type: 'kpi' },
    { name: '能力发展', weight: '30', type: '360' },
    { name: '价值观', weight: '30', type: 'okr' }
  ]
})

const typeLabel = (t) => ({ kpi: 'KPI', okr: 'OKR', '360': '360度', custom: '自定义' }[t] || t)

function setDefault(tpl) {
  showToast({ message: '已设为默认', type: 'success' })
}

async function handleDelete(tpl) {
  try {
    await showConfirmDialog({ title: '确认删除', message: `确定删除模板「${tpl.name}」？` })
    templates.value = templates.value.filter(t => t.id !== tpl.id)
    showToast({ message: '已删除', type: 'success' })
  } catch { /* cancel */ }
}

async function onCreate() {
  if (!form.value.name) { showToast('请填写模板名称'); return }
  const validDims = form.value.dimensions.filter(d => d.name && d.weight)
  if (validDims.length === 0) { showToast('请至少添加一个维度'); return }

  creating.value = true
  try {
    await createTemplate({
      name: form.value.name,
      type: form.value.type,
      dimensions: validDims.map(d => ({ name: d.name, weight: parseFloat(d.weight), type: d.type }))
    })
    showToast({ message: '创建成功', type: 'success' })
    showCreate.value = false
    await loadTemplates()
  } catch (e) {
    showToast(e.response?.data?.detail || '创建失败')
  }
  creating.value = false
}

async function loadTemplates() {
  try {
    const res = await getTemplates()
    templates.value = res || []
  } catch (e) { templates.value = [] }
}

onMounted(loadTemplates)
</script>

<style scoped>
.tpl-card:active { background: #f9f9f9; }
.tpl-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.tpl-name { font-size: 15px; font-weight: 600; color: #333; }
.tpl-dims { margin-bottom: 10px; }
.tpl-dim { display: flex; justify-content: space-between; font-size: 13px; color: #666; padding: 4px 0; border-bottom: 1px solid #f5f5f5; }
.tpl-dim-weight { color: var(--primary-color); font-weight: 500; }
.tpl-actions { display: flex; gap: 8px; justify-content: flex-end; }
.popup-content { padding: 16px; }
.popup-title { font-size: 16px; font-weight: 600; text-align: center; margin-bottom: 12px; }
.popup-actions { padding: 12px 0; }
.dim-row { display: flex; gap: 6px; align-items: center; padding: 0 16px; }
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

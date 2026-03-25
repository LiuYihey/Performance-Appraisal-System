import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const pageTitle = ref('绩效管理系统')
  const loading = ref(false)
  const currentPlan = ref(null)

  function setPageTitle(title) {
    pageTitle.value = title
    document.title = title
  }

  function setLoading(val) {
    loading.value = val
  }

  function setCurrentPlan(plan) {
    currentPlan.value = plan
  }

  return {
    pageTitle,
    loading,
    currentPlan,
    setPageTitle,
    setLoading,
    setCurrentPlan
  }
})

<template>
  <div class="my-push-requests">
    <van-nav-bar title="我的推送申请" left-arrow @click-left="$router.back()" fixed placeholder />
    <div class="content">
      <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
        <van-empty v-if="!loading && list.length === 0" description="暂无推送申请" image="search" />
        <div v-for="item in list" :key="item.id" class="request-card">
          <div class="card-top">
            <span class="blacklist-id">条目 #{{ item.blacklist_id }}</span>
            <van-tag :type="getStatusType(item.status)" round>{{ getStatusText(item.status) }}</van-tag>
          </div>
          <div class="evidence-preview">{{ item.evidence }}</div>
          <div class="reject-reason" v-if="item.status === 'REJECTED' && item.reject_reason">
            <van-icon name="cross" color="#ee0a24" />
            <span>拒绝原因：{{ item.reject_reason }}</span>
          </div>
          <div class="card-time">{{ formatDate(item.created_at) }}</div>
        </div>
        <div v-if="totalPages > 1" class="pagination-bar">
          <van-button size="small" plain :disabled="page === 1" icon="arrow-left" @click="goPage(page - 1)" />
          <span class="page-info">{{ page }} / {{ totalPages }}</span>
          <van-button size="small" plain :disabled="page === totalPages" icon="arrow" @click="goPage(page + 1)" />
        </div>
      </van-pull-refresh>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { showToast } from 'vant'
import { blacklistAPI } from '@/api/blacklist'

const list = ref([])
const loading = ref(false)
const refreshing = ref(false)
const page = ref(1)
const pageSize = 20
const total = ref(0)
const totalPages = computed(() => Math.ceil(total.value / pageSize))

const getStatusType = (s) => ({ PENDING: 'warning', APPROVED: 'success', REJECTED: 'danger' }[s] || 'default')
const getStatusText = (s) => ({ PENDING: '待审核', APPROVED: '已通过', REJECTED: '已拒绝' }[s] || s)
const formatDate = (d) => d ? new Date(d).toLocaleString('zh-CN') : ''

const loadData = async (p = page.value) => {
  loading.value = true
  try {
    const res = await blacklistAPI.getMyPushRequests(p, pageSize)
    list.value = res.items
    total.value = res.total
    page.value = p
  } catch (e) {
    showToast('加载失败')
  } finally {
    loading.value = false
  }
}

const onRefresh = async () => {
  refreshing.value = true
  await loadData(1)
  refreshing.value = false
}

const goPage = (p) => { if (p >= 1 && p <= totalPages.value) loadData(p) }

onMounted(() => loadData())
</script>

<style scoped>
.my-push-requests { min-height: 100vh; background: #f7f8fa; padding-bottom: 40px; }
.content { padding: 16px; }
.request-card {
  background: #fff; border-radius: 12px; padding: 14px;
  margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,.06);
}
.card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.blacklist-id { font-size: 14px; font-weight: 600; color: #323233; }
.evidence-preview { font-size: 13px; color: #646566; margin-bottom: 8px; line-height: 1.5;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.reject-reason { display: flex; align-items: flex-start; gap: 4px; font-size: 12px; color: #ee0a24; margin-bottom: 6px; }
.card-time { font-size: 12px; color: #969799; }
.pagination-bar { display: flex; align-items: center; justify-content: center; gap: 16px; padding: 16px 0; }
.page-info { font-size: 14px; color: #646566; min-width: 60px; text-align: center; }
</style>

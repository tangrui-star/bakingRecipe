<template>
  <div class="notifications-page">
    <div class="page-header">
      <div class="header-content">
        <el-button size="small" @click="$router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
        <div class="header-title">通知中心</div>
        <el-button size="small" @click="markAllRead" :disabled="unreadCount === 0">全部已读</el-button>
      </div>
    </div>

    <div class="content">
      <div v-if="loading" class="loading-state">
        <el-icon class="is-loading" :size="32"><Loading /></el-icon>
      </div>

      <div v-else-if="list.length === 0" class="empty-state">
        <el-icon :size="48"><Bell /></el-icon>
        <p>暂无通知</p>
      </div>

      <div v-else>
        <div
          v-for="item in list"
          :key="item.id"
          class="notification-card"
          :class="{ unread: !item.is_read }"
          @click="markRead(item)"
        >
          <div class="notif-icon" :class="item.type === 'PUSH_APPROVED' ? 'approved' : 'rejected'">
            <el-icon><Check v-if="item.type === 'PUSH_APPROVED'" /><Close v-else /></el-icon>
          </div>
          <div class="notif-body">
            <div class="notif-title">{{ item.title }}</div>
            <div class="notif-content">{{ item.content }}</div>
            <div class="notif-time">{{ formatDate(item.created_at) }}</div>
          </div>
          <div class="unread-dot" v-if="!item.is_read"></div>
        </div>

        <div v-if="totalPages > 1" class="pagination">
          <el-pagination
            v-model:current-page="page"
            :page-size="pageSize"
            :total="total"
            layout="prev, pager, next"
            @current-change="loadData"
            small
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Loading, Bell, Check, Close } from '@element-plus/icons-vue'
import axios from 'axios'

const list = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = 20
const total = ref(0)
const unreadCount = ref(0)
const totalPages = computed(() => Math.ceil(total.value / pageSize))

const api = () => {
  const token = localStorage.getItem('access_token')
  return axios.create({ baseURL: '/api', headers: { Authorization: `Bearer ${token}` } })
}

const formatDate = (d) => d ? new Date(d).toLocaleString('zh-CN') : ''

const loadData = async (p = page.value) => {
  loading.value = true
  try {
    const res = await api().get('/notifications', { params: { page: p, page_size: pageSize } })
    list.value = res.data.items
    total.value = res.data.total
    unreadCount.value = res.data.unread_count
    page.value = p
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const markRead = async (item) => {
  if (item.is_read) return
  try {
    const res = await api().put(`/notifications/${item.id}/read`)
    item.is_read = true
    unreadCount.value = res.data.unread_count
  } catch {}
}

const markAllRead = async () => {
  try {
    await api().put('/notifications/read-all')
    list.value.forEach(n => n.is_read = true)
    unreadCount.value = 0
    ElMessage.success('已全部标记为已读')
  } catch {
    ElMessage.error('操作失败')
  }
}

onMounted(() => loadData())
</script>

<style scoped>
.notifications-page { min-height: 100vh; background: var(--bg-primary); padding-bottom: 40px; }
.page-header {
  position: fixed; top: 0; left: 0; right: 0; z-index: 100;
  background: var(--bg-card); border-bottom: 1px solid var(--border-color);
}
.header-content {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px; height: 48px; max-width: 800px; margin: 0 auto;
}
.header-title { font-size: 17px; font-weight: 600; color: var(--text-primary); }
.content { padding: 12px; padding-top: 60px; max-width: 800px; margin: 0 auto; }
.loading-state, .empty-state {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; padding: 60px 20px; gap: 16px; color: var(--text-secondary);
}
.notification-card {
  display: flex; align-items: flex-start; gap: 12px;
  background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: 12px; padding: 14px; margin-bottom: 10px;
  cursor: pointer; transition: all .2s; position: relative;
}
.notification-card.unread { border-left: 3px solid var(--primary-blue); }
.notif-icon {
  width: 36px; height: 36px; min-width: 36px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; color: #fff; font-size: 16px;
}
.notif-icon.approved { background: linear-gradient(135deg, #43e97b, #38f9d7); }
.notif-icon.rejected { background: linear-gradient(135deg, #f093fb, #f5576c); }
.notif-body { flex: 1; min-width: 0; }
.notif-title { font-size: 15px; font-weight: 600; color: var(--text-primary); margin-bottom: 4px; }
.notif-content { font-size: 13px; color: var(--text-secondary); line-height: 1.5; margin-bottom: 6px; }
.notif-time { font-size: 12px; color: var(--text-muted); }
.unread-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--primary-blue); flex-shrink: 0; margin-top: 4px;
}
.pagination { display: flex; justify-content: center; padding: 16px 0; }
</style>

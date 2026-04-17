<template>
  <div class="push-review">
    <div class="page-header">
      <div class="header-content">
        <el-button size="small" @click="$router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
        <div class="header-title">推送申请审核</div>
        <div style="width:60px"></div>
      </div>
    </div>

    <div class="content">
      <div class="filter-bar">
        <el-select v-model="statusFilter" placeholder="全部状态" clearable @change="loadData(1)" style="width:140px">
          <el-option label="待审核" value="PENDING" />
          <el-option label="已通过" value="APPROVED" />
          <el-option label="已拒绝" value="REJECTED" />
        </el-select>
      </div>

      <div v-loading="loading">
        <div v-if="list.length === 0 && !loading" class="empty-state">
          <el-icon :size="48"><Document /></el-icon>
          <p>暂无推送申请</p>
        </div>

        <div v-for="item in list" :key="item.id" class="review-card">
          <div class="card-top">
            <span class="card-id">申请 #{{ item.id }}</span>
            <el-tag :type="getStatusType(item.status)" size="small">{{ getStatusText(item.status) }}</el-tag>
          </div>
          <div class="card-info">
            <span class="info-label">条目ID：</span>{{ item.blacklist_id }}
          </div>
          <div class="card-evidence">
            <span class="info-label">证据：</span>{{ item.evidence }}
          </div>
          <div class="card-time">{{ formatDate(item.created_at) }}</div>
          <div v-if="item.status === 'REJECTED' && item.reject_reason" class="reject-reason">
            拒绝原因：{{ item.reject_reason }}
          </div>
          <div v-if="item.status === 'PENDING'" class="card-actions">
            <el-button type="success" size="small" :loading="actionId === item.id + '_approve'" @click="onApprove(item)">通过</el-button>
            <el-button type="danger" size="small" :loading="actionId === item.id + '_reject'" @click="openReject(item)">拒绝</el-button>
          </div>
        </div>
      </div>

      <el-pagination v-if="total > pageSize" v-model:current-page="page" :page-size="pageSize"
        :total="total" layout="prev, pager, next" @current-change="loadData" small
        style="margin-top:16px;justify-content:center;display:flex" />
    </div>

    <!-- 拒绝弹窗 -->
    <el-dialog v-model="rejectDialogVisible" title="填写拒绝原因" width="90%" style="max-width:480px" align-center>
      <el-input v-model="rejectReason" type="textarea" :rows="4" placeholder="请填写拒绝原因（必填）" />
      <template #footer>
        <el-button @click="rejectDialogVisible = false">取消</el-button>
        <el-button type="danger" :loading="rejecting" @click="onRejectConfirm">确认拒绝</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Document } from '@element-plus/icons-vue'
import axios from 'axios'

const list = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = 20
const total = ref(0)
const statusFilter = ref('PENDING')
const actionId = ref('')
const rejectDialogVisible = ref(false)
const rejectReason = ref('')
const rejectingItem = ref(null)
const rejecting = ref(false)

const getStatusType = (s) => ({ PENDING: 'warning', APPROVED: 'success', REJECTED: 'danger' }[s] || 'info')
const getStatusText = (s) => ({ PENDING: '待审核', APPROVED: '已通过', REJECTED: '已拒绝' }[s] || s)
const formatDate = (d) => d ? new Date(d).toLocaleString('zh-CN') : ''

const api = () => {
  const token = localStorage.getItem('access_token')
  return axios.create({ baseURL: '/api', headers: { Authorization: `Bearer ${token}` } })
}

const loadData = async (p = page.value) => {
  loading.value = true
  try {
    const params = { page: p, page_size: pageSize }
    if (statusFilter.value) params.status = statusFilter.value
    const res = await api().get('/push-requests', { params })
    list.value = res.data.items
    total.value = res.data.total
    page.value = p
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}

const onApprove = async (item) => {
  actionId.value = item.id + '_approve'
  try {
    await api().post(`/push-requests/${item.id}/approve`)
    ElMessage.success('已通过，条目已加入系统黑名单')
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally { actionId.value = '' }
}

const openReject = (item) => {
  rejectingItem.value = item
  rejectReason.value = ''
  rejectDialogVisible.value = true
}

const onRejectConfirm = async () => {
  if (!rejectReason.value.trim()) { ElMessage.warning('请填写拒绝原因'); return }
  rejecting.value = true
  try {
    await api().post(`/push-requests/${rejectingItem.value.id}/reject`, { reject_reason: rejectReason.value.trim() })
    ElMessage.success('已拒绝')
    rejectDialogVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally { rejecting.value = false }
}

onMounted(() => loadData())
</script>

<style scoped>
.push-review { min-height: 100vh; background: var(--bg-primary); padding-bottom: 40px; }
.page-header { position: fixed; top: 0; left: 0; right: 0; z-index: 100; background: var(--bg-card); border-bottom: 1px solid var(--border-color); }
.header-content { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; height: 48px; max-width: 1200px; margin: 0 auto; }
.header-title { font-size: 17px; font-weight: 600; }
.content { padding: 16px; padding-top: 64px; max-width: 1200px; margin: 0 auto; }
.filter-bar { margin-bottom: 16px; }
.empty-state { display: flex; flex-direction: column; align-items: center; padding: 60px 20px; gap: 16px; color: var(--text-secondary); }
.review-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; padding: 14px; margin-bottom: 10px; }
.card-top { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.card-id { font-size: 14px; font-weight: 600; }
.card-info, .card-evidence { font-size: 13px; color: var(--text-secondary); margin-bottom: 4px; }
.info-label { font-weight: 600; color: var(--text-primary); }
.card-time { font-size: 12px; color: var(--text-muted); margin-bottom: 8px; }
.reject-reason { font-size: 13px; color: #ee0a24; margin-bottom: 8px; }
.card-actions { display: flex; gap: 8px; }
</style>

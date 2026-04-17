<template>
  <div class="user-management">
    <div class="page-header">
      <div class="header-content">
        <el-button size="small" @click="$router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
        <div class="header-title">用户管理</div>
        <div style="width:60px"></div>
      </div>
    </div>

    <div class="content">
      <div v-loading="loading">
        <div v-if="list.length === 0 && !loading" class="empty-state">
          <el-icon :size="48"><User /></el-icon>
          <p>暂无用户数据</p>
        </div>

        <div v-for="item in list" :key="item.id" class="user-card">
          <div class="user-top">
            <el-avatar :size="40">{{ item.username?.charAt(0).toUpperCase() }}</el-avatar>
            <div class="user-info">
              <div class="user-name">
                {{ item.username }}
                <el-tag v-if="item.is_admin" type="danger" size="small" style="margin-left:6px">管理员</el-tag>
              </div>
              <div class="user-email">{{ item.email }}</div>
            </div>
            <el-switch
              :model-value="item.is_active"
              :loading="togglingId === item.id"
              @change="onToggle(item)"
              :disabled="item.is_admin"
            />
          </div>
          <div class="user-meta">
            注册时间：{{ formatDate(item.created_at) }}
            <span v-if="item.last_login"> · 最后登录：{{ formatDate(item.last_login) }}</span>
          </div>
        </div>
      </div>

      <el-pagination v-if="total > pageSize" v-model:current-page="page" :page-size="pageSize"
        :total="total" layout="prev, pager, next" @current-change="loadData" small
        style="margin-top:16px;justify-content:center;display:flex" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowLeft, User } from '@element-plus/icons-vue'
import axios from 'axios'

const list = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = 20
const total = ref(0)
const togglingId = ref('')

const formatDate = (d) => d ? new Date(d).toLocaleString('zh-CN') : '-'

const api = () => {
  const token = localStorage.getItem('access_token')
  return axios.create({ baseURL: '/api', headers: { Authorization: `Bearer ${token}` } })
}

const loadData = async (p = page.value) => {
  loading.value = true
  try {
    const res = await api().get('/admin/users', { params: { page: p, page_size: pageSize } })
    list.value = res.data.items
    total.value = res.data.total
    page.value = p
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}

const onToggle = async (item) => {
  togglingId.value = item.id
  try {
    const res = await api().put(`/admin/users/${item.id}/toggle-active`)
    item.is_active = res.data.is_active
    ElMessage.success(res.data.message)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally { togglingId.value = '' }
}

onMounted(() => loadData())
</script>

<style scoped>
.user-management { min-height: 100vh; background: var(--bg-primary); padding-bottom: 40px; }
.page-header { position: fixed; top: 0; left: 0; right: 0; z-index: 100; background: var(--bg-card); border-bottom: 1px solid var(--border-color); }
.header-content { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; height: 48px; max-width: 1200px; margin: 0 auto; }
.header-title { font-size: 17px; font-weight: 600; }
.content { padding: 16px; padding-top: 64px; max-width: 1200px; margin: 0 auto; }
.empty-state { display: flex; flex-direction: column; align-items: center; padding: 60px 20px; gap: 16px; color: var(--text-secondary); }
.user-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; padding: 14px; margin-bottom: 10px; }
.user-top { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.user-info { flex: 1; min-width: 0; }
.user-name { font-size: 15px; font-weight: 600; color: var(--text-primary); }
.user-email { font-size: 13px; color: var(--text-secondary); }
.user-meta { font-size: 12px; color: var(--text-muted); }
</style>

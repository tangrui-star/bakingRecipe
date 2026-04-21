<template>
  <div class="admin-user-blacklist">
    <div class="page-header">
      <div class="header-content">
        <el-button size="small" @click="$router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
        <div class="header-title">全平台用户黑名单</div>
        <div style="width:60px"></div>
      </div>
    </div>

    <div class="content">
      <div class="filter-bar">
        <el-input v-model="search" placeholder="搜索姓名/电话" clearable @clear="loadData(1)" @keyup.enter="loadData(1)" style="flex:1" />
        <el-select v-model="riskFilter" placeholder="风险等级" clearable @change="loadData(1)" style="width:120px">
          <el-option label="高风险" value="HIGH" />
          <el-option label="中风险" value="MEDIUM" />
          <el-option label="低风险" value="LOW" />
        </el-select>
        <el-button @click="loadData(1)">搜索</el-button>
      </div>

      <div v-loading="loading">
        <div v-if="list.length === 0 && !loading" class="empty-state">
          <el-icon :size="48"><Warning /></el-icon>
          <p>暂无数据</p>
        </div>

        <div v-for="item in list" :key="item.id" class="bl-card">
          <div class="bl-top">
            <span class="bl-name">{{ item.ktt_name || '未知' }}</span>
            <el-tag :type="getRiskType(item.risk_level)" size="small">{{ getRiskText(item.risk_level) }}</el-tag>
            <el-tag type="info" size="small" style="margin-left:4px">{{ item.owner_id ? '用户' : '系统' }}</el-tag>
          </div>
          <div class="bl-contact" v-if="item.phone_numbers?.length">
            <span class="bl-icon">📞</span>
            <span>{{ item.phone_numbers.join(', ') }}</span>
          </div>
          <div class="bl-contact" v-if="item.wechat_name">
            <span class="bl-icon">💬</span>
            <span>{{ item.wechat_name }}<span v-if="item.wechat_id" class="bl-sub">（{{ item.wechat_id }}）</span></span>
          </div>
          <div class="bl-contact" v-if="item.order_name_phone">
            <span class="bl-icon">🛒</span>
            <span>{{ item.order_name_phone }}</span>
          </div>
          <div class="bl-contact" v-if="item.order_address1">
            <span class="bl-icon">📍</span>
            <span>{{ item.order_address1 }}</span>
          </div>
          <div class="bl-reason" v-if="item.blacklist_reason">
            <div class="reason-label">原因：</div>
            <div class="reason-text">{{ item.blacklist_reason }}</div>
          </div>
          <div class="bl-footer">
            <span>创建人：{{ item.created_by || '-' }}</span>
            <span>{{ formatDate(item.created_at) }}</span>
            <span v-if="item.new_id" class="bl-id">{{ item.new_id }}</span>
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
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Warning } from '@element-plus/icons-vue'
import axios from 'axios'

const route = useRoute()
const list = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = 20
const total = ref(0)
const search = ref('')
const riskFilter = ref(route.query.risk_level || '')

const getRiskType = (l) => ({ HIGH: 'danger', MEDIUM: 'warning', LOW: 'success' }[l] || 'info')
const getRiskText = (l) => ({ HIGH: '高风险', MEDIUM: '中风险', LOW: '低风险' }[l] || l)
const formatDate = (d) => d ? new Date(d).toLocaleString('zh-CN') : ''

const api = () => {
  const token = localStorage.getItem('access_token')
  return axios.create({ baseURL: '/api', headers: { Authorization: `Bearer ${token}` } })
}

const loadData = async (p = page.value) => {
  loading.value = true
  try {
    const params = { page: p, page_size: pageSize }
    if (search.value) params.search = search.value
    if (riskFilter.value) params.risk_level = riskFilter.value
    const res = await api().get('/blacklist', { params })
    list.value = res.data.items
    total.value = res.data.total
    page.value = p
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}

onMounted(() => loadData())
</script>

<style scoped>
.admin-user-blacklist { min-height: 100vh; background: var(--bg-primary); padding-bottom: 40px; }
.page-header { position: fixed; top: 0; left: 0; right: 0; z-index: 100; background: var(--bg-card); border-bottom: 1px solid var(--border-color); }
.header-content { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; height: 48px; max-width: 1200px; margin: 0 auto; }
.header-title { font-size: 17px; font-weight: 600; }
.content { padding: 16px; padding-top: 64px; max-width: 1200px; margin: 0 auto; }
.filter-bar { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
.empty-state { display: flex; flex-direction: column; align-items: center; padding: 60px 20px; gap: 16px; color: var(--text-secondary); }
.bl-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; padding: 14px; margin-bottom: 10px; }
.bl-top { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; }
.bl-name { font-size: 15px; font-weight: 600; }
.bl-contact { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; padding: 7px 10px; background: var(--bg-secondary); border-radius: 8px; font-size: 13px; color: var(--text-secondary); }
.bl-icon { font-size: 14px; flex-shrink: 0; }
.bl-sub { color: var(--text-muted); font-size: 12px; }
.bl-reason { margin: 8px 0; padding: 10px 12px; background: #fff7e6; border-left: 3px solid #ff976a; border-radius: 4px; }
.reason-label { font-size: 12px; color: #ed6a0c; font-weight: 600; margin-bottom: 4px; }
.reason-text { font-size: 13px; color: #646566; line-height: 1.5; }
.bl-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 8px; padding-top: 8px; border-top: 1px solid var(--border-color); font-size: 12px; color: var(--text-muted); flex-wrap: wrap; gap: 4px; }
.bl-id { background: var(--bg-secondary); padding: 2px 6px; border-radius: 4px; }
</style>

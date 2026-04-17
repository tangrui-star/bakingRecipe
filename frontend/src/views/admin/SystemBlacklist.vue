<template>
  <div class="system-blacklist">
    <div class="page-header">
      <div class="header-content">
        <el-button size="small" @click="$router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
        <div class="header-title">系统黑名单管理</div>
        <el-button type="primary" size="small" @click="openCreate">新增</el-button>
      </div>
    </div>

    <div class="content">
      <!-- 搜索栏 -->
      <div class="filter-bar">
        <el-input v-model="search" placeholder="搜索姓名/电话" clearable @clear="loadData(1)" @keyup.enter="loadData(1)" style="flex:1" />
        <el-select v-model="riskFilter" placeholder="风险等级" clearable @change="loadData(1)" style="width:120px">
          <el-option label="高风险" value="HIGH" />
          <el-option label="中风险" value="MEDIUM" />
          <el-option label="低风险" value="LOW" />
        </el-select>
        <el-button @click="loadData(1)">搜索</el-button>
      </div>

      <!-- 列表 -->
      <div v-loading="loading">
        <div v-if="list.length === 0 && !loading" class="empty-state">
          <el-icon :size="48"><Warning /></el-icon>
          <p>暂无系统黑名单数据</p>
        </div>
        <div v-for="item in list" :key="item.id" class="bl-card">
          <div class="bl-top">
            <span class="bl-name">{{ item.ktt_name || '未知' }}</span>
            <el-tag :type="getRiskType(item.risk_level)" size="small">{{ getRiskText(item.risk_level) }}</el-tag>
          </div>
          <div class="bl-phones" v-if="item.phone_numbers?.length">
            {{ item.phone_numbers.join(', ') }}
          </div>
          <div class="bl-reason" v-if="item.blacklist_reason">{{ item.blacklist_reason }}</div>
          <div class="bl-actions">
            <el-button size="small" @click="openEdit(item)">编辑</el-button>
            <el-button size="small" type="danger" @click="onDelete(item)">删除</el-button>
          </div>
        </div>
      </div>

      <el-pagination v-if="total > pageSize" v-model:current-page="page" :page-size="pageSize"
        :total="total" layout="prev, pager, next" @current-change="loadData" small style="margin-top:16px;justify-content:center;display:flex" />
    </div>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editItem ? '编辑系统黑名单' : '新增系统黑名单'" width="95%" style="max-width:560px" align-center>
      <el-form :model="form" label-width="80px">
        <el-form-item label="KTT名字"><el-input v-model="form.ktt_name" /></el-form-item>
        <el-form-item label="订单姓名"><el-input v-model="form.order_name_phone" /></el-form-item>
        <el-form-item label="入黑原因"><el-input v-model="form.blacklist_reason" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="风险等级">
          <el-select v-model="form.risk_level" style="width:100%">
            <el-option label="高风险" value="HIGH" />
            <el-option label="中风险" value="MEDIUM" />
            <el-option label="低风险" value="LOW" />
          </el-select>
        </el-form-item>
        <el-form-item label="店铺ID"><el-input v-model="form.shop_id" placeholder="留空使用默认" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Warning } from '@element-plus/icons-vue'
import axios from 'axios'

const list = ref([])
const loading = ref(false)
const saving = ref(false)
const page = ref(1)
const pageSize = 20
const total = ref(0)
const search = ref('')
const riskFilter = ref('')
const dialogVisible = ref(false)
const editItem = ref(null)
const form = ref({ ktt_name: '', order_name_phone: '', blacklist_reason: '', risk_level: 'MEDIUM', shop_id: '' })

const getRiskType = (l) => ({ HIGH: 'danger', MEDIUM: 'warning', LOW: 'success' }[l] || 'info')
const getRiskText = (l) => ({ HIGH: '高风险', MEDIUM: '中风险', LOW: '低风险' }[l] || l)

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
    const res = await api().get('/system-blacklist', { params })
    list.value = res.data.items
    total.value = res.data.total
    page.value = p
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}

const openCreate = () => {
  editItem.value = null
  const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}')
  form.value = { ktt_name: '', order_name_phone: '', blacklist_reason: '', risk_level: 'MEDIUM', shop_id: userInfo.shop_id || '' }
  dialogVisible.value = true
}

const openEdit = (item) => {
  editItem.value = item
  form.value = { ktt_name: item.ktt_name || '', order_name_phone: item.order_name_phone || '', blacklist_reason: item.blacklist_reason || '', risk_level: item.risk_level || 'MEDIUM', shop_id: item.shop_id || '' }
  dialogVisible.value = true
}

const onSave = async () => {
  saving.value = true
  try {
    if (editItem.value) {
      await api().put(`/system-blacklist/${editItem.value.id}`, form.value)
      ElMessage.success('更新成功')
    } else {
      await api().post('/system-blacklist', form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '操作失败') }
  finally { saving.value = false }
}

const onDelete = async (item) => {
  try {
    await ElMessageBox.confirm(`确定删除「${item.ktt_name || '未知'}」吗？`, '确认删除', { type: 'warning' })
    await api().delete(`/system-blacklist/${item.id}`)
    ElMessage.success('删除成功')
    loadData()
  } catch (e) { if (e !== 'cancel') ElMessage.error('删除失败') }
}

onMounted(() => loadData())
</script>

<style scoped>
.system-blacklist { min-height: 100vh; background: var(--bg-primary); padding-bottom: 40px; }
.page-header { position: fixed; top: 0; left: 0; right: 0; z-index: 100; background: var(--bg-card); border-bottom: 1px solid var(--border-color); }
.header-content { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; height: 48px; max-width: 1200px; margin: 0 auto; }
.header-title { font-size: 17px; font-weight: 600; }
.content { padding: 16px; padding-top: 64px; max-width: 1200px; margin: 0 auto; }
.filter-bar { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
.empty-state { display: flex; flex-direction: column; align-items: center; padding: 60px 20px; gap: 16px; color: var(--text-secondary); }
.bl-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; padding: 14px; margin-bottom: 10px; }
.bl-top { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.bl-name { font-size: 15px; font-weight: 600; }
.bl-phones { font-size: 13px; color: var(--text-secondary); margin-bottom: 6px; }
.bl-reason { font-size: 13px; color: var(--text-secondary); margin-bottom: 8px; }
.bl-actions { display: flex; gap: 8px; }
</style>

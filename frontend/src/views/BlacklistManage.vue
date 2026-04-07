<template>
  <div class="blacklist-manage">
    <!-- 顶部搜索区域 -->
    <div class="search-bar">
      <van-search v-model="searchKeyword" placeholder="搜索姓名或电话" shape="round" background="#f7f8fa" @search="onSearch"
        @clear="onClear" />
    </div>

    <!-- 信息总览卡片 -->
    <div class="overview-card">
      <div class="overview-header">
        <van-icon name="chart-trending-o" />
        <span>黑名单总览</span>
      </div>
      <div class="overview-stats">
        <div class="stat-item" :class="{ active: filterRiskLevel === '' }" @click="onQuickFilter('')">
          <div class="stat-number">{{ statistics.total }}</div>
          <div class="stat-label">全部</div>
        </div>
        <div class="stat-item high" :class="{ active: filterRiskLevel === 'HIGH' }" @click="onQuickFilter('HIGH')">
          <div class="stat-number">{{ statistics.high }}</div>
          <div class="stat-label">高风险</div>
        </div>
        <div class="stat-item medium" :class="{ active: filterRiskLevel === 'MEDIUM' }"
          @click="onQuickFilter('MEDIUM')">
          <div class="stat-number">{{ statistics.medium }}</div>
          <div class="stat-label">中风险</div>
        </div>
        <div class="stat-item low" :class="{ active: filterRiskLevel === 'LOW' }" @click="onQuickFilter('LOW')">
          <div class="stat-number">{{ statistics.low }}</div>
          <div class="stat-label">低风险</div>
        </div>
      </div>
    </div>

    <!-- 订单检查入口 -->
    <div class="screening-entry">
      <div class="entry-card" @click="goToScreening">
        <div class="entry-icon">
          <van-icon name="search" />
        </div>
        <div class="entry-content">
          <div class="entry-title">订单检查</div>
          <div class="entry-desc">上传订单Excel，快速检查黑名单</div>
        </div>
        <van-icon name="arrow" class="entry-arrow" />
      </div>
      <div class="entry-card" @click="goToHistory">
        <div class="entry-icon history">
          <van-icon name="clock-o" />
        </div>
        <div class="entry-content">
          <div class="entry-title">检查历史</div>
          <div class="entry-desc">查看历史检查记录</div>
        </div>
        <van-icon name="arrow" class="entry-arrow" />
      </div>
    </div>

    <!-- 列表容器 -->
    <div class="list-container">
      <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
        <van-list v-model:loading="loading" :finished="finished" :finished-text="list.length > 0 ? '没有更多了' : ''"
          @load="onLoad">
          <van-swipe-cell v-for="item in list" :key="item.id" class="list-item">
            <div class="blacklist-card" @click="onEdit(item)">
              <!-- 卡片头部 -->
              <div class="card-header">
                <div class="name-section">
                  <span class="name">{{ item.ktt_name || '未知' }}</span>
                  <van-tag :type="getRiskLevelType(item.risk_level)" size="medium" round>
                    {{ getRiskLevelText(item.risk_level) }}
                  </van-tag>
                </div>
                <van-icon name="arrow" class="arrow-icon" />
              </div>

              <!-- 联系信息 -->
              <div class="contact-info" v-if="item.phone_numbers && item.phone_numbers.length > 0">
                <van-icon name="phone-o" class="info-icon" />
                <span class="phone-text">{{ item.phone_numbers.join(', ') }}</span>
              </div>

              <!-- 微信信息 -->
              <div class="contact-info" v-if="item.wechat_name">
                <van-icon name="chat-o" class="info-icon" />
                <span class="wechat-text">{{ item.wechat_name }}</span>
              </div>

              <!-- 原因 -->
              <div class="reason-section" v-if="item.blacklist_reason">
                <div class="reason-label">原因：</div>
                <div class="reason-text">{{ item.blacklist_reason }}</div>
              </div>

              <!-- 卡片底部 -->
              <div class="card-footer">
                <div class="footer-item">
                  <van-icon name="clock-o" />
                  <span>{{ formatDate(item.created_at) }}</span>
                </div>
                <div class="footer-item" v-if="item.new_id">
                  <van-icon name="label-o" />
                  <span>{{ item.new_id }}</span>
                </div>
              </div>
            </div>

            <template #right>
              <van-button square type="danger" text="删除" class="delete-button" @click="onDelete(item)" />
            </template>
          </van-swipe-cell>

          <!-- 空状态 -->
          <van-empty v-if="!loading && list.length === 0" description="暂无黑名单记录" image="search" />
        </van-list>
      </van-pull-refresh>
    </div>

    <!-- 添加按钮 -->
    <van-floating-bubble icon="plus" @click="onAdd" :style="{ right: '16px', top: '-50px' }" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showConfirmDialog, showToast } from 'vant'
import { blacklistAPI } from '@/api/blacklist'

const router = useRouter()

// 数据
const list = ref([])
const loading = ref(false)
const finished = ref(false)
const refreshing = ref(false)
const page = ref(1)
const pageSize = 20

// 搜索和筛选
const searchKeyword = ref('')
const filterRiskLevel = ref('')

// 统计数据
const statistics = ref({
  total: 0,
  high: 0,
  medium: 0,
  low: 0
})

// 获取店铺ID（从localStorage或用户信息中获取）
const getShopId = () => {
  const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}')
  const shopId = userInfo.shop_id || '2c2f8124-150b-4351-956a-5d86d2f377aa' // 使用默认店铺ID
  console.log('Shop ID:', shopId)
  return shopId
}

// 加载统计数据
const loadStatistics = async () => {
  try {
    const shopId = getShopId()

    // 获取总数
    const totalRes = await blacklistAPI.getList({ shop_id: shopId, page: 1, page_size: 1 })
    statistics.value.total = totalRes.total

    // 获取各风险等级数量
    const highRes = await blacklistAPI.getList({ shop_id: shopId, risk_level: 'HIGH', page: 1, page_size: 1 })
    statistics.value.high = highRes.total

    const mediumRes = await blacklistAPI.getList({ shop_id: shopId, risk_level: 'MEDIUM', page: 1, page_size: 1 })
    statistics.value.medium = mediumRes.total

    const lowRes = await blacklistAPI.getList({ shop_id: shopId, risk_level: 'LOW', page: 1, page_size: 1 })
    statistics.value.low = lowRes.total
  } catch (error) {
    console.error('Load statistics error:', error)
  }
}

// 加载数据
const loadData = async (isRefresh = false) => {
  if (isRefresh) {
    page.value = 1
    list.value = []
    finished.value = false
  }

  try {
    const shopId = getShopId()
    console.log('Loading blacklist data for shop:', shopId)

    const params = {
      shop_id: shopId,
      page: page.value,
      page_size: pageSize
    }

    if (searchKeyword.value) {
      params.search = searchKeyword.value
    }

    if (filterRiskLevel.value) {
      params.risk_level = filterRiskLevel.value
    }

    console.log('Request params:', params)
    const response = await blacklistAPI.getList(params)
    console.log('Response:', response)

    if (isRefresh) {
      list.value = response.items
    } else {
      list.value.push(...response.items)
    }

    // 判断是否还有更多数据
    if (list.value.length >= response.total) {
      finished.value = true
    }

    page.value++
  } catch (error) {
    console.error('Load data error:', error)
    const errorMsg = error.response?.data?.detail || error.message || '加载失败'
    showToast('加载失败：' + errorMsg)
  }
}

// 下拉刷新
const onRefresh = async () => {
  refreshing.value = true
  await loadData(true)
  refreshing.value = false
}

// 上拉加载
const onLoad = async () => {
  await loadData()
  loading.value = false
}

// 搜索
const onSearch = () => {
  loadData(true)
}

// 清除搜索
const onClear = () => {
  searchKeyword.value = ''
  loadData(true)
}

// 快速筛选
const onQuickFilter = (level) => {
  filterRiskLevel.value = level
  loadData(true)
}

// 筛选变化
const onFilterChange = () => {
  loadData(true)
}

// 添加
const onAdd = () => {
  router.push('/blacklist/edit')
}

// 跳转到订单检查
const goToScreening = () => {
  router.push('/screening')
}

// 跳转到检查历史
const goToHistory = () => {
  router.push('/screening-history')
}

// 编辑
const onEdit = (item) => {
  router.push(`/blacklist/edit/${item.id}`)
}

// 删除
const onDelete = async (item) => {
  try {
    await showConfirmDialog({
      title: '确认删除',
      message: `确定要删除黑名单"${item.ktt_name || '未知'}"吗？`
    })

    await blacklistAPI.delete(item.id)
    showToast('删除成功')
    loadData(true)
  } catch (error) {
    if (error !== 'cancel') {
      showToast('删除失败：' + (error.response?.data?.detail || error.message))
    }
  }
}

// 获取风险等级类型
const getRiskLevelType = (level) => {
  const typeMap = {
    HIGH: 'danger',
    MEDIUM: 'warning',
    LOW: 'success'
  }
  return typeMap[level] || 'default'
}

// 获取风险等级文本
const getRiskLevelText = (level) => {
  const textMap = {
    HIGH: '高风险',
    MEDIUM: '中风险',
    LOW: '低风险'
  }
  return textMap[level] || level
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

// 初始化
onMounted(async () => {
  await loadStatistics()
  // 不需要手动调用loadData，van-list会自动触发
})
</script>

<style scoped>
.blacklist-manage {
  min-height: 100vh;
  background: linear-gradient(180deg, #f7f8fa 0%, #ffffff 100%);
  padding-bottom: 120px;
  display: flex;
  flex-direction: column;
  position: relative;
}

/* 搜索区域 */
.search-bar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

/* 订单检查入口 */
.screening-entry {
  display: flex;
  gap: 12px;
  margin: 12px 16px;
  flex-direction: column;

}

.entry-card {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: all 0.2s;
}

.entry-card:active {
  transform: scale(0.98);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

.entry-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
  color: #fff;
  font-size: 20px;
}

.entry-icon.history {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.entry-content {
  flex: 1;
  min-width: 0;
}

.entry-title {
  font-size: 14px;
  font-weight: 600;
  color: #323233;
  margin-bottom: 4px;
}

.entry-desc {
  font-size: 12px;
  color: #969799;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.entry-arrow {
  color: #c8c9cc;
  font-size: 16px;
}

/* 信息总览卡片 */
.overview-card {
  margin: 12px 16px;
  padding: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
}

.overview-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  color: #fff;
  font-size: 15px;
  font-weight: 600;
}

.overview-header .van-icon {
  font-size: 20px;
}

.overview-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.stat-item {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 12px 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.stat-item:active {
  transform: scale(0.95);
}

.stat-item.active {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.stat-number {
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  line-height: 1.2;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
}

/* 高风险特殊样式 */
.stat-item.high .stat-number {
  color: #ff6b6b;
  text-shadow: 0 2px 4px rgba(255, 107, 107, 0.3);
}

/* 中风险特殊样式 */
.stat-item.medium .stat-number {
  color: #ffa940;
  text-shadow: 0 2px 4px rgba(255, 169, 64, 0.3);
}

/* 低风险特殊样式 */
.stat-item.low .stat-number {
  color: #52c41a;
  text-shadow: 0 2px 4px rgba(82, 196, 26, 0.3);
}

/* 列表容器 */
.list-container {
  flex: 1;
  overflow-y: auto;
  padding: 0 16px 16px;
}

.list-item {
  margin-bottom: 12px;
}

/* 黑名单卡片 */
.blacklist-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  cursor: pointer;
}

.blacklist-card:active {
  transform: scale(0.98);
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.12);
}

/* 卡片头部 */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.name-section {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.name {
  font-size: 17px;
  font-weight: 600;
  color: #323233;
  line-height: 24px;
}

.arrow-icon {
  color: #c8c9cc;
  font-size: 16px;
}

/* 联系信息 */
.contact-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  padding: 8px 12px;
  background: #f7f8fa;
  border-radius: 8px;
}

.info-icon {
  color: #646566;
  font-size: 16px;
}

.phone-text,
.wechat-text {
  font-size: 14px;
  color: #646566;
  flex: 1;
}

/* 原因区域 */
.reason-section {
  margin: 12px 0;
  padding: 12px;
  background: #fff7e6;
  border-left: 3px solid #ff976a;
  border-radius: 4px;
}

.reason-label {
  font-size: 12px;
  color: #ed6a0c;
  font-weight: 600;
  margin-bottom: 4px;
}

.reason-text {
  font-size: 14px;
  color: #646566;
  line-height: 20px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 卡片底部 */
.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.footer-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #969799;
}

.footer-item .van-icon {
  font-size: 14px;
}

/* 删除按钮 */
.delete-button {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 浮动按钮 */
:deep(.van-floating-bubble) {
  position: fixed !important;
  top: -60px;
  z-index: 1001 !important;
  box-shadow: 0 4px 12px rgba(25, 137, 250, 0.4) !important;
}

/* 空状态 */
.van-empty {
  padding: 60px 0;
}

/* 风险等级标签样式优化 */
:deep(.van-tag--danger) {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
  border: none;
}

:deep(.van-tag--warning) {
  background: linear-gradient(135deg, #ffa940 0%, #fa8c16 100%);
  border: none;
}

:deep(.van-tag--success) {
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
  border: none;
}
</style>

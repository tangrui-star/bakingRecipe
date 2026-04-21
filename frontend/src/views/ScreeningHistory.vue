<template>
  <div class="screening-history">
    <van-nav-bar
      title="检查历史"
      left-arrow
      @click-left="onBack"
      fixed
      placeholder
    />

    <div class="content-container">
      <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
        <!-- 展开/收起控制栏 -->
        <div class="list-toolbar" v-if="list.length > 0">
          <span class="list-count">共 {{ total }} 条记录</span>
          <van-button size="mini" plain @click="toggleExpandAll">
            {{ allExpanded ? '收起' : `展开全部(${total})` }}
          </van-button>
        </div>

        <div
          v-for="item in displayedList"
          :key="item.id"
          class="history-card"
        >
          <!-- 卡片头部：点击展开/收起 -->
          <div class="card-header" @click="toggleExpand(item.id)">
            <van-icon name="description" class="file-icon" />
            <div class="file-info">
              <div class="file-name">{{ item.file_name }}</div>
              <div class="file-time">{{ formatTime(item.screening_time) }}</div>
            </div>
            <van-icon
              :name="expandedIds.has(item.id) ? 'arrow-up' : 'arrow-down'"
              class="expand-icon"
            />
          </div>

          <!-- 展开内容 -->
          <div v-if="expandedIds.has(item.id)">
            <div class="card-stats">
              <div class="stat-item">
                <span class="stat-label">总订单</span>
                <span class="stat-value">{{ item.total_orders }}</span>
              </div>
              <div class="stat-divider"></div>
              <div class="stat-item danger">
                <span class="stat-label">命中</span>
                <span class="stat-value">{{ item.matched_count }}</span>
              </div>
            </div>

            <div class="card-footer">
              <van-button size="small" type="primary" plain @click.stop="viewDetail(item)">
                查看详情
              </van-button>
              <van-button size="small" type="danger" plain @click.stop="deleteRecord(item)">
                删除
              </van-button>
            </div>
          </div>

          <!-- 收起时显示简要信息 -->
          <div v-else class="card-summary">
            <span :class="item.matched_count > 0 ? 'hit' : 'safe'">
              命中 {{ item.matched_count }} / {{ item.total_orders }} 条
            </span>
          </div>
        </div>

        <!-- 未展开时显示"还有N条" -->
        <div v-if="!allExpanded && total > 3" class="show-more" @click="toggleExpandAll">
          还有 {{ total - 3 }} 条，点击展开全部
        </div>

        <van-empty
          v-if="!loading && list.length === 0"
          description="暂无检查记录"
          image="search"
        />
      </van-pull-refresh>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'

const router = useRouter()

const list = ref([])
const loading = ref(false)
const refreshing = ref(false)
const total = ref(0)
const expandedIds = ref(new Set())
const allExpanded = ref(false)

// 默认显示3条，展开后显示全部
const displayedList = computed(() => allExpanded.value ? list.value : list.value.slice(0, 3))

const toggleExpand = (id) => {
  const s = new Set(expandedIds.value)
  s.has(id) ? s.delete(id) : s.add(id)
  expandedIds.value = s
}

const toggleExpandAll = async () => {
  if (!allExpanded.value && list.value.length < total.value) {
    await loadList(true)
  }
  allExpanded.value = !allExpanded.value
}

// 获取店铺ID
const getShopId = () => {
  const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}')
  return userInfo.shop_id || '2c2f8124-150b-4351-956a-5d86d2f377aa'
}

// 加载列表
const loadList = async (loadAll = false) => {
  loading.value = true
  try {
    const shopId = getShopId()
    const token = localStorage.getItem('access_token')
    const pageSize = loadAll ? 100 : 50
    const response = await fetch(`/api/screening/history?shop_id=${shopId}&page=1&page_size=${pageSize}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (!response.ok) throw new Error('加载失败')
    const data = await response.json()
    list.value = data.items
    total.value = data.total
  } catch (error) {
    showToast('加载失败：' + error.message)
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

// 下拉刷新
const onRefresh = () => {
  allExpanded.value = false
  loadList()
}

// 查看详情
const viewDetail = (item) => {
  router.push(`/screening-detail/${item.id}`)
}

// 删除记录
const deleteRecord = async (item) => {
  try {
    await showConfirmDialog({
      title: '确认删除',
      message: `确定要删除"${item.file_name}"的检查记录吗？`
    })

    const token = localStorage.getItem('access_token')
    const response = await fetch(`/api/screening/history/${item.id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (!response.ok) {
      throw new Error('删除失败')
    }

    showToast('删除成功')
    // 重置并刷新列表
    page.value = 1
    finished.value = false
    list.value = []
    loadList()
  } catch (error) {
    if (error !== 'cancel') {
      showToast('删除失败：' + error.message)
    }
  }
}

// 格式化时间
const formatTime = (timeStr) => {
  const date = new Date(timeStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day} ${hour}:${minute}`
}

// 返回
const onBack = () => {
  router.back()
}

onMounted(() => {
  loadList()
})
</script>

<style scoped>
.screening-history {
  min-height: 100vh;
  background: #f7f8fa;
  padding-bottom: 20px;
}

.content-container {
  padding: 16px;
}

/* 历史卡片 */
.history-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: transform 0.2s;
}

.history-card:active {
  transform: scale(0.98);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.file-icon {
  font-size: 32px;
  color: #1989fa;
}

.file-info {
  flex: 1;
}

.file-name {
  font-size: 15px;
  font-weight: 600;
  color: #323233;
  margin-bottom: 4px;
}

.file-time {
  font-size: 13px;
  color: #969799;
}

.card-stats {
  display: flex;
  align-items: center;
  padding: 12px;
  background: #f7f8fa;
  border-radius: 8px;
  margin-bottom: 12px;
}

.stat-item {
  flex: 1;
  text-align: center;
}

.stat-item.danger .stat-value {
  color: #ee0a24;
}

.stat-label {
  display: block;
  font-size: 13px;
  color: #646566;
  margin-bottom: 4px;
}

.stat-value {
  display: block;
  font-size: 20px;
  font-weight: 600;
  color: #323233;
}

.stat-divider {
  width: 1px;
  height: 30px;
  background: #dcdee0;
}

.card-footer {
  display: flex;
  gap: 12px;
}

.card-footer .van-button {
  flex: 1;
}

.expand-icon {
  font-size: 16px;
  color: #c8c9cc;
  flex-shrink: 0;
}

.card-summary {
  margin-top: 6px;
  font-size: 13px;
}

.card-summary .hit  { color: #ee0a24; font-weight: 600; }
.card-summary .safe { color: #07c160; }

.list-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0 10px;
}

.list-count { font-size: 13px; color: #969799; }

.show-more {
  text-align: center;
  font-size: 13px;
  color: #1989fa;
  padding: 10px 0 4px;
  cursor: pointer;
}

/* 导航栏样式 */
:deep(.van-nav-bar) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

:deep(.van-nav-bar__title) {
  color: #fff;
  font-weight: 600;
}

:deep(.van-nav-bar .van-icon) {
  color: #fff;
}
</style>

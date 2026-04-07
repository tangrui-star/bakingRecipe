<template>
  <div class="order-screening">
    <van-nav-bar
      title="订单检查"
      left-arrow
      @click-left="onBack"
      fixed
      placeholder
    />

    <div class="content-container">
      <!-- 上传区域 -->
      <div class="upload-section">
        <van-uploader
          v-model="fileList"
          :max-count="1"
          :after-read="handleFileRead"
          accept=".xlsx,.xls"
        >
          <van-button icon="plus" type="primary" size="large" block>
            上传订单Excel文件
          </van-button>
        </van-uploader>
        <div class="upload-tip">
          <van-icon name="info-o" />
          <span>支持.xlsx和.xls格式，需包含"收货人"和"联系电话"列</span>
        </div>

        <!-- 历史文件列表（从数据库读取） -->
        <div v-if="historyList.length > 0" class="file-list">
          <div class="file-list-title">历史检查记录</div>
          <div
            v-for="item in historyList"
            :key="item.id"
            class="file-item"
            :class="{ active: activeId === item.id }"
            @click="viewHistory(item)"
          >
            <div class="file-item-left">
              <van-icon name="description" class="file-icon" />
              <div class="file-meta">
                <div class="file-name">{{ item.file_name }}</div>
                <div class="file-info">
                  {{ item.total_orders }} 条订单 ·
                  <span :class="item.matched_count > 0 ? 'hit' : 'safe'">
                    命中 {{ item.matched_count }}
                  </span>
                  · {{ formatTime(item.screening_time) }}
                </div>
              </div>
            </div>
            <van-icon name="arrow" class="arrow-icon" />
          </div>
        </div>
        <div v-else-if="!historyLoading" class="file-list-empty">
          <span>暂无历史记录</span>
        </div>
      </div>

      <!-- 当次检查结果（上传后展示） -->
      <div v-if="screeningResult" class="result-section" style="padding-bottom: 30px;">
        <div class="stats-card">
          <div class="stat-item">
            <div class="stat-label">文件名</div>
            <div class="stat-value filename">{{ screeningResult.file_name }}</div>
          </div>
          <div class="stat-row">
            <div class="stat-item">
              <div class="stat-label">总订单数</div>
              <div class="stat-value">{{ screeningResult.total_orders }}</div>
            </div>
            <div class="stat-item danger">
              <div class="stat-label">命中黑名单</div>
              <div class="stat-value">{{ screeningResult.matched_count }}</div>
            </div>
          </div>
        </div>

        <!-- 命中列表 -->
        <div v-if="screeningResult.matched_count > 0" class="matched-list">
          <div class="list-header">
            <van-icon name="warning-o" color="#ee0a24" />
            <span>命中黑名单订单（按风险等级排序）</span>
          </div>

          <div
            v-for="(item, index) in screeningResult.results"
            :key="index"
            class="matched-item"
            :class="'risk-' + item.risk_level.toLowerCase()"
          >
            <div class="item-header">
              <van-tag :type="getRiskLevelType(item.risk_level)" size="medium">
                {{ getRiskLevelText(item.risk_level) }}
              </van-tag>
              <span class="row-number">跟团号 {{ item.group_no || ('第' + item.row_number + '行') }}</span>
            </div>

            <div class="match-reason-bar">
              <van-icon name="warning" />
              <span>{{ item.match_reason }}</span>
            </div>

            <div class="two-col">
              <div class="col-block">
                <div class="col-title">📦 订单信息</div>
                <div class="info-row"><span class="label">下单人</span><span class="value">{{ item.ktt_name || '-' }}</span></div>
                <div class="info-row"><span class="label">收货人</span><span class="value">{{ item.order_name || '-' }}</span></div>
                <div class="info-row"><span class="label">电话</span><span class="value">{{ item.order_phone || '-' }}</span></div>
                <div class="info-row"><span class="label">地址</span><span class="value">{{ item.order_address || '-' }}</span></div>
              </div>
              <div class="col-block blacklist-col">
                <div class="col-title">🚫 黑名单信息</div>
                <div class="info-row"><span class="label">KTT名</span><span class="value">{{ item.blacklist_ktt_name || '-' }}</span></div>
                <div class="info-row"><span class="label">下单名</span><span class="value">{{ item.blacklist_order_name || '-' }}</span></div>
                <div class="info-row"><span class="label">电话</span><span class="value">{{ (item.blacklist_phones || []).join('、') || '-' }}</span></div>
                <div class="info-row"><span class="label">地址</span><span class="value">{{ item.blacklist_address1 || '-' }}</span></div>
                <div v-if="item.blacklist_reason" class="info-row">
                  <span class="label">原因</span>
                  <span class="value reason">{{ item.blacklist_reason }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <van-empty v-else description="未检测到黑名单订单" image="success" />

        <div class="action-buttons">
          <van-button size="large" block @click="resetScreening">
            关闭结果
          </van-button>
        </div>
      </div>
    </div>

    <!-- 检查中遮罩 -->
    <van-overlay :show="checking">
      <div class="loading-wrapper">
        <van-loading size="24px" vertical>检查并保存中...</van-loading>
      </div>
    </van-overlay>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'

const router = useRouter()

const fileList = ref([])
const checking = ref(false)
const screeningResult = ref(null)
const historyList = ref([])
const historyLoading = ref(false)
const activeId = ref(null)

const getShopId = () => {
  const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}')
  return userInfo.shop_id || '2c2f8124-150b-4351-956a-5d86d2f377aa'
}

const getToken = () => localStorage.getItem('access_token')

// 加载历史列表（从数据库）
const loadHistory = async () => {
  historyLoading.value = true
  try {
    const shopId = getShopId()
    const res = await fetch(`/api/screening/history?shop_id=${shopId}&page=1&page_size=50`, {
      headers: { 'Authorization': `Bearer ${getToken()}` }
    })
    if (!res.ok) throw new Error()
    const data = await res.json()
    historyList.value = data.items || []
  } catch {
    // 静默失败，不影响上传功能
  } finally {
    historyLoading.value = false
  }
}

// 上传并检查（完成后自动保存）
const handleFileRead = async (file) => {
  checking.value = true
  fileList.value = []

  try {
    const shopId = getShopId()
    const token = getToken()

    // 1. 检查
    const formData = new FormData()
    formData.append('file', file.file)
    const checkRes = await fetch(`/api/screening/check-orders?shop_id=${shopId}`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    })
    if (!checkRes.ok) {
      const err = await checkRes.json()
      throw new Error(err.detail || '检查失败')
    }
    const data = await checkRes.json()

    // 2. 自动保存到数据库
    const saveRes = await fetch('/api/screening/save-screening', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        shop_id: shopId,
        file_name: file.file.name,
        total_orders: data.total_orders,
        matched_count: data.matched_count,
        results: data.results
      })
    })
    if (!saveRes.ok) {
      const err = await saveRes.json()
      throw new Error(err.detail || '保存失败')
    }

    // 3. 展示结果
    screeningResult.value = { ...data, file_name: file.file.name }

    // 4. 刷新历史列表
    await loadHistory()

    showToast(`检查完成，命中 ${data.matched_count} 条`)
  } catch (error) {
    showToast('失败：' + error.message)
  } finally {
    checking.value = false
  }
}

// 点击历史记录 → 跳转详情页
const viewHistory = (item) => {
  activeId.value = item.id
  router.push(`/screening-detail/${item.id}`)
}

// 关闭当次结果
const resetScreening = () => {
  screeningResult.value = null
  activeId.value = null
}

const getRiskLevelType = (level) => ({ HIGH: 'danger', MEDIUM: 'warning', LOW: 'primary' }[level] || 'default')
const getRiskLevelText = (level) => ({ HIGH: '高风险', MEDIUM: '中风险', LOW: '低风险' }[level] || level)

const formatTime = (t) => {
  const d = new Date(t)
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

const onBack = () => router.back()

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.order-screening {
  min-height: 100vh;
  background: #f7f8fa;
  padding-bottom: 20px;
}

.content-container { padding: 16px; }

/* 上传区域 */
.upload-section {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.upload-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  padding: 8px 12px;
  background: #fff7e6;
  border-radius: 6px;
  font-size: 13px;
  color: #ed6a0c;
}

/* 历史文件列表 */
.file-list {
  margin-top: 16px;
  border-top: 1px solid #f0f0f0;
  padding-top: 12px;
}

.file-list-title {
  font-size: 13px;
  color: #969799;
  margin-bottom: 8px;
}

.file-list-empty {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
  font-size: 13px;
  color: #c8c9cc;
  text-align: center;
  padding-bottom: 4px;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 8px;
  margin-bottom: 8px;
  background: #f7f8fa;
  cursor: pointer;
  border: 1.5px solid transparent;
  transition: background 0.15s;
}

.file-item:last-child { margin-bottom: 0; }
.file-item:active, .file-item.active { background: #eef2ff; border-color: #667eea; }

.file-item-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.file-icon { font-size: 24px; color: #1989fa; flex-shrink: 0; }

.file-meta { min-width: 0; }

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: #323233;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-info { font-size: 12px; color: #969799; margin-top: 2px; }
.file-info .hit  { color: #ee0a24; font-weight: 600; }
.file-info .safe { color: #07c160; }

.arrow-icon { font-size: 14px; color: #c8c9cc; flex-shrink: 0; margin-left: 8px; }

/* 统计卡片 */
.stats-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  color: #fff;
  box-shadow: 0 4px 12px rgba(102,126,234,0.3);
}

.stat-row { display: flex; gap: 16px; margin-top: 16px; }
.stat-item { flex: 1; }
.stat-item.danger { background: rgba(238,10,36,0.2); border-radius: 8px; padding: 12px; }
.stat-label { font-size: 13px; opacity: 0.9; margin-bottom: 6px; }
.stat-value { font-size: 24px; font-weight: 600; }
.stat-value.filename { font-size: 15px; word-break: break-all; }

/* 命中列表 */
.matched-list {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.list-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 12px;
  font-size: 15px;
  font-weight: 600;
  color: #323233;
}

.matched-item {
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
  border-left: 4px solid #dcdee0;
  background: #fafafa;
}

.matched-item.risk-high   { border-left-color: #ee0a24; background: #fff5f5; }
.matched-item.risk-medium { border-left-color: #ff976a; background: #fffaf5; }
.matched-item.risk-low    { border-left-color: #1989fa; background: #f5f9ff; }
.matched-item:last-child  { margin-bottom: 0; }

.item-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.row-number { font-size: 13px; font-weight: 600; color: #323233; }

.match-reason-bar {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 6px 10px;
  background: rgba(0,0,0,0.04);
  border-radius: 6px;
  font-size: 13px;
  color: #323233;
  margin-bottom: 10px;
  line-height: 1.5;
}

.risk-high .match-reason-bar   { background: rgba(238,10,36,0.08); color: #c00; }
.risk-medium .match-reason-bar { background: rgba(255,151,106,0.12); color: #b05000; }

.two-col { display: flex; gap: 10px; }

.col-block {
  flex: 1;
  min-width: 0;
  background: rgba(255,255,255,0.7);
  border-radius: 6px;
  padding: 8px;
}

.blacklist-col {
  background: rgba(238,10,36,0.04);
  border: 1px solid rgba(238,10,36,0.12);
}

.col-title { font-size: 12px; font-weight: 600; color: #646566; margin-bottom: 6px; padding-bottom: 4px; border-bottom: 1px solid #f0f0f0; }

.info-row { display: flex; flex-direction: column; margin-bottom: 5px; }
.info-row:last-child { margin-bottom: 0; }
.info-row .label { font-size: 11px; color: #969799; margin-bottom: 1px; }
.info-row .value { font-size: 13px; color: #323233; word-break: break-all; line-height: 1.4; }
.info-row .value.reason { color: #ee0a24; font-size: 12px; }

.action-buttons { display: flex; flex-direction: column; gap: 12px; }

.loading-wrapper { display: flex; align-items: center; justify-content: center; height: 100%; }

:deep(.van-nav-bar) { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
:deep(.van-nav-bar__title) { color: #fff; font-weight: 600; }
:deep(.van-nav-bar .van-icon) { color: #fff; }
</style>

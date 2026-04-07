<template>
  <div class="screening-detail">
    <van-nav-bar
      title="检查详情"
      left-arrow
      @click-left="onBack"
      fixed
      placeholder
    />

    <div v-if="detail" class="content-container">
      <!-- 统计信息 -->
      <div class="stats-card">
        <div class="stat-item">
          <div class="stat-label">文件名</div>
          <div class="stat-value">{{ detail.file_name }}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">检查时间</div>
          <div class="stat-value">{{ formatTime(detail.screening_time) }}</div>
        </div>
        <div class="stat-row">
          <div class="stat-item">
            <div class="stat-label">总订单数</div>
            <div class="stat-value">{{ detail.total_orders }}</div>
          </div>
          <div class="stat-item danger">
            <div class="stat-label">命中黑名单</div>
            <div class="stat-value">{{ detail.matched_count }}</div>
          </div>
        </div>
      </div>

      <!-- 命中详情列表 -->
      <div v-if="detail.details && detail.details.length > 0" class="details-list">
        <div class="list-header">
          <van-icon name="warning-o" color="#ee0a24" />
          <span>命中黑名单详情</span>
        </div>
        <div
          v-for="(item, index) in detail.details"
          :key="item.id"
          class="detail-item"
          :class="'risk-' + item.risk_level.toLowerCase()"
        >
          <!-- 卡片头部 -->
          <div class="item-header">
            <span class="item-number">跟团号 {{ item.group_no || ('#' + (index + 1)) }}</span>
            <van-tag :type="getRiskLevelType(item.risk_level)" size="medium">
              {{ getRiskLevelText(item.risk_level) }}
            </van-tag>
          </div>

          <!-- 命中原因 -->
          <div class="match-reason-bar">
            <van-icon name="warning" />
            <span>{{ item.match_reason || getMatchTypeText(item.match_type) }}</span>
          </div>

          <div class="two-col">
            <!-- 左：订单信息 -->
            <div class="col-block">
              <div class="col-title">📦 订单信息</div>
              <div class="info-row">
                <span class="label">下单人</span>
                <span class="value">{{ item.ktt_name || '-' }}</span>
              </div>
              <div class="info-row">
                <span class="label">收货人</span>
                <span class="value">{{ item.order_name || '-' }}</span>
              </div>
              <div class="info-row">
                <span class="label">电话</span>
                <span class="value">{{ item.order_phone || '-' }}</span>
              </div>
              <div class="info-row">
                <span class="label">地址</span>
                <span class="value">{{ item.order_address || '-' }}</span>
              </div>
            </div>

            <!-- 右：黑名单信息 -->
            <div class="col-block blacklist-col">
              <div class="col-title">🚫 黑名单信息</div>
              <div class="info-row">
                <span class="label">KTT名</span>
                <span class="value">{{ item.blacklist_ktt_name || '-' }}</span>
              </div>
              <div class="info-row">
                <span class="label">下单名</span>
                <span class="value">{{ item.blacklist_order_name || '-' }}</span>
              </div>
              <div class="info-row">
                <span class="label">电话</span>
                <span class="value">{{ (item.blacklist_phones || []).join('、') || '-' }}</span>
              </div>
              <div class="info-row">
                <span class="label">地址</span>
                <span class="value">{{ item.blacklist_address1 || '-' }}</span>
              </div>
              <div v-if="item.blacklist_reason" class="info-row">
                <span class="label">原因</span>
                <span class="value reason">{{ item.blacklist_reason }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 无命中 -->
      <van-empty
        v-else
        description="未检测到黑名单订单"
        image="success"
      />
    </div>

    <!-- 加载中 -->
    <van-loading v-else class="loading-container" size="24px" vertical>
      加载中...
    </van-loading>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast } from 'vant'

const router = useRouter()
const route = useRoute()

const detail = ref(null)

// 加载详情
const loadDetail = async () => {
  try {
    const token = localStorage.getItem('access_token')
    const response = await fetch(`/api/screening/history/${route.params.id}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (!response.ok) {
      throw new Error('加载失败')
    }

    detail.value = await response.json()
  } catch (error) {
    showToast('加载失败：' + error.message)
    router.back()
  }
}

// 风险等级类型
const getRiskLevelType = (level) => {
  const types = {
    'HIGH': 'danger',
    'MEDIUM': 'warning',
    'LOW': 'primary'
  }
  return types[level] || 'default'
}

// 风险等级文本
const getRiskLevelText = (level) => {
  const texts = {
    'HIGH': '高风险',
    'MEDIUM': '中风险',
    'LOW': '低风险'
  }
  return texts[level] || level
}

// 匹配类型文本
const getMatchTypeText = (type) => {
  const texts = {
    'PHONE':              '电话号码完全一致',
    'NAME_EXACT_ADDRESS': '名字完全一致 + 地址高度匹配',
    'NAME_EXACT':         '名字完全一致',
    'NAME_PARTIAL':       '名字部分相似',
    'ADDRESS_ONLY':       '地址高度匹配',
  }
  return texts[type] || type
}

// 格式化时间
const formatTime = (timeStr) => {
  const date = new Date(timeStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')
  const second = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hour}:${minute}:${second}`
}

// 返回
const onBack = () => {
  router.back()
}

onMounted(() => {
  loadDetail()
})
</script>

<style scoped>
.screening-detail {
  min-height: 100vh;
  background: #f7f8fa;
  padding-bottom: 20px;
}

.content-container {
  padding: 16px;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 50vh;
}

/* 统计卡片 */
.stats-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  color: #fff;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.stat-row {
  display: flex;
  gap: 16px;
  margin-top: 16px;
}

.stat-item {
  margin-bottom: 12px;
}

.stat-item:last-child {
  margin-bottom: 0;
}

.stat-row .stat-item {
  flex: 1;
  margin-bottom: 0;
}

.stat-item.danger {
  background: rgba(238, 10, 36, 0.2);
  border-radius: 8px;
  padding: 12px;
}

.stat-label {
  font-size: 13px;
  opacity: 0.9;
  margin-bottom: 6px;
}

.stat-value {
  font-size: 16px;
  font-weight: 600;
  word-break: break-all;
}

.stat-row .stat-value {
  font-size: 24px;
}

/* 详情列表 */
.details-list {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
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

.detail-item {
  background: #fafafa;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
  border-left: 4px solid #dcdee0;
}

.detail-item.risk-high   { border-left-color: #ee0a24; background: #fff5f5; }
.detail-item.risk-medium { border-left-color: #ff976a; background: #fffaf5; }
.detail-item.risk-low    { border-left-color: #1989fa; background: #f5f9ff; }
.detail-item:last-child  { margin-bottom: 0; }

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.item-number {
  font-size: 14px;
  font-weight: 600;
  color: #323233;
}

/* 命中原因条 */
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

/* 双栏布局 */
.two-col {
  display: flex;
  gap: 10px;
}

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

.col-title {
  font-size: 12px;
  font-weight: 600;
  color: #646566;
  margin-bottom: 6px;
  padding-bottom: 4px;
  border-bottom: 1px solid #f0f0f0;
}

.info-row {
  display: flex;
  flex-direction: column;
  margin-bottom: 5px;
}

.info-row:last-child { margin-bottom: 0; }

.info-row .label {
  font-size: 11px;
  color: #969799;
  margin-bottom: 1px;
}

.info-row .value {
  font-size: 13px;
  color: #323233;
  word-break: break-all;
  line-height: 1.4;
}

.info-row .value.reason {
  color: #ee0a24;
  font-size: 12px;
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

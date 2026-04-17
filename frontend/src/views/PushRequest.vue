<template>
  <div class="push-request-page">
    <van-nav-bar title="申请推送至系统库" left-arrow @click-left="$router.back()" fixed placeholder />

    <div class="content">
      <!-- 条目信息 -->
      <div class="entry-card" v-if="entry">
        <div class="entry-header">
          <span class="entry-name">{{ entry.ktt_name || '未知' }}</span>
          <van-tag :type="getRiskType(entry.risk_level)" round>{{ getRiskText(entry.risk_level) }}</van-tag>
        </div>
        <div class="entry-reason" v-if="entry.blacklist_reason">
          <van-icon name="warning-o" />
          <span>{{ entry.blacklist_reason }}</span>
        </div>
      </div>

      <!-- 证据填写 -->
      <div class="evidence-section">
        <div class="section-title">填写证据（必填，至少10字）</div>
        <van-field
          v-model="evidence"
          type="textarea"
          placeholder="请描述证据，例如：订单截图说明、沟通记录等，至少10个字符"
          rows="5"
          autosize
          maxlength="1000"
          show-word-limit
          :class="{ 'field-error': evidenceError }"
        />
        <div class="error-tip" v-if="evidenceError">{{ evidenceError }}</div>
      </div>

      <div class="tip-box">
        <van-icon name="info-o" />
        <span>申请通过后，该条目将加入系统黑名单，帮助所有用户识别风险买家。管理员将在审核后通知您结果。</span>
      </div>

      <van-button type="primary" block round :loading="submitting" @click="onSubmit" class="submit-btn">
        提交申请
      </van-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import { blacklistAPI } from '@/api/blacklist'

const route = useRoute()
const router = useRouter()
const entry = ref(null)
const evidence = ref('')
const evidenceError = ref('')
const submitting = ref(false)

const getRiskType = (level) => ({ HIGH: 'danger', MEDIUM: 'warning', LOW: 'success' }[level] || 'default')
const getRiskText = (level) => ({ HIGH: '高风险', MEDIUM: '中风险', LOW: '低风险' }[level] || level)

onMounted(async () => {
  try {
    entry.value = await blacklistAPI.getDetail(route.params.id)
  } catch (e) {
    showToast('加载失败')
    router.back()
  }
})

const onSubmit = async () => {
  evidenceError.value = ''
  if (!evidence.value || evidence.value.trim().length < 10) {
    evidenceError.value = '证据描述不能少于10个字符'
    return
  }
  submitting.value = true
  try {
    await blacklistAPI.pushRequest(Number(route.params.id), evidence.value.trim())
    showToast('申请已提交，等待管理员审核')
    router.back()
  } catch (e) {
    const status = e.response?.status
    const detail = e.response?.data?.detail
    if (status === 409) {
      showToast('该条目已有待审核的推送申请')
    } else if (status === 400) {
      evidenceError.value = detail || '证据描述不足'
    } else {
      showToast('提交失败：' + (detail || e.message))
    }
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.push-request-page { min-height: 100vh; background: #f7f8fa; padding-bottom: 40px; }
.content { padding: 16px; }
.entry-card {
  background: #fff; border-radius: 12px; padding: 16px;
  margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,.06);
}
.entry-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.entry-name { font-size: 17px; font-weight: 600; color: #323233; }
.entry-reason { display: flex; align-items: flex-start; gap: 6px; font-size: 13px; color: #646566; }
.section-title { font-size: 14px; font-weight: 600; color: #323233; margin-bottom: 8px; }
.evidence-section { background: #fff; border-radius: 12px; padding: 16px; margin-bottom: 16px; }
.field-error :deep(.van-field__control) { border-color: #ee0a24; }
.error-tip { color: #ee0a24; font-size: 12px; margin-top: 4px; }
.tip-box {
  display: flex; align-items: flex-start; gap: 8px; padding: 12px 16px;
  background: rgba(25,137,250,.08); border-radius: 8px; font-size: 13px;
  color: #1989fa; margin-bottom: 24px;
}
.submit-btn { height: 48px; font-size: 16px; font-weight: 600; }
</style>

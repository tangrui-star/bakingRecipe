<template>
  <div class="blacklist-edit">
    <van-nav-bar
      :title="isEdit ? '编辑黑名单' : '添加黑名单'"
      left-arrow
      @click-left="onBack"
      fixed
      placeholder
    />

    <div class="form-container">
      <van-form @submit="onSubmit">
        <!-- 基本信息 -->
        <div class="form-section">
          <div class="section-title">
            <van-icon name="user-o" />
            <span>基本信息</span>
          </div>
          
          <van-cell-group inset>
            <van-field
              v-model="formData.order_name_phone"
              label="订单姓名"
              placeholder="请输入订单姓名"
              required
              :rules="[{ required: true, message: '请输入订单姓名' }]"
            />

            <van-field
              v-model="formData.ktt_name"
              label="KTT名字"
              placeholder="请输入KTT名字"
            />

            <van-field
              v-model="formData.wechat_name"
              label="微信名字"
              placeholder="请输入微信名字"
            />

            <van-field
              v-model="formData.wechat_id"
              label="微信号"
              placeholder="请输入微信号"
            />
          </van-cell-group>
        </div>

        <!-- 联系方式 -->
        <div class="form-section">
          <div class="section-title">
            <van-icon name="phone-o" />
            <span>联系方式</span>
          </div>
          
          <van-cell-group inset>
            <div v-for="(phone, index) in phoneNumbers" :key="`phone-${index}`" class="phone-input-group">
              <van-field
                :model-value="phoneNumbers[index]"
                @update:model-value="updatePhone(index, $event)"
                :label="`电话${index + 1}`"
                placeholder="请输入手机号码"
                type="tel"
                maxlength="11"
                :required="index === 0"
                :rules="index === 0 ? [{ required: true, message: '请至少输入一个电话号码' }] : []"
              >
                <template #button>
                  <van-button 
                    v-if="phoneNumbers.length > 1"
                    size="small" 
                    type="danger" 
                    plain
                    @click="removePhone(index)"
                  >
                    删除
                  </van-button>
                </template>
              </van-field>
            </div>
            
            <van-cell>
              <van-button 
                block 
                plain 
                type="primary" 
                icon="plus"
                @click="addPhone"
              >
                添加电话号码
              </van-button>
            </van-cell>
          </van-cell-group>
        </div>

        <!-- 地址信息 -->
        <div class="form-section">
          <div class="section-title">
            <van-icon name="location-o" />
            <span>地址信息</span>
          </div>
          
          <van-cell-group inset>
            <van-field
              v-model="formData.order_address1"
              label="地址1"
              type="textarea"
              placeholder="请输入下单地址1"
              rows="2"
              autosize
            />

            <van-field
              v-model="formData.order_address2"
              label="地址2"
              type="textarea"
              placeholder="请输入下单地址2"
              rows="2"
              autosize
            />
          </van-cell-group>
        </div>

        <!-- 黑名单信息 -->
        <div class="form-section">
          <div class="section-title">
            <van-icon name="warning-o" />
            <span>黑名单信息</span>
          </div>
          
          <van-cell-group inset>
            <van-field
              v-model="formData.blacklist_reason"
              label="入黑原因"
              type="textarea"
              placeholder="请输入入黑名单原因"
              rows="3"
              autosize
              required
              :rules="[{ required: true, message: '请输入入黑名单原因' }]"
            />

            <van-field
              v-model="riskLevelText"
              is-link
              readonly
              label="风险等级"
              placeholder="请选择风险等级"
              @click="showRiskLevelPicker = true"
              required
              :rules="[{ required: true, message: '请选择风险等级' }]"
            />
          </van-cell-group>
        </div>

        <!-- 提交按钮 -->
        <div class="submit-section">
          <van-button 
            round 
            block 
            type="primary" 
            native-type="submit" 
            :loading="submitting"
            size="large"
          >
            <van-icon name="success" />
            {{ isEdit ? '保存修改' : '添加到黑名单' }}
          </van-button>
        </div>
      </van-form>
    </div>

    <!-- 风险等级选择器 -->
    <van-popup v-model:show="showRiskLevelPicker" position="bottom" round>
      <van-picker
        :columns="riskLevelColumns"
        @confirm="onRiskLevelConfirm"
        @cancel="showRiskLevelPicker = false"
      />
    </van-popup>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast } from 'vant'
import { blacklistAPI } from '@/api/blacklist'

const router = useRouter()
const route = useRoute()

// 是否为编辑模式
const isEdit = computed(() => !!route.params.id)

// 表单数据
const formData = ref({
  order_name_phone: '', // 订单姓名
  ktt_name: '',
  wechat_name: '',
  wechat_id: '',
  order_address1: '',
  order_address2: '',
  blacklist_reason: '',
  risk_level: 'MEDIUM'
})

// 电话号码列表
const phoneNumbers = ref([''])

// 提交状态
const submitting = ref(false)

// 风险等级选择器
const showRiskLevelPicker = ref(false)
const riskLevelColumns = [
  { text: '高风险', value: 'HIGH' },
  { text: '中风险', value: 'MEDIUM' },
  { text: '低风险', value: 'LOW' }
]

// 风险等级文本
const riskLevelText = computed(() => {
  const item = riskLevelColumns.find(col => col.value === formData.value.risk_level)
  return item ? item.text : ''
})

// 获取店铺ID
const getShopId = () => {
  const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}')
  const shopId = userInfo.shop_id || '2c2f8124-150b-4351-956a-5d86d2f377aa' // 使用默认店铺ID
  console.log('Shop ID:', shopId)
  return shopId
}

// 添加电话号码
const addPhone = () => {
  phoneNumbers.value.push('')
}

// 更新电话号码
const updatePhone = (index, value) => {
  phoneNumbers.value[index] = value
}

// 删除电话号码
const removePhone = (index) => {
  if (phoneNumbers.value.length > 1) {
    phoneNumbers.value.splice(index, 1)
  } else {
    showToast('至少保留一个电话号码输入框')
  }
}

// 验证电话号码格式
const validatePhone = (phone) => {
  if (!phone) return true // 允许空
  const phonePattern = /^1[3-9]\d{9}$/
  return phonePattern.test(phone)
}

// 加载详情
const loadDetail = async () => {
  try {
    const data = await blacklistAPI.getDetail(route.params.id)
    formData.value = {
      order_name_phone: data.order_name_phone || '',
      ktt_name: data.ktt_name || '',
      wechat_name: data.wechat_name || '',
      wechat_id: data.wechat_id || '',
      order_address1: data.order_address1 || '',
      order_address2: data.order_address2 || '',
      blacklist_reason: data.blacklist_reason || '',
      risk_level: data.risk_level || 'MEDIUM'
    }
    
    // 加载电话号码列表
    if (data.phone_numbers && data.phone_numbers.length > 0) {
      phoneNumbers.value = data.phone_numbers
    } else {
      phoneNumbers.value = ['']
    }
  } catch (error) {
    showToast('加载失败：' + (error.response?.data?.detail || error.message))
  }
}

// 风险等级确认
const onRiskLevelConfirm = ({ selectedOptions }) => {
  formData.value.risk_level = selectedOptions[0].value
  showRiskLevelPicker.value = false
}

// 返回
const onBack = () => {
  router.back()
}

// 提交
const onSubmit = async () => {
  // 验证电话号码
  const validPhones = phoneNumbers.value.filter(phone => phone.trim())
  
  if (validPhones.length === 0) {
    showToast('请至少输入一个电话号码')
    return
  }
  
  const invalidPhones = validPhones.filter(phone => !validatePhone(phone))
  
  if (invalidPhones.length > 0) {
    showToast('请输入正确的手机号码格式')
    return
  }

  submitting.value = true

  try {
    // 构建提交数据
    const submitData = {
      ...formData.value,
      shop_id: getShopId(),
      phone_numbers: validPhones // 直接发送电话号码数组
    }

    if (isEdit.value) {
      await blacklistAPI.update(route.params.id, submitData)
      showToast('保存成功')
    } else {
      await blacklistAPI.create(submitData)
      showToast('添加成功')
    }

    router.back()
  } catch (error) {
    showToast('操作失败：' + (error.response?.data?.detail || error.message))
  } finally {
    submitting.value = false
  }
}

// 初始化
onMounted(() => {
  if (isEdit.value) {
    loadDetail()
  }
})
</script>

<style scoped>
.blacklist-edit {
  min-height: 100vh;
  background: linear-gradient(180deg, #f7f8fa 0%, #ffffff 100%);
  padding-bottom: 100px;
}

.form-container {
  padding: 16px;
}

/* 表单分组 */
.form-section {
  margin-bottom: 20px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  font-size: 15px;
  font-weight: 600;
  color: #323233;
}

.section-title .van-icon {
  color: #1989fa;
  font-size: 18px;
}

/* 表单组样式 */
.van-cell-group {
  margin-top: 8px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

/* 字段样式优化 */
:deep(.van-field__label) {
  color: #646566;
  font-weight: 500;
}

:deep(.van-field__control) {
  color: #323233;
}

:deep(.van-field__control::placeholder) {
  color: #c8c9cc;
}

/* 必填标记 */
:deep(.van-field--required .van-field__label::before) {
  color: #ee0a24;
}

/* 电话输入组 */
.phone-input-group {
  position: relative;
}

.phone-input-group:not(:last-child) {
  border-bottom: 1px solid #f0f0f0;
}

.phone-input-group .van-button {
  margin-left: 8px;
}

/* 提交按钮区域 */
.submit-section {
  margin-top: 32px;
  margin-bottom: 40px;
  padding: 0 16px;
}

.submit-section .van-button {
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(25, 137, 250, 0.3);
}

.submit-section .van-icon {
  margin-right: 6px;
}

/* 选择器弹窗 */
:deep(.van-popup--round) {
  border-radius: 16px 16px 0 0;
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

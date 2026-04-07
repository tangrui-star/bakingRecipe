<template>
  <div class="order-process">
    <van-nav-bar title="订单数据处理" left-arrow @click-left="() => router.back()" fixed placeholder />

    <div class="content">
      <!-- 操作卡片 -->
      <div class="section-card">
        <!-- 跟团号 -->
        <div class="row-between">
          <div class="section-title">跟团号 <span class="badge">{{ dynamicTags.length }}</span></div>
          <van-button size="mini" type="primary" plain @click="showTagDialog = true">+ 添加</van-button>
        </div>
        <div class="tag-area" v-if="dynamicTags.length > 0">
          <van-tag
            v-for="tag in dynamicTags" :key="tag"
            closeable type="primary" size="medium"
            @close="removeTag(tag)"
          >{{ tag }}</van-tag>
        </div>
        <div v-else class="empty-tip">点击"添加"录入跟团号</div>

        <!-- 文件上传 -->
        <div class="row-between" style="margin-top:14px">
          <div class="section-title">订单文件</div>
          <van-button v-if="fileName" size="mini" plain icon="cross" @click="clearFile" />
        </div>
        <input ref="fileInputRef" type="file" accept=".xlsx,.xls" style="display:none" @change="onFileChange" />
        <div class="file-btn" @click="fileInputRef.click()">
          <van-icon name="description" size="20" color="#1989fa" />
          <span>{{ fileName || '点击选择 Excel 文件' }}</span>
        </div>

        <!-- 操作按钮 -->
        <van-button
          type="primary" block size="large"
          :loading="processing" :disabled="!fileData"
          style="margin-top:14px"
          @click="handleProcess"
        >数据处理生成</van-button>
        <van-button block plain size="normal" style="margin-top:8px" @click="handleReset">重置</van-button>
      </div>

      <!-- 历史记录 -->
      <div class="section-card" v-if="historyList.length > 0">
        <div class="section-title">历史记录</div>
        <div v-for="item in historyList" :key="item.id" class="history-item">
          <div class="row-between">
            <span class="history-file">{{ item.file_name }}</span>
            <span class="history-time">{{ formatTime(item.created_at) }}</span>
          </div>
          <div class="history-sub">
            跟团号 {{ (item.group_nos || []).join(' ') }} · {{ item.total_orders }} 条 · {{ item.product_types }} 种商品
          </div>
        </div>
      </div>

      <!-- 结果区 -->
      <div v-if="hasResult" class="result-section">
        <div class="row-between section-card" style="margin-bottom:0;border-radius:12px 12px 0 0">
          <div class="section-title" style="margin-bottom:0">处理结果</div>
          <van-button size="small" type="success" icon="down" @click="exportExcel">导出</van-button>
        </div>

        <van-tabs v-model:active="activeTab" sticky :offset-top="46" animated swipeable>
          <!-- 数量汇总 -->
          <van-tab :title="`汇总(${summaryData.length})`">
            <div class="card-list">
              <div v-for="row in summaryData" :key="row.id" class="summary-card">
                <div class="row-between">
                  <span class="product-name">{{ row['商品'] }}</span>
                  <span class="qty-badge">× {{ row['数量'] }}</span>
                </div>
                <div class="category-tag">{{ row['分类'] || '未分类' }}</div>
                <div class="detail-text">{{ row['跟团号及数量'] }}</div>
              </div>
            </div>
          </van-tab>

          <!-- 配方计算 -->
          <van-tab :title="`配方(${recipeData.length})`">
            <div class="card-list">
              <div v-for="row in recipeData" :key="row.formulaId" class="recipe-card">
                <div class="recipe-header">
                  <span class="recipe-name">{{ row.formulaName }}</span>
                  <span class="recipe-batch">批次 {{ row.formulaNumber }}</span>
                </div>
                <div class="material-grid">
                  <template v-for="i in 7" :key="i">
                    <div v-if="row[`subitem${i}`]" class="material-item">
                      <div class="material-name">{{ row[`subitem${i}`] }}</div>
                      <div class="material-weight">{{ row[`subitem${i}Weight`] }}</div>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </van-tab>

          <!-- 团员备注 -->
          <van-tab :title="`团员(${memberRemarkData.length})`">
            <div class="card-list">
              <div v-for="(row, i) in memberRemarkData" :key="i" class="remark-card">
                <div class="row-between">
                  <span class="gno">跟团号 {{ row['跟团号'] }}</span>
                  <span class="person">{{ row['下单人'] }}</span>
                </div>
                <div class="remark-text member">{{ row['团员备注'] }}</div>
                <div class="product-small">{{ row['商品'] }}</div>
              </div>
            </div>
          </van-tab>

          <!-- 团长备注 -->
          <van-tab :title="`团长(${leaderRemarkData.length})`">
            <div class="card-list">
              <div v-for="(row, i) in leaderRemarkData" :key="i" class="remark-card">
                <div class="row-between">
                  <span class="gno">跟团号 {{ row['跟团号'] }}</span>
                  <span class="person">{{ row['下单人'] }}</span>
                </div>
                <div class="remark-text leader">{{ row['团长备注'] }}</div>
                <div class="product-small">{{ row['商品'] }}</div>
              </div>
            </div>
          </van-tab>

          <!-- 数据源 -->
          <van-tab :title="`数据(${filteredData.length})`">
            <div class="card-list">
              <div v-for="(row, i) in filteredData" :key="i" class="source-card">
                <div class="row-between">
                  <span class="gno">{{ row['跟团号'] }} · {{ row['下单人'] }}</span>
                  <span class="qty-badge">× {{ row['数量'] }}</span>
                </div>
                <div class="product-name" style="margin:4px 0">{{ row['商品'] }}</div>
                <div class="receiver-info">{{ row['收货人'] }} {{ row['联系电话'] }}</div>
              </div>
            </div>
          </van-tab>

          <!-- 打印单号 -->
          <van-tab :title="`打印(${printData.length})`">
            <div class="card-list">
              <div v-for="item in printData" :key="item.formulaNumber" class="print-card">
                <pre class="print-content">{{ item.formulaInfor }}</pre>
              </div>
            </div>
          </van-tab>
        </van-tabs>
      </div>
    </div>

    <!-- 跟团号输入弹窗 -->
    <van-dialog
      v-model:show="showTagDialog"
      title="录入跟团号"
      show-cancel-button
      confirm-button-text="确认"
      @confirm="confirmTagInput"
      @cancel="tagInput = ''"
    >
      <div style="padding:16px">
        <van-field
          v-model="tagInput"
          type="textarea"
          rows="3"
          placeholder="输入跟团号，多个用空格或换行分隔&#10;例：101 102 103"
          autofocus
        />
      </div>
    </van-dialog>

    <!-- 密码弹窗 -->
    <van-dialog
      v-model:show="pwdDialogVisible"
      title="文件受密码保护"
      show-cancel-button
      @confirm="onPwdConfirm"
    >
      <div style="padding:16px">
        <van-field v-model="filePassword" placeholder="请输入文件密码" type="password" />
      </div>
    </van-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import * as XLSX from 'xlsx'
import { calcRecipes } from '@/utils/recipeRules'

const router = useRouter()

const dynamicTags = ref([])
const showTagDialog = ref(false)
const tagInput = ref('')

const fileInputRef = ref(null)
const fileName = ref('')
const fileData = ref(null)

const processing = ref(false)
const hasResult = ref(false)
const activeTab = ref(0)

const summaryData = ref([])
const recipeData = ref([])
const memberRemarkData = ref([])
const leaderRemarkData = ref([])
const filteredData = ref([])
const printData = ref([])
const historyList = ref([])

const pwdDialogVisible = ref(false)
const filePassword = ref('')

// ── 跟团号 ───────────────────────────────────────────────────
const confirmTagInput = () => {
  const nums = tagInput.value.split(/[\s\n,，]+/)
    .map(s => Number(s.trim()))
    .filter(n => Number.isInteger(n) && n > 0)
  dynamicTags.value = [...new Set([...dynamicTags.value, ...nums])].sort((a, b) => a - b)
  tagInput.value = ''
}

const removeTag = (tag) => {
  dynamicTags.value = dynamicTags.value.filter(t => t !== tag)
}

// ── 文件 ─────────────────────────────────────────────────────
const onFileChange = (e) => {
  const file = e.target.files[0]
  if (!file) return
  fileName.value = file.name
  const reader = new FileReader()
  reader.onload = (ev) => { fileData.value = ev.target.result }
  reader.readAsArrayBuffer(file)
  e.target.value = ''
}

const clearFile = () => { fileName.value = ''; fileData.value = null }

// ── 解析 Excel ───────────────────────────────────────────────
const parseExcel = (buffer, password = '') => {
  const wb = XLSX.read(buffer, { type: 'array', password: password || undefined })
  const ws = wb.Sheets[wb.SheetNames[0]]
  if (!ws) throw new Error('未找到工作表')
  return XLSX.utils.sheet_to_json(ws, { defval: '' })
}

// ── 处理 ─────────────────────────────────────────────────────
const handleProcess = async () => {
  if (!fileData.value) return
  processing.value = true
  try {
    let rows
    try { rows = parseExcel(fileData.value) }
    catch (e) {
      if (String(e).includes('password')) { pwdDialogVisible.value = true; processing.value = false; return }
      throw new Error('读取文件时出错，请检查文件格式')
    }
    doProcess(rows)
    await saveRecord()
    await loadHistory()
    hasResult.value = true
    activeTab.value = 0
    showToast({ message: '处理完成', position: 'bottom' })
  } catch (e) {
    showToast(e.message || '处理失败')
  } finally {
    processing.value = false
  }
}

const onPwdConfirm = () => {
  try {
    doProcess(parseExcel(fileData.value, filePassword.value))
    saveRecord(); loadHistory()
    hasResult.value = true
    showToast({ message: '处理完成', position: 'bottom' })
  } catch { showToast('密码错误，请重新输入') }
}

const doProcess = (rows) => {
  const tagSet = new Set(dynamicTags.value)
  const filtered = rows.filter(r => tagSet.has(Number(r['跟团号'])))
  filteredData.value = filtered

  // 商品汇总
  const map = {}
  filtered.forEach(r => {
    const key = `${r['商品']}__${r['分类'] || ''}`
    if (!map[key]) map[key] = { 商品: r['商品'], 分类: r['分类'] || '', 数量: 0, details: {} }
    const qty = Number(r['数量']) || 1
    map[key].数量 += qty
    const gno = Number(r['跟团号'])
    map[key].details[gno] = (map[key].details[gno] || 0) + qty
  })
  let summary = Object.values(map)
  summary.sort((a, b) => a.分类 < b.分类 ? -1 : a.分类 > b.分类 ? 1 : b.数量 - a.数量)
  summaryData.value = summary.map((s, i) => ({
    id: i + 1, 分类: s.分类, 商品: s.商品, 数量: s.数量,
    跟团号及数量: Object.entries(s.details).map(([k, v]) => `${k}:${v}`).join('、'),
  }))

  recipeData.value = calcRecipes(summaryData.value)

  const mSeen = new Set()
  memberRemarkData.value = filtered.filter(r => {
    if (r['团员备注'] && !mSeen.has(r['跟团号'])) { mSeen.add(r['跟团号']); return true }
    return false
  })

  const lSeen = new Set()
  leaderRemarkData.value = filtered.filter(r => {
    if (r['团长备注'] && !lSeen.has(r['跟团号'])) { lSeen.add(r['跟团号']); return true }
    return false
  })

  const pSeen = new Set()
  printData.value = filtered
    .filter(r => { if (!pSeen.has(r['跟团号'])) { pSeen.add(r['跟团号']); return true } return false })
    .map(r => {
      const addr = r['详细地址'] || ''
      const lines = []
      for (let i = 0; i < addr.length; i += 16) lines.push(addr.slice(i, i + 16))
      return {
        formulaNumber: r['跟团号'],
        formulaInfor: [r['跟团号'], `收货信息：${r['收货人']} ${r['联系电话']}`, ...lines].join('\n')
      }
    })
}

// ── 导出 ─────────────────────────────────────────────────────
const exportExcel = () => {
  const now = new Date()
  const p = `${now.getMonth() + 1}月${now.getDate()}日`
  const wb = XLSX.utils.book_new()
  const app = (data, name) => XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(data), name)

  app(summaryData.value.map(r => ({ 序号: r.id, 分类: r['分类'], 商品: r['商品'], 数量: r['数量'], 跟团号及数量: r['跟团号及数量'] })), `${p}数据汇总`)
  app(memberRemarkData.value, `${p}团员备注`)
  app(leaderRemarkData.value, `${p}团长备注`)
  app(filteredData.value, `${p}单号数据源`)
  app(recipeData.value.map(r => {
    const row = { 配方名称: r.formulaName, 批次数: r.formulaNumber }
    for (let i = 1; i <= 7; i++) if (r[`subitem${i}`]) { row[`材料${i}`] = r[`subitem${i}`]; row[`用量${i}`] = r[`subitem${i}Weight`] }
    return row
  }), `${p}配方计算`)
  app(printData.value.map(r => ({ 跟团号: r.formulaInfor })), `${p}批量打印单号`)

  const buf = XLSX.write(wb, { bookType: 'xlsx', type: 'array' })
  const url = URL.createObjectURL(new Blob([buf], { type: 'application/octet-stream' }))
  const a = document.createElement('a'); a.href = url; a.download = `${p}数据结果.xlsx`; a.click()
  URL.revokeObjectURL(url)
}

// ── 数据库 ───────────────────────────────────────────────────
const getShopId = () => JSON.parse(localStorage.getItem('user_info') || '{}').shop_id || ''
const getToken = () => localStorage.getItem('access_token')

const saveRecord = async () => {
  if (!getShopId()) return
  try {
    await fetch('/api/order-process/save', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        shop_id: getShopId(), file_name: fileName.value,
        group_nos: dynamicTags.value, total_orders: filteredData.value.length,
        product_types: summaryData.value.length,
        summary: summaryData.value.slice(0, 10).map(r => ({ 商品: r['商品'], 数量: r['数量'] })),
      })
    })
  } catch { /* 静默 */ }
}

const loadHistory = async () => {
  const shopId = getShopId()
  if (!shopId) return
  try {
    const res = await fetch(`/api/order-process/history?shop_id=${shopId}&page=1&page_size=5`, {
      headers: { 'Authorization': `Bearer ${getToken()}` }
    })
    if (res.ok) historyList.value = (await res.json()).items || []
  } catch { /* 静默 */ }
}

const handleReset = () => {
  dynamicTags.value = []; fileName.value = ''; fileData.value = null
  hasResult.value = false; summaryData.value = []; recipeData.value = []
  memberRemarkData.value = []; leaderRemarkData.value = []; filteredData.value = []; printData.value = []
}

const formatTime = (t) => {
  const d = new Date(t)
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

onMounted(() => loadHistory())
</script>

<style scoped>
.order-process {
  min-height: 100vh;
  background: #f7f8fa;
  padding-bottom: 80px; /* TabBar高度 */
}

.content { padding: 12px; }

.section-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.row-between {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #323233;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.badge {
  font-size: 11px;
  font-weight: normal;
  background: #1989fa;
  color: #fff;
  padding: 1px 7px;
  border-radius: 10px;
}

/* 标签区 */
.tag-area {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 4px;
}

.empty-tip {
  font-size: 13px;
  color: #c8c9cc;
  padding: 4px 0 8px;
}

/* 文件按钮 */
.file-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  background: #f7f8fa;
  border-radius: 8px;
  border: 1px dashed #c8c9cc;
  cursor: pointer;
  font-size: 14px;
  color: #646566;
  min-height: 48px;
  transition: border-color 0.2s;
}

.file-btn:active { border-color: #1989fa; background: #e8f3ff; }

/* 历史记录 */
.history-item {
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}
.history-item:last-child { border-bottom: none; }
.history-file { font-size: 13px; font-weight: 500; color: #323233; }
.history-time { font-size: 12px; color: #969799; }
.history-sub  { font-size: 12px; color: #969799; margin-top: 3px; }

/* 结果区 */
.result-section { background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }

/* 卡片列表通用 */
.card-list { padding: 10px 12px 12px; display: flex; flex-direction: column; gap: 10px; }

/* 数量汇总卡片 */
.summary-card {
  background: #f7f8fa;
  border-radius: 8px;
  padding: 12px;
  border-left: 3px solid #1989fa;
}

.product-name {
  font-size: 14px;
  font-weight: 500;
  color: #323233;
  flex: 1;
  line-height: 1.4;
}

.qty-badge {
  font-size: 16px;
  font-weight: 700;
  color: #1989fa;
  white-space: nowrap;
  margin-left: 8px;
}

.category-tag {
  display: inline-block;
  font-size: 11px;
  color: #969799;
  background: #ebedf0;
  padding: 2px 8px;
  border-radius: 4px;
  margin: 6px 0 4px;
}

.detail-text {
  font-size: 12px;
  color: #969799;
  line-height: 1.5;
  word-break: break-all;
}

/* 配方卡片 */
.recipe-card {
  background: #f7f8fa;
  border-radius: 8px;
  padding: 12px;
  border-left: 3px solid #07c160;
}

.recipe-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.recipe-name {
  font-size: 14px;
  font-weight: 600;
  color: #323233;
}

.recipe-batch {
  font-size: 12px;
  color: #07c160;
  background: #e8f8ef;
  padding: 2px 8px;
  border-radius: 10px;
}

.material-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
}

.material-item {
  background: #fff;
  border-radius: 6px;
  padding: 6px 8px;
}

.material-name {
  font-size: 12px;
  color: #646566;
}

.material-weight {
  font-size: 14px;
  font-weight: 600;
  color: #323233;
  margin-top: 2px;
}

/* 备注卡片 */
.remark-card {
  background: #f7f8fa;
  border-radius: 8px;
  padding: 12px;
}

.gno { font-size: 12px; color: #969799; }
.person { font-size: 13px; font-weight: 500; color: #323233; }

.remark-text {
  font-size: 13px;
  line-height: 1.5;
  margin: 8px 0 6px;
  padding: 8px 10px;
  border-radius: 6px;
  word-break: break-all;
}

.remark-text.member { background: #fff7e6; color: #ed6a0c; border-left: 3px solid #ff976a; }
.remark-text.leader { background: #f0f9eb; color: #389e0d; border-left: 3px solid #52c41a; }

.product-small { font-size: 12px; color: #969799; }

/* 数据源卡片 */
.source-card {
  background: #f7f8fa;
  border-radius: 8px;
  padding: 10px 12px;
}

.receiver-info { font-size: 12px; color: #969799; }

/* 打印单号 */
.print-card {
  background: #f7f8fa;
  border-radius: 8px;
  padding: 12px;
  border: 1px solid #ebedf0;
}

.print-content {
  font-size: 13px;
  color: #323233;
  white-space: pre-wrap;
  margin: 0;
  font-family: 'Courier New', monospace;
  line-height: 1.8;
}

:deep(.van-nav-bar) { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
:deep(.van-nav-bar__title) { color: #fff; font-weight: 600; }
:deep(.van-nav-bar .van-icon) { color: #fff; }
:deep(.van-tabs__nav) { background: #fff; }
:deep(.van-tab) { font-size: 13px; }
</style>

<template>
  <div class="logistics-process">
    <van-nav-bar title="中通快递表生成" left-arrow @click-left="() => router.back()" fixed placeholder />

    <div class="content">
      <div class="section-card">
        <div class="section-title">上传物流 Excel</div>
        <div class="desc-text">上传打印单号格式的 Excel 文件，自动解析为中通快递对接表格</div>

        <input ref="fileInputRef" type="file" accept=".xlsx,.xls" style="display:none" @change="onFileChange" />
        <div class="file-btn" @click="fileInputRef.click()">
          <van-icon name="description" size="20" color="#1989fa" />
          <span>{{ fileName || '点击选择 Excel 文件' }}</span>
        </div>

        <div class="format-tip">
          <van-icon name="info-o" color="#ed6a0c" />
          <span>文件格式：每行一个单元格，内容为"跟团号\n收货信息：姓名 手机号\n地址..."</span>
        </div>

        <van-button
          type="primary" block size="large"
          :loading="processing" :disabled="!fileData"
          style="margin-top:14px"
          @click="handleProcess"
        >解析生成</van-button>
      </div>

      <!-- 结果 -->
      <div v-if="logisticsData.length > 0" class="section-card">
        <div class="row-between">
          <div class="section-title" style="margin-bottom:0">
            解析结果 <span class="badge">{{ logisticsData.length }}</span>
          </div>
          <van-button size="small" type="success" icon="down" @click="exportExcel">导出</van-button>
        </div>

        <div class="card-list">
          <div v-for="(row, i) in logisticsData" :key="i" class="logistics-card">
            <div class="row-between">
              <span class="l-name">{{ row['收件人姓名'] }}</span>
              <span class="l-phone">{{ row['收件人手机'] }}</span>
            </div>
            <div class="l-addr">{{ row['收件人地址'] }}</div>
            <div v-if="row['_groupNo']" class="l-gno">跟团号 {{ row['_groupNo'] }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import * as XLSX from 'xlsx'

const router = useRouter()

const fileInputRef = ref(null)
const fileName = ref('')
const fileData = ref(null)
const processing = ref(false)
const logisticsData = ref([])

const onFileChange = (e) => {
  const file = e.target.files[0]
  if (!file) return
  fileName.value = file.name
  const reader = new FileReader()
  reader.onload = (ev) => { fileData.value = ev.target.result }
  reader.readAsArrayBuffer(file)
  e.target.value = ''
}

const parseLogisticsText = (text) => {
  const result = {
    '订单号': '', '代收金额': '', '收件人姓名': '', '收件人手机': '',
    '收件人电话': '', '收件人地址': '', '收件人单位': '',
    '品名': '', '数量': '', '买家备注': '', '卖家备注': '', '_groupNo': ''
  }
  if (!text || text === 'nan') return result

  const lines = String(text).split('\n').map(l => l.trim()).filter(Boolean)
  if (!lines.length) return result

  result['_groupNo'] = lines[0]

  const receiverIdx = lines.findIndex(l => l.includes('收货信息') || l.includes('收件信息'))
  if (receiverIdx !== -1) {
    const m = lines[receiverIdx].match(/收货信息[：:]\s*(.+?)\s+(\d{10,11})/)
    if (m) {
      result['收件人姓名'] = m[1].trim()
      result['收件人手机'] = m[2]
      result['收件人电话'] = m[2]
    }
    result['收件人地址'] = lines.slice(receiverIdx + 1)
      .filter(l => !l.match(/品名|数量|备注|代收金额/))
      .join('').replace(/\s+/g, '')
  } else if (lines.length >= 2) {
    const m = lines[1].match(/([^\d]+?)\s+(\d{10,11})/)
    if (m) {
      result['收件人姓名'] = m[1].trim()
      result['收件人手机'] = m[2]
      result['收件人电话'] = m[2]
    }
    result['收件人地址'] = lines.slice(2).join('').replace(/\s+/g, '')
  }

  return result
}

const handleProcess = () => {
  if (!fileData.value) return
  processing.value = true
  try {
    const wb = XLSX.read(fileData.value, { type: 'array' })
    const ws = wb.Sheets[wb.SheetNames[0]]
    const rows = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '' })
    // 跳过第一行（表头"跟团号"）
    const parsed = rows.slice(1)
      .map(r => parseLogisticsText(String(r[0] || '')))
      .filter(r => r['收件人姓名'])
    logisticsData.value = parsed
    showToast({ message: `解析完成，共 ${parsed.length} 条`, position: 'bottom' })
  } catch {
    showToast('文件解析失败，请检查格式')
  } finally {
    processing.value = false
  }
}

const exportExcel = () => {
  const now = new Date()
  const p = `${now.getMonth() + 1}月${now.getDate()}日`
  const cols = ['订单号', '代收金额', '收件人姓名', '收件人手机', '收件人电话',
    '收件人地址', '收件人单位', '品名', '数量', '买家备注', '卖家备注']
  const data = logisticsData.value.map(r => {
    const row = {}
    cols.forEach(k => { row[k] = r[k] || '' })
    return row
  })
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(data), '中通快递')
  const buf = XLSX.write(wb, { bookType: 'xlsx', type: 'array' })
  const url = URL.createObjectURL(new Blob([buf], { type: 'application/octet-stream' }))
  const a = document.createElement('a')
  a.href = url
  a.download = `${p}中通快递.xlsx`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.logistics-process {
  min-height: 100vh;
  background: #f7f8fa;
  padding-bottom: 80px;
}

.content { padding: 12px; }

.section-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
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
  background: #07c160;
  color: #fff;
  padding: 1px 7px;
  border-radius: 10px;
}

.desc-text {
  font-size: 13px;
  color: #969799;
  margin-bottom: 12px;
  line-height: 1.5;
}

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
}

.file-btn:active { border-color: #1989fa; background: #e8f3ff; }

.format-tip {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-top: 10px;
  padding: 8px 10px;
  background: #fff7e6;
  border-radius: 6px;
  font-size: 12px;
  color: #ed6a0c;
  line-height: 1.5;
}

.row-between { display: flex; justify-content: space-between; align-items: center; }

.card-list { display: flex; flex-direction: column; gap: 10px; margin-top: 14px; }

.logistics-card {
  background: #f7f8fa;
  border-radius: 8px;
  padding: 12px;
  border-left: 3px solid #07c160;
}

.l-name { font-size: 15px; font-weight: 600; color: #323233; }
.l-phone { font-size: 14px; color: #1989fa; }
.l-addr { font-size: 13px; color: #646566; margin-top: 6px; line-height: 1.5; word-break: break-all; }
.l-gno { font-size: 11px; color: #c8c9cc; margin-top: 4px; }

:deep(.van-nav-bar) { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
:deep(.van-nav-bar__title) { color: #fff; font-weight: 600; }
:deep(.van-nav-bar .van-icon) { color: #fff; }
</style>

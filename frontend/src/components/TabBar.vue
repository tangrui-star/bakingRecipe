<template>
  <div class="tab-bar" v-if="isMobile">
    <div 
      v-for="item in tabs" 
      :key="item.path"
      class="tab-item"
      :class="{ active: isActive(item.path) }"
      @click="navigate(item.path)"
    >
      <div class="icon-wrapper">
        <el-icon :size="24" class="tab-icon">
          <component :is="item.icon" />
        </el-icon>
        <span v-if="item.path === '/notifications' && unreadCount > 0" class="badge">
          {{ unreadCount > 99 ? '99+' : unreadCount }}
        </span>
      </div>
      <span class="tab-label">{{ item.label }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed, markRaw, ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { 
  House, 
  Document, 
  Operation,
  Warning,
  User,
  Bell
} from '@element-plus/icons-vue'
import axios from 'axios'

const router = useRouter()
const route = useRoute()
const unreadCount = ref(0)

const tabs = [
  { path: '/dashboard', label: '首页', icon: markRaw(House) },
  { path: '/recipes', label: '配方', icon: markRaw(Document) },
  { path: '/blacklist', label: '黑名单', icon: markRaw(Warning) },
  { path: '/calculator', label: '计算', icon: markRaw(Operation) },
  { path: '/notifications', label: '通知', icon: markRaw(Bell) },
  { path: '/profile', label: '我的', icon: markRaw(User) }
]

const isMobile = computed(() => {
  return window.innerWidth <= 768
})

const isActive = (path) => {
  return route.path === path || route.path.startsWith(path + '/')
}

const navigate = (path) => {
  if (route.path !== path) {
    router.push(path)
  }
}

const fetchUnreadCount = async () => {
  try {
    const token = localStorage.getItem('access_token')
    if (!token) return
    const res = await axios.get('/api/notifications/unread-count', {
      headers: { Authorization: `Bearer ${token}` }
    })
    unreadCount.value = res.data.unread_count || 0
  } catch {}
}

onMounted(() => {
  fetchUnreadCount()
  // 每60秒轮询一次未读数
  setInterval(fetchUnreadCount, 60000)
})
</script>

<style scoped>
.tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 56px;
  background: var(--bg-card);
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: space-around;
  align-items: center;
  z-index: 1000;
  padding-bottom: env(safe-area-inset-bottom);
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.05);
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 6px 0;
  cursor: pointer;
  transition: all 0.3s ease;
  -webkit-tap-highlight-color: transparent;
  user-select: none;
}

.tab-item:active {
  transform: scale(0.95);
}

.tab-icon {
  color: var(--text-muted);
  transition: all 0.3s ease;
}

.tab-label {
  font-size: 11px;
  color: var(--text-muted);
  transition: all 0.3s ease;
  font-weight: 500;
}

.tab-item.active .tab-icon {
  color: var(--primary-blue);
}

.tab-item.active .tab-label {
  color: var(--primary-blue);
  font-weight: 600;
}

/* 添加激活动画 */
.tab-item.active {
  position: relative;
}

.tab-item.active::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 24px;
  height: 3px;
  background: var(--primary-blue);
  border-radius: 0 0 3px 3px;
}

.badge {
  position: absolute;
  top: -4px;
  right: -6px;
  background: #ee0a24;
  color: #fff;
  font-size: 10px;
  min-width: 16px;
  height: 16px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
  line-height: 1;
  pointer-events: none;
}

.icon-wrapper {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
</style>

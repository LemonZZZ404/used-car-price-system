<template>
  <div class="profile-page">
    <el-row :gutter="20">
      <el-col :xs="24" :md="8">
        <div class="card user-card">
          <el-avatar :size="72" class="avatar">{{ initial }}</el-avatar>
          <h3>{{ username }}</h3>
          <el-tag :type="userStore.isAdmin ? 'danger' : 'success'" effect="dark" size="small" round>
            {{ userStore.isAdmin ? '管理员' : '普通用户' }}
          </el-tag>
          <div class="user-meta">
            <div class="meta-row"><span>登录状态</span><b>已登录</b></div>
            <div class="meta-row"><span>账号角色</span><b>{{ userStore.isAdmin ? 'admin' : 'user' }}</b></div>
            <div class="meta-row"><span>累计估价</span><b>{{ totalPredictions }} 次</b></div>
          </div>
        </div>

        <div class="card pref-card">
          <div class="card-title"><el-icon><Setting /></el-icon><span>偏好设置</span></div>
          <div class="pref-row">
            <span>暗色主题</span>
            <el-switch v-model="dark" @change="toggleDark" />
          </div>
          <div class="pref-row">
            <span>自动刷新实时数据</span>
            <el-switch v-model="autoRefresh" @change="savePref" />
          </div>
        </div>

        <div class="card quick-card">
          <div class="card-title"><el-icon><Promotion /></el-icon><span>快捷入口</span></div>
          <div class="quick-grid">
            <div class="quick-item" v-for="q in quicks" :key="q.path" @click="$router.push(q.path)">
              <el-icon><component :is="q.icon" /></el-icon>
              <span>{{ q.name }}</span>
            </div>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :md="16">
        <div class="card history-card" v-loading="loading">
          <div class="card-title">
            <el-icon><Clock /></el-icon>
            <span>最近估价记录</span>
            <el-button link type="primary" size="small" @click="$router.push('/history')">
              查看全部
            </el-button>
          </div>
          <el-table :data="records" stripe size="default" class="record-table">
            <el-table-column prop="brand" label="品牌" width="90" />
            <el-table-column prop="age" label="车龄" width="70">
              <template #default="{ row }">{{ row.age }} 年</template>
            </el-table-column>
            <el-table-column prop="mileage" label="里程" width="90">
              <template #default="{ row }">{{ row.mileage }} 万km</template>
            </el-table-column>
            <el-table-column prop="predicted_price" label="预估价" width="100">
              <template #default="{ row }">
                <b class="price">{{ row.predicted_price }} 万</b>
              </template>
            </el-table-column>
            <el-table-column prop="model_type" label="模型" width="110" />
            <el-table-column prop="create_time" label="时间" min-width="150">
              <template #default="{ row }">{{ (row.create_time || '').replace('T', ' ').slice(0, 16) }}</template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Setting, Promotion, Clock, MagicStick, ScaleToOriginal, Aim, DataAnalysis } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { getPredictionHistory } from '@/api'

const userStore = useUserStore()
const username = computed(() => userStore.user?.username || '用户')
const initial = computed(() => username.value[0]?.toUpperCase() || '用')

const totalPredictions = ref(0)
const records = ref([])
const loading = ref(true)

const dark = ref(document.documentElement.getAttribute('data-theme') === 'dark')
const autoRefresh = ref(localStorage.getItem('pref_auto_refresh') !== '0')

const quicks = [
  { path: '/predict', name: '智能估价', icon: MagicStick },
  { path: '/compare', name: '多车对比', icon: ScaleToOriginal },
  { path: '/recommend', name: '智能选车', icon: Aim },
  { path: '/dashboard', name: '数据看板', icon: DataAnalysis },
]

const toggleDark = () => {
  document.documentElement.setAttribute('data-theme', dark.value ? 'dark' : 'light')
  localStorage.setItem('theme', dark.value ? 'dark' : 'light')
}

const savePref = () => {
  localStorage.setItem('pref_auto_refresh', autoRefresh.value ? '1' : '0')
}

onMounted(async () => {
  try {
    const res = await getPredictionHistory({ limit: 8 })
    records.value = res.data || []
    totalPredictions.value = res.total ?? records.value.length
  } catch (e) { /* 拦截器已提示 */ } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.profile-page { max-width: 1200px; margin: 0 auto; }

.user-card { text-align: center; padding: 30px 24px 24px; margin-bottom: 20px; }
.avatar {
  background: linear-gradient(135deg, #2D6BFF, #5B8CFF);
  font-size: 26px; color: #fff; margin-bottom: 12px;
}
.user-card h3 { margin: 0 0 10px; color: var(--text-primary); }
.user-meta { margin-top: 20px; text-align: left; }
.meta-row {
  display: flex; justify-content: space-between; padding: 10px 4px;
  border-bottom: 1px dashed var(--border-color); font-size: 13.5px;
}
.meta-row:last-child { border-bottom: none; }
.meta-row span { color: var(--text-secondary); }
.meta-row b { color: var(--text-primary); }

.card-title {
  display: flex; align-items: center; gap: 8px;
  font-size: 15px; font-weight: 600; color: var(--text-primary); margin-bottom: 16px;
}
.card-title .el-button { margin-left: auto; }

.pref-card, .quick-card { padding: 20px 22px; margin-bottom: 20px; }
.pref-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 0; font-size: 13.5px; color: var(--text-secondary);
}

.quick-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
.quick-item {
  display: flex; align-items: center; gap: 8px; padding: 12px 14px;
  border-radius: 10px; border: 1px solid var(--border-color);
  font-size: 13.5px; color: var(--text-primary); cursor: pointer;
  transition: all 0.2s;
}
.quick-item:hover {
  border-color: #2D6BFF; color: #2D6BFF;
  transform: translateY(-2px); box-shadow: 0 4px 12px rgba(45, 107, 255, 0.15);
}

.history-card { padding: 20px 22px; }
.price { color: #F56C6C; }
</style>

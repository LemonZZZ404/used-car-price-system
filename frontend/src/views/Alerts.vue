<template>
  <div class="alerts-page">
    <div class="hero card">
      <div class="hero-left">
        <div class="hero-icon"><el-icon :size="28"><Bell /></el-icon></div>
        <div>
          <h2>预警中心</h2>
          <p>Kafka + Spark Streaming 实时监测价格异常 · 流状态
            <el-tag :type="streamOk ? 'success' : 'danger'" size="small" effect="dark" round>{{ statusText }}</el-tag>
          </p>
        </div>
      </div>
      <div class="hero-right">
        <span class="auto-label">自动刷新</span>
        <el-switch v-model="autoRefresh" @change="setupTimer" />
        <el-button circle :loading="loading" @click="load"><el-icon><Refresh /></el-icon></el-button>
      </div>
    </div>

    <div class="stat-strip card">
      <div class="stat">
        <div class="stat-value warn">{{ data?.count ?? '-' }}</div>
        <div class="stat-label">当前预警数</div>
      </div>
      <div class="stat">
        <div class="stat-value high">{{ data?.level_stat?.['高'] ?? '-' }}</div>
        <div class="stat-label">高风险（偏差≥50%）</div>
      </div>
      <div class="stat">
        <div class="stat-value mid">{{ data?.level_stat?.['中'] ?? '-' }}</div>
        <div class="stat-label">中风险（30-50%）</div>
      </div>
      <div class="stat">
        <div class="stat-value ok">{{ data?.level_stat?.['低'] ?? '-' }}</div>
        <div class="stat-label">低风险（&lt;30%）</div>
      </div>
      <div class="stat">
        <div class="stat-value">{{ data?.total_search_events?.toLocaleString?.() ?? '-' }}</div>
        <div class="stat-label">累计搜索事件</div>
      </div>
      <div class="stat">
        <div class="stat-value small-text">{{ data?.last_update || '-' }}</div>
        <div class="stat-label">流处理最近更新</div>
      </div>
    </div>

    <div class="card list-card">
      <div class="filter-row">
        <el-radio-group v-model="level" size="small" @change="load">
          <el-radio-button value="">全部</el-radio-button>
          <el-radio-button value="高">高风险</el-radio-button>
          <el-radio-button value="中">中风险</el-radio-button>
          <el-radio-button value="低">低风险</el-radio-button>
        </el-radio-group>
        <span class="hint" v-if="autoRefresh">每 30 秒自动刷新</span>
      </div>

      <el-timeline class="alert-timeline" v-if="alerts.length">
        <el-timeline-item
          v-for="(a, i) in alerts" :key="i"
          :type="levelType(a.level)"
          :hollow="i > 0"
          :timestamp="a.time || a.ts || '实时捕获'"
          placement="top"
        >
          <div class="alert-item">
            <div class="alert-main">
              <el-tag :type="levelType(a.level)" size="small" effect="dark" round class="level-tag">
                {{ a.level }}风险
              </el-tag>
              <b class="car-name">{{ a.brand }} {{ a.model || a.series || '' }}</b>
              <span class="alert-msg">{{ a.alert || '价格偏离异常' }}</span>
            </div>
            <div class="alert-side" v-if="a.deviation !== undefined">
              偏差 <b :class="devClass(a.deviation)">{{ (a.deviation * 100).toFixed(0) }}%</b>
            </div>
          </div>
        </el-timeline-item>
      </el-timeline>

      <div v-else class="empty">
        <el-icon :size="44" class="dim"><Bell /></el-icon>
        <p>当前条件下暂无预警</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Bell, Refresh } from '@element-plus/icons-vue'
import { getRealtimeAlerts } from '@/api'

const loading = ref(false)
const autoRefresh = ref(true)
const level = ref('')
const data = ref(null)
let timer = null

const alerts = computed(() => data.value?.alerts || [])
const streamOk = computed(() => data.value?.status === 'running')
const statusText = computed(() => data.value?.status === 'running' ? '运行中' : (data.value?.status || '未知'))

const levelType = (lv) => ({ 高: 'danger', 中: 'warning', 低: 'info' }[lv] || 'info')
const devClass = (d) => Math.abs(d) >= 0.5 ? 'high' : (Math.abs(d) >= 0.3 ? 'mid' : 'ok')

const load = async () => {
  loading.value = true
  try {
    const res = await getRealtimeAlerts({ level: level.value || undefined, limit: 100 })
    data.value = res.data
  } catch (e) { /* 拦截器已提示 */ } finally {
    loading.value = false
  }
}

const setupTimer = () => {
  if (timer) { clearInterval(timer); timer = null }
  if (autoRefresh.value) {
    timer = setInterval(load, 30000)
  }
}

onMounted(() => { load(); setupTimer() })
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<style scoped>
.alerts-page { max-width: 1200px; margin: 0 auto; }
.hero { display: flex; align-items: center; justify-content: space-between; padding: 22px 26px; margin-bottom: 20px; }
.hero-left { display: flex; align-items: center; gap: 14px; }
.hero-icon {
  width: 52px; height: 52px; border-radius: 13px;
  background: linear-gradient(135deg, #EF4444, #F87171);
  display: flex; align-items: center; justify-content: center; color: #fff;
  box-shadow: 0 6px 16px rgba(239, 68, 68, 0.35);
}
.hero h2 { margin: 0 0 4px; font-size: 20px; color: var(--text-primary); }
.hero p { margin: 0; font-size: 13px; color: var(--text-secondary); display: flex; align-items: center; gap: 6px; }
.hero-right { display: flex; align-items: center; gap: 10px; }
.auto-label { font-size: 13px; color: var(--text-secondary); }

.stat-strip { display: flex; flex-wrap: wrap; padding: 16px 10px; margin-bottom: 20px; }
.stat { flex: 1; min-width: 130px; text-align: center; padding: 6px 8px; }
.stat-value {
  font-size: 26px; font-weight: 800; color: #2D6BFF;
}
.stat-value.warn { color: #F59E0B; }
.stat-value.high { color: #EF4444; }
.stat-value.mid { color: #F59E0B; }
.stat-value.ok { color: #22C55E; }
.stat-value.small-text { font-size: 15px; }
.stat-label { font-size: 12px; color: var(--text-secondary); margin-top: 4px; }

.list-card { padding: 20px 26px; }
.filter-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 18px; }
.hint { font-size: 12px; color: var(--text-secondary); }

.alert-timeline { padding-left: 4px; }
.alert-item {
  display: flex; align-items: center; justify-content: space-between; gap: 14px;
  padding: 12px 16px; border-radius: 10px; background: var(--bg-secondary, rgba(148,163,184,0.06));
}
.alert-main { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; min-width: 0; }
.level-tag { flex-shrink: 0; }
.car-name { font-size: 14.5px; color: var(--text-primary); }
.alert-msg { font-size: 13px; color: var(--text-secondary); }
.alert-side { font-size: 13px; color: var(--text-secondary); flex-shrink: 0; }
.alert-side b.high { color: #EF4444; font-size: 15px; }
.alert-side b.mid { color: #F59E0B; font-size: 15px; }
.alert-side b.ok { color: #22C55E; font-size: 15px; }

.empty { text-align: center; padding: 46px 0; color: var(--text-secondary); }
.empty p { margin-top: 10px; font-size: 14px; }
.dim { opacity: 0.3; }
</style>

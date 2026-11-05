<template>
  <div class="realtime-page">
    <!-- 状态栏 -->
    <div class="status-bar">
      <div class="status-left">
        <div class="status-indicator" :class="rtData.status">
          <span class="status-dot"></span>
          <span class="status-text">{{ statusText }}</span>
        </div>
        <el-tag type="info" effect="plain" size="small" round>Kafka Topic: car_search_events</el-tag>
        <el-tag type="warning" effect="light" size="small" round>滑动窗口 5min / 1min</el-tag>
      </div>
      <div class="status-right">
        <el-button :icon="Refresh" @click="loadData" :loading="loading" size="small">刷新</el-button>
        <el-switch v-model="autoRefresh" active-text="自动刷新" @change="toggleAutoRefresh" />
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #2D6BFF, #5B8CFF)">
            <el-icon><DataAnalysis /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ formatNumber(rtData.total_events) }}</div>
            <div class="stat-label">总搜索事件</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #22C55E, #4ADE80)">
            <el-icon><Lightning /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ rtData.top_brands?.length || 0 }}</div>
            <div class="stat-label">活跃品牌数</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #F59E0B, #FBBF24)">
            <el-icon><Timer /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value" style="font-size:16px">{{ rtData.last_update || '--' }}</div>
            <div class="stat-label">最后更新</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #8B5CF6, #A78BFA)">
            <el-icon><Connection /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ autoRefresh ? '实时' : '手动' }}</div>
            <div class="stat-label">数据模式</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :xs="24" :md="12">
        <div class="card">
          <div class="card-title">
            热门品牌 Top 10
            <span class="card-sub">实时搜索量排行</span>
          </div>
          <div ref="brandChartRef" class="chart-container"></div>
        </div>
      </el-col>
      <el-col :xs="24" :md="12">
        <div class="card">
          <div class="card-title">
            热门车型 Top 10
            <span class="card-sub">品牌 + 车型搜索量</span>
          </div>
          <div ref="modelChartRef" class="chart-container"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 品牌均价 + 数据流 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :xs="24" :md="12">
        <div class="card">
          <div class="card-title">
            品牌搜索占比
            <span class="card-sub">当前窗口内分布</span>
          </div>
          <div ref="pieChartRef" class="chart-container"></div>
        </div>
      </el-col>
      <el-col :xs="24" :md="12">
        <div class="card">
          <div class="card-title">
            热门品牌搜索量 + 均价
            <span class="card-sub">双轴联动</span>
          </div>
          <div ref="comboChartRef" class="chart-container"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 数据明细表 -->
    <div class="card">
      <div class="card-title">
        热门品牌明细
        <el-tag type="primary" effect="light" size="small" round>实时数据</el-tag>
      </div>
      <el-table :data="rtData.top_brands || []" stripe border size="small">
        <el-table-column type="index" label="排名" width="70" align="center">
          <template #default="{ $index }">
            <span v-if="$index < 3" class="rank-badge">{{ $index + 1 }}</span>
            <span v-else style="color:#9CA3AF">{{ $index + 1 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="brand" label="品牌" width="120">
          <template #default="{ row }">
            <span style="font-weight:600">{{ row.brand }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="search_count" label="搜索次数" width="120" sortable>
          <template #default="{ row }">
            <span style="color:#2D6BFF;font-weight:600">{{ row.search_count }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="avg_price" label="平均价格" width="120">
          <template #default="{ row }">
            {{ row.avg_price ? row.avg_price + ' 万' : '--' }}
          </template>
        </el-table-column>
        <el-table-column label="搜索占比" min-width="200">
          <template #default="{ row }">
            <el-progress
              :percentage="getPercentage(row.search_count)"
              :color="getProgressColor(row.search_count)"
              :stroke-width="14"
              :text-inside="true"
            />
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!rtData.top_brands || rtData.top_brands.length === 0"
                description="暂无实时数据，请确保流处理消费者正在运行"
                :image-size="80" />
    </div>

    <!-- 架构说明 -->
    <div class="card" style="margin-top:20px">
      <div class="card-title">
        实时数据管道架构
        <el-tag type="success" effect="light" size="small" round>Lambda 架构</el-tag>
      </div>
      <div class="arch-flow">
        <div class="arch-node">
          <el-icon><Monitor /></el-icon>
          <span>用户搜索</span>
        </div>
        <div class="arch-arrow">→</div>
        <div class="arch-node">
          <el-icon><Connection /></el-icon>
          <span>Flume 采集</span>
        </div>
        <div class="arch-arrow">→</div>
        <div class="arch-node highlight">
          <el-icon><ChatDotRound /></el-icon>
          <span>Kafka</span>
        </div>
        <div class="arch-arrow">→</div>
        <div class="arch-node highlight">
          <el-icon><Cpu /></el-icon>
          <span>Streaming Consumer</span>
        </div>
        <div class="arch-arrow">→</div>
        <div class="arch-node">
          <el-icon><Coin /></el-icon>
          <span>Redis 聚合</span>
        </div>
        <div class="arch-arrow">→</div>
        <div class="arch-node highlight">
          <el-icon><DataAnalysis /></el-icon>
          <span>Django API</span>
        </div>
        <div class="arch-arrow">→</div>
        <div class="arch-node">
          <el-icon><Monitor /></el-icon>
          <span>前端展示</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import echarts from '@/utils/echarts'
import {
  Refresh, DataAnalysis, Connection, Timer, Monitor, Cpu, Coin, ChatDotRound
} from '@element-plus/icons-vue'
import { getRealtimeHot } from '@/api'

const loading = ref(false)
const autoRefresh = ref(true)
const rtData = reactive({
  status: 'unknown',
  total_events: 0,
  last_update: '',
  top_brands: [],
  top_models: []
})

const brandChartRef = ref(null)
const modelChartRef = ref(null)
const pieChartRef = ref(null)
const comboChartRef = ref(null)

let brandChart = null
let modelChart = null
let pieChart = null
let comboChart = null
let refreshTimer = null

const CHART_COLORS = ['#2D6BFF', '#22C55E', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4', '#EC4899', '#84CC16', '#F97316', '#6366F1']

const statusText = ref('未知')

const formatNumber = (n) => {
  if (!n) return 0
  return Number(n).toLocaleString('zh-CN')
}

const getPercentage = (count) => {
  const total = rtData.top_brands?.reduce((s, b) => s + b.search_count, 0) || 1
  return Math.round((count / total) * 100)
}

const getProgressColor = (count) => {
  if (count > 50) return '#EF4444'
  if (count > 30) return '#F59E0B'
  return '#22C55E'
}

const updateStatusText = () => {
  const map = { running: '运行中', stopped: '已停止', starting: '启动中', unknown: '未知', unavailable: '不可用' }
  statusText.value = map[rtData.status] || '未知'
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await getRealtimeHot()
    if (res.code === 200 && res.data) {
      Object.assign(rtData, res.data)
      updateStatusText()
      updateCharts()
    }
  } catch (e) {
    console.error('实时数据加载失败', e)
  } finally {
    loading.value = false
  }
}

const initCharts = () => {
  if (brandChartRef.value) brandChart = echarts.init(brandChartRef.value)
  if (modelChartRef.value) modelChart = echarts.init(modelChartRef.value)
  if (pieChartRef.value) pieChart = echarts.init(pieChartRef.value)
  if (comboChartRef.value) comboChart = echarts.init(comboChartRef.value)
}

const updateCharts = () => {
  // 热门品牌柱状图
  if (brandChart) {
    const brands = rtData.top_brands || []
    brandChart.setOption({
      color: CHART_COLORS,
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '3%', right: '4%', bottom: '10%', containLabel: true },
      xAxis: {
        type: 'category',
        data: brands.map(b => b.brand),
        axisLabel: { rotate: 30, color: '#6B7280' },
        axisLine: { lineStyle: { color: '#E5E7EB' } }
      },
      yAxis: { type: 'value', name: '搜索次数', axisLabel: { color: '#6B7280' }, splitLine: { lineStyle: { color: '#F3F4F6' } } },
      series: [{
        type: 'bar',
        data: brands.map(b => b.search_count),
        barMaxWidth: 30,
        itemStyle: {
          borderRadius: [6, 6, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#2D6BFF' },
            { offset: 1, color: '#5B8CFF' }
          ])
        },
        label: { show: true, position: 'top', color: '#4B5563', fontWeight: 600 }
      }]
    })
  }

  // 热门车型柱状图
  if (modelChart) {
    const models = rtData.top_models || []
    modelChart.setOption({
      color: CHART_COLORS,
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '3%', right: '4%', bottom: '10%', containLabel: true },
      xAxis: {
        type: 'category',
        data: models.map(m => `${m.brand} ${m.model}`),
        axisLabel: { rotate: 35, color: '#6B7280', fontSize: 11 },
        axisLine: { lineStyle: { color: '#E5E7EB' } }
      },
      yAxis: { type: 'value', name: '搜索次数', axisLabel: { color: '#6B7280' }, splitLine: { lineStyle: { color: '#F3F4F6' } } },
      series: [{
        type: 'bar',
        data: models.map(m => m.search_count),
        barMaxWidth: 30,
        itemStyle: {
          borderRadius: [6, 6, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#22C55E' },
            { offset: 1, color: '#4ADE80' }
          ])
        },
        label: { show: true, position: 'top', color: '#4B5563', fontWeight: 600 }
      }]
    })
  }

  // 品牌搜索占比饼图
  if (pieChart) {
    const brands = rtData.top_brands || []
    pieChart.setOption({
      color: CHART_COLORS,
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { orient: 'vertical', left: 'left', textStyle: { color: '#4B5563' } },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['55%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 },
        label: { show: false, position: 'center' },
        emphasis: { label: { show: true, fontSize: 18, fontWeight: 'bold', color: '#1F2937' } },
        labelLine: { show: false },
        data: brands.map(b => ({ value: b.search_count, name: b.brand }))
      }]
    })
  }

  // 品牌搜索量 + 均价双轴图
  if (comboChart) {
    const brands = rtData.top_brands || []
    comboChart.setOption({
      color: CHART_COLORS,
      tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
      legend: { data: ['搜索次数', '平均价格'], top: 0, textStyle: { color: '#4B5563' } },
      grid: { left: '3%', right: '4%', bottom: '10%', containLabel: true },
      xAxis: {
        type: 'category',
        data: brands.map(b => b.brand),
        axisLabel: { rotate: 30, color: '#6B7280' },
        axisLine: { lineStyle: { color: '#E5E7EB' } }
      },
      yAxis: [
        { type: 'value', name: '搜索次数', axisLabel: { color: '#6B7280' }, splitLine: { lineStyle: { color: '#F3F4F6' } } },
        { type: 'value', name: '均价(万)', axisLabel: { color: '#6B7280' }, splitLine: { show: false } }
      ],
      series: [
        {
          name: '搜索次数', type: 'bar', barMaxWidth: 24,
          data: brands.map(b => b.search_count),
          itemStyle: { borderRadius: [4, 4, 0, 0], color: '#2D6BFF' }
        },
        {
          name: '平均价格', type: 'line', yAxisIndex: 1, smooth: true,
          data: brands.map(b => b.avg_price || 0),
          itemStyle: { color: '#F59E0B' }, lineStyle: { width: 3 },
          symbolSize: 8
        }
      ]
    })
  }
}

const toggleAutoRefresh = (val) => {
  if (val) {
    refreshTimer = setInterval(loadData, 5000)
  } else {
    if (refreshTimer) clearInterval(refreshTimer)
    refreshTimer = null
  }
}

const handleResize = () => {
  brandChart?.resize()
  modelChart?.resize()
  pieChart?.resize()
  comboChart?.resize()
}

onMounted(async () => {
  await nextTick()
  initCharts()
  await loadData()
  if (autoRefresh.value) {
    refreshTimer = setInterval(loadData, 5000)
  }
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  window.removeEventListener('resize', handleResize)
  brandChart?.dispose()
  modelChart?.dispose()
  pieChart?.dispose()
  comboChart?.dispose()
})
</script>

<style scoped>
.realtime-page { padding: 0; }

.status-bar {
  background: #fff;
  border-radius: var(--radius-md);
  padding: 12px 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.status-left { display: flex; align-items: center; gap: 12px; }
.status-right { display: flex; align-items: center; gap: 12px; }

.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
}

.status-indicator.running {
  background: rgba(34, 197, 94, 0.1);
  color: #22C55E;
}

.status-indicator.running .status-dot {
  background: #22C55E;
  box-shadow: 0 0 8px rgba(34, 197, 94, 0.6);
  animation: pulse 1.5s infinite;
}

.status-indicator.stopped, .status-indicator.unavailable {
  background: rgba(239, 68, 68, 0.1);
  color: #EF4444;
}

.status-indicator.stopped .status-dot, .status-indicator.unavailable .status-dot {
  background: #EF4444;
}

.status-indicator.unknown {
  background: rgba(156, 163, 175, 0.1);
  color: #9CA3AF;
}

.status-indicator.unknown .status-dot { background: #9CA3AF; }

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.stat-row { margin-bottom: 20px; }
.stat-row .el-col { margin-bottom: 12px; }
.chart-row { margin-bottom: 20px; }
.chart-row .el-col { margin-bottom: 12px; }

.card-sub {
  font-size: 12px;
  color: #9CA3AF;
  font-weight: 400;
  margin-left: 8px;
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: linear-gradient(135deg, #2D6BFF, #5B8CFF);
  color: #fff;
  font-weight: 700;
  font-size: 12px;
}

.arch-flow {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 20px 0;
}

.arch-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 16px;
  border-radius: 12px;
  background: #F9FAFB;
  border: 1px solid #E5E7EB;
  min-width: 90px;
  transition: all 0.25s;
}

.arch-node.highlight {
  background: linear-gradient(135deg, #E8F0FF, #F0F6FF);
  border-color: #B9D1FF;
}

.arch-node:hover {
  box-shadow: 0 4px 12px rgba(15, 30, 58, 0.1);
  transform: translateY(-2px);
}

.arch-node .el-icon {
  font-size: 20px;
  color: var(--primary);
}

.arch-node span {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
}

.arch-arrow {
  font-size: 18px;
  color: #9CA3AF;
  font-weight: 300;
}
</style>

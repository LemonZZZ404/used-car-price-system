<template>
  <div class="trend-page">
    <div class="hero card">
      <div class="hero-left">
        <div class="hero-icon"><el-icon :size="28"><TrendCharts /></el-icon></div>
        <div>
          <h2>行情月报</h2>
          <p>基于真实上牌数据按月聚合 · 近 24 个月走势</p>
        </div>
      </div>
      <el-button circle :loading="loading" @click="load"><el-icon><Refresh /></el-icon></el-button>
    </div>

    <!-- 市场洞察 -->
    <el-row :gutter="16" class="insight-row" v-if="insights.length">
      <el-col :xs="24" :sm="12" :md="6" v-for="ins in insights" :key="ins.title">
        <div class="card insight-card">
          <div class="ins-icon" :style="{ background: ins.bg }">
            <el-icon :size="18"><component :is="ins.icon" /></el-icon>
          </div>
          <div>
            <div class="ins-title">{{ ins.title }}</div>
            <div class="ins-value" :style="{ color: ins.color }" v-html="ins.value"></div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="24">
        <div class="card chart-card">
          <div class="card-head"><b>全市场月度均价与在售量</b><span class="sub">折线为均价（万），柱状为在售量</span></div>
          <div ref="mainRef" class="chart-tall"></div>
        </div>
      </el-col>
      <el-col :xs="24" :lg="14">
        <div class="card chart-card">
          <div class="card-head"><b>TOP5 品牌分月均价对比</b><span class="sub">真实上牌月均价（万元）</span></div>
          <div ref="brandRef" class="chart"></div>
        </div>
      </el-col>
      <el-col :xs="24" :lg="10">
        <div class="card chart-card">
          <div class="card-head"><b>近 6 个月环比变化</b><span class="sub">均价环比涨跌</span></div>
          <div class="mom-list">
            <div v-for="m in momRows" :key="m.month" class="mom-row">
              <span class="mom-month">{{ m.month }}</span>
              <el-progress
                :percentage="Math.min(Math.abs(m.pct) * 8, 100)"
                :status="m.pct >= 0 ? 'success' : 'exception'"
                :show-text="false" class="mom-bar"
              />
              <span class="mom-pct" :class="m.pct >= 0 ? 'up' : 'down'">
                {{ m.pct >= 0 ? '+' : '' }}{{ m.pct }}%
              </span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { TrendCharts, Refresh, Top, Bottom, Aim, Coin } from '@element-plus/icons-vue'
import echarts from '@/utils/echarts'
import { chartPalette, linearGradient, registerChart, unregisterChart, SERIES_COLORS } from '@/utils/theme'
import { getMonthlyTrend } from '@/api'

const loading = ref(false)
const data = ref(null)
const mainRef = ref(null)
const brandRef = ref(null)
const charts = {}

const momRows = computed(() => data.value?.mom || [])

const insights = computed(() => {
  const d = data.value
  if (!d || !d.months?.length) return []
  const list = []
  const n = d.months.length
  const lastP = d.avg_prices[n - 1]
  const firstP = d.avg_prices[0]
  const pct = firstP > 0 ? ((lastP - firstP) / firstP * 100).toFixed(1) : 0
  list.push({
    title: '近两年均价变化', icon: pct >= 0 ? Top : Bottom,
    bg: pct >= 0 ? 'rgba(34,197,94,0.12)' : 'rgba(239,68,68,0.12)',
    color: pct >= 0 ? '#22C55E' : '#EF4444',
    value: `${pct >= 0 ? '+' : ''}${pct}%`,
  })
  const maxCnt = Math.max(...d.counts)
  const maxMonth = d.months[d.counts.indexOf(maxCnt)]
  list.push({
    title: '在售最热门月份', icon: Aim, bg: 'rgba(45,107,255,0.12)', color: '#2D6BFF',
    value: `${maxMonth} · ${maxCnt.toLocaleString()}辆`,
  })
  const peakPrice = Math.max(...d.avg_prices)
  const peakMonth = d.months[d.avg_prices.indexOf(peakPrice)]
  list.push({
    title: '均价峰值月份', icon: Coin, bg: 'rgba(245,158,11,0.12)', color: '#F59E0B',
    value: `${peakMonth} · ${peakPrice}万`,
  })
  if (d.brands?.length) {
    list.push({
      title: '保有量第一品牌', icon: TrendCharts, bg: 'rgba(139,92,246,0.12)', color: '#8B5CF6',
      value: d.brands[0],
    })
  }
  return list
})

const tooltipStyle = () => {
  const p = chartPalette()
  return { backgroundColor: p.tooltipBg, borderColor: p.tooltipBorder, textStyle: { color: p.tooltipText } }
}

const renderMain = () => {
  const el = mainRef.value
  const d = data.value
  if (!el || !d) return
  const p = chartPalette()
  if (!charts.main) charts.main = echarts.init(el)
  charts.main.setOption({
    tooltip: { trigger: 'axis', ...tooltipStyle() },
    legend: { top: 0, textStyle: { color: p.text, fontSize: 12 }, itemWidth: 14, itemHeight: 8 },
    grid: { left: 12, right: 20, top: 40, bottom: 12, containLabel: true },
    xAxis: { type: 'category', data: d.months,
      axisLabel: { color: p.textSecondary, fontSize: 10, rotate: 40 },
      axisLine: { lineStyle: { color: p.axisLine } } },
    yAxis: [
      { type: 'value', name: '均价(万)', nameTextStyle: { color: p.textSecondary },
        scale: true, axisLabel: { color: p.textSecondary }, splitLine: { lineStyle: { color: p.splitLine } } },
      { type: 'value', name: '在售量', nameTextStyle: { color: p.textSecondary },
        axisLabel: { color: p.textSecondary, formatter: v => (v / 1000).toFixed(0) + 'k' },
        splitLine: { show: false } },
    ],
    series: [
      {
        name: '月度均价', type: 'line', smooth: true, data: d.avg_prices,
        symbol: 'circle', symbolSize: 6,
        lineStyle: { width: 3, color: '#2D6BFF' }, itemStyle: { color: '#2D6BFF' },
        areaStyle: { color: linearGradient(['rgba(45,107,255,0.22)', 'rgba(45,107,255,0.02)']) },
      },
      {
        name: '在售量', type: 'bar', yAxisIndex: 1, data: d.counts, barWidth: '45%',
        itemStyle: { borderRadius: [4, 4, 0, 0], color: 'rgba(148,163,184,0.35)' },
      },
    ],
  })
  registerChart(charts.main, renderMain)
}

const renderBrand = () => {
  const el = brandRef.value
  const d = data.value
  if (!el || !d) return
  const p = chartPalette()
  if (!charts.brand) charts.brand = echarts.init(el)
  charts.brand.setOption({
    tooltip: { trigger: 'axis', ...tooltipStyle(), valueFormatter: v => v == null ? '-' : v + ' 万' },
    legend: { top: 0, textStyle: { color: p.text, fontSize: 12 }, itemWidth: 14, itemHeight: 8 },
    grid: { left: 12, right: 20, top: 40, bottom: 12, containLabel: true },
    xAxis: { type: 'category', data: d.months, boundaryGap: false,
      axisLabel: { color: p.textSecondary, fontSize: 10, rotate: 40 },
      axisLine: { lineStyle: { color: p.axisLine } } },
    yAxis: { type: 'value', scale: true, name: '均价(万)', nameTextStyle: { color: p.textSecondary },
      axisLabel: { color: p.textSecondary }, splitLine: { lineStyle: { color: p.splitLine } } },
    series: d.brands.map((b, i) => ({
      name: b, type: 'line', smooth: true, data: d.brand_trends[b],
      symbol: 'none', lineStyle: { width: 2.5 },
      itemStyle: { color: SERIES_COLORS[i % SERIES_COLORS.length][0] },
    })),
  })
  registerChart(charts.brand, renderBrand)
}

const load = async () => {
  loading.value = true
  try {
    const res = await getMonthlyTrend()
    data.value = res.data
    await nextTick()
    renderMain(); renderBrand()
  } finally {
    loading.value = false
  }
}

const resizeAll = () => Object.values(charts).forEach(c => c && c.resize())

onMounted(() => { load(); window.addEventListener('resize', resizeAll) })
onUnmounted(() => {
  window.removeEventListener('resize', resizeAll)
  Object.values(charts).forEach(c => { unregisterChart(c); c && c.dispose() })
})
</script>

<style scoped>
.trend-page { max-width: 1400px; margin: 0 auto; }
.hero { display: flex; align-items: center; justify-content: space-between; padding: 22px 26px; margin-bottom: 20px; }
.hero-left { display: flex; align-items: center; gap: 14px; }
.hero-icon {
  width: 52px; height: 52px; border-radius: 13px;
  background: linear-gradient(135deg, #F97316, #FB923C);
  display: flex; align-items: center; justify-content: center; color: #fff;
  box-shadow: 0 6px 16px rgba(249, 115, 22, 0.35);
}
.hero h2 { margin: 0 0 4px; font-size: 20px; color: var(--text-primary); }
.hero p { margin: 0; font-size: 13px; color: var(--text-secondary); }

.insight-row { margin-bottom: 4px; }
.insight-card { display: flex; align-items: center; gap: 12px; padding: 16px 18px; margin-bottom: 16px; }
.ins-icon { width: 40px; height: 40px; border-radius: 11px; display: flex; align-items: center; justify-content: center; }
.ins-title { font-size: 12px; color: var(--text-secondary); }
.ins-value { font-size: 17px; font-weight: 700; margin-top: 2px; }

.chart-card { padding: 18px 20px; margin-bottom: 20px; }
.card-head { display: flex; align-items: baseline; gap: 10px; margin-bottom: 4px; }
.card-head b { font-size: 15px; color: var(--text-primary); }
.card-head .sub { font-size: 12px; color: var(--text-secondary); }
.chart { height: 340px; }
.chart-tall { height: 360px; }

.mom-list { display: flex; flex-direction: column; gap: 14px; padding-top: 14px; }
.mom-row { display: flex; align-items: center; gap: 12px; }
.mom-month { width: 64px; font-size: 13px; color: var(--text-primary); }
.mom-bar { flex: 1; }
.mom-pct { width: 62px; text-align: right; font-weight: 700; font-size: 14px; }
.mom-pct.up { color: #22C55E; }
.mom-pct.down { color: #EF4444; }
</style>

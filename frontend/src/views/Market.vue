<template>
  <div class="market-page">
    <div class="hero card">
      <div class="hero-left">
        <div class="hero-icon"><el-icon :size="28"><DataLine /></el-icon></div>
        <div>
          <h2>市场行情总览</h2>
          <p>百万级在售车源聚合分析 · Redis 缓存加速</p>
        </div>
      </div>
      <el-button circle :loading="loading" @click="load"><el-icon><Refresh /></el-icon></el-button>
    </div>

    <div class="stat-strip card" v-if="data">
      <div class="stat" v-for="s in statItems" :key="s.label">
        <div class="stat-value">{{ s.value }}<small>{{ s.unit }}</small></div>
        <div class="stat-label">{{ s.label }}</div>
      </div>
    </div>

    <el-row :gutter="20">
      <el-col :xs="24" :lg="14">
        <div class="card chart-card">
          <div class="card-head"><b>二手车价格分布</b><span class="sub">按价格区间统计在售量</span></div>
          <div ref="histRef" class="chart"></div>
        </div>
      </el-col>
      <el-col :xs="24" :lg="10">
        <div class="card chart-card">
          <div class="card-head"><b>动力类型结构</b><span class="sub">在售占比</span></div>
          <div ref="fuelRef" class="chart"></div>
        </div>
      </el-col>
      <el-col :xs="24" :lg="12">
        <div class="card chart-card">
          <div class="card-head"><b>车龄 × 价格 热力分布</b><span class="sub">颜色越亮车源越密集</span></div>
          <div ref="heatRef" class="chart"></div>
        </div>
      </el-col>
      <el-col :xs="24" :lg="12">
        <div class="card chart-card">
          <div class="card-head"><b>各车龄保值率曲线</b><span class="sub">avg(price/original_price)</span></div>
          <div ref="retentionRef" class="chart"></div>
        </div>
      </el-col>
      <el-col :span="24">
        <div class="card chart-card">
          <div class="card-head"><b>里程 - 价格 散点分布</b><span class="sub">最新 400 条在售车源（点大小代表车龄）</span></div>
          <div ref="scatterRef" class="chart-tall"></div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { DataLine, Refresh } from '@element-plus/icons-vue'
import echarts from '@/utils/echarts'
import { chartPalette, linearGradient, registerChart, unregisterChart, SERIES_COLORS } from '@/utils/theme'
import { getMarketOverview } from '@/api'

const loading = ref(false)
const data = ref(null)
const histRef = ref(null)
const fuelRef = ref(null)
const heatRef = ref(null)
const retentionRef = ref(null)
const scatterRef = ref(null)
const charts = {}

const statItems = computed(() => {
  const s = data.value?.summary
  if (!s) return []
  return [
    { label: '在售车源', value: s.total?.toLocaleString(), unit: '辆' },
    { label: '平均售价', value: s.avg_price, unit: '万' },
    { label: '平均车龄', value: s.avg_age, unit: '年' },
    { label: '平均里程', value: s.avg_mileage, unit: '万km' },
    { label: '覆盖品牌', value: s.brand_count, unit: '个' },
    { label: '覆盖城市', value: s.city_count, unit: '个' },
  ]
})

const tooltipStyle = () => {
  const p = chartPalette()
  return { backgroundColor: p.tooltipBg, borderColor: p.tooltipBorder, textStyle: { color: p.tooltipText } }
}

const renderHist = () => {
  const el = histRef.value
  if (!el || !data.value) return
  const p = chartPalette()
  const d = data.value.hist
  if (!charts.hist) charts.hist = echarts.init(el)
  charts.hist.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, ...tooltipStyle(),
      valueFormatter: v => v?.toLocaleString() + ' 辆' },
    grid: { left: 10, right: 20, top: 30, bottom: 10, containLabel: true },
    xAxis: { type: 'category', data: d.labels,
      axisLabel: { color: p.textSecondary, fontSize: 11, rotate: 30 },
      axisLine: { lineStyle: { color: p.axisLine } } },
    yAxis: { type: 'value', axisLabel: { color: p.textSecondary }, splitLine: { lineStyle: { color: p.splitLine } } },
    series: [{
      type: 'bar', data: d.counts, barWidth: '55%',
      itemStyle: { borderRadius: [6, 6, 0, 0], color: linearGradient(SERIES_COLORS[0]) },
    }],
  })
  registerChart(charts.hist, renderHist)
}

const renderFuel = () => {
  const el = fuelRef.value
  if (!el || !data.value) return
  const p = chartPalette()
  if (!charts.fuel) charts.fuel = echarts.init(el)
  charts.fuel.setOption({
    tooltip: { trigger: 'item', ...tooltipStyle(), formatter: '{b}: {c} 辆 ({d}%)' },
    legend: { bottom: 0, textStyle: { color: p.text, fontSize: 11 }, itemWidth: 12, itemHeight: 8 },
    series: [{
      type: 'pie', radius: ['42%', '68%'], center: ['50%', '44%'],
      itemStyle: { borderRadius: 6, borderColor: p.tooltipBg, borderWidth: 2 },
      label: { show: false },
      data: data.value.fuel.map((f, i) => ({
        name: f.name, value: f.count,
        itemStyle: { color: linearGradient(SERIES_COLORS[i % SERIES_COLORS.length], 'vertical') },
      })),
    }],
  })
  registerChart(charts.fuel, renderFuel)
}

const renderHeat = () => {
  const el = heatRef.value
  if (!el || !data.value) return
  const p = chartPalette()
  const ages = [...new Set(data.value.heatmap.map(h => h[0]))]
  const prices = [...new Set(data.value.heatmap.map(h => h[1]))]
  const maxVal = Math.max(...data.value.heatmap.map(h => h[2]), 1)
  if (!charts.heat) charts.heat = echarts.init(el)
  charts.heat.setOption({
    tooltip: { position: 'top', ...tooltipStyle(),
      formatter: ({ name, seriesName, value }) => `${value[0]} · ${value[1]}<br/><b>${value[2].toLocaleString()} 辆</b>` },
    grid: { left: 10, right: 20, top: 12, bottom: 60, containLabel: true },
    xAxis: { type: 'category', data: prices, axisLabel: { color: p.textSecondary, fontSize: 11, rotate: 25 },
      axisLine: { show: false }, axisTick: { show: false }, splitArea: { show: true } },
    yAxis: { type: 'category', data: ages, axisLabel: { color: p.text, fontSize: 11 },
      axisLine: { show: false }, axisTick: { show: false }, splitArea: { show: true } },
    visualMap: {
      min: 0, max: maxVal, calculable: false, orient: 'horizontal',
      left: 'center', bottom: 0, itemWidth: 12, itemHeight: 90,
      textStyle: { color: p.textSecondary, fontSize: 10 },
      inRange: { color: ['#E0EAFF', '#2D6BFF', '#1E3FA0'] },
    },
    series: [{
      type: 'heatmap', data: data.value.heatmap.map(h => [h[1], h[0], h[2]]),
      label: { show: true, fontSize: 9, color: p.text,
        formatter: ({ value }) => value[2] > 9999 ? (value[2] / 10000).toFixed(1) + 'w' : value[2] },
      itemStyle: { borderColor: p.splitLine, borderWidth: 2, borderRadius: 4 },
    }],
  })
  registerChart(charts.heat, renderHeat)
}

const renderRetention = () => {
  const el = retentionRef.value
  if (!el || !data.value) return
  const p = chartPalette()
  const rows = data.value.retention_by_age
  if (!charts.retention) charts.retention = echarts.init(el)
  charts.retention.setOption({
    tooltip: { trigger: 'axis', ...tooltipStyle(), valueFormatter: v => v + '%' },
    grid: { left: 10, right: 20, top: 30, bottom: 10, containLabel: true },
    xAxis: { type: 'category', data: rows.map(r => r.age + '年'),
      boundaryGap: false, axisLabel: { color: p.textSecondary, fontSize: 11 },
      axisLine: { lineStyle: { color: p.axisLine } } },
    yAxis: { type: 'value', axisLabel: { color: p.textSecondary, formatter: '{value}%' },
      splitLine: { lineStyle: { color: p.splitLine } } },
    series: [{
      type: 'line', data: rows.map(r => r.retention), smooth: true,
      symbol: 'circle', symbolSize: 7,
      lineStyle: { width: 3, color: '#22C55E' },
      itemStyle: { color: '#22C55E' },
      areaStyle: { color: linearGradient(['rgba(34,197,94,0.25)', 'rgba(34,197,94,0.02)']) },
    }],
  })
  registerChart(charts.retention, renderRetention)
}

const renderScatter = () => {
  const el = scatterRef.value
  if (!el || !data.value) return
  const p = chartPalette()
  if (!charts.scatter) charts.scatter = echarts.init(el)
  charts.scatter.setOption({
    tooltip: { ...tooltipStyle(),
      formatter: (pt) => `里程 <b>${pt.value[0]} 万km</b> · 价格 <b>${pt.value[1]} 万</b><br/>车龄 ${pt.value[2]} 年` },
    grid: { left: 10, right: 30, top: 20, bottom: 10, containLabel: true },
    xAxis: { type: 'value', name: '里程(万km)', nameTextStyle: { color: p.textSecondary },
      axisLabel: { color: p.textSecondary }, splitLine: { lineStyle: { color: p.splitLine } } },
    yAxis: { type: 'value', name: '价格(万)', nameTextStyle: { color: p.textSecondary },
      axisLabel: { color: p.textSecondary }, splitLine: { lineStyle: { color: p.splitLine } } },
    series: [{
      type: 'scatter', data: data.value.scatter,
      symbolSize: (d) => Math.max(5, 14 - d[2]),
      itemStyle: {
        color: linearGradient(SERIES_COLORS[0], 'vertical'), opacity: 0.65,
        borderColor: 'rgba(45,107,255,0.4)', borderWidth: 1,
      },
    }],
  })
  registerChart(charts.scatter, renderScatter)
}

const renderAll = () => { renderHist(); renderFuel(); renderHeat(); renderRetention(); renderScatter() }
const resizeAll = () => Object.values(charts).forEach(c => c && c.resize())

const load = async () => {
  loading.value = true
  try {
    const res = await getMarketOverview()
    data.value = res.data
    await nextTick()
    renderAll()
  } finally {
    loading.value = false
  }
}

onMounted(() => { load(); window.addEventListener('resize', resizeAll) })
onUnmounted(() => {
  window.removeEventListener('resize', resizeAll)
  Object.values(charts).forEach(c => { unregisterChart(c); c && c.dispose() })
})
</script>

<style scoped>
.market-page { max-width: 1400px; margin: 0 auto; }
.hero { display: flex; align-items: center; justify-content: space-between; padding: 22px 26px; margin-bottom: 20px; }
.hero-left { display: flex; align-items: center; gap: 14px; }
.hero-icon {
  width: 52px; height: 52px; border-radius: 13px;
  background: linear-gradient(135deg, #06B6D4, #22D3EE);
  display: flex; align-items: center; justify-content: center; color: #fff;
  box-shadow: 0 6px 16px rgba(6, 182, 212, 0.35);
}
.hero h2 { margin: 0 0 4px; font-size: 20px; color: var(--text-primary); }
.hero p { margin: 0; font-size: 13px; color: var(--text-secondary); }

.stat-strip { display: flex; flex-wrap: wrap; padding: 18px 10px; margin-bottom: 20px; }
.stat { flex: 1; min-width: 120px; text-align: center; padding: 6px 8px; }
.stat-value {
  font-size: 24px; font-weight: 800;
  background: linear-gradient(90deg, #2D6BFF, #06B6D4);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.stat-value small { font-size: 12px; margin-left: 3px; font-weight: 400; }
.stat-label { font-size: 12px; color: var(--text-secondary); margin-top: 4px; }

.chart-card { padding: 18px 20px; margin-bottom: 20px; }
.card-head { display: flex; align-items: baseline; gap: 10px; margin-bottom: 4px; }
.card-head b { font-size: 15px; color: var(--text-primary); }
.card-head .sub { font-size: 12px; color: var(--text-secondary); }
.chart { height: 320px; }
.chart-tall { height: 380px; }
</style>

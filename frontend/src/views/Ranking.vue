<template>
  <div class="ranking-page">
    <div class="hero card">
      <div class="hero-left">
        <div class="hero-icon"><el-icon :size="28"><Trophy /></el-icon></div>
        <div>
          <h2>排行榜中心</h2>
          <p>基于在售车源数据实时聚合 · 每 10 分钟刷新</p>
        </div>
      </div>
      <el-button circle :loading="loading" @click="load">
        <el-icon><Refresh /></el-icon>
      </el-button>
    </div>

    <el-row :gutter="20">
      <el-col :xs="24" :lg="12">
        <div class="card chart-card">
          <div class="card-head">
            <span class="dot" style="background:#22C55E"></span>
            <b>最保值车系 TOP10</b><span class="sub">均价保值率 %</span>
          </div>
          <div ref="retentionRef" class="chart"></div>
        </div>
      </el-col>
      <el-col :xs="24" :lg="12">
        <div class="card chart-card">
          <div class="card-head">
            <span class="dot" style="background:#F59E0B"></span>
            <b>性价比之王 TOP10</b><span class="sub">保值率最低 = 折价最狠</span>
          </div>
          <div ref="valueRef" class="chart"></div>
        </div>
      </el-col>
      <el-col :xs="24" :lg="12">
        <div class="card chart-card">
          <div class="card-head">
            <span class="dot" style="background:#2D6BFF"></span>
            <b>热门品牌 TOP10</b><span class="sub">按在售数量</span>
          </div>
          <div ref="hotRef" class="chart"></div>
        </div>
      </el-col>
      <el-col :xs="24" :lg="12">
        <div class="card chart-card">
          <div class="card-head">
            <span class="dot" style="background:#8B5CF6"></span>
            <b>城市均价 TOP10</b><span class="sub">万元 · 在售≥10辆</span>
          </div>
          <div ref="cityRef" class="chart"></div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { Trophy, Refresh } from '@element-plus/icons-vue'
import echarts from '@/utils/echarts'
import { chartPalette, linearGradient, registerChart, unregisterChart } from '@/utils/theme'
import { getRanking } from '@/api'

const loading = ref(false)
const data = ref(null)
const retentionRef = ref(null)
const valueRef = ref(null)
const hotRef = ref(null)
const cityRef = ref(null)
const charts = {}

const makeBarOption = (names, values, colorPair, fmt) => {
  const p = chartPalette()
  return {
    tooltip: {
      trigger: 'axis', axisPointer: { type: 'shadow' },
      backgroundColor: p.tooltipBg, borderColor: p.tooltipBorder,
      textStyle: { color: p.tooltipText },
      valueFormatter: (v) => fmt(v),
    },
    grid: { left: 8, right: 40, top: 8, bottom: 8, containLabel: true },
    xAxis: {
      type: 'value',
      axisLabel: { color: p.textSecondary, fontSize: 11 },
      splitLine: { lineStyle: { color: p.splitLine } },
    },
    yAxis: {
      type: 'category', data: names,
      axisLabel: { color: p.text, fontSize: 12 },
      axisLine: { lineStyle: { color: p.axisLine } },
      axisTick: { show: false },
    },
    series: [{
      type: 'bar', data: values, barWidth: 14,
      itemStyle: {
        borderRadius: [0, 7, 7, 0],
        color: linearGradient(colorPair, 'horizontal'),
      },
      label: { show: true, position: 'right', color: p.text, fontSize: 11, formatter: ({ value }) => fmt(value) },
    }],
  }
}

const renderAll = () => {
  if (!data.value) return
  const d = data.value
  const specs = {
    retention: makeBarOption(
      [...d.retention].reverse().map(r => `${r.brand} ${r.series}`),
      [...d.retention].reverse().map(r => r.retention),
      ['#16A34A', '#4ADE80'], v => v + '%'),
    value: makeBarOption(
      [...d.value].reverse().map(r => `${r.brand} ${r.series}`),
      [...d.value].reverse().map(r => r.retention),
      ['#D97706', '#FBBF24'], v => v + '%'),
    hot: makeBarOption(
      [...d.hot].reverse().map(r => r.brand),
      [...d.hot].reverse().map(r => r.count),
      ['#2D6BFF', '#5B8CFF'], v => v + ' 辆'),
    city: makeBarOption(
      [...d.city].reverse().map(r => r.city),
      [...d.city].reverse().map(r => r.avg_price),
      ['#7C3AED', '#A78BFA'], v => v + ' 万'),
  }
  for (const [key, elRef] of Object.entries({ retention: retentionRef, value: valueRef, hot: hotRef, city: cityRef })) {
    const el = elRef.value
    if (!el) continue
    if (!charts[key]) charts[key] = echarts.init(el)
    charts[key].setOption(specs[key])
    registerChart(charts[key], () => charts[key].setOption(specs[key]))
  }
}

const resizeAll = () => Object.values(charts).forEach(c => c && c.resize())

const load = async () => {
  loading.value = true
  try {
    const res = await getRanking()
    data.value = res.data
    await nextTick()
    renderAll()
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  load()
  window.addEventListener('resize', resizeAll)
})
onUnmounted(() => {
  window.removeEventListener('resize', resizeAll)
  Object.values(charts).forEach(c => { unregisterChart(c); c && c.dispose() })
})
</script>

<style scoped>
.ranking-page { max-width: 1400px; margin: 0 auto; }
.hero { display: flex; align-items: center; justify-content: space-between; padding: 22px 26px; margin-bottom: 20px; }
.hero-left { display: flex; align-items: center; gap: 14px; }
.hero-icon {
  width: 52px; height: 52px; border-radius: 13px;
  background: linear-gradient(135deg, #F59E0B, #FBBF24);
  display: flex; align-items: center; justify-content: center; color: #fff;
  box-shadow: 0 6px 16px rgba(245, 158, 11, 0.35);
}
.hero h2 { margin: 0 0 4px; font-size: 20px; color: var(--text-primary); }
.hero p { margin: 0; font-size: 13px; color: var(--text-secondary); }

.chart-card { padding: 18px 20px; margin-bottom: 20px; }
.card-head { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.card-head b { font-size: 15px; color: var(--text-primary); }
.card-head .sub { font-size: 12px; color: var(--text-secondary); margin-left: auto; }
.dot { width: 10px; height: 10px; border-radius: 3px; display: inline-block; }
.chart { height: 340px; }
</style>

<template>
  <div class="detail-page" v-loading="loading" element-loading-text="加载车系数据...">
    <div class="card head-card">
      <el-button circle :icon="ArrowLeft" @click="$router.back()" />
      <div class="head-main">
        <div class="head-title">
          <h2>{{ detail?.brand }} {{ detail?.series }}</h2>
          <el-tag v-if="detail" type="primary" effect="plain" round>{{ detail.stats.count }} 辆在售</el-tag>
        </div>
        <div class="head-stats" v-if="detail">
          <div class="hs"><span>均价</span><b>{{ detail.stats.avg_price }} 万</b></div>
          <div class="hs"><span>价格区间</span><b>{{ detail.stats.min_price }} ~ {{ detail.stats.max_price }} 万</b></div>
          <div class="hs"><span>平均车龄</span><b>{{ detail.stats.avg_age ?? '-' }} 年</b></div>
          <div class="hs"><span>平均里程</span><b>{{ detail.stats.avg_mileage ?? '-' }} 万km</b></div>
          <div class="hs"><span>新车均价</span><b>{{ detail.stats.avg_orig }} 万</b></div>
        </div>
      </div>
    </div>

    <el-row :gutter="20">
      <el-col :xs="24" :lg="12">
        <div class="card chart-card">
          <div class="card-head"><b>车龄贬值曲线</b><span class="sub">各车龄段均价（万元）</span></div>
          <div ref="ageRef" class="chart"></div>
        </div>
      </el-col>
      <el-col :xs="24" :lg="12">
        <div class="card chart-card">
          <div class="card-head"><b>上牌月份价格走势</b><span class="sub">按注册月份均价</span></div>
          <div ref="monthRef" class="chart"></div>
        </div>
      </el-col>
      <el-col :xs="24" :lg="12">
        <div class="card chart-card">
          <div class="card-head"><b>在售城市分布 TOP10</b><span class="sub">城市在售量与均价</span></div>
          <div ref="cityRef" class="chart"></div>
        </div>
      </el-col>
      <el-col :xs="24" :lg="12">
        <div class="card chart-card">
          <div class="card-head"><b>最新在售车源</b><span class="sub">最近入库 8 条</span></div>
          <el-table :data="detail?.samples || []" stripe size="small" max-height="320">
            <el-table-column prop="model" label="车型" min-width="140" show-overflow-tooltip />
            <el-table-column prop="price" label="售价" width="80">
              <template #default="{ row }"><b class="p">{{ row.price }}万</b></template>
            </el-table-column>
            <el-table-column prop="age" label="车龄" width="64">
              <template #default="{ row }">{{ row.age }}年</template>
            </el-table-column>
            <el-table-column prop="mileage" label="里程" width="84">
              <template #default="{ row }">{{ row.mileage }}万km</template>
            </el-table-column>
            <el-table-column prop="city" label="城市" width="76" />
            <el-table-column prop="gearbox" label="变速箱" width="72" />
          </el-table>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import echarts from '@/utils/echarts'
import { chartPalette, linearGradient, registerChart, unregisterChart, SERIES_COLORS } from '@/utils/theme'
import { getSeriesDetail } from '@/api'

const route = useRoute()
const detail = ref(null)
const loading = ref(true)
const ageRef = ref(null)
const monthRef = ref(null)
const cityRef = ref(null)
const charts = {}

const tooltipStyle = () => {
  const p = chartPalette()
  return { backgroundColor: p.tooltipBg, borderColor: p.tooltipBorder, textStyle: { color: p.tooltipText } }
}

const renderAge = () => {
  const el = ageRef.value
  const d = detail.value
  if (!el || !d) return
  const p = chartPalette()
  if (!charts.age) charts.age = echarts.init(el)
  charts.age.setOption({
    tooltip: { trigger: 'axis', ...tooltipStyle(), valueFormatter: v => v + ' 万' },
    grid: { left: 10, right: 20, top: 30, bottom: 10, containLabel: true },
    xAxis: { type: 'category', data: d.age_dep.map(r => r.age + '年'),
      axisLabel: { color: p.textSecondary, fontSize: 11 },
      axisLine: { lineStyle: { color: p.axisLine } } },
    yAxis: { type: 'value', axisLabel: { color: p.textSecondary }, splitLine: { lineStyle: { color: p.splitLine } } },
    series: [{
      type: 'bar', data: d.age_dep.map(r => r.avg_price), barWidth: '50%',
      itemStyle: { borderRadius: [6, 6, 0, 0], color: linearGradient(SERIES_COLORS[0]) },
    }],
  })
  registerChart(charts.age, renderAge)
}

const renderMonth = () => {
  const el = monthRef.value
  const d = detail.value
  if (!el || !d) return
  const p = chartPalette()
  if (!charts.month) charts.month = echarts.init(el)
  charts.month.setOption({
    tooltip: { trigger: 'axis', ...tooltipStyle(), valueFormatter: v => v + ' 万' },
    grid: { left: 10, right: 20, top: 30, bottom: 10, containLabel: true },
    xAxis: { type: 'category', data: d.monthly.map(r => r.month), boundaryGap: false,
      axisLabel: { color: p.textSecondary, fontSize: 10, rotate: 35 },
      axisLine: { lineStyle: { color: p.axisLine } } },
    yAxis: { type: 'value', scale: true, axisLabel: { color: p.textSecondary },
      splitLine: { lineStyle: { color: p.splitLine } } },
    series: [{
      type: 'line', data: d.monthly.map(r => r.avg_price), smooth: true,
      symbol: 'circle', symbolSize: 6,
      lineStyle: { width: 3, color: '#F59E0B' }, itemStyle: { color: '#F59E0B' },
      areaStyle: { color: linearGradient(['rgba(245,158,11,0.22)', 'rgba(245,158,11,0.02)']) },
    }],
  })
  registerChart(charts.month, renderMonth)
}

const renderCity = () => {
  const el = cityRef.value
  const d = detail.value
  if (!el || !d) return
  const p = chartPalette()
  const rows = [...d.cities].reverse()
  if (!charts.city) charts.city = echarts.init(el)
  charts.city.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, ...tooltipStyle(),
      formatter: (pts) => {
        const i = pts[0].dataIndex
        const c = rows[i]
        return `${c.city}<br/>在售 <b>${c.count}</b> 辆 · 均价 <b>${c.avg_price} 万</b>`
      } },
    grid: { left: 8, right: 46, top: 8, bottom: 8, containLabel: true },
    xAxis: { type: 'value', axisLabel: { color: p.textSecondary, fontSize: 11 },
      splitLine: { lineStyle: { color: p.splitLine } } },
    yAxis: { type: 'category', data: rows.map(r => r.city),
      axisLabel: { color: p.text, fontSize: 12 },
      axisLine: { lineStyle: { color: p.axisLine } }, axisTick: { show: false } },
    series: [{
      type: 'bar', data: rows.map(r => r.count), barWidth: 13,
      itemStyle: { borderRadius: [0, 7, 7, 0], color: linearGradient(SERIES_COLORS[6], 'horizontal') },
      label: { show: true, position: 'right', color: p.text, fontSize: 11 },
    }],
  })
  registerChart(charts.city, renderCity)
}

const load = async () => {
  const series = decodeURIComponent(route.params.series || '')
  if (!series) { loading.value = false; return }
  try {
    const res = await getSeriesDetail({ series })
    detail.value = res.data
    await nextTick()
    renderAge(); renderMonth(); renderCity()
  } finally {
    loading.value = false
  }
}

const resizeAll = () => Object.values(charts).forEach(c => c && c.resize())

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
.detail-page { max-width: 1400px; margin: 0 auto; }
.head-card { display: flex; align-items: center; gap: 16px; padding: 20px 24px; margin-bottom: 20px; }
.head-main { flex: 1; min-width: 0; }
.head-title { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.head-title h2 { margin: 0; font-size: 20px; color: var(--text-primary); }
.head-stats { display: flex; flex-wrap: wrap; gap: 8px 26px; }
.hs span { font-size: 12px; color: var(--text-secondary); margin-right: 6px; }
.hs b { font-size: 15px; color: #2D6BFF; }

.chart-card { padding: 18px 20px; margin-bottom: 20px; }
.card-head { display: flex; align-items: baseline; gap: 10px; margin-bottom: 4px; }
.card-head b { font-size: 15px; color: var(--text-primary); }
.card-head .sub { font-size: 12px; color: var(--text-secondary); }
.chart { height: 300px; }
.p { color: #F56C6C; }
</style>

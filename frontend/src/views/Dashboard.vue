<template>
  <div class="dashboard-page" v-loading="loading" element-loading-text="数据加载中...">
    <!-- Hero 区域 -->
    <div class="hero-section">
      <div class="hero-badge">
        <el-icon><DataAnalysis /></el-icon>
        <span>数据看板</span>
      </div>
      <h1 class="hero-title">
        <span class="gradient-text">二手车市场全景洞察</span>
      </h1>
      <p class="hero-sub">实时数据 · 智能分析 · 多维可视化</p>
    </div>

    <!-- Bento Grid 统计卡片 -->
    <div class="bento-stats">
      <div class="bento-card bento-large card card-grad-blue">
        <div class="bento-icon"><el-icon><Collection /></el-icon></div>
        <div class="bento-content">
          <div class="bento-label">车辆总量</div>
          <div class="bento-value">
            <CountUp :end-value="summary.total_cars || 0" :duration="1600" :delay="200" />
          </div>
          <div class="bento-trend up">
            <el-icon><TrendCharts /></el-icon> 较上月 +3.2%
          </div>
        </div>
        <div class="bento-deco">
          <svg viewBox="0 0 200 200" class="deco-bars">
            <rect x="20" y="140" width="18" height="40" rx="3" fill="rgba(255,255,255,0.15)"/>
            <rect x="50" y="110" width="18" height="70" rx="3" fill="rgba(255,255,255,0.2)"/>
            <rect x="80" y="80" width="18" height="100" rx="3" fill="rgba(255,255,255,0.25)"/>
            <rect x="110" y="50" width="18" height="130" rx="3" fill="rgba(255,255,255,0.3)"/>
            <rect x="140" y="20" width="18" height="160" rx="3" fill="rgba(255,255,255,0.35)"/>
          </svg>
        </div>
      </div>

      <div class="bento-card card card-grad-green">
        <div class="bento-icon"><el-icon><MagicStick /></el-icon></div>
        <div class="bento-content">
          <div class="bento-label">品牌数量</div>
          <div class="bento-value">
            <CountUp :end-value="summary.total_brands || 0" :duration="1400" :delay="400" />
          </div>
        </div>
        <div class="bento-deco">
          <svg viewBox="0 0 100 100" class="deco-circle"><circle cx="75" cy="25" r="45" fill="rgba(255,255,255,0.1)"/></svg>
        </div>
      </div>

      <div class="bento-card card card-grad-orange">
        <div class="bento-icon"><el-icon><Money /></el-icon></div>
        <div class="bento-content">
          <div class="bento-label">平均价格</div>
          <div class="bento-value">
            <span class="price-unit">¥</span>
            <CountUp :end-value="summary.avg_price || 0" :decimals="2" :duration="1400" :delay="600" />
            <span class="price-unit">万</span>
          </div>
        </div>
        <div class="bento-deco">
          <svg viewBox="0 0 100 100" class="deco-line">
            <path d="M10,70 Q30,50 50,60 T90,30" stroke="rgba(255,255,255,0.3)" stroke-width="2" fill="none"/>
          </svg>
        </div>
      </div>

      <div class="bento-card card card-grad-purple">
        <div class="bento-icon"><el-icon><Lightning /></el-icon></div>
        <div class="bento-content">
          <div class="bento-label">预测次数</div>
          <div class="bento-value">
            <CountUp :end-value="summary.total_predictions || 0" :duration="1400" :delay="800" />
          </div>
        </div>
        <div class="bento-deco">
          <svg viewBox="0 0 100 100" class="deco-ring">
            <circle cx="50" cy="50" r="35" fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="8"/>
            <circle cx="50" cy="50" r="35" fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="8"
              stroke-dasharray="140 220" stroke-linecap="round" transform="rotate(-90 50 50)"/>
          </svg>
        </div>
      </div>
    </div>

    <!-- 价格走势（大图） -->
    <div class="card chart-card chart-wide">
      <div class="card-title">
        <span>价格走势 · 近12个月</span>
        <div class="title-right">
          <el-tag type="primary" effect="light" size="small" round>价格指数 + 成交量</el-tag>
        </div>
      </div>
      <div ref="trendChartRef" class="chart-container chart-xl"></div>
    </div>

    <!-- 第二行：品牌柱状 + 价格分布 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :xs="24" :md="14">
        <div class="card chart-card">
          <div class="card-title">
            <span>品牌车辆数 Top 10</span>
            <el-tag type="success" effect="light" size="small" round>保有量</el-tag>
          </div>
          <div ref="brandChartRef" class="chart-container chart-lg"></div>
        </div>
      </el-col>
      <el-col :xs="24" :md="10">
        <div class="card chart-card">
          <div class="card-title">
            <span>价格区间分布</span>
            <el-tag type="warning" effect="light" size="small" round>占比分析</el-tag>
          </div>
          <div ref="priceDistChartRef" class="chart-container chart-lg"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 第三行：雷达图 + 散点图 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :xs="24" :md="12">
        <div class="card chart-card">
          <div class="card-title">
            <span>品牌多维对比</span>
            <el-tag type="danger" effect="light" size="small" round>雷达图</el-tag>
          </div>
          <div ref="radarChartRef" class="chart-container chart-lg"></div>
        </div>
      </el-col>
      <el-col :xs="24" :md="12">
        <div class="card chart-card">
          <div class="card-title">
            <span>里程 vs 价格分布</span>
            <el-tag type="info" effect="light" size="small" round>散点图</el-tag>
          </div>
          <div ref="scatterChartRef" class="chart-container chart-lg"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 第四行：旭日图 + 车龄分布 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :xs="24" :md="12">
        <div class="card chart-card">
          <div class="card-title">
            <span>品牌 · 车系 层级分布</span>
            <el-tag type="primary" effect="light" size="small" round>旭日图</el-tag>
          </div>
          <div ref="sunburstChartRef" class="chart-container chart-lg"></div>
        </div>
      </el-col>
      <el-col :xs="24" :md="12">
        <div class="card chart-card">
          <div class="card-title">
            <span>车龄分布</span>
            <el-tag type="success" effect="light" size="small" round>面积图</el-tag>
          </div>
          <div ref="ageChartRef" class="chart-container chart-lg"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 实时热门搜索 -->
    <div class="card">
      <div class="card-title">
        <span>实时热门搜索</span>
        <div class="title-right">
          <el-tag type="danger" effect="dark" size="small" round>
            <span class="live-dot"></span> 实时
          </el-tag>
        </div>
      </div>
      <div class="hot-list">
        <div v-for="(item, index) in hotBrands" :key="item.name" class="hot-item" :class="{ top3: index < 3 }">
          <div class="hot-rank" :class="'rank-' + (index + 1)">{{ index + 1 }}</div>
          <div class="hot-name">{{ item.name }}</div>
          <div class="hot-bar">
            <div class="hot-bar-fill" :style="{ width: item.percent + '%' }"></div>
          </div>
          <div class="hot-count">{{ formatNum(item.count) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { DataAnalysis, Collection, Money, MagicStick, Lightning, TrendCharts, Refresh } from '@element-plus/icons-vue'
import echarts from '@/utils/echarts'
import { getDashboardSummary as dashboardSummary, vizPriceTrend, vizBrandRadar, vizPriceScatter, vizBrandHierarchy } from '@/api'
import CountUp from '@/components/CountUp.vue'

const summary = ref({})
const hotBrands = ref([])
// 5 个聚合接口并发加载，期间用骨架 loading 遮罩，避免首屏出现空图表
const loading = ref(true)

const brandChartRef = ref(null)
const priceDistChartRef = ref(null)
const ageChartRef = ref(null)
const trendChartRef = ref(null)
const radarChartRef = ref(null)
const scatterChartRef = ref(null)
const sunburstChartRef = ref(null)

let brandChart, priceDistChart, ageChart, trendChart, radarChart, scatterChart, sunburstChart

const gradientColors = [
  ['#2D6BFF', '#5B8CFF'],
  ['#22C55E', '#4ADE80'],
  ['#F59E0B', '#FBBF24'],
  ['#EF4444', '#F87171'],
  ['#8B5CF6', '#A78BFA'],
  ['#EC4899', '#F472B6'],
  ['#06B6D4', '#22D3EE'],
  ['#F97316', '#FB923C'],
]

const formatNum = (n) => {
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  return n.toLocaleString()
}

const initTrendChart = (data) => {
  if (!trendChartRef.value) return
  trendChart = echarts.init(trendChartRef.value)
  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#E5E7EB',
      borderWidth: 1,
      textStyle: { color: '#1F2937' },
      axisPointer: { type: 'cross', crossStyle: { color: '#9CA3AF' } }
    },
    legend: {
      data: ['平均价格', '成交量'],
      top: 10,
      right: 20,
      textStyle: { color: '#6B7280', fontSize: 12 }
    },
    grid: { left: 50, right: 60, top: 50, bottom: 30 },
    xAxis: {
      type: 'category',
      data: data.months,
      boundaryGap: false,
      axisLine: { lineStyle: { color: '#E5E7EB' } },
      axisLabel: { color: '#6B7280', fontSize: 11 }
    },
    yAxis: [
      {
        type: 'value',
        name: '价格(万)',
        nameTextStyle: { color: '#6B7280', fontSize: 11 },
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#6B7280', fontSize: 11 },
        splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } }
      },
      {
        type: 'value',
        name: '成交量',
        nameTextStyle: { color: '#6B7280', fontSize: 11 },
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#6B7280', fontSize: 11, formatter: (v) => v >= 10000 ? (v/10000)+'万' : v },
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: '平均价格',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: { width: 3, color: '#2D6BFF' },
        itemStyle: { color: '#2D6BFF', borderColor: '#fff', borderWidth: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(45,107,255,0.35)' },
            { offset: 1, color: 'rgba(45,107,255,0.02)' }
          ])
        },
        data: data.avg_prices
      },
      {
        name: '成交量',
        type: 'bar',
        yAxisIndex: 1,
        barWidth: '40%',
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(34,197,94,0.6)' },
            { offset: 1, color: 'rgba(34,197,94,0.1)' }
          ]),
          borderRadius: [4, 4, 0, 0]
        },
        data: data.volumes
      }
    ]
  }
  trendChart.setOption(option)
}

const initBrandChart = () => {
  if (!brandChartRef.value) return
  brandChart = echarts.init(brandChartRef.value)
  const brands = ['大众', '丰田', '本田', '别克', '宝马', '奔驰', '奥迪', '日产', '福特', '雪佛兰']
  const data = [128500, 112300, 98700, 85600, 72400, 68900, 65200, 58300, 45600, 38900]
  const option = {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 20, right: 30, top: 20, bottom: 30, containLabel: true },
    xAxis: {
      type: 'category',
      data: brands,
      axisLine: { lineStyle: { color: '#E5E7EB' } },
      axisLabel: { color: '#6B7280', fontSize: 11, rotate: 30 }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#6B7280', fontSize: 11, formatter: (v) => v >= 10000 ? (v/10000)+'万' : v },
      splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } }
    },
    series: [{
      type: 'bar',
      data: data,
      barWidth: '55%',
      itemStyle: {
        borderRadius: [6, 6, 0, 0],
        color: (params) => {
          return new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: gradientColors[params.dataIndex % 8][0] },
            { offset: 1, color: gradientColors[params.dataIndex % 8][1] }
          ])
        }
      },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(45,107,255,0.3)' } }
    }]
  }
  brandChart.setOption(option)
}

const initPriceDistChart = () => {
  if (!priceDistChartRef.value) return
  priceDistChart = echarts.init(priceDistChartRef.value)
  const dist = summary.value.price_distribution || []
  const option = {
    tooltip: { trigger: 'item', formatter: '{b}: {c}辆 ({d}%)' },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      textStyle: { color: '#6B7280', fontSize: 12 }
    },
    series: [{
      type: 'pie',
      radius: ['45%', '70%'],
      center: ['35%', '50%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      emphasis: {
        label: { show: true, fontSize: 14, fontWeight: 'bold' },
        itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.15)' }
      },
      data: dist.map((d, i) => ({
        name: d.price_range,
        value: d.car_count,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 1, [
            { offset: 0, color: gradientColors[i % 8][0] },
            { offset: 1, color: gradientColors[i % 8][1] }
          ])
        }
      }))
    }]
  }
  priceDistChart.setOption(option)
}

const initAgeChart = () => {
  if (!ageChartRef.value) return
  ageChart = echarts.init(ageChartRef.value)
  const ages = ['0-1年', '1-3年', '3-5年', '5-7年', '7-10年', '10年以上']
  const data = [85000, 186000, 245000, 212000, 158000, 98000]
  const option = {
    tooltip: { trigger: 'axis' },
    grid: { left: 10, right: 20, top: 20, bottom: 30, containLabel: true },
    xAxis: {
      type: 'category',
      data: ages,
      boundaryGap: false,
      axisLine: { lineStyle: { color: '#E5E7EB' } },
      axisLabel: { color: '#6B7280', fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#6B7280', fontSize: 11, formatter: (v) => v >= 10000 ? (v/10000)+'万' : v },
      splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } }
    },
    series: [{
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: { width: 2.5, color: '#8B5CF6' },
      itemStyle: { color: '#8B5CF6' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(139,92,246,0.35)' },
          { offset: 1, color: 'rgba(139,92,246,0.02)' }
        ])
      },
      data: data
    }]
  }
  ageChart.setOption(option)
}

const initRadarChart = (data) => {
  if (!radarChartRef.value) return
  radarChart = echarts.init(radarChartRef.value)
  const colors = ['#2D6BFF', '#22C55E', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4']
  const option = {
    tooltip: {},
    legend: {
      data: data.brands.map(b => b.name),
      bottom: 5,
      textStyle: { color: '#6B7280', fontSize: 11 }
    },
    radar: {
      indicator: data.indicators,
      shape: 'polygon',
      splitNumber: 4,
      axisName: { color: '#4B5563', fontSize: 11 },
      splitLine: { lineStyle: { color: '#E5E7EB' } },
      splitArea: { areaStyle: { color: ['rgba(255,255,255,0)', 'rgba(243,244,246,0.3)'] } },
      axisLine: { lineStyle: { color: '#D1D5DB' } }
    },
    series: [{
      type: 'radar',
      data: data.brands.map((b, i) => ({
        name: b.name,
        value: b.value,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { width: 2, color: colors[i] },
        itemStyle: { color: colors[i] },
        areaStyle: { color: colors[i] + '20' }
      }))
    }]
  }
  radarChart.setOption(option)
}

const initScatterChart = (data) => {
  if (!scatterChartRef.value) return
  scatterChart = echarts.init(scatterChartRef.value)
  const colors = ['#2D6BFF', '#22C55E', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4', '#F97316']
  const series = data.brands.map((brand, i) => ({
    name: brand,
    type: 'scatter',
    data: data.scatter_data[brand],
    symbolSize: 8,
    itemStyle: {
      color: colors[i],
      opacity: 0.7,
      borderColor: '#fff',
      borderWidth: 1
    },
    emphasis: { itemStyle: { opacity: 1, shadowBlur: 10, shadowColor: colors[i] + '80' } }
  }))

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (p) => `${p.seriesName}<br/>里程: ${p.value[0]} 万公里<br/>价格: ${p.value[1]} 万<br/>车龄: ${p.value[2]} 年`
    },
    legend: {
      data: data.brands,
      bottom: 5,
      textStyle: { color: '#6B7280', fontSize: 11 },
      type: 'scroll'
    },
    grid: { left: 50, right: 20, top: 20, bottom: 40 },
    xAxis: {
      name: '里程(万公里)',
      nameTextStyle: { color: '#6B7280', fontSize: 11 },
      type: 'value',
      axisLine: { lineStyle: { color: '#E5E7EB' } },
      axisLabel: { color: '#6B7280', fontSize: 11 },
      splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } }
    },
    yAxis: {
      name: '价格(万)',
      nameTextStyle: { color: '#6B7280', fontSize: 11 },
      type: 'value',
      axisLine: { lineStyle: { color: '#E5E7EB' } },
      axisLabel: { color: '#6B7280', fontSize: 11 },
      splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } }
    },
    series: series
  }
  scatterChart.setOption(option)
}

const initSunburstChart = (data) => {
  if (!sunburstChartRef.value) return
  sunburstChart = echarts.init(sunburstChartRef.value)
  const colors = ['#2D6BFF', '#22C55E', '#F59E0B', '#EF4444', '#8B5CF6',
                  '#EC4899', '#06B6D4', '#F97316', '#6366F1', '#14B8A6', '#EAB308', '#84CC16']

  const treeData = data.tree.map((brand, i) => ({
    name: brand.name,
    value: brand.value,
    itemStyle: { color: colors[i % colors.length] },
    children: brand.children.map(s => ({
      name: s.name,
      value: s.value,
      itemStyle: { color: colors[i % colors.length] + 'AA' }
    }))
  }))

  const option = {
    tooltip: {
      formatter: function(p) {
        const path = (p.treePathInfo || []).map(function(t) { return t.name }).join(' / ')
        return path + '<br/>数量: ' + (p.value || 0).toLocaleString() + ' 辆'
      }
    },
    series: [{
      type: 'sunburst',
      data: treeData,
      radius: ['15%', '90%'],
      center: ['50%', '50%'],
      sort: null,
      emphasis: { focus: 'ancestor' },
      levels: [
        {},
        {
          r0: '15%', r: '40%',
          label: { rotate: 'tangential', fontSize: 11, fontWeight: 'bold', color: '#fff' },
          itemStyle: { borderWidth: 2, borderColor: '#fff', borderRadius: 4 }
        },
        {
          r0: '40%', r: '90%',
          label: { rotate: 'radial', fontSize: 10, color: '#fff' },
          itemStyle: { borderWidth: 1, borderColor: '#fff', borderRadius: 2 }
        }
      ]
    }]
  }
  sunburstChart.setOption(option)
}

const loadAllData = async () => {
  try {
    const [summaryRes, trendRes, radarRes, scatterRes, hierarchyRes] = await Promise.all([
      dashboardSummary(),
      vizPriceTrend(),
      vizBrandRadar(),
      vizPriceScatter(),
      vizBrandHierarchy()
    ])

    if (summaryRes.code === 200) {
      summary.value = summaryRes.data
      hotBrands.value = [
        { name: '大众', count: 128500, percent: 100 },
        { name: '丰田', count: 112300, percent: 87 },
        { name: '本田', count: 98700, percent: 77 },
        { name: '别克', count: 85600, percent: 67 },
        { name: '宝马', count: 72400, percent: 56 },
        { name: '奔驰', count: 68900, percent: 54 },
        { name: '奥迪', count: 65200, percent: 51 },
        { name: '日产', count: 58300, percent: 45 },
      ]
      await nextTick()
      try { initBrandChart() } catch(e) { console.error('initBrandChart error:', e) }
      try { initPriceDistChart() } catch(e) { console.error('initPriceDistChart error:', e) }
      try { initAgeChart() } catch(e) { console.error('initAgeChart error:', e) }
    }

    if (trendRes.code === 200) {
      try { initTrendChart(trendRes.data) } catch(e) { console.error('initTrendChart error:', e) }
    }

    if (radarRes.code === 200) {
      try { initRadarChart(radarRes.data) } catch(e) { console.error('initRadarChart error:', e) }
    }

    if (scatterRes.code === 200) {
      try { initScatterChart(scatterRes.data) } catch(e) { console.error('initScatterChart error:', e) }
    }

    if (hierarchyRes.code === 200) {
      try { initSunburstChart(hierarchyRes.data) } catch(e) { console.error('initSunburstChart error:', e) }
    }
  } catch (e) {
    console.error('Dashboard data load error:', e)
  } finally {
    loading.value = false
  }
}

const handleResize = () => {
  [brandChart, priceDistChart, ageChart, trendChart, radarChart, scatterChart, sunburstChart].forEach(c => {
    c && c.resize()
  })
}

onMounted(() => {
  loadAllData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  [brandChart, priceDistChart, ageChart, trendChart, radarChart, scatterChart, sunburstChart].forEach(c => {
    c && c.dispose()
  })
})
</script>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* Hero */
.hero-section {
  text-align: center;
  padding: 20px 0 10px;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: linear-gradient(135deg, rgba(45,107,255,0.1), rgba(139,92,246,0.1));
  color: #2D6BFF;
  padding: 5px 14px;
  border-radius: 20px;
  font-size: 12.5px;
  font-weight: 600;
  margin-bottom: 12px;
}

.hero-title {
  font-size: 28px;
  font-weight: 800;
  margin: 0 0 8px;
}

.gradient-text {
  background: linear-gradient(135deg, #2D6BFF 0%, #8B5CF6 50%, #EC4899 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-sub {
  color: #6B7280;
  font-size: 13.5px;
  margin: 0;
}

/* Bento Grid */
.bento-stats {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 16px;
}

.bento-card {
  position: relative;
  overflow: hidden;
  color: #fff;
  padding: 20px;
  min-height: 120px;
  display: flex;
  align-items: flex-start;
  gap: 14px;
  border: none;
}

.bento-card::before { display: none; }

/* 四张统计卡片的渐变底色（原先只有类名没有样式，
   导致卡片仍是白底而文字为 #fff，出现“白字白底看不清”） */
.card-grad-blue {
  background: linear-gradient(135deg, #1E40AF 0%, #2D6BFF 55%, #3B82F6 100%);
}

.card-grad-green {
  background: linear-gradient(135deg, #047857 0%, #10B981 55%, #34D399 100%);
}

.card-grad-orange {
  background: linear-gradient(135deg, #B45309 0%, #F59E0B 55%, #FBBF24 100%);
}

.card-grad-purple {
  background: linear-gradient(135deg, #6D28D9 0%, #8B5CF6 55%, #A78BFA 100%);
}

.bento-large {
  min-height: 120px;
}

.bento-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(255,255,255,0.2);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
  z-index: 2;
}

.bento-content {
  flex: 1;
  z-index: 2;
  position: relative;
}

.bento-label {
  font-size: 13px;
  opacity: 0.85;
  margin-bottom: 4px;
}

.bento-value {
  font-size: 28px;
  font-weight: 800;
  line-height: 1.2;
  letter-spacing: -0.5px;
}

.bento-large .bento-value {
  font-size: 36px;
}

.price-unit {
  font-size: 16px;
  font-weight: 500;
  opacity: 0.8;
  margin: 0 2px;
}

.bento-trend {
  font-size: 11.5px;
  margin-top: 8px;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(255,255,255,0.15);
}

.bento-trend.up { color: #86EFAC; }

.bento-deco {
  position: absolute;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 1;
}

.deco-bars { width: 200px; height: 140px; }
.deco-circle { width: 100px; height: 100px; }
.deco-line { width: 100px; height: 100px; }
.deco-ring { width: 100px; height: 100px; }

/* Charts */
.chart-row {
  margin: 0 !important;
}

.chart-card {
  height: 100%;
}

.chart-wide {
  width: 100%;
}

.chart-container {
  width: 100%;
}

.chart-xl { height: 320px; }
.chart-lg { height: 280px; }

.card-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  padding-left: 10px;
  border-left: 3px solid;
  border-image: linear-gradient(180deg, #2D6BFF, #8B5CF6) 1;
}

.title-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Hot list */
.hot-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.hot-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.hot-item:hover {
  background: var(--bg-hover);
  transform: translateX(4px);
}

.hot-rank {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: #F3F4F6;
  color: #6B7280;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.hot-rank.rank-1 { background: linear-gradient(135deg, #EF4444, #F97316); color: #fff; }
.hot-rank.rank-2 { background: linear-gradient(135deg, #F59E0B, #FBBF24); color: #fff; }
.hot-rank.rank-3 { background: linear-gradient(135deg, #2D6BFF, #60A5FA); color: #fff; }

.hot-name {
  width: 70px;
  font-size: 13.5px;
  font-weight: 600;
  color: var(--text-primary);
  flex-shrink: 0;
}

.hot-bar {
  flex: 1;
  height: 8px;
  background: #F3F4F6;
  border-radius: 4px;
  overflow: hidden;
}

.hot-bar-fill {
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, #2D6BFF, #8B5CF6);
  transition: width 1s ease;
}

.hot-count {
  width: 70px;
  text-align: right;
  font-size: 12.5px;
  color: #6B7280;
  font-weight: 500;
  flex-shrink: 0;
}

.live-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #fff;
  margin-right: 4px;
  animation: live-pulse 1.5s infinite;
}

@keyframes live-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.3); }
}

@media (max-width: 1024px) {
  .bento-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  .bento-large {
    grid-column: span 2;
  }
}

@media (max-width: 640px) {
  .bento-stats {
    grid-template-columns: 1fr;
  }
  .bento-large {
    grid-column: span 1;
  }
  .hero-title { font-size: 22px; }
}
</style>

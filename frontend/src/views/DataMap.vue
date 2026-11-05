<template>
  <div class="datamap-page">
    <!-- Hero -->
    <div class="hero-card card card-grad-green">
      <div class="hero-left">
        <div class="hero-badge">
          <el-icon><Location /></el-icon>
          <span>数据地图</span>
        </div>
        <h2 class="hero-title">
          <span class="gradient-text-white">全国二手车分布热力图</span>
        </h2>
        <p class="hero-desc">34 个省级行政区 · 实时车源分布 · 价格地域差异分析</p>
      </div>
      <div class="hero-right">
        <div class="stat-pill">
          <div class="pill-value">{{ formatNum(mapData.max_value || 0) }}</div>
          <div class="pill-label">峰值车源</div>
        </div>
      </div>
      <div class="hero-deco">
        <svg viewBox="0 0 200 200" class="deco-globe">
          <circle cx="170" cy="50" r="70" fill="rgba(255,255,255,0.08)"/>
          <circle cx="150" cy="70" r="45" fill="rgba(255,255,255,0.1)"/>
        </svg>
      </div>
    </div>

    <!-- 切换器 -->
    <div class="view-toggle card">
      <div class="toggle-group">
        <div class="toggle-btn" :class="{ active: viewMode === 'count' }" @click="viewMode = 'count'">
          <el-icon><Histogram /></el-icon>
          <span>车源数量</span>
        </div>
        <div class="toggle-btn" :class="{ active: viewMode === 'price' }" @click="viewMode = 'price'">
          <el-icon><Money /></el-icon>
          <span>平均价格</span>
        </div>
      </div>
      <div class="toggle-legend">
        <span class="legend-min">{{ viewMode === 'count' ? '少' : '低' }}</span>
        <div class="legend-bar" :class="viewMode"></div>
        <span class="legend-max">{{ viewMode === 'count' ? '多' : '高' }}</span>
      </div>
    </div>

    <!-- 地图主区域 -->
    <div class="map-card card">
      <div v-if="mapReady" ref="mapChartRef" class="map-container"></div>
      <div v-else-if="mapFailed" class="map-fallback">
        <div class="fallback-icon"><el-icon :size="40"><Warning /></el-icon></div>
        <div class="fallback-title">地图资源加载失败</div>
        <div class="fallback-desc">已切换为列表模式展示省份数据</div>
        <div ref="fallbackChartRef" class="fallback-chart"></div>
      </div>
      <div v-else class="map-loading">
        <el-icon class="loading-icon" :size="32"><Loading /></el-icon>
        <p>地图加载中...</p>
      </div>
    </div>

    <!-- 排行榜 -->
    <el-row :gutter="20">
      <el-col :xs="24" :md="12">
        <div class="card">
          <div class="card-title">
            <span>车源数量 TOP 10</span>
            <el-tag type="primary" effect="light" size="small" round>省份排名</el-tag>
          </div>
          <div class="rank-list">
            <div v-for="(item, index) in topCount" :key="item.name" class="rank-item">
              <div class="rank-num" :class="'rank-' + (index + 1)">{{ index + 1 }}</div>
              <div class="rank-name">{{ shortName(item.name) }}</div>
              <div class="rank-bar">
                <div class="rank-fill count" :style="{ width: countPct(item) + '%' }"></div>
              </div>
              <div class="rank-value">{{ formatNum(item.value) }}</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :md="12">
        <div class="card">
          <div class="card-title">
            <span>均价 TOP 10</span>
            <el-tag type="warning" effect="light" size="small" round>价格排名</el-tag>
          </div>
          <div class="rank-list">
            <div v-for="(item, index) in topPrice" :key="item.name" class="rank-item">
              <div class="rank-num" :class="'rank-' + (index + 1)">{{ index + 1 }}</div>
              <div class="rank-name">{{ shortName(item.name) }}</div>
              <div class="rank-bar">
                <div class="rank-fill price" :style="{ width: pricePct(item) + '%' }"></div>
              </div>
              <div class="rank-value">{{ '¥' + item.avg_price + '万' }}</div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 区域分析 -->
    <div class="card">
      <div class="card-title">
        <span>七大区域对比</span>
        <el-tag type="success" effect="light" size="small" round>区域分析</el-tag>
      </div>
      <div ref="regionChartRef" class="region-chart"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { Location, Histogram, Money, Loading, Warning } from '@element-plus/icons-vue'
import echarts from '@/utils/echarts'
import { vizProvinceHeatmap } from '@/api'

const viewMode = ref('count')
const loading = ref(true)
const mapReady = ref(false)
const mapFailed = ref(false)
const mapData = ref({ provinces: [], max_value: 0 })

const mapChartRef = ref(null)
const regionChartRef = ref(null)
let mapChart = null
let regionChart = null
let mapRegistered = false

const shortName = (name) => {
  if (!name) return name
  return name
    .replace(/省$/, '')
    .replace(/市$/, '')
    .replace(/壮族自治区$/, '')
    .replace(/回族自治区$/, '')
    .replace(/维吾尔自治区$/, '')
    .replace(/自治区$/, '')
    .replace(/特别行政区$/, '')
}

const formatNum = (n) => {
  if (!n) return 0
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  return n.toLocaleString()
}

const topCount = computed(() => {
  return [...mapData.value.provinces].sort((a, b) => b.value - a.value).slice(0, 10)
})

const topPrice = computed(() => {
  return [...mapData.value.provinces].sort((a, b) => b.avg_price - a.avg_price).slice(0, 10)
})

const countPct = (item) => {
  const max = topCount.value[0]?.value || 1
  return (item.value / max * 100).toFixed(1)
}

const pricePct = (item) => {
  const max = topPrice.value[0]?.avg_price || 1
  return (item.avg_price / max * 100).toFixed(1)
}

import chinaGeoJson from '@/assets/map/china.json'

const registerChinaMap = () => {
  if (mapRegistered) return true
  try {
    echarts.registerMap('china', chinaGeoJson)
    mapRegistered = true
    return true
  } catch (e) {
    console.error('Failed to register china map:', e)
    return false
  }
}

const initMapChart = () => {
  if (!mapChartRef.value || !mapRegistered) return
  if (mapChart) mapChart.dispose()
  mapChart = echarts.init(mapChartRef.value)

  const data = mapData.value.provinces
  const isCount = viewMode.value === 'count'

  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#E5E7EB',
      borderWidth: 1,
      textStyle: { color: '#1F2937', fontSize: 13 },
      formatter: (p) => {
        const d = p.data || {}
        return '<div style="font-weight:700;margin-bottom:4px">' + p.name + '</div>' +
                '<div>车源数量: <b>' + formatNum(d.value || 0) + '</b> 辆</div>' +
                '<div>平均价格: <b>¥' + (d.avg_price || 0) + '</b> 万</div>'
      }
    },
    visualMap: {
      min: 0,
      max: isCount ? mapData.value.max_value : 15,
      left: 20,
      bottom: 20,
      text: ['高', '低'],
      textStyle: { color: '#6B7280', fontSize: 11 },
      calculable: true,
      inRange: {
        color: isCount
          ? ['#EFF6FF', '#BFDBFE', '#60A5FA', '#2D6BFF', '#1E40AF']
          : ['#FEF3C7', '#FCD34D', '#F59E0B', '#EA580C', '#C2410C']
      }
    },
    series: [{
      name: isCount ? '车源数量' : '平均价格',
      type: 'map',
      map: 'china',
      roam: true,
      zoom: 1.2,
      scaleLimit: { min: 0.8, max: 3 },
      label: {
        show: false,
        fontSize: 10,
        color: '#374151'
      },
      emphasis: {
        label: { show: true, fontSize: 12, fontWeight: 'bold', color: '#fff' },
        itemStyle: {
          areaColor: '#2D6BFF',
          shadowBlur: 20,
          shadowColor: 'rgba(45,107,255,0.4)'
        }
      },
      itemStyle: {
        borderColor: '#fff',
        borderWidth: 1,
        areaColor: '#F3F4F6'
      },
      data: data.map(d => ({
        name: d.name,
        value: isCount ? d.value : d.avg_price,
        avg_price: d.avg_price
      }))
    }]
  }
  mapChart.setOption(option)
  loading.value = false
}

const initFallbackChart = () => {
  if (!mapChartRef.value && !document.querySelector('.fallback-chart')) return
  const el = document.querySelector('.fallback-chart')
  if (!el) return
  const fallbackChart = echarts.init(el)
  const data = [...mapData.value.provinces].sort((a, b) => b.value - a.value).slice(0, 20)
  fallbackChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: function(p) {
        const d = data[p[0].dataIndex]
        return p[0].name + '<br/>车源: <b>' + formatNum(d.value) + '</b> 辆<br/>均价: ¥' + d.avg_price + '万'
      }
    },
    grid: { left: 10, right: 40, top: 10, bottom: 20, containLabel: true },
    xAxis: {
      type: 'value',
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#6B7280', fontSize: 11, formatter: function(v) { return v >= 10000 ? (v/10000).toFixed(0)+'万' : v } },
      splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } }
    },
    yAxis: {
      type: 'category',
      data: data.map(function(d) { return d.name.replace(/省$/, '').replace(/市$/, '').replace(/自治区$/, '') }),
      axisLine: { lineStyle: { color: '#E5E7EB' } },
      axisLabel: { color: '#4B5563', fontSize: 11 }
    },
    series: [{
      type: 'bar',
      data: data.map(function(d) { return d.value }),
      barWidth: '60%',
      itemStyle: {
        borderRadius: [0, 4, 4, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#93C5FD' },
          { offset: 1, color: '#2D6BFF' }
        ])
      }
    }]
  })
}

const initRegionChart = () => {
  if (!regionChartRef.value) return
  if (regionChart) regionChart.dispose()
  regionChart = echarts.init(regionChartRef.value)

  const regions = {
    '华东': ['上海市', '江苏省', '浙江省', '安徽省', '福建省', '江西省', '山东省'],
    '华北': ['北京市', '天津市', '河北省', '山西省', '内蒙古自治区'],
    '华南': ['广东省', '广西壮族自治区', '海南省'],
    '华中': ['河南省', '湖北省', '湖南省'],
    '西南': ['重庆市', '四川省', '贵州省', '云南省', '西藏自治区'],
    '西北': ['陕西省', '甘肃省', '青海省', '宁夏回族自治区', '新疆维吾尔自治区'],
    '东北': ['辽宁省', '吉林省', '黑龙江省']
  }

  const provinceMap = {}
  mapData.value.provinces.forEach(p => { provinceMap[p.name] = p })

  const regionData = Object.entries(regions).map(([name, provs]) => {
    let totalCount = 0
    let totalPrice = 0
    let cnt = 0
    provs.forEach(p => {
      if (provinceMap[p]) {
        totalCount += provinceMap[p].value
        totalPrice += provinceMap[p].avg_price
        cnt++
      }
    })
    return {
      name: name,
      count: totalCount,
      avg_price: cnt > 0 ? Math.round(totalPrice / cnt * 100) / 100 : 0
    }
  })

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: {
      data: ['车源数量', '平均价格'],
      top: 5,
      right: 20,
      textStyle: { color: '#6B7280', fontSize: 12 }
    },
    grid: { left: 50, right: 60, top: 40, bottom: 30 },
    xAxis: {
      type: 'category',
      data: regionData.map(r => r.name),
      axisLine: { lineStyle: { color: '#E5E7EB' } },
      axisLabel: { color: '#6B7280', fontSize: 12 }
    },
    yAxis: [
      {
        type: 'value',
        name: '车源数',
        nameTextStyle: { color: '#6B7280', fontSize: 11 },
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#6B7280', fontSize: 11, formatter: v => v >= 10000 ? (v/10000)+'万' : v },
        splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } }
      },
      {
        type: 'value',
        name: '均价(万)',
        nameTextStyle: { color: '#6B7280', fontSize: 11 },
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#6B7280', fontSize: 11 },
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: '车源数量',
        type: 'bar',
        data: regionData.map(r => r.count),
        barWidth: '35%',
        itemStyle: {
          borderRadius: [6, 6, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#2D6BFF' },
            { offset: 1, color: '#93C5FD' }
          ])
        }
      },
      {
        name: '平均价格',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: { width: 2.5, color: '#F59E0B' },
        itemStyle: { color: '#F59E0B', borderColor: '#fff', borderWidth: 2 },
        data: regionData.map(r => r.avg_price)
      }
    ]
  }
  regionChart.setOption(option)
}

const loadData = async () => {
  loading.value = true
  try {
    const mapOk = registerChinaMap()
    const res = await vizProvinceHeatmap()
    if (res.code === 200) {
      mapData.value = res.data
      await nextTick()
      if (mapOk) {
        mapReady.value = true
        await nextTick()
        initMapChart()
      } else {
        mapFailed.value = true
        loading.value = false
        await nextTick()
        initFallbackChart()
      }
      initRegionChart()
    }
  } catch (e) {
    console.error('Load map data error:', e)
    loading.value = false
  }
}

watch(viewMode, () => {
  if (mapRegistered && mapData.value.provinces.length > 0) {
    initMapChart()
  }
})

const handleResize = () => {
  mapChart && mapChart.resize()
  regionChart && regionChart.resize()
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  mapChart && mapChart.dispose()
  regionChart && regionChart.dispose()
})
</script>

<style scoped>
.datamap-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.hero-card {
  position: relative;
  overflow: hidden;
  color: #fff;
  background: linear-gradient(135deg, #059669 0%, #10B981 50%, #34D399 100%);
  border: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 28px 32px;
}

.hero-card::before { display: none; }

.hero-left { position: relative; z-index: 2; flex: 1; }

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(255,255,255,0.2);
  backdrop-filter: blur(10px);
  padding: 5px 14px;
  border-radius: 20px;
  font-size: 12.5px;
  font-weight: 500;
  margin-bottom: 14px;
}

.hero-title { font-size: 26px; font-weight: 800; margin: 0 0 8px; }

.gradient-text-white {
  background: linear-gradient(90deg, #fff, #D1FAE5);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-desc { font-size: 13.5px; color: rgba(255,255,255,0.75); margin: 0; }

.hero-right { position: relative; z-index: 2; }

.stat-pill {
  background: rgba(255,255,255,0.15);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 14px 24px;
  text-align: center;
}

.pill-value { font-size: 24px; font-weight: 800; line-height: 1; }
.pill-label { font-size: 11px; opacity: 0.8; margin-top: 4px; }

.hero-deco { position: absolute; top: 0; right: 0; pointer-events: none; }
.deco-globe { width: 280px; height: 280px; }

.view-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
}

.toggle-group {
  display: flex;
  background: var(--bg-secondary);
  border-radius: 10px;
  padding: 4px;
}

.toggle-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #6B7280;
  cursor: pointer;
  transition: all 0.2s ease;
}

.toggle-btn:hover { color: var(--text-primary); }

.toggle-btn.active {
  background: #fff;
  color: #2D6BFF;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  font-weight: 600;
}

.toggle-legend {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: #6B7280;
}

.legend-bar {
  width: 120px;
  height: 10px;
  border-radius: 5px;
}

.legend-bar.count {
  background: linear-gradient(90deg, #EFF6FF, #BFDBFE, #60A5FA, #2D6BFF, #1E40AF);
}

.legend-bar.price {
  background: linear-gradient(90deg, #FEF3C7, #FCD34D, #F59E0B, #EA580C, #C2410C);
}

.map-card {
  position: relative;
  min-height: 500px;
  padding: 10px;
}

.map-container {
  width: 100%;
  height: 500px;
}

.map-fallback {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

.fallback-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: #FEF3C7;
  color: #F59E0B;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 14px;
}

.fallback-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 6px;
}

.fallback-desc {
  font-size: 13px;
  color: #6B7280;
  margin-bottom: 20px;
}

.fallback-chart {
  width: 100%;
  height: 420px;
}

.map-loading {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #6B7280;
  background: var(--card-bg);
  border-radius: inherit;
}

.loading-icon {
  color: #2D6BFF;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.rank-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.rank-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 10px;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.rank-item:hover {
  background: var(--bg-hover);
  transform: translateX(3px);
}

.rank-num {
  width: 26px;
  height: 26px;
  border-radius: 7px;
  background: #F3F4F6;
  color: #6B7280;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.rank-num.rank-1 { background: linear-gradient(135deg, #EF4444, #F97316); color: #fff; }
.rank-num.rank-2 { background: linear-gradient(135deg, #F59E0B, #FBBF24); color: #fff; }
.rank-num.rank-3 { background: linear-gradient(135deg, #2D6BFF, #60A5FA); color: #fff; }

.rank-name {
  width: 60px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  flex-shrink: 0;
}

.rank-bar {
  flex: 1;
  height: 8px;
  background: #F3F4F6;
  border-radius: 4px;
  overflow: hidden;
}

.rank-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 1s ease;
}

.rank-fill.count { background: linear-gradient(90deg, #2D6BFF, #60A5FA); }
.rank-fill.price { background: linear-gradient(90deg, #F59E0B, #FBBF24); }

.rank-value {
  width: 80px;
  text-align: right;
  font-size: 12.5px;
  color: #4B5563;
  font-weight: 600;
  flex-shrink: 0;
}

.region-chart { height: 280px; }

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
  border-image: linear-gradient(180deg, #10B981, #2D6BFF) 1;
}

@media (max-width: 768px) {
  .hero-card { flex-direction: column; gap: 16px; text-align: center; padding: 24px 20px; }
  .view-toggle { flex-direction: column; gap: 12px; }
  .map-container { height: 350px; }
}
</style>

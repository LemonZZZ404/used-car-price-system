<template>
  <div class="brandgraph-page" v-loading="loading" element-loading-text="图谱加载中...">
    <!-- Hero -->
    <div class="hero-card card card-grad-purple">
      <div class="hero-left">
        <div class="hero-badge">
          <el-icon><Share /></el-icon>
          <span>品牌图谱</span>
        </div>
        <h2 class="hero-title">
          <span class="gradient-text-white">品牌 · 车系 关系网络</span>
        </h2>
        <p class="hero-desc">共 {{ totalBrands }} 个品牌 · 层级化展示 · 交互式探索</p>
      </div>
      <div class="hero-right">
        <div class="view-mode-toggle">
          <div class="vm-btn" :class="{ active: graphMode === 'tree' }" @click="graphMode = 'tree'">
            <el-icon><Menu /></el-icon> 树状图
          </div>
          <div class="vm-btn" :class="{ active: graphMode === 'graph' }" @click="graphMode = 'graph'">
            <el-icon><Connection /></el-icon> 关系图
          </div>
          <div class="vm-btn" :class="{ active: graphMode === 'radial' }" @click="graphMode = 'radial'">
            <el-icon><Aim /></el-icon> 放射图
          </div>
        </div>
      </div>
      <div class="hero-deco">
        <svg viewBox="0 0 200 200" class="deco-network">
          <circle cx="40" cy="160" r="30" fill="rgba(255,255,255,0.08)"/>
          <circle cx="80" cy="120" r="20" fill="rgba(255,255,255,0.1)"/>
          <circle cx="120" cy="160" r="25" fill="rgba(255,255,255,0.08)"/>
          <line x1="40" y1="160" x2="80" y2="120" stroke="rgba(255,255,255,0.2)" stroke-width="1.5"/>
          <line x1="80" y1="120" x2="120" y2="160" stroke="rgba(255,255,255,0.2)" stroke-width="1.5"/>
        </svg>
      </div>
    </div>

    <!-- 主图 -->
    <div class="card graph-card">
      <div class="graph-header">
        <div class="graph-title">
          <span v-if="graphMode === 'tree'">树状层级图</span>
          <span v-else-if="graphMode === 'graph'">力导向关系图</span>
          <span v-else>放射状树图</span>
        </div>
        <div class="graph-tips">
          <el-tag size="small" type="info" effect="plain">滚轮缩放 · 拖拽移动 · 点击展开</el-tag>
        </div>
      </div>
      <div ref="graphChartRef" class="graph-container"></div>
    </div>

    <!-- 品牌详情卡片 -->
    <div class="card">
      <div class="card-title">
        <span>品牌详情</span>
        <el-tag type="primary" effect="light" size="small" round>TOP 12 品牌</el-tag>
      </div>
      <div class="brand-grid">
        <div v-for="(brand, index) in brandList" :key="brand.name"
             class="brand-card" :class="{ active: selectedBrand === brand.name }"
             @click="selectBrand(brand.name)">
          <div class="bc-rank" :style="{ background: brandColors[index % brandColors.length] }">{{ index + 1 }}</div>
          <div class="bc-name">{{ brand.name }}</div>
          <div class="bc-stats">
            <div class="bc-stat">
              <div class="bc-stat-num">{{ formatNum(brand.value) }}</div>
              <div class="bc-stat-label">车源数</div>
            </div>
            <div class="bc-stat">
              <div class="bc-stat-num">{{ brand.children?.length || 0 }}</div>
              <div class="bc-stat-label">车系</div>
            </div>
          </div>
          <div class="bc-series">
            <span v-for="s in (brand.children || []).slice(0, 4)" :key="s.name" class="bc-series-tag">
              {{ s.name }}
            </span>
            <span v-if="(brand.children || []).length > 4" class="bc-series-tag more">
              +{{ (brand.children || []).length - 4 }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 选中品牌详情 -->
    <div v-if="selectedBrand" class="card detail-card">
      <div class="detail-header">
        <div class="detail-brand-name">
          <span class="brand-dot" :style="{ background: selectedBrandColor }"></span>
          {{ selectedBrand }}
        </div>
        <el-button size="small" @click="selectedBrand = ''" text>
          <el-icon><Close /></el-icon> 关闭
        </el-button>
      </div>
      <el-row :gutter="20">
        <el-col :xs="24" :md="12">
          <div class="detail-chart-title">车系价格分布</div>
          <div ref="seriesChartRef" class="detail-chart"></div>
        </el-col>
        <el-col :xs="24" :md="12">
          <div class="detail-chart-title">车系数量占比</div>
          <div ref="seriesPieRef" class="detail-chart"></div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { Share, Menu, Connection, Aim, Close } from '@element-plus/icons-vue'
import echarts from '@/utils/echarts'
import { vizBrandHierarchy } from '@/api'

const graphMode = ref('tree')
const selectedBrand = ref('')
const brandData = ref({ tree: [], total_brands: 0 })
const loading = ref(true)

const graphChartRef = ref(null)
const seriesChartRef = ref(null)
const seriesPieRef = ref(null)
let graphChart = null
let seriesChart = null
let seriesPieChart = null

const brandColors = [
  '#2D6BFF', '#22C55E', '#F59E0B', '#EF4444', '#8B5CF6',
  '#EC4899', '#06B6D4', '#F97316', '#6366F1', '#14B8A6',
  '#EAB308', '#84CC16'
]

const totalBrands = computed(() => brandData.value.total_brands || 0)
const brandList = computed(() => brandData.value.tree || [])

const selectedBrandColor = computed(() => {
  const idx = brandList.value.findIndex(b => b.name === selectedBrand.value)
  return idx >= 0 ? brandColors[idx % brandColors.length] : '#2D6BFF'
})

const formatNum = (n) => {
  if (!n) return 0
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  return n.toLocaleString()
}

const initTreeChart = () => {
  if (!graphChartRef.value) return
  if (graphChart) graphChart.dispose()
  graphChart = echarts.init(graphChartRef.value)

  const treeData = brandData.value.tree.map((brand, i) => ({
    name: brand.name,
    value: brand.value,
    itemStyle: { color: brandColors[i % brandColors.length] },
    children: brand.children.map(s => ({
      name: s.name,
      value: s.value,
      itemStyle: { color: brandColors[i % brandColors.length] + '99' }
    }))
  }))

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (p) => {
        const path = (p.treePathInfo || []).map(t => t.name).join(' / ')
        return `${path}<br/>车源: <b>${formatNum(p.value)}</b> 辆`
      }
    },
    series: [{
      type: 'tree',
      data: treeData,
      top: '5%',
      left: '10%',
      bottom: '5%',
      right: '20%',
      symbolSize: 10,
      orient: 'LR',
      expandAndCollapse: true,
      initialTreeDepth: 2,
      animationDuration: 550,
      animationDurationUpdate: 750,
      label: {
        position: 'left',
        verticalAlign: 'middle',
        align: 'right',
        fontSize: 12,
        fontWeight: 500,
        color: '#374151'
      },
      leaves: {
        label: {
          position: 'right',
          verticalAlign: 'middle',
          align: 'left',
          fontSize: 11,
          color: '#6B7280',
          fontWeight: 'normal'
        }
      },
      emphasis: { focus: 'descendant' },
      lineStyle: {
        color: '#D1D5DB',
        width: 1.5,
        curveness: 0.5
      },
      itemStyle: {
        borderColor: '#fff',
        borderWidth: 2
      }
    }]
  }
  graphChart.setOption(option)
}

const initGraphChart = () => {
  if (!graphChartRef.value) return
  if (graphChart) graphChart.dispose()
  graphChart = echarts.init(graphChartRef.value)

  const nodes = []
  const links = []
  const categories = []

  brandData.value.tree.forEach((brand, bi) => {
    categories.push({ name: brand.name })
    nodes.push({
      name: brand.name,
      value: brand.value,
      symbolSize: Math.min(50, 20 + Math.log10(brand.value) * 8),
      category: bi,
      itemStyle: { color: brandColors[bi % brandColors.length] }
    })
    brand.children.forEach(s => {
      nodes.push({
        name: s.name,
        value: s.value,
        symbolSize: Math.min(30, 10 + Math.log10(s.value + 1) * 6),
        category: bi,
        itemStyle: { color: brandColors[bi % brandColors.length] + 'AA' }
      })
      links.push({ source: brand.name, target: s.name, value: s.value })
    })
  })

  const option = {
    tooltip: {
      formatter: (p) => {
        if (p.dataType === 'node') {
          return `<b>${p.name}</b><br/>车源: ${formatNum(p.value)} 辆`
        }
        return ''
      }
    },
    legend: {
      data: categories.map(c => c.name),
      type: 'scroll',
      top: 10,
      textStyle: { color: '#6B7280', fontSize: 11 }
    },
    series: [{
      type: 'graph',
      layout: 'force',
      data: nodes,
      links: links,
      categories: categories,
      roam: true,
      draggable: true,
      label: {
        show: true,
        position: 'right',
        fontSize: 10,
        color: '#4B5563',
        formatter: '{b}'
      },
      force: {
        repulsion: 200,
        edgeLength: [30, 80],
        gravity: 0.1
      },
      lineStyle: {
        color: '#E5E7EB',
        width: 1,
        curveness: 0.1
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: { width: 2 }
      },
      itemStyle: {
        borderColor: '#fff',
        borderWidth: 2,
        shadowBlur: 8,
        shadowColor: 'rgba(0,0,0,0.1)'
      }
    }]
  }
  graphChart.setOption(option)
}

const initRadialChart = () => {
  if (!graphChartRef.value) return
  if (graphChart) graphChart.dispose()
  graphChart = echarts.init(graphChartRef.value)

  const treeData = brandData.value.tree.map((brand, i) => ({
    name: brand.name,
    value: brand.value,
    itemStyle: { color: brandColors[i % brandColors.length] },
    children: brand.children.map(s => ({
      name: s.name,
      value: s.value,
      itemStyle: { color: brandColors[i % brandColors.length] + '99' }
    }))
  }))

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (p) => {
        const path = (p.treePathInfo || []).map(t => t.name).join(' / ')
        return `${path}<br/>车源: <b>${formatNum(p.value)}</b> 辆`
      }
    },
    series: [{
      type: 'tree',
      data: treeData,
      top: '10%',
      left: '15%',
      bottom: '10%',
      right: '15%',
      symbolSize: 8,
      layout: 'radial',
      expandAndCollapse: true,
      initialTreeDepth: 2,
      animationDuration: 550,
      label: {
        position: 'radial',
        rotate: 'tangential',
        fontSize: 11,
        color: '#374151',
        fontWeight: 500
      },
      leaves: {
        label: { fontSize: 10, color: '#6B7280', fontWeight: 'normal' }
      },
      emphasis: { focus: 'descendant' },
      lineStyle: {
        color: '#D1D5DB',
        width: 1,
        curveness: 0.4
      },
      itemStyle: { borderColor: '#fff', borderWidth: 2 }
    }]
  }
  graphChart.setOption(option)
}

const renderGraph = () => {
  if (graphMode.value === 'tree') initTreeChart()
  else if (graphMode.value === 'graph') initGraphChart()
  else initRadialChart()
}

const selectBrand = (name) => {
  selectedBrand.value = name
  setTimeout(() => {
    renderSeriesCharts(name)
  }, 150)
}

const renderSeriesCharts = (brandName) => {
  const brand = brandList.value.find(b => b.name === brandName)
  if (!brand) return
  const series = brand.children || []
  const bi = brandList.value.findIndex(b => b.name === brandName)
  const color = brandColors[bi % brandColors.length]

  // 横向柱状图
  if (seriesChartRef.value) {
    if (seriesChart) seriesChart.dispose()
    seriesChart = echarts.init(seriesChartRef.value)
    seriesChart.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: 10, right: 30, top: 10, bottom: 10, containLabel: true },
      xAxis: {
        type: 'value',
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#6B7280', fontSize: 11, formatter: v => formatNum(v) },
        splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } }
      },
      yAxis: {
        type: 'category',
        data: series.map(s => s.name).reverse(),
        axisLine: { lineStyle: { color: '#E5E7EB' } },
        axisLabel: { color: '#4B5563', fontSize: 11 }
      },
      series: [{
        type: 'bar',
        data: series.map(s => s.value).reverse(),
        barWidth: '55%',
        itemStyle: {
          borderRadius: [0, 4, 4, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: color + '40' },
            { offset: 1, color: color }
          ])
        }
      }]
    })
  }

  // 饼图
  if (seriesPieRef.value) {
    if (seriesPieChart) seriesPieChart.dispose()
    seriesPieChart = echarts.init(seriesPieRef.value)
    seriesPieChart.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '50%'],
        itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
        label: { show: false },
        emphasis: {
          label: { show: true, fontSize: 12, fontWeight: 'bold' },
          itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.15)' }
        },
        data: series.slice(0, 8).map((s, i) => ({
          name: s.name,
          value: s.value,
          itemStyle: {
            color: i === 0 ? color : color + Math.max(30, 90 - i * 10).toString(16)
          }
        }))
      }]
    })
  }
}

const loadData = async () => {
  try {
    const res = await vizBrandHierarchy()
    if (res.code === 200) {
      brandData.value = res.data
      await nextTick()
      // 延迟初始化，确保 DOM 布局完成；图画完再撤掉 loading，避免闪现空画布
      setTimeout(() => {
        renderGraph()
        loading.value = false
      }, 100)
      return
    }
  } catch (e) {
    console.error('Load brand graph error:', e)
  }
  loading.value = false
}

watch(graphMode, () => {
  renderGraph()
})

const handleResize = () => {
  graphChart && graphChart.resize()
  seriesChart && seriesChart.resize()
  seriesPieChart && seriesPieChart.dispose()
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  graphChart && graphChart.dispose()
  seriesChart && seriesChart.dispose()
  seriesPieChart && seriesPieChart.dispose()
})
</script>

<style scoped>
.brandgraph-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* Hero */
.hero-card {
  position: relative;
  overflow: hidden;
  color: #fff;
  background: linear-gradient(135deg, #7C3AED 0%, #8B5CF6 50%, #A78BFA 100%);
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
  background: linear-gradient(90deg, #fff, #DDD6FE);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-desc { font-size: 13.5px; color: rgba(255,255,255,0.75); margin: 0; }

.hero-right { position: relative; z-index: 2; }

.view-mode-toggle {
  display: flex;
  background: rgba(255,255,255,0.15);
  backdrop-filter: blur(10px);
  border-radius: 10px;
  padding: 4px;
}

.vm-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 12.5px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  color: rgba(255,255,255,0.7);
}

.vm-btn:hover { color: #fff; }

.vm-btn.active {
  background: #fff;
  color: #7C3AED;
  font-weight: 600;
}

.hero-deco { position: absolute; bottom: 0; right: 0; pointer-events: none; }
.deco-network { width: 200px; height: 200px; opacity: 0.8; }

/* Graph card */
.graph-card { padding: 16px 20px; }

.graph-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.graph-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  padding-left: 10px;
  border-left: 3px solid;
  border-image: linear-gradient(180deg, #8B5CF6, #EC4899) 1;
}

.graph-container {
  width: 100%;
  height: 500px;
}

/* Brand grid */
.brand-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}

.brand-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.25s ease;
  position: relative;
  overflow: hidden;
}

.brand-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--card-shadow-hover);
  border-color: #BFDBFE;
}

.brand-card.active {
  border-color: #2D6BFF;
  background: linear-gradient(180deg, #EFF6FF, #fff 40%);
  box-shadow: 0 4px 16px rgba(45,107,255,0.15);
}

.bc-rank {
  position: absolute;
  top: 0;
  right: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  color: #fff;
  border-bottom-left-radius: 12px;
  clip-path: polygon(100% 0, 0 0, 100% 100%);
}

.bc-name {
  font-size: 16px;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.bc-stats {
  display: flex;
  gap: 20px;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px dashed var(--border-color);
}

.bc-stat-num {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
}

.bc-stat-label {
  font-size: 11px;
  color: #6B7280;
  margin-top: 3px;
}

.bc-series {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.bc-series-tag {
  font-size: 11px;
  padding: 2px 7px;
  background: var(--bg-secondary);
  color: #4B5563;
  border-radius: 4px;
}

.bc-series-tag.more {
  background: #EFF6FF;
  color: #2D6BFF;
  font-weight: 600;
}

/* Detail card */
.detail-card {
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.detail-brand-name {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 800;
  color: var(--text-primary);
}

.brand-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  box-shadow: 0 0 10px currentColor;
}

.detail-chart-title {
  font-size: 13px;
  font-weight: 600;
  color: #4B5563;
  margin-bottom: 8px;
}

.detail-chart {
  width: 100%;
  height: 240px;
}

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
  border-image: linear-gradient(180deg, #8B5CF6, #2D6BFF) 1;
}

@media (max-width: 768px) {
  .hero-card { flex-direction: column; gap: 16px; text-align: center; padding: 24px 20px; }
  .graph-container { height: 350px; }
  .brand-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>

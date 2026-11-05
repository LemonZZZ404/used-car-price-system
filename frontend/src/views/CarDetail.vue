<template>
  <div class="car-detail-page">
    <div class="page-top">
      <el-button :icon="ArrowLeft" @click="goBack">返回</el-button>
      <span class="top-title">{{ car.brand }} {{ car.series }} {{ car.model }}</span>
    </div>

    <el-empty v-if="notFound" description="车辆不存在或已被下架" />

    <template v-else>
      <!-- 头部价格区 -->
      <div class="card hero-card">
        <div class="hero-left">
          <div class="hero-price">
            <span class="price-num">{{ car.price }}</span>
            <span class="price-unit">万元</span>
          </div>
          <div class="hero-tags">
            <el-tag effect="plain" size="small">{{ car.brand }}</el-tag>
            <el-tag effect="plain" size="small" type="info" v-if="car.age !== null">{{ car.age }} 年车龄</el-tag>
            <el-tag effect="plain" size="small" type="info" v-if="car.mileage !== null">{{ car.mileage }} 万公里</el-tag>
            <el-tag effect="plain" size="small" :type="car.gearbox === '自动' ? 'success' : 'info'">{{ car.gearbox }}</el-tag>
            <el-tag effect="plain" size="small" type="warning" v-if="car.fuel_type">{{ car.fuel_type }}</el-tag>
          </div>
          <div class="hero-sub" v-if="car.original_price">
            新车指导价 {{ car.original_price }} 万 · 当前保值率
            <b>{{ retentionPct }}%</b>
          </div>
        </div>
        <div class="hero-right">
          <el-button type="primary" :icon="MagicStick" @click="goSimulate">模拟估价</el-button>
        </div>
      </div>

      <el-row :gutter="20" class="mt20">
        <!-- 基本信息 -->
        <el-col :xs="24" :md="10">
          <div class="card h-full">
            <div class="card-title">基本信息</div>
            <el-descriptions :column="1" border size="small" class="detail-desc">
              <el-descriptions-item label="车辆编号">{{ car.car_id }}</el-descriptions-item>
              <el-descriptions-item label="品牌 / 车系">{{ car.brand }} / {{ car.series }}</el-descriptions-item>
              <el-descriptions-item label="车型">{{ car.model || '—' }}</el-descriptions-item>
              <el-descriptions-item label="售价">{{ car.price }} 万元</el-descriptions-item>
              <el-descriptions-item label="新车指导价">{{ car.original_price ?? '—' }} 万元</el-descriptions-item>
              <el-descriptions-item label="车龄">{{ car.age ?? '—' }} 年</el-descriptions-item>
              <el-descriptions-item label="里程">{{ car.mileage ?? '—' }} 万公里</el-descriptions-item>
              <el-descriptions-item label="变速箱">{{ car.gearbox || '—' }}</el-descriptions-item>
              <el-descriptions-item label="排量">{{ car.displacement || '—' }}</el-descriptions-item>
              <el-descriptions-item label="燃油类型">{{ car.fuel_type || '—' }}</el-descriptions-item>
              <el-descriptions-item label="颜色">{{ car.color || '—' }}</el-descriptions-item>
              <el-descriptions-item label="所在城市">{{ car.city || '—' }}</el-descriptions-item>
              <el-descriptions-item label="上牌日期">{{ car.register_date || '—' }}</el-descriptions-item>
              <el-descriptions-item label="数据入库">{{ car.create_time || '—' }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </el-col>

        <el-col :xs="24" :md="14">
          <!-- 同车系比价 -->
          <div class="card">
            <div class="card-title">同车系比价（车龄 ±1 年）</div>
            <div class="peer-grid">
              <div class="peer-item">
                <div class="peer-num">{{ peers.count }}</div>
                <div class="peer-label">可比车源</div>
              </div>
              <div class="peer-item">
                <div class="peer-num">{{ peers.avg_price ?? '—' }}</div>
                <div class="peer-label">车系均价(万)</div>
              </div>
              <div class="peer-item">
                <div class="peer-num">{{ marketDepth.count }}</div>
                <div class="peer-label">同价位在售(±15%)</div>
              </div>
            </div>
            <div class="pct-wrap" v-if="peers.percentile !== null">
              <div class="pct-label">
                该车价格低于同车系近龄车源中 <b class="pct-val">{{ peers.percentile }}%</b> 的车源
              </div>
              <div class="pct-bar">
                <div class="pct-fill" :style="{ width: (peers.percentile || 0) + '%' }"></div>
                <div class="pct-marker" :style="{ left: (peers.percentile || 0) + '%' }"></div>
              </div>
              <div class="pct-legend">
                <span>便宜</span><span>贵</span>
              </div>
            </div>
            <el-empty v-else description="暂无可比车源" :image-size="60" />
          </div>

          <!-- 车龄贬值曲线 -->
          <div class="card mt20">
            <div class="card-title">
              <span>{{ car.series }} 车龄-均价曲线</span>
              <el-tag size="small" effect="plain" type="primary" v-if="car.age !== null">
                当前 {{ car.age }} 年
              </el-tag>
            </div>
            <div ref="depChartRef" class="chart-box"></div>
          </div>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, MagicStick } from '@element-plus/icons-vue'
import echarts from '@/utils/echarts'
import { chartPalette, SERIES_COLORS, registerChart, unregisterChart } from '@/utils/theme'
import { getCarDetail } from '@/api'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const notFound = ref(false)
const car = ref({})
const peers = ref({})
const seriesDep = ref([])
const marketDepth = ref({})

const depChartRef = ref(null)
let depChart = null

const retentionPct = computed(() => {
  if (!car.value.price || !car.value.original_price) return '—'
  return Math.round(car.value.price / car.value.original_price * 100)
})

const goBack = () => {
  if (window.history.length > 1) router.back()
  else router.push('/cars')
}
const goSimulate = () => router.push({
  path: '/simulator',
  query: {
    brand: car.value.brand, age: car.value.age ?? 3,
    mileage: car.value.mileage ?? 5, original_price: car.value.original_price ?? 15
  }
})

const loadDetail = async () => {
  loading.value = true
  try {
    const res = await getCarDetail(route.params.id)
    if (res.code === 200 && res.data) {
      car.value = res.data.car || {}
      peers.value = res.data.peers || {}
      seriesDep.value = res.data.series_dep || []
      marketDepth.value = res.data.market_depth || {}
      await nextTick()
      renderDepChart()
    } else {
      notFound.value = true
    }
  } catch (e) {
    if (e?.response?.status === 404) notFound.value = true
    else ElMessage.error('加载车辆详情失败')
  } finally {
    loading.value = false
  }
}

const renderDepChart = () => {
  if (!depChartRef.value || !seriesDep.value.length) return
  if (!depChart) depChart = echarts.init(depChartRef.value)
  const p = chartPalette()
  depChart.setOption({
    grid: { left: 50, right: 20, top: 30, bottom: 30 },
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const d = params[0]
        const row = seriesDep.value[d.dataIndex]
        return `${row.age} 年车龄<br/>均价 ${row.avg_price} 万 · ${row.count} 辆在售`
      }
    },
    xAxis: {
      type: 'category',
      data: seriesDep.value.map(r => r.age + '年'),
      axisLine: { lineStyle: { color: p.axisLine } },
      axisLabel: { color: p.text }
    },
    yAxis: {
      type: 'value',
      name: '均价(万)',
      nameTextStyle: { color: p.text },
      axisLine: { show: false },
      splitLine: { lineStyle: { color: p.splitLine } },
      axisLabel: { color: p.text }
    },
    series: [{
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 7,
      data: seriesDep.value.map(r => r.avg_price),
      lineStyle: { width: 3, color: SERIES_COLORS[0][0] },
      itemStyle: { color: SERIES_COLORS[0][0] },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(45,107,255,0.25)' },
            { offset: 1, color: 'rgba(45,107,255,0.02)' }
          ]
        }
      },
      markPoint: car.value.age !== null ? {
        symbol: 'pin', symbolSize: 46,
        itemStyle: { color: '#EF4444' },
        label: { color: '#fff', fontSize: 10, formatter: '本车' },
        data: [{ coord: [car.value.age + '年', car.value.price] }]
      } : undefined
    }]
  })
  registerChart(depChart, renderDepChart)
}

onMounted(loadDetail)
onUnmounted(() => {
  if (depChart) { unregisterChart(depChart); depChart.dispose() }
})
</script>

<style scoped>
.page-top { display: flex; align-items: center; gap: 14px; }
.top-title { font-size: 17px; font-weight: 600; }
.mt20 { margin-top: 20px; }
.h-full { height: 100%; }

.hero-card { display: flex; justify-content: space-between; align-items: center; }
.hero-price .price-num { font-size: 42px; font-weight: 700; color: #EF4444; }
.hero-price .price-unit { font-size: 14px; color: #EF4444; margin-left: 4px; }
.hero-tags { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
.hero-sub { margin-top: 10px; color: #6B7280; font-size: 13px; }
.hero-sub b { color: #2D6BFF; }

.detail-desc :deep(.el-descriptions__label) { width: 110px; }
.peer-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 14px 0; }
.peer-item { text-align: center; padding: 14px 8px; border-radius: 10px; background: rgba(45,107,255,0.05); }
.peer-num { font-size: 26px; font-weight: 700; color: #2D6BFF; }
.peer-label { font-size: 12px; color: #6B7280; margin-top: 4px; }
.pct-wrap { margin-top: 6px; }
.pct-label { font-size: 13px; color: #6B7280; margin-bottom: 10px; }
.pct-val { color: #EF4444; font-size: 16px; }
.pct-bar { position: relative; height: 10px; border-radius: 5px; background: linear-gradient(90deg, #22C55E, #F59E0B, #EF4444); }
.pct-fill { display: none; }
.pct-marker {
  position: absolute; top: -5px; width: 4px; height: 20px;
  background: #fff; border: 2px solid #1F2937; border-radius: 2px;
  transform: translateX(-2px); box-shadow: 0 1px 4px rgba(0,0,0,0.3);
}
.pct-legend { display: flex; justify-content: space-between; font-size: 12px; color: #9CA3AF; margin-top: 8px; }
.chart-box { height: 300px; }
</style>

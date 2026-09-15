<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #409EFF, #66b1ff)">
            <el-icon><Car /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ summary.total_cars || 0 }}</div>
            <div class="stat-label">车辆总数</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #67C23A, #85ce61)">
            <el-icon><Collection /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ summary.total_brands || 0 }}</div>
            <div class="stat-label">品牌数量</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #E6A23C, #ebb563)">
            <el-icon><Money /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ summary.avg_price || 0 }}<span style="font-size:16px">万</span></div>
            <div class="stat-label">平均售价</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #F56C6C, #f78989)">
            <el-icon><MagicStick /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ summary.total_predictions || 0 }}</div>
            <div class="stat-label">预测次数</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <div class="card">
          <div class="card-title">品牌均价 Top 10</div>
          <div ref="brandChartRef" class="chart-container"></div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="card">
          <div class="card-title">车龄与价格关系</div>
          <div ref="ageChartRef" class="chart-container"></div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <div class="card">
          <div class="card-title">价格分布</div>
          <div ref="priceDistChartRef" class="chart-container"></div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="card">
          <div class="card-title">最近预测记录</div>
          <el-table :data="summary.latest_predictions || []" size="small" stripe>
            <el-table-column prop="brand" label="品牌" width="80" />
            <el-table-column prop="age" label="车龄" width="60">
              <template #default="{ row }">{{ row.age }}年</template>
            </el-table-column>
            <el-table-column prop="mileage" label="里程" width="80">
              <template #default="{ row }">{{ row.mileage }}万</template>
            </el-table-column>
            <el-table-column prop="predicted_price" label="预测价格" width="100">
              <template #default="{ row }">
                <span style="color:#F56C6C;font-weight:600">{{ row.predicted_price }}万</span>
              </template>
            </el-table-column>
            <el-table-column prop="model_type" label="模型" width="100" />
            <el-table-column prop="create_time" label="时间" min-width="140" />
          </el-table>
          <el-empty v-if="!summary.latest_predictions || summary.latest_predictions.length === 0"
                    description="暂无预测记录" :image-size="80" />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getDashboardSummary, getBrandPriceTop10, getAgePriceChart, getPriceDistributionChart } from '@/api'

const summary = ref({})
const brandChartRef = ref(null)
const ageChartRef = ref(null)
const priceDistChartRef = ref(null)

let brandChart = null
let ageChart = null
let priceDistChart = null

const initCharts = () => {
  if (brandChartRef.value) brandChart = echarts.init(brandChartRef.value)
  if (ageChartRef.value) ageChart = echarts.init(ageChartRef.value)
  if (priceDistChartRef.value) priceDistChart = echarts.init(priceDistChartRef.value)
}

const loadDashboard = async () => {
  try {
    const res = await getDashboardSummary()
    if (res.code === 200) summary.value = res.data
  } catch (e) {
    console.error('加载看板数据失败', e)
  }
}

const loadBrandChart = async () => {
  try {
    const res = await getBrandPriceTop10()
    if (!brandChart) return
    brandChart.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      legend: { data: ['平均售价', '车辆数量'] },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'category', data: res.xAxis || [], axisLabel: { rotate: 30 } },
      yAxis: [
        { type: 'value', name: '售价(万)' },
        { type: 'value', name: '数量' }
      ],
      series: res.series || []
    })
  } catch (e) {
    // 使用模拟数据
    brandChart?.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: ['保时捷', '奔驰', '宝马', '奥迪', '雷克萨斯', '沃尔沃', '特斯拉', '大众', '丰田', '本田'] },
      yAxis: { type: 'value', name: '售价(万)' },
      series: [{ type: 'bar', data: [85, 42, 40, 36, 35, 32, 28, 16, 16, 15], itemStyle: { color: '#409EFF' } }]
    })
  }
}

const loadAgeChart = async () => {
  try {
    const res = await getAgePriceChart()
    if (!ageChart) return
    ageChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['平均售价', '车辆数量'] },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'category', data: res.xAxis || [] },
      yAxis: [
        { type: 'value', name: '售价(万)' },
        { type: 'value', name: '数量' }
      ],
      series: res.series || []
    })
  } catch (e) {
    ageChart?.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: ['0年','1年','2年','3年','4年','5年','6年','7年','8年','10年','12年','15年'] },
      yAxis: { type: 'value', name: '售价(万)' },
      series: [{ type: 'line', smooth: true, data: [22, 19, 16, 14, 12, 10, 8.5, 7.5, 6.5, 5, 4, 3], areaStyle: {}, itemStyle: { color: '#67C23A' } }]
    })
  }
}

const loadPriceDistChart = async () => {
  try {
    const res = await getPriceDistributionChart()
    if (!priceDistChart) return
    priceDistChart.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c}辆 ({d}%)' },
      legend: { orient: 'vertical', left: 'left' },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
        label: { show: false, position: 'center' },
        emphasis: { label: { show: true, fontSize: 18, fontWeight: 'bold' } },
        labelLine: { show: false },
        data: res.pie_data || []
      }]
    })
  } catch (e) {
    priceDistChart?.setOption({
      tooltip: { trigger: 'item' },
      series: [{
        type: 'pie', radius: ['40%', '70%'],
        data: [
          { value: 3200, name: '0-5万' }, { value: 5800, name: '5-10万' },
          { value: 4500, name: '10-15万' }, { value: 3000, name: '15-20万' },
          { value: 2000, name: '20-30万' }, { value: 1000, name: '30-50万' },
          { value: 500, name: '50万以上' }
        ]
      }]
    })
  }
}

const handleResize = () => {
  brandChart?.resize()
  ageChart?.resize()
  priceDistChart?.resize()
}

onMounted(async () => {
  await nextTick()
  initCharts()
  await Promise.all([loadDashboard(), loadBrandChart(), loadAgeChart(), loadPriceDistChart()])
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  brandChart?.dispose()
  ageChart?.dispose()
  priceDistChart?.dispose()
})
</script>

<style scoped>
.dashboard { padding: 0; }
.stat-row { margin-bottom: 20px; }
.chart-row { margin-bottom: 20px; }
</style>

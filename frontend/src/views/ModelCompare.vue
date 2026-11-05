<template>
  <div class="model-compare">
    <!-- 模型对比指标卡片 -->
    <el-row :gutter="20" class="metric-cards">
      <el-col v-for="m in models" :key="m.name" :xs="12" :sm="12" :md="6">
        <div class="model-card" :class="{ best: m.isBest }">
          <div class="model-badge" v-if="m.isBest">最优</div>
          <div class="model-name">{{ m.name }}</div>
          <div class="model-metrics">
            <div class="metric-row">
              <span class="metric-label">RMSE</span>
              <span class="metric-value">{{ m.rmse }}</span>
            </div>
            <div class="metric-row">
              <span class="metric-label">MAE</span>
              <span class="metric-value">{{ m.mae }}</span>
            </div>
            <div class="metric-row">
              <span class="metric-label">MAPE</span>
              <span class="metric-value" :class="{ 'best-val': m.isBest }">{{ m.mape }}%</span>
            </div>
            <div class="metric-row">
              <span class="metric-label">R²</span>
              <span class="metric-value">{{ m.r2 }}</span>
            </div>
            <div class="metric-row">
              <span class="metric-label">训练耗时</span>
              <span class="metric-value">{{ m.train_time }}s</span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 对比图表 -->
    <el-row :gutter="20">
      <el-col :xs="24" :md="12">
        <div class="card">
          <div class="card-title">RMSE 对比（越低越好）</div>
          <div ref="rmseChartRef" class="chart-container"></div>
        </div>
      </el-col>
      <el-col :xs="24" :md="12">
        <div class="card">
          <div class="card-title">MAPE 对比（越低越好）</div>
          <div ref="mapeChartRef" class="chart-container"></div>
        </div>
      </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top:20px">
      <el-col :xs="24" :md="12">
        <div class="card">
          <div class="card-title">R² 对比（越高越好）</div>
          <div ref="r2ChartRef" class="chart-container"></div>
        </div>
      </el-col>
      <el-col :xs="24" :md="12">
        <div class="card">
          <div class="card-title">训练效率对比（秒）</div>
          <div ref="timeChartRef" class="chart-container"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 完整对比表 -->
    <div class="card" style="margin-top:20px">
      <div class="card-title">
        四模型完整指标对比
        <el-tag type="primary" effect="light" size="small" round>100 万条数据</el-tag>
      </div>
      <el-table :data="models" stripe border size="default">
        <el-table-column prop="name" label="模型" width="160">
          <template #default="{ row }">
            <span style="font-weight:600">{{ row.name }}</span>
            <el-tag v-if="row.isBest" type="success" size="small" round style="margin-left:8px">最优</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="rmse" label="RMSE" width="100" align="center">
          <template #default="{ row }">
            <span :style="{ color: row.isBest ? '#22C55E' : '', fontWeight: row.isBest ? 700 : 400 }">{{ row.rmse }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="mae" label="MAE" width="100" align="center" />
        <el-table-column prop="mape" label="MAPE (%)" width="110" align="center">
          <template #default="{ row }">
            <span :style="{ color: row.mape <= 15 ? '#22C55E' : row.mape <= 25 ? '#F59E0B' : '#EF4444', fontWeight: 600 }">
              {{ row.mape }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="r2" label="R²" width="100" align="center">
          <template #default="{ row }">
            <span :style="{ color: row.r2 >= 0.94 ? '#22C55E' : row.r2 >= 0.9 ? '#F59E0B' : '#EF4444', fontWeight: 600 }">
              {{ row.r2 }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="train_time" label="训练耗时(s)" width="120" align="center" />
        <el-table-column label="特点" min-width="200">
          <template #default="{ row }">
            <span style="color:#6B7280;font-size:13px">{{ row.desc }}</span>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import echarts from '@/utils/echarts'

const models = ref([
  { name: '线性回归', rmse: 2.4601, mae: 1.6348, mape: 41.10, r2: 0.7921, train_time: 2.3, isBest: false, desc: '基线模型，解释性强但精度低' },
  { name: '随机森林', rmse: 1.4030, mae: 1.0135, mape: 20.51, r2: 0.9323, train_time: 16.5, isBest: false, desc: '稳定可靠，特征重要性可解释' },
  { name: 'LightGBM', rmse: 1.2367, mae: 0.8771, mape: 14.36, r2: 0.9474, train_time: 2.5, isBest: true, desc: '梯度提升，训练快精度高' },
  { name: 'XGBoost', rmse: 1.2482, mae: 0.8801, mape: 14.35, r2: 0.9464, train_time: 23.9, isBest: false, desc: '梯度提升，精度高但训练慢' }
])

const rmseChartRef = ref(null)
const mapeChartRef = ref(null)
const r2ChartRef = ref(null)
const timeChartRef = ref(null)

let rmseChart = null
let mapeChart = null
let r2Chart = null
let timeChart = null

const COLORS = {
  blue: '#2D6BFF',
  green: '#22C55E',
  orange: '#F59E0B',
  red: '#EF4444',
  purple: '#8B5CF6'
}

const modelColors = ['#9CA3AF', COLORS.blue, COLORS.green, COLORS.orange]

const makeBarOption = (title, field, suffix = '', lowerBetter = true) => {
  const data = models.value.map(m => m[field])
  const minVal = Math.min(...data)
  return {
    color: modelColors,
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: models.value.map(m => m.name),
      axisLabel: { color: '#6B7280', fontSize: 11 },
      axisLine: { lineStyle: { color: '#E5E7EB' } }
    },
    yAxis: { type: 'value', name: title, axisLabel: { color: '#6B7280' }, splitLine: { lineStyle: { color: '#F3F4F6' } } },
    series: [{
      type: 'bar',
      data: data.map((v, i) => ({
        value: v,
        itemStyle: {
          borderRadius: [6, 6, 0, 0],
          color: v === minVal && lowerBetter ? new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: COLORS.green },
            { offset: 1, color: '#4ADE80' }
          ]) : modelColors[i]
        }
      })),
      barMaxWidth: 40,
      label: { show: true, position: 'top', color: '#4B5563', fontWeight: 600, formatter: '{c}' + suffix }
    }]
  }
}

const initCharts = () => {
  if (rmseChartRef.value) rmseChart = echarts.init(rmseChartRef.value)
  if (mapeChartRef.value) mapeChart = echarts.init(mapeChartRef.value)
  if (r2ChartRef.value) r2Chart = echarts.init(r2ChartRef.value)
  if (timeChartRef.value) timeChart = echarts.init(timeChartRef.value)
}

const updateCharts = () => {
  rmseChart?.setOption(makeBarOption('RMSE', 'rmse', '', true))
  mapeChart?.setOption(makeBarOption('MAPE(%)', 'mape', '%', true))
  r2Chart?.setOption(makeBarOption('R²', 'r2', '', false))
  timeChart?.setOption(makeBarOption('耗时(s)', 'train_time', 's', true))
}

const handleResize = () => {
  rmseChart?.resize()
  mapeChart?.resize()
  r2Chart?.resize()
  timeChart?.resize()
}

onMounted(async () => {
  await nextTick()
  initCharts()
  updateCharts()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  rmseChart?.dispose()
  mapeChart?.dispose()
  r2Chart?.dispose()
  timeChart?.dispose()
})
</script>

<style scoped>
.metric-cards { margin-bottom: 20px; }
.metric-cards .el-col { margin-bottom: 12px; }

.model-card {
  background: var(--card-bg);
  border-radius: var(--radius-md);
  padding: 20px;
  box-shadow: var(--card-shadow);
  border: 1px solid #EEF1F6;
  position: relative;
  transition: all 0.25s;
}

.model-card.best {
  border-color: #22C55E;
  background: linear-gradient(180deg, #F0FDF4, #FFFFFF 60%);
  box-shadow: 0 4px 16px rgba(34, 197, 94, 0.15);
}

.model-card:hover {
  box-shadow: var(--card-shadow-hover);
  transform: translateY(-2px);
}

.model-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  background: linear-gradient(135deg, #22C55E, #4ADE80);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 10px;
  border-radius: 12px;
}

.model-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 12px;
  padding-left: 10px;
  border-left: 3px solid var(--primary);
}

.model-card.best .model-name {
  border-left-color: #22C55E;
  color: #15803D;
}

.metric-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 0;
  border-bottom: 1px solid #F3F4F6;
}

.metric-row:last-child { border-bottom: none; }

.metric-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.metric-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
}

.best-val { color: #22C55E !important; }
</style>

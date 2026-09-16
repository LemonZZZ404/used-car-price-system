<template>
  <div class="model-analysis">
    <!-- 模型对比指标卡片 -->
    <el-row :gutter="20" class="metric-row">
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #2D6BFF, #5B8CFF)">
            <el-icon><Odometer /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ formatMetric(sklearn.r2) }}</div>
            <div class="stat-label">R² 决定系数</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #22C55E, #4ADE80)">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ formatMetric(sklearn.rmse) }}<span class="stat-unit">万</span></div>
            <div class="stat-label">RMSE 均方根误差</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #F59E0B, #FBBF24)">
            <el-icon><Aim /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ formatMetric(sklearn.mae) }}<span class="stat-unit">万</span></div>
            <div class="stat-label">MAE 平均绝对误差</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #EF4444, #F87171)">
            <el-icon><Cpu /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ formatNumber(sklearn.train_size) }}</div>
            <div class="stat-label">训练样本数</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <!-- 特征重要性 -->
      <el-col :xs="24" :md="14">
        <div class="card">
          <div class="card-title">
            <span>特征重要性 Top 12</span>
            <el-tag type="primary" effect="light" size="small" round>Scikit-learn 随机森林</el-tag>
          </div>
          <div ref="importanceChartRef" v-loading="loading" class="chart-container-lg"></div>
        </div>
      </el-col>

      <!-- 模型对比 -->
      <el-col :xs="24" :md="10">
        <div class="card">
          <div class="card-title">模型性能对比</div>
          <div ref="compareChartRef" v-loading="loading" class="chart-container-lg"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 模型对比明细表 -->
    <div class="card" style="margin-top:20px">
      <div class="card-title">模型训练指标明细</div>
      <el-table :data="compareRows" v-loading="loading" stripe border size="default">
        <el-table-column prop="metric" label="指标" width="200" />
        <el-table-column prop="sklearn" label="Scikit-learn 随机森林" />
        <el-table-column prop="spark" label="Spark MLlib 随机森林" />
        <el-table-column label="说明" min-width="220">
          <template #default="{ row }">
            <span style="color:#6B7280;font-size:13px">{{ row.desc }}</span>
          </template>
        </el-table-column>
      </el-table>
      <el-alert
        v-if="compareNote"
        type="info"
        :closable="false"
        style="margin-top:16px"
        :title="compareNote"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { Odometer, TrendCharts, Aim, Cpu } from '@element-plus/icons-vue'
import { getModelAnalysis } from '@/api'

const loading = ref(false)
const data = ref({})
const importanceChartRef = ref(null)
const compareChartRef = ref(null)
let importanceChart = null
let compareChart = null

const sklearn = computed(() => data.value.sklearn_metrics || {})
const spark = computed(() => data.value.spark_metrics || {})
const featureImportance = computed(() => data.value.feature_importance || [])

// 指标明细行
const compareRows = computed(() => {
  const s = sklearn.value
  const sp = spark.value
  return [
    { metric: 'R² 决定系数', sklearn: s.r2?.toFixed(4) ?? '-', spark: sp.r2?.toFixed(4) ?? '-', desc: '越接近 1 拟合越好' },
    { metric: 'RMSE (万元)', sklearn: s.rmse?.toFixed(4) ?? '-', spark: sp.rmse?.toFixed(4) ?? '-', desc: '均方根误差，越小越好' },
    { metric: 'MAE (万元)', sklearn: s.mae?.toFixed(4) ?? '-', spark: sp.mae?.toFixed(4) ?? '-', desc: '平均绝对误差，越小越好' },
    { metric: 'MAPE (%)', sklearn: s.mape?.toFixed(2) ?? '-', spark: '-', desc: '平均绝对百分比误差' },
    { metric: '训练样本数', sklearn: s.train_size ? Number(s.train_size).toLocaleString() : '-', spark: sp.train_size ? Number(sp.train_size).toLocaleString() : '-', desc: '模型训练使用的样本量' },
    { metric: '测试样本数', sklearn: s.test_size ? Number(s.test_size).toLocaleString() : '-', spark: sp.test_size ? Number(sp.test_size).toLocaleString() : '-', desc: '模型评估使用的样本量' },
    { metric: '树数量', sklearn: s.n_estimators ?? '-', spark: sp.num_trees ?? '-', desc: '随机森林中决策树数量' },
    { metric: '最大深度', sklearn: s.max_depth ?? '-', spark: sp.max_depth ?? '-', desc: '决策树最大深度' },
    { metric: '训练耗时', sklearn: s.train_time_seconds ? `${s.train_time_seconds}s` : '-', spark: '-', desc: '训练花费时间' },
    { metric: '训练时间', sklearn: s.train_time ?? '-', spark: sp.train_time ?? '-', desc: '模型训练完成时间' }
  ]
})

// 说明：Spark MLlib 是早期小样本实验，与 sklearn 百万样本对比说明
const compareNote = computed(() => {
  const s = sklearn.value
  const sp = spark.value
  if (s && sp && s.train_size && sp.train_size && s.train_size > sp.train_size) {
    return `说明：Scikit-learn 使用 ${Number(s.train_size).toLocaleString()} 条样本训练（在线预测），Spark MLlib 为早期 ${Number(sp.train_size).toLocaleString()} 条小样本对比实验（离线训练演示）。两者不可直接横向比较精度，体现的是"单机 vs 分布式"两种技术路线。`
  }
  return ''
})

const formatNumber = (n) => {
  if (n === undefined || n === null) return '-'
  return Number(n).toLocaleString('zh-CN')
}

const formatMetric = (v) => {
  if (v === undefined || v === null) return '-'
  return Number(v).toFixed(4)
}

const initCharts = () => {
  if (importanceChartRef.value) importanceChart = echarts.init(importanceChartRef.value)
  if (compareChartRef.value) compareChart = echarts.init(compareChartRef.value)
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await getModelAnalysis()
    if (res.code === 200) {
      data.value = res.data
      nextTick(() => {
        renderImportanceChart()
        renderCompareChart()
      })
    }
  } catch (e) {
    console.error('加载模型分析数据失败', e)
  } finally {
    loading.value = false
  }
}

const renderImportanceChart = () => {
  if (!importanceChart || featureImportance.value.length === 0) return
  const items = [...featureImportance.value].reverse()
  importanceChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const p = params[0]
        return `${p.name}<br/>重要性：${(p.value * 100).toFixed(2)}%`
      }
    },
    grid: { left: '3%', right: '8%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'value',
      axisLabel: { color: '#6B7280', formatter: (v) => (v * 100).toFixed(0) + '%' },
      splitLine: { lineStyle: { color: '#F3F4F6' } }
    },
    yAxis: {
      type: 'category',
      data: items.map(i => i.feature),
      axisLabel: { color: '#4B5563' },
      axisLine: { lineStyle: { color: '#E5E7EB' } }
    },
    series: [{
      type: 'bar',
      data: items.map(i => i.importance),
      barMaxWidth: 18,
      itemStyle: {
        borderRadius: [0, 6, 6, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#5B8CFF' },
          { offset: 1, color: '#2D6BFF' }
        ])
      },
      label: {
        show: true,
        position: 'right',
        formatter: (p) => (p.value * 100).toFixed(1) + '%',
        color: '#4B5563',
        fontSize: 12
      }
    }]
  })
}

const renderCompareChart = () => {
  if (!compareChart) return
  const s = sklearn.value
  const sp = spark.value
  if (!s || !sp) return

  // 归一化对比：R² 越大越好，误差越小越好（用 1-RMSE/10 之类归一化）
  const metrics = [
    { name: 'R²', s: s.r2 ?? 0, sp: sp.r2 ?? 0, max: 1 },
    { name: 'RMSE', s: s.rmse ?? 0, sp: sp.rmse ?? 0, max: 10 },
    { name: 'MAE', s: s.mae ?? 0, sp: sp.mae ?? 0, max: 10 }
  ]

  compareChart.setOption({
    tooltip: {},
    legend: { data: ['Scikit-learn', 'Spark MLlib'], top: 0, textStyle: { color: '#4B5563' } },
    radar: {
      indicator: [
        { name: 'R²', max: 1 },
        { name: 'RMSE', max: 10 },
        { name: 'MAE', max: 10 }
      ],
      radius: '65%',
      axisName: { color: '#4B5563' },
      splitLine: { lineStyle: { color: '#E5E7EB' } },
      splitArea: { areaStyle: { color: ['#F9FAFB', '#F3F4F6'] } },
      axisLine: { lineStyle: { color: '#E5E7EB' } }
    },
    series: [{
      type: 'radar',
      data: [
        {
          name: 'Scikit-learn',
          value: [metrics[0].s, metrics[1].s, metrics[2].s],
          areaStyle: { color: 'rgba(45,107,255,0.2)' },
          lineStyle: { color: '#2D6BFF', width: 2 },
          itemStyle: { color: '#2D6BFF' }
        },
        {
          name: 'Spark MLlib',
          value: [metrics[0].sp, metrics[1].sp, metrics[2].sp],
          areaStyle: { color: 'rgba(34,197,94,0.15)' },
          lineStyle: { color: '#22C55E', width: 2 },
          itemStyle: { color: '#22C55E' }
        }
      ]
    }]
  })
}

const handleResize = () => {
  importanceChart?.resize()
  compareChart?.resize()
}

onMounted(async () => {
  await nextTick()
  initCharts()
  loadData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  importanceChart?.dispose()
  compareChart?.dispose()
})
</script>

<style scoped>
.metric-row { margin-bottom: 20px; }
.metric-row .el-col { margin-bottom: 12px; }
.stat-unit {
  font-size: 14px;
  color: var(--text-secondary);
  margin-left: 4px;
}
</style>

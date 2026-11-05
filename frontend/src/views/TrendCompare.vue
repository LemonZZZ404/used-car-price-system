<template>
  <div class="trend-compare-page">
    <!-- 车系选择 -->
    <div class="card">
      <div class="card-title">
        <span>车系走势对比</span>
        <el-tag size="small" effect="plain" type="primary">最多同时对比 4 个车系</el-tag>
      </div>
      <div class="picker-row">
        <el-select
          v-model="selected"
          multiple filterable remote clearable
          reserve-keyword
          :remote-method="searchSeries"
          :loading="seriesLoading"
          :multiple-limit="4"
          placeholder="搜索并选择车系（如：朗逸、轩逸、卡罗拉）"
          style="width: 520px; max-width: 100%"
          @change="handleSelect"
        >
          <el-option v-for="s in seriesOptions" :key="s.series" :label="`${s.series}（${s.brand} · ${s.count}辆）`" :value="s.series" />
        </el-select>
        <el-button type="primary" :icon="DataLine" :loading="loading" @click="loadCompare" :disabled="!selected.length">
          生成对比
        </el-button>
      </div>
      <div class="quick-row" v-if="hotSeries.length">
        <span class="quick-label">热门：</span>
        <el-tag v-for="s in hotSeries" :key="s.series" class="quick-tag" effect="plain"
                :type="selected.includes(s.series) ? 'primary' : 'info'"
                style="cursor:pointer"
                @click="toggleSeries(s.series)">
          {{ s.series }}
        </el-tag>
      </div>
    </div>

    <!-- 折线图 -->
    <div class="card mt20" v-if="compareData">
      <div class="card-title">
        <span>近 24 个月挂牌均价走势</span>
        <span class="sub-title">按上牌月份聚合 · 单位：万元</span>
      </div>
      <div ref="chartRef" class="main-chart"></div>
    </div>
    <div class="card mt20" v-else>
      <el-empty description="选择 1-4 个车系后生成走势对比" :image-size="90" />
    </div>

    <!-- 对比明细表 -->
    <div class="card mt20" v-if="compareData">
      <div class="card-title">对比明细</div>
      <el-table :data="compareData.series" stripe border>
        <el-table-column prop="series" label="车系" min-width="120">
          <template #default="{ row }">
            <span class="dot" :style="{ background: colorOf(row.series) }"></span>{{ row.series }}
          </template>
        </el-table-column>
        <el-table-column prop="count" label="在售样本(辆)" width="130" sortable />
        <el-table-column prop="avg_price" label="整体均价(万)" width="130" sortable />
        <el-table-column label="最新月均价(万)" width="140">
          <template #default="{ row }">{{ lastPrice(row) ?? '—' }}</template>
        </el-table-column>
        <el-table-column label="最新环比" width="110">
          <template #default="{ row }">
            <span v-if="row.mom_pct !== null" :class="row.mom_pct >= 0 ? 'up' : 'down'">
              {{ row.mom_pct >= 0 ? '↑' : '↓' }} {{ Math.abs(row.mom_pct) }}%
            </span>
            <span v-else>—</span>
          </template>
        </el-table-column>
        <el-table-column label="覆盖月份" width="100">
          <template #default="{ row }">{{ row.values.filter(v => v !== null).length }} / {{ compareData.months.length }}</template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { DataLine } from '@element-plus/icons-vue'
import echarts from '@/utils/echarts'
import { chartPalette, SERIES_COLORS, registerChart, unregisterChart } from '@/utils/theme'
import { getSeriesList, getTrendCompare } from '@/api'

const selected = ref([])
const seriesOptions = ref([])
const hotSeries = ref([])
const seriesLoading = ref(false)
const loading = ref(false)
const compareData = ref(null)

const chartRef = ref(null)
let chart = null

const lastPrice = (row) => {
  const v = [...row.values].reverse().find(x => x !== null)
  return v ?? null
}

const searchSeries = async (q) => {
  seriesLoading.value = true
  try {
    const res = await getSeriesList({ q, limit: 30 })
    seriesOptions.value = res.code === 200 ? (res.data?.items || []) : []
  } catch (e) {
    seriesOptions.value = []
  } finally {
    seriesLoading.value = false
  }
}

const toggleSeries = (name) => {
  const i = selected.value.indexOf(name)
  if (i >= 0) selected.value.splice(i, 1)
  else {
    if (selected.value.length >= 4) { ElMessage.warning('最多同时对比 4 个车系'); return }
    selected.value.push(name)
  }
  loadCompare()
}

const handleSelect = () => { if (selected.value.length) loadCompare() }

const loadCompare = async () => {
  if (!selected.value.length) return
  loading.value = true
  try {
    const res = await getTrendCompare({ series: selected.value })
    if (res.code === 200) {
      compareData.value = res.data
      await nextTick()
      renderChart()
    } else {
      ElMessage.error(res.message || '获取走势失败')
    }
  } finally {
    loading.value = false
  }
}

const colorOf = (name) => {
  if (!compareData.value) return SERIES_COLORS[0][0]
  const idx = compareData.value.series.findIndex(s => s.series === name)
  return SERIES_COLORS[idx % SERIES_COLORS.length][0]
}

const renderChart = () => {
  if (!chartRef.value || !compareData.value) return
  if (!chart) chart = echarts.init(chartRef.value)
  const p = chartPalette()
  const legend = compareData.value.series.map(s => s.series)
  chart.setOption({
    legend: { data: legend, top: 0, textStyle: { color: p.text } },
    grid: { left: 55, right: 24, top: 36, bottom: 60 },
    tooltip: { trigger: 'axis', valueFormatter: v => v == null ? '—' : v + ' 万' },
    dataZoom: [{ type: 'slider', height: 20, bottom: 8 }],
    xAxis: {
      type: 'category', data: compareData.value.months, boundaryGap: false,
      axisLine: { lineStyle: { color: p.axisLine } }, axisLabel: { color: p.text }
    },
    yAxis: {
      type: 'value', name: '均价(万)', nameTextStyle: { color: p.text },
      scale: true,
      splitLine: { lineStyle: { color: p.splitLine } }, axisLabel: { color: p.text }
    },
    series: compareData.value.series.map((s, i) => ({
      name: s.series,
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      connectNulls: true,
      data: s.values,
      lineStyle: { width: 2.5, color: SERIES_COLORS[i % SERIES_COLORS.length][0] },
      itemStyle: { color: SERIES_COLORS[i % SERIES_COLORS.length][0] },
    }))
  }, true)
  registerChart(chart, renderChart)
}

onMounted(async () => {
  try {
    const res = await getSeriesList({ limit: 8 })
    if (res.code === 200) hotSeries.value = res.data?.items || []
  } catch (e) { hotSeries.value = [] }
  seriesOptions.value = hotSeries.value
})
onUnmounted(() => {
  if (chart) { unregisterChart(chart); chart.dispose() }
})
</script>

<style scoped>
.picker-row { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.quick-row { margin-top: 14px; display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
.quick-label { font-size: 13px; color: #6B7280; }
.quick-tag { cursor: pointer; }
.mt20 { margin-top: 20px; }
.sub-title { font-size: 12px; color: #9CA3AF; font-weight: 400; }
.main-chart { height: 420px; }
.dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 8px; }
.up { color: #22C55E; font-weight: 600; }
.down { color: #EF4444; font-weight: 600; }
</style>

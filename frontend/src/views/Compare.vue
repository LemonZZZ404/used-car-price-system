<template>
  <div class="compare-page">
    <!-- Hero -->
    <div class="hero-section">
      <div class="hero-badge">
        <el-icon><ScaleToOriginal /></el-icon>
        <span>多车对比</span>
      </div>
      <h1 class="hero-title"><span class="gradient-text">多车对比评估</span></h1>
      <p class="hero-sub">同时评估 2-3 辆车 · 并排展示各项指标</p>
    </div>

    <!-- 对比表单区 -->
    <el-row :gutter="16">
      <el-col v-for="(car, idx) in carForms" :key="idx" :xs="24" :md="8">
        <div class="card car-form-card" :class="'fc-' + idx">
          <div class="car-form-header">
            <div class="cf-title">
              <span class="cf-badge" :class="'b' + idx">车辆 {{ idx + 1 }}</span>
            </div>
            <el-button v-if="carForms.length > 2" size="small" text type="danger" :icon="Delete" @click="removeCar(idx)" />
          </div>

          <el-form :model="car" label-width="76px" size="default">
            <el-form-item label="品牌">
              <el-select v-model="car.brand" filterable style="width:100%">
                <el-option v-for="b in brands" :key="b" :label="b" :value="b" />
              </el-select>
            </el-form-item>
            <el-row :gutter="8">
              <el-col :span="12">
                <el-form-item label="车龄">
                  <el-input-number v-model="car.age" :min="0" :max="30" controls-position="right" style="width:100%" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="里程">
                  <el-input-number v-model="car.mileage" :min="0" :max="50" :precision="1" controls-position="right" style="width:100%" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="新车价">
              <el-input-number v-model="car.original_price" :min="0" :max="500" :precision="1" controls-position="right" style="width:100%" />
            </el-form-item>
            <el-row :gutter="8">
              <el-col :span="12">
                <el-form-item label="变速箱">
                  <el-select v-model="car.gearbox" style="width:100%">
                    <el-option label="自动" value="自动" /><el-option label="手动" value="手动" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="排量">
                  <el-select v-model="car.displacement" style="width:100%">
                    <el-option v-for="d in displacements" :key="d" :label="d" :value="d" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="城市">
              <el-select v-model="car.city" filterable style="width:100%">
                <el-option v-for="c in cities" :key="c" :label="c" :value="c" />
              </el-select>
            </el-form-item>
          </el-form>
        </div>
      </el-col>

      <!-- 添加车辆卡片 -->
      <el-col :xs="24" :md="8" v-if="carForms.length < 3">
        <div class="card add-car-card" @click="addCar">
          <el-icon :size="40"><CirclePlus /></el-icon>
          <span>添加第 {{ carForms.length + 1 }} 辆车</span>
        </div>
      </el-col>
    </el-row>

    <div class="compare-action">
      <el-button type="primary" size="large" :loading="loading" :icon="MagicStick" @click="handleCompare" class="compare-btn">
        {{ loading ? '对比分析中...' : '开始对比评估' }}
      </el-button>
    </div>

    <!-- 对比结果 -->
    <template v-if="results.length">
      <!-- 并排指标卡片 -->
      <el-row :gutter="16" class="result-row">
        <el-col v-for="(r, idx) in results" :key="idx" :xs="24" :md="8">
          <div class="card result-card" :class="'rc-' + idx">
            <div class="rc-header">
              <span class="rc-badge" :class="'b' + idx">车辆 {{ idx + 1 }}</span>
              <span class="rc-brand">{{ r.input_params.brand }}</span>
            </div>
            <div class="rc-price">
              <span class="rc-num">{{ r.predicted_price }}</span>
              <span class="rc-unit">万</span>
            </div>
            <div class="rc-range">{{ r.price_range.min }} ~ {{ r.price_range.max }} 万</div>
            <div class="rc-metrics">
              <div class="rcm-item">
                <span class="rcm-label">置信度</span>
                <el-progress :percentage="Math.round(r.confidence * 100)" :stroke-width="8" :color="confColors[idx]" :show-text="false" />
                <span class="rcm-val">{{ Math.round(r.confidence * 100) }}%</span>
              </div>
              <div class="rcm-item">
                <span class="rcm-label">保值率</span>
                <el-progress :percentage="retentionOf(r)" :stroke-width="8" :color="confColors[idx]" :show-text="false" />
                <span class="rcm-val">{{ retentionOf(r) }}%</span>
              </div>
            </div>
            <div class="rc-tags">
              <el-tag v-if="idx === bestPriceIdx" size="small" type="success" effect="dark" round>最划算</el-tag>
              <el-tag v-if="idx === bestRetentionIdx" size="small" type="warning" effect="dark" round>最保值</el-tag>
              <el-tag size="small" effect="plain" round>{{ modelShortName(r.model_type) }}</el-tag>
            </div>
          </div>
        </el-col>
      </el-row>

      <!-- 对比雷达图 -->
      <div class="card radar-card">
        <div class="card-title">
          <span>综合指标雷达</span>
          <el-tag size="small" type="primary" effect="light">五维对比</el-tag>
        </div>
        <div ref="radarRef" class="radar-chart"></div>
      </div>

      <!-- 详细参数表 -->
      <div class="card">
        <div class="card-title"><span>详细参数对比</span></div>
        <el-table :data="compareTable" border stripe>
          <el-table-column prop="label" label="指标" width="140" fixed />
          <el-table-column v-for="(r, idx) in results" :key="idx" :label="'车辆 ' + (idx + 1) + ' · ' + r.input_params.brand" align="center">
            <template #default="{ row }">
              <span :class="{ 'cell-highlight': row.highlight === idx }">{{ row.values[idx] }}</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </template>

    <!-- 空状态 -->
    <div class="card placeholder-card" v-else-if="!loading">
      <div class="empty-illustration">
        <el-icon :size="56"><ScaleToOriginal /></el-icon>
        <div class="empty-title">填写车辆信息后开始对比</div>
        <div class="empty-desc">最多支持 3 辆车同时评估，AI 将并排展示各项指标</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { MagicStick, CirclePlus, Delete, ScaleToOriginal } from '@element-plus/icons-vue'
import echarts from '@/utils/echarts'
import { predictPrice, getCarBrands, getCarCities } from '@/api'
import { chartPalette, SERIES_COLORS, registerChart, unregisterChart } from '@/utils/theme'

const loading = ref(false)
const results = ref([])
const brands = ref([])
const cities = ref([])
const radarRef = ref(null)
let radarChart = null

const displacements = ['1.0L', '1.2T', '1.4T', '1.5L', '1.5T', '1.6L', '1.8L', '2.0L', '2.0T', '2.5L', '3.0T', '纯电']
const confColors = ['#2D6BFF', '#22C55E', '#F59E0B']

const defaultCar = () => ({
  brand: '大众', age: 3, mileage: 5.0, original_price: 16.0,
  gearbox: '自动', displacement: '1.4T', fuel_type: '汽油', city: '北京', model_type: 'sklearn'
})

const carForms = reactive([defaultCar(), { ...defaultCar(), brand: '丰田', original_price: 18 }])

const addCar = () => { if (carForms.length < 3) carForms.push({ ...defaultCar(), brand: '本田' }) }
const removeCar = (idx) => { if (carForms.length > 2) carForms.splice(idx, 1) }

const retentionOf = (r) => {
  const op = r.input_params?.original_price
  if (!op) return 0
  return Math.round(r.predicted_price / op * 100)
}

const modelShortName = (t) => ({ sklearn: '随机森林', lightgbm: 'LightGBM', xgboost: 'XGBoost', spark_mllib: 'Spark' }[t] || t)

const bestPriceIdx = computed(() => {
  if (!results.value.length) return -1
  let idx = 0
  results.value.forEach((r, i) => { if (r.predicted_price < results.value[idx].predicted_price) idx = i })
  return idx
})

const bestRetentionIdx = computed(() => {
  if (!results.value.length) return -1
  let idx = 0
  results.value.forEach((r, i) => { if (retentionOf(r) > retentionOf(results.value[idx])) idx = i })
  return idx
})

const compareTable = computed(() => {
  if (!results.value.length) return []
  const rows = [
    { label: '预测价格（万）', key: 'predicted_price', fmt: v => v, best: 'min' },
    { label: '价格区间（万）', key: '_range', fmt: (_, r) => `${r.price_range.min} ~ ${r.price_range.max}` },
    { label: '置信度', key: 'confidence', fmt: v => Math.round(v * 100) + '%', best: 'max' },
    { label: '保值率', key: '_retention', fmt: (_, r) => retentionOf(r) + '%', best: 'max' },
    { label: '品牌', key: '_brand', fmt: (_, r) => r.input_params.brand },
    { label: '车龄（年）', key: '_age', fmt: (_, r) => r.input_params.age },
    { label: '里程（万 km）', key: '_mileage', fmt: (_, r) => r.input_params.mileage },
    { label: '新车价（万）', key: '_op', fmt: (_, r) => r.input_params.original_price },
    { label: '变速箱', key: '_gearbox', fmt: (_, r) => r.input_params.gearbox },
    { label: '排量', key: '_disp', fmt: (_, r) => r.input_params.displacement },
    { label: '城市', key: '_city', fmt: (_, r) => r.input_params.city },
  ]
  return rows.map(row => {
    const values = results.value.map(r => row.fmt(row.key === '_retention' ? null : r[row.key], r))
    let highlight = -1
    if (row.best && results.value.length > 1) {
      const nums = results.value.map(r => row.key === '_retention' ? retentionOf(r) : Number(r[row.key]))
      highlight = row.best === 'min' ? nums.indexOf(Math.min(...nums)) : nums.indexOf(Math.max(...nums))
    }
    return { label: row.label, values, highlight }
  })
})

const handleCompare = async () => {
  loading.value = true
  results.value = []
  try {
    const promises = carForms.map(car => predictPrice({ ...car }))
    const resList = await Promise.all(promises)
    const ok = resList.filter(r => r.code === 200)
    if (!ok.length) { ElMessage.error('所有预测都失败了'); return }
    results.value = ok.map(r => r.data)
    ElMessage.success('对比完成')
    await nextTick()
    renderRadar()
  } catch (e) {
    ElMessage.error('对比请求失败')
  } finally {
    loading.value = false
  }
}

const renderRadar = () => {
  if (!radarRef.value || !results.value.length) return
  if (!radarChart) radarChart = echarts.init(radarRef.value)
  const p = chartPalette()

  // 归一化：价格取反向（越低越好），其余正向
  const maxPrice = Math.max(...results.value.map(r => r.predicted_price), 1)
  const maxOp = Math.max(...results.value.map(r => r.input_params.original_price || 1), 1)

  const data = results.value.map((r, i) => ({
    name: `车辆${i + 1} · ${r.input_params.brand}`,
    value: [
      Math.round(r.confidence * 100),                            // 置信度
      retentionOf(r),                                            // 保值率
      Math.round((1 - r.predicted_price / maxPrice) * 50 + 50),  // 性价比（反向）
      Math.round((r.input_params.original_price / maxOp) * 100), // 原始价值
      Math.max(0, 100 - r.input_params.age * 8),                 // 车况（车龄反向）
    ],
    itemStyle: { color: SERIES_COLORS[i][0] },
    areaStyle: { opacity: 0.15 }
  }))

  radarChart.setOption({
    tooltip: { backgroundColor: p.tooltipBg, borderColor: p.tooltipBorder, textStyle: { color: p.tooltipText } },
    legend: { bottom: 0, textStyle: { color: p.textSecondary }, icon: 'circle' },
    radar: {
      indicator: [
        { name: '置信度', max: 100 },
        { name: '保值率', max: 100 },
        { name: '性价比', max: 100 },
        { name: '原始价值', max: 100 },
        { name: '车况', max: 100 },
      ],
      axisName: { color: p.text, fontSize: 12 },
      splitLine: { lineStyle: { color: p.splitLine } },
      splitArea: { areaStyle: { color: [p.dark ? '#1A1D28' : '#FAFBFF', p.dark ? '#1E2233' : '#F4F6FA'] } },
    },
    series: [{ type: 'radar', data, symbolSize: 5 }]
  })
  radarChart.resize()
  registerChart(radarChart, renderRadar)
}

onMounted(async () => {
  try { const res = await getCarBrands(); brands.value = res.brands || [] } catch (e) { brands.value = ['大众', '丰田', '本田'] }
  try { const res = await getCarCities(); cities.value = res.cities || [] } catch (e) { cities.value = ['北京', '上海'] }
})

onUnmounted(() => { if (radarChart) { unregisterChart(radarChart); radarChart.dispose() } })
</script>

<style scoped>
.compare-page { padding: 0; }

.hero-section { text-align: center; margin-bottom: 24px; padding: 20px 0 8px; }
.hero-badge {
  display: inline-flex; align-items: center; gap: 6px; padding: 5px 14px;
  border-radius: 20px; background: var(--primary-lighter); color: var(--primary);
  font-size: 12px; font-weight: 600; margin-bottom: 10px;
}
.hero-title { font-size: 26px; font-weight: 800; margin-bottom: 6px; }
.hero-sub { font-size: 13px; color: var(--text-secondary); }

/* 表单卡片 */
.car-form-card { position: relative; overflow: visible; }
.car-form-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
  border-radius: var(--radius-md) var(--radius-md) 0 0;
}
.car-form-card.fc-0::before { background: linear-gradient(90deg, #2D6BFF, #5B8CFF); }
.car-form-card.fc-1::before { background: linear-gradient(90deg, #22C55E, #4ADE80); }
.car-form-card.fc-2::before { background: linear-gradient(90deg, #F59E0B, #FBBF24); }

.car-form-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.cf-badge { padding: 4px 12px; border-radius: 8px; font-size: 12px; font-weight: 700; color: #fff; }
.cf-badge.b0 { background: linear-gradient(135deg, #2D6BFF, #5B8CFF); }
.cf-badge.b1 { background: linear-gradient(135deg, #22C55E, #4ADE80); }
.cf-badge.b2 { background: linear-gradient(135deg, #F59E0B, #FBBF24); }

.add-car-card {
  min-height: 300px; display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 12px; cursor: pointer; border: 2px dashed var(--border-color); color: var(--text-secondary);
  transition: all var(--transition-base); font-size: 14px; font-weight: 500;
}
.add-car-card:hover { border-color: var(--primary); color: var(--primary); background: var(--primary-lighter); }

.compare-action { text-align: center; margin: 20px 0; }
.compare-btn {
  height: 46px; padding: 0 40px; font-size: 15px; font-weight: 600; letter-spacing: 2px;
  border-radius: 12px; background: var(--gradient-primary); border: none;
  box-shadow: 0 6px 20px rgba(45, 107, 255, 0.35);
}
.compare-btn:hover { transform: translateY(-2px); box-shadow: 0 10px 28px rgba(45, 107, 255, 0.45); }

/* 结果卡片 */
.result-row { margin-bottom: 20px; }
.result-card { text-align: center; padding: 24px 20px; animation: fadeInUp 0.4s ease; }
.result-card.rc-0 { animation-delay: 0s; } .result-card.rc-1 { animation-delay: 0.1s; } .result-card.rc-2 { animation-delay: 0.2s; }

.rc-header { display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 12px; }
.rc-badge { padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; color: #fff; }
.rc-badge.b0 { background: linear-gradient(135deg, #2D6BFF, #5B8CFF); }
.rc-badge.b1 { background: linear-gradient(135deg, #22C55E, #4ADE80); }
.rc-badge.b2 { background: linear-gradient(135deg, #F59E0B, #FBBF24); }
.rc-brand { font-size: 15px; font-weight: 700; color: var(--text-primary); }

.rc-price { margin-bottom: 4px; }
.rc-num {
  font-size: 42px; font-weight: 800; line-height: 1.1;
  background: var(--gradient-primary); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.rc-unit { font-size: 14px; color: var(--text-secondary); margin-left: 2px; }
.rc-range { font-size: 12px; color: var(--text-secondary); margin-bottom: 14px; }

.rc-metrics { display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px; }
.rcm-item { display: flex; align-items: center; gap: 8px; }
.rcm-label { font-size: 12px; color: var(--text-secondary); width: 44px; text-align: right; flex-shrink: 0; }
.rcm-item :deep(.el-progress) { flex: 1; }
.rcm-val { font-size: 12px; font-weight: 700; color: var(--text-primary); width: 34px; flex-shrink: 0; }

.rc-tags { display: flex; justify-content: center; gap: 6px; flex-wrap: wrap; }

.radar-card { margin-bottom: 20px; }
.radar-chart { width: 100%; height: 340px; }

.cell-highlight { color: var(--primary); font-weight: 700; }

.placeholder-card { min-height: 280px; display: flex; align-items: center; justify-content: center; margin-top: 20px; }
.empty-illustration { text-align: center; padding: 30px; color: var(--text-secondary); }
.empty-illustration .el-icon { color: var(--primary); margin-bottom: 12px; }
.empty-title { font-size: 16px; font-weight: 700; color: var(--text-primary); margin-bottom: 6px; }
.empty-desc { font-size: 12px; }
</style>

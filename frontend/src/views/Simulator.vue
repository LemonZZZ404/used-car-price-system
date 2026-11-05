<template>
  <div class="simulator-page">
    <el-row :gutter="20">
      <!-- 左侧：参数调节 -->
      <el-col :xs="24" :md="13">
        <div class="card">
          <div class="card-title">
            <span>参数调节</span>
            <el-tag size="small" effect="plain" type="success" v-if="autoRunning">实时计算中</el-tag>
          </div>

          <div class="slider-group">
            <div class="slider-head">
              <span class="slider-name">车龄</span>
              <span class="slider-val">{{ form.age }} 年</span>
            </div>
            <el-slider v-model="form.age" :min="0" :max="15" :step="1" show-stops :marks="{ 0: '新车', 5: '5年', 10: '10年', 15: '15年' }" />
          </div>

          <div class="slider-group">
            <div class="slider-head">
              <span class="slider-name">里程</span>
              <span class="slider-val">{{ form.mileage }} 万公里</span>
            </div>
            <el-slider v-model="form.mileage" :min="0" :max="30" :step="0.5" :marks="{ 0: '0', 10: '10', 20: '20', 30: '30' }" />
          </div>

          <div class="slider-group">
            <div class="slider-head">
              <span class="slider-name">新车指导价</span>
              <span class="slider-val">{{ form.original_price }} 万</span>
            </div>
            <el-slider v-model="form.original_price" :min="2" :max="100" :step="1" :marks="{ 2: '2万', 30: '30万', 60: '60万', 100: '100万' }" />
          </div>

          <el-form label-width="80px" class="mt10" size="default">
            <el-row :gutter="14">
              <el-col :span="12">
                <el-form-item label="品牌">
                  <el-select v-model="form.brand" filterable style="width:100%">
                    <el-option v-for="b in brands" :key="b" :label="b" :value="b" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="城市">
                  <el-select v-model="form.city" filterable style="width:100%">
                    <el-option v-for="c in cities" :key="c" :label="c" :value="c" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="排量">
                  <el-select v-model="form.displacement" style="width:100%">
                    <el-option v-for="d in displacements" :key="d" :label="d" :value="d" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="燃油">
                  <el-select v-model="form.fuel_type" style="width:100%">
                    <el-option v-for="f in fuelTypes" :key="f" :label="f" :value="f" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="变速箱">
              <el-radio-group v-model="form.gearbox">
                <el-radio-button value="自动">自动</el-radio-button>
                <el-radio-button value="手动">手动</el-radio-button>
              </el-radio-group>
            </el-form-item>
          </el-form>

          <div class="sim-actions">
            <el-button type="primary" plain :icon="Lightning" @click="runSensitivity" :loading="sensLoading">
              里程敏感性分析
            </el-button>
            <span class="action-tip">调整滑杆后估价自动实时更新</span>
          </div>
        </div>
      </el-col>

      <!-- 右侧：实时结果 -->
      <el-col :xs="24" :md="11">
        <div class="card result-card">
          <div class="card-title">实时估价</div>
          <template v-if="result">
            <div class="res-price">
              <CountUp :end-value="result.predicted_price" :decimals="2" :duration="600" easing="easeOutCubic" class="res-num" />
              <span class="res-unit">万元</span>
            </div>
            <div class="res-range-bar">
              <div class="res-range-fill" :style="rangeFillStyle"></div>
              <div class="res-range-dot" :style="rangeDotStyle"></div>
            </div>
            <div class="res-range-label">
              <span>{{ result.price_range?.min }} 万</span>
              <span>{{ result.price_range?.max }} 万</span>
            </div>
            <div class="res-stats">
              <div class="res-stat">
                <div class="rs-val">{{ Math.round((result.confidence || 0) * 100) }}%</div>
                <div class="rs-label">模型置信度</div>
              </div>
              <div class="res-stat">
                <div class="rs-val">{{ retentionPct }}%</div>
                <div class="rs-label">保值率</div>
              </div>
              <div class="res-stat">
                <div class="rs-val">{{ perYearLoss }}</div>
                <div class="rs-label">年均折旧(万)</div>
              </div>
            </div>
            <el-alert v-if="result.confidence_source === 'fallback_rule'" type="warning" :closable="false"
              title="模型离线，当前为规则兜底估价" class="mt10" />
          </template>
          <el-skeleton v-else-if="loading" :rows="4" animated class="res-skeleton" />
          <el-empty v-else description="调整左侧参数即可实时估价" :image-size="80" />
        </div>

        <!-- 里程敏感性曲线 -->
        <div class="card mt20" v-if="sensData">
          <div class="card-title">
            <span>里程敏感性（{{ form.brand }} · {{ form.age }} 年车）</span>
            <el-tag size="small" effect="plain" type="primary">固定其他参数</el-tag>
          </div>
          <div ref="sensChartRef" class="sens-chart"></div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lightning } from '@element-plus/icons-vue'
import echarts from '@/utils/echarts'
import { chartPalette, SERIES_COLORS, registerChart, unregisterChart } from '@/utils/theme'
import CountUp from '@/components/CountUp.vue'
import { predictPrice, getCarBrands, getCarCities } from '@/api'

const route = useRoute()

const loading = ref(false)
const autoRunning = ref(false)
const result = ref(null)
const sensData = ref(null)
const sensLoading = ref(false)
const brands = ref([])
const cities = ref([])

const sensChartRef = ref(null)
let sensChart = null
let debounceTimer = null

const displacements = ['1.0L', '1.2T', '1.4T', '1.5L', '1.5T', '1.6L', '1.8L', '2.0L', '2.0T', '2.5L', '3.0T', '纯电']
const fuelTypes = ['汽油', '柴油', '纯电动', '混合动力', '插电混动']

const form = reactive({
  brand: '大众', age: 3, mileage: 5, original_price: 16,
  gearbox: '自动', displacement: '1.4T', fuel_type: '汽油', city: '北京',
})

// 从车辆详情页带参进入
if (route.query.brand) form.brand = String(route.query.brand)
if (route.query.age !== undefined) form.age = Number(route.query.age) || 0
if (route.query.mileage !== undefined) form.mileage = Number(route.query.mileage) || 0
if (route.query.original_price !== undefined) form.original_price = Number(route.query.original_price) || 16

const retentionPct = computed(() => {
  if (!result.value?.predicted_price || !form.original_price) return '—'
  return Math.round(result.value.predicted_price / form.original_price * 100)
})

const perYearLoss = computed(() => {
  if (!result.value?.predicted_price || !form.original_price || !form.age) return '—'
  return ((form.original_price - result.value.predicted_price) / form.age).toFixed(2)
})

const rangeFillStyle = computed(() => {
  if (!result.value?.price_range) return {}
  const { min, max } = result.value.price_range
  const pct = Math.min(100, Math.max(0, ((result.value.predicted_price - min) / (max - min)) * 100))
  return { width: pct + '%' }
})
const rangeDotStyle = computed(() => {
  if (!result.value?.price_range) return {}
  const { min, max } = result.value.price_range
  const pct = Math.min(100, Math.max(0, ((result.value.predicted_price - min) / (max - min)) * 100))
  return { left: `calc(${pct}% - 7px)` }
})

const doPredict = async () => {
  loading.value = true
  autoRunning.value = true
  try {
    const res = await predictPrice({ ...form, model_type: 'sklearn' })
    if (res.code === 200) result.value = res.data
    else ElMessage.error(res.message || '预测失败')
  } catch (e) {
    // 静默：滑杆连续调整时不弹错误刷屏，仅最后一次失败提示
  } finally {
    loading.value = false
    setTimeout(() => { autoRunning.value = false }, 300)
  }
}

watch(form, () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(doPredict, 450)
})

const runSensitivity = async () => {
  sensLoading.value = true
  const points = [1, 4, 8, 12, 16, 20, 24, 28, 30]
  try {
    const tasks = points.map(m =>
      predictPrice({ ...form, mileage: m, model_type: 'sklearn' })
        .then(res => (res.code === 200 ? res.data.predicted_price : null))
        .catch(() => null)
    )
    const values = await Promise.all(tasks)
    sensData.value = { points, values }
    await nextTick()
    renderSensChart()
  } finally {
    sensLoading.value = false
  }
}

const renderSensChart = () => {
  if (!sensChartRef.value || !sensData.value) return
  if (!sensChart) sensChart = echarts.init(sensChartRef.value)
  const p = chartPalette()
  const { points, values } = sensData.value
  sensChart.setOption({
    grid: { left: 50, right: 20, top: 30, bottom: 32 },
    tooltip: { trigger: 'axis', valueFormatter: v => v == null ? '—' : v + ' 万' },
    xAxis: {
      type: 'category', data: points.map(m => m + '万km'),
      axisLine: { lineStyle: { color: p.axisLine } }, axisLabel: { color: p.text }
    },
    yAxis: {
      type: 'value', name: '估价(万)', nameTextStyle: { color: p.text },
      splitLine: { lineStyle: { color: p.splitLine } }, axisLabel: { color: p.text }
    },
    series: [{
      type: 'line', smooth: true, symbol: 'circle', symbolSize: 8,
      data: values,
      connectNulls: true,
      lineStyle: { width: 3, color: SERIES_COLORS[0][0] },
      itemStyle: { color: SERIES_COLORS[0][0] },
      ...(points.includes(form.mileage) ? {
        markLine: {
          silent: true, symbol: 'none',
          lineStyle: { type: 'dashed', color: '#EF4444' },
          label: { formatter: '当前 {c} 万', color: '#EF4444' },
          data: [{ xAxis: form.mileage + '万km' }]
        }
      } : {})
    }]
  })
  registerChart(sensChart, renderSensChart)
}

const loadOptions = async () => {
  try { const r = await getCarBrands(); brands.value = r.brands || [] }
  catch (e) { brands.value = ['大众', '丰田', '本田', '日产', '别克', '奥迪', '宝马', '奔驰', '比亚迪', '特斯拉'] }
  try { const r = await getCarCities(); cities.value = r.cities || [] }
  catch (e) { cities.value = ['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '西安', '南京', '重庆'] }
}

onMounted(() => { loadOptions(); doPredict() })
onUnmounted(() => {
  clearTimeout(debounceTimer)
  if (sensChart) { unregisterChart(sensChart); sensChart.dispose() }
})
</script>

<style scoped>
.slider-group { margin: 26px 0 6px; }
.slider-head { display: flex; justify-content: space-between; margin-bottom: 6px; }
.slider-name { font-size: 14px; font-weight: 600; }
.slider-val { color: #2D6BFF; font-weight: 700; font-size: 15px; }
.mt10 { margin-top: 10px; }
.mt20 { margin-top: 20px; }

.sim-actions { margin-top: 18px; display: flex; align-items: center; gap: 12px; }
.action-tip { font-size: 12px; color: #9CA3AF; }

.result-card { min-height: 320px; }
.res-price { text-align: center; margin: 24px 0 10px; }
.res-num { font-size: 52px; font-weight: 800; color: #EF4444; }
.res-unit { font-size: 15px; color: #EF4444; margin-left: 6px; }
.res-range-bar { position: relative; height: 8px; margin: 18px 10px 6px; border-radius: 4px; background: linear-gradient(90deg, #22C55E, #F59E0B); }
.res-range-fill { display: none; }
.res-range-dot {
  position: absolute; top: -4px; width: 14px; height: 14px; border-radius: 50%;
  background: #fff; border: 3px solid #EF4444; box-shadow: 0 1px 4px rgba(0,0,0,0.25);
}
.res-range-label { display: flex; justify-content: space-between; font-size: 12px; color: #9CA3AF; padding: 0 10px; }
.res-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 22px; }
.res-stat { text-align: center; padding: 14px 6px; border-radius: 10px; background: rgba(45,107,255,0.05); }
.rs-val { font-size: 22px; font-weight: 700; color: #2D6BFF; }
.rs-label { font-size: 12px; color: #6B7280; margin-top: 4px; }
.res-skeleton { padding: 30px 20px; }
.sens-chart { height: 260px; }
</style>

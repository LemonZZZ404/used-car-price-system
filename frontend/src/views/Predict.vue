<template>
  <div class="predict-page-v2">
    <el-row :gutter="20">
      <!-- 左侧：预测表单 -->
      <el-col :xs="24" :sm="24" :md="9" :lg="8">
        <div class="card form-card">
          <div class="card-title">
            <span>车辆信息录入</span>
            <el-tag size="small" type="primary" effect="plain">AI 估价</el-tag>
          </div>

          <el-form :model="form" :rules="rules" ref="formRef" label-width="90px" size="default" class="predict-form">
            <el-form-item label="品牌" prop="brand">
              <el-select v-model="form.brand" placeholder="请选择品牌" filterable style="width:100%">
                <el-option v-for="b in brands" :key="b" :label="b" :value="b" />
              </el-select>
            </el-form-item>

            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="车龄" prop="age">
                  <el-input-number v-model="form.age" :min="0" :max="30" :step="1" controls-position="right" style="width:100%" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="里程" prop="mileage">
                  <el-input-number v-model="form.mileage" :min="0" :max="50" :step="0.5" :precision="1" controls-position="right" style="width:100%" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="新车价" prop="original_price">
              <el-input-number v-model="form.original_price" :min="0" :max="500" :step="1" :precision="2" controls-position="right" style="width:100%" />
              <span class="unit-suffix">万元</span>
            </el-form-item>

            <el-form-item label="变速箱" prop="gearbox">
              <el-radio-group v-model="form.gearbox" class="pill-group">
                <el-radio-button value="自动">自动</el-radio-button>
                <el-radio-button value="手动">手动</el-radio-button>
              </el-radio-group>
            </el-form-item>

            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="排量" prop="displacement">
                  <el-select v-model="form.displacement" placeholder="请选择" style="width:100%">
                    <el-option v-for="d in displacements" :key="d" :label="d" :value="d" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="燃油" prop="fuel_type">
                  <el-select v-model="form.fuel_type" placeholder="请选择" style="width:100%">
                    <el-option v-for="f in fuelTypes" :key="f" :label="f" :value="f" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="城市" prop="city">
              <el-select v-model="form.city" placeholder="请选择城市" filterable style="width:100%">
                <el-option v-for="c in cities" :key="c" :label="c" :value="c" />
              </el-select>
            </el-form-item>

            <el-form-item label="预测模型">
              <div class="model-selector">
                <div v-for="m in modelOptions" :key="m.value"
                     class="model-card"
                     :class="{ active: form.model_type === m.value }"
                     @click="form.model_type = m.value">
                  <div class="mc-icon" :style="{ background: m.gradient }">
                    <el-icon><component :is="iconMap[m.icon]" /></el-icon>
                  </div>
                  <div class="mc-info">
                    <div class="mc-name">{{ m.label }}</div>
                    <div class="mc-desc">{{ m.desc }}</div>
                  </div>
                  <div class="mc-check" v-if="form.model_type === m.value">
                    <el-icon><CircleCheckFilled /></el-icon>
                  </div>
                </div>
              </div>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" :icon="MagicStick" :loading="loading" @click="handlePredict" class="predict-btn">
                {{ loading ? '正在分析...' : '开始智能估价' }}
              </el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-col>

      <!-- 右侧：预测结果 -->
      <el-col :xs="24" :sm="24" :md="15" :lg="16">
        <!-- 结果主卡片 -->
        <div class="card result-hero-card" v-if="result" ref="reportRef">
          <div class="result-hero">
            <div class="result-left">
              <div class="result-badge">
                <el-icon><MagicStick /></el-icon>
                <span>AI 智能估价</span>
                <el-tag size="small" effect="dark" type="success" round class="conf-tag">
                  置信度 {{ Math.round(result.confidence * 100) }}%
                </el-tag>
              </div>
              <div class="result-title">{{ form.brand }} · 估价结果</div>

              <!-- 大数字 + 仪表盘 并排 -->
              <div class="hero-main">
                <div class="hero-price-block">
                  <div class="price-label">预测价格</div>
                  <div class="price-main">
                    <CountUp :end-value="result.predicted_price" :decimals="2" :duration="1800" easing="easeOutExpo" class="price-value" />
                    <span class="price-unit">万元</span>
                  </div>
                  <div class="price-sub" v-if="result.input_params?.original_price">
                    保值率 <b :class="retentionClass">{{ retentionRate }}%</b>
                    · 新车价 {{ result.input_params.original_price }} 万
                  </div>
                  <div class="hero-actions">
                    <el-button size="small" type="primary" plain round :icon="Download" :loading="pdfLoading" @click="downloadReport">
                      下载评估报告
                    </el-button>
                  </div>
                </div>
                <div ref="gaugeChartRef" class="gauge-chart"></div>
              </div>

              <!-- 价格区间 -->
              <div class="result-range">
                <el-tag type="info" effect="light" size="large" round class="range-tag">
                  <el-icon><Bottom /></el-icon>{{ result.price_range?.min }} 万
                </el-tag>
                <div class="range-bar">
                  <div class="range-fill" :style="rangeFillStyle"></div>
                  <div class="range-pointer" :style="rangePointerStyle"></div>
                </div>
                <el-tag type="info" effect="light" size="large" round class="range-tag">
                  <el-icon><Top /></el-icon>{{ result.price_range?.max }} 万
                </el-tag>
              </div>
            </div>
          </div>
        </div>

        <!-- 骨架屏 / 空状态 -->
        <div class="card placeholder-card" v-else-if="loading">
          <el-skeleton :rows="8" animated />
        </div>
        <div class="card placeholder-card" v-else>
          <div class="empty-illustration">
            <div class="empty-icon-wrap">
              <el-icon :size="72"><DataAnalysis /></el-icon>
            </div>
            <div class="empty-title">开始你的第一次估价</div>
            <div class="empty-desc">在左侧填写车辆信息，AI 将基于百万级交易数据为你精准估价</div>
            <div class="empty-features">
              <div class="ef-item"><el-icon><TrendCharts /></el-icon><span>4 种模型可选</span></div>
              <div class="ef-item"><el-icon><MagicStick /></el-icon><span>SHAP 可解释性</span></div>
              <div class="ef-item"><el-icon><Money /></el-icon><span>市场行情对比</span></div>
            </div>
          </div>
        </div>

        <!-- 保值率曲线 + 同价位推荐 -->
        <el-row :gutter="16" class="detail-row" v-if="result">
          <el-col :xs="24" :md="12">
            <div class="card detail-card">
              <div class="card-title">
                <span>保值率预测</span>
                <el-tag size="small" type="success" effect="light">未来 3 年</el-tag>
              </div>
              <div ref="retentionChartRef" class="factor-chart"></div>
              <div class="retention-note" v-if="retentionData">
                按年均 <b>{{ retentionData.annual_mileage }}</b> 万公里使用，
                3 年后预计 <b>{{ retentionData.curve?.[3]?.price ?? '—' }}</b> 万
                （保值率 {{ retentionData.curve?.[3]?.retention ?? '—' }}%）
              </div>
            </div>
          </el-col>
          <el-col :xs="24" :md="12">
            <div class="card detail-card">
              <div class="card-title">
                <span>同价位热门车</span>
                <el-tag size="small" type="warning" effect="light">{{ similarRange }}</el-tag>
              </div>
              <div class="similar-list" v-if="similarCars.length">
                <div v-for="(c, i) in similarCars" :key="c.brand + c.series" class="similar-item">
                  <div class="si-rank" :class="'r' + (i + 1)">{{ i + 1 }}</div>
                  <div class="si-info">
                    <div class="si-name">{{ c.brand }} · {{ c.series }}</div>
                    <div class="si-meta">{{ c.avg_age }} 年 · {{ c.avg_mileage }} 万 km · 在售 {{ c.count }} 辆</div>
                  </div>
                  <div class="si-price">{{ c.avg_price }} 万</div>
                </div>
              </div>
              <el-empty v-else description="该价位暂无热门车数据" :image-size="60" />
            </div>
          </el-col>
        </el-row>

        <!-- SHAP + 市场对比 -->
        <el-row :gutter="16" class="detail-row" v-if="result">
          <el-col :xs="24" :md="12">
            <div class="card detail-card">
              <div class="card-title">
                <span>价格影响因子</span>
                <el-tag size="small" type="info" effect="plain">SHAP 归因分析</el-tag>
              </div>
              <div ref="shapChartRef" class="factor-chart"></div>
              <div class="explain-legend">
                <div class="legend-item up"><span class="dot"></span>推高价格</div>
                <div class="legend-item down"><span class="dot"></span>拉低价格</div>
              </div>
            </div>
          </el-col>
          <el-col :xs="24" :md="12">
            <div class="card detail-card">
              <div class="card-title">
                <span>市场行情对比</span>
                <el-tag size="small" type="warning" effect="light">100 万条数据</el-tag>
              </div>
              <div ref="marketChartRef" class="factor-chart"></div>
              <div class="market-note">
                <el-icon><InfoFilled /></el-icon>
                <span>将本次预测价与同品牌 / 同车龄 / 全市场均价对比</span>
              </div>
            </div>
          </el-col>
        </el-row>

        <!-- 车辆参数 + 模型信息 -->
        <el-row :gutter="16" class="detail-row" v-if="result">
          <el-col :xs="24" :md="16">
            <div class="card info-card">
              <div class="card-title"><span>车辆参数</span></div>
              <div class="param-grid">
                <div class="param-item"><span class="param-label">品牌</span><span class="param-value">{{ result.input_params?.brand }}</span></div>
                <div class="param-item"><span class="param-label">车龄</span><span class="param-value">{{ result.input_params?.age }} 年</span></div>
                <div class="param-item"><span class="param-label">里程</span><span class="param-value">{{ result.input_params?.mileage }} 万 km</span></div>
                <div class="param-item"><span class="param-label">新车指导价</span><span class="param-value">{{ result.input_params?.original_price }} 万</span></div>
                <div class="param-item"><span class="param-label">变速箱</span><span class="param-value">{{ result.input_params?.gearbox }}</span></div>
                <div class="param-item"><span class="param-label">排量</span><span class="param-value">{{ result.input_params?.displacement }}</span></div>
                <div class="param-item"><span class="param-label">燃油类型</span><span class="param-value">{{ result.input_params?.fuel_type }}</span></div>
                <div class="param-item"><span class="param-label">所在城市</span><span class="param-value">{{ result.input_params?.city }}</span></div>
              </div>
            </div>
          </el-col>
          <el-col :xs="24" :md="8">
            <div class="card info-card">
              <div class="card-title"><span>模型信息</span></div>
              <div class="model-info-list">
                <div class="mi-item">
                  <span class="mi-label">模型状态</span>
                  <el-tag :type="modelInfo.model_loaded ? 'success' : 'danger'" effect="light" size="small">
                    {{ modelInfo.model_loaded ? '已加载' : '兜底模式' }}
                  </el-tag>
                </div>
                <div class="mi-item"><span class="mi-label">使用模型</span><span class="mi-value">{{ modelTagLabel }}</span></div>
                <div class="mi-item" v-if="modelInfo.n_estimators"><span class="mi-label">树数量</span><span class="mi-value">{{ modelInfo.n_estimators }}</span></div>
                <div class="mi-item" v-if="modelInfo.max_depth"><span class="mi-label">最大深度</span><span class="mi-value">{{ modelInfo.max_depth }}</span></div>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-col>
    </el-row>

    <!-- 隐藏的报告模板（用于生成 PDF） -->
    <div v-if="result" ref="pdfTemplateRef" class="pdf-template" aria-hidden="true">
      <div class="pdf-header">
        <div class="pdf-title">二手车价格评估报告</div>
        <div class="pdf-sub">二手车价格评估系统 · AI 智能估价 · {{ reportDate }}</div>
      </div>
      <div class="pdf-section">
        <div class="pdf-sec-title">一、车辆信息</div>
        <table class="pdf-table">
          <tr><td>品牌</td><td>{{ result.input_params?.brand }}</td><td>车龄</td><td>{{ result.input_params?.age }} 年</td></tr>
          <tr><td>里程</td><td>{{ result.input_params?.mileage }} 万公里</td><td>新车指导价</td><td>{{ result.input_params?.original_price }} 万元</td></tr>
          <tr><td>变速箱</td><td>{{ result.input_params?.gearbox }}</td><td>排量</td><td>{{ result.input_params?.displacement }}</td></tr>
          <tr><td>燃油类型</td><td>{{ result.input_params?.fuel_type }}</td><td>所在城市</td><td>{{ result.input_params?.city }}</td></tr>
        </table>
      </div>
      <div class="pdf-section">
        <div class="pdf-sec-title">二、评估结果</div>
        <div class="pdf-price-box">
          <div class="pdf-price-label">评估价格</div>
          <div class="pdf-price-value">{{ result.predicted_price }} <span>万元</span></div>
          <div class="pdf-price-range">
            价格区间 {{ result.price_range?.min }} ~ {{ result.price_range?.max }} 万元
            · 模型置信度 {{ Math.round(result.confidence * 100) }}%
            · 当前保值率 {{ retentionRate }}%
          </div>
        </div>
        <table class="pdf-table" style="margin-top:12px">
          <tr><td>评估模型</td><td>{{ modelTagLabel }}</td></tr>
          <tr v-if="retentionData?.curve?.[3]"><td>3 年后预估</td><td>{{ retentionData.curve[3].price }} 万元（保值率 {{ retentionData.curve[3].retention }}%）</td></tr>
          <tr><td>数据来源</td><td>基于 100 万条二手车真实交易数据训练</td></tr>
        </table>
      </div>
      <div class="pdf-section" v-if="result.explain?.length">
        <div class="pdf-sec-title">三、价格影响因子</div>
        <table class="pdf-table">
          <tr><th>影响因素</th><th>影响方向</th><th>影响金额</th></tr>
          <tr v-for="e in result.explain.slice(0, 6)" :key="e.feature">
            <td>{{ e.label }}</td>
            <td>{{ e.direction === 'up' ? '推高价格' : '拉低价格' }}</td>
            <td>{{ e.impact > 0 ? '+' : '' }}{{ e.impact }} 万元</td>
          </tr>
        </table>
      </div>
      <div class="pdf-footer">本报告由二手车价格评估系统自动生成，仅供参考，不构成交易建议。</div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { ElMessage } from 'element-plus'
import echarts from '@/utils/echarts'
import {
  MagicStick, DataAnalysis, CircleCheckFilled, InfoFilled,
  TrendCharts, Bottom, Top, Lightning, Cpu, Connection, Download
} from '@element-plus/icons-vue'
import CountUp from '@/components/CountUp.vue'
import {
  predictPrice, getCarBrands, getCarCities, getModelInfo,
  getMarketCompare, getRetentionCurve, getSimilarCars
} from '@/api'
import { chartPalette, linearGradient, registerChart, unregisterChart } from '@/utils/theme'

const formRef = ref(null)
const loading = ref(false)
const pdfLoading = ref(false)
const result = ref(null)
const modelInfo = ref({})
const brands = ref([])
const cities = ref([])
const marketData = ref(null)
const retentionData = ref(null)
const similarCars = ref([])
const similarRange = ref('')

const shapChartRef = ref(null)
const marketChartRef = ref(null)
const gaugeChartRef = ref(null)
const retentionChartRef = ref(null)
const reportRef = ref(null)
const pdfTemplateRef = ref(null)

let shapChart = null
let marketChart = null
let gaugeChart = null
let retentionChart = null

const displacements = ['1.0L', '1.2T', '1.4T', '1.5L', '1.5T', '1.6L', '1.8L', '2.0L', '2.0T', '2.5L', '3.0T', '纯电']
const fuelTypes = ['汽油', '柴油', '纯电动', '混合动力', '插电混动']

const iconMap = { TrendCharts, Lightning, Cpu, Connection }
const modelOptions = [
  { value: 'sklearn', label: '随机森林', desc: 'Scikit-learn', icon: 'TrendCharts', gradient: 'linear-gradient(135deg, #22C55E, #4ADE80)' },
  { value: 'lightgbm', label: 'LightGBM', desc: '精度最高', icon: 'Lightning', gradient: 'linear-gradient(135deg, #2D6BFF, #5B8CFF)' },
  { value: 'xgboost', label: 'XGBoost', desc: '梯度提升', icon: 'Cpu', gradient: 'linear-gradient(135deg, #F59E0B, #FBBF24)' },
  { value: 'spark_mllib', label: 'Spark MLlib', desc: '分布式', icon: 'Connection', gradient: 'linear-gradient(135deg, #8B5CF6, #A78BFA)' },
]

const modelTagLabel = computed(() => {
  const map = { sklearn: 'Scikit-learn 随机森林', lightgbm: 'LightGBM 梯度提升', xgboost: 'XGBoost 梯度提升', spark_mllib: 'Spark MLlib 随机森林' }
  return map[result.value?.model_type || form.model_type] || '随机森林'
})

const form = reactive({
  brand: '大众', age: 3, mileage: 5.0, original_price: 16.0,
  gearbox: '自动', displacement: '1.4T', fuel_type: '汽油', city: '北京', model_type: 'sklearn'
})

const rules = {
  brand: [{ required: true, message: '请选择品牌', trigger: 'change' }],
  age: [{ required: true, message: '请输入车龄', trigger: 'blur' }],
  mileage: [{ required: true, message: '请输入里程', trigger: 'blur' }]
}

const retentionRate = computed(() => {
  if (!result.value?.predicted_price || !result.value?.input_params?.original_price) return '—'
  return Math.round(result.value.predicted_price / result.value.input_params.original_price * 100)
})

const retentionClass = computed(() => {
  const r = Number(retentionRate.value)
  if (Number.isNaN(r)) return ''
  return r >= 60 ? 'ret-high' : r >= 40 ? 'ret-mid' : 'ret-low'
})

const reportDate = computed(() => new Date().toLocaleString('zh-CN'))

const rangeFillStyle = computed(() => {
  if (!result.value?.price_range) return {}
  const { min, max } = result.value.price_range
  const pct = Math.min(100, Math.max(0, ((result.value.predicted_price - min) / (max - min)) * 100))
  return { width: pct + '%' }
})

const rangePointerStyle = computed(() => {
  if (!result.value?.price_range) return {}
  const { min, max } = result.value.price_range
  const pct = Math.min(100, Math.max(0, ((result.value.predicted_price - min) / (max - min)) * 100))
  return { left: `calc(${pct}% - 8px)` }
})

const loadBrands = async () => {
  try { const res = await getCarBrands(); brands.value = res.brands || [] }
  catch (e) { brands.value = ['大众', '丰田', '本田', '日产', '别克', '奥迪', '宝马', '奔驰', '比亚迪', '特斯拉'] }
}

const loadCities = async () => {
  try { const res = await getCarCities(); cities.value = res.cities || [] }
  catch (e) { cities.value = ['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '西安', '南京', '重庆'] }
}

const loadModelInfo = async () => {
  try { const res = await getModelInfo(); if (res.code === 200) modelInfo.value = res.data }
  catch (e) { modelInfo.value = { model_loaded: false, model_type: 'fallback' } }
}

/* ==================== 仪表盘 ==================== */
const renderGauge = () => {
  if (!gaugeChartRef.value || !result.value) return
  if (!gaugeChart) gaugeChart = echarts.init(gaugeChartRef.value)
  const p = chartPalette()
  const price = result.value.predicted_price
  const min = result.value.price_range?.min ?? price * 0.8
  const max = result.value.price_range?.max ?? price * 1.2
  const span = Math.max(max - min, 0.01)
  const pct = Math.min(1, Math.max(0, (price - min) / span))

  gaugeChart.setOption({
    series: [{
      type: 'gauge',
      startAngle: 210, endAngle: -30,
      min: 0, max: 100,
      radius: '100%', center: ['50%', '62%'],
      progress: {
        show: true, width: 12, roundCap: true,
        itemStyle: { color: linearGradient(['#2D6BFF', '#8B5CF6'], 'horizontal') }
      },
      axisLine: { lineStyle: { width: 12, color: [[1, p.dark ? '#2D3142' : '#EEF1F6']] } },
      axisTick: { show: false }, splitLine: { show: false }, axisLabel: { show: false },
      pointer: { show: false }, anchor: { show: false },
      title: { show: true, offsetCenter: [0, '28%'], color: p.textSecondary, fontSize: 11 },
      detail: {
        valueAnimation: true,
        offsetCenter: [0, '-2%'],
        formatter: () => price.toFixed(2),
        color: p.dark ? '#F3F4F6' : '#1F2937',
        fontSize: 26, fontWeight: 800
      },
      data: [{ value: Math.round(pct * 100), name: '区间位置' }]
    }]
  })
  gaugeChart.resize()
}

/* ==================== 保值率曲线 ==================== */
const renderRetention = () => {
  if (!retentionChartRef.value || !retentionData.value?.curve?.length) return
  if (!retentionChart) retentionChart = echarts.init(retentionChartRef.value)
  const p = chartPalette()
  const curve = retentionData.value.curve
  retentionChart.setOption({
    tooltip: {
      trigger: 'axis', backgroundColor: p.tooltipBg, borderColor: p.tooltipBorder,
      textStyle: { color: p.tooltipText },
      formatter: (ps) => {
        const i = ps[0].dataIndex
        const c = curve[i]
        return `${c.year === 0 ? '当前' : c.year + ' 年后'}（${c.age} 年车龄）<br/>预估价：${c.price} 万<br/>保值率：${c.retention}%`
      }
    },
    grid: { left: 44, right: 44, top: 30, bottom: 26 },
    xAxis: {
      type: 'category',
      data: curve.map(c => c.year === 0 ? '当前' : `+${c.year}年`),
      axisLine: { lineStyle: { color: p.axisLine } },
      axisLabel: { color: p.textSecondary, fontSize: 11 }
    },
    yAxis: [
      { type: 'value', name: '价格(万)', nameTextStyle: { color: p.textSecondary }, axisLabel: { color: p.textSecondary }, splitLine: { lineStyle: { color: p.splitLine } } },
      { type: 'value', name: '保值率%', max: 100, nameTextStyle: { color: p.textSecondary }, axisLabel: { color: p.textSecondary, formatter: '{value}%' }, splitLine: { show: false } }
    ],
    series: [
      {
        name: '预估价格', type: 'line', smooth: true, symbolSize: 8,
        data: curve.map(c => c.price),
        lineStyle: { width: 3, color: linearGradient(['#2D6BFF', '#8B5CF6'], 'horizontal') },
        itemStyle: { color: '#2D6BFF', borderColor: '#fff', borderWidth: 2 },
        areaStyle: { color: linearGradient(['rgba(45,107,255,0.25)', 'rgba(45,107,255,0.02)']) },
        label: { show: true, position: 'top', color: p.text, fontWeight: 600, fontSize: 11, formatter: '{c}万' }
      },
      {
        name: '保值率', type: 'line', smooth: true, yAxisIndex: 1, symbol: 'circle', symbolSize: 6,
        data: curve.map(c => c.retention),
        lineStyle: { width: 2, type: 'dashed', color: '#22C55E' },
        itemStyle: { color: '#22C55E' }
      }
    ]
  })
  retentionChart.resize()
}

/* ==================== SHAP ==================== */
const renderShap = () => {
  if (!shapChartRef.value || !result.value?.explain?.length) return
  if (!shapChart) shapChart = echarts.init(shapChartRef.value)
  const p = chartPalette()
  const list = result.value.explain
  shapChart.setOption({
    tooltip: {
      trigger: 'axis', axisPointer: { type: 'shadow' },
      backgroundColor: p.tooltipBg, borderColor: p.tooltipBorder, textStyle: { color: p.tooltipText },
      formatter: (ps) => {
        const item = list[ps[0].dataIndex]
        return item ? `${item.label}<br/>影响：${item.impact > 0 ? '+' : ''}${item.impact} 万（${item.direction === 'up' ? '推高' : '拉低'}）` : ''
      }
    },
    grid: { left: '4%', right: '8%', top: 12, bottom: 12, containLabel: true },
    xAxis: { type: 'value', name: '影响(万元)', nameTextStyle: { color: p.textSecondary }, axisLabel: { color: p.textSecondary }, splitLine: { lineStyle: { color: p.splitLine } } },
    yAxis: { type: 'category', data: list.map(i => i.label), axisLabel: { color: p.text, fontWeight: 500 }, axisLine: { lineStyle: { color: p.axisLine } } },
    series: [{
      type: 'bar',
      data: list.map(i => ({
        value: Number(Number(i.impact).toFixed(2)),
        itemStyle: {
          color: i.direction === 'up' ? linearGradient(['#4ADE80', '#22C55E'], 'horizontal') : linearGradient(['#F87171', '#EF4444'], 'horizontal'),
          borderRadius: [0, 4, 4, 0]
        }
      })),
      barMaxWidth: 20,
      label: {
        show: true, position: 'right',
        formatter: (p) => `${p.value > 0 ? '+' : ''}${p.value}万`,
        color: p.text, fontWeight: 600, fontSize: 12
      }
    }]
  })
  shapChart.resize()
}

/* ==================== 市场对比 ==================== */
const loadMarketCompare = async () => {
  if (!result.value) return
  try {
    const res = await getMarketCompare({ brand: result.value.input_params?.brand, age: result.value.input_params?.age })
    if (res.code === 200) { marketData.value = res.data; await nextTick(); renderMarketChart() }
  } catch (e) { }
}

const renderMarketChart = () => {
  if (!marketChartRef.value || !marketData.value) return
  if (!marketChart) marketChart = echarts.init(marketChartRef.value)
  const p = chartPalette()
  const d = marketData.value
  const rows = [{ name: '本次预测', value: Number(Number(result.value.predicted_price).toFixed(2)), isMain: true }]
  if (d.brand_avg != null) rows.push({ name: '同品牌均价', value: Number(d.brand_avg), color: '#22C55E' })
  if (d.age_avg != null) rows.push({ name: '同车龄均价', value: Number(d.age_avg), color: '#F59E0B' })
  rows.push({ name: '全市场均价', value: Number(d.all_avg), color: '#9CA3AF' })
  marketChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, backgroundColor: p.tooltipBg, borderColor: p.tooltipBorder, textStyle: { color: p.tooltipText }, formatter: '{b}: {c} 万' },
    grid: { left: '3%', right: '6%', bottom: '3%', top: 12, containLabel: true },
    xAxis: { type: 'category', data: rows.map(r => r.name), axisLabel: { color: p.textSecondary, fontSize: 12 }, axisLine: { lineStyle: { color: p.axisLine } } },
    yAxis: { type: 'value', name: '万元', nameTextStyle: { color: p.textSecondary }, axisLabel: { color: p.textSecondary }, splitLine: { lineStyle: { color: p.splitLine } } },
    series: [{
      type: 'bar',
      data: rows.map(r => ({
        value: r.value,
        itemStyle: { color: r.isMain ? linearGradient(['#2D6BFF', '#6B9BFF']) : r.color, borderRadius: [6, 6, 0, 0] }
      })),
      barMaxWidth: 44,
      label: { show: true, position: 'top', formatter: '{c} 万', color: p.text, fontWeight: 600, fontSize: 12 }
    }]
  })
  marketChart.resize()
}

/* ==================== 附加数据 ==================== */
const loadRetention = async () => {
  try {
    const res = await getRetentionCurve({ ...form, years: 3 })
    if (res.code === 200) { retentionData.value = res.data; await nextTick(); renderRetention() }
  } catch (e) { }
}

const loadSimilar = async () => {
  try {
    const res = await getSimilarCars({ price: result.value.predicted_price, limit: 6 })
    if (res.code === 200) {
      similarCars.value = res.data || []
      similarRange.value = res.range ? `${res.range[0]}~${res.range[1]} 万` : ''
    }
  } catch (e) { similarCars.value = [] }
}

/* ==================== PDF 报告 ==================== */
const downloadReport = async () => {
  if (!pdfTemplateRef.value) return
  pdfLoading.value = true
  try {
    const [{ default: html2canvas }, { jsPDF }] = await Promise.all([
      import('html2canvas'),
      import('jspdf')
    ])
    const canvas = await html2canvas(pdfTemplateRef.value, {
      scale: 2, useCORS: true, backgroundColor: '#ffffff', logging: false
    })
    const img = canvas.toDataURL('image/jpeg', 0.95)
    const pdf = new jsPDF('p', 'mm', 'a4')
    const pageW = pdf.internal.pageSize.getWidth()
    const pageH = pdf.internal.pageSize.getHeight()
    const imgH = canvas.height * pageW / canvas.width
    let heightLeft = imgH
    let pos = 0
    pdf.addImage(img, 'JPEG', 0, pos, pageW, imgH)
    heightLeft -= pageH
    while (heightLeft > 0) {
      pos = heightLeft - imgH
      pdf.addPage()
      pdf.addImage(img, 'JPEG', 0, pos, pageW, imgH)
      heightLeft -= pageH
    }
    pdf.save(`估价报告_${form.brand}_${Date.now()}.pdf`)
    ElMessage.success('报告已生成')
  } catch (e) {
    console.error(e)
    ElMessage.error('报告生成失败')
  } finally {
    pdfLoading.value = false
  }
}

/* ==================== 主流程 ==================== */
const handlePredict = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    result.value = null
    marketData.value = null
    retentionData.value = null
    similarCars.value = []
    try {
      const res = await predictPrice({ ...form })
      if (res.code === 200) {
        result.value = res.data
        ElMessage.success('估价完成')
        await nextTick()
        renderGauge()
        renderShap()
        loadMarketCompare()
        loadRetention()
        loadSimilar()
      } else {
        ElMessage.error(res.message || '预测失败')
      }
    } catch (e) {
      ElMessage.error('预测请求失败，请检查后端服务')
    } finally {
      loading.value = false
    }
  })
}

onMounted(() => { loadBrands(); loadCities(); loadModelInfo() })
onUnmounted(() => {
  ;[shapChart, marketChart, gaugeChart, retentionChart].forEach(c => {
    if (c) { unregisterChart(c); c.dispose() }
  })
})

// 注册主题跟随重绘
const _registerAll = () => {
  if (gaugeChart) registerChart(gaugeChart, renderGauge)
  if (retentionChart) registerChart(retentionChart, renderRetention)
  if (shapChart) registerChart(shapChart, renderShap)
  if (marketChart) registerChart(marketChart, renderMarketChart)
}
onMounted(() => setTimeout(_registerAll, 100))
</script>

<style scoped>
.predict-page-v2 { padding: 0; }

/* ============ 表单卡片 ============ */
.form-card { position: sticky; top: 20px; }
.predict-form .el-form-item { margin-bottom: 16px; }

.unit-suffix {
  position: absolute; right: 12px; top: 50%;
  transform: translateY(-50%);
  font-size: 12px; color: var(--text-secondary); pointer-events: none;
}

.predict-form :deep(.el-input-number) { width: 100%; }
.predict-form :deep(.el-input-number .el-input__inner) { text-align: left; }
.pill-group :deep(.el-radio-button__inner) { border-radius: 8px !important; padding: 8px 18px; }

/* ============ 模型选择器 ============ */
.model-selector { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
.model-card {
  display: flex; align-items: center; gap: 10px; padding: 10px 12px;
  border-radius: 10px; border: 2px solid var(--border-color);
  background: var(--card-bg); cursor: pointer;
  transition: all var(--transition-fast); position: relative;
}
.model-card:hover { border-color: var(--primary-lighter); transform: translateY(-1px); }
.model-card.active { border-color: var(--primary); background: var(--primary-lighter); box-shadow: 0 4px 12px var(--primary-glow); }
.mc-icon { width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 18px; flex-shrink: 0; }
.mc-info { flex: 1; min-width: 0; }
.mc-name { font-size: 13px; font-weight: 600; color: var(--text-primary); line-height: 1.2; }
.mc-desc { font-size: 11px; color: var(--text-secondary); margin-top: 2px; }
.mc-check { position: absolute; top: 6px; right: 6px; color: var(--primary); font-size: 16px; }

/* ============ 预测按钮 ============ */
.predict-btn {
  width: 100%; height: 48px; font-size: 15px; font-weight: 600; letter-spacing: 2px;
  border-radius: 12px; background: var(--gradient-primary); border: none;
  box-shadow: 0 6px 20px rgba(45, 107, 255, 0.35); transition: all var(--transition-base);
}
.predict-btn:hover { transform: translateY(-2px); box-shadow: 0 10px 28px rgba(45, 107, 255, 0.45); }
.predict-btn:active { transform: translateY(0); }

/* ============ 结果主卡片 ============ */
.result-hero-card { padding: 0; overflow: hidden; margin-bottom: 20px; animation: fadeInUp 0.5s ease; }
.result-hero {
  display: flex; gap: 24px; padding: 28px 32px;
  background: radial-gradient(ellipse at top right, rgba(139, 92, 246, 0.1), transparent 50%),
    linear-gradient(135deg, #F8FAFF 0%, #FFFFFF 100%);
  position: relative;
}
[data-theme="dark"] .result-hero {
  background: radial-gradient(ellipse at top right, rgba(139, 92, 246, 0.15), transparent 50%),
    linear-gradient(135deg, #1E2233 0%, #1A1D28 100%);
}
.result-left { flex: 1; min-width: 0; }
.result-badge {
  display: inline-flex; align-items: center; gap: 6px; padding: 5px 12px;
  border-radius: 20px; background: var(--primary-lighter); color: var(--primary);
  font-size: 12px; font-weight: 600; margin-bottom: 12px;
}
.conf-tag { margin-left: 6px; }
.result-title { font-size: 22px; font-weight: 700; color: var(--text-primary); margin-bottom: 18px; letter-spacing: -0.3px; }

/* 大数字 + 仪表盘 */
.hero-main { display: flex; align-items: center; gap: 20px; margin-bottom: 18px; flex-wrap: wrap; }
.hero-price-block { flex: 1; min-width: 220px; }
.price-label { display: block; font-size: 13px; color: var(--text-secondary); margin-bottom: 6px; letter-spacing: 2px; font-weight: 500; }
.price-main { display: flex; align-items: baseline; }
.price-value {
  font-size: 64px; font-weight: 800; line-height: 1.1;
  background: var(--gradient-primary);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  letter-spacing: -2px;
}
.price-unit { font-size: 18px; color: var(--text-secondary); margin-left: 6px; font-weight: 500; }
.price-sub { margin-top: 8px; font-size: 13px; color: var(--text-secondary); }
.price-sub b { font-size: 16px; }
.ret-high { color: #22C55E; } .ret-mid { color: #F59E0B; } .ret-low { color: #EF4444; }
.hero-actions { margin-top: 14px; }
.gauge-chart { width: 200px; height: 160px; flex-shrink: 0; }

.result-range { display: flex; align-items: center; gap: 14px; }
.range-tag { font-size: 13px; padding: 4px 12px; display: flex; align-items: center; gap: 4px; font-weight: 500; }
.range-bar { flex: 1; height: 8px; background: linear-gradient(90deg, #BBF7D0, #22C55E); border-radius: 4px; position: relative; overflow: visible; }
.range-fill { height: 100%; background: linear-gradient(90deg, #2D6BFF, #6B9BFF); border-radius: 4px; transition: width 1s cubic-bezier(0.4, 0, 0.2, 1); }
.range-pointer {
  position: absolute; top: 50%; transform: translateY(-50%);
  width: 16px; height: 16px; border-radius: 50%;
  background: #fff; border: 3px solid var(--primary);
  box-shadow: 0 2px 8px rgba(45, 107, 255, 0.4);
  transition: left 1s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ============ 空状态 ============ */
.placeholder-card { min-height: 420px; display: flex; align-items: center; justify-content: center; margin-bottom: 20px; }
.empty-illustration { text-align: center; padding: 40px 20px; }
.empty-icon-wrap {
  width: 120px; height: 120px; margin: 0 auto 20px; border-radius: 30px;
  background: var(--primary-lighter); color: var(--primary);
  display: flex; align-items: center; justify-content: center;
  animation: float 3s ease-in-out infinite;
}
.empty-title { font-size: 18px; font-weight: 700; color: var(--text-primary); margin-bottom: 8px; }
.empty-desc { font-size: 13px; color: var(--text-secondary); margin-bottom: 24px; max-width: 320px; margin-left: auto; margin-right: auto; line-height: 1.6; }
.empty-features { display: flex; justify-content: center; gap: 24px; flex-wrap: wrap; }
.ef-item { display: flex; flex-direction: column; align-items: center; gap: 6px; font-size: 12px; color: var(--text-secondary); font-weight: 500; }
.ef-item .el-icon { font-size: 20px; color: var(--primary); }

/* ============ 详情行 ============ */
.detail-row { margin-bottom: 20px; }
.detail-card { min-height: 340px; }
.factor-chart { width: 100%; height: 240px; }

.retention-note { margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--border-color-light); font-size: 12px; color: var(--text-secondary); line-height: 1.6; }
.retention-note b { color: var(--text-primary); }

/* 同价位推荐 */
.similar-list { display: flex; flex-direction: column; gap: 4px; max-height: 250px; overflow-y: auto; }
.similar-item {
  display: flex; align-items: center; gap: 10px; padding: 9px 10px;
  border-radius: 10px; transition: background var(--transition-fast);
}
.similar-item:hover { background: var(--page-bg); }
.si-rank {
  width: 24px; height: 24px; border-radius: 7px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; color: #fff;
  background: var(--text-muted);
}
.si-rank.r1 { background: linear-gradient(135deg, #F59E0B, #FBBF24); }
.si-rank.r2 { background: linear-gradient(135deg, #94A3B8, #CBD5E1); }
.si-rank.r3 { background: linear-gradient(135deg, #D97706, #F59E0B); }
.si-info { flex: 1; min-width: 0; }
.si-name { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.si-meta { font-size: 11px; color: var(--text-secondary); margin-top: 2px; }
.si-price { font-size: 15px; font-weight: 700; color: var(--primary); flex-shrink: 0; }

.explain-legend { display: flex; justify-content: center; gap: 20px; margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--border-color-light); }
.legend-item { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--text-secondary); }
.legend-item .dot { width: 10px; height: 10px; border-radius: 3px; }
.legend-item.up .dot { background: linear-gradient(90deg, #4ADE80, #22C55E); }
.legend-item.down .dot { background: linear-gradient(90deg, #F87171, #EF4444); }

.market-note { display: flex; align-items: center; gap: 6px; margin-top: 12px; padding-top: 10px; border-top: 1px solid var(--border-color-light); font-size: 12px; color: var(--text-secondary); }

/* ============ 参数网格 ============ */
.info-card { margin-bottom: 0; }
.param-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.param-item { display: flex; flex-direction: column; gap: 6px; padding: 12px 14px; border-radius: 10px; background: var(--page-bg); transition: background var(--transition-fast); }
.param-item:hover { background: var(--primary-lighter); }
.param-label { font-size: 12px; color: var(--text-secondary); font-weight: 500; }
.param-value { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.model-info-list { display: flex; flex-direction: column; gap: 10px; }
.mi-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; border-radius: 8px; background: var(--page-bg); }
.mi-label { font-size: 13px; color: var(--text-secondary); font-weight: 500; }
.mi-value { font-size: 14px; font-weight: 600; color: var(--text-primary); }

/* ============ PDF 模板（隐藏，仅截图用） ============ */
.pdf-template {
  position: fixed; left: -9999px; top: 0;
  width: 794px; padding: 48px 56px;
  background: #ffffff; color: #1F2937;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
  z-index: -1;
}
.pdf-header { text-align: center; margin-bottom: 28px; padding-bottom: 18px; border-bottom: 3px solid #2D6BFF; }
.pdf-title { font-size: 26px; font-weight: 800; color: #1F2937; letter-spacing: 4px; }
.pdf-sub { font-size: 12px; color: #6B7280; margin-top: 8px; letter-spacing: 1px; }
.pdf-section { margin-bottom: 22px; }
.pdf-sec-title { font-size: 15px; font-weight: 700; color: #2D6BFF; margin-bottom: 10px; padding-left: 10px; border-left: 4px solid #2D6BFF; }
.pdf-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.pdf-table td, .pdf-table th { border: 1px solid #E5E7EB; padding: 8px 12px; text-align: left; }
.pdf-table td:first-child, .pdf-table td:nth-child(3) { background: #F7F9FC; color: #6B7280; width: 15%; font-weight: 600; }
.pdf-table th { background: #F0F6FF; color: #1F2937; font-weight: 700; }
.pdf-price-box { text-align: center; padding: 18px; background: linear-gradient(135deg, #F8FAFF, #EEF2FF); border-radius: 12px; }
.pdf-price-label { font-size: 12px; color: #6B7280; letter-spacing: 3px; }
.pdf-price-value { font-size: 42px; font-weight: 800; color: #2D6BFF; margin: 6px 0; }
.pdf-price-value span { font-size: 16px; font-weight: 500; color: #6B7280; }
.pdf-price-range { font-size: 12px; color: #4B5563; }
.pdf-footer { margin-top: 28px; padding-top: 14px; border-top: 1px solid #E5E7EB; font-size: 10px; color: #9CA3AF; text-align: center; line-height: 1.6; }

/* ============ 响应式 ============ */
@media (max-width: 1200px) {
  .param-grid { grid-template-columns: repeat(3, 1fr); }
  .price-value { font-size: 52px; }
}
@media (max-width: 768px) {
  .result-hero { padding: 20px; }
  .hero-main { flex-direction: column; align-items: flex-start; }
  .gauge-chart { width: 100%; }
  .param-grid { grid-template-columns: repeat(2, 1fr); }
  .price-value { font-size: 42px; }
  .model-selector { grid-template-columns: 1fr; }
}
</style>

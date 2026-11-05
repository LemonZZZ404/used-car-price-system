<template>
  <div class="export-page">
    <el-row :gutter="20">
      <el-col :xs="24" :md="14">
        <div class="card">
          <div class="card-title">
            <span>导出条件</span>
            <el-tag size="small" effect="plain" type="warning">CSV 流式导出 · 上限 10 万行</el-tag>
          </div>
          <el-form label-width="90px" size="default">
            <el-row :gutter="14">
              <el-col :span="12">
                <el-form-item label="品牌">
                  <el-select v-model="form.brand" placeholder="全部品牌" clearable filterable style="width:100%">
                    <el-option v-for="b in brands" :key="b" :label="b" :value="b" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="城市">
                  <el-select v-model="form.city" placeholder="全部城市" clearable filterable style="width:100%">
                    <el-option v-for="c in cities" :key="c" :label="c" :value="c" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="燃油类型">
                  <el-select v-model="form.fuel_type" placeholder="全部" clearable style="width:100%">
                    <el-option v-for="f in fuelTypes" :key="f" :label="f" :value="f" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="行数上限">
                  <el-select v-model="form.limit" style="width:100%">
                    <el-option label="1 万行" :value="10000" />
                    <el-option label="5 万行" :value="50000" />
                    <el-option label="10 万行（全量）" :value="100000" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="价格区间">
                  <div class="range-inline">
                    <el-input-number v-model="form.min_price" :min="0" :max="500" :controls="false" placeholder="最低" style="width:90px" />
                    <span class="dash">-</span>
                    <el-input-number v-model="form.max_price" :min="0" :max="500" :controls="false" placeholder="最高" style="width:90px" />
                    <span class="unit">万</span>
                  </div>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="车龄区间">
                  <div class="range-inline">
                    <el-input-number v-model="form.min_age" :min="0" :max="30" :controls="false" placeholder="最低" style="width:90px" />
                    <span class="dash">-</span>
                    <el-input-number v-model="form.max_age" :min="0" :max="30" :controls="false" placeholder="最高" style="width:90px" />
                    <span class="unit">年</span>
                  </div>
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>

          <div class="export-foot">
            <div class="est">
              <span v-if="estimating">预估中...</span>
              <template v-else-if="estCount !== null">
                预估约 <b>{{ estCount.toLocaleString('zh-CN') }}</b> 条
                <span class="est-tip" v-if="hasPriceFilter">（价格区间不计入预估，以实际导出为准）</span>
              </template>
              <span v-else class="est-tip">设置条件后自动预估条数</span>
            </div>
            <el-button type="success" size="large" :icon="Download" :disabled="estimating" @click="handleExport">
              导出 CSV
            </el-button>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :md="10">
        <div class="card h-full">
          <div class="card-title">
            <span>最近导出记录</span>
            <el-button text size="small" type="danger" @click="clearHistory" v-if="history.length">清空</el-button>
          </div>
          <el-empty v-if="!history.length" description="暂无导出记录" :image-size="70" />
          <div v-else class="history-list">
            <div v-for="(h, i) in history" :key="i" class="history-item">
              <div class="hi-main">
                <div class="hi-name">{{ h.label }}</div>
                <div class="hi-meta">{{ h.time }}</div>
              </div>
              <el-tag size="small" effect="plain">{{ h.limit }} 行上限</el-tag>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted } from 'vue'
import { Download } from '@element-plus/icons-vue'
import { getCarList, getCarBrands, getCarCities } from '@/api'

const form = reactive({
  brand: '', city: '', fuel_type: '',
  min_price: null, max_price: null, min_age: null, max_age: null,
  limit: 10000
})
const brands = ref([])
const cities = ref([])
const fuelTypes = ['汽油', '柴油', '纯电动', '混合动力', '插电混动']

const estCount = ref(null)
const estimating = ref(false)
const history = ref(JSON.parse(localStorage.getItem('used_car_export_history') || '[]'))

const hasPriceFilter = form.min_price !== null || form.max_price !== null

const buildQuery = () => {
  const params = new URLSearchParams()
  Object.entries(form).forEach(([k, v]) => {
    if (v !== '' && v !== null && v !== undefined) params.set(k, v)
  })
  return params.toString()
}

const describeFilter = () => {
  const parts = []
  if (form.brand) parts.push(form.brand)
  if (form.city) parts.push(form.city)
  if (form.fuel_type) parts.push(form.fuel_type)
  if (form.min_price !== null || form.max_price !== null) {
    parts.push(`${form.min_price ?? 0}-${form.max_price ?? '∞'}万`)
  }
  if (form.min_age !== null || form.max_age !== null) {
    parts.push(`${form.min_age ?? 0}-${form.max_age ?? 30}年`)
  }
  return parts.length ? parts.join(' / ') : '全量数据'
}

const estimate = async () => {
  estimating.value = true
  try {
    const params = { page: 1, page_size: 1 }
    if (form.brand) params.brand = form.brand
    if (form.city) params.city = form.city
    if (form.fuel_type) params.fuel_type = form.fuel_type
    if (form.min_age !== null && form.min_age !== undefined) params.age = form.min_age
    const res = await getCarList(params)
    estCount.value = res.count || 0
  } catch (e) {
    estCount.value = null
  } finally {
    estimating.value = false
  }
}

const handleExport = () => {
  const qs = buildQuery()
  window.open(`/api/export/csv/?${qs}`, '_blank')
  history.value.unshift({ label: describeFilter(), time: new Date().toLocaleString('zh-CN'), limit: form.limit })
  history.value = history.value.slice(0, 8)
  localStorage.setItem('used_car_export_history', JSON.stringify(history.value))
}

const clearHistory = () => {
  history.value = []
  localStorage.removeItem('used_car_export_history')
}

watch(() => ({ ...form }), () => {
  estCount.value = null
  const t = setTimeout(estimate, 400)
  return () => clearTimeout(t)
}, { deep: true })

onMounted(async () => {
  try { const r = await getCarBrands(); brands.value = r.brands || [] }
  catch (e) { brands.value = ['大众', '丰田', '本田', '日产', '别克', '奥迪', '宝马', '奔驰', '比亚迪', '特斯拉'] }
  try { const r = await getCarCities(); cities.value = r.cities || [] }
  catch (e) { cities.value = ['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '西安', '南京', '重庆'] }
})
</script>

<style scoped>
.h-full { height: 100%; }
.range-inline { display: flex; align-items: center; gap: 6px; }
.range-inline .dash { color: #9CA3AF; }
.range-inline .unit { color: #6B7280; font-size: 13px; }
.export-foot { margin-top: 10px; padding-top: 16px; border-top: 1px solid rgba(148,163,184,0.2); display: flex; justify-content: space-between; align-items: center; }
.est { font-size: 14px; color: #6B7280; }
.est b { color: #2D6BFF; font-size: 18px; }
.est-tip { font-size: 12px; color: #9CA3AF; }
.history-list { max-height: 360px; overflow-y: auto; }
.history-item { display: flex; justify-content: space-between; align-items: center; padding: 12px 4px; border-bottom: 1px solid rgba(148,163,184,0.15); }
.hi-name { font-size: 13px; font-weight: 500; }
.hi-meta { font-size: 12px; color: #9CA3AF; margin-top: 3px; }
</style>

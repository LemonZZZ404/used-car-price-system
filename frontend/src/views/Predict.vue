<template>
  <div class="predict-page">
    <el-row :gutter="20">
      <!-- 左侧：预测表单 -->
      <el-col :span="10">
        <div class="card">
          <div class="card-title">车辆信息录入</div>
          <el-form :model="form" :rules="rules" ref="formRef" label-width="100px" size="default">
            <el-form-item label="品牌" prop="brand">
              <el-select v-model="form.brand" placeholder="请选择品牌" filterable style="width:100%">
                <el-option v-for="b in brands" :key="b" :label="b" :value="b" />
              </el-select>
            </el-form-item>

            <el-form-item label="车龄" prop="age">
              <el-input-number v-model="form.age" :min="0" :max="30" :step="1" style="width:100%" />
              <span style="margin-left:8px;color:#909399">年</span>
            </el-form-item>

            <el-form-item label="里程" prop="mileage">
              <el-input-number v-model="form.mileage" :min="0" :max="50" :step="0.5" :precision="1" style="width:100%" />
              <span style="margin-left:8px;color:#909399">万公里</span>
            </el-form-item>

            <el-form-item label="新车指导价" prop="original_price">
              <el-input-number v-model="form.original_price" :min="0" :max="500" :step="1" :precision="2" style="width:100%" />
              <span style="margin-left:8px;color:#909399">万元</span>
            </el-form-item>

            <el-form-item label="变速箱" prop="gearbox">
              <el-radio-group v-model="form.gearbox">
                <el-radio value="自动">自动</el-radio>
                <el-radio value="手动">手动</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="排量" prop="displacement">
              <el-select v-model="form.displacement" placeholder="请选择排量" style="width:100%">
                <el-option v-for="d in displacements" :key="d" :label="d" :value="d" />
              </el-select>
            </el-form-item>

            <el-form-item label="燃油类型" prop="fuel_type">
              <el-select v-model="form.fuel_type" placeholder="请选择燃油类型" style="width:100%">
                <el-option v-for="f in fuelTypes" :key="f" :label="f" :value="f" />
              </el-select>
            </el-form-item>

            <el-form-item label="所在城市" prop="city">
              <el-select v-model="form.city" placeholder="请选择城市" filterable style="width:100%">
                <el-option v-for="c in cities" :key="c" :label="c" :value="c" />
              </el-select>
            </el-form-item>

            <el-form-item label="预测模型">
              <el-radio-group v-model="form.model_type">
                <el-radio value="sklearn">Scikit-learn</el-radio>
                <el-radio value="spark_mllib">Spark MLlib</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" :icon="MagicStick" :loading="loading" @click="handlePredict" style="width:100%">
                开始预测
              </el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-col>

      <!-- 右侧：预测结果 -->
      <el-col :span="14">
        <div class="card result-card" v-if="result">
          <div class="card-title">预测结果</div>
          <div class="result-main">
            <div class="result-price">
              <span class="price-label">预测价格</span>
              <span class="price-value">{{ result.predicted_price }}</span>
              <span class="price-unit">万元</span>
            </div>
            <div class="result-range">
              <el-tag type="info" size="large">
                合理区间：{{ result.price_range?.min }} ~ {{ result.price_range?.max }} 万元
              </el-tag>
            </div>
          </div>

          <el-divider />

          <el-descriptions :column="2" border size="default">
            <el-descriptions-item label="品牌">{{ result.input_params?.brand }}</el-descriptions-item>
            <el-descriptions-item label="车龄">{{ result.input_params?.age }} 年</el-descriptions-item>
            <el-descriptions-item label="里程">{{ result.input_params?.mileage }} 万公里</el-descriptions-item>
            <el-descriptions-item label="新车指导价">{{ result.input_params?.original_price }} 万</el-descriptions-item>
            <el-descriptions-item label="变速箱">{{ result.input_params?.gearbox }}</el-descriptions-item>
            <el-descriptions-item label="燃油类型">{{ result.input_params?.fuel_type }}</el-descriptions-item>
            <el-descriptions-item label="排量">{{ result.input_params?.displacement }}</el-descriptions-item>
            <el-descriptions-item label="城市">{{ result.input_params?.city }}</el-descriptions-item>
          </el-descriptions>

          <el-divider />

          <div class="result-meta">
            <el-tag :type="result.model_type === 'sklearn' ? 'success' : 'warning'">
              模型：{{ result.model_type === 'sklearn' ? 'Scikit-learn 随机森林' : 'Spark MLlib 随机森林' }}
            </el-tag>
            <el-tag type="primary">置信度：{{ (result.confidence * 100).toFixed(0) }}%</el-tag>
          </div>
        </div>

        <!-- 未预测时的占位 -->
        <div class="card placeholder-card" v-else>
          <el-empty description="请在左侧填写车辆信息，点击开始预测">
            <template #image>
              <el-icon :size="80" color="#c0c4cc"><DataAnalysis /></el-icon>
            </template>
          </el-empty>
        </div>

        <!-- 模型信息 -->
        <div class="card" style="margin-top:20px">
          <div class="card-title">模型信息</div>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="模型状态">
              <el-tag :type="modelInfo.model_loaded ? 'success' : 'danger'">
                {{ modelInfo.model_loaded ? '已加载' : '未加载(使用兜底)' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="模型类型">{{ modelInfo.model_type }}</el-descriptions-item>
            <el-descriptions-item label="树数量" v-if="modelInfo.n_estimators">{{ modelInfo.n_estimators }}</el-descriptions-item>
            <el-descriptions-item label="最大深度" v-if="modelInfo.max_depth">{{ modelInfo.max_depth }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { MagicStick, DataAnalysis } from '@element-plus/icons-vue'
import { predictPrice, getCarBrands, getCarCities, getModelInfo } from '@/api'

const formRef = ref(null)
const loading = ref(false)
const result = ref(null)
const modelInfo = ref({})
const brands = ref([])
const cities = ref([])

const displacements = ['1.0L', '1.2T', '1.4T', '1.5L', '1.5T', '1.6L', '1.8L', '2.0L', '2.0T', '2.5L', '3.0T', '纯电']
const fuelTypes = ['汽油', '柴油', '纯电动', '混合动力', '插电混动']

const form = reactive({
  brand: '大众',
  age: 3,
  mileage: 5.0,
  original_price: 16.0,
  gearbox: '自动',
  displacement: '1.4T',
  fuel_type: '汽油',
  city: '北京',
  model_type: 'sklearn'
})

const rules = {
  brand: [{ required: true, message: '请选择品牌', trigger: 'change' }],
  age: [{ required: true, message: '请输入车龄', trigger: 'blur' }],
  mileage: [{ required: true, message: '请输入里程', trigger: 'blur' }]
}

const loadBrands = async () => {
  try {
    const res = await getCarBrands()
    brands.value = res.brands || []
  } catch (e) {
    brands.value = ['大众', '丰田', '本田', '日产', '别克', '奥迪', '宝马', '奔驰', '比亚迪', '特斯拉']
  }
}

const loadCities = async () => {
  try {
    const res = await getCarCities()
    cities.value = res.cities || []
  } catch (e) {
    cities.value = ['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '西安', '南京', '重庆']
  }
}

const loadModelInfo = async () => {
  try {
    const res = await getModelInfo()
    if (res.code === 200) modelInfo.value = res.data
  } catch (e) {
    modelInfo.value = { model_loaded: false, model_type: 'fallback' }
  }
}

const handlePredict = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    result.value = null
    try {
      const res = await predictPrice({ ...form })
      if (res.code === 200) {
        result.value = res.data
        ElMessage.success('预测完成')
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

onMounted(() => {
  loadBrands()
  loadCities()
  loadModelInfo()
})
</script>

<style scoped>
.predict-page { padding: 0; }

.result-card { min-height: 400px; }

.result-main { text-align: center; padding: 20px 0; }

.result-price { margin-bottom: 16px; }

.price-label {
  display: block;
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.price-value {
  font-size: 56px;
  font-weight: 700;
  color: #F56C6C;
  line-height: 1;
}

.price-unit {
  font-size: 20px;
  color: #F56C6C;
  margin-left: 4px;
}

.result-range { margin-top: 12px; }

.result-meta {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.placeholder-card {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>

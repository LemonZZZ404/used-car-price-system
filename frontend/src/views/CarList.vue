<template>
  <div class="car-list-page">
    <!-- 搜索筛选区 -->
    <div class="card filter-card">
      <el-form :inline="true" :model="filterForm" size="default">
        <el-form-item label="品牌">
          <el-select v-model="filterForm.brand" placeholder="全部品牌" clearable filterable style="width:160px">
            <el-option v-for="b in brands" :key="b" :label="b" :value="b" />
          </el-select>
        </el-form-item>
        <el-form-item label="价格区间">
          <el-input-number v-model="filterForm.min_price" :min="0" :max="500" placeholder="最低" style="width:120px" />
          <span style="margin:0 8px">-</span>
          <el-input-number v-model="filterForm.max_price" :min="0" :max="500" placeholder="最高" style="width:120px" />
        </el-form-item>
        <el-form-item label="车龄">
          <el-input-number v-model="filterForm.min_age" :min="0" :max="30" placeholder="最低" style="width:100px" />
          <span style="margin:0 8px">-</span>
          <el-input-number v-model="filterForm.max_age" :min="0" :max="30" placeholder="最高" style="width:100px" />
        </el-form-item>
        <el-form-item label="变速箱">
          <el-select v-model="filterForm.gearbox" placeholder="全部" clearable style="width:120px">
            <el-option label="自动" value="自动" />
            <el-option label="手动" value="手动" />
          </el-select>
        </el-form-item>
        <el-form-item label="燃油类型">
          <el-select v-model="filterForm.fuel_type" placeholder="全部" clearable style="width:120px">
            <el-option v-for="f in fuelTypes" :key="f" :label="f" :value="f" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 车辆列表 -->
    <div class="card" style="margin-top:20px">
      <div class="card-title">车辆列表（共 {{ total }} 条）</div>
      <el-table :data="tableData" v-loading="loading" stripe border size="default">
        <el-table-column prop="car_id" label="车辆编号" width="120" />
        <el-table-column prop="brand" label="品牌" width="80" />
        <el-table-column prop="series" label="车系" width="100" />
        <el-table-column prop="model" label="车型" min-width="180" show-overflow-tooltip />
        <el-table-column prop="price" label="售价(万)" width="100" sortable>
          <template #default="{ row }">
            <span style="color:#F56C6C;font-weight:600">{{ row.price }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="age" label="车龄" width="70">
          <template #default="{ row }">{{ row.age }}年</template>
        </el-table-column>
        <el-table-column prop="mileage" label="里程(万)" width="90" />
        <el-table-column prop="gearbox" label="变速箱" width="80" />
        <el-table-column prop="fuel_type" label="燃油类型" width="90" />
        <el-table-column prop="city" label="城市" width="80" />
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'
import { getCarList, getCarBrands } from '@/api'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const brands = ref([])
const fuelTypes = ['汽油', '柴油', '纯电动', '混合动力', '插电混动']

const filterForm = reactive({
  brand: '',
  min_price: null,
  max_price: null,
  min_age: null,
  max_age: null,
  gearbox: '',
  fuel_type: ''
})

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
      ...filterForm
    }
    // 清理空值
    Object.keys(params).forEach(k => {
      if (params[k] === '' || params[k] === null || params[k] === undefined) delete params[k]
    })
    const res = await getCarList(params)
    tableData.value = res.results || res.data || []
    total.value = res.count || 0
  } catch (e) {
    console.error('加载车辆列表失败', e)
    // 模拟数据
    tableData.value = generateMockData()
    total.value = 100
  } finally {
    loading.value = false
  }
}

const generateMockData = () => {
  const brands = ['大众', '丰田', '本田', '宝马', '奔驰', '奥迪', '比亚迪', '特斯拉']
  return Array.from({ length: 20 }, (_, i) => ({
    car_id: `CAR${String(i + 1).padStart(8, '0')}`,
    brand: brands[i % brands.length],
    series: '示例车系',
    model: '示例车型 2020款 自动豪华版',
    price: (Math.random() * 30 + 5).toFixed(2),
    age: Math.floor(Math.random() * 15),
    mileage: (Math.random() * 20).toFixed(1),
    gearbox: Math.random() > 0.3 ? '自动' : '手动',
    fuel_type: '汽油',
    city: '北京'
  }))
}

const loadBrands = async () => {
  try {
    const res = await getCarBrands()
    brands.value = res.brands || []
  } catch (e) {
    brands.value = ['大众', '丰田', '本田', '日产', '别克', '奥迪', '宝马', '奔驰', '比亚迪', '特斯拉']
  }
}

const handleSearch = () => {
  page.value = 1
  loadData()
}

const handleReset = () => {
  Object.assign(filterForm, {
    brand: '', min_price: null, max_price: null,
    min_age: null, max_age: null, gearbox: '', fuel_type: ''
  })
  page.value = 1
  loadData()
}

onMounted(() => {
  loadBrands()
  loadData()
})
</script>

<style scoped>
.filter-card { margin-bottom: 0; }
.pagination { margin-top: 20px; display: flex; justify-content: flex-end; }
</style>

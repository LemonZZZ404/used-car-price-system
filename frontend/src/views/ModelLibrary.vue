<template>
  <div class="library-page">
    <div class="hero card">
      <div class="hero-left">
        <div class="hero-icon"><el-icon :size="28"><Collection /></el-icon></div>
        <div>
          <h2>车型库</h2>
          <p>共 {{ total }} 个车系 · 点击卡片查看车系行情详情</p>
        </div>
      </div>
      <div class="hero-search">
        <el-select v-model="brand" placeholder="全部品牌" clearable filterable style="width: 140px" @change="reload">
          <el-option v-for="b in brands" :key="b" :label="b" :value="b" />
        </el-select>
        <el-input v-model="q" placeholder="搜索车系，如：朗逸" clearable style="width: 200px" @keyup.enter="reload" @clear="reload">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button type="primary" @click="reload">搜索</el-button>
      </div>
    </div>

    <div v-if="loading" class="card empty-card"><el-icon class="is-loading" :size="36"><Loading /></el-icon><p>加载中...</p></div>

    <template v-else>
      <el-row :gutter="16">
        <el-col :xs="12" :sm="8" :md="6" v-for="s in items" :key="s.brand + s.series">
          <div class="card series-card" @click="goDetail(s)">
            <div class="s-brand">{{ s.brand }}</div>
            <div class="s-name">{{ s.series }}</div>
            <div class="s-price"><b>{{ s.avg_price }}</b> 万均价<small v-if="s.min_price !== s.max_price">（{{ s.min_price }}~{{ s.max_price }}万）</small></div>
            <div class="s-meta">
              <span>{{ s.count }} 辆在售</span>
              <span v-if="s.avg_age !== null">均 {{ s.avg_age }} 年</span>
            </div>
          </div>
        </el-col>
      </el-row>

      <div class="load-more" v-if="items.length < total">
        <el-button :loading="loadingMore" round @click="loadMore">加载更多（{{ total - items.length }}）</el-button>
      </div>
      <div class="card empty-card" v-if="!items.length">
        <el-icon :size="44" class="dim"><Search /></el-icon>
        <p>没有匹配的车系，换个关键词试试</p>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Collection, Search, Loading } from '@element-plus/icons-vue'
import { getSeriesList } from '@/api'

const router = useRouter()
const q = ref('')
const brand = ref('')
const items = ref([])
const brands = ref([])
const total = ref(0)
const loading = ref(false)
const loadingMore = ref(false)

const fetchList = async (offset = 0) => {
  const res = await getSeriesList({
    q: q.value || undefined,
    brand: brand.value || undefined,
    limit: 40, offset,
  })
  if (offset === 0) {
    items.value = res.data.items
    if (res.data.brands?.length) brands.value = res.data.brands
  } else {
    items.value = items.value.concat(res.data.items)
  }
  total.value = res.data.total
}

const reload = async () => {
  loading.value = true
  try { await fetchList(0) } finally { loading.value = false }
}

const loadMore = async () => {
  loadingMore.value = true
  try { await fetchList(items.value.length) } finally { loadingMore.value = false }
}

const goDetail = (s) => {
  router.push({ path: `/models/${encodeURIComponent(s.series)}`, query: { brand: s.brand } })
}

onMounted(reload)
</script>

<style scoped>
.library-page { max-width: 1400px; margin: 0 auto; }
.hero { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; padding: 22px 26px; margin-bottom: 20px; }
.hero-left { display: flex; align-items: center; gap: 14px; }
.hero-icon {
  width: 52px; height: 52px; border-radius: 13px;
  background: linear-gradient(135deg, #8B5CF6, #A78BFA);
  display: flex; align-items: center; justify-content: center; color: #fff;
  box-shadow: 0 6px 16px rgba(139, 92, 246, 0.35);
}
.hero h2 { margin: 0 0 4px; font-size: 20px; color: var(--text-primary); }
.hero p { margin: 0; font-size: 13px; color: var(--text-secondary); }
.hero-search { display: flex; gap: 10px; }

.series-card { padding: 18px; cursor: pointer; transition: all 0.22s; border-left: 3px solid #8B5CF6; }
.series-card:hover { transform: translateY(-4px); box-shadow: 0 10px 26px rgba(0, 0, 0, 0.12); border-left-color: #2D6BFF; }
.s-brand { font-size: 12px; color: var(--text-secondary); margin-bottom: 4px; }
.s-name { font-size: 16px; font-weight: 700; color: var(--text-primary); margin-bottom: 10px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.s-price { margin-bottom: 10px; }
.s-price b {
  font-size: 22px; font-weight: 800;
  background: linear-gradient(90deg, #2D6BFF, #8B5CF6);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.s-price small { font-size: 11px; color: var(--text-secondary); margin-left: 4px; }
.s-meta { display: flex; justify-content: space-between; font-size: 12px; color: var(--text-secondary); }

.empty-card { padding: 60px 20px; text-align: center; color: var(--text-secondary); }
.empty-card p { margin: 10px 0 0; font-size: 14px; }
.dim { opacity: 0.35; }
.load-more { text-align: center; margin: 6px 0 26px; }
</style>

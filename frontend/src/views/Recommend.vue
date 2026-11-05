<template>
  <div class="recommend-page">
    <!-- 顶部 Hero -->
    <div class="hero card">
      <div class="hero-left">
        <div class="hero-icon">
          <el-icon :size="30"><Aim /></el-icon>
        </div>
        <div>
          <h2>智能选车</h2>
          <p>告诉我预算和用车场景，从 {{ totalHint }} 在售车源中为你挑出最合适的几款</p>
        </div>
      </div>
    </div>

    <el-row :gutter="20">
      <!-- 左侧：需求表单 -->
      <el-col :xs="24" :md="9">
        <div class="card form-card">
          <div class="card-title">
            <el-icon><EditPen /></el-icon>
            <span>你的需求</span>
          </div>
          <el-form label-position="top">
            <el-form-item label="预算范围（万元）">
              <div class="budget-row">
                <el-input-number v-model="form.budget_min" :min="1" :max="form.budget_max" :step="1" controls-position="right" />
                <span class="budget-sep">至</span>
                <el-input-number v-model="form.budget_max" :min="form.budget_min" :max="200" :step="1" controls-position="right" />
              </div>
              <el-slider
                v-model="budgetRange"
                range
                :min="1"
                :max="100"
                :format-tooltip="v => v + ' 万'"
                class="budget-slider"
              />
            </el-form-item>

            <el-form-item label="用车场景">
              <div class="scene-grid">
                <div
                  v-for="s in scenes"
                  :key="s.value"
                  class="scene-item"
                  :class="{ active: form.scene === s.value }"
                  @click="form.scene = s.value"
                >
                  <el-icon :size="22"><component :is="s.icon" /></el-icon>
                  <span class="scene-name">{{ s.label }}</span>
                  <span class="scene-desc">{{ s.desc }}</span>
                </div>
              </div>
            </el-form-item>

            <el-form-item label="燃油类型">
              <el-radio-group v-model="form.fuel_type">
                <el-radio-button value="">不限</el-radio-button>
                <el-radio-button value="汽油">汽油</el-radio-button>
                <el-radio-button value="纯电动">纯电</el-radio-button>
                <el-radio-button value="混合动力">混动</el-radio-button>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="最大车龄">
              <el-slider v-model="form.max_age" :min="1" :max="15" :format-tooltip="v => v + ' 年'" show-input />
            </el-form-item>

            <el-button
              type="primary"
              size="large"
              class="recommend-btn"
              :loading="loading"
              @click="handleRecommend"
            >
              <el-icon style="margin-right:6px"><MagicStick /></el-icon>
              为我推荐
            </el-button>
          </el-form>
        </div>
      </el-col>

      <!-- 右侧：推荐结果 -->
      <el-col :xs="24" :md="15">
        <div v-if="!hasResult && !loading" class="card empty-card">
          <el-icon :size="56" class="empty-icon"><Aim /></el-icon>
          <p>填写左侧需求，点击「为我推荐」</p>
          <span>系统会按场景打分并给出推荐理由</span>
        </div>

        <div v-else-if="loading" class="card empty-card">
          <el-icon class="is-loading" :size="40"><Loading /></el-icon>
          <p>正在从车源库中筛选打分...</p>
        </div>

        <template v-else>
          <div class="result-summary">
            <span>为你找到 <b>{{ results.length }}</b> 款匹配车型，按推荐度排序</span>
            <el-tag size="small" effect="plain" round>{{ sceneLabel }}场景</el-tag>
          </div>
          <transition-group name="list" tag="div" class="result-list">
            <div
              v-for="(car, i) in results"
              :key="car.car_id || i"
              class="card car-card"
            >
              <div class="rank-badge" :class="'rank-' + (i + 1)" v-if="i < 3">{{ i + 1 }}</div>
              <div class="rank-badge rank-normal" v-else>{{ i + 1 }}</div>

              <div class="car-main">
                <div class="car-title">
                  <span class="car-brand">{{ car.brand }}</span>
                  <span class="car-series">{{ car.series }}</span>
                </div>
                <div class="car-tags">
                  <el-tag size="small" effect="plain">{{ car.age }} 年车龄</el-tag>
                  <el-tag size="small" effect="plain">{{ car.mileage }} 万公里</el-tag>
                  <el-tag size="small" effect="plain">{{ car.fuel_type }}</el-tag>
                  <el-tag size="small" effect="plain">{{ car.city }}</el-tag>
                </div>
                <div class="car-reasons" v-if="car.reasons && car.reasons.length">
                  <div v-for="(r, ri) in car.reasons" :key="ri" class="reason-item">
                    <el-icon color="#67C23A"><CircleCheckFilled /></el-icon>
                    <span>{{ r }}</span>
                  </div>
                </div>
              </div>

              <div class="car-side">
                <div class="car-price">{{ car.price }}<small>万</small></div>
                <div class="score-ring">
                  <el-progress
                    type="circle"
                    :percentage="car.score"
                    :width="64"
                    :stroke-width="6"
                    :color="scoreColor"
                  >
                    <template #default>
                      <span class="score-num">{{ car.score }}</span>
                    </template>
                  </el-progress>
                  <span class="score-label">推荐度</span>
                </div>
              </div>
            </div>
          </transition-group>
        </template>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Aim, EditPen, MagicStick, Loading, CircleCheckFilled,
  Van, OfficeBuilding, Trophy, Coin, Star
} from '@element-plus/icons-vue'
import { recommendCars } from '@/api'

const totalHint = '10万+'

const budgetRange = computed({
  get: () => [form.budget_min, form.budget_max],
  set: (v) => { form.budget_min = v[0]; form.budget_max = v[1] }
})

const scenes = [
  { value: 'family', label: '家用代步', desc: '空间大·省心耐用', icon: Van },
  { value: 'business', label: '商务出行', desc: '品牌体面·舒适', icon: OfficeBuilding },
  { value: 'sport', label: '运动操控', desc: '动力强·驾驶乐趣', icon: Trophy },
  { value: 'economy', label: '经济实惠', desc: '油耗低·保值', icon: Coin },
  { value: 'newbie', label: '新手练手', desc: '便宜·刮蹭不心疼', icon: Star },
]

const form = reactive({
  budget_min: 8,
  budget_max: 20,
  scene: 'family',
  fuel_type: '',
  max_age: 8,
})

const loading = ref(false)
const hasResult = ref(false)
const results = ref([])
const totalCandidates = ref(0)

const sceneLabel = computed(() => scenes.find(s => s.value === form.scene)?.label || '')

const scoreColor = (p) => {
  if (p >= 90) return '#F56C6C'
  if (p >= 75) return '#E6A23C'
  return '#2D6BFF'
}

const handleRecommend = async () => {
  if (form.budget_min >= form.budget_max) {
    ElMessage.warning('预算下限需小于上限')
    return
  }
  loading.value = true
  try {
    const res = await recommendCars({
      budget_min: form.budget_min,
      budget_max: form.budget_max,
      scene: form.scene,
      fuel_type: form.fuel_type || undefined,
      max_age: form.max_age,
      limit: 10,
    })
    // 后端返回 {code, data: {scene, budget, total_candidates, items}}，取 items 字段
    results.value = res.data?.items || []
    totalCandidates.value = res.data?.total_candidates ?? 0
    hasResult.value = true
    if (!results.value.length) {
      ElMessage.info('当前条件下没有匹配车源，试试放宽预算或车龄')
    }
  } catch (e) {
    ElMessage.error('推荐失败，请稍后重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.recommend-page { max-width: 1400px; margin: 0 auto; }

.hero {
  display: flex; align-items: center; justify-content: space-between;
  padding: 24px 28px; margin-bottom: 20px;
}
.hero-left { display: flex; align-items: center; gap: 16px; }
.hero-icon {
  width: 56px; height: 56px; border-radius: 14px;
  background: linear-gradient(135deg, #F56C6C, #F78989);
  display: flex; align-items: center; justify-content: center; color: #fff;
  box-shadow: 0 6px 16px rgba(245, 108, 108, 0.35);
}
.hero h2 { margin: 0 0 4px; font-size: 20px; color: var(--text-primary); }
.hero p { margin: 0; font-size: 13px; color: var(--text-secondary); }

.form-card { padding: 22px; }
.card-title {
  display: flex; align-items: center; gap: 8px;
  font-size: 15px; font-weight: 600; color: var(--text-primary);
  margin-bottom: 18px;
}

.budget-row { display: flex; align-items: center; gap: 10px; width: 100%; }
.budget-row .el-input-number { flex: 1; }
.budget-sep { color: var(--text-secondary); }
.budget-slider { margin-top: 12px; }

.scene-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 10px; width: 100%;
}
.scene-item {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  padding: 14px 6px; border-radius: 12px; cursor: pointer;
  border: 1.5px solid var(--border-color);
  transition: all 0.2s; color: var(--text-secondary);
}
.scene-item:hover { border-color: #F56C6C; transform: translateY(-2px); }
.scene-item.active {
  border-color: #F56C6C;
  background: rgba(245, 108, 108, 0.08);
  color: #F56C6C;
}
.scene-name { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.scene-item.active .scene-name { color: #F56C6C; }
.scene-desc { font-size: 11px; opacity: 0.75; text-align: center; }

.recommend-btn {
  width: 100%; height: 44px; font-size: 15px; border-radius: 10px;
  background: linear-gradient(90deg, #F56C6C, #F78989);
  border: none;
}
.recommend-btn:hover { opacity: 0.9; }

.empty-card {
  padding: 80px 20px; text-align: center; color: var(--text-secondary);
  display: flex; flex-direction: column; align-items: center; gap: 10px;
}
.empty-icon { opacity: 0.3; }
.empty-card p { margin: 0; font-size: 15px; }
.empty-card span { font-size: 12px; opacity: 0.7; }

.result-summary {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 14px; color: var(--text-secondary); font-size: 14px;
}
.result-summary b { color: #F56C6C; font-size: 18px; }

.result-list { display: flex; flex-direction: column; gap: 14px; }

.car-card {
  display: flex; align-items: center; gap: 18px;
  padding: 18px 22px; position: relative;
  transition: transform 0.2s, box-shadow 0.2s;
}
.car-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.1); }

.rank-badge {
  width: 34px; height: 34px; border-radius: 10px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 15px; color: #fff;
}
.rank-1 { background: linear-gradient(135deg, #F7B500, #FDCB45); box-shadow: 0 4px 10px rgba(247,181,0,0.4); }
.rank-2 { background: linear-gradient(135deg, #9DA7B5, #C3CCD8); box-shadow: 0 4px 10px rgba(157,167,181,0.4); }
.rank-3 { background: linear-gradient(135deg, #CD7F32, #E2A76D); box-shadow: 0 4px 10px rgba(205,127,50,0.4); }
.rank-normal { background: var(--fill-color, #e5e9f2); color: var(--text-secondary); }

.car-main { flex: 1; min-width: 0; }
.car-title { display: flex; align-items: baseline; gap: 8px; margin-bottom: 8px; }
.car-brand { font-size: 17px; font-weight: 700; color: var(--text-primary); }
.car-series { font-size: 14px; color: var(--text-secondary); }
.car-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }

.car-reasons { display: flex; flex-direction: column; gap: 4px; }
.reason-item {
  display: flex; align-items: center; gap: 6px;
  font-size: 12.5px; color: var(--text-secondary);
}

.car-side {
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  flex-shrink: 0;
}
.car-price {
  font-size: 26px; font-weight: 800;
  background: linear-gradient(90deg, #F56C6C, #E6A23C);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.car-price small { font-size: 13px; margin-left: 2px; }
.score-ring { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.score-num { font-size: 16px; font-weight: 700; color: var(--text-primary); }
.score-label { font-size: 11px; color: var(--text-secondary); }

.list-enter-active { transition: all 0.35s ease; }
.list-enter-from { opacity: 0; transform: translateY(16px); }

@media (max-width: 768px) {
  .car-card { flex-direction: column; align-items: flex-start; }
  .car-side { flex-direction: row; width: 100%; justify-content: space-between; }
}
</style>

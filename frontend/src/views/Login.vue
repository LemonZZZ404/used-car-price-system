<template>
  <div class="login-page">
    <!-- 背景装饰 -->
    <div class="bg-grid"></div>
    <div class="bg-glow glow-1"></div>
    <div class="bg-glow glow-2"></div>

    <div class="login-shell">
      <!-- 左侧品牌区 -->
      <div class="brand-panel">
        <div class="brand-logo">
          <div class="brand-icon"><el-icon :size="24"><Van /></el-icon></div>
          <div class="brand-name">CarValue <span>Analytics</span></div>
        </div>

        <h1 class="brand-title">二手车价格评估系统</h1>
        <p class="brand-sub">海量车源数据 × 机器学习估价模型 × 实时行情监控</p>

        <ul class="brand-features">
          <li>
            <span class="feat-icon"><el-icon :size="16"><DataAnalysis /></el-icon></span>
            <div>
              <b>百万级车源样本</b>
              <i>Spark 离线聚合 + Kafka 实时管道双链路</i>
            </div>
          </li>
          <li>
            <span class="feat-icon"><el-icon :size="16"><Cpu /></el-icon></span>
            <div>
              <b>智能估价引擎</b>
              <i>输出置信度与 P10/P90 价格区间，拒绝拍脑袋</i>
            </div>
          </li>
          <li>
            <span class="feat-icon"><el-icon :size="16"><TrendCharts /></el-icon></span>
            <div>
              <b>行情趋势洞察</b>
              <i>贬值曲线、比价分位、区域热度一目了然</i>
            </div>
          </li>
        </ul>

        <div class="brand-stats">
          <div class="stat">
            <div class="stat-num">100<i>万+</i></div>
            <div class="stat-label">在库车源</div>
          </div>
          <div class="stat-line"></div>
          <div class="stat">
            <div class="stat-num">97<i>%</i></div>
            <div class="stat-label">估价置信度</div>
          </div>
          <div class="stat-line"></div>
          <div class="stat">
            <div class="stat-num">24<i>月</i></div>
            <div class="stat-label">行情走势</div>
          </div>
        </div>
      </div>

      <!-- 右侧表单区 -->
      <div class="form-panel">
        <div class="form-head">
          <div class="form-title">欢迎登录</div>
          <div class="form-desc">请选择身份并输入账号信息</div>
        </div>

        <!-- 角色切换 -->
        <div class="role-switch">
          <div class="role-item" :class="{ active: role === 'user' }" @click="switchRole('user')">
            <el-icon :size="15"><User /></el-icon>
            <span>普通用户</span>
          </div>
          <div class="role-item" :class="{ active: role === 'admin' }" @click="switchRole('admin')">
            <el-icon :size="15"><Setting /></el-icon>
            <span>管理员</span>
          </div>
        </div>

        <el-form ref="formRef" :model="form" :rules="rules" size="large" @keyup.enter="handleLogin">
          <el-form-item prop="username">
            <el-input v-model="form.username" placeholder="用户名" :prefix-icon="User" clearable />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="form.password" type="password" placeholder="密码" :prefix-icon="Lock" show-password />
          </el-form-item>
          <el-button type="primary" class="login-btn" :loading="loading" @click="handleLogin">
            {{ loading ? '登录中...' : '进入系统' }}
          </el-button>
        </el-form>

        <!-- 演示账号快捷提示 -->
        <div class="demo-box">
          <div class="demo-title">演示账号（点击自动填充）</div>
          <div class="demo-row">
            <div class="demo-chip" @click="fillAccount('user', '123456')">
              <span class="chip-tag user">用户</span>user / 123456
            </div>
            <div class="demo-chip" @click="fillAccount('admin', '200412230')">
              <span class="chip-tag admin">管理</span>admin / 200412230
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="page-foot">Used-Car Price Evaluation · Big Data Platform</div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Van, Setting, DataAnalysis, Cpu, TrendCharts } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref(null)
const loading = ref(false)
const role = ref('user')

const form = reactive({ username: 'user', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const switchRole = (r) => {
  if (role.value === r) return
  role.value = r
  form.username = r === 'admin' ? 'admin' : 'user'
  form.password = ''
}

const fillAccount = (u, p) => {
  role.value = u === 'admin' ? 'admin' : 'user'
  form.username = u
  form.password = p
}

const handleLogin = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const res = await userStore.login(form.username, form.password)
      if (res.code === 200) {
        ElMessage.success(`欢迎回来，${res.data.user.username}`)
        router.push('/dashboard')
      }
    } catch (e) { /* 错误提示由拦截器处理 */ }
    finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(150deg, #0A1128 0%, #0F172A 45%, #132447 100%);
  position: relative;
  overflow: hidden;
  font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* 网格纹理 */
.bg-grid {
  position: absolute; inset: 0;
  background-image:
    linear-gradient(rgba(91, 140, 255, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(91, 140, 255, 0.05) 1px, transparent 1px);
  background-size: 42px 42px;
  mask-image: radial-gradient(ellipse 70% 60% at 50% 45%, #000 30%, transparent 100%);
}

.bg-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(10px);
}
.glow-1 {
  width: 560px; height: 560px; top: -180px; right: -120px;
  background: radial-gradient(circle, rgba(45, 107, 255, 0.22), transparent 65%);
  animation: drift 12s ease-in-out infinite alternate;
}
.glow-2 {
  width: 460px; height: 460px; bottom: -160px; left: -100px;
  background: radial-gradient(circle, rgba(91, 140, 255, 0.16), transparent 65%);
  animation: drift 9s ease-in-out infinite alternate-reverse;
}
@keyframes drift {
  from { transform: translate(0, 0) scale(1); }
  to { transform: translate(40px, 26px) scale(1.08); }
}

.login-shell {
  display: flex;
  width: 980px;
  max-width: calc(100vw - 32px);
  min-height: 560px;
  border-radius: 20px;
  overflow: hidden;
  background: rgba(17, 28, 54, 0.72);
  backdrop-filter: blur(18px);
  border: 1px solid rgba(91, 140, 255, 0.18);
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.45);
  position: relative;
  z-index: 1;
}

/* ============ 左侧品牌区 ============ */
.brand-panel {
  flex: 1.15;
  padding: 44px 40px 36px;
  display: flex;
  flex-direction: column;
  background:
    radial-gradient(circle at 80% 0%, rgba(45, 107, 255, 0.16), transparent 55%),
    linear-gradient(160deg, rgba(26, 43, 77, 0.6), rgba(10, 17, 40, 0.6));
  border-right: 1px solid rgba(91, 140, 255, 0.12);
}

.brand-logo { display: flex; align-items: center; gap: 12px; margin-bottom: 40px; }
.brand-icon {
  width: 44px; height: 44px; border-radius: 12px;
  background: linear-gradient(135deg, #2D6BFF, #5B8CFF);
  display: flex; align-items: center; justify-content: center;
  color: #fff; box-shadow: 0 6px 18px rgba(45, 107, 255, 0.45);
}
.brand-name { font-size: 16px; font-weight: 700; color: #E8F0FF; letter-spacing: 0.5px; }
.brand-name span { color: #5B8CFF; font-weight: 400; }

.brand-title { font-size: 28px; font-weight: 800; color: #F3F6FF; letter-spacing: 1px; margin: 0 0 12px; }
.brand-sub { font-size: 13.5px; color: #8FA3C8; margin: 0 0 34px; letter-spacing: 0.5px; }

.brand-features { list-style: none; margin: 0 0 auto; padding: 0; display: flex; flex-direction: column; gap: 20px; }
.brand-features li { display: flex; gap: 14px; align-items: flex-start; }
.feat-icon {
  width: 34px; height: 34px; flex-shrink: 0; border-radius: 9px;
  background: rgba(45, 107, 255, 0.14);
  border: 1px solid rgba(91, 140, 255, 0.25);
  color: #7DA3FF;
  display: flex; align-items: center; justify-content: center;
}
.brand-features b { display: block; font-size: 14px; color: #E2E8F0; font-weight: 600; }
.brand-features i { display: block; font-style: normal; font-size: 12px; color: #7488AB; margin-top: 3px; }

.brand-stats { display: flex; align-items: center; gap: 18px; margin-top: 34px; padding-top: 22px; border-top: 1px solid rgba(91, 140, 255, 0.14); }
.stat { text-align: left; }
.stat-num { font-size: 24px; font-weight: 800; color: #F3F6FF; }
.stat-num i { font-style: normal; font-size: 13px; color: #5B8CFF; margin-left: 2px; }
.stat-label { font-size: 11.5px; color: #7488AB; margin-top: 2px; }
.stat-line { width: 1px; height: 30px; background: rgba(91, 140, 255, 0.2); }

/* ============ 右侧表单区 ============ */
.form-panel {
  width: 380px;
  flex-shrink: 0;
  padding: 48px 40px 36px;
  display: flex;
  flex-direction: column;
}

.form-title { font-size: 24px; font-weight: 700; color: #F3F6FF; }
.form-desc { font-size: 13px; color: #7488AB; margin-top: 8px; margin-bottom: 26px; }

.role-switch {
  display: flex;
  background: rgba(10, 17, 40, 0.6);
  border: 1px solid rgba(91, 140, 255, 0.15);
  border-radius: 10px;
  padding: 4px;
  margin-bottom: 24px;
}
.role-item {
  flex: 1;
  display: flex; align-items: center; justify-content: center; gap: 6px;
  height: 36px; border-radius: 7px;
  font-size: 13.5px; font-weight: 500; color: #7488AB;
  cursor: pointer; transition: all 0.2s; user-select: none;
}
.role-item.active {
  background: linear-gradient(135deg, #2D6BFF, #4A7DFF);
  color: #fff; font-weight: 600;
  box-shadow: 0 4px 12px rgba(45, 107, 255, 0.35);
}
.role-item:not(.active):hover { color: #B8C7E5; }

.form-panel :deep(.el-input__wrapper) {
  background: rgba(10, 17, 40, 0.6);
  box-shadow: 0 0 0 1px rgba(91, 140, 255, 0.2) inset;
  border-radius: 9px;
}
.form-panel :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1.5px rgba(91, 140, 255, 0.55) inset;
}
.form-panel :deep(.el-input__inner) { color: #E2E8F0; }
.form-panel :deep(.el-input__inner::placeholder) { color: #5A6B8C; }
.form-panel :deep(.el-input__prefix) { color: #7488AB; }
.form-panel :deep(.el-form-item) { margin-bottom: 18px; }

.login-btn {
  width: 100%;
  height: 46px;
  margin-top: 6px;
  font-size: 15.5px;
  font-weight: 600;
  letter-spacing: 6px;
  border: none;
  background: linear-gradient(90deg, #2D6BFF, #4A7DFF);
  box-shadow: 0 8px 20px rgba(45, 107, 255, 0.35);
  transition: all 0.25s;
}
.login-btn:hover {
  background: linear-gradient(90deg, #3D6BFF, #5B8CFF);
  box-shadow: 0 10px 26px rgba(45, 107, 255, 0.5);
  transform: translateY(-1px);
}

/* 演示账号 */
.demo-box {
  margin-top: auto;
  padding-top: 20px;
  border-top: 1px dashed rgba(91, 140, 255, 0.2);
}
.demo-title { font-size: 11.5px; color: #5A6B8C; margin-bottom: 10px; letter-spacing: 0.5px; }
.demo-row { display: flex; flex-direction: column; gap: 8px; }
.demo-chip {
  display: flex; align-items: center; gap: 8px;
  font-size: 12.5px; color: #A9B9D8; font-family: Consolas, Monaco, monospace;
  background: rgba(10, 17, 40, 0.5);
  border: 1px solid rgba(91, 140, 255, 0.14);
  border-radius: 8px; padding: 8px 12px;
  cursor: pointer; transition: all 0.2s;
}
.demo-chip:hover {
  border-color: rgba(91, 140, 255, 0.45);
  background: rgba(45, 107, 255, 0.1);
  color: #E2E8F0;
}
.chip-tag {
  font-style: normal; font-size: 10.5px; padding: 1px 7px; border-radius: 4px;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
}
.chip-tag.user { background: rgba(91, 140, 255, 0.16); color: #7DA3FF; }
.chip-tag.admin { background: rgba(245, 158, 11, 0.14); color: #F5B84E; }

.page-foot {
  position: absolute; bottom: 18px;
  font-size: 11px; color: #3D4E6E; letter-spacing: 2px;
}

/* 响应式：窄屏隐藏品牌区 */
@media (max-width: 860px) {
  .brand-panel { display: none; }
  .login-shell { width: 420px; }
}
@media (max-width: 460px) {
  .form-panel { width: 100%; padding: 40px 26px 30px; }
}
</style>

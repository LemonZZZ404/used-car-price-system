<template>
  <!-- 公开页（登录页）独立渲染，不套侧边栏主布局 -->
  <router-view v-if="isPublicRoute" />
  <el-container v-else class="app-container">
    <el-aside :width="isCollapse ? '68px' : '220px'" class="sidebar">
      <div class="logo" :class="{ collapsed: isCollapse }">
        <div class="logo-icon">
          <el-icon :size="22"><Van /></el-icon>
        </div>
        <transition name="fade">
          <span v-if="!isCollapse" class="logo-text">二手车价格评估</span>
        </transition>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        :collapse="isCollapse"
        :collapse-transition="false"
        background-color="transparent"
        text-color="var(--sidebar-text)"
        active-text-color="#ffffff"
        class="sidebar-menu"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>数据看板</template>
        </el-menu-item>
        <el-menu-item index="/predict">
          <el-icon><MagicStick /></el-icon>
          <template #title>价格预测</template>
        </el-menu-item>
        <el-menu-item index="/compare">
          <el-icon><ScaleToOriginal /></el-icon>
          <template #title>多车对比</template>
        </el-menu-item>
        <el-menu-item index="/recommend">
          <el-icon><Aim /></el-icon>
          <template #title>智能选车</template>
        </el-menu-item>
        <el-menu-item index="/realtime">
          <el-icon><Monitor /></el-icon>
          <template #title>实时监控</template>
        </el-menu-item>
        <el-menu-item index="/simulator">
          <el-icon><Odometer /></el-icon>
          <template #title>价格试算器</template>
        </el-menu-item>
        <el-menu-item index="/cars">
          <el-icon><List /></el-icon>
          <template #title>车辆列表</template>
        </el-menu-item>
        <el-menu-item index="/history">
          <el-icon><History /></el-icon>
          <template #title>预测历史</template>
        </el-menu-item>

        <div class="menu-divider" v-if="!isCollapse">数据可视化</div>
        <el-menu-item index="/datamap">
          <el-icon><Location /></el-icon>
          <template #title>数据地图</template>
        </el-menu-item>
        <el-menu-item index="/brand-graph">
          <el-icon><Share /></el-icon>
          <template #title>品牌图谱</template>
        </el-menu-item>
        <el-menu-item index="/ranking">
          <el-icon><Trophy /></el-icon>
          <template #title>排行榜中心</template>
        </el-menu-item>
        <el-menu-item index="/market">
          <el-icon><DataLine /></el-icon>
          <template #title>市场行情</template>
        </el-menu-item>
        <el-menu-item index="/models">
          <el-icon><Collection /></el-icon>
          <template #title>车型库</template>
        </el-menu-item>
        <el-menu-item index="/trend">
          <el-icon><Histogram /></el-icon>
          <template #title>行情月报</template>
        </el-menu-item>
        <el-menu-item index="/trend-compare">
          <el-icon><TrendCharts /></el-icon>
          <template #title>走势对比</template>
        </el-menu-item>
        <el-menu-item index="/alerts">
          <el-icon><Bell /></el-icon>
          <template #title>预警中心</template>
        </el-menu-item>

        <div class="menu-divider" v-if="!isCollapse">用户</div>
        <el-menu-item index="/export">
          <el-icon><Files /></el-icon>
          <template #title>导出中心</template>
        </el-menu-item>
        <el-menu-item index="/profile">
          <el-icon><UserFilled /></el-icon>
          <template #title>个人中心</template>
        </el-menu-item>
        <el-menu-item index="/data-dict">
          <el-icon><Collection /></el-icon>
          <template #title>数据字典</template>
        </el-menu-item>
        <el-menu-item index="/help">
          <el-icon><QuestionFilled /></el-icon>
          <template #title>帮助中心</template>
        </el-menu-item>

        <template v-if="userStore.isAdmin">
          <div class="menu-divider" v-if="!isCollapse">模型管理</div>
          <el-menu-item index="/model-analysis">
            <el-icon><TrendCharts /></el-icon>
            <template #title>模型分析</template>
          </el-menu-item>
          <el-menu-item index="/users">
            <el-icon><User /></el-icon>
            <template #title>用户管理</template>
          </el-menu-item>
          <div class="menu-divider" v-if="!isCollapse">大数据链路</div>
          <el-menu-item index="/lineage">
            <el-icon><Connection /></el-icon>
            <template #title>数据血缘</template>
          </el-menu-item>
          <el-menu-item index="/logs">
            <el-icon><FolderOpened /></el-icon>
            <template #title>运维日志</template>
          </el-menu-item>
          <el-menu-item index="/system">
            <el-icon><Monitor /></el-icon>
            <template #title>系统状态</template>
          </el-menu-item>
          <el-menu-item index="/about">
            <el-icon><InfoFilled /></el-icon>
            <template #title>关于项目</template>
          </el-menu-item>
        </template>
      </el-menu>
      <div class="sidebar-footer" v-if="!isCollapse">
        <div class="footer-dot"></div>
        <span>{{ userStore.isAdmin ? '管理员模式' : '用户模式' }}</span>
      </div>
    </el-aside>

    <el-container class="right-container">
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" :size="20" @click="isCollapse = !isCollapse">
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <span class="page-title">{{ pageTitle }}</span>
        </div>
        <div class="header-right">
          <!-- 全局搜索 -->
          <el-autocomplete
            v-model="searchKeyword"
            :fetch-suggestions="searchSuggestions"
            placeholder="搜索品牌/页面..."
            :prefix-icon="Search"
            class="global-search"
            size="small"
            @select="handleSearchSelect"
            clearable
          />
          <el-tag type="primary" effect="light" round class="tech-tag">大数据 + 机器学习</el-tag>
          <!-- 暗黑模式切换 -->
          <el-icon class="dark-toggle" @click="toggleDark">
            <Sunny v-if="isDark" />
            <Moon v-else />
          </el-icon>
          <template v-if="userStore.isLogin">
            <el-tag :type="userStore.isAdmin ? 'danger' : 'success'" effect="dark" size="small" round>
              {{ userStore.isAdmin ? '管理员' : '普通用户' }}
            </el-tag>
            <div class="user-info">
              <el-avatar :size="30" class="user-avatar">{{ userStore.user?.username?.[0]?.toUpperCase() || '管' }}</el-avatar>
              <span>{{ userStore.user?.username }}</span>
              <el-icon class="logout-btn" :size="16" @click="handleLogout" title="退出登录">
                <SwitchButton />
              </el-icon>
            </div>
          </template>
          <template v-else>
            <el-button size="small" type="primary" plain @click="$router.push('/login')">登录</el-button>
          </template>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="page-fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Search, Sunny, Moon, ScaleToOriginal, Aim } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const isCollapse = ref(false)
const isDark = ref(localStorage.getItem('theme') === 'dark')
const searchKeyword = ref('')

const activeMenu = computed(() => route.path)
const pageTitle = computed(() => route.meta.title || '二手车价格评估系统')
// meta.public 的路由（如 /login）不渲染侧边栏/顶栏布局
const isPublicRoute = computed(() => route.meta.public === true)

const toggleDark = () => {
  isDark.value = !isDark.value
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}

const pageRoutes = [
  { path: '/dashboard', name: '数据看板' },
  { path: '/predict', name: '价格预测' },
  { path: '/compare', name: '多车对比' },
  { path: '/recommend', name: '智能选车' },
  { path: '/realtime', name: '实时监控' },
  { path: '/cars', name: '车辆列表' },
  { path: '/history', name: '预测历史' },
  { path: '/ranking', name: '排行榜中心' },
  { path: '/market', name: '市场行情' },
  { path: '/models', name: '车型库' },
  { path: '/trend', name: '行情月报' },
  { path: '/alerts', name: '预警中心' },
  { path: '/profile', name: '个人中心' },
  { path: '/help', name: '帮助中心' },
  { path: '/model-analysis', name: '模型分析' },
  { path: '/lineage', name: '数据血缘' },
  { path: '/system', name: '系统状态' },
  { path: '/about', name: '关于项目' },
]

const brands = ['大众', '宝马', '奔驰', '丰田', '本田', '比亚迪', '奥迪', '日产', '吉利', '现代', '别克', '福特', '特斯拉', '长安', '长城']

const searchSuggestions = (query, cb) => {
  if (!query) return cb([])
  const results = []
  const q = query.toLowerCase()
  pageRoutes.forEach(r => {
    if (r.name.toLowerCase().includes(q) || r.path.includes(q)) {
      results.push({ value: r.name, type: 'page', path: r.path })
    }
  })
  brands.forEach(b => {
    if (b.includes(query)) {
      results.push({ value: `${b} - 车辆列表`, type: 'brand', path: `/cars?brand=${b}` })
    }
  })
  cb(results)
}

const handleSearchSelect = (item) => {
  if (item.path) {
    router.push(item.path)
  }
}

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '退出', cancelButtonText: '取消', type: 'warning'
    })
  } catch (e) { return }
  await userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}

const handleResize = () => { isCollapse.value = window.innerWidth < 900 }

onMounted(() => {
  handleResize()
  window.addEventListener('resize', handleResize)
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
})

onUnmounted(() => { window.removeEventListener('resize', handleResize) })
</script>

<style scoped>
.app-container { height: 100vh; }

.sidebar {
  background: linear-gradient(180deg, var(--sidebar-bg) 0%, var(--sidebar-bg-light) 100%);
  display: flex; flex-direction: column;
  transition: width 0.25s ease;
  overflow: hidden;
}

.logo {
  height: 64px; display: flex; align-items: center; justify-content: center; gap: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08); flex-shrink: 0; white-space: nowrap;
}
.logo.collapsed { gap: 0; }

.logo-icon {
  width: 36px; height: 36px; border-radius: 10px;
  background: linear-gradient(135deg, #2D6BFF, #5B8CFF);
  display: flex; align-items: center; justify-content: center; color: #fff;
  box-shadow: 0 4px 12px rgba(45, 107, 255, 0.4); flex-shrink: 0;
}

.logo-text { color: #fff; font-size: 15px; font-weight: 600; letter-spacing: 0.5px; }

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.sidebar-menu {
  border-right: none; padding: 12px 10px; flex: 1;
  /* 菜单项较多时（23 项 ≈ 1200px）超出视口高度，必须允许内部滚动，
     否则被 .sidebar 的 overflow:hidden 裁掉，底部功能入口不可见 */
  min-height: 0;            /* flex 子项默认 min-height:auto，不加这个 overflow 不生效 */
  overflow-y: auto; overflow-x: hidden;
  scrollbar-width: thin; scrollbar-color: rgba(255, 255, 255, 0.18) transparent;
  --el-menu-bg-color: transparent;
  --el-menu-text-color: var(--sidebar-text);
  --el-menu-active-color: #fff;
}
.sidebar-menu::-webkit-scrollbar { width: 4px; }
.sidebar-menu::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.18); border-radius: 2px; }
.sidebar-menu::-webkit-scrollbar-track { background: transparent; }

.sidebar-menu :deep(.el-menu-item) {
  height: 46px; line-height: 46px; border-radius: 10px; margin-bottom: 4px;
  transition: background 0.2s, color 0.2s;
}
.sidebar-menu :deep(.el-menu-item:hover) { background: rgba(255, 255, 255, 0.08); color: #fff; }
.sidebar-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, #2D6BFF, #4A7DFF);
  box-shadow: 0 4px 12px rgba(45, 107, 255, 0.35); color: #fff;
}
.sidebar-menu :deep(.el-menu-item.is-active .el-icon) { color: #fff; }

.menu-divider { font-size: 11px; color: #64748B; padding: 14px 12px 6px; letter-spacing: 1px; font-weight: 600; }

.sidebar-footer {
  height: 40px; display: flex; align-items: center; justify-content: center; gap: 8px;
  color: var(--sidebar-text); font-size: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.08); flex-shrink: 0;
}

.footer-dot {
  width: 8px; height: 8px; border-radius: 50%; background: #22C55E;
  box-shadow: 0 0 6px rgba(34, 197, 94, 0.8); animation: pulse 2s infinite;
}

@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

.right-container { flex-direction: column; min-width: 0; }

.header {
  background: var(--card-bg);
  border-bottom: 1px solid var(--border-color);
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px; height: 64px;
  transition: background 0.3s ease, border-color 0.3s ease;
}

.header-left { display: flex; align-items: center; gap: 16px; }

.collapse-btn {
  color: var(--text-regular); cursor: pointer; padding: 6px; border-radius: 8px;
  transition: background 0.2s, color 0.2s;
}
.collapse-btn:hover { background: var(--primary-lighter); color: var(--primary); }

.page-title { font-size: 18px; font-weight: 600; color: var(--text-primary); }

.header-right { display: flex; align-items: center; gap: 16px; }

.tech-tag { border: 1px solid #D6E4FF; background: #F0F6FF; color: var(--primary); font-weight: 500; }

.user-info { display: flex; align-items: center; gap: 8px; color: var(--text-regular); font-size: 14px; }

.user-avatar { background: linear-gradient(135deg, #2D6BFF, #5B8CFF); color: #fff; font-weight: 600; }

.logout-btn { color: #9CA3AF; cursor: pointer; transition: color 0.2s; }
.logout-btn:hover { color: var(--danger); }

.main-content {
  background-color: var(--page-bg);
  padding: 20px; overflow-y: auto;
  transition: background-color 0.3s ease;
}

@media (max-width: 1200px) {
  .tech-tag { display: none; }
  .global-search { width: 140px; }
  .global-search:focus-within { width: 180px; }
}
</style>

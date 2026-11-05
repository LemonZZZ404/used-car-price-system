import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', public: true }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '数据看板' }
  },
  {
    path: '/predict',
    name: 'Predict',
    component: () => import('@/views/Predict.vue'),
    meta: { title: '价格预测' }
  },
  {
    path: '/compare',
    name: 'Compare',
    component: () => import('@/views/Compare.vue'),
    meta: { title: '多车对比' }
  },
  {
    path: '/recommend',
    name: 'Recommend',
    component: () => import('@/views/Recommend.vue'),
    meta: { title: '智能选车' }
  },
  {
    path: '/realtime',
    name: 'RealTimeMonitor',
    component: () => import('@/views/RealTimeMonitor.vue'),
    meta: { title: '实时监控' }
  },
  {
    path: '/ranking',
    name: 'Ranking',
    component: () => import('@/views/Ranking.vue'),
    meta: { title: '排行榜中心' }
  },
  {
    path: '/market',
    name: 'Market',
    component: () => import('@/views/Market.vue'),
    meta: { title: '市场行情' }
  },
  {
    path: '/models',
    name: 'ModelLibrary',
    component: () => import('@/views/ModelLibrary.vue'),
    meta: { title: '车型库' }
  },
  {
    path: '/models/:series',
    name: 'SeriesDetail',
    component: () => import('@/views/SeriesDetail.vue'),
    meta: { title: '车系详情' }
  },
  {
    path: '/trend',
    name: 'Trend',
    component: () => import('@/views/Trend.vue'),
    meta: { title: '行情月报' }
  },
  {
    path: '/alerts',
    name: 'Alerts',
    component: () => import('@/views/Alerts.vue'),
    meta: { title: '预警中心' }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile.vue'),
    meta: { title: '个人中心' }
  },
  {
    path: '/help',
    name: 'Help',
    component: () => import('@/views/Help.vue'),
    meta: { title: '帮助中心' }
  },
  {
    path: '/users',
    name: 'Users',
    component: () => import('@/views/Users.vue'),
    meta: { title: '用户管理', adminOnly: true }
  },
  {
    path: '/model-analysis',
    name: 'ModelAnalysis',
    component: () => import('@/views/ModelAnalysis.vue'),
    meta: { title: '模型分析', adminOnly: true }
  },
  {
    path: '/cars',
    name: 'CarList',
    component: () => import('@/views/CarList.vue'),
    meta: { title: '车辆列表' }
  },
  {
    path: '/car/:id',
    name: 'CarDetail',
    component: () => import('@/views/CarDetail.vue'),
    meta: { title: '车辆详情' }
  },
  {
    path: '/simulator',
    name: 'Simulator',
    component: () => import('@/views/Simulator.vue'),
    meta: { title: '价格试算器' }
  },
  {
    path: '/trend-compare',
    name: 'TrendCompare',
    component: () => import('@/views/TrendCompare.vue'),
    meta: { title: '走势对比' }
  },
  {
    path: '/export',
    name: 'ExportCenter',
    component: () => import('@/views/ExportCenter.vue'),
    meta: { title: '导出中心' }
  },
  {
    path: '/data-dict',
    name: 'DataDict',
    component: () => import('@/views/DataDict.vue'),
    meta: { title: '数据字典' }
  },
  {
    path: '/logs',
    name: 'Logs',
    component: () => import('@/views/Logs.vue'),
    meta: { title: '运维日志', adminOnly: true }
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('@/views/History.vue'),
    meta: { title: '预测历史' }
  },
  {
    path: '/datamap',
    name: 'DataMap',
    component: () => import('@/views/DataMap.vue'),
    meta: { title: '数据地图' }
  },
  {
    path: '/brand-graph',
    name: 'BrandGraph',
    component: () => import('@/views/BrandGraph.vue'),
    meta: { title: '品牌图谱' }
  },
  {
    path: '/lineage',
    name: 'DataLineage',
    component: () => import('@/views/DataLineage.vue'),
    meta: { title: '数据血缘', adminOnly: true }
  },
  {
    path: '/system',
    name: 'SystemStatus',
    component: () => import('@/views/SystemStatus.vue'),
    meta: { title: '系统状态', adminOnly: true }
  },
  {
    path: '/about',
    name: 'About',
    component: () => import('@/views/About.vue'),
    meta: { title: '关于项目', adminOnly: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to) => {
  const token = localStorage.getItem('used_car_token')
  const userStr = localStorage.getItem('used_car_user')
  let user = null
  try { user = userStr ? JSON.parse(userStr) : null } catch (e) { user = null }

  if (to.meta.public) {
    return token ? '/dashboard' : true
  }

  if (!token || !user) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  if (to.meta.adminOnly && !user.is_staff) {
    return '/dashboard'
  }

  return true
})

export default router

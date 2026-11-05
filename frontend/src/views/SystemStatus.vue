<template>
  <div class="system-status-page">
    <!-- Hero 概览 -->
    <div class="hero-card card card-grad-blue">
      <div class="hero-left">
        <div class="hero-badge">
          <el-icon><Monitor /></el-icon>
          <span>系统监控</span>
        </div>
        <h2 class="hero-title">
          <span class="gradient-text-white">实时运行状态</span>
        </h2>
        <p class="hero-desc">全链路服务健康检查 · 3 节点分布式集群 · 大数据 + 机器学习平台</p>
      </div>
      <div class="hero-right">
        <div class="health-score" :class="{ all: allHealthy, some: !allHealthy && okCount > 0, none: okCount === 0 }">
          <div class="score-ring">
            <svg viewBox="0 0 120 120" class="ring-svg">
              <circle cx="60" cy="60" r="52" class="ring-bg" />
              <circle cx="60" cy="60" r="52" class="ring-progress" :style="ringStyle" />
            </svg>
            <div class="score-inner">
              <div class="score-num">{{ okCount }}/{{ totalCount }}</div>
              <div class="score-label">服务正常</div>
            </div>
          </div>
        </div>
        <el-button :icon="Refresh" @click="checkHealth" :loading="healthLoading" type="primary" plain size="default" round>
          刷新状态
        </el-button>
      </div>
      <div class="hero-deco">
        <svg viewBox="0 0 200 200" class="deco-waves">
          <circle cx="180" cy="40" r="80" fill="rgba(255,255,255,0.06)"/>
          <circle cx="160" cy="60" r="50" fill="rgba(255,255,255,0.08)"/>
        </svg>
      </div>
    </div>

    <!-- 服务健康检查 -->
    <div class="card">
      <div class="card-title">
        <span>服务健康检查</span>
        <div class="title-right">
          <el-tag :type="allHealthy ? 'success' : 'warning'" effect="dark" size="small" round>
            {{ allHealthy ? '全部正常' : '部分异常' }}
          </el-tag>
        </div>
      </div>
      <div class="health-grid">
        <div v-for="svc in healthChecks" :key="svc.name" class="health-card" :class="svc.status">
          <div class="hc-top">
            <div class="hc-icon" :class="svc.status">
              <el-icon v-if="svc.status === 'ok'"><CircleCheckFilled /></el-icon>
              <el-icon v-else-if="svc.status === 'fail'"><CircleCloseFilled /></el-icon>
              <el-icon v-else><Loading /></el-icon>
            </div>
            <div class="hc-status-dot" :class="svc.status"></div>
          </div>
          <div class="hc-name">{{ svc.label }}</div>
          <div class="hc-port">端口 {{ svc.port }}</div>
          <div class="hc-status-text" :class="svc.status">
            {{ svc.status === 'ok' ? '运行中' : svc.status === 'fail' ? '未响应' : '检测中...' }}
          </div>
        </div>
      </div>
    </div>

    <!-- 集群拓扑 -->
    <div class="card">
      <div class="card-title">
        <span>集群拓扑</span>
        <el-tag type="danger" effect="light" size="small" round>3 节点分布式</el-tag>
      </div>
      <el-row :gutter="20">
        <el-col v-for="node in nodes" :key="node.ip" :xs="24" :md="8">
          <div class="node-card" :class="{ master: node.role === 'Master' }">
            <div class="node-head">
              <div class="node-icon">
                <el-icon :size="20"><Platform /></el-icon>
              </div>
              <div class="node-info">
                <div class="node-host">{{ node.host }}</div>
                <div class="node-ip">{{ node.ip }}</div>
              </div>
              <el-tag :type="node.role === 'Master' ? 'danger' : 'primary'" size="small" effect="dark" round>{{ node.role }}</el-tag>
            </div>
            <div class="node-svc">
              <div v-for="svc in node.services" :key="svc" class="svc-item">
                <span class="svc-dot"></span>{{ svc }}
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 组件版本 + 端口 -->
    <el-row :gutter="20">
      <el-col :xs="24" :md="12">
        <div class="card">
          <div class="card-title">
            <span>组件版本清单</span>
            <el-tag type="primary" effect="light" size="small" round>/opt/module</el-tag>
          </div>
          <el-table :data="versions" size="small" stripe border class="status-table">
            <el-table-column prop="name" label="组件" width="130">
              <template #default="{ row }">
                <span style="font-weight:600">{{ row.name }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="version" label="版本" width="130" />
            <el-table-column prop="role" label="用途" min-width="180">
              <template #default="{ row }">
                <span style="color:#6B7280;font-size:12.5px">{{ row.role }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
      <el-col :xs="24" :md="12">
        <div class="card">
          <div class="card-title">
            <span>服务端口</span>
            <el-tag type="success" effect="light" size="small" round>防火墙已放行</el-tag>
          </div>
          <el-table :data="ports" size="small" stripe border class="status-table">
            <el-table-column prop="port" label="端口" width="100">
              <template #default="{ row }">
                <span style="font-weight:700;color:#2D6BFF">{{ row.port }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="service" label="服务" width="150" />
            <el-table-column prop="desc" label="说明" min-width="160">
              <template #default="{ row }">
                <span style="color:#6B7280;font-size:12.5px">{{ row.desc }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
    </el-row>

    <!-- 技术栈 -->
    <div class="card">
      <div class="card-title">
        <span>技术栈</span>
        <el-tag type="warning" effect="light" size="small" round>全栈 + 大数据 + ML</el-tag>
      </div>
      <div class="stack-tags">
        <el-tag v-for="t in stack" :key="t.name" :type="t.type" effect="light" size="large" round class="stack-tag">
          {{ t.name }}
        </el-tag>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Platform, Refresh, CircleCheckFilled, CircleCloseFilled, Monitor, Loading } from '@element-plus/icons-vue'
import { systemHealth } from '@/api'

const healthLoading = ref(false)
const healthChecks = ref([])

const allHealthy = computed(() => healthChecks.value.length > 0 && healthChecks.value.every(s => s.status === 'ok'))
const okCount = computed(() => healthChecks.value.filter(s => s.status === 'ok').length)
const totalCount = computed(() => healthChecks.value.length)

const ringStyle = computed(() => {
  const pct = totalCount.value > 0 ? (okCount.value / totalCount.value) : 0
  const circumference = 2 * Math.PI * 52
  const offset = circumference * (1 - pct)
  return {
    strokeDasharray: `${circumference}`,
    strokeDashoffset: `${offset}`
  }
})

const checkHealth = async () => {
  healthLoading.value = true
  try {
    const res = await systemHealth()
    if (res.code === 200 && res.data?.services) {
      healthChecks.value = res.data.services
    }
  } catch (e) {
    console.error('Health check failed:', e)
  } finally {
    healthLoading.value = false
  }
}

onMounted(() => {
  // 初始化为 pending 状态
  healthChecks.value = [
    { name: 'backend_api', label: '后端 API', port: '8000', status: 'pending' },
    { name: 'mysql', label: 'MySQL', port: '3306', status: 'pending' },
    { name: 'redis', label: 'Redis', port: '6379', status: 'pending' },
    { name: 'hdfs_web', label: 'HDFS Web', port: '9870', status: 'pending' },
    { name: 'yarn_web', label: 'YARN Web', port: '8088', status: 'pending' },
    { name: 'zookeeper', label: 'ZooKeeper', port: '2181', status: 'pending' },
    { name: 'kafka', label: 'Kafka', port: '9092', status: 'pending' },
    { name: 'hive_metastore', label: 'Hive Metastore', port: '9083', status: 'pending' },
  ]
  checkHealth()
})

const nodes = [
  {
    host: 'hadoop101', ip: '192.168.249.101', role: 'Master',
    services: ['NameNode', 'JobHistoryServer', 'Hive Metastore', 'HiveServer2', 'MySQL', 'Redis', 'Django', 'Nginx', 'Celery', 'ZooKeeper', 'Kafka']
  },
  {
    host: 'hadoop102', ip: '192.168.249.102', role: 'Worker',
    services: ['ResourceManager', 'NodeManager', 'ZooKeeper', 'Kafka']
  },
  {
    host: 'hadoop103', ip: '192.168.249.103', role: 'Worker',
    services: ['SecondaryNameNode', 'NodeManager', 'ZooKeeper', 'Kafka']
  }
]

const versions = [
  { name: 'Hadoop', version: '3.1.3', role: 'HDFS 存储 + YARN 资源调度' },
  { name: 'ZooKeeper', version: '3.5.7', role: '分布式协调服务' },
  { name: 'Kafka', version: '2.4.1', role: '消息队列（实时搜索事件）' },
  { name: 'Hive', version: '3.1.2', role: '数据仓库分层建模（ODS/DWD）' },
  { name: 'Spark', version: '3.0.0', role: '离线聚合分析 + MLlib 实验' },
  { name: 'Sqoop', version: '1.4.6', role: 'MySQL ↔ HDFS 数据导入导出' },
  { name: 'Flume', version: '1.9.0', role: '日志采集 → Kafka' },
  { name: 'MySQL', version: 'MariaDB 10.3', role: '业务库 / 统计结果存储' },
  { name: 'JDK', version: '1.8.0_212', role: 'Java 运行环境' },
  { name: 'Python', version: '3.9', role: 'Django / sklearn / Celery' }
]

const ports = [
  { port: 80, service: 'Nginx', desc: '前端页面（Vue 构建产物）' },
  { port: 8000, service: 'Gunicorn', desc: 'Django REST API' },
  { port: 3306, service: 'MySQL', desc: '业务数据库' },
  { port: 6379, service: 'Redis', desc: '缓存 + Celery Broker + 实时聚合' },
  { port: 9083, service: 'Hive Metastore', desc: '元数据服务' },
  { port: 10000, service: 'HiveServer2', desc: 'Hive JDBC 查询' },
  { port: 9870, service: 'NameNode', desc: 'HDFS Web UI' },
  { port: 8088, service: 'ResourceManager', desc: 'YARN Web UI' },
  { port: 2181, service: 'ZooKeeper', desc: '集群协调' },
  { port: 9092, service: 'Kafka', desc: '消息队列（car_search_events）' }
]

const stack = [
  { name: 'Vue3 + Vite', type: 'success' },
  { name: 'Element Plus', type: 'success' },
  { name: 'ECharts 5', type: 'success' },
  { name: 'Django + DRF', type: 'primary' },
  { name: 'MySQL / MariaDB', type: 'primary' },
  { name: 'Redis', type: 'primary' },
  { name: 'Celery 异步任务', type: 'primary' },
  { name: 'Nginx', type: 'primary' },
  { name: 'Hadoop HDFS', type: 'warning' },
  { name: 'YARN', type: 'warning' },
  { name: 'ZooKeeper', type: 'warning' },
  { name: 'Kafka', type: 'warning' },
  { name: 'Flume', type: 'warning' },
  { name: 'Sqoop', type: 'warning' },
  { name: 'Hive', type: 'warning' },
  { name: 'Spark SQL', type: 'warning' },
  { name: 'Random Forest', type: 'danger' },
  { name: 'LightGBM', type: 'danger' },
  { name: 'XGBoost', type: 'danger' },
  { name: 'Spark Streaming', type: 'danger' }
]
</script>

<style scoped>
.system-status-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Hero 卡片 */
.hero-card {
  position: relative;
  overflow: hidden;
  color: #fff;
  background: linear-gradient(135deg, #1E40AF 0%, #2D6BFF 50%, #3B82F6 100%);
  border: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 28px 32px;
}

.hero-card::before { display: none; }

.hero-left { position: relative; z-index: 2; flex: 1; }

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(255,255,255,0.2);
  backdrop-filter: blur(10px);
  padding: 5px 14px;
  border-radius: 20px;
  font-size: 12.5px;
  font-weight: 500;
  margin-bottom: 14px;
}

.hero-title {
  font-size: 28px;
  font-weight: 800;
  margin: 0 0 8px;
  letter-spacing: 0.5px;
}

.gradient-text-white {
  background: linear-gradient(90deg, #fff, #BFDBFE);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-desc {
  font-size: 13.5px;
  color: rgba(255,255,255,0.75);
  margin: 0;
}

.hero-right {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
}

.hero-deco {
  position: absolute;
  top: 0;
  right: 0;
  pointer-events: none;
  opacity: 0.8;
}

.deco-waves { width: 300px; height: 300px; }

/* 健康评分环 */
.health-score { display: flex; flex-direction: column; align-items: center; gap: 10px; }

.score-ring {
  position: relative;
  width: 110px;
  height: 110px;
}

.ring-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.ring-bg {
  fill: none;
  stroke: rgba(255,255,255,0.15);
  stroke-width: 8;
}

.ring-progress {
  fill: none;
  stroke: #fff;
  stroke-width: 8;
  stroke-linecap: round;
  transition: stroke-dashoffset 1s ease;
  filter: drop-shadow(0 0 6px rgba(255,255,255,0.5));
}

.score-inner {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.score-num {
  font-size: 22px;
  font-weight: 800;
  line-height: 1;
}

.score-label {
  font-size: 11px;
  opacity: 0.8;
  margin-top: 4px;
}

/* 健康检查网格 */
.health-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px;
}

.health-card {
  position: relative;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 18px 16px;
  text-align: center;
  transition: all 0.3s ease;
  overflow: hidden;
}

.health-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--border-color);
}

.health-card.ok {
  border-color: #BBF7D0;
  background: linear-gradient(180deg, #F0FDF4 0%, #fff 100%);
}
.health-card.ok::before { background: linear-gradient(90deg, #22C55E, #4ADE80); }

.health-card.fail {
  border-color: #FECACA;
  background: linear-gradient(180deg, #FEF2F2 0%, #fff 100%);
}
.health-card.fail::before { background: linear-gradient(90deg, #EF4444, #F87171); }

.health-card.pending {
  border-color: #E5E7EB;
  background: linear-gradient(180deg, #F9FAFB 0%, #fff 100%);
}
.health-card.pending::before { background: linear-gradient(90deg, #9CA3AF, #D1D5DB); }

.hc-top {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 10px;
}

.hc-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.hc-icon.ok { background: #DCFCE7; color: #16A34A; }
.hc-icon.fail { background: #FEE2E2; color: #DC2626; }
.hc-icon.pending { background: #F3F4F6; color: #6B7280; }

.hc-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  position: absolute;
  top: 14px;
  right: 14px;
}

.hc-status-dot.ok {
  background: #22C55E;
  box-shadow: 0 0 8px rgba(34, 197, 94, 0.6);
  animation: pulse-dot 2s infinite;
}

.hc-status-dot.fail { background: #EF4444; }
.hc-status-dot.pending { background: #9CA3AF; }

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.2); }
}

.hc-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.hc-port {
  font-size: 11.5px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.hc-status-text {
  font-size: 12px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 12px;
  display: inline-block;
}

.hc-status-text.ok { background: #DCFCE7; color: #16A34A; }
.hc-status-text.fail { background: #FEE2E2; color: #DC2626; }
.hc-status-text.pending { background: #F3F4F6; color: #6B7280; }

/* 节点卡片 */
.node-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 18px;
  height: 100%;
  transition: box-shadow 0.3s ease, transform 0.3s ease;
}

.node-card:hover {
  box-shadow: var(--card-shadow-hover);
  transform: translateY(-2px);
}

.node-card.master {
  border-color: #FECACA;
  background: linear-gradient(180deg, #FEF2F2, #fff 40%);
}

.node-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-bottom: 14px;
  border-bottom: 1px dashed var(--border-color);
  margin-bottom: 14px;
}

.node-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #2D6BFF, #5B8CFF);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.node-info { flex: 1; min-width: 0; }

.node-host {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
}

.node-ip {
  font-size: 12px;
  color: var(--text-secondary);
  font-family: var(--font-mono, monospace);
}

.node-svc {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.svc-item {
  font-size: 12px;
  color: #4B5563;
  background: #fff;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 3px 8px;
  display: flex;
  align-items: center;
  gap: 5px;
}

.svc-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #22C55E;
}

/* 表格 */
.status-table { margin-top: 8px; }

/* 技术栈 */
.stack-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.stack-tag {
  font-size: 13px;
  transition: all 0.2s ease;
}

.stack-tag:hover {
  transform: translateY(-1px);
}

@media (max-width: 768px) {
  .hero-card {
    flex-direction: column;
    text-align: center;
    gap: 20px;
    padding: 24px 20px;
  }
  .health-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>

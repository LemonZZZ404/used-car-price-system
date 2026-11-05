<template>
  <div class="logs-page">
    <div class="card">
      <div class="card-title">
        <span>运维日志</span>
        <div class="log-toolbar">
          <el-select v-model="lines" style="width: 110px" @change="loadLog">
            <el-option label="最近 100 行" :value="100" />
            <el-option label="最近 200 行" :value="200" />
            <el-option label="最近 500 行" :value="500" />
          </el-select>
          <el-button :icon="Refresh" @click="loadLog" :loading="loading">刷新</el-button>
          <el-switch v-model="autoRefresh" active-text="自动刷新" @change="toggleAuto" />
        </div>
      </div>

      <el-tabs v-model="activeLog" @tab-change="loadLog">
        <el-tab-pane v-for="(label, name) in LOG_TABS" :key="name" :name="name" :label="label" />
      </el-tabs>

      <div class="log-meta" v-if="meta">
        <span class="meta-path">{{ meta.path }}</span>
        <span class="meta-info">大小 {{ formatSize(meta.size) }} · 更新于 {{ meta.mtime }} · 返回 {{ meta.returned }} 行</span>
      </div>

      <div class="log-viewer" v-loading="loading">
        <pre v-if="logLines.length" class="log-pre"><code><span v-for="(l, i) in logLines" :key="i" :class="lineClass(l)">{{ l }}
</span></code></pre>
        <el-empty v-else-if="!loading" description="日志为空" :image-size="80" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { getAdminLogs } from '@/api'

const LOG_TABS = {
  gunicorn_error: 'Gunicorn 错误',
  gunicorn_access: 'Gunicorn 访问',
  django: 'Django',
  celery: 'Celery',
  warmup: '缓存预热',
  streaming: 'Kafka 流处理',
  nginx_access: 'Nginx 访问',
  nginx_error: 'Nginx 错误',
}

const activeLog = ref('gunicorn_error')
const lines = ref(200)
const autoRefresh = ref(false)
const loading = ref(false)
const meta = ref(null)
const logLines = ref([])

let timer = null

const formatSize = (n) => {
  if (n == null) return '—'
  if (n > 1024 * 1024) return (n / 1024 / 1024).toFixed(1) + ' MB'
  if (n > 1024) return (n / 1024).toFixed(1) + ' KB'
  return n + ' B'
}

const lineClass = (l) => {
  if (/error|critical|traceback|exception|failed/i.test(l)) return 'ln-err'
  if (/warn/i.test(l)) return 'ln-warn'
  return ''
}

const loadLog = async () => {
  loading.value = true
  try {
    const res = await getAdminLogs({ name: activeLog.value, lines: lines.value })
    if (res.code === 200) {
      meta.value = res.data
      logLines.value = res.data.lines || []
    } else {
      ElMessage.error(res.message || '日志获取失败')
      logLines.value = []
    }
  } catch (e) {
    logLines.value = []
  } finally {
    loading.value = false
  }
}

const toggleAuto = (on) => {
  clearInterval(timer)
  if (on) timer = setInterval(loadLog, 10000)
}

onMounted(loadLog)
onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.log-toolbar { display: flex; align-items: center; gap: 12px; }
.log-meta { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin: 4px 0 12px; font-size: 12px; color: #9CA3AF; }
.meta-path { font-family: Consolas, Monaco, monospace; }
.log-viewer { min-height: 300px; }
.log-pre {
  margin: 0; padding: 14px 16px; border-radius: 10px;
  background: #0F172A; color: #E2E8F0;
  font-family: Consolas, Monaco, 'Courier New', monospace;
  font-size: 12px; line-height: 1.65;
  max-height: 560px; overflow: auto;
  white-space: pre-wrap; word-break: break-all;
}
.ln-err { color: #F87171; }
.ln-warn { color: #FBBF24; }
</style>

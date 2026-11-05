<template>
  <div class="users-page">
    <div class="hero card">
      <div class="hero-left">
        <div class="hero-icon"><el-icon :size="28"><UserFilled /></el-icon></div>
        <div>
          <h2>用户管理</h2>
          <p>账号启停用与角色管理 · 仅管理员可见</p>
        </div>
      </div>
      <el-button circle :loading="loading" @click="load"><el-icon><Refresh /></el-icon></el-button>
    </div>

    <div class="stat-strip card">
      <div class="stat">
        <div class="stat-value">{{ users.length }}</div>
        <div class="stat-label">注册用户</div>
      </div>
      <div class="stat">
        <div class="stat-value admin">{{ users.filter(u => u.is_staff || u.is_superuser).length }}</div>
        <div class="stat-label">管理员</div>
      </div>
      <div class="stat">
        <div class="stat-value ok">{{ users.filter(u => u.is_active).length }}</div>
        <div class="stat-label">活跃账号</div>
      </div>
      <div class="stat">
        <div class="stat-value danger">{{ users.filter(u => !u.is_active).length }}</div>
        <div class="stat-label">已禁用</div>
      </div>
    </div>

    <div class="card table-card">
      <el-table :data="users" stripe>
        <el-table-column prop="username" label="用户名" min-width="120">
          <template #default="{ row }">
            <div class="u-name">
              <el-avatar :size="28" class="u-avatar">{{ row.username[0]?.toUpperCase() }}</el-avatar>
              <span>{{ row.username }}</span>
              <el-tag v-if="row.is_superuser" type="danger" size="small" effect="dark" round>超级管理员</el-tag>
              <el-tag v-else-if="row.is_staff" type="warning" size="small" effect="dark" round>管理员</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">{{ row.email || '-' }}</template>
        </el-table-column>
        <el-table-column prop="date_joined" label="注册时间" width="140" />
        <el-table-column prop="last_login" label="最近登录" width="140" />
        <el-table-column label="账号状态" width="110" align="center">
          <template #default="{ row }">
            <el-switch
              :model-value="row.is_active"
              :disabled="row.is_superuser"
              @change="toggleActive(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="管理员角色" width="130" align="center">
          <template #default="{ row }">
            <el-switch
              :model-value="row.is_staff"
              :disabled="row.is_superuser"
              @change="toggleStaff(row)"
            />
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UserFilled, Refresh } from '@element-plus/icons-vue'
import { getUserList, toggleUserActive, toggleUserStaff } from '@/api'

const users = ref([])
const loading = ref(false)

const load = async () => {
  loading.value = true
  try {
    const res = await getUserList()
    users.value = res.data || []
  } finally {
    loading.value = false
  }
}

const toggleActive = async (row) => {
  try {
    const res = await toggleUserActive(row.id)
    row.is_active = res.data.is_active
    ElMessage.success(row.is_active ? '已启用' : '已禁用')
  } catch (e) { /* 拦截器已提示 */ }
}

const toggleStaff = async (row) => {
  try {
    const res = await toggleUserStaff(row.id)
    row.is_staff = res.data.is_staff
    ElMessage.success(row.is_staff ? '已授予管理员' : '已收回管理员')
  } catch (e) { /* 拦截器已提示 */ }
}

onMounted(load)
</script>

<style scoped>
.users-page { max-width: 1200px; margin: 0 auto; }
.hero { display: flex; align-items: center; justify-content: space-between; padding: 22px 26px; margin-bottom: 20px; }
.hero-left { display: flex; align-items: center; gap: 14px; }
.hero-icon {
  width: 52px; height: 52px; border-radius: 13px;
  background: linear-gradient(135deg, #0EA5E9, #38BDF8);
  display: flex; align-items: center; justify-content: center; color: #fff;
  box-shadow: 0 6px 16px rgba(14, 165, 233, 0.35);
}
.hero h2 { margin: 0 0 4px; font-size: 20px; color: var(--text-primary); }
.hero p { margin: 0; font-size: 13px; color: var(--text-secondary); }

.stat-strip { display: flex; flex-wrap: wrap; padding: 16px 10px; margin-bottom: 20px; }
.stat { flex: 1; min-width: 110px; text-align: center; padding: 6px 8px; }
.stat-value { font-size: 26px; font-weight: 800; color: #2D6BFF; }
.stat-value.admin { color: #F59E0B; }
.stat-value.ok { color: #22C55E; }
.stat-value.danger { color: #EF4444; }
.stat-label { font-size: 12px; color: var(--text-secondary); margin-top: 4px; }

.table-card { padding: 20px 22px; }
.u-name { display: flex; align-items: center; gap: 8px; }
.u-avatar { background: linear-gradient(135deg, #2D6BFF, #5B8CFF); color: #fff; font-size: 13px; }
</style>

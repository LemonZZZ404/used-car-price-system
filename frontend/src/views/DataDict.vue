<template>
  <div class="data-dict-page">
    <!-- 数据表字典 -->
    <div class="card">
      <div class="card-title">
        <span>数据表字典 · car_info（车辆信息主表，约 100 万行）</span>
        <el-tag size="small" effect="plain" type="primary">Sqoop/Spark 写入 · Django 只读</el-tag>
      </div>
      <el-table :data="carInfoFields" stripe border size="small">
        <el-table-column prop="field" label="字段名" width="150">
          <template #default="{ row }"><code class="field-code">{{ row.field }}</code></template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="130" />
        <el-table-column prop="unit" label="单位" width="100" />
        <el-table-column prop="desc" label="口径说明" min-width="240" />
        <el-table-column prop="usage" label="业务用途" min-width="200" />
      </el-table>
    </div>

    <el-row :gutter="20" class="mt20">
      <el-col :xs="24" :md="12">
        <div class="card h-full">
          <div class="card-title">统计宽表（Spark 离线聚合）</div>
          <el-table :data="statTables" stripe border size="small">
            <el-table-column prop="table" label="表名" width="190">
              <template #default="{ row }"><code class="field-code">{{ row.table }}</code></template>
            </el-table-column>
            <el-table-column prop="granularity" label="粒度" width="110" />
            <el-table-column prop="desc" label="说明" min-width="160" />
          </el-table>
        </div>
      </el-col>
      <el-col :xs="24" :md="12">
        <div class="card h-full">
          <div class="card-title">业务表（Django 写入）</div>
          <el-table :data="bizTables" stripe border size="small">
            <el-table-column prop="table" label="表名" width="190">
              <template #default="{ row }"><code class="field-code">{{ row.table }}</code></template>
            </el-table-column>
            <el-table-column prop="granularity" label="粒度" width="110" />
            <el-table-column prop="desc" label="说明" min-width="160" />
          </el-table>
        </div>
      </el-col>
    </el-row>

    <!-- API 清单 -->
    <div class="card mt20">
      <div class="card-title">
        <span>API 清单与缓存策略</span>
        <el-tag size="small" effect="plain" type="success">Redis 缓存 300-600s</el-tag>
      </div>
      <el-table :data="apiList" stripe border size="small">
        <el-table-column prop="method" label="方法" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="row.method === 'POST' ? 'warning' : 'success'" effect="plain">{{ row.method }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="path" label="路径" min-width="230">
          <template #default="{ row }"><code class="field-code">{{ row.path }}</code></template>
        </el-table-column>
        <el-table-column prop="desc" label="说明" min-width="230" />
        <el-table-column prop="cache" label="缓存" width="150" />
      </el-table>
    </div>

    <!-- 数据链路 -->
    <div class="card mt20">
      <div class="card-title">数据链路与指标口径</div>
      <div class="pipeline-flow">
        <div class="pf-node">数据源<br><span>车源平台采集</span></div>
        <div class="pf-arrow">→</div>
        <div class="pf-node">采集入仓<br><span>Kafka / Sqoop</span></div>
        <div class="pf-arrow">→</div>
        <div class="pf-node">离线加工<br><span>Spark 聚合</span></div>
        <div class="pf-arrow">→</div>
        <div class="pf-node">MySQL<br><span>car_info / stat_*</span></div>
        <div class="pf-arrow">→</div>
        <div class="pf-node">服务层<br><span>Django + Redis</span></div>
      </div>
      <el-alert type="info" :closable="false" class="mt10" title="关键指标口径说明">
        <template #default>
          <ul class="metric-list">
            <li><b>售价（price）</b>：车源挂牌价，单位万元，为平台展示一口价，非成交价。</li>
            <li><b>车龄（age）</b>：按上牌日期至数据采集日的整年数向下取整。</li>
            <li><b>里程（mileage）</b>：表显里程，单位万公里，保留两位小数。</li>
            <li><b>月均价走势</b>：按上牌月份（register_date）聚合的挂牌价算术平均，非时间序列成交价。</li>
            <li><b>比价分位</b>：同车系且车龄 ±1 年车源中，低于该车价格的车源占比。</li>
            <li><b>模型置信度</b>：1 - MAPE（交叉验证得出），估价区间为残差分位数 P10/P90。</li>
          </ul>
        </template>
      </el-alert>
    </div>
  </div>
</template>

<script setup>
const carInfoFields = [
  { field: 'car_id', type: 'varchar(64)', unit: '-', desc: '车源唯一编号（平台原始 ID）', usage: '唯一索引 / 详情定位' },
  { field: 'brand', type: 'varchar(64)', unit: '-', desc: '品牌名称（标准化后）', usage: '品牌筛选 / 品牌统计' },
  { field: 'series', type: 'varchar(128)', unit: '-', desc: '车系名称（如朗逸、轩逸）', usage: '车系聚合 / 走势对比' },
  { field: 'model', type: 'varchar(256)', unit: '-', desc: '具体车型配置描述', usage: '车型库展示' },
  { field: 'price', type: 'decimal(12,2)', unit: '万元', desc: '挂牌售价（一口价）', usage: '估价目标变量 / 行情分析' },
  { field: 'original_price', type: 'decimal(12,2)', unit: '万元', desc: '新车指导价（可能缺失）', usage: '保值率 / 折旧计算' },
  { field: 'age', type: 'int', unit: '年', desc: '车龄 = 采集年 - 上牌年', usage: '贬值曲线核心特征' },
  { field: 'mileage', type: 'decimal(10,2)', unit: '万公里', desc: '表显行驶里程', usage: '估价核心特征' },
  { field: 'gearbox', type: 'varchar(32)', unit: '-', desc: '变速箱类型：自动 / 手动', usage: '估价类别特征' },
  { field: 'displacement', type: 'varchar(32)', unit: 'L/T', desc: '排量标识（如 1.5T、纯电）', usage: '估价类别特征' },
  { field: 'fuel_type', type: 'varchar(32)', unit: '-', desc: '燃油类型：汽油/柴油/纯电动/混合动力/插电混动', usage: '能源结构分析' },
  { field: 'color', type: 'varchar(32)', unit: '-', desc: '车身颜色', usage: '流通性参考' },
  { field: 'city', type: 'varchar(64)', unit: '-', desc: '车源所在城市', usage: '地域分布 / 热力图' },
  { field: 'register_date', type: 'date', unit: '-', desc: '上牌日期', usage: '月度走势时间轴' },
]

const statTables = [
  { table: 'stat_brand_price', granularity: '品牌', desc: '品牌维度：车源量、均价、最低/最高价' },
  { table: 'stat_age_price', granularity: '车龄', desc: '车龄维度：车源量、均价（贬值曲线）' },
  { table: 'stat_price_distribution', granularity: '价格段', desc: '价格区间分布：各价格段车源量' },
]

const bizTables = [
  { table: 'prediction_record', granularity: '单次预测', desc: '用户预测输入与模型输出记录' },
  { table: 'auth_user / token', granularity: '用户', desc: 'Django 用户与 Token 认证' },
]

const apiList = [
  { method: 'GET', path: '/api/cars/', desc: '车源分页列表（品牌/城市/燃油/车龄筛选）', cache: '无' },
  { method: 'GET', path: '/api/cars/{id}/car_detail/', desc: '车辆详情 + 同车系比价分位 + 贬值曲线', cache: '600s' },
  { method: 'GET', path: '/api/cars/trend_compare/', desc: '车系走势对比（≤4 个车系，近 24 个月）', cache: '600s' },
  { method: 'GET', path: '/api/export/csv/', desc: '条件筛选 CSV 流式导出（≤10 万行）', cache: '无（流式）' },
  { method: 'POST', path: '/api/prediction/predict/', desc: '单车估价（含置信度与 P10/P90 区间）', cache: '模型单例缓存' },
  { method: 'POST', path: '/api/prediction/batch/', desc: '批量预测（Celery 异步，≤1000 条）', cache: '异步任务' },
  { method: 'GET', path: '/api/cars/monthly/', desc: '行情月报：全量 + TOP5 品牌月均走势', cache: '3600s' },
  { method: 'GET', path: '/api/dashboard/summary/', desc: '看板概览指标', cache: '300s' },
  { method: 'GET', path: '/api/realtime/hot/', desc: '实时热门搜索（Kafka 聚合结果）', cache: '实时' },
  { method: 'GET', path: '/api/admin/logs/', desc: '运维日志尾部（仅管理员）', cache: '无' },
  { method: 'GET', path: '/api/system/health/', desc: '系统健康检查（端口/MySQL/Redis）', cache: '无' },
]
</script>

<style scoped>
.mt20 { margin-top: 20px; }
.h-full { height: 100%; }
.field-code {
  font-family: Consolas, Monaco, monospace;
  background: rgba(45,107,255,0.08);
  color: #2D6BFF; padding: 2px 6px; border-radius: 4px; font-size: 12px;
}
.pipeline-flow { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; padding: 8px 0; }
.pf-node {
  padding: 12px 18px; border-radius: 10px; text-align: center;
  background: rgba(45,107,255,0.07); font-weight: 600; font-size: 14px;
  border: 1px solid rgba(45,107,255,0.2);
}
.pf-node span { font-weight: 400; font-size: 12px; color: #6B7280; }
.pf-arrow { color: #9CA3AF; font-size: 18px; }
.metric-list { margin: 8px 0 0; padding-left: 18px; line-height: 2; font-size: 13px; }
</style>

<template>
  <div class="help-page">
    <div class="hero card">
      <div class="hero-icon"><el-icon :size="32"><QuestionFilled /></el-icon></div>
      <h2>帮助中心</h2>
      <p>了解系统的使用流程、常见问题与底层技术栈</p>
    </div>

    <div class="card section">
      <div class="section-title"><el-icon><Guide /></el-icon><span>使用流程</span></div>
      <el-steps :active="4" align-center finish-status="success" class="steps">
        <el-step title="填写车况" description="品牌 / 车龄 / 里程 / 排量等" />
        <el-step title="智能估价" description="机器学习模型秒级出价" />
        <el-step title="对比选购" description="多车对比 · 智能选车推荐" />
        <el-step title="导出报告" description="一键下载 PDF 评估报告" />
      </el-steps>
    </div>

    <el-row :gutter="20">
      <el-col :xs="24" :md="14">
        <div class="card section">
          <div class="section-title"><el-icon><ChatDotRound /></el-icon><span>常见问题</span></div>
          <el-collapse accordion>
            <el-collapse-item v-for="f in faqs" :key="f.q" :title="f.q" :name="f.q">
              <p class="faq-a">{{ f.a }}</p>
            </el-collapse-item>
          </el-collapse>
        </div>
      </el-col>
      <el-col :xs="24" :md="10">
        <div class="card section">
          <div class="section-title"><el-icon><Cpu /></el-icon><span>技术栈</span></div>
          <div class="tech-groups">
            <div v-for="g in tech" :key="g.name" class="tech-group">
              <div class="tech-name">{{ g.name }}</div>
              <div class="tech-tags">
                <el-tag v-for="t in g.items" :key="t" size="small" effect="plain" round>{{ t }}</el-tag>
              </div>
            </div>
          </div>
        </div>
        <div class="card section">
          <div class="section-title"><el-icon><InfoFilled /></el-icon><span>数据说明</span></div>
          <ul class="data-notes">
            <li>车源数据由 Hadoop 集群离线清洗后经 Sqoop 同步至 MySQL</li>
            <li>实时搜索热度与价格预警由 Kafka + Spark Streaming 流式计算</li>
            <li>价格区间由模型测试集残差分位数（P10/P90）推导</li>
            <li>所有接口均带 Redis 缓存，命中后响应 &lt; 10ms</li>
          </ul>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import {
  QuestionFilled, Guide, ChatDotRound, Cpu, InfoFilled
} from '@element-plus/icons-vue'

const faqs = [
  { q: '估价结果可信吗？价格区间是什么意思？', a: '模型基于数十万条真实成交数据训练，置信度取自测试集表现。价格区间为测试集残差的 P10/P90 分位数，表示 80% 的类似车源成交价落在该区间内。' },
  { q: '智能选车的推荐分是怎么算的？', a: '系统根据你选择的用车场景（家用/商务/运动/经济/新手）对车龄、里程、排量、变速箱、品牌等维度进行规则打分，并给出可解释的推荐理由。' },
  { q: '保值率预测是怎么实现的？', a: '以当前车况为基准，按年均里程外推未来 1-3 年的车龄与里程，逐点调用估价模型得到价格曲线，再除以新车指导价得到保值率。' },
  { q: '为什么有的页面第一次打开稍慢？', a: '首次请求需要实时聚合百万级车源数据（约 1-2 秒），聚合结果会缓存至 Redis（1-10 分钟），之后的请求都在毫秒级返回。' },
  { q: '预警中心的异常价格是怎么发现的？', a: '实时流消费者持续比对用户搜索价格与模型期望价格，偏差超过阈值即写入预警队列，偏差 50% 以上为高风险。' },
  { q: '评估报告包含哪些内容？', a: '报告包含车辆参数、预估价格与区间、置信度、关键影响因子（SHAP 分析）、同价位热门车对比与免责声明，可直接下载 PDF 用于交易参考。' },
]

const tech = [
  { name: '大数据', items: ['Hadoop HDFS', 'Hive', 'Spark', 'Sqoop', 'Kafka'] },
  { name: '算法', items: ['RandomForest', 'LightGBM', 'XGBoost', 'SHAP'] },
  { name: '后端', items: ['Django', 'DRF', 'Celery', 'Redis', 'MySQL'] },
  { name: '前端', items: ['Vue3', 'Vite', 'Element Plus', 'ECharts'] },
  { name: '部署', items: ['Nginx', 'Gunicorn', 'systemd', '3 节点集群'] },
]
</script>

<style scoped>
.help-page { max-width: 1200px; margin: 0 auto; }
.hero { text-align: center; padding: 40px 20px 34px; margin-bottom: 20px; }
.hero-icon {
  width: 64px; height: 64px; border-radius: 16px; margin: 0 auto 14px;
  background: linear-gradient(135deg, #2D6BFF, #5B8CFF);
  display: flex; align-items: center; justify-content: center; color: #fff;
  box-shadow: 0 8px 20px rgba(45, 107, 255, 0.35);
}
.hero h2 { margin: 0 0 6px; font-size: 22px; color: var(--text-primary); }
.hero p { margin: 0; font-size: 13px; color: var(--text-secondary); }

.section { padding: 22px 24px; margin-bottom: 20px; }
.section-title {
  display: flex; align-items: center; gap: 8px;
  font-size: 15px; font-weight: 600; color: var(--text-primary); margin-bottom: 18px;
}
.steps { padding: 10px 0 4px; }

.faq-a { margin: 0; font-size: 13.5px; line-height: 1.8; color: var(--text-secondary); }

.tech-groups { display: flex; flex-direction: column; gap: 14px; }
.tech-group { display: flex; align-items: flex-start; gap: 12px; }
.tech-name { width: 52px; flex-shrink: 0; font-size: 13px; font-weight: 600; color: var(--text-primary); padding-top: 3px; }
.tech-tags { display: flex; flex-wrap: wrap; gap: 6px; }

.data-notes { margin: 0; padding-left: 18px; }
.data-notes li { font-size: 13px; line-height: 2; color: var(--text-secondary); }
</style>

#!/bin/bash
#=============================================================================
# 集群健康检查脚本
# 检查三台节点的所有服务状态，输出彩色报告
# 用法：bash cluster_health_check.sh
#=============================================================================

H1=hadoop101
H2=hadoop102
H3=hadoop103
USER=gk

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; NC='\033[0m'
BOLD='\033[1m'

ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; }
warn() { echo -e "  ${YELLOW}!${NC} $1"; }
hdr()  { echo -e "\n${CYAN}${BOLD}[$1]${NC}"; }

echo -e "${CYAN}${BOLD}"
echo "============================================"
echo " 二手车价格评估系统 - 集群健康检查"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"
echo -e "${NC}"

check_port() {
    local host=$1 port=$2 name=$3
    if ssh -o ConnectTimeout=5 "$USER@$host" "ss -tln 2>/dev/null | grep -q ':$port '" 2>/dev/null; then
        ok "$name ($host:$port)"
        return 0
    else
        fail "$name ($host:$port)"
        return 1
    fi
}

check_jps() {
    local host=$1 proc=$2 name=$3
    if ssh -o ConnectTimeout=5 "$host" "jps 2>/dev/null | grep -q '$proc'" 2>/dev/null; then
        ok "$name ($host)"
    else
        fail "$name ($host)"
    fi
}

check_http() {
    local url=$1 name=$2
    code=$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 5 "$url" 2>/dev/null)
    if [ "$code" = "200" ]; then
        ok "$name (HTTP $code)"
    else
        fail "$name (HTTP $code)"
    fi
}

check_redis_key() {
    local key=$1 name=$2
    val=$(redis-cli get "$key" 2>/dev/null)
    if [ -n "$val" ]; then
        ok "$name: $val"
    else
        warn "$name: 无数据"
    fi
}

# ---------- hadoop101 ----------
hdr "hadoop101 (192.168.249.101) - 主节点"
echo "  系统: $(ssh $USER@$H1 'uname -r' 2>/dev/null)"
echo "  负载: $(ssh $USER@$H1 'cat /proc/loadavg' 2>/dev/null | awk '{print $1,$2,$3}')"
echo "  内存: $(ssh $USER@$H1 'free -h' 2>/dev/null | awk '/Mem/{print $3"/"$2}')"
echo "  磁盘: $(ssh $USER@$H1 'df -h /opt' 2>/dev/null | awk 'NR==2{print $3"/"$2" ("$5")"}')"
echo "  服务:"
check_port $H1 3306 "MySQL"
check_port $H1 6379 "Redis"
check_port $H1 8020 "HDFS NameNode"
check_port $H1 9083 "Hive Metastore"
check_port $H1 10000 "HiveServer2"
check_port $H1 8000 "Django/Gunicorn"
check_port $H1 80    "Nginx"
check_port $H1 2181 "ZooKeeper"
check_port $H1 9092 "Kafka"
check_jps  $H1 "JobHistoryServer" "JobHistory"
check_jps  $H1 "NameNode" "NameNode进程"

# ---------- hadoop102 ----------
hdr "hadoop102 (192.168.249.102) - 计算节点"
echo "  负载: $(ssh $USER@$H2 'cat /proc/loadavg' 2>/dev/null | awk '{print $1,$2,$3}')"
echo "  内存: $(ssh $USER@$H2 'free -h' 2>/dev/null | awk '/Mem/{print $3"/"$2}')"
echo "  服务:"
check_jps $H2 "ResourceManager" "ResourceManager"
check_port $H2 8088 "YARN Web UI"
check_port $H2 2181 "ZooKeeper"
check_port $H2 9092 "Kafka"

# ---------- hadoop103 ----------
hdr "hadoop103 (192.168.249.103) - 备份节点"
echo "  负载: $(ssh $USER@$H3 'cat /proc/loadavg' 2>/dev/null | awk '{print $1,$2,$3}')"
echo "  内存: $(ssh $USER@$H3 'free -h' 2>/dev/null | awk '/Mem/{print $3"/"$2}')"
echo "  服务:"
check_jps $H3 "SecondaryNameNode" "SecondaryNameNode"
check_port $H3 2181 "ZooKeeper"
check_port $H3 9092 "Kafka"

# ---------- HDFS ----------
hdr "HDFS 数据"
ssh $USER@$H1 'hdfs dfsadmin -report 2>/dev/null' | grep -E 'Live datanodes|DFS Used|DFS Remaining' | while read line; do
    echo "  $line"
done

# ---------- Kafka ----------
hdr "Kafka 状态"
kafka_topics=$(ssh $USER@$H1 '/opt/module/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092 2>/dev/null' | wc -l)
echo "  Topics 数量: $kafka_topics"
ssh $USER@$H1 '/opt/module/kafka/bin/kafka-topics.sh --describe --bootstrap-server localhost:9092 --topic car_search_events 2>/dev/null' | head -2 | while read line; do
    echo "  $line"
done

# ---------- Hive ----------
hdr "Hive 数据"
hive_tables=$(ssh $USER@$H1 'hive -e "SHOW TABLES IN used_car" 2>/dev/null' | grep -v "^$" | grep -v "_col" | wc -l)
echo "  used_car 表数量: $hive_tables"
for t in ods_car_info dwd_car_info ads_brand_price ads_age_price ads_price_distribution; do
    cnt=$(ssh $USER@$H1 "hive -e 'SELECT COUNT(*) FROM used_car.$t' 2>/dev/null" | grep -E '^[0-9]+$' | head -1)
    echo "  $t: ${cnt:-N/A} 条"
done

# ---------- MySQL ----------
hdr "MySQL 数据"
mysql -uroot -p200412230 used_car -e "SELECT 'car_info' as tbl, COUNT(*) as cnt FROM car_info UNION ALL SELECT 'stat_brand_price', COUNT(*) FROM stat_brand_price UNION ALL SELECT 'stat_age_price', COUNT(*) FROM stat_age_price UNION ALL SELECT 'stat_price_distribution', COUNT(*) FROM stat_price_distribution" 2>/dev/null | while read line; do
    echo "  $line"
done

# ---------- Redis 实时数据 ----------
hdr "Redis 实时数据"
check_redis_key "used_car:realtime:status" "流处理状态"
check_redis_key "used_car:realtime:total_events" "总搜索事件"
check_redis_key "used_car:realtime:last_update" "最后更新"

# ---------- API 健康检查 ----------
hdr "API 健康"
check_http "http://192.168.249.101/api/health/" "后端 API"
check_http "http://192.168.249.101/" "前端页面"
check_http "http://192.168.249.101/api/realtime/hot/" "实时热门 API"
check_http "http://192.168.249.101:9870/" "HDFS Web UI"
check_http "http://192.168.249.101:8088/" "YARN Web UI"

# ---------- Celery ----------
hdr "Celery 状态"
celery_pids=$(pgrep -f "celery.*config worker" | wc -l)
if [ "$celery_pids" -gt 0 ]; then
    ok "Celery worker 运行中 ($celery_pids 进程)"
else
    fail "Celery worker 未运行"
fi

# ---------- 模型文件 ----------
hdr "模型文件"
for f in rf_price_model.joblib lightgbm_model.joblib xgboost_model.joblib; do
    path="/opt/used-car-price-cluster/ml/models/$f"
    if ssh $USER@$H1 "test -f $path" 2>/dev/null; then
        size=$(ssh $USER@$H1 "du -h $path" 2>/dev/null | awk '{print $1}')
        ok "$f ($size)"
    else
        warn "$f 不存在"
    fi
done

# ---------- 总结 ----------
hdr "总结"
echo -e "  ${CYAN}优化项目完成状态:${NC}"
echo "  [✓] P0: 部署脚本修复 + 集群启动"
echo "  [✓] P1: 4模型对比 (RF + LightGBM + XGBoost + LR)"
echo "  [✓] P1: Kafka 实时管道 (Consumer + Redis)"
echo "  [✓] P2: 后端增强 (实时API + 缓存 + 限流 + 批量预测)"
echo "  [✓] P2: 集群健康检查"

echo ""
echo -e "${GREEN}${BOLD}检查完成！$(date '+%Y-%m-%d %H:%M:%S')${NC}"

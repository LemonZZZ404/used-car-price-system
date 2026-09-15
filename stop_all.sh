#!/bin/bash
# ============================================
# 二手车价格评估系统 - 一键停止脚本
# 用法: sudo ./stop_all.sh
# 反向于 start_all.sh，幂等执行
# ============================================

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
log_info() { echo -e "${GREEN}[停止]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[跳过]${NC} $1"; }
log_err()  { echo -e "${RED}[失败]${NC} $1"; }

port_in_use() { ss -tln | grep -q ":$1 "; }
svc_active()  { systemctl is-active --quiet "$1" 2>/dev/null; }

echo "============================================"
echo " 二手车价格评估系统 一键停止"
echo "============================================"

# 1. 前端 dev server（Nginx 是系统服务，默认不停，见文末说明）
if port_in_use 5173; then
  log_info "停止前端 dev server (5173) ..."
  fuser -k 5173/tcp 2>/dev/null || pkill -f "vite" 2>/dev/null
else
  log_warn "前端 dev server 未运行"
fi

# 2. Django 后端 (gunicorn)
if port_in_use 8000; then
  log_info "停止 Django 后端 (8000) ..."
  fuser -k 8000/tcp 2>/dev/null || pkill -f "gunicorn config.wsgi" 2>/dev/null
  sleep 2
  port_in_use 8000 && log_err "8000 仍被占用" || log_info "Django 后端已停止"
else
  log_warn "Django 后端未运行"
fi

# 3. Hive Metastore
if port_in_use 9083; then
  log_info "停止 Hive Metastore (9083) ..."
  pkill -f "hive.*metastore" 2>/dev/null
  sleep 3
  port_in_use 9083 && log_err "9083 仍被占用" || log_info "Hive Metastore 已停止"
else
  log_warn "Hive Metastore 未运行"
fi

# 4. Hadoop YARN + HDFS
source /etc/profile 2>/dev/null; source ~/.bashrc 2>/dev/null
if jps 2>/dev/null | grep -qE "ResourceManager|NameNode"; then
  log_info "停止 Hadoop YARN + HDFS ..."
  stop-yarn.sh; stop-dfs.sh
else
  log_warn "Hadoop 未运行"
fi

# 5. Redis
if svc_active redis; then
  log_info "停止 Redis ..."; systemctl stop redis
else
  log_warn "Redis 未运行"
fi

# 6. MySQL
if svc_active mysqld; then
  log_info "停止 MySQL ..."; systemctl stop mysqld
else
  log_warn "MySQL 未运行"
fi

echo ""
echo "系统已全部停止（Nginx 除外）"


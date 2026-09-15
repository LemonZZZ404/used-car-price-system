#!/bin/bash
# ============================================
# 二手车价格评估系统 - 一键启动脚本
# 用法: sudo ./start_all.sh
# 幂等：已运行的服务会自动跳过
# ============================================

PROJECT_DIR="/opt/used-car-price-system"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
log_info() { echo -e "${GREEN}[启动]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[跳过]${NC} $1"; }
log_err()  { echo -e "${RED}[失败]${NC} $1"; }

port_in_use() { ss -tln | grep -q ":$1 "; }
svc_active()  { systemctl is-active --quiet "$1" 2>/dev/null; }

echo "============================================"
echo " 二手车价格评估系统 一键启动"
echo "============================================"

# 1. MySQL
if svc_active mysqld; then log_warn "MySQL 已在运行"
else log_info "启动 MySQL ..."; systemctl start mysqld || { log_err "MySQL 启动失败"; exit 1; }; fi

# 2. Redis
if svc_active redis; then log_warn "Redis 已在运行"
else log_info "启动 Redis ..."; systemctl start redis || { log_err "Redis 启动失败"; exit 1; }; fi

# 3. Hadoop（需要已配置 HADOOP_HOME）
source /etc/profile 2>/dev/null; source ~/.bashrc 2>/dev/null
if jps 2>/dev/null | grep -q NameNode; then log_warn "Hadoop HDFS/YARN 已在运行"
else log_info "启动 Hadoop HDFS + YARN ..."; start-dfs.sh && start-yarn.sh || { log_err "Hadoop 启动失败"; exit 1; }; fi

# 4. Hive Metastore
if port_in_use 9083; then log_warn "Hive Metastore 已在运行"
else
  log_info "启动 Hive Metastore ..."
  nohup hive --service metastore > "$LOG_DIR/metastore.log" 2>&1 &
  sleep 5
  port_in_use 9083 && log_info "Hive Metastore 启动完成" || log_err "Hive Metastore 未起来，看 $LOG_DIR/metastore.log"
fi

# 5. Django 后端 (gunicorn)
if port_in_use 8000; then log_warn "Django 后端已在运行 (8000)"
else
  log_info "启动 Django 后端 ..."
  cd "$BACKEND_DIR" && source venv/bin/activate
  gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --daemon
  sleep 3
  port_in_use 8000 && log_info "Django 后端启动完成" || log_err "Django 后端启动失败"
fi

# 6. 前端（优先 Nginx，否则 dev 模式）
if port_in_use 80; then log_warn "Nginx 已在运行，前端走 Nginx (80)"
else
  log_info "Nginx 未运行，以前端开发模式启动 ..."
  cd "$FRONTEND_DIR" && nohup npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
fi

# 健康检查
echo ""
echo "============================================"
echo " 健康检查"
echo "============================================"
sleep 2
echo "后端 API:  /api/cars/ -> HTTP $(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/api/cars/)"
port_in_use 80 \
  && echo "前端页面:  http://<虚拟机IP> -> HTTP $(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1/)" \
  || echo "前端页面:  http://<虚拟机IP>:5173 (开发模式)"
echo ""
echo "系统启动完成！"


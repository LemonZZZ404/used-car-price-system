#!/bin/bash
# ============================================================
# 系统状态检查脚本
# 用法: bash status_all.sh
# ============================================================
PROJECT_DIR="/opt/used-car-price-system"
port_in_use() { ss -tln | grep -q ":$1 "; }

echo "============================================"
echo " 二手车价格评估系统 - 状态检查"
echo "============================================"

echo ""
echo "--- 服务端口 ---"
[ $(systemctl is-active mysqld 2>/dev/null) = "active" ] && echo "  MySQL      3306  [运行中]" || echo "  MySQL      3306  [未运行]"
[ $(systemctl is-active redis 2>/dev/null) = "active" ] && echo "  Redis      6379  [运行中]" || echo "  Redis      6379  [未运行]"
port_in_use 80   && echo "  Nginx       80  [运行中]"   || echo "  Nginx       80  [未运行]"
port_in_use 8000 && echo "  Django     8000  [运行中]"   || echo "  Django     8000  [未运行]"
port_in_use 8088 && echo "  YARN       8088  [运行中]"   || echo "  YARN       8088  [未运行]"
port_in_use 9870 && echo "  HDFS       9870  [运行中]"   || echo "  HDFS       9870  [未运行]"
port_in_use 9083 && echo "  HiveMetast 9083  [运行中]"   || echo "  HiveMetast 9083  [未运行]"

echo ""
echo "--- 数据量 ---"
mysql -uroot -p123456 used_car -e "SELECT COUNT(*) AS car_info行数 FROM car_info;" 2>/dev/null | grep -v Warning
mysql -uroot -p123456 used_car -e "SELECT COUNT(*) AS 品牌统计行数 FROM stat_brand_price;" 2>/dev/null | grep -v Warning

echo ""
echo "--- 模型文件 ---"
ls -lh "$PROJECT_DIR/ml/models/rf_price_model.joblib" 2>/dev/null || echo "  模型文件不存在！"

echo ""
echo "--- 前端访问 ---"
echo "  http://$(hostname -I | awk '{print $1}')  -> HTTP $(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1/ 2>/dev/null)"
echo "  后端API: /api/cars/ -> HTTP $(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/api/cars/ 2>/dev/null)"
echo ""
echo "============================================"

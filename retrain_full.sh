#!/bin/bash
# ============================================================
# 一键全流程重训脚本：数据生成 -> 入库 -> 大数据链路 -> 模型训练
# 用法: bash retrain_full.sh [数据条数]
# 示例: bash retrain_full.sh 1000000
# 注意: 内存仅3.5G时，建议先执行 stop_all.sh 停掉大数据服务再训练
# ============================================================
set -e
PROJECT_DIR="/opt/used-car-price-system"
COUNT="${1:-1000000}"

echo "============================================"
echo " 二手车价格评估系统 - 全流程重训"
echo " 数据条数: $COUNT"
echo "============================================"

echo ""
echo "[1/6] 生成模拟数据 ($COUNT 条)..."
python "$PROJECT_DIR/data/scripts/generate_mock_data_v2.py" --count $COUNT

echo ""
echo "[2/6] 数据预处理并导入 MySQL..."
python "$PROJECT_DIR/data/scripts/data_preprocess.py" --mysql

echo ""
echo "[3/6] Sqoop 导入 HDFS/Hive ODS..."
bash "$PROJECT_DIR/bigdata/sqoop/sqoop_import.sh"

echo ""
echo "[4/6] Hive ETL 清洗 ODS->DWD->ADS..."
hive -f "$PROJECT_DIR/bigdata/hive/etl_clean.hql" --hivevar dt=20240101

echo ""
echo "[5/6] Spark 分析并写回 MySQL 统计表..."
source /etc/profile
spark-submit --master yarn --deploy-mode client "$PROJECT_DIR/bigdata/spark/spark_analysis.py"

echo ""
echo "[6/6] 训练价格预测模型..."
python "$PROJECT_DIR/ml/train_sklearn.py"

echo ""
echo "============================================"
echo " 全部完成！"
echo " 下一步：重启 Django 加载新模型:"
echo "   bash $PROJECT_DIR/start_all.sh"
echo "============================================"

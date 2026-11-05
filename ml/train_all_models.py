#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
四模型对比训练脚本
对比：线性回归 / 随机森林 / LightGBM / XGBoost
输出：各模型指标 JSON + Markdown 对比报告
用法：python train_all_models.py
"""

import os
import sys
import json
import time
import joblib
import numpy as np
import pandas as pd
from datetime import datetime

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

import lightgbm as lgb
import xgboost as xgb

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, '..', 'data', 'dataset', 'clean_car_data.csv')
MODEL_DIR = os.path.join(BASE_DIR, 'models')
METRICS_FILE = os.path.join(MODEL_DIR, 'all_models_metrics.json')
COMPARISON_FILE = os.path.join(MODEL_DIR, 'model_comparison.md')

CATEGORICAL_COLS = ['brand', 'gearbox', 'fuel_type', 'displacement', 'city']
NUMERIC_COLS = ['age', 'mileage', 'original_price']
LABEL_COL = 'price'
ALL_FEATURES = CATEGORICAL_COLS + NUMERIC_COLS


def load_data():
    if not os.path.exists(DATA_FILE):
        print(f"[ERROR] 数据文件不存在: {DATA_FILE}")
        sys.exit(1)
    df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
    print(f"[INFO] 数据加载完成，共 {len(df)} 行")
    df = df[(df[LABEL_COL] > 0) & (df[LABEL_COL] < 500)]
    df = df[df['age'].between(0, 30)]
    df = df[df['mileage'].between(0, 50)]
    print(f"[INFO] 过滤后: {len(df)} 行")
    return df


def build_preprocessor():
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    return ColumnTransformer(transformers=[
        ('num', numeric_transformer, NUMERIC_COLS),
        ('cat', categorical_transformer, CATEGORICAL_COLS)
    ], remainder='drop')


def evaluate(y_test, y_pred, train_time, model_name, config=None):
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    mae = float(mean_absolute_error(y_test, y_pred))
    r2 = float(r2_score(y_test, y_pred))
    mape = float(np.mean(np.abs((y_test - y_pred) / y_test)) * 100)

    # 相对残差分位数：价格残差随价格规模变化，所以用 实际值/预测值 的比值分位数
    # 得到 P10/P90 后，服务端即可用 预测价*P10 ~ 预测价*P90 给出该模型的真实预测区间
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio = np.where(y_pred > 0, y_test / y_pred, np.nan)
    ratio = ratio[np.isfinite(ratio)]
    ratio_p10 = float(np.clip(np.percentile(ratio, 10) if ratio.size else 0.9, 0.3, 3.0))
    ratio_p90 = float(np.clip(np.percentile(ratio, 90) if ratio.size else 1.1, ratio_p10, 3.0))

    # 置信度由测试集误差反推（MAPE 越低越可信），截断到 [0.5, 0.99]
    confidence = float(np.clip(1 - mape / 100, 0.5, 0.99))

    print(f"  RMSE={rmse:.4f}  MAE={mae:.4f}  MAPE={mape:.2f}%  R2={r2:.4f}  "
          f"区间=[{ratio_p10:.3f}, {ratio_p90:.3f}]  置信度={confidence:.4f}  耗时={train_time:.1f}s")
    return {
        "model": model_name,
        "rmse": round(rmse, 4),
        "mae": round(mae, 4),
        "mape": round(mape, 2),
        "r2": round(r2, 4),
        "confidence": round(confidence, 4),
        "ratio_p10": round(ratio_p10, 4),
        "ratio_p90": round(ratio_p90, 4),
        "train_time_seconds": round(train_time, 2),
        "config": config or {},
    }


def train_linear_regression(X_train, X_test, y_train, y_test):
    print("\n[1/4] 线性回归 (基线)")
    pipe = Pipeline([('preprocessor', build_preprocessor()), ('regressor', LinearRegression(n_jobs=-1))])
    t0 = time.time()
    pipe.fit(X_train, y_train)
    train_time = time.time() - t0
    y_pred = pipe.predict(X_test)
    return evaluate(y_test, y_pred, train_time, "Linear Regression", {"normalize": False}), pipe


def train_random_forest(X_train, X_test, y_train, y_test):
    print("[2/4] 随机森林")
    rf = RandomForestRegressor(
        n_estimators=100, max_depth=15, min_samples_split=10,
        min_samples_leaf=5, max_features='sqrt', n_jobs=-1, random_state=42
    )
    pipe = Pipeline([('preprocessor', build_preprocessor()), ('regressor', rf)])
    t0 = time.time()
    pipe.fit(X_train, y_train)
    train_time = time.time() - t0
    y_pred = pipe.predict(X_test)
    return evaluate(y_test, y_pred, train_time, "Random Forest", {
        "n_estimators": 100, "max_depth": 15
    }), pipe


def train_lightgbm(X_train, X_test, y_train, y_test):
    print("[3/4] LightGBM")
    # LightGBM 需要类别特征为 categorical 类型
    X_train_lgb = X_train.copy()
    X_test_lgb = X_test.copy()
    for col in CATEGORICAL_COLS:
        X_train_lgb[col] = X_train_lgb[col].astype('category')
        X_test_lgb[col] = X_test_lgb[col].astype('category')

    model = lgb.LGBMRegressor(
        n_estimators=500, max_depth=-1, num_leaves=63,
        learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
        reg_alpha=0.1, reg_lambda=0.1, n_jobs=-1, random_state=42,
        verbose=-1
    )
    t0 = time.time()
    model.fit(X_train_lgb, y_train, eval_set=[(X_test_lgb, y_test)],
              callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)])
    train_time = time.time() - t0
    y_pred = model.predict(X_test_lgb)
    return evaluate(y_test, y_pred, train_time, "LightGBM", {
        "n_estimators": 500, "num_leaves": 63, "learning_rate": 0.05
    }), model


def train_xgboost(X_train, X_test, y_train, y_test):
    print("[4/4] XGBoost")
    # XGBoost 需要类别特征编码
    preprocessor = build_preprocessor()
    X_train_enc = preprocessor.fit_transform(X_train)
    X_test_enc = preprocessor.transform(X_test)

    model = xgb.XGBRegressor(
        n_estimators=500, max_depth=8, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        reg_alpha=0.1, reg_lambda=1.0, n_jobs=-1, random_state=42,
        tree_method='hist', verbosity=0
    )
    t0 = time.time()
    model.fit(X_train_enc, y_train, eval_set=[(X_test_enc, y_test)], verbose=False)
    train_time = time.time() - t0
    y_pred = model.predict(X_test_enc)
    return evaluate(y_test, y_pred, train_time, "XGBoost", {
        "n_estimators": 500, "max_depth": 8, "learning_rate": 0.05
    }), (model, preprocessor)


def generate_report(metrics_list):
    md = ["# 二手车价格预测 - 四模型对比评估报告\n",
          f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
          "## 一、模型性能对比\n",
          "| 模型 | RMSE | MAE | MAPE(%) | R² | 预测区间(×预测价) | 置信度 | 训练耗时(s) |",
          "|------|------|-----|---------|-----|------------------|--------|------------|"]
    for m in metrics_list:
        md.append(f"| {m['model']} | {m['rmse']} | {m['mae']} | {m['mape']} | {m['r2']} | "
                  f"{m.get('ratio_p10', '-')} ~ {m.get('ratio_p90', '-')} | "
                  f"{m.get('confidence', '-')} | {m['train_time_seconds']} |")

    md.append("\n## 二、模型配置\n")
    for m in metrics_list:
        md.append(f"### {m['model']}")
        for k, v in m.get('config', {}).items():
            md.append(f"- {k}: {v}")
        md.append("")

    best = min(metrics_list, key=lambda x: x['rmse'])
    md.append("## 三、分析结论\n")
    md.append(f"- **最优模型**: {best['model']} (RMSE={best['rmse']}, R²={best['r2']})")
    md.append(f"- MAPE 最低: {min(metrics_list, key=lambda x: x['mape'])['model']} "
              f"({min(m['mape'] for m in metrics_list)}%)")
    md.append(f"- 训练最快: {min(metrics_list, key=lambda x: x['train_time_seconds'])['model']} "
              f"({min(m['train_time_seconds'] for m in metrics_list)}s)")
    md.append("\n### 适用场景")
    md.append("- **线性回归**: 基线模型，解释性强，速度快，但精度最低")
    md.append("- **随机森林**: 稳定可靠，特征重要性可解释，当前生产模型")
    md.append("- **LightGBM**: 梯度提升，训练快，精度高，适合大数据场景")
    md.append("- **XGBoost**: 梯度提升，精度通常最高，但训练较慢")

    return "\n".join(md)


def main():
    print("=" * 60)
    print("二手车价格预测 - 四模型对比训练")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    df = load_data()
    X = df[ALL_FEATURES]
    y = df[LABEL_COL]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"[INFO] 训练集: {len(X_train)}, 测试集: {len(X_test)}")

    all_metrics = []
    all_models = {}

    m_lr, model_lr = train_linear_regression(X_train, X_test, y_train, y_test)
    all_metrics.append(m_lr)
    all_models['linear_regression'] = model_lr

    m_rf, model_rf = train_random_forest(X_train, X_test, y_train, y_test)
    all_metrics.append(m_rf)
    all_models['random_forest'] = model_rf

    m_lgb, model_lgb = train_lightgbm(X_train, X_test, y_train, y_test)
    all_metrics.append(m_lgb)
    all_models['lightgbm'] = model_lgb

    m_xgb, model_xgb = train_xgboost(X_train, X_test, y_train, y_test)
    all_metrics.append(m_xgb)
    all_models['xgboost'] = model_xgb

    # 保存指标
    os.makedirs(MODEL_DIR, exist_ok=True)
    with open(METRICS_FILE, 'w', encoding='utf-8') as f:
        json.dump({"metrics": all_metrics, "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
                  f, ensure_ascii=False, indent=2)
    print(f"\n[SAVED] 指标: {METRICS_FILE}")

    # 保存 LightGBM 和 XGBoost 模型
    joblib.dump(model_lgb, os.path.join(MODEL_DIR, 'lightgbm_model.joblib'))
    joblib.dump(model_xgb, os.path.join(MODEL_DIR, 'xgboost_model.joblib'))
    print(f"[SAVED] 模型文件: {MODEL_DIR}/{{lightgbm,xgboost}}_model.joblib")

    # 生成对比报告
    report = generate_report(all_metrics)
    with open(COMPARISON_FILE, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"[SAVED] 报告: {COMPARISON_FILE}")

    print("\n" + "=" * 60)
    print("四模型对比训练完成！")
    print("=" * 60)
    print(report)


if __name__ == '__main__':
    main()

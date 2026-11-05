"""
服务层 - 模型加载与预测服务
负责：加载多个模型（sklearn/lightgbm/xgboost）、执行预测、Redis缓存
"""
import os
import json
import hashlib
import logging
import joblib
import numpy as np
import pandas as pd
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger('car_api')

MODEL_DIR = getattr(settings, 'MODEL_DIR', os.path.join(settings.BASE_DIR, '..', 'ml', 'models'))
METRICS_FILE = os.path.join(MODEL_DIR, 'all_models_metrics.json')

MODEL_PATHS = {
    'sklearn': os.path.join(MODEL_DIR, 'rf_price_model.joblib'),
    'lightgbm': os.path.join(MODEL_DIR, 'lightgbm_model.joblib'),
    'xgboost': os.path.join(MODEL_DIR, 'xgboost_model.joblib'),
}

# model_type -> train_all_models.py 写入 all_models_metrics.json 的模型名
MODEL_METRIC_NAMES = {
    'sklearn': 'Random Forest',
    'lightgbm': 'LightGBM',
    'xgboost': 'XGBoost',
}

# 置信度兜底值：仅在模型指标文件缺失/无法解析时使用；
# 正常情况下置信度与预测区间由测试集相对残差推导（见 _get_model_metrics）
MODEL_CONFIDENCE = {
    'sklearn': 0.85,
    'lightgbm': 0.85,
    'xgboost': 0.85,
    'spark_mllib': 0.85,
}

# 预测区间兜底比例：无指标文件时沿用固定 ±10%
FALLBACK_RANGE_RATIO = 0.10

FEATURE_COLS = ['brand', 'gearbox', 'fuel_type', 'displacement', 'city',
                'age', 'mileage', 'original_price']


class ModelService:
    """机器学习模型服务（单例模式）"""

    _instance = None
    _models = {}
    _loaded_types = set()
    _metrics_cache = None      # {模型名: 指标dict}，随 METRICS_FILE 变化自动重载
    _metrics_mtime = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls):
        return cls()

    def load_model(self, model_type='sklearn'):
        """加载指定类型的模型"""
        if model_type in self._loaded_types and self._models.get(model_type) is not None:
            return self._models[model_type]

        model_path = MODEL_PATHS.get(model_type, MODEL_PATHS['sklearn'])
        logger.info(f"[ModelService] 正在加载 {model_type} 模型: {model_path}")

        if not os.path.exists(model_path):
            logger.error(f"[ModelService] 模型文件不存在: {model_path}")
            self._loaded_types.add(model_type)
            return None

        try:
            model = joblib.load(model_path)
            self._models[model_type] = model
            self._loaded_types.add(model_type)
            logger.info(f"[ModelService] {model_type} 模型加载成功，类型: {type(model).__name__}")
            return model
        except Exception as e:
            logger.error(f"[ModelService] {model_type} 模型加载失败: {e}")
            self._loaded_types.add(model_type)
            return None

    def _get_model_metrics(self, model_type):
        """读取训练脚本产出的测试集指标（含相对残差区间与置信度）

        文件缺失或解析失败时返回 None，调用方回退到固定 ±10% 区间与兜底置信度，
        保证不重新训练也能继续对外服务。
        """
        try:
            mtime = os.path.getmtime(METRICS_FILE)
        except OSError:
            return None

        if self._metrics_cache is None or self._metrics_mtime != mtime:
            try:
                with open(METRICS_FILE, 'r', encoding='utf-8') as f:
                    payload = json.load(f)
                self._metrics_cache = {
                    item.get('model'): item for item in payload.get('metrics', [])
                }
                self._metrics_mtime = mtime
                logger.info(f"[ModelService] 模型指标已加载: {list(self._metrics_cache)}")
            except Exception as e:
                logger.warning(f"[ModelService] 指标文件解析失败，回退固定区间: {e}")
                self._metrics_cache = {}
                self._metrics_mtime = mtime

        return self._metrics_cache.get(MODEL_METRIC_NAMES.get(model_type, ''))

    def _generate_cache_key(self, params):
        params_str = json.dumps(params, sort_keys=True, ensure_ascii=False)
        # 拼入模型与指标文件的修改时间，重新训练后旧缓存自动失效
        versions = []
        for path in (MODEL_PATHS.get(params.get('model_type', 'sklearn'), ''), METRICS_FILE):
            try:
                versions.append(str(int(os.path.getmtime(path))))
            except OSError:
                versions.append('0')
        return f"predict:{hashlib.md5(params_str.encode()).hexdigest()}:" + "-".join(versions)

    def _build_features(self, params):
        """构建特征DataFrame"""
        feature_data = {
            'brand': [params.get('brand', '大众')],
            'gearbox': [params.get('gearbox', '自动')],
            'fuel_type': [params.get('fuel_type', '汽油')],
            'displacement': [params.get('displacement', '2.0L')],
            'city': [params.get('city', '北京')],
            'age': [float(params.get('age', 3))],
            'mileage': [float(params.get('mileage', 5.0))],
            'original_price': [float(params.get('original_price', 15.0))],
        }
        return pd.DataFrame(feature_data)[FEATURE_COLS]

    def _predict_with_model(self, model, X, model_type):
        """根据模型类型执行预测，返回 predicted_price"""
        if model_type == 'sklearn':
            # Pipeline: preprocessor + regressor
            return float(model.predict(X)[0])

        elif model_type == 'lightgbm':
            # LGBMRegressor 需要将字符串列转为 category 类型
            cat_cols = ['brand', 'gearbox', 'fuel_type', 'displacement', 'city']
            X_cat = X.copy()
            for col in cat_cols:
                X_cat[col] = X_cat[col].astype('category')
            return float(model.predict(X_cat)[0])

        elif model_type == 'xgboost':
            # tuple (XGBRegressor, ColumnTransformer)
            if isinstance(model, tuple) and len(model) == 2:
                xgb_model, preprocessor = model
                Xt = preprocessor.transform(X)
                if hasattr(Xt, 'toarray'):
                    Xt = Xt.toarray()
                return float(xgb_model.predict(Xt)[0])
            # 兜底：直接 predict
            return float(model.predict(X)[0])

        else:
            # spark_mllib 等回退到 sklearn 逻辑
            if hasattr(model, 'predict'):
                return float(model.predict(X)[0])
            raise ValueError(f"不支持的模型类型: {model_type}")

    def predict_batch(self, df, model_type='sklearn'):
        """批量预测（向量化）

        复用单例中已加载的模型，避免每个 Celery 任务重复 joblib.load。
        df 需包含 FEATURE_COLS，缺失列由调用方补齐。
        返回预测值列表；模型不可用时返回 None。
        """
        effective_type = 'sklearn' if model_type == 'spark_mllib' else model_type
        model = self.load_model(effective_type)
        if model is None:
            return None

        try:
            if effective_type == 'lightgbm':
                X = df[FEATURE_COLS].copy()
                for col in ['brand', 'gearbox', 'fuel_type', 'displacement', 'city']:
                    X[col] = X[col].astype('category')
                preds = model.predict(X)
            elif effective_type == 'xgboost' and isinstance(model, tuple) and len(model) == 2:
                xgb_model, preprocessor = model
                Xt = preprocessor.transform(df[FEATURE_COLS])
                if hasattr(Xt, 'toarray'):
                    Xt = Xt.toarray()
                preds = xgb_model.predict(Xt)
            else:
                preds = model.predict(df[FEATURE_COLS])
            return [float(v) for v in preds]
        except Exception as e:
            logger.error(f"[ModelService] 批量预测失败 ({effective_type}): {e}", exc_info=True)
            return None

    def predict(self, params):
        """执行价格预测"""
        model_type = params.get('model_type', 'sklearn')

        # spark_mllib 没有本地模型，回退到 sklearn
        effective_type = 'sklearn' if model_type == 'spark_mllib' else model_type

        # 1. 检查缓存
        cache_key = self._generate_cache_key(params)
        cached = cache.get(cache_key)
        if cached:
            logger.info(f"[ModelService] 缓存命中: {cache_key}")
            return cached

        # 2. 加载模型
        model = self.load_model(effective_type)

        # 3. 构建特征
        X = self._build_features(params)

        # 4. 预测
        if model is not None:
            try:
                predicted_price = round(self._predict_with_model(model, X, effective_type), 2)
                confidence = MODEL_CONFIDENCE.get(effective_type, 0.85)
            except Exception as e:
                import traceback
                logger.error(f"[ModelService] {effective_type} 预测失败: {e}", exc_info=True)
                predicted_price = self._fallback_predict(params)
                model_type = 'fallback'
                confidence = 0.5
        else:
            predicted_price = self._fallback_predict(params)
            model_type = 'fallback'
            confidence = 0.5

        # 5. 价格区间与置信度：优先由该模型在测试集上的相对残差推导，指标文件缺失时回退固定 ±10%
        metrics = self._get_model_metrics(effective_type) if model_type != 'fallback' else None
        if metrics and metrics.get('ratio_p10') and metrics.get('ratio_p90'):
            price_range = {
                'min': round(predicted_price * float(metrics['ratio_p10']), 2),
                'max': round(predicted_price * float(metrics['ratio_p90']), 2),
                'unit': '万元'
            }
            confidence = float(metrics.get('confidence') or MODEL_CONFIDENCE.get(effective_type, 0.85))
            confidence_source = 'model_metrics'
        else:
            price_range = {
                'min': round(predicted_price * (1 - FALLBACK_RANGE_RATIO), 2),
                'max': round(predicted_price * (1 + FALLBACK_RANGE_RATIO), 2),
                'unit': '万元'
            }
            confidence_source = 'fallback_rule' if model_type == 'fallback' else 'default'

        # 6. SHAP 影响因子解释
        explain = self._explain_prediction(model, X, effective_type)

        result = {
            'predicted_price': predicted_price,
            'model_type': model_type,
            'confidence': confidence,
            'confidence_source': confidence_source,
            'price_range': price_range,
            'explain': explain,
            'input_params': params
        }

        # 7. 写入缓存
        try:
            cache.set(cache_key, result, timeout=600)
        except Exception as e:
            logger.warning(f"[ModelService] 缓存写入失败: {e}")

        logger.info(f"[ModelService] 预测完成: {params.get('brand')} "
                    f"车龄{params.get('age')}年 -> {predicted_price}万元 "
                    f"(模型: {model_type})")

        return result

    def _explain_prediction(self, model, X, model_type='sklearn'):
        """SHAP 特征影响因子解释"""
        try:
            if model is None:
                return None

            import shap

            regressor = None
            preprocessor = None

            if model_type == 'sklearn' and hasattr(model, 'named_steps'):
                regressor = model.named_steps.get('regressor')
                preprocessor = model.named_steps.get('preprocessor')
            elif model_type == 'xgboost' and isinstance(model, tuple) and len(model) == 2:
                regressor, preprocessor = model
            elif model_type == 'lightgbm':
                regressor = model
                # LightGBM 不需要预处理器，直接用原始特征名
                explainer = shap.TreeExplainer(regressor)
                shap_values = explainer.shap_values(X)[0]
                label_map = {
                    'age': '车龄', 'mileage': '行驶里程', 'original_price': '新车价格',
                    'brand': '品牌', 'gearbox': '变速箱', 'fuel_type': '燃油类型',
                    'displacement': '排量', 'city': '城市'
                }
                explain = []
                for name, v in zip(FEATURE_COLS, shap_values):
                    if abs(v) >= 0.05:
                        explain.append({
                            'feature': name,
                            'label': label_map.get(name, name),
                            'impact': round(float(v), 2),
                            'direction': 'up' if v > 0 else 'down'
                        })
                explain.sort(key=lambda x: abs(x['impact']), reverse=True)
                return explain
            else:
                return None

            if regressor is None or preprocessor is None:
                return None

            explainer = shap.TreeExplainer(regressor, feature_perturbation='tree_path_dependent')
            Xt = preprocessor.transform(X)
            if hasattr(Xt, 'toarray'):
                Xt = Xt.toarray()
            shap_values = explainer.shap_values(Xt)[0]

            # 特征名：数值3列 + 类别one-hot列
            num_names = ['age', 'mileage', 'original_price']
            cat_encoder = preprocessor.named_transformers_['cat'].named_steps['onehot']
            cat_names = list(cat_encoder.get_feature_names_out(
                ['brand', 'gearbox', 'fuel_type', 'displacement', 'city']
            ))
            names = num_names + cat_names

            label_map = {
                'age': '车龄', 'mileage': '行驶里程', 'original_price': '新车价格',
                'brand': '品牌', 'gearbox': '变速箱', 'fuel_type': '燃油类型',
                'displacement': '排量', 'city': '城市'
            }
            raw_fields = list(label_map.keys())
            impacts = {f: 0.0 for f in raw_fields}
            for name, v in zip(names, shap_values):
                if name in impacts:
                    impacts[name] = float(v)
                else:
                    prefix = name.split('_')[0]
                    if prefix in impacts:
                        impacts[prefix] += float(v)

            explain = []
            for f in raw_fields:
                v = impacts[f]
                if abs(v) >= 0.05:
                    explain.append({
                        'feature': f,
                        'label': label_map[f],
                        'impact': round(v, 2),
                        'direction': 'up' if v > 0 else 'down'
                    })
            explain.sort(key=lambda x: abs(x['impact']), reverse=True)
            return explain

        except Exception as e:
            logger.warning(f"[ModelService] SHAP 解释失败 ({model_type}): {e}")
            return None

    def _fallback_predict(self, params):
        """兜底预测：基于折旧规则"""
        original_price = float(params.get('original_price', 15.0))
        age = float(params.get('age', 3))
        mileage = float(params.get('mileage', 5.0))

        if age <= 1:
            depreciation = 0.82
        elif age <= 3:
            depreciation = 0.65
        elif age <= 5:
            depreciation = 0.50
        elif age <= 8:
            depreciation = 0.38
        elif age <= 12:
            depreciation = 0.26
        else:
            depreciation = 0.15

        mileage_factor = max(0.6, 1.0 - mileage * 0.015)

        brand = params.get('brand', '')
        premium_brands = ['宝马', '奔驰', '奥迪', '雷克萨斯', '保时捷', '特斯拉', '蔚来', '理想']
        brand_factor = 1.05 if brand in premium_brands else 1.0

        predicted = original_price * depreciation * mileage_factor * brand_factor
        return round(max(predicted, 0.5), 2)

    def get_model_info(self):
        """获取模型信息"""
        model = self.load_model('sklearn')
        info = {
            'model_loaded': model is not None,
            'model_type': 'sklearn_random_forest' if model else 'fallback',
            'model_path': MODEL_PATHS.get('sklearn', ''),
        }
        if model is not None and hasattr(model, 'named_steps'):
            regressor = model.named_steps.get('regressor')
            if regressor:
                info['n_estimators'] = getattr(regressor, 'n_estimators', None)
                info['max_depth'] = getattr(regressor, 'max_depth', None)

        info['available_models'] = []
        for mt, path in MODEL_PATHS.items():
            loaded = mt in self._loaded_types and self._models.get(mt) is not None
            info['available_models'].append({
                'type': mt,
                'loaded': loaded,
                'path': path,
                'exists': os.path.exists(path),
            })

        return info


model_service = ModelService.get_instance()

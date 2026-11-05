"""
后端增强模块
包含：
1. 实时热门搜索 API（从 Redis 读取 Kafka 聚合结果）
2. Redis 缓存装饰器
3. API 限流中间件
4. 批量预测 Celery 任务
"""

import json
import time
import os
import hashlib
import logging
import pandas as pd
from functools import wraps
from datetime import datetime

from django.core.cache import cache
from django.http import JsonResponse
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger('car_api')

# 批量预测输入列与缺失值默认值（与 ModelService._build_features 的默认值保持一致）
CATEGORICAL_COLS = ['brand', 'gearbox', 'fuel_type', 'displacement', 'city']
NUMERIC_COLS = ['age', 'mileage', 'original_price']
BATCH_DEFAULTS = {
    'brand': '大众', 'gearbox': '自动', 'fuel_type': '汽油',
    'displacement': '2.0L', 'city': '北京',
    'age': 3.0, 'mileage': 5.0, 'original_price': 15.0,
}


def _build_batch_frame(batch):
    """构造批量预测输入：缺失列按各自列默认值补齐"""
    df = pd.DataFrame(batch)
    for col, default in BATCH_DEFAULTS.items():
        if col not in df.columns:
            df[col] = default
        elif col in NUMERIC_COLS:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(default)
        else:
            df[col] = df[col].fillna(default)
    return df[CATEGORICAL_COLS + NUMERIC_COLS]


# ============================================================
# 1. 实时热门搜索 API
# ============================================================

def _realtime_redis():
    """复用 Django CACHES 配置连接 Redis（供 realtime_hot / realtime_alerts 共用）"""
    import redis as redis_lib
    redis_host = getattr(settings, 'CACHES', {}).get('default', {}).get('LOCATION', '')
    if 'redis://' in redis_host:
        redis_host = redis_host.split('redis://')[1].split('/')[0]
        r_host = redis_host.split(':')[0]
        r_port = int(redis_host.split(':')[1]) if ':' in redis_host else 6379
    else:
        r_host = 'localhost'
        r_port = 6379
    return redis_lib.Redis(host=r_host, port=r_port, decode_responses=True, socket_timeout=3)


@api_view(['GET'])
@permission_classes([AllowAny])
def realtime_hot(request):
    """
    实时热门搜索 API
    从 Redis 读取 Kafka 流处理聚合结果
    返回：热门品牌 Top10、热门车型 Top10、总搜索量、价格异常预警、状态
    """
    try:
        r = _realtime_redis()

        top_brands = r.get('used_car:realtime:top_brands')
        top_models = r.get('used_car:realtime:top_models')
        total_events = r.get('used_car:realtime:total_events') or 0
        last_update = r.get('used_car:realtime:last_update') or ''
        rt_status = r.get('used_car:realtime:status') or 'unknown'

        # 价格异常预警（由 streaming_consumer 写入，最近 20 条）
        recent_alerts = []
        for raw in r.lrange('used_car:realtime:alerts', 0, 19):
            try:
                recent_alerts.append(json.loads(raw))
            except (TypeError, ValueError):
                continue

        return Response({
            'code': 200,
            'message': 'success',
            'data': {
                'status': rt_status,
                'total_search_events': int(total_events),
                'last_update': last_update,
                'top_brands': json.loads(top_brands) if top_brands else [],
                'top_models': json.loads(top_models) if top_models else [],
                'recent_alerts': recent_alerts,
            }
        })
    except Exception as e:
        logger.warning(f"Redis realtime read failed: {e}")
        return Response({
            'code': 503,
            'message': '实时数据服务暂时不可用',
            'data': {
                'status': 'unavailable',
                'top_brands': [],
                'top_models': [],
                'recent_alerts': [],
            }
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


# ============================================================
# 1.2 预警中心 API（价格异常预警时间线）
# ============================================================

def _alert_level(deviation):
    """根据偏差幅度划分预警等级"""
    try:
        d = abs(float(deviation))
    except (TypeError, ValueError):
        return '低'
    if d >= 0.5:
        return '高'
    if d >= 0.3:
        return '中'
    return '低'


@api_view(['GET'])
@permission_classes([AllowAny])
def realtime_alerts(request):
    """
    预警中心：读取最近的价格异常预警（streaming_consumer 写入 Redis 列表）
    参数：level(可选, 高/中/低), limit(可选, 默认100, 上限200)
    返回：预警列表（派生 level 字段）+ 流处理状态
    """
    level = (request.query_params.get('level') or '').strip()
    try:
        limit = min(int(request.query_params.get('limit', 100)), 200)
    except (TypeError, ValueError):
        limit = 100

    try:
        r = _realtime_redis()
        raws = r.lrange('used_car:realtime:alerts', 0, limit - 1)
        rt_status = r.get('used_car:realtime:status') or 'unknown'
        last_update = r.get('used_car:realtime:last_update') or ''
        total_events = r.get('used_car:realtime:total_events') or 0

        alerts = []
        for raw in raws:
            try:
                item = json.loads(raw)
            except (TypeError, ValueError):
                continue
            if not isinstance(item, dict):
                continue
            item = dict(item)
            item['level'] = item.get('level') or _alert_level(item.get('deviation'))
            if level and item['level'] != level:
                continue
            alerts.append(item)

        level_stat = {'高': 0, '中': 0, '低': 0}
        for a in alerts:
            if a.get('level') in level_stat:
                level_stat[a['level']] += 1

        return Response({
            'code': 200,
            'message': 'success',
            'data': {
                'alerts': alerts,
                'count': len(alerts),
                'level_stat': level_stat,
                'status': rt_status,
                'last_update': last_update,
                'total_search_events': int(total_events or 0),
            }
        })
    except Exception as e:
        logger.warning(f"Redis alerts read failed: {e}")
        return Response({
            'code': 503,
            'message': '预警数据服务暂时不可用',
            'data': {'alerts': [], 'count': 0, 'level_stat': {'高': 0, '中': 0, '低': 0},
                     'status': 'unavailable', 'last_update': '', 'total_search_events': 0}
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


# ============================================================
# 2. Redis 缓存装饰器
# ============================================================

def redis_cache(timeout=300, key_prefix='api'):
    """
    Redis 缓存装饰器
    根据请求路径 + 查询参数生成缓存 key
    用法：
        @api_view(['GET'])
        @permission_classes([AllowAny])
        @redis_cache(timeout=300, key_prefix='cars')
        def my_view(request):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if request.method != 'GET':
                return func(request, *args, **kwargs)

            cache_key = f"{key_prefix}:{request.get_full_path()}"
            cache_key = hashlib.md5(cache_key.encode()).hexdigest()
            cache_key = f"used_car:view:{cache_key}"

            cached = cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                from rest_framework.response import Response as DRFResponse
                return DRFResponse(cached, status=status.HTTP_200_OK)

            logger.debug(f"Cache MISS: {cache_key}")
            response = func(request, *args, **kwargs)

            if hasattr(response, 'data') and response.status_code == 200:
                cache.set(cache_key, response.data, timeout)

            return response
        return wrapper
    return decorator


# ============================================================
# 3. API 限流中间件
# ============================================================

_RATE_REDIS = None


def _get_rate_redis():
    """模块级单例 Redis 连接池

    原实现每个请求都 redis.Redis(...) 新建一次连接（TCP 三次握手 + AUTH），
    在 gthread 多线程模式下还会迅速耗尽 fd；改为进程内复用连接池，
    多线程共享时 redis-py 自身保证线程安全。
    """
    global _RATE_REDIS
    if _RATE_REDIS is None:
        import redis as redis_lib
        pool = redis_lib.ConnectionPool(
            host='localhost', port=6379, decode_responses=True,
            socket_timeout=1, max_connections=64)
        _RATE_REDIS = redis_lib.Redis(connection_pool=pool)
    return _RATE_REDIS


class RateLimitMiddleware:
    """
    简单 API 限流中间件（基于 Redis 令牌桶）
    限制每个 IP 每分钟最多 300 次请求
    在 settings.py MIDDLEWARE 中添加即可
    """
    RATE_LIMIT = 300
    WINDOW = 60

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith('/api/'):
            return self.get_response(request)

        try:
            r = _get_rate_redis()
            client_ip = self.get_client_ip(request)
            key = f"used_car:rate:{client_ip}"
            current = r.incr(key)
            if current == 1:
                r.expire(key, self.WINDOW)
            if current > self.RATE_LIMIT:
                return JsonResponse({
                    'code': 429,
                    'message': '请求过于频繁，请稍后再试',
                    'data': None
                }, status=429)
        except Exception:
            pass

        return self.get_response(request)

    def get_client_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')


# ============================================================
# 4. 批量预测 Celery 任务
# ============================================================

from celery import shared_task

@shared_task(bind=True)
def batch_predict_task(self, car_data_list, model_type='sklearn'):
    """
    批量预测 Celery 任务
    输入：车辆数据列表 [{"brand":"大众","age":3,...}, ...]
    输出：预测价格列表 [{"index":0,"predicted_price":8.5,"status":"ok"}, ...]

    模型统一由 ModelService 单例加载，任务之间复用同一份内存模型，不再重复 joblib.load。
    """
    from .services import model_service

    total = len(car_data_list)
    if total == 0:
        return []

    results = []
    batch_size = 100

    for start in range(0, total, batch_size):
        batch = car_data_list[start:start + batch_size]
        df = _build_batch_frame(batch)

        predictions = model_service.predict_batch(df, model_type)
        if predictions is None:
            logger.error(f"批量预测不可用：模型 {model_type} 未加载")
            results.extend(
                {"index": start + i, "predicted_price": 0, "status": "model_unavailable"}
                for i in range(len(batch))
            )
        else:
            results.extend(
                {"index": start + i, "predicted_price": round(pred, 2), "status": "ok"}
                for i, pred in enumerate(predictions)
            )

        progress = min(100, int((start + len(batch)) / total * 100))
        self.update_state(state='PROGRESS', meta={'progress': progress})

    return results


@api_view(['POST'])
@permission_classes([AllowAny])
def batch_predict(request):
    """
    批量预测接口
    POST /api/prediction/batch/
    Body: {"cars": [{"brand":"大众","age":3,"mileage":4.5,...}, ...]}
    返回：task_id，前端轮询 /api/prediction/batch/status/ 获取结果
    """
    cars = request.data.get('cars', [])
    if not cars or len(cars) > 1000:
        return Response({
            'code': 400,
            'message': '请提供 1-1000 条车辆数据',
            'data': None
        }, status=status.HTTP_400_BAD_REQUEST)

    task = batch_predict_task.delay(cars)
    return Response({
        'code': 200,
        'message': '批量预测任务已提交',
        'data': {
            'task_id': task.id,
            'total': len(cars),
        }
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def batch_predict_status(request):
    """
    批量预测结果查询
    GET /api/prediction/batch/status/?task_id=xxx
    """
    from celery.result import AsyncResult
    task_id = request.query_params.get('task_id', '')
    if not task_id:
        return Response({'code': 400, 'message': '缺少 task_id'}, status=400)

    result = AsyncResult(task_id)
    if result.ready():
        if result.successful():
            return Response({
                'code': 200,
                'message': '预测完成',
                'data': {
                    'status': 'success',
                    'results': result.result,
                }
            })
        else:
            return Response({
                'code': 500,
                'message': '预测任务失败',
                'data': {'status': 'failed'}
            }, status=500)
    else:
        progress = 0
        if result.state == 'PROGRESS' and result.info:
            progress = result.info.get('progress', 0)
        return Response({
            'code': 200,
            'message': '预测中...',
            'data': {
                'status': 'pending',
                'progress': progress,
            }
        })


# ============================================================
# 5. 数据导出中心（CSV 流式下载）
# ============================================================

from .models import CarInfo

EXPORT_MAX_ROWS = 100000
EXPORT_COLUMNS = ['car_id', 'brand', 'series', 'model', 'price', 'original_price',
                  'age', 'mileage', 'gearbox', 'displacement', 'fuel_type',
                  'color', 'city', 'register_date']
EXPORT_HEADERS = ['车辆编号', '品牌', '车系', '车型', '售价(万)', '新车指导价(万)',
                  '车龄(年)', '里程(万公里)', '变速箱', '排量', '燃油类型',
                  '颜色', '城市', '上牌日期']


def _csv_cell(v):
    """CSV 单元格转义：含逗号/引号/换行时加双引号包裹"""
    if v is None:
        return ''
    s = str(v)
    if any(ch in s for ch in ',\n"'):
        return '"' + s.replace('"', '""') + '"'
    return s


@api_view(['GET'])
@permission_classes([AllowAny])
def export_csv(request):
    """
    条件筛选导出 CSV（StreamingHttpResponse 流式输出，避免大结果集占内存）
    参数：brand / city / fuel_type / min_price / max_price / min_age / max_age / limit(上限10万)
    """
    from django.http import StreamingHttpResponse

    qs = CarInfo.objects.all().order_by('id')
    brand = (request.query_params.get('brand') or '').strip()
    city = (request.query_params.get('city') or '').strip()
    fuel_type = (request.query_params.get('fuel_type') or '').strip()
    if brand:
        qs = qs.filter(brand=brand)
    if city:
        qs = qs.filter(city=city)
    if fuel_type:
        qs = qs.filter(fuel_type=fuel_type)
    for name, lookup in [('min_price', 'price__gte'), ('max_price', 'price__lte'),
                         ('min_age', 'age__gte'), ('max_age', 'age__lte')]:
        raw = (request.query_params.get(name) or '').strip()
        if raw:
            try:
                qs = qs.filter(**{lookup: float(raw)})
            except ValueError:
                pass
    try:
        limit = min(int(request.query_params.get('limit', EXPORT_MAX_ROWS)), EXPORT_MAX_ROWS)
    except ValueError:
        limit = EXPORT_MAX_ROWS

    header = ','.join(EXPORT_HEADERS)

    def _gen():
        buf = ['\ufeff' + header]  # UTF-8 BOM，保证 Excel 中文不乱码
        n = 0
        # 必须在 SQL 层加 LIMIT：MySQL 客户端驱动会缓冲整个结果集，
        # 否则即使 Python 侧提前 break，100 万行仍会全量传输（实测 limit=3 耗时 18s）
        for obj in qs[:limit].iterator(chunk_size=2000):
            row = []
            for col in EXPORT_COLUMNS:
                v = getattr(obj, col)
                if col == 'register_date' and v is not None:
                    v = v.strftime('%Y-%m-%d')
                row.append(_csv_cell(v))
            buf.append(','.join(row))
            n += 1
            if len(buf) >= 1000:
                yield '\n'.join(buf) + '\n'
                buf = []
        if buf:
            yield '\n'.join(buf) + '\n'

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    resp = StreamingHttpResponse(_gen(), content_type='text/csv; charset=utf-8')
    resp['Content-Disposition'] = f'attachment; filename="cars_export_{ts}.csv"'
    resp['X-Export-Limit'] = str(limit)
    return resp


# ============================================================
# 6. 运维日志（管理员）
# ============================================================

from rest_framework.permissions import IsAdminUser
import collections

LOG_FILES = {
    'gunicorn_access': '/opt/used-car-price-cluster/logs/gunicorn_access.log',
    'gunicorn_error': '/opt/used-car-price-cluster/logs/gunicorn_error.log',
    'django': '/opt/used-car-price-cluster/logs/django.log',
    'celery': '/opt/used-car-price-cluster/logs/celery.log',
    'warmup': '/opt/used-car-price-cluster/logs/warmup.log',
    'streaming': '/opt/used-car-price-cluster/logs/streaming.log',
    'nginx_access': '/var/log/nginx/access.log',
    'nginx_error': '/var/log/nginx/error.log',
}


@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_logs(request):
    """
    运维日志尾部（仅管理员）
    参数：name（日志名，见 LOG_FILES）、lines（默认200，上限500）
    """
    name = (request.query_params.get('name') or 'gunicorn_error').strip()
    if name not in LOG_FILES:
        return Response({'code': 400, 'message': f'未知日志名，可选: {", ".join(LOG_FILES)}', 'data': None},
                        status=status.HTTP_400_BAD_REQUEST)
    try:
        lines = min(max(int(request.query_params.get('lines', 200)), 10), 500)
    except ValueError:
        lines = 200

    path = LOG_FILES[name]
    try:
        st = os.stat(path)
    except OSError as e:
        return Response({'code': 404, 'message': f'日志文件不存在: {e}', 'data': None},
                        status=status.HTTP_404_NOT_FOUND)

    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            tail = list(collections.deque(f, maxlen=lines))
    except OSError as e:
        return Response({'code': 500, 'message': f'日志读取失败: {e}', 'data': None},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({
        'code': 200,
        'message': 'success',
        'data': {
            'name': name,
            'path': path,
            'size': st.st_size,
            'mtime': datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            'returned': len(tail),
            'lines': [l.rstrip('\n') for l in tail],
        }
    })

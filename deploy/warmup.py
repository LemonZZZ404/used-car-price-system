#!/opt/used-car-price-cluster/backend/venv/bin/python
"""
缓存预热：定时访问聚合接口，把 Redis 缓存提前填好，
避免用户踩到冷缓存（冷查询 1-4s，热查询 0ms）。

两种触发方式：
  1) crontab 每 5 分钟：
     */5 * * * * /opt/.../venv/bin/python /opt/.../deploy/warmup.py >> /opt/.../logs/warmup.log 2>&1
  2) 后端服务启动时（car-backend.service 的 ExecStartPost）：
     /opt/.../venv/bin/python /opt/.../deploy/warmup.py --wait 10
     （--wait 用于等 gunicorn 把 8000 端口监听起来）

脚本必须始终以 0 退出：ExecStartPost 失败会把整个 unit 标记为 failed。
"""
import json
import sys
import time
import urllib.parse
import urllib.request

BASE = 'http://127.0.0.1'
SLOW_THRESHOLD = 1.0

# 匿名聚合接口（全站首屏 + 可视化接口）
ENDPOINTS = [
    '/api/cars/ranking/',
    '/api/cars/market/',
    '/api/cars/monthly/',
    '/api/cars/series/',
    '/api/dashboard/summary/',
    '/api/viz/province-heatmap/',
    '/api/viz/brand-hierarchy/',
    '/api/viz/price-trend/',
    '/api/viz/brand-radar/',
    '/api/viz/price-scatter/',
]

# 车系详情是「按车系」缓存的，无法枚举，改为从车系列表里取热度最高的前 N 个预热
TOP_SERIES = 8
TOP_BRANDS = 4


def fetch(path, timeout=90):
    """请求接口，返回 (解析后的 data, 耗时秒)"""
    start = time.time()
    with urllib.request.urlopen(BASE + path, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode('utf-8'))
    return payload.get('data'), time.time() - start


def main():
    stamp = time.strftime('%Y-%m-%d %H:%M:%S')

    # --wait N：等服务启动后端口就绪（供 systemd ExecStartPost 使用）
    wait = 0
    if '--wait' in sys.argv:
        try:
            wait = int(sys.argv[sys.argv.index('--wait') + 1])
        except (IndexError, ValueError):
            wait = 10
    if wait > 0:
        time.sleep(wait)

    slow = []
    for path in ENDPOINTS:
        start = time.time()
        try:
            fetch(path)
        except Exception as exc:  # noqa: BLE001
            slow.append('%s ERR %s' % (path, str(exc)[:40]))
            continue
        cost = time.time() - start
        if cost > SLOW_THRESHOLD:
            slow.append('%s %.2fs' % (path, cost))

    # 车系列表预热时顺带取回 top 车系名，用于预热车系详情（按热度顺序，额度内）
    extra = 0
    try:
        listing, _ = fetch('/api/cars/series/?limit=60')
        items = (listing or {}).get('items') or []
        brands = (listing or {}).get('brands') or []
    except Exception as exc:  # noqa: BLE001
        items, brands = [], []
        slow.append('series_list ERR %s' % str(exc)[:40])

    for it in items[:TOP_SERIES]:
        series = it.get('series')
        if not series:
            continue
        path = '/api/cars/series_detail/?series=' + urllib.parse.quote(series)
        start = time.time()
        try:
            fetch(path)
            extra += 1
        except Exception as exc:  # noqa: BLE001
            slow.append('%s ERR %s' % (path, str(exc)[:30]))
            continue
        cost = time.time() - start
        if cost > SLOW_THRESHOLD:
            slow.append('%s %.2fs' % (path, cost))

    # 筛选型车系列表（车型库下拉切换品牌时命中）
    for b in brands[:TOP_BRANDS]:
        path = '/api/cars/series/?brand=' + urllib.parse.quote(b)
        try:
            fetch(path)
            extra += 1
        except Exception as exc:  # noqa: BLE001
            slow.append('%s ERR %s' % (path, str(exc)[:30]))

    print('%s warmup done | extra=%d%s'
          % (stamp, extra,
             (' | slow: ' + '; '.join(slow)) if slow else ''))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print('%s warmup FAILED %s'
              % (time.strftime('%Y-%m-%d %H:%M:%S'), str(exc)[:100]))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时流处理消费者
功能：
1. 从 Kafka topic car_search_events 消费用户搜索事件
2. 滑动窗口统计热门车型 Top10（5分钟窗口，1分钟滑动）
3. 结果写入 Redis，供 Django API 实时读取
4. 价格异常预警（预测偏差 >30% 的记录推送到 alert topic）

用法：python streaming_consumer.py
依赖：kafka-python, redis, joblib, pandas, scikit-learn
"""

import os
import sys
import json
import time
import signal
from collections import defaultdict, deque
from datetime import datetime

import redis
from kafka import KafkaConsumer, KafkaProducer

# ============ 配置 ============
KAFKA_BROKERS = os.getenv('KAFKA_BROKERS', '192.168.249.101:9092,192.168.249.102:9092,192.168.249.103:9092')
KAFKA_TOPIC = 'car_search_events'
KAFKA_ALERT_TOPIC = 'car_price_alerts'
KAFKA_GROUP = 'streaming-consumer-v2'

REDIS_HOST = os.getenv('REDIS_HOST', '192.168.249.101')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))

WINDOW_SIZE = 300      # 窗口大小：5分钟（秒）
WINDOW_SLIDE = 60      # 滑动间隔：1分钟（秒）
TOP_N = 10             # 热门榜单数量
ALERT_THRESHOLD = 0.30  # 价格异常阈值：30%

# 事件结构：{"brand": "大众", "model": "朗逸", "price": 8.5, "predicted": 7.2,
#          "action": "search", "city": "北京", "timestamp": 1699000000}


class SlidingWindowAggregator:
    """滑动窗口聚合器"""

    def __init__(self, window_size, slide_interval):
        self.window_size = window_size
        self.slide_interval = slide_interval
        self.events = deque()  # (timestamp, event_dict)
        self.brand_counts = defaultdict(int)
        self.model_counts = defaultdict(int)
        self.brand_prices = defaultdict(list)

    def add_event(self, event):
        """添加事件到窗口"""
        ts = event.get('timestamp', time.time())
        self.events.append((ts, event))
        brand = event.get('brand', '未知')
        model = event.get('model', '未知')
        price = event.get('price')
        self.brand_counts[brand] += 1
        self.model_counts[f"{brand}|{model}"] += 1
        if price and isinstance(price, (int, float)):
            self.brand_prices[brand].append(price)

    def evict_expired(self, current_time):
        """淘汰过期事件"""
        cutoff = current_time - self.window_size
        while self.events and self.events[0][0] < cutoff:
            _, event = self.events.popleft()
            brand = event.get('brand', '未知')
            model = event.get('model', '未知')
            self.brand_counts[brand] = max(0, self.brand_counts[brand] - 1)
            key = f"{brand}|{model}"
            self.model_counts[key] = max(0, self.model_counts[key] - 1)
            price = event.get('price')
            if price and brand in self.brand_prices:
                try:
                    self.brand_prices[brand].remove(price)
                except ValueError:
                    pass
                if not self.brand_prices[brand]:
                    del self.brand_prices[brand]

    def get_top_brands(self, n=10):
        """获取热门品牌 Top N"""
        sorted_brands = sorted(self.brand_counts.items(), key=lambda x: x[1], reverse=True)
        result = []
        for brand, count in sorted_brands[:n]:
            prices = self.brand_prices.get(brand, [])
            avg_price = sum(prices) / len(prices) if prices else 0
            result.append({
                'brand': brand,
                'search_count': count,
                'avg_price': round(avg_price, 2),
            })
        return result

    def get_top_models(self, n=10):
        """获取热门车型 Top N"""
        sorted_models = sorted(self.model_counts.items(), key=lambda x: x[1], reverse=True)
        result = []
        for key, count in sorted_models[:n]:
            brand, model = key.rsplit('|', 1) if '|' in key else (key, '')
            result.append({
                'brand': brand,
                'model': model,
                'search_count': count,
            })
        return result

    def total_events(self):
        return len(self.events)


def create_redis():
    """创建 Redis 连接"""
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
        socket_connect_timeout=5,
    )


def safe_deserialize(raw):
    """脏消息防御：解析失败返回 None，由消费循环跳过"""
    try:
        return json.loads(raw.decode('utf-8'))
    except Exception as e:
        print(f"[WARN] 消息反序列化失败，已跳过: {e}")
        return None


def create_consumer():
    """创建 Kafka 消费者"""
    return KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BROKERS.split(','),
        group_id=KAFKA_GROUP,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        auto_commit_interval_ms=5000,
        value_deserializer=safe_deserialize,
        consumer_timeout_ms=300000,
    )


def create_producer():
    """创建预警生产者"""
    return KafkaProducer(
        bootstrap_servers=KAFKA_BROKERS.split(','),
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
        retries=3,
        linger_ms=200,
    )


def write_to_redis(r, aggregator):
    """将聚合结果写入 Redis"""
    pipe = r.pipeline()

    top_brands = aggregator.get_top_brands(TOP_N)
    top_models = aggregator.get_top_models(TOP_N)

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    pipe.set('used_car:realtime:top_brands', json.dumps(top_brands, ensure_ascii=False))
    pipe.set('used_car:realtime:top_models', json.dumps(top_models, ensure_ascii=False))
    pipe.set('used_car:realtime:total_events', aggregator.total_events())
    pipe.set('used_car:realtime:last_update', now_str)
    pipe.set('used_car:realtime:status', 'running')

    pipe.execute()


def check_price_anomaly(event):
    """检查价格异常"""
    actual = event.get('price')
    predicted = event.get('predicted')
    if actual and predicted and isinstance(actual, (int, float)) and isinstance(predicted, (int, float)):
        if predicted > 0:
            deviation = abs(actual - predicted) / predicted
            if deviation > ALERT_THRESHOLD:
                return {
                    'brand': event.get('brand', '未知'),
                    'model': event.get('model', '未知'),
                    'actual_price': actual,
                    'predicted_price': predicted,
                    'deviation': round(deviation * 100, 2),
                    'timestamp': event.get('timestamp', time.time()),
                    'alert': f"价格异常: {event.get('brand')} {event.get('model', '')} "
                             f"实际{actual}万 vs 预测{predicted}万, 偏差{deviation*100:.1f}%"
                }
    return None


def publish_alert(r, producer, alert):
    """预警落地：推送到 Kafka 预警 topic + 写入 Redis 列表（保留最近 100 条）

    两者相互独立，任一路径失败不影响另一条，避免预警静默丢失。
    """
    try:
        producer.send(KAFKA_ALERT_TOPIC, alert)
    except Exception as e:
        print(f"[WARN] 预警推送 {KAFKA_ALERT_TOPIC} 失败: {e}")

    try:
        pipe = r.pipeline()
        pipe.lpush('used_car:realtime:alerts', json.dumps(alert, ensure_ascii=False))
        pipe.ltrim('used_car:realtime:alerts', 0, 99)
        pipe.execute()
    except Exception as e:
        print(f"[WARN] 预警写入 Redis 失败: {e}")


def main():
    print("=" * 60)
    print("二手车实时流处理消费者")
    print(f"Kafka: {KAFKA_BROKERS}")
    print(f"Topic: {KAFKA_TOPIC}")
    print(f"Redis: {REDIS_HOST}:{REDIS_PORT}")
    print(f"窗口: {WINDOW_SIZE}s / 滑动: {WINDOW_SLIDE}s")
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    r = create_redis()
    r.ping()
    print("[INFO] Redis 连接成功")

    r.set('used_car:realtime:status', 'starting')

    consumer = create_consumer()
    print("[INFO] Kafka 消费者已连接")

    producer = create_producer()
    print(f"[INFO] 预警生产者已就绪 (topic: {KAFKA_ALERT_TOPIC})")

    aggregator = SlidingWindowAggregator(WINDOW_SIZE, WINDOW_SLIDE)
    last_write = 0
    total_consumed = 0
    alerts = []

    def graceful_shutdown(signum, frame):
        print(f"\n[SHUTDOWN] 正在停止... 共消费 {total_consumed} 条消息")
        r.set('used_car:realtime:status', 'stopped')
        try:
            producer.flush(timeout=5)
        except Exception:
            pass
        consumer.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    r.set('used_car:realtime:status', 'running')
    print("[INFO] 开始消费消息...\n")

    while True:
        try:
            records = consumer.poll(timeout_ms=1000, max_records=500)
            if not records:
                now = time.time()
                aggregator.evict_expired(now)
                if now - last_write >= WINDOW_SLIDE:
                    write_to_redis(r, aggregator)
                    last_write = now
                continue

            for tp, messages in records.items():
                for msg in messages:
                    event = msg.value
                    if event is None:      # 脏消息已在反序列化阶段拦截
                        continue
                    aggregator.add_event(event)
                    total_consumed += 1

                    alert = check_price_anomaly(event)
                    if alert:
                        alerts.append(alert)
                        publish_alert(r, producer, alert)
                        print(f"  [ALERT] {alert['alert']}")
                        if len(alerts) > 100:
                            alerts = alerts[-100:]

            now = time.time()
            aggregator.evict_expired(now)

            if now - last_write >= WINDOW_SLIDE:
                write_to_redis(r, aggregator)
                last_write = now
                top = aggregator.get_top_brands(3)
                top_str = ", ".join(f"{t['brand']}({t['search_count']})" for t in top)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"消费={total_consumed} 窗口内={aggregator.total_events()} "
                      f"Top3: {top_str}")

        except StopIteration:
            time.sleep(1)
        except Exception as e:
            print(f"[ERROR] {e}")
            time.sleep(2)


if __name__ == '__main__':
    main()

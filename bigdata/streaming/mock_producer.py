#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟用户搜索事件生产者
向 Kafka topic car_search_events 发送模拟搜索事件，用于演示和测试
用法：python mock_producer.py [条数] [间隔秒]
"""

import os
import sys
import json
import time
import random
from datetime import datetime

from kafka import KafkaProducer

KAFKA_BROKERS = os.getenv('KAFKA_BROKERS', '192.168.249.101:9092,192.168.249.102:9092,192.168.249.103:9092')
KAFKA_TOPIC = 'car_search_events'

BRANDS = ['大众', '宝马', '奔驰', '丰田', '本田', '比亚迪', '奥迪', '日产',
          '吉利', '现代', '别克', '福特', '雪佛兰', '特斯拉', '长安', '长城']

MODELS = {
    '大众': ['朗逸', '帕萨特', '途观', '迈腾', 'polo'],
    '宝马': ['3系', '5系', 'X3', 'X5', '1系'],
    '奔驰': ['C级', 'E级', 'GLC', 'A级', 'S级'],
    '丰田': ['卡罗拉', '凯美瑞', 'RAV4', '汉兰达', '雷凌'],
    '比亚迪': ['汉', '秦', '宋', '唐', '海豚'],
    '奥迪': ['A4L', 'A6L', 'Q5', 'A3', 'Q3'],
}

CITIES = ['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '南京', '西安', '重庆']


def generate_event():
    brand = random.choice(BRANDS)
    models = MODELS.get(brand, ['默认车型'])
    model = random.choice(models)
    age = random.randint(1, 15)
    mileage = round(random.uniform(0.5, 20), 1)
    original_price = round(random.uniform(8, 50), 1)
    depreciation = max(0.3, 1 - age * 0.08)
    price = round(original_price * depreciation * random.uniform(0.85, 1.15), 2)
    predicted = round(price * random.uniform(0.85, 1.15), 2)

    # 小概率注入显著偏差，用于演示/验证价格异常预警（偏差需 > 30% 才会触发）
    if random.random() < 0.15:
        predicted = round(price * random.choice([0.6, 1.6]) * random.uniform(0.95, 1.05), 2)

    return {
        'brand': brand,
        'model': model,
        'age': age,
        'mileage': mileage,
        'original_price': original_price,
        'price': price,
        'predicted': predicted,
        'city': random.choice(CITIES),
        'action': random.choice(['search', 'search', 'search', 'view', 'predict']),
        'user_id': f"user_{random.randint(1, 500)}",
        'timestamp': time.time(),
    }


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    interval = float(sys.argv[2]) if len(sys.argv) > 2 else 0.1

    print("=" * 60)
    print(f"模拟搜索事件生产者")
    print(f"目标: {KAFKA_BROKERS}")
    print(f"Topic: {KAFKA_TOPIC}")
    print(f"条数: {count}, 间隔: {interval}s")
    print("=" * 60)

    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKERS.split(','),
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
        key_serializer=lambda k: str(k).encode('utf-8'),
        acks='all',
        retries=3,
    )
    print("[INFO] Kafka 生产者已连接\n")

    for i in range(count):
        event = generate_event()
        key = event['brand']
        producer.send(KAFKA_TOPIC, key=key, value=event)
        if (i + 1) % 50 == 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 已发送 {i+1}/{count} 条")
        time.sleep(interval)

    producer.flush()
    producer.close()
    print(f"\n[DONE] 共发送 {count} 条消息")


if __name__ == '__main__':
    main()

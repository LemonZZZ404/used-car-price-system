"""
car_api 应用路由配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    system_health,
    viz_province_heatmap,
    viz_brand_hierarchy,
    viz_price_trend,
    viz_brand_radar,
    viz_price_scatter,
    CarInfoViewSet, StatBrandPriceViewSet, StatAgePriceViewSet,
    StatPriceDistributionViewSet, PredictionViewSet, AdminUserViewSet,
    dashboard_summary, model_analysis, train_start, train_status, health_check,
    stat_aggregate, market_compare,
    auth_login, auth_logout, auth_me
)
from .enhancements import (
    realtime_hot, realtime_alerts, batch_predict, batch_predict_status,
    export_csv, admin_logs
)

router = DefaultRouter()
router.register(r'cars', CarInfoViewSet, basename='car')
router.register(r'stat/brand-price', StatBrandPriceViewSet, basename='stat-brand')
router.register(r'stat/age-price', StatAgePriceViewSet, basename='stat-age')
router.register(r'stat/price-distribution', StatPriceDistributionViewSet, basename='stat-dist')
router.register(r'prediction', PredictionViewSet, basename='prediction')
router.register(r'users', AdminUserViewSet, basename='user-admin')

urlpatterns = [
    # 实时热门搜索（Kafka 流处理结果）
    path('realtime/hot/', realtime_hot, name='realtime-hot'),
    # 预警中心（价格异常预警时间线）
    path('realtime/alerts/', realtime_alerts, name='realtime-alerts'),
    # 批量预测（Celery 异步）
    path('prediction/batch/', batch_predict, name='batch-predict'),
    path('prediction/batch/status/', batch_predict_status, name='batch-predict-status'),

    # 数据导出中心（CSV 流式下载）
    path('export/csv/', export_csv, name='export-csv'),
    # 运维日志（管理员）
    path('admin/logs/', admin_logs, name='admin-logs'),

    # 路由注册
    path('', include(router.urls)),

    # 看板概览
    path('dashboard/summary/', dashboard_summary, name='dashboard-summary'),

    # 模型分析（特征重要性 + 指标对比）
    path('model/analysis/', model_analysis, name='model-analysis'),

    # 模型训练（Celery 异步）
    path('train/start/', train_start, name='train-start'),
    path('train/status/', train_status, name='train-status'),

    # 健康检查
    path('health/', health_check, name='health-check'),
    path('system/health/', system_health, name='system-health'),
    # 数据可视化
    path('viz/province-heatmap/', viz_province_heatmap, name='viz-province-heatmap'),
    path('viz/brand-hierarchy/', viz_brand_hierarchy, name='viz-brand-hierarchy'),
    path('viz/price-trend/', viz_price_trend, name='viz-price-trend'),
    path('viz/brand-radar/', viz_brand_radar, name='viz-brand-radar'),
    path('viz/price-scatter/', viz_price_scatter, name='viz-price-scatter'),

    # 统计聚合（看板筛选联动）
    path('stat/aggregate/', stat_aggregate, name='stat-aggregate'),

    # 市场行情对比（预测页）
    path('stat/market-compare/', market_compare, name='stat-market-compare'),

    # 认证（用户/管理员分层）
    path('auth/login/', auth_login, name='auth-login'),
    path('auth/logout/', auth_logout, name='auth-logout'),
    path('auth/me/', auth_me, name='auth-me'),
]

from .base import *

DEBUG = False

# django 缓存
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://redis:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# celery 定时任务
# 注意，celery4 版本后，CELERY_BROKER_URL 改为 BROKER_URL
CELERY_BROKER_URL = 'redis://redis:6379/0'  # Broker 使用 Redis, 使用0数据库(暂时不是很清楚原理)
# CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'  # 定时任务调度器 python manage.py celery beat
CELERYD_MAX_TASKS_PER_CHILD = 3  # 每个 worker 最多执行3个任务就会被销毁，可防止内存泄露
# CELERY_RESULT_BACKEND = 'redis://redis:6379/0'  # celery 结果返回，可用于跟踪结果
CELERY_RESULT_BACKEND = 'django-db'  # 使用 database 作为结果存储
CELERY_CACHE_BACKEND = 'django-cache'  # celery 后端缓存

# celery 内容等消息的格式设置
# Mac and Centos
# worker 启动命令：celery -A joyoo worker -l info
CELERY_ACCEPT_CONTENT = ['application/json', ]
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# CELERY BEAT SCHEDULER
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
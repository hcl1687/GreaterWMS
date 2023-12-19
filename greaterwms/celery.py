from __future__ import absolute_import, unicode_literals
from celery import Celery
from django.conf import settings
import os

# 获取当前文件夹名，即为该 Django 的项目名
project_name = os.path.split(os.path.abspath('.'))[-1]

# 设置环境变量
ENV = os.environ.get("GREATERWMS_ENV", "prod")
print(f'GREATERWMS_ENV: {ENV}')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greaterwms.settings.{0}'.format(ENV))

# 实例化 Celery
app = Celery(project_name)

# 使用 django 的 settings 文件配置 celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# Celery 加载所有注册的应用
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
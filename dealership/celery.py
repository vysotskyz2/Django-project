import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salon.settings')

app = Celery('salon')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

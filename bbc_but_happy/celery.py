from __future__ import absolute_import
import os
from celery import Celery
from celery.schedules import crontab

# default django settings from Celery documentation
os.environ.setdefault('DJANGO_SETTINGS_MODULE','bbc_but_happy.settings')
app = Celery('bbc_but_happy')
app.conf.timezone = 'UTC'
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# beat scheduler to execute scrape task every 15 min
app.conf.beat_schedule = {
    'scraping-task-fifteen-min': {
        'task': 'scraper.tasks.scrape_bbc',
        'schedule': crontab(minute='*/15')
    }
}
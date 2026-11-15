import os

from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

# manage.py loads .env, but `celery -A config worker` bypasses it.
load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Every Monday at 06:00 UTC
app.conf.beat_schedule = {
    'refresh-players-weekly': {
        'task': 'playerstats.tasks.refresh_players',
        'schedule': crontab(hour=6, minute=0, day_of_week=1),
    },
}

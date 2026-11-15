from celery import shared_task
from django.core.management import call_command


@shared_task
def refresh_players():
    """Weekly MoneyPuck refresh; same as `manage.py refresh_players`."""
    call_command('refresh_players')

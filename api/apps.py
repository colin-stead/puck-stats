from django.apps import AppConfig


class PlayerstatsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'  # keep whatever is already there
    name = 'api'
    label = 'playerstats'

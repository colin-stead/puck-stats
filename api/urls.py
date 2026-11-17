from django.urls import path
from . import views

urlpatterns = [
    path('players', views.player_list, name='player-list'),
    path('players/<int:nhl_id>', views.player_detail, name='player-detail'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('', views.player_list, name='player-list'),
    path('<int:nhl_id>/', views.player_detail, name='player-detail'),
]

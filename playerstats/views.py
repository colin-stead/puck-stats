from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Player
from .serializers import PlayerListSerializer, PlayerDetailSerializer

WING_POSITIONS = ['LW', 'RW']


@api_view(['GET'])
def player_list(request):
    """
    GET /api/players/
    Query params:
      ?position=Wing|Center|Defenseman  (optional)
      ?limit=10  (optional, default 10)
    Returns the top players sorted by ranking, optionally filtered by position category.
    """
    position_filter = request.query_params.get('position')
    limit = int(request.query_params.get('limit', 10))

    players = Player.objects.all()

    if position_filter == 'Wing':
        players = players.filter(position__in=WING_POSITIONS)
    elif position_filter == 'Center':
        players = players.filter(position='C')
    elif position_filter == 'Defenseman':
        players = players.filter(position='D')

    players = players.order_by('ranking')[:limit]

    serializer = PlayerListSerializer(players, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def player_detail(request, nhl_id):
    """
    GET /api/players/<nhl_id>/
    Returns full stats, videos, AI description, and weekly appearance history for one player.
    """
    try:
        player = Player.objects.prefetch_related('videos', 'descriptions', 'weekly_appearances__week').get(nhl_id=nhl_id)
    except Player.DoesNotExist:
        return Response({'detail': 'Player not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = PlayerDetailSerializer(player)
    return Response(serializer.data)

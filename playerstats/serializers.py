from rest_framework import serializers
from .models import Player, PlayerVideo, PlayerWeeklySnapshot


class PlayerVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerVideo
        fields = ['youtube_url', 'title', 'display_order']


class PlayerWeeklySnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerWeeklySnapshot
        fields = ['week', 'consecutive_weeks', 'current_ranking', 'previous_ranking',
                  'goals', 'assists', 'points', 'plus_minus', 'created_at', 'updated_at']


class PlayerListSerializer(serializers.ModelSerializer):
    position_category = serializers.CharField(read_only=True)

    class Meta:
        model = Player
        fields = [
            'id', 'nhl_id', 'name', 'team', 'position', 'position_category',
            'ranking', 'iq_score', 'games', 'goals', 'assists', 'points', 'plus_minus',
            'headshot_url',
        ]


class PlayerDetailSerializer(serializers.ModelSerializer):
    position_category = serializers.CharField(read_only=True)
    videos = PlayerVideoSerializer(many=True, read_only=True)
    weekly_snapshots = PlayerWeeklySnapshotSerializer(many=True, read_only=True)

    class Meta:
        model = Player
        fields = [
            'id', 'nhl_id', 'name', 'number', 'team', 'position', 'position_category',
            'ranking', 'iq_score',
            'games', 'goals', 'assists', 'primary_assists', 'points', 'plus_minus',
            'time_on_ice_per_game',
            'points_per_60', 'primary_assists_per_60', 'plus_minus_per_60',
            'corsi_percentage', 'xgoals_percentage', 'zone_entry_success', 'defensive_zone_exits',
            'description', 'headshot_url',
            'videos', 'weekly_snapshots',
            'created_at', 'updated_at',
        ]

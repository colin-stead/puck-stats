from rest_framework import serializers
from .models import Player, PlayerVideo, PlayerWeeklySnapshot


class PlayerVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerVideo
        fields = ['youtube_url', 'title', 'display_order']


class PlayerWeeklySnapshotSerializer(serializers.ModelSerializer):
    week_number = serializers.IntegerField(source='week')
    ranking = serializers.IntegerField(source='current_ranking')

    class Meta:
        model = PlayerWeeklySnapshot
        fields = ['week_number', 'ranking', 'previous_ranking', 'goals', 'assists', 'points', 'plus_minus']


class PlayerListSerializer(serializers.ModelSerializer):
    position_category = serializers.CharField(read_only=True)
    previous_ranking = serializers.SerializerMethodField()
    consecutive_weeks = serializers.SerializerMethodField()

    def get_previous_ranking(self, obj):
        snapshot = obj.weekly_snapshots.first()
        return snapshot.previous_ranking if snapshot else None

    def get_consecutive_weeks(self, obj):
        snapshot = obj.weekly_snapshots.first()
        return snapshot.consecutive_weeks if snapshot else 0

    class Meta:
        model = Player
        fields = [
            'id', 'nhl_id', 'name', 'team', 'position', 'position_category',
            'ranking', 'previous_ranking', 'consecutive_weeks', 'iq_score',
            'games', 'goals', 'assists', 'points', 'plus_minus',
            'headshot_url',
        ]


class PlayerDetailSerializer(serializers.ModelSerializer):
    position_category = serializers.CharField(read_only=True)
    previous_ranking = serializers.SerializerMethodField()
    consecutive_weeks = serializers.SerializerMethodField()
    videos = PlayerVideoSerializer(many=True, read_only=True)
    weekly_appearances = PlayerWeeklySnapshotSerializer(
        many=True, read_only=True, source='weekly_snapshots'
    )

    def get_previous_ranking(self, obj):
        snapshot = obj.weekly_snapshots.first()
        return snapshot.previous_ranking if snapshot else None

    def get_consecutive_weeks(self, obj):
        snapshot = obj.weekly_snapshots.first()
        return snapshot.consecutive_weeks if snapshot else 0

    class Meta:
        model = Player
        fields = [
            'id', 'nhl_id', 'name', 'number', 'team', 'position', 'position_category',
            'ranking', 'previous_ranking', 'consecutive_weeks', 'iq_score',
            'games', 'goals', 'assists', 'primary_assists', 'points', 'plus_minus',
            'time_on_ice_per_game',
            'points_per_60', 'primary_assists_per_60', 'plus_minus_per_60',
            'corsi_percentage', 'xgoals_percentage', 'zone_entry_success', 'defensive_zone_exits',
            'headshot_url', 'description',
            'videos', 'weekly_appearances',
        ]

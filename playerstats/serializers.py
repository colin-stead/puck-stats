from rest_framework import serializers
from .models import Player, PlayerVideo


class PlayerVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerVideo
        fields = ['youtube_url', 'title', 'display_order']


class PlayerListSerializer(serializers.ModelSerializer):
    position_category = serializers.CharField(read_only=True)
    previous_ranking = serializers.SerializerMethodField()
    consecutive_weeks = serializers.SerializerMethodField()

    def get_previous_ranking(self, obj):
        snapshot = getattr(obj, 'snapshot', None)
        return snapshot.previous_ranking if snapshot else None

    def get_consecutive_weeks(self, obj):
        snapshot = getattr(obj, 'snapshot', None)
        return snapshot.consecutive_weeks if snapshot else 0

    class Meta:
        model = Player
        fields = [
            'id', 'nhl_id', 'name', 'team', 'position', 'position_category',
            'ranking', 'position_rank', 'previous_ranking', 'consecutive_weeks', 'iq_score',
            'games', 'goals', 'assists', 'points', 'plus_minus',
            'headshot_url',
        ]


class PlayerDetailSerializer(serializers.ModelSerializer):
    position_category = serializers.CharField(read_only=True)
    previous_ranking = serializers.SerializerMethodField()
    consecutive_weeks = serializers.SerializerMethodField()
    videos = PlayerVideoSerializer(many=True, read_only=True)
    weekly = serializers.SerializerMethodField()

    def get_weekly(self, obj):
        """This week's gains (season totals minus start-of-week baselines); null if unknown."""
        snap = getattr(obj, 'snapshot', None)
        if snap is None or snap.start_points is None:
            return None
        return {
            'goals': obj.goals - snap.start_goals,
            'assists': obj.assists - snap.start_assists,
            'points': obj.points - snap.start_points,
            'plus_minus': obj.plus_minus - snap.start_plus_minus,
        }

    def get_previous_ranking(self, obj):
        snapshot = getattr(obj, 'snapshot', None)
        return snapshot.previous_ranking if snapshot else None

    def get_consecutive_weeks(self, obj):
        snapshot = getattr(obj, 'snapshot', None)
        return snapshot.consecutive_weeks if snapshot else 0

    class Meta:
        model = Player
        fields = [
            'id', 'nhl_id', 'name', 'number', 'team', 'position', 'position_category',
            'ranking', 'position_rank', 'previous_ranking', 'consecutive_weeks', 'iq_score',
            'games', 'goals', 'assists', 'primary_assists', 'points', 'plus_minus',
            'time_on_ice_per_game',
            'points_per_60', 'primary_assists_per_60', 'plus_minus_per_60',
            'corsi_percentage', 'xgoals_percentage',
            'headshot_url', 'description', 'updated_at',
            'videos', 'weekly',
        ]

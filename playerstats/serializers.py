from rest_framework import serializers
from .models import Player, PlayerDescription, PlayerVideo, PlayerWeeklyAppearance


class PlayerVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerVideo
        fields = ['youtube_url', 'title', 'display_order']


class PlayerDescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerDescription
        fields = ['description', 'current_rank', 'previous_rank', 'iq_score_at_time',
                  'consecutive_weeks_at_time', 'created_at']


class PlayerWeeklyAppearanceSerializer(serializers.ModelSerializer):
    week_number = serializers.IntegerField(source='week.week_number')
    season = serializers.CharField(source='week.season')
    start_date = serializers.DateField(source='week.start_date')

    class Meta:
        model = PlayerWeeklyAppearance
        fields = ['week_number', 'season', 'start_date', 'ranking', 'iq_score', 'points']


class PlayerListSerializer(serializers.ModelSerializer):
    """Compact serializer for the rankings table."""
    position_category = serializers.CharField(read_only=True)
    latest_description = serializers.SerializerMethodField()

    class Meta:
        model = Player
        fields = [
            'id', 'nhl_id', 'name', 'team', 'position', 'position_category',
            'ranking', 'previous_ranking', 'iq_score',
            'consecutive_weeks', 'games', 'goals', 'assists', 'points', 'plus_minus',
            'headshot_url', 'latest_description',
        ]

    def get_latest_description(self, obj):
        desc = obj.descriptions.first()
        if desc:
            return PlayerDescriptionSerializer(desc).data
        return None


class PlayerDetailSerializer(serializers.ModelSerializer):
    """Full serializer for the player detail page."""
    position_category = serializers.CharField(read_only=True)
    videos = PlayerVideoSerializer(many=True, read_only=True)
    latest_description = serializers.SerializerMethodField()
    weekly_appearances = PlayerWeeklyAppearanceSerializer(many=True, read_only=True)

    class Meta:
        model = Player
        fields = [
            'id', 'nhl_id', 'name', 'number', 'team', 'position', 'position_category',
            'ranking', 'previous_ranking', 'iq_score',
            'consecutive_weeks', 'last_seen_week',
            'games', 'goals', 'assists', 'primary_assists', 'points', 'plus_minus',
            'time_on_ice_per_game', 'shots_on_goal', 'shooting_percentage',
            'power_play_goals', 'power_play_points', 'short_handed_goals', 'game_winning_goals',
            'points_per_60', 'primary_assists_per_60', 'plus_minus_per_60',
            'corsi_percentage', 'xgoals_percentage', 'zone_entry_success', 'defensive_zone_exits',
            'headshot_url', 'videos', 'latest_description', 'weekly_appearances',
        ]

    def get_latest_description(self, obj):
        desc = obj.descriptions.first()
        if desc:
            return PlayerDescriptionSerializer(desc).data
        return None

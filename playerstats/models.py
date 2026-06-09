from django.db import models


class Week(models.Model):
    """A single weekly refresh cycle for rankings and descriptions."""
    week_number = models.IntegerField()
    season = models.CharField(max_length=10)  # e.g. "2025-26"
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['week_number', 'season']
        ordering = ['-start_date']

    def __str__(self):
        return f"Week {self.week_number} ({self.season})"


class Player(models.Model):
    # LW/RW are stored for correct display, but the API filter for position category
    # "Wing" maps to position__in=['LW', 'RW'] — see playerstats/views.py.
    POSITION_CHOICES = [
        ('C', 'Center'),
        ('LW', 'Left Wing'),
        ('RW', 'Right Wing'),
        ('D', 'Defenseman'),
    ]

    # Identity
    nhl_id = models.IntegerField(unique=True)  # NHL API player ID — also used to build headshot URL
    name = models.CharField(max_length=200)
    number = models.IntegerField(default=0)
    position = models.CharField(max_length=3, choices=POSITION_CHOICES)
    team = models.CharField(max_length=100)
    headshot_url = models.CharField(max_length=500, blank=True)

    # Rankings
    ranking = models.IntegerField()
    previous_ranking = models.IntegerField(null=True, blank=True)
    iq_score = models.FloatField(default=0.0)

    # Weekly visibility — updated each refresh cycle
    consecutive_weeks = models.IntegerField(default=0)
    last_seen_week = models.ForeignKey(
        'Week', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='last_seen_players',
    )

    # Basic stats (NHL API)
    games = models.IntegerField(default=0)
    goals = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    primary_assists = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    plus_minus = models.IntegerField(default=0)
    time_on_ice_per_game = models.FloatField(default=0.0)  # minutes
    shots_on_goal = models.IntegerField(default=0)
    shooting_percentage = models.FloatField(default=0.0)
    power_play_goals = models.IntegerField(default=0)
    power_play_points = models.IntegerField(default=0)
    short_handed_goals = models.IntegerField(default=0)
    game_winning_goals = models.IntegerField(default=0)

    # Per-60 stats (computed in compute_iq_score before saving)
    points_per_60 = models.FloatField(default=0.0)
    primary_assists_per_60 = models.FloatField(default=0.0)
    plus_minus_per_60 = models.FloatField(default=0.0)

    # Advanced stats (MoneyPuck)
    corsi_percentage = models.FloatField(default=0.0)       # CF% — possession proxy
    xgoals_percentage = models.FloatField(default=0.0)      # xG% — shot quality
    zone_entry_success = models.FloatField(default=0.0)     # controlled entries %
    defensive_zone_exits = models.FloatField(default=0.0)   # clean exits per 60

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['ranking']

    def __str__(self):
        return f"#{self.ranking} {self.name} ({self.team})"

    @property
    def position_category(self):
        """Returns the broad category used by the frontend position filter."""
        return {'C': 'Center', 'LW': 'Wing', 'RW': 'Wing', 'D': 'Defenseman'}.get(self.position, 'Wing')

    def compute_iq_score(self):
        """
        TopShelfIQ Formula:
          Points per 60          × 0.20
          Primary Assists per 60 × 0.15
          Corsi%                 × 0.20
          xGoals%                × 0.15
          Plus/Minus per 60      × 0.10
          Defensive Zone Exits   × 0.10
          Zone Entry Success%    × 0.10
        """
        toi = self.time_on_ice_per_game
        if toi > 0 and self.games > 0:
            total_hours = (toi / 60) * self.games
            self.points_per_60 = round(self.points / total_hours, 2)
            self.primary_assists_per_60 = round(self.primary_assists / total_hours, 2)
            self.plus_minus_per_60 = round(self.plus_minus / total_hours, 2)

        self.iq_score = round(
            (self.points_per_60 * 0.20) +
            (self.primary_assists_per_60 * 0.15) +
            (self.corsi_percentage * 0.20) +
            (self.xgoals_percentage * 0.15) +
            (self.plus_minus_per_60 * 0.10) +
            (self.defensive_zone_exits * 0.10) +
            (self.zone_entry_success * 0.10),
            2,
        )
        return self.iq_score

    def save(self, *args, **kwargs):
        self.compute_iq_score()
        super().save(*args, **kwargs)


class PlayerWeeklyAppearance(models.Model):
    """Records every week a player appears in any top-10 list. Used for streak and comeback tracking."""
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='weekly_appearances')
    week = models.ForeignKey(Week, on_delete=models.CASCADE, related_name='player_appearances')
    ranking = models.IntegerField()
    iq_score = models.FloatField()
    points = models.IntegerField(default=0)

    class Meta:
        unique_together = ['player', 'week']
        ordering = ['-week__start_date']

    def __str__(self):
        return f"{self.player.name} — Week {self.week.week_number} ({self.week.season}) #{self.ranking}"


class PlayerDescription(models.Model):
    """
    AI-generated scouting report for a player, regenerated each week.
    A new record per week gives a full history of how the analysis evolves.
    The Claude prompt receives current_rank, previous_rank, iq_score_at_time,
    and consecutive_weeks_at_time to write a hockey-IQ analysis under 1500 chars.
    """
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='descriptions')
    week = models.ForeignKey(Week, null=True, blank=True, on_delete=models.SET_NULL, related_name='descriptions')
    description = models.TextField()
    current_rank = models.IntegerField()
    previous_rank = models.IntegerField(null=True, blank=True)
    iq_score_at_time = models.FloatField()
    consecutive_weeks_at_time = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.player.name} scouting report — {self.created_at.strftime('%Y-%m-%d')}"

    @property
    def latest(self):
        return PlayerDescription.objects.filter(player=self.player).first()


class PlayerVideo(models.Model):
    """YouTube analysis videos for a player, shown on the detail page."""
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='videos')
    youtube_url = models.CharField(max_length=500)
    title = models.CharField(max_length=200, blank=True)
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return f"{self.player.name} — {self.title or self.youtube_url}"

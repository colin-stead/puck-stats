from django.db import models


class Player(models.Model):
    # LW/RW stored for display; the API filter for "Wing" maps to position__in=['LW','RW']
    POSITION_CHOICES = [
        ('C', 'Center'),
        ('LW', 'Left Wing'),
        ('RW', 'Right Wing'),
        ('D', 'Defenseman'),
    ]

    # Identity
    nhl_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=200)
    number = models.IntegerField(default=0)
    position = models.CharField(max_length=3, choices=POSITION_CHOICES)
    team = models.CharField(max_length=100)
    headshot_url = models.CharField(max_length=500, blank=True)

    # Current ranking
    ranking = models.IntegerField()
    iq_score = models.FloatField(default=0.0)

    # Current season stats (NHL API)
    games = models.IntegerField(default=0)
    goals = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    primary_assists = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    plus_minus = models.IntegerField(default=0)
    time_on_ice_per_game = models.FloatField(default=0.0)  # minutes

    # Per-60 stats (computed before saving)
    points_per_60 = models.FloatField(default=0.0)
    primary_assists_per_60 = models.FloatField(default=0.0)
    plus_minus_per_60 = models.FloatField(default=0.0)

    # Advanced stats (MoneyPuck)
    corsi_percentage = models.FloatField(default=0.0)
    xgoals_percentage = models.FloatField(default=0.0)
    zone_entry_success = models.FloatField(default=0.0)
    defensive_zone_exits = models.FloatField(default=0.0)

    # AI-generated scouting report, refreshed weekly
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['ranking']

    def __str__(self):
        return f"#{self.ranking} {self.name} ({self.team})"

    @property
    def position_category(self):
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


class PlayerWeeklySnapshot(models.Model):
    """One row per player per weekly refresh. Tracks ranking history and streak visibility."""
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='weekly_snapshots')
    week = models.IntegerField()
    consecutive_weeks = models.IntegerField(default=1)
    current_ranking = models.IntegerField()
    previous_ranking = models.IntegerField(null=True, blank=True)
    goals = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    plus_minus = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['player', 'week']
        ordering = ['-week']

    def __str__(self):
        return f"{self.player.name} — Week {self.week} #{self.current_ranking}"


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

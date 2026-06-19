import io
import os
import time
import zipfile

import pandas as pd
import requests
from django.core.management.base import BaseCommand

from playerstats.models import Player

SCOUTING_PROMPT = """\
You are a hockey analyst for TopShelfIQ, a site that ranks NHL players by \
a proprietary Hockey IQ metric. Write a scouting report explaining why \
{player_name} ({position}, {team}, #{number}) is ranked #{current_rank} \
this week.

THE FORMULA:
HockeyIQ Score =
  (Points per 60 × 0.20) +
  (Primary Assists per 60 × 0.15) +
  (Corsi% × 0.20) +
  (xGoals% × 0.15) +
  (Plus/Minus per 60 × 0.10) +
  (Blue Line Wins per 60 × 0.20)

Blue Line Wins = successful zone entries + successful zone exits per 60 \
minutes — a measure of how often a player wins the small, unglamorous \
battles at the blue line that sustain possession and limit odd-man rushes.

PLAYER'S RAW STATS THIS WEEK:
- Points per 60: {points_per_60}
- Primary Assists per 60: {primary_assists_per_60}
- Corsi%: {corsi_percentage}
- xGoals%: {xgoals_percentage}
- Plus/Minus per 60: {plus_minus_per_60}
- Blue Line Wins per 60: {blue_line_wins_per_60}
- Final HockeyIQ Score: {iq_score}

CONTEXT:
- Previous rank: {previous_rank}
- Rank change: {rank_change}
- Consecutive weeks in top 10: {consecutive_weeks}
- Returning after absence: {is_returning} ({weeks_absent} weeks gone)

INSTRUCTIONS:
Write exactly 2 paragraphs, no headers or bullet points:

Paragraph 1: State their rank and the stat driving it most, with specific \
numbers. Then explain what "Hockey IQ" means in their specific case — tie \
their Blue Line Wins and Corsi% to in-game decision making, not just raw \
talent. This is a player coaches want others to study, not just a good \
scorer.

Paragraph 2: Note one limiting factor holding them back from a higher \
rank, and mention their rank trend (climbing, falling, returning, or \
holding steady this week).

Tone: confident, analytical, a notch above typical broadcast commentary. \
Avoid clichés like "elite" or "dynamic." Write like someone who actually \
watches tape, not a press release.\
"""

MONEYPUCK_URL = (
    "https://peter-tanner.com/moneypuck/downloads/seasonPlayersSummary/skaters/2025.zip"
)
NHL_API_URL = "https://api-web.nhle.com/v1/player/{}/landing"

TOP_N = 10
POSITION_GROUPS = ("C", "W", "D")

# MoneyPuck uses L/R; our model uses LW/RW
MP_TO_MODEL_POSITION = {"C": "C", "L": "LW", "R": "RW", "D": "D"}


class Command(BaseCommand):
    help = "Refresh top 30 players (10 C / 10 W / 10 D) from MoneyPuck data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--inspect",
            action="store_true",
            help="Print CSV columns and sample values, then exit without writing to DB.",
        )

    def handle(self, *args, **options):
        self.stdout.write("Downloading MoneyPuck data...")
        df = self._fetch_moneypuck()
        self.stdout.write(f"Loaded {len(df)} rows (per-game, all situations).")

        if options["inspect"]:
            self._inspect(df)
            return

        top = self._select_top_players(df)
        self.stdout.write(f"Selected {len(top)} players. Writing to DB...")
        self._upsert_players(top)
        self.stdout.write(self.style.SUCCESS("Refresh complete."))

    # ------------------------------------------------------------------
    # Data fetching
    # ------------------------------------------------------------------

    def _fetch_moneypuck(self):
        resp = requests.get(MONEYPUCK_URL, timeout=30)
        resp.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            with zf.open(zf.namelist()[0]) as f:
                return pd.read_csv(f)

    # ------------------------------------------------------------------
    # Player selection
    # ------------------------------------------------------------------

    def _select_top_players(self, df):
        # One row per player per game — keep all-situation rows only
        df = df[df["situation"] == "all"].copy()

        # Aggregate per-game rows into season totals per player.
        # Percentage stats (Corsi%, xGoals%) are recomputed from their
        # underlying totals so averaging doesn't introduce bias.
        agg = (
            df.groupby("playerId")
            .agg(
                name=("name", "last"),
                position=("position", "last"),
                team=("playerTeam", "last"),  # most recent team
                games_played=("gameId", "nunique"),
                icetime=("icetime", "sum"),
                points=("I_F_points", "sum"),
                goals=("I_F_goals", "sum"),
                primary_assists=("I_F_primaryAssists", "sum"),
                secondary_assists=("I_F_secondaryAssists", "sum"),
                on_ice_f_goals=("OnIce_F_goals", "sum"),
                on_ice_a_goals=("OnIce_A_goals", "sum"),
                on_ice_f_shots=("OnIce_F_shotAttempts", "sum"),
                on_ice_a_shots=("OnIce_A_shotAttempts", "sum"),
                on_ice_f_xgoals=("OnIce_F_xGoals", "sum"),
                on_ice_a_xgoals=("OnIce_A_xGoals", "sum"),
                penalty_minutes=("I_F_penalityMinutes", "sum"),
            )
            .reset_index()
        )

        # Average TOI per game in seconds
        agg["avg_toi_sec"] = agg["icetime"] / agg["games_played"]

        # Minimum 10 min/game
        agg = agg[agg["avg_toi_sec"] >= 600]

        # Games minimum only once the season has 10 games
        if agg["games_played"].max() >= 10:
            agg = agg[agg["games_played"] >= 10]

        # Derived stats
        agg["assists"] = agg["primary_assists"] + agg["secondary_assists"]
        agg["plus_minus"] = (agg["on_ice_f_goals"] - agg["on_ice_a_goals"]).round().astype(int)

        # Corsi% and xGoals% from season totals (0–100 scale)
        total_shots = agg["on_ice_f_shots"] + agg["on_ice_a_shots"]
        total_xgoals = agg["on_ice_f_xgoals"] + agg["on_ice_a_xgoals"]
        agg["corsi_pct"] = (agg["on_ice_f_shots"] / total_shots * 100).round(2)
        agg["xgoals_pct"] = (agg["on_ice_f_xgoals"] / total_xgoals * 100).round(2)

        # Per-60 stats (icetime is total seconds)
        hours = agg["icetime"] / 3600
        agg["points_per_60"] = agg["points"] / hours
        agg["primary_assists_per_60"] = agg["primary_assists"] / hours
        agg["plus_minus_per_60"] = agg["plus_minus"] / hours
        agg["penalty_min_per_60"] = agg["penalty_minutes"] / hours
        agg["xgoals_against_per_60"] = agg["on_ice_a_xgoals"] / hours

        # Elite TOI bonus: minutes above position threshold × 0.10
        # Mirrors compute_iq_score() in the model.
        avg_toi_min = agg["avg_toi_sec"] / 60
        toi_threshold = agg["position"].map(lambda p: 23.0 if p == "D" else 21.0)
        above = avg_toi_min >= toi_threshold
        agg["toi_bonus"] = (2.0 + (avg_toi_min - toi_threshold) * 0.10).where(above, 0.0)

        # iq_score — mirrors compute_iq_score() in the model.
        # zone_entry_success and defensive_zone_exits omitted: not in this CSV.
        agg["iq_score"] = (
            agg["points_per_60"] * 0.20
            + agg["primary_assists_per_60"] * 0.15
            + agg["corsi_pct"] * 0.20
            + agg["xgoals_pct"] * 0.15
            + agg["plus_minus_per_60"] * 0.10
            + agg["toi_bonus"]
            - agg["penalty_min_per_60"] * 0.15
            - agg["xgoals_against_per_60"] * 0.10
        ).round(2)

        agg["mapped_position"] = agg["position"].map(MP_TO_MODEL_POSITION)
        agg["group"] = agg["position"].apply(lambda p: "W" if p in ("L", "R") else p)

        return pd.concat(
            [agg[agg["group"] == g].nlargest(TOP_N, "iq_score") for g in POSITION_GROUPS]
        ).reset_index(drop=True)

    # ------------------------------------------------------------------
    # DB upsert
    # ------------------------------------------------------------------

    def _upsert_players(self, df):
        df = df.sort_values("iq_score", ascending=False).copy()
        df["ranking"] = range(1, len(df) + 1)

        for _, row in df.iterrows():
            nhl_id = int(row["playerId"])
            toi_per_game = round(float(row["avg_toi_sec"]) / 60, 2)  # seconds → minutes

            player, created = Player.objects.update_or_create(
                nhl_id=nhl_id,
                defaults={
                    "name": row["name"],
                    "position": row["mapped_position"],
                    "team": row["team"],
                    "ranking": int(row["ranking"]),
                    "games": int(row["games_played"]),
                    "goals": int(row["goals"]),
                    "assists": int(row["assists"]),
                    "primary_assists": int(row["primary_assists"]),
                    "points": int(row["points"]),
                    "plus_minus": int(row["plus_minus"]),
                    "time_on_ice_per_game": toi_per_game,
                    "corsi_percentage": float(row["corsi_pct"]),
                    "xgoals_percentage": float(row["xgoals_pct"]),
                    "xgoals_against_per_60": round(float(row["xgoals_against_per_60"]), 2),
                    "penalty_minutes": int(row["penalty_minutes"]),
                    # save() recomputes per-60s and iq_score from the raw fields above
                },
            )

            if created or not player.headshot_url:
                headshot, number = self._fetch_nhl_player(nhl_id)
                update_fields = {}
                if headshot:
                    update_fields["headshot_url"] = headshot
                if number:
                    update_fields["number"] = number
                if update_fields:
                    Player.objects.filter(nhl_id=nhl_id).update(**update_fields)
                    player.refresh_from_db()
                    self.stdout.write(f"  Fetched NHL data for {row['name']}")

            self._generate_description(player)

        self.stdout.write(f"Upserted {len(df)} players.")

    def _generate_description(self, player):
        snapshot = player.weekly_snapshots.first()
        previous_rank = snapshot.previous_ranking if snapshot else None
        consecutive_weeks = snapshot.consecutive_weeks if snapshot else 1

        if previous_rank is None:
            rank_change = "new entry"
        elif player.ranking < previous_rank:
            rank_change = f"up {previous_rank - player.ranking}"
        elif player.ranking > previous_rank:
            rank_change = f"down {player.ranking - previous_rank}"
        else:
            rank_change = "held steady"

        snapshot_count = player.weekly_snapshots.count()
        is_returning = previous_rank is None and snapshot_count > 1
        weeks_absent = snapshot_count - 1 if is_returning else 0

        prompt = SCOUTING_PROMPT.format(
            player_name=player.name,
            position=player.position,
            team=player.team,
            number=player.number or "?",
            current_rank=player.ranking,
            points_per_60=round(player.points_per_60, 2),
            primary_assists_per_60=round(player.primary_assists_per_60, 2),
            corsi_percentage=round(player.corsi_percentage, 1),
            xgoals_percentage=round(player.xgoals_percentage, 1),
            plus_minus_per_60=round(player.plus_minus_per_60, 2),
            blue_line_wins_per_60=0.0,  # not yet available in source data
            iq_score=player.iq_score,
            previous_rank=previous_rank if previous_rank is not None else "N/A",
            rank_change=rank_change,
            consecutive_weeks=consecutive_weeks,
            is_returning=str(is_returning).lower(),
            weeks_absent=weeks_absent,
        )

        api_key = os.environ.get("GEMINI_API_KEY", "")
        model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
        if not api_key:
            self.stdout.write(self.style.WARNING("  GEMINI_API_KEY not set — skipping description"))
            return

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        delay = 5  # seconds between retries, doubles each attempt
        for _ in range(3):
            try:
                resp = requests.post(
                    url,
                    params={"key": api_key},
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                    timeout=60,
                )
                if resp.status_code == 429:
                    try:
                        api_msg = resp.json().get("error", {}).get("message", resp.text[:300])
                    except Exception:
                        api_msg = resp.text[:300]
                    self.stdout.write(self.style.WARNING(f"  429: {api_msg}"))
                    time.sleep(delay)
                    delay *= 2
                    continue
                resp.raise_for_status()
                description = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                Player.objects.filter(pk=player.pk).update(description=description)
                self.stdout.write(f"  Generated description for {player.name}")
                time.sleep(4)  # stay under 15 RPM free-tier limit
                return
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f"  Description failed for {player.name}: {exc}"))
                return

    # ------------------------------------------------------------------
    # NHL API
    # ------------------------------------------------------------------

    def _fetch_nhl_player(self, nhl_id):
        try:
            resp = requests.get(NHL_API_URL.format(nhl_id), timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return data.get("headshot", ""), data.get("sweaterNumber")
        except Exception:
            return "", None

    # ------------------------------------------------------------------
    # Debug helper
    # ------------------------------------------------------------------

    def _inspect(self, df):
        self.stdout.write("\nColumns:")
        for col in df.columns.tolist():
            self.stdout.write(f"  {col}")
        self.stdout.write(f"\nSituations: {df['situation'].unique().tolist()}")
        self.stdout.write(f"Positions:  {df['position'].unique().tolist()}")
        all_df = df[df["situation"] == "all"]
        self.stdout.write(f"\nAll-situation rows: {len(all_df)}")
        self.stdout.write(f"Unique players:     {all_df['playerId'].nunique()}")
        self.stdout.write("\nSample row (first all-situation player):")
        self.stdout.write(str(all_df.iloc[0].to_dict()))

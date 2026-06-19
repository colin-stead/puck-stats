import io
import zipfile

import pandas as pd
import requests
from django.core.management.base import BaseCommand

from playerstats.models import Player

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
                    self.stdout.write(f"  Fetched NHL data for {row['name']}")

        self.stdout.write(f"Upserted {len(df)} players.")

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

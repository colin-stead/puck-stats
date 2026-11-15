"""
On-demand scouting descriptions. The weekly refresh clears every Player.description;
the detail view calls ensure_description() and the first visitor of the week pays for
one Gemini call, which is then cached on the Player row.
"""
import logging
import os

import requests

logger = logging.getLogger(__name__)

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
  (Ice-time bonus: 2.0 + 0.10 per minute above 21 min/game for forwards, \
23 for defensemen) −
  (Penalty Minutes per 60 × 0.15) −
  (xGoals Against per 60 × 0.10)

Corsi% is the share of shot attempts the team takes while the player is on \
the ice; xGoals% is the same for shot quality. Together they show whether \
the player tilts the game in his team's favour.

PLAYER'S STATS THIS SEASON:
- Points per 60: {points_per_60}
- Primary Assists per 60: {primary_assists_per_60}
- Corsi%: {corsi_percentage}
- xGoals%: {xgoals_percentage}
- Plus/Minus per 60: {plus_minus_per_60}
- Penalty Minutes per 60: {penalty_minutes_per_60}
- xGoals Against per 60: {xgoals_against_per_60}
- Ice time per game: {toi} min
- Final HockeyIQ Score: {iq_score}

CONTEXT:
- Previous rank: {previous_rank}
- Rank change: {rank_change}
- Consecutive weeks in the top 30: {consecutive_weeks}

INSTRUCTIONS:
Write about 80 words total, as exactly 3 very short paragraphs separated by \
a blank line. No headers, bullets or markdown.

Paragraph 1 (1-2 sentences): State their rank and the stat driving it most, \
with specific numbers.

Paragraph 2 (1-2 sentences): What "Hockey IQ" means for this player — tie \
their Corsi% and xGoals% to in-game decision making, not just raw talent.

Paragraph 3 (1 sentence): One limiting factor holding them back from a \
higher rank, and their rank trend (climbing, falling, new to the list, or \
holding steady this week).

Tone: confident, analytical, a notch above typical broadcast commentary. \
Avoid clichés like "elite" or "dynamic." Write like someone who actually \
watches tape, not a press release.\
"""


def _rank_change(player, previous_rank):
    if previous_rank is None:
        return "new entry"
    if player.ranking < previous_rank:
        return f"up {previous_rank - player.ranking}"
    if player.ranking > previous_rank:
        return f"down {player.ranking - previous_rank}"
    return "held steady"


def _build_prompt(player):
    snapshot = getattr(player, "snapshot", None)
    previous_rank = snapshot.previous_ranking if snapshot else None
    penalty_per_60 = 0.0
    if player.time_on_ice_per_game > 0 and player.games > 0:
        penalty_per_60 = player.penalty_minutes / ((player.time_on_ice_per_game / 60) * player.games)

    return SCOUTING_PROMPT.format(
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
        penalty_minutes_per_60=round(penalty_per_60, 2),
        xgoals_against_per_60=round(player.xgoals_against_per_60, 2),
        toi=round(player.time_on_ice_per_game, 1),
        iq_score=player.iq_score,
        previous_rank=previous_rank if previous_rank is not None else "N/A",
        rank_change=_rank_change(player, previous_rank),
        consecutive_weeks=snapshot.consecutive_weeks if snapshot else 1,
    )


def ensure_description(player):
    """
    Return the player's description, generating and saving one if it is empty.
    On any failure (no key, API error) returns "" and stores nothing, so the next
    request tries again.
    """
    if player.description:
        return player.description

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        logger.warning("GEMINI_API_KEY not set; skipping description for %s", player.name)
        return ""

    model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    try:
        resp = requests.post(
            url,
            headers={"x-goog-api-key": api_key},
            json={"contents": [{"parts": [{"text": _build_prompt(player)}]}]},
            timeout=30,
        )
        if not resp.ok:
            logger.warning("Gemini %s for %s: %s", resp.status_code, player.name, resp.text[:300])
            return ""
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        logger.exception("Description generation failed for %s", player.name)
        return ""

    # Only write if still empty, so two simultaneous first visits don't clobber each other.
    type(player).objects.filter(pk=player.pk, description="").update(description=text)
    player.description = text
    return text

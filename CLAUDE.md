# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

TopShelfIQ / puck-stats ranks NHL skaters by a custom "Hockey IQ" score. There are two parts:
- **Backend**: Django + DRF at the repo root (`config/` is the project, `api/` is the only app). It uses SQLite (`db.sqlite3`, gitignored).
- **Frontend**: Vite + React 18 + Tailwind v4 in `frontend/`. It was exported from Figma Make, so `frontend/src/app/components/ui/` is generated shadcn/Radix boilerplate.

## Project goals

This is a deploy-once portfolio project. It should run without ongoing attention or spend, so **keep the DB as small as possible** (SQLite, no paid DB or storage) and avoid designs that grow over time. For example, no per-week history rows. State is rolled forward in place.

## Commands

Backend (from the repo root):
```bash
pip install -r requirements.txt python-dotenv   # manage.py imports dotenv, but requirements.txt doesn't list it
python manage.py migrate
python manage.py runserver                      # serves on :8000
python manage.py refresh_players                # pull MoneyPuck data, upsert top players, generate descriptions
python manage.py refresh_players --inspect      # print the CSV columns and a sample row; writes nothing
python manage.py test api               # tests.py is currently empty
python manage.py test api.tests.SomeTestCase.test_method
celery -A config worker -B -l info              # worker + embedded beat; runs refresh_players Mon 06:00 UTC (keep running)
```

Frontend (from `frontend/`):
```bash
npm i
npm run dev     # Vite on :5173, proxies /api to localhost:8000
npm run build
```
There is no lint or typecheck script on either side.

## Scheduling

The weekly refresh runs on Celery ([config/celery.py](config/celery.py) holds the beat schedule and [api/tasks.py](api/tasks.py) the task, which just calls `refresh_players`). The broker is kombu's filesystem transport (`.celery_broker/`, gitignored), so no Redis or other service is needed. There is no result backend, to avoid growth. Beat is embedded in the worker (`-B`), so run exactly one worker process or the job will fire more than once.

## Environment

`manage.py` and `config/celery.py` load `.env` through `load_dotenv()`. `wsgi.py` and `asgi.py` don't, so env vars set only in `.env` are visible to management commands and `runserver`, not to WSGI deployments. Variables used:
- `GEMINI_API_KEY` (sent as the `x-goog-api-key` header): if unset, description generation is skipped with a warning.
- `GEMINI_MODEL`: defaults to `gemini-2.0-flash`.

## Architecture

**Data pipeline** ([refresh_players.py](api/management/commands/refresh_players.py)):
1. Download the MoneyPuck season skater zip (the season is hardcoded in `MONEYPUCK_URL`). The CSV has one row per player per game per situation. Keep only `situation == "all"` and aggregate to season totals per `playerId`. Corsi% and xGoals% are recomputed from summed totals, not averaged.
2. Filter to players averaging at least 10 min TOI. Once anyone has played 10+ games, also require 10+ games played.
3. Compute `iq_score` in pandas and take the top 10 in each group: C, W (MoneyPuck `L`/`R` → model `LW`/`RW`), and D. Rank the combined 30 by score (1–30).
4. `update_or_create` each `Player` by `nhl_id` (MoneyPuck `playerId` == NHL id). The NHL web API (`api-web.nhle.com`) is called only for headshot and sweater number, and only when the headshot is missing.
5. Call Gemini with `SCOUTING_PROMPT` for each player to write `description`. A 4s sleep between calls keeps it under the free-tier rate limit.

**The IQ formula exists in two places and they must stay in sync**:
- `Player.compute_iq_score()` in [models.py](api/models.py) runs on every `save()` and recomputes the per-60 fields and `iq_score` from raw totals.
- The vectorized copy in `_select_top_players()` is used to pick who gets stored.

Two places describe the formula in text and are currently out of date:
- `SCOUTING_PROMPT` still describes "Blue Line Wins" (zone entries/exits), which the data source doesn't have. `blue_line_wins_per_60` is passed as `0.0`.
- [AlgorithmDescription.tsx](frontend/src/app/components/AlgorithmDescription.tsx) is the user-facing explanation of the formula.

When the formula changes, update all four.

**Rankings and weekly snapshots**: `Player.ranking` is overall (1–30) and `position_rank` is within C/W/D (1–10). Each player has exactly one `PlayerWeeklySnapshot` (OneToOne, `player.snapshot`), rolled forward in place by `_update_snapshot()` in `refresh_players`. No history is kept. The snapshot holds `previous_ranking`, `consecutive_weeks`, `week`, and `start_*` baselines (season totals at the start of the week). The API's `weekly` object is the current season totals minus those baselines. Rules:
- `week` is `(date.toordinal() - 1) // 7` (contiguous Mon–Sun integers). A refresh in the same week as the snapshot does nothing to it, so re-runs are safe.
- If `week` is exactly 1 more than the snapshot's, the streak increments and `previous_ranking` and the baselines come from the Player row as it was before this refresh.
- A new entrant, or a gap of more than a week, restarts the streak at 1 with null baselines (`weekly` is null).
- Players who fall out of the top 30 are deleted, which cascades to their snapshot and `PlayerVideo` rows.
- The snapshot is updated before `_generate_description`, which reads rank change and streak from it.

`PlayerVideo` rows (YouTube links on the detail page) are entered by hand, e.g. through the admin.

**API** ([views.py](api/views.py)). `APPEND_SLASH = False`, and the URLs have no trailing slash. The app routes are mounted at `api/players` and the detail route is `'/<int:nhl_id>'`, which builds the paths below:
- `GET /api/players?position=Wing|Center|Defenseman&limit=10` → `PlayerListSerializer`. `Wing` maps to `position__in=['LW','RW']`.
- `GET /api/players/<nhl_id>` → `PlayerDetailSerializer` (adds videos and `weekly`).

**Frontend**: the routes are `/` ([HomePage](frontend/src/app/components/HomePage.tsx)) and `/player/:playerId` ([PlayerDetail](frontend/src/app/components/PlayerDetail.tsx)), where `playerId` is the `nhl_id`. All fetches and the TypeScript response types are in [frontend/src/api.ts](frontend/src/api.ts). Keep these types in sync with the serializer field lists. The `@` import alias points to `frontend/src`. Per a comment in `vite.config.ts`, the React and Tailwind Vite plugins must stay in the config, and so must the `figma:asset/` resolver.

# Architecture

High-level map of how this repo fits together. For signal math see [`docs/MODEL.md`](docs/MODEL.md). For data ingestion see [`docs/DATA_PIPELINE.md`](docs/DATA_PIPELINE.md).

---

## Data flow

```
                    ┌─────────────────────┐
                    │  scripts/fetch_public.py  │
                    │  (Wikipedia MediaWiki API)  │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
      data/bracket.json  fixtures_cache.json   (group + KO results)
              │
              │     ┌──────────────────────┐
              │     │  update.py (optional) │
              │     │  API-Football, Odds,   │
              │     │  Transfermarkt, Elo    │
              │     └──────────┬───────────┘
              │                │
              ▼                ▼
      data/teams.json    data/predictions.json
      (strengths)        (_meta.weights, sim results)
              │                │
              └────────┬───────┘
                       ▼
              web/index.html
              (static fetch of predictions.json)
```

**Primary path:** `fetch_public.py` → `update.py`. No keys required.

**Optional enrichers** in `update.py`: API-Football (injuries, extra fixtures), Odds API or `manual_odds.json`, Transfermarkt scrape, ClubElo CSV. Each module fails soft; `strength.py` redistributes missing signal weights per team.

---

## Core modules

| Module | Role |
|--------|------|
| `config.py` | `MODEL` weights, `STRENGTH_SCALE`, sim count, injury caps |
| `update.py` | Orchestrator: load data → signals → strengths → simulate → write JSON |
| `src/public_fetch.py` | Parse Wikipedia WC 2026 page, merge into bracket + fixtures cache |
| `src/strength.py` | Weighted signal blend + per-team effective weights when sources missing |
| `src/xg.py` | Rolling form from match xG; goals-based fallback when xG absent |
| `src/simulate.py` | Monte Carlo over `bracket_topology.MATCH_FEEDERS` |
| `src/fetch.py` | API-Football client + `merge_fixtures()` (keeps seed fixtures without `match_id`) |
| `src/elo.py` | ClubElo load + FIFA rank fallback |
| `src/value.py` | Transfermarkt squad values (cached in teams.json) |
| `src/odds.py` | Odds API + `load_manual_odds()` from `data/manual_odds.json` |

---

## Outputs

### `data/predictions.json`

- `teams[]`: `win_probability`, `strength`, signal breakdown
- `matches[]`: per-knockout advancement probabilities
- `_meta`: `model_version`, `weights`, `strength_scale`, `data_sources`, `strength_meta` (per-team effective weights, form source notes)

The web UI reads `_meta` so displayed formulas match what the engine actually used.

### `data/bracket.json`

Single source of truth for bracket structure, group standings, knockout results. `fetch_public.py` updates scores by team pairing; manual edits still work for edge cases Wikipedia hasn't caught up on.

### `data/fixtures_cache.json`

Persisted match list (groups + knockouts) for xG/form even when API-Football free tier can't serve 2026.

---

## Web UI

Static `web/index.html`. No build step. Fetches `../data/predictions.json` relative to Pages root.

Features: athletic bracket layout, champion hero, expandable team rows (strength formula + signals), tiered team list, background watermarks.

---

## Testing

```bash
pytest tests/
python scripts/backtest.py
python scripts/backtest.py --sweep   # STRENGTH_SCALE calibration
```

Backtest uses completed knockouts in `bracket.json` vs strengths in `teams.json`.

---

## Deployment

GitHub Pages from `main`. `predictions.json` and `teams.json` are committed so the site always has data without a CI build. Push after `update.py` when you want the public bracket to refresh.

---

## Versioning

Model version in `config.py` (`MODEL_VERSION`) and `predictions.json` `_meta`. Breaking signal or sim changes → bump minor. Doc-only → patch in CHANGELOG.

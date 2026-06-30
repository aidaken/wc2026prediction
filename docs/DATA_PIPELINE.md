# Data pipeline

Step-by-step breakdown of what `update.py` does, JSON schemas for every data file, validation rules, and error handling.

---

## Pipeline overview

```
python update.py
       │
       ├── [FETCH]     fetch_all_data()           → raw dict (in memory)
       │     ├── fetch.get_fixtures(round)
       │     ├── fetch.get_player_stats(team_ids)
       │     ├── fetch.get_injuries(team_ids)
       │     ├── value.get_squad_values(team_ids)
       │     └── odds.get_implied_probs()
       │
       ├── [VALIDATE]  validate_raw_data(raw)     → raises on critical failure
       │
       ├── [CALCULATE] calculate_strengths(raw)   → dict[team_id, TeamStrength]
       │     ├── elo.update_ratings(fixtures)
       │     ├── xg.calculate_form_ratios(fixtures)
       │     ├── injury.calculate_multipliers(injuries, player_stats)
       │     └── combine() → team_strength scores
       │
       ├── [SIMULATE]  simulate.run(teams, bracket, n=10_000) → dict[team_id, float]
       │
       ├── [WRITE]     write_outputs(strengths, win_probs)
       │     ├── write data/teams.json
       │     ├── write data/bracket.json
       │     └── write data/predictions.json
       │
       └── [ARCHIVE]   archive_round(round_name)
             └── copy predictions.json → data/history/{round}.json
```

Total wall-clock time: ~15–30 seconds (dominated by network calls).

---

## JSON schemas

### `data/teams.json`

Registry of all 32 teams with current ratings and metadata. Updated in-place after each round.

```json
{
  "_meta": {
    "last_updated": "2026-06-30T20:15:00Z",
    "round": "Round of 32",
    "teams_remaining": 32
  },
  "teams": {
    "BRA": {
      "id": "BRA",
      "name": "Brazil",
      "api_football_id": 6,
      "transfermarkt_id": "brasilien",
      "elo": 2050.4,
      "elo_change_this_round": +12.3,
      "squad_value_eur": 1180000000,
      "eliminated": false,
      "group": "C",
      "group_position": 1
    },
    "FRA": {
      "id": "FRA",
      "name": "France",
      "api_football_id": 2,
      "transfermarkt_id": "frankreich",
      "elo": 1938.7,
      "elo_change_this_round": -8.1,
      "squad_value_eur": 1050000000,
      "eliminated": false,
      "group": "I",
      "group_position": 1
    }
  }
}
```

**Required fields per team:** `id`, `name`, `api_football_id`, `elo`, `eliminated`  
**Optional fields:** `transfermarkt_id`, `squad_value_eur`, `elo_change_this_round`

---

### `data/bracket.json`

Full bracket state — all matches past and future. The simulation reads this to know which matches are still to be played.

```json
{
  "_meta": {
    "last_updated": "2026-06-30T20:15:00Z",
    "current_round": "Round of 16",
    "wc_year": 2026
  },
  "rounds": {
    "round_of_32": {
      "status": "completed",
      "matches": [
        {
          "match_id": "r32_m01",
          "api_fixture_id": 867241,
          "date": "2026-06-28T19:00:00Z",
          "team_home": "CAN",
          "team_away": "RSA",
          "score_home": 1,
          "score_away": 0,
          "penalties_home": null,
          "penalties_away": null,
          "winner": "CAN",
          "xg_home": 1.42,
          "xg_away": 0.67,
          "status": "FT"
        }
      ]
    },
    "round_of_16": {
      "status": "in_progress",
      "matches": [
        {
          "match_id": "r16_m01",
          "api_fixture_id": null,
          "date": "2026-07-04T18:00:00Z",
          "team_home": "CAN",
          "team_away": "MAR",
          "score_home": null,
          "score_away": null,
          "winner": null,
          "xg_home": null,
          "xg_away": null,
          "status": "NS"
        }
      ]
    },
    "quarter_finals": { "status": "pending", "matches": [] },
    "semi_finals":    { "status": "pending", "matches": [] },
    "final":          { "status": "pending", "matches": [] }
  }
}
```

**Match status values:** `NS` (not started), `FT` (full time), `PEN` (after penalties), `AET` (after extra time)

---

### `data/predictions.json`

Output file. Read by `web/index.html` at page load. Contains win probabilities for all remaining teams plus intermediate signal values for transparency.

```json
{
  "_meta": {
    "generated_at": "2026-06-30T20:15:44Z",
    "round": "Round of 16",
    "simulations": 10000,
    "model_version": "1.0.0"
  },
  "predictions": [
    {
      "team_id": "BRA",
      "team_name": "Brazil",
      "win_probability": 0.184,
      "reach_final_probability": 0.341,
      "reach_semis_probability": 0.512,
      "signals": {
        "elo_normalized": 0.91,
        "xg_form_ratio": 0.67,
        "squad_value_normalized": 0.88,
        "betting_implied_prob": 0.21,
        "injury_multiplier": 1.00
      },
      "team_strength": 0.763,
      "eliminated": false
    },
    {
      "team_id": "GER",
      "team_name": "Germany",
      "win_probability": 0.0,
      "reach_final_probability": 0.0,
      "reach_semis_probability": 0.0,
      "signals": null,
      "team_strength": null,
      "eliminated": true
    }
  ]
}
```

`predictions` array is sorted by `win_probability` descending. Eliminated teams are included with `eliminated: true` and zeroed probabilities (so the dashboard can show the full bracket history).

---

### `data/history/{round}.json`

Snapshot of `predictions.json` taken immediately after each round update. Identical schema to `predictions.json`. Used to show how probabilities evolved across the tournament.

Naming convention:
- `data/history/round_32.json`
- `data/history/round_16.json`
- `data/history/quarter_finals.json`
- `data/history/semi_finals.json`

---

## Validation rules

`validate_raw_data()` runs before any calculation. It raises a `DataValidationError` (custom exception in `src/fetch.py`) if any of these fail:

| Rule | Critical? | Behavior on failure |
|---|---|---|
| All matches from last round have `status: FT` or `PEN` | Yes | Raise — do not update until round is fully complete |
| At least 16 teams not eliminated | Yes | Raise — something is wrong with the bracket |
| `xg_home` and `xg_away` present for completed matches | No | Warn, use 0.0 as fallback |
| Squad value available for at least 12 teams | No | Warn, skip normalization, drop W_VALUE weight |
| Odds available for at least 8 teams | No | Warn, skip betting signal, use FALLBACK_WEIGHTS |

---

## Error handling

All network calls use a retry wrapper with exponential backoff:

```python
@retry(max_attempts=3, backoff_factor=2.0)
def get_fixtures(round_name: str) -> list[dict]:
    ...
```

If all retries fail:
- API-Football: raise `FetchError` — this is critical, update aborts
- Transfermarkt: log warning, return last known values from `teams.json`
- OddsAPI: log warning, return `None`, redistribute weight to `W_ELO`
- FBref: log warning, return `None`, fall back to API-Football player stats

---

## Logging

`update.py` logs to stdout with timestamps. Redirect to file if you want to keep a log:

```bash
python update.py 2>&1 | tee logs/update_$(date +%Y%m%d).log
```

Log levels:
- `INFO` — normal progress (e.g., "Fetching Round of 16 fixtures...")
- `WARNING` — non-critical failures (e.g., "OddsAPI unavailable, skipping betting signal")
- `ERROR` — critical failures that abort the pipeline
- `DEBUG` — per-match calculations (disabled by default, enable in `config.py`)

---

## Adding a new round

After each round completes, `update.py` auto-detects the current round from `bracket.json`. No manual round configuration is needed. The pipeline reads the last round where all matches have `status: FT/PEN/AET` and updates forward.

If you want to force a specific round (e.g., for testing):

```bash
python update.py --round "Round of 16"
```

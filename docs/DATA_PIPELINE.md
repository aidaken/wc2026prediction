# Data pipeline

What `update.py` actually does, step by step. Read this when something in the output looks off.

---

## Overview

```
fetch everything → validate → score teams → sim bracket → write JSON → archive
```

One script. No queue, no worker. Takes a few minutes if APIs are happy.

---

## Step 1: Load config and data

- Read `config.py` weights, `STRENGTH_SCALE`, API settings
- Load existing `data/teams.json`, `data/bracket.json` if present
- Read `_meta.elo_processed_matches` so we don't double-count Elo

---

## Step 2: Fetch

| Call | Module | Output |
|---|---|---|
| Fixtures + results | `fetch.py` | Match list, scores |
| xG per match | `fetch.py` | xG for/against |
| Player stats | `fetch.py` | Goals, assists |
| Injuries | `fetch.py` | Who's out |
| Squad values | `value.py` | € per team |
| Winner odds | `odds.py` | Implied probs |

All in memory. Nothing persisted until the end except what we already had on disk.

---

## Step 3: Validate

- Enough teams still in the tournament
- Bracket matches line up with known structure
- Fail loud if critical fetch failed (unless `--demo`)

---

## Step 4: Elo

`elo.py`:

- Only process fixtures whose IDs aren't in `elo_processed_matches`
- Update ratings for both teams per result
- Append new IDs to `_meta`

This was a real bug before: every run re-applied all matches and ratings blew up.

---

## Step 5: Signals per team

For each **active** team (still in bracket):

| Signal | Module | Notes |
|---|---|---|
| Elo | `elo.py` | Normalized to ~[0,1] band |
| xG form | `xg.py` | Last 5 games |
| Squad value | `value.py` | Log-scaled € |
| Betting | `odds.py` | Normalized across active teams only |
| Injury | `injury.py` | Multiplier on key players out |

---

## Step 6: Combine strength

Weighted sum from `config.py` (must sum to 1.0):

```
team_strength = w_elo * elo_norm + w_xg * xg_norm + ... 
team_strength *= injury_multiplier
```

Stored on each team in `teams.json`.

---

## Step 7: Monte Carlo

`simulate.py`:

- Uses `bracket_topology.MATCH_FEEDERS` so winners land in the right next match
- `STRENGTH_SCALE` on [0,1] strengths (not raw Elo 400 scale)
- `DRAW_PROBABILITY` for group-stage style ties if applicable; knockouts go to pens logic as coded
- 10,000 iterations (configurable)

Outputs:

- `win_probability` per team
- `match_predictions` — P(team advances) per knockout match

---

## Step 8: Write files

| File | Contents |
|---|---|
| `teams.json` | All teams, strengths, signals, `_meta` |
| `bracket.json` | Remaining fixtures, winners filled where known |
| `predictions.json` | Win %, match_predictions, model version, timestamp |

---

## Step 9: History

Copy snapshot to `data/history/predictions_YYYYMMDD_HHMMSS.json` (or similar). Lets you diff how predictions moved round to round.

---

## Demo mode

`python update.py --demo`:

- Skips live API calls where possible
- Uses bundled/cached data so you can test the pipeline without burning quota

Good for CI and local UI work.

---

## What I run after a knockout round

```bash
python update.py
git add data/predictions.json data/bracket.json data/teams.json
git commit -m "chore: update predictions after quarter-finals"
git push
```

That's the whole ops story.

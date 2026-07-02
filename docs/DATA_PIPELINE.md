# Data pipeline

What actually runs, in order. Read this when output looks wrong or you're onboarding.

---

## Overview

```
fetch_public.py  →  update.py  →  commit data/*.json  →  GitHub Pages
     │                  │
 Wikipedia          signals + sim
 bracket + cache
```

Two scripts. No queue, no worker. A few minutes end to end.

---

## Step 0: Public fetch (do this first)

```bash
python scripts/fetch_public.py
```

| Action | Module | Output |
|---|---|---|
| Scrape WC 2026 Wikipedia page | `public_fetch.py` | Parsed group + KO results |
| Merge into bracket | `public_fetch.py` | Updated `data/bracket.json` |
| Build match history | `public_fetch.py` | `data/fixtures_cache.json` |

No API keys. This is how bracket scores and fixture history stay current when API-Football free tier can't serve 2026.

Re-run after each match day before `update.py`.

---

## Step 1: Load config and data

`update.py` starts by loading:

- `config.py` — weights, `STRENGTH_SCALE`, sim count
- `data/teams.json`, `data/bracket.json`, `data/fixtures_cache.json`
- `_meta.elo_processed_matches` so Elo isn't double-applied

---

## Step 2: Optional API fetch

| Call | Module | Output | If it fails |
|---|---|---|---|
| Fixtures + xG | `fetch.py` | Merged into fixture list | Use cache + bracket |
| Player stats | `fetch.py` | Goals, assists | Skip / last known |
| Injuries | `fetch.py` | Who's out | Multiplier 1.0 |
| Squad values | `value.py` | € per team | Last cached |
| Winner odds | `odds.py` | Implied probs | `manual_odds.json` or redistribute weight |
| ClubElo | `elo.py` | Base ratings | FIFA fallback |

`merge_fixtures()` keeps seed group matches even without `match_id`. Important when Wikipedia gives results but API doesn't.

---

## Step 3: Validate

- Enough active teams in bracket
- Structure matches `bracket_topology.py`
- Fail loud on critical errors unless `--demo`

---

## Step 4: Elo

`elo.py`:

- Process only fixtures not in `elo_processed_matches`
- Update both teams per result
- Append new IDs to `_meta`

Re-running all historical matches every time was a real bug. Fixed.

---

## Step 5: Signals per team

For each **active** team:

| Signal | Module | Notes |
|---|---|---|
| Elo | `elo.py` | Normalized ~[0,1] |
| Form | `xg.py` | Last N games: xG if present, else goals-based fallback |
| Squad value | `value.py` | Log-scaled € |
| Betting | `odds.py` | API or manual; renormalized across active teams |
| Injury | `injury.py` | Multiplier on key players out |

Partial data? `strength.py` computes **effective_weights** per team (missing signal's share goes to what's left). Logged in `_meta.strength_meta`.

---

## Step 6: Combine strength

```python
team_strength = sum(w_i * signal_i)   # w_i may differ per team
team_strength *= injury_multiplier
```

xG coverage shrink: if only a few teams have match xG, don't let form dominate the whole field.

Stored on each team in `teams.json`.

---

## Step 7: Monte Carlo

`simulate.py`:

- `bracket_topology.MATCH_FEEDERS` for correct winner placement
- `STRENGTH_SCALE = 0.68` on [0,1] strengths (tune with `backtest.py --sweep`)
- `DRAW_PROBABILITY` for simulated draws in applicable stages
- 10,000 iterations (configurable)

Outputs:

- `win_probability` per team
- `match_predictions` — P(advance) per knockout match

---

## Step 8: Write files

| File | Contents |
|---|---|
| `teams.json` | Strengths, signals, Elo, `_meta` |
| `bracket.json` | Structure + results (may have been touched in step 0) |
| `predictions.json` | Win %, match_predictions, `_meta` (weights, scale, sources) |

---

## Step 9: History

Snapshot to `data/history/` when configured. Diff predictions round to round.

---

## Demo mode

```bash
python update.py --demo
```

Skips live API calls where possible. Uses bundled/cached data. Good for CI and UI work without burning quota.

**Note:** Demo doesn't replace `fetch_public.py` if you want fresh Wikipedia results. Run both in prod.

---

## What I run after a knockout round

```bash
python scripts/fetch_public.py
python update.py
git add data/bracket.json data/fixtures_cache.json data/predictions.json data/teams.json
git commit -m "data: post-round-N results"
git push
```

Site rebuilds in ~30s. That's the whole ops story.

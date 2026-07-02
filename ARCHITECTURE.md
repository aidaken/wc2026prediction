# Architecture

How this repo fits together. Three layers, and they only talk through JSON on disk

---

## The flow

```
INGESTION     fetch, scrape, odds APIs
     ↓
ENGINE        elo, xg, injuries, monte carlo
     ↓ writes
data/*.json   teams, bracket, predictions
     ↓ fetch()
WEB           static dashboard on GitHub Pages
```

### Ingestion

Raw data in, dicts out. No math.

| File | What | From |
|---|---|---|
| `fetch.py` | Fixtures, xG, players, injuries | API-Football |
| `value.py` | Squad € | Transfermarkt scrape |
| `odds.py` | Tournament winner odds | The Odds API |

Keys in `.env`. More detail in [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md).

### Engine

This is where predictions actually happen. `update.py` calls modules in order and writes JSON.

| File | What |
|---|---|
| `elo.py` | Ratings after each result |
| `xg.py` | Form from last 5 games |
| `injury.py` | Penalty when key players are out |
| `simulate.py` | 10k bracket runs |
| `bracket_topology.py` | Fixed WC tree (combination 67) |

Weights and scales live in `config.py`. Math in [docs/MODEL.md](docs/MODEL.md).

### Web

One HTML file. Loads `predictions.json` and `bracket.json`. No build step.

GitHub Pages hosts it. Push new JSON, site updates in ~30s.

---

## What `update.py` runs, in order

1. Fetch fixtures, players, injuries, squad values, odds
2. Sanity check (teams still in, bracket makes sense)
3. Update Elo, xG form, injury multipliers
4. Combine into `team_strength` per active team
5. Monte Carlo the remaining bracket
6. Write `teams.json`, `bracket.json`, `predictions.json`
7. Snapshot to `data/history/`

Step-by-step: [docs/DATA_PIPELINE.md](docs/DATA_PIPELINE.md).

---

## Why I split it this way

- **`update.py`** is glue only. I didn't want business logic hiding in there.
- **`config.py`** is the one knob board for weights and API constants.
- **`src/`** modules don't import each other. Circular imports get ugly fast; `update.py` wires everything.
- **`data/`** is the whole state. Git history = prediction history for free.
- **`web/`** is swappable. Anything that can read JSON works.

---

## Assumptions (on purpose)

- Bracket is locked after groups (combination 67). No re-draws.
- I update once per round, not per match. Good enough for knockouts.
- Free API tiers only (~15-20 API-Football calls per run).
- Weights stay in `config.py` unless I deliberately change them.

---

## Adding a signal

1. New `src/your_signal.py` → `dict[team_id, float]`
2. Call it from `update.py` before `combine_strengths`
3. Weight in `config.py` (still sum to 1.0)
4. Note it in `docs/MODEL.md` and `docs/DATA_SOURCES.md`

Why JSON, why Monte Carlo, why manual updates: [docs/DECISIONS.md](docs/DECISIONS.md).

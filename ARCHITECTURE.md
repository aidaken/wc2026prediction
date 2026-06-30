# Architecture

This document describes the system design, component responsibilities, data flow, and technology decisions for `wc2026prediction`.

---

## Overview

The system is split into three independent layers. Each layer has one job and communicates with the others only through JSON files on disk.

```
┌─────────────────────────────────────────────────────────┐
│                    INGESTION LAYER                       │
│  API-Football · Transfermarkt · OddsAPI · FBref          │
│  (src/fetch.py, src/value.py, src/odds.py)               │
└────────────────────────┬────────────────────────────────┘
                         │ raw data (in memory)
                         ▼
┌─────────────────────────────────────────────────────────┐
│                    ENGINE LAYER                          │
│  Elo · xG form · Squad value · Injuries · Monte Carlo    │
│  (src/elo.py, src/xg.py, src/injury.py, src/simulate.py)│
└────────────────────────┬────────────────────────────────┘
                         │ writes
                         ▼
               ┌─────────────────┐
               │  data/ (JSON)   │
               │  teams.json     │
               │  bracket.json   │
               │  predictions.json│
               └────────┬────────┘
                         │ reads
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  PRESENTATION LAYER                      │
│  Static HTML/JS dashboard                                │
│  (web/index.html) hosted on GitHub Pages                 │
└─────────────────────────────────────────────────────────┘
```

---

## Layers in detail

### Layer 1 — Ingestion

Responsible for fetching all raw external data and returning it as normalized Python dicts. No calculation happens here. Every function in this layer is independently testable and mockable.

| Module | Responsibility | Source |
|---|---|---|
| `src/fetch.py` | Match results, lineups, xG, player stats, injuries | API-Football |
| `src/value.py` | Squad total transfer market value per team | Transfermarkt (scrape) |
| `src/odds.py` | Betting market implied win probability per team | The Odds API |

All API keys are read from environment variables. No keys are ever hardcoded. See [`docs/DATA_SOURCES.md`](DATA_SOURCES.md) for endpoint details and rate limits.

### Layer 2 — Engine

Responsible for all computation. Reads raw data from the ingestion layer (passed in memory from `update.py`), applies the model, and writes results to `data/`.

| Module | Responsibility |
|---|---|
| `src/elo.py` | Maintain and update Elo ratings after each match |
| `src/xg.py` | Calculate xG form ratio from last 5 games |
| `src/injury.py` | Calculate injury multiplier based on key player absences |
| `src/simulate.py` | Run Monte Carlo simulation across the remaining bracket |

The combined team strength formula and all model weights live in `config.py`. See [`docs/MODEL.md`](MODEL.md) for the full model specification.

### Layer 3 — Presentation

A single static HTML file. It fetches `data/predictions.json` at page load using the Fetch API and renders the bracket and win percentages. No build step. No framework. No backend.

Hosted on GitHub Pages — any push that updates `predictions.json` triggers an automatic redeploy within ~30 seconds.

---

## Data flow

This is what happens when you run `python update.py`:

```
update.py starts
    │
    ├─ 1. fetch.py: GET /fixtures (all matches this round, results, xG)
    ├─ 2. fetch.py: GET /players (stats for key players — goals, xG, assists)
    ├─ 3. fetch.py: GET /injuries (current unavailable players per team)
    ├─ 4. value.py: scrape Transfermarkt squad values
    ├─ 5. odds.py:  GET tournament winner odds, convert to implied probabilities
    │
    ├─ 6. elo.py:     update Elo ratings using match results from step 1
    ├─ 7. xg.py:      calculate xG form ratio from last 5 games per team
    ├─ 8. injury.py:  calculate injury multiplier per team from step 3
    │
    ├─ 9. combine: team_strength = weighted sum of all signals × injury_multiplier
    │
    ├─ 10. simulate.py: run 10,000 Monte Carlo simulations of the remaining bracket
    │
    ├─ 11. write data/teams.json      (updated Elo ratings)
    ├─ 12. write data/bracket.json    (updated match results and bracket state)
    └─ 13. write data/predictions.json (win % per team — read by the dashboard)
```

---

## File structure rationale

```
wc2026prediction/
│
├── update.py       Orchestrator. Imports from src/, runs steps 1-13 above.
│                   Should contain no business logic — only calls and ordering.
│
├── config.py       Single source of truth for all constants:
│                   model weights, K-factors, API base URLs, tournament ID,
│                   initial Elo values. Changing a weight means changing one
│                   line here, not hunting through multiple files.
│
├── src/            All business logic. One file per concern.
│                   No file imports from another file in src/ — everything
│                   is coordinated through update.py to avoid circular deps.
│
├── data/           The shared state of the system.
│                   - teams.json and bracket.json are inputs to the engine
│                   - predictions.json is the engine's output
│                   - history/ is write-only (archived after each round)
│                   All three JSON files are committed to Git. This means
│                   the full history of predictions is in version control.
│
└── web/            Completely decoupled from the Python code.
                    Reads predictions.json via fetch() at runtime.
                    Could be replaced with any other frontend without
                    touching a single line of Python.
```

---

## Key design decisions

For the reasoning behind each of these, see [`docs/DECISIONS.md`](DECISIONS.md).

| Decision | Choice | Alternatives considered |
|---|---|---|
| Data storage | JSON files | SQLite, Supabase, Firebase |
| Update trigger | Manual (`python update.py`) | GitHub Actions cron, webhooks |
| Base rating system | Elo | FIFA ranking points, SPI |
| Simulation method | Monte Carlo | Analytical probability math |
| Frontend stack | Vanilla HTML/JS | React, Next.js, Svelte |
| Hosting | GitHub Pages | Vercel, Netlify, Render |

---

## Constraints and assumptions

- **WC 2026 bracket is fixed.** No re-draws after the group stage. Once the Round of 32 bracket was set, every team already knows their path to the final. This means we can fully specify the simulation tree upfront.
- **We update once per round, not per match.** The bracket only meaningfully changes after a full round completes. No need for real-time streaming.
- **Free API tiers only.** API-Football gives 500 calls/day. We use roughly 15-20 calls per update. Plenty of headroom.
- **Model weights are static per round.** We do not recalculate weights between rounds. Weights can be manually tuned in `config.py` if the model is consistently over/under-rating teams.

---

## Extending the system

To add a new data signal:

1. Create `src/your_signal.py` with a single function that returns a `dict[str, float]` mapping team name to signal value
2. Add the function call in `update.py` between steps 5 and 9
3. Add a weight key to `WEIGHTS` in `config.py`
4. Update the `combine()` step to include the new signal
5. Document the signal in `docs/MODEL.md` and the data source in `docs/DATA_SOURCES.md`

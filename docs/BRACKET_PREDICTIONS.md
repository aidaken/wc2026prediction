# Bracket & Round Predictions

This document describes how per-round matchup predictions work, the bracket topology engine, and how advancement probabilities are surfaced on the dashboard.

---

## Overview

The prediction engine produces two complementary outputs:

| Output | File key | Purpose |
|---|---|---|
| **Tournament predictions** | `predictions[]` | Per-team win %, reach-final %, reach-semis % |
| **Match predictions** | `match_predictions{}` | Per-matchup advancement % for each knockout round |

The bracket view on the dashboard shows both **results** (for completed matches) and **estimated advancement chances** (for upcoming matches), similar to a live tournament bracket with win probabilities on each team.

Example display for an upcoming Round of 32 match:

```
POR   62.3%  →
CRO   37.7%  →
```

For a completed match, the winner shows 100% and the loser 0% (or the actual score).

---

## Advancement probability definition

For a knockout match between team A (home) and team B (away):

```
advance_probability_home = P(home wins this match)
advance_probability_away = P(away wins this match)
```

These are computed via **Monte Carlo simulation** over the full remaining bracket:

1. Run `N_SIMULATIONS` (default 10,000) tournament play-throughs.
2. For each unresolved match, simulate a winner using team strengths and the Elo win formula (with draw adjustment).
3. Count how often each team wins their specific matchup.
4. Divide by total simulations → advancement probability.

For **already completed** matches, probabilities are fixed: winner = 1.0, loser = 0.0.

### Why Monte Carlo for matchups?

A team's chance of winning a specific match depends on:

- Direct strength comparison vs their opponent
- The ~25% draw/extra-time compression (`DRAW_PROBABILITY` in `config.py`)

Analytical 1v1 probability is also available via `match_win_probability()` in `simulate.py` as a fallback, but the published numbers come from the same simulation run that produces tournament win %.

---

## Bracket topology

WC 2026 uses a **fixed knockout tree** (combination 67). After the group stage, every team's path to the final is predetermined. Winners do not get re-paired sequentially — they advance into specific next-round slots.

The topology is defined in `src/bracket_topology.py` as `MATCH_FEEDERS`:

```
source_match_id → (target_match_id, "home" | "away")
```

### Example: left side of the bracket

```
GER/PAR ──┐
          ├── r16 Philadelphia (r16_m89) ──┐
FRA/SWE ──┘                                ├── qf Boston (qf_m01)
RSA/CAN ──┐                                │
          ├── r16 Houston (r16_m90) ───────┘
NED/MAR ──┘
```

### Full feeder chain

| From | To |
|---|---|
| 16 × Round of 32 matches | 8 × Round of 16 slots |
| 8 × Round of 16 matches | 4 × Quarter-final slots |
| 4 × Quarter-final matches | 2 × Semi-final slots |
| 2 × Semi-final matches | 1 × Final |

See `MATCH_FEEDERS` in `src/bracket_topology.py` for the complete mapping of all 31 feeder links.

### Simulation algorithm

```python
for each simulation:
    working = copy(bracket.rounds)
    for round in [R32, R16, QF, SF, Final]:
        for match in round.matches:
            if both teams set:
                winner = existing_winner or simulate_match(home, away)
                propagate_winner(working, match_id, winner)  # via MATCH_FEEDERS
    record champion, finalists, per-match win counts
```

**Important:** The engine never uses sequential winner pairing (match 1 winner vs match 2 winner). That was a prior bug; all advancement now follows `MATCH_FEEDERS`.

---

## Output schema

`data/predictions.json` includes a `match_predictions` object keyed by round:

```json
{
  "match_predictions": {
    "round_of_32": [
      {
        "match_id": "r32_m83",
        "team_home": "POR",
        "team_away": "CRO",
        "advance_probability_home": 0.623,
        "advance_probability_away": 0.377,
        "winner": null,
        "status": "NS",
        "score_home": null,
        "score_away": null
      }
    ],
    "round_of_16": [ ... ],
    "quarter_finals": [ ... ],
    "semi_finals": [ ... ],
    "final": [ ... ]
  }
}
```

Round keys match `bracket.json`: `round_of_32`, `round_of_16`, `quarter_finals`, `semi_finals`, `final`.

---

## Dashboard integration

`web/index.html` reads `match_predictions` from `predictions.json` and renders them inside the bracket card below each matchup:

- **Upcoming match:** both teams show their advancement % with a small probability bar.
- **Completed match:** winner highlighted in gold; score shown in the center.
- **TBD slots:** hidden until both teams are known.

The bracket card appears below the tournament win-probability table and top-pick sidebar.

---

## Relationship to tournament-level predictions

| Metric | Scope |
|---|---|
| `advance_probability_*` | Win this specific match → advance one round |
| `reach_semis_probability` | Win all matches on path to semi-finals |
| `reach_final_probability` | Win all matches on path to the final |
| `win_probability` | Win the entire tournament |

A team can have high advancement % in Round of 32 (easy opponent) but lower tournament win % (harder path ahead). The bracket view makes this visible.

---

## Engine fixes (v1.1)

This round-prediction work also addresses structural bugs and model calibration:

### 1. Bracket topology
Replaced sequential winner pairing with `MATCH_FEEDERS` topology map.

### 2. Elo deduplication
`teams.json` `_meta.elo_processed_matches` tracks which fixture IDs have already updated Elo.

### 3. Betting odds normalization
`normalize_betting_probs()` renormalizes implied probabilities across all active teams.

### 4. STRENGTH_SCALE (critical)
`simulate.py` uses `STRENGTH_SCALE` (default 0.50) on normalized `[0, 1]` team strengths — not `ELO_SCALE=400`. See `docs/MODEL.md` and `python scripts/backtest.py --sweep`.

---

## Extending

To add a new knockout round or change the bracket structure:

1. Update `data/bracket.json` match slots.
2. Update `MATCH_FEEDERS` in `src/bracket_topology.py`.
3. Update `DEMO_BRACKET` in `src/seed.py` if using demo mode.
4. No changes needed to the dashboard if round keys stay the same.

---

## Limitations

- Match predictions for future rounds (e.g. a QF matchup) only appear once both teams are known in the bracket.
- Probabilities assume current squad strength and injuries; they do not update mid-match.
- The draw/extra-time model is a simplified probability compression, not a full extra-time + penalties simulation.

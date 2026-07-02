# Bracket and match predictions

How per-match advance % works, the fixed WC tree, and what the dashboard shows.

---

## Two outputs

| What | JSON key | Use |
|---|---|---|
| Tournament | `predictions[]` | Win %, reach final, reach semis |
| Per match | `match_predictions{}` | Advance % for each knockout game |

Bracket UI shows results for finished games and estimated advance % for what's left. Athletic-style tree with flags and little % bars.

Example upcoming R32:

```
POR   62.3%  →
CRO   37.7%  →
```

Done game: winner at 100%, loser 0%, score in the middle.

---

## What advance % means

For home A vs away B:

```
advance_probability_home = P(A wins this match)
advance_probability_away = P(B wins this match)
```

From the same 10k sim run that produces tournament win %:

1. Run `N_SIMULATIONS` (10,000) full bracket play-throughs
2. Each open match: pick winner from strengths + draw logic
3. Count how often each team wins **that specific** fixture
4. Divide by N

Finished matches: winner 1.0, loser 0.0. No sim needed.

### Why Monte Carlo for matchups?

You need direct 1v1 strength **and** the ~27% draw/ET compression (`DRAW_PROBABILITY`). MC handles both in one pass.

`simulate.py` also has `match_win_probability()` for analytical 1v1, but published numbers come from the sim.

---

## Bracket topology

WC 2026 = fixed tree, combination 67. After groups, your path to the final is set. Winners don't get re-drawn into random slots.

Defined in `src/bracket_topology.py` as `MATCH_FEEDERS`:

```
source_match_id → (target_match_id, "home" | "away")
```

### Left side example

```
GER/PAR ──┐
          ├── r16 Philadelphia (r16_m89) ──┐
FRA/SWE ──┘                                ├── qf Boston (qf_m01)
RSA/CAN ──┐                                │
          ├── r16 Houston (r16_m90) ───────┘
NED/MAR ──┘
```

### Feeder chain

| From | To |
|---|---|
| 16 R32 | 8 R16 |
| 8 R16 | 4 QF |
| 4 QF | 2 SF |
| 2 SF | 1 Final |

Full map: `MATCH_FEEDERS` in `bracket_topology.py` (31 links).

### Sim loop

```python
for each simulation:
    working = copy(bracket.rounds)
    for round in [R32, R16, QF, SF, Final]:
        for match in round.matches:
            if both teams set:
                winner = existing_winner or simulate_match(home, away)
                propagate_winner(working, match_id, winner)  # MATCH_FEEDERS
    record champion, finalists, per-match win counts
```

Old bug: paired R32 winner 1 vs winner 2 sequentially. Wrong. Brazil and France are on opposite sides; they should only meet in the final if at all.

---

## JSON shape

`data/predictions.json`:

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

Round keys match `bracket.json`.

---

## Dashboard

`web/index.html` pulls `match_predictions` and paints them on the tree:

- **Upcoming:** both teams get % + thin bar
- **Done:** gold highlight on winner, score center
- **TBD:** hidden until both teams known

Bracket sits below the win-probability table, full width.

---

## Tournament vs match metrics

| Metric | Means |
|---|---|
| `advance_probability_*` | Win this game, go one round further |
| `reach_semis_probability` | Win everything on path to semis |
| `reach_final_probability` | Win everything on path to final |
| `win_probability` | Win the whole thing |

Easy R32 opponent can mean high advance % but lower trophy % if the other side of the bracket is brutal. Bracket view makes that obvious.

---

## v1.1 fixes bundled with this

1. **Topology** — `MATCH_FEEDERS` instead of sequential pairing
2. **Elo dedup** — `_meta.elo_processed_matches` in `teams.json`
3. **Odds norm** — `normalize_betting_probs()` over active teams
4. **STRENGTH_SCALE** — sim uses **0.68** on [0,1] strengths (v1.2 default), not Elo 400 scale. See `docs/MODEL.md`, `backtest.py --sweep`

---

## If you change the bracket

1. Edit `data/bracket.json`
2. Update `MATCH_FEEDERS` in `bracket_topology.py`
3. Update `DEMO_BRACKET` in `src/seed.py` for demo mode
4. Dashboard fine if round key names stay the same

---

## Limits

- QF/SF slots only get predictions when both teams are locked in
- Strengths are pre-match snapshot, no live in-game update
- Draw model compresses to a prob, not full ET + pen shootout sim

# Model

Every formula, signal, weight, and how the Monte Carlo sim works. Constants live in `config.py`.

---

## Overview

Each team gets one **team strength** number. Five signals, weighted sum, then injuries multiply on top:

```
team_strength = (
    elo_normalized          × W_ELO        +
    xg_form_ratio           × W_XG         +
    squad_value_normalized  × W_VALUE      +
    betting_implied_prob    × W_ODDS
) × injury_multiplier
```

Default weights:

| Signal | Weight | Why |
|---|---|---|
| Elo | 0.35 | Long-term baseline, updates after every match |
| xG form | 0.30 | Recent chance quality beats raw goals |
| Squad value | 0.15 | Depth/talent proxy from Transfermarkt |
| Betting odds | 0.20 | Market already mashed a lot of models together |
| Injury | multiplicative | Can shave up to ~20% off if key guys are out |

Weights should sum to 1.0 (injury is separate). Tweak in `config.py` if you disagree with the blend.

---

## Signal 1: Elo

Chess rating system, adapted for football. Beat someone strong, gain more points. Lose to someone weak, lose more.

### Update

```
E_A = 1 / (1 + 10^((R_B - R_A) / ELO_SCALE))

R_A_new = R_A + K × (S_A - E_A)
```

- `R_A`, `R_B` = raw Elo (~1400–2100)
- `ELO_SCALE` = 400 (only for Elo updates, **not** for simulate.py)
- `S_A` = 1 win, 0.5 draw, 0 loss
- `K` = how jumpy ratings are per match type

### K-factors

| Match type | K |
|---|---|
| WC knockout | 60 |
| WC group | 50 |
| Qualifier / big tournament | 40 |
| Friendly | 20 |

### Normalization

For the combined score, squash Elo to [0, 1] across remaining teams:

```
elo_normalized = (R_team - R_min) / (R_max - R_min)
```

---

## Signal 2: xG form

xG = expected goals from shot quality, not lucky bounces. A 35-yard screamer and a tap-in don't weigh the same.

### Form ratio

```
xg_form_ratio = avg_xG_for / (avg_xG_for + avg_xG_against)
```

Last `XG_FORM_GAMES` matches (default 5). WC group games count `XG_WC_MATCH_WEIGHT`× (default 2×) vs friendlies.

- 0.5 = even on chances
- \> 0.5 = creating more than conceding
- \< 0.5 = getting out-chanced

### Luck cap

```
luck_score = actual_goals_for / xg_for
```

If `luck_score > XG_LUCK_THRESHOLD` (1.3), we cap how much that inflates form. Finishing hot streaks don't always repeat.

---

## Signal 3: Squad value

Total Transfermarkt squad €, normalized [0, 1]:

```
squad_value_normalized = (V_team - V_min) / (V_max - V_min)
```

Scraped once per round in `src/value.py`.

---

## Signal 4: Betting odds

Books aggregate a ton of sharp and dumb money. Their outright winner prices are stupidly informative.

### Conversion

```
implied_prob_raw = 1 / decimal_odds
implied_prob     = implied_prob_raw / sum(all_implied_prob_raw)
```

Second step strips the book margin. We also renormalize across **active teams only** in `update.py`.

### Heads up: market bias

20% of strength comes straight from odds. Markets love Brazil, Argentina, Germany brand names. Colombia or Morocco might look underrated vs their xG/Elo. That's not a bug, it's a choice. Drop `W_ODDS` if you want less market in the mix.

---

## Signal 5: Injuries

### Who counts as "key"

**Auto:** top `KEY_PLAYERS_PER_TEAM` (default 2) by goal involvement per 90 this tournament:

```
goal_involvement_per90 = (goals + assists) / minutes_played * 90
```

**Manual:** `KEY_PLAYER_OVERRIDES` in `config.py` for GKs, defensive anchors, etc.

### Importance

```
player_importance = (player_xG_per90 + player_xA_per90) / (team_avg_xG_per90 + team_avg_xA_per90)
```

Capped at `MAX_PLAYER_IMPORTANCE = 0.20`. Missing first-choice GK = flat `GK_PENALTY = 0.05`.

### Multiplier

```
injury_multiplier = 1.0 - sum(importance for each injured starter)
injury_multiplier = max(injury_multiplier, MIN_INJURY_MULTIPLIER)   # floor 0.75
```

The 0.75 floor is a round number. Check if it matters:

```bash
python scripts/backtest.py --sensitivity
```

If ±0.05 on the floor moves top-team win% by more than ~3pp, worth calibrating harder.

---

## Monte Carlo

### STRENGTH_SCALE (don't skip this)

Combined strengths land roughly in [0.15, 0.80]. They are **not** raw Elo.

If you plug `ELO_SCALE = 400` into the match win formula, every game becomes ~50/50. Coin flip tournament. We fixed that in v1.1:

```python
def win_probability(strength_a: float, strength_b: float) -> float:
    return 1 / (1 + 10 ** ((strength_b - strength_a) / STRENGTH_SCALE))
```

Brazil (0.78) vs France (0.64), gap 0.14:

| STRENGTH_SCALE | Brazil win % | Vibe |
|---|---|---|
| 400 (bug) | 50% | wrong |
| 0.30 | 75% | too hot |
| **0.50** | **66%** | starting point |
| 0.80 | 60% | conservative |

Tune it:

```bash
python scripts/backtest.py --sweep
```

Pick the scale that minimizes Brier on completed knockouts, update `config.py`, rerun `update.py`.

### Algorithm (simplified)

```python
def simulate_tournament(teams, bracket, n=10_000):
    win_counts = {team_id: 0 for team_id in teams}
    for _ in range(n):
        winner = play_bracket(teams, bracket)
        win_counts[winner] += 1
    return {team_id: count / n for team_id, count in win_counts.items()}
```

Winners propagate through `MATCH_FEEDERS` in `bracket_topology.py`, not "winner 1 vs winner 2" sequential pairing.

### Draws

`DRAW_PROBABILITY = 0.27` (~share of WC knockouts that went to ET/pens 1994–2022). On a simulated draw, winner picked by strength-weighted coin flip.

±0.05 on draw prob moves top-team win% by ~0.5–1pp. Low sensitivity. `backtest.py --sensitivity` to sanity check.

---

## Backtest

```bash
python scripts/backtest.py           # Brier with current settings
python scripts/backtest.py --sweep   # find STRENGTH_SCALE
python scripts/backtest.py --sensitivity
```

Uses completed matches in `data/bracket.json` and strengths in `data/teams.json`. Best after a round when snapshots are fresh.

**Brier score:**
- \< 0.20: nice
- 0.20–0.25: okay
- \> 0.25: worse than always guessing 50/50, something's off

---

## Limitations (real talk)

- Seven matches max per team. 70% still loses 30% of the time.
- No pressing shape, no "this manager parks the bus" factor beyond xG.
- xG form doesn't adjust for weak group opponents.
- 20% betting signal = some brand-name overweighting.
- Injury floor and draw % are educated guesses, not gospel.
- Transfermarkt lags. Monthly updates, not live.

---

## Done / todo

- [x] STRENGTH_SCALE separate from ELO_SCALE (v1.1)
- [x] Dynamic key players (v1.1)
- [x] Backtest + sweep (v1.1)
- [ ] SOS adjustment on xG form
- [ ] Pre-match Elo snapshots from `data/history/` for cleaner backtest
- [ ] Learn weights from historical WCs
- [ ] Poisson goals instead of binary W/L
- [ ] Confederation strength calibration

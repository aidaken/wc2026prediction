# Model

This document specifies the complete prediction model — every formula, every signal, every weight, and the Monte Carlo simulation algorithm.

All weights and constants referenced here are defined in `config.py`.

---

## Overview

Each team is assigned a **Team Strength Score** — a single normalized number representing their overall strength at any point in the tournament. This score combines five independent signals:

```
team_strength = (
    elo_normalized          × W_ELO        +
    xg_form_ratio           × W_XG         +
    squad_value_normalized  × W_VALUE       +
    betting_implied_prob    × W_ODDS
) × injury_multiplier
```

Default weights (`config.py`):

| Signal | Weight | Reason |
|---|---|---|
| Elo rating | 0.35 | Strong long-term predictor; established baseline |
| xG form ratio | 0.30 | Best short-term form indicator; less noisy than raw goals |
| Squad market value | 0.15 | Strong proxy for depth and overall talent level |
| Betting implied probability | 0.20 | Aggregates thousands of expert models efficiently |
| Injury multiplier | multiplicative | Applied last; can reduce strength by up to 20% |

Weights must sum to 1.0 (excluding the injury multiplier). They can be tuned in `config.py`.

---

## Signal 1 — Elo rating

### What it is

Elo is a zero-sum rating system originally designed for chess. Every team starts with a rating. After each match, the winner gains points from the loser. The number of points exchanged depends on the expected outcome — beating a much stronger team earns more points than beating a weak one.

### Update formula

```
E_A = 1 / (1 + 10^((R_B - R_A) / ELO_SCALE))

R_A_new = R_A + K × (S_A - E_A)
```

Where:
- `R_A` = team A's current Elo rating (raw values ~1400–2100)
- `R_B` = team B's current Elo rating
- `ELO_SCALE` = 400 (standard Elo scale for raw rating values — **only used here, not in simulate.py**)
- `S_A` = actual match outcome: 1.0 (win), 0.5 (draw), 0.0 (loss)
- `K` = K-factor (controls how much ratings shift per match)

### K-factors

| Match type | K value | Rationale |
|---|---|---|
| World Cup knockout match | 60 | Highest-stakes international football |
| World Cup group stage | 50 | High stakes but less decisive |
| WC qualifier / major tournament | 40 | Important but not the main event |
| Friendly / pre-tournament | 20 | Low stakes, often rotated squads |

### Normalization

For the combined formula, Elo is normalized to [0, 1] across all remaining teams:

```
elo_normalized = (R_team - R_min) / (R_max - R_min)
```

---

## Signal 2 — xG form ratio

### What xG is

Expected Goals (xG) measures the quality of goalscoring chances, not the actual result. A shot from close range is worth ~0.3 xG. A shot from 35 yards is worth ~0.02 xG. xG is a much better predictor of future performance than actual goals because it removes short-term luck.

### Form ratio formula

```
xg_form_ratio = avg_xG_for / (avg_xG_for + avg_xG_against)
```

Averages are calculated across the last `XG_FORM_GAMES` matches (default: 5), with WC group stage matches weighted `XG_WC_MATCH_WEIGHT` × (default: 2×) relative to pre-tournament matches.

- 0.5 = team creates as many chances as they concede (neutral)
- Above 0.5 = team dominates chance creation (strong)
- Below 0.5 = team is being out-chanced (weak)

### Score vs xG divergence adjustment

```
luck_score = actual_goals_for / xg_for
```

If `luck_score > XG_LUCK_THRESHOLD` (default 1.3), we cap the effective `xg_form_ratio` to avoid rewarding unsustainable finishing.

---

## Signal 3 — Squad market value

The total transfer market value of a team's squad from Transfermarkt, normalized to [0, 1]:

```
squad_value_normalized = (V_team - V_min) / (V_max - V_min)
```

Fetched once per round via the Transfermarkt scraper in `src/value.py`.

---

## Signal 4 — Betting market implied probability

### Why this works

Betting markets aggregate thousands of models, analysts, and bettors — all with money at stake. Their consensus is empirically one of the strongest predictors of tournament outcomes.

### Conversion formula

```
implied_prob_raw = 1 / decimal_odds
implied_prob     = implied_prob_raw / sum(all_implied_prob_raw)   # removes bookmaker margin
```

### Known bias — self-reinforcing market sentiment

20% of the team_strength score comes directly from betting markets. The model's own docs acknowledge that markets tend to overweight historically prominent teams (Brazil, Argentina, Germany) due to public betting bias and brand recognition. This means the model is **not fully independent from market sentiment** — a team like Colombia or Morocco may be systematically underrated relative to what their on-pitch metrics would suggest.

This is not necessarily wrong to include — markets are genuinely informative — but it should be understood when interpreting results. If you believe the market is systematically wrong about a specific team, decrease `W_ODDS` in `config.py` for that update cycle.

---

## Signal 5 — Injury multiplier

### Key player detection

Players are flagged as "key" by two mechanisms:

**Automatic detection (per-round):** For every team, `src/injury.py` ranks all players by goal involvement per 90 minutes this tournament:

```
goal_involvement_per90 = (goals + assists) / minutes_played * 90
```

The top `KEY_PLAYERS_PER_TEAM` players (default: 2) per team are automatically flagged as key. This ensures that Colombia's top scorer, Morocco's key midfielder, or any other team's standout player is captured without manual intervention.

**Manual overrides:** `KEY_PLAYER_OVERRIDES` in `config.py` hard-codes players whose importance cannot be captured by goal involvement alone (e.g. a goalkeeper, a player whose value is defensive).

### Importance formula

For each flagged player:

```
player_importance = (player_xG_per90 + player_xA_per90) / (team_avg_xG_per90 + team_avg_xA_per90)
```

Capped at `MAX_PLAYER_IMPORTANCE = 0.20` (no single player can account for more than 20% of team strength).

Goalkeepers: a missing first-choice GK applies a fixed `GK_PENALTY = 0.05` regardless of attacking stats.

### Multiplier formula

```
injury_multiplier = 1.0 - sum(player_importance for each injured starter)
injury_multiplier = max(injury_multiplier, MIN_INJURY_MULTIPLIER)   # floor: 0.75
```

The floor (`MIN_INJURY_MULTIPLIER = 0.75`) prevents extreme cases from producing unrealistic predictions. This is a round number with no precise empirical source. To validate it, run:

```bash
python scripts/backtest.py --sensitivity
```

If shifting the floor by ±0.05 moves the top team's predicted win% by less than 1–2 percentage points, the round number is fine to keep. If the swing is larger than 3pp, it warrants a cited source or more careful calibration.

---

## Monte Carlo simulation

### ⚠️ STRENGTH_SCALE — critical parameter

The team_strength values produced by the combined formula above are normalized floats roughly in the range [0.15, 0.80]. They are **not** raw Elo ratings.

Using `ELO_SCALE = 400` in the win probability formula with these normalized values would produce near-50/50 probabilities for every match — effectively a coin flip. The fix is a separate `STRENGTH_SCALE` constant calibrated to the [0, 1] strength range:

```python
# simulate.py — correct version
def win_probability(strength_a: float, strength_b: float) -> float:
    return 1 / (1 + 10 ** ((strength_b - strength_a) / STRENGTH_SCALE))
```

Effect of `STRENGTH_SCALE` on a Brazil (0.78) vs France (0.64) matchup (gap = 0.14):

| STRENGTH_SCALE | Brazil win prob | Assessment |
|---|---|---|
| 400 (bug) | 50.0% | coin flip — completely wrong |
| 0.30 | 75% | overconfident for football |
| **0.50** | **66%** | **sensible starting point** |
| 0.80 | 60% | conservative but defensible |

The right value depends on what the actual combined strength scores look like after normalization. **Tune it empirically:**

```bash
python scripts/backtest.py --sweep
```

The sweep tests `STRENGTH_SCALE` from 0.10 to 1.50 and finds the value that minimises Brier score on completed matches. After finding the best value, update `config.py` and re-run `update.py`.

### Algorithm

```python
def simulate_tournament(teams, bracket, n=10_000):
    win_counts = {team_id: 0 for team_id in teams}
    for _ in range(n):
        winner = play_bracket(teams, bracket)
        win_counts[winner] += 1
    return {team_id: count / n for team_id, count in win_counts.items()}

def play_bracket(teams, bracket):
    remaining = copy(bracket)
    for round in ["r16", "qf", "sf", "final"]:
        for match in remaining[round]:
            winner = simulate_match(teams[match.team_a], teams[match.team_b])
            advance(winner, next_round)
    return champion

def simulate_match(team_a, team_b):
    prob_a = win_probability(team_a.strength, team_b.strength)
    return team_a.id if random() < prob_a else team_b.id
```

### Draw probability

`DRAW_PROBABILITY = 0.27` — approximately 27% of knockout matches in World Cup history (1994–2022) were decided in extra time or penalties. When a draw is simulated, the winner is determined by a coin flip weighted by relative team strength.

Sensitivity: shifting this value by ±0.05 moves the top team's predicted win% by ~0.5–1 percentage point. Low impact. To verify:

```bash
# In config.py, temporarily change DRAW_PROBABILITY, run update.py, compare predictions
python scripts/backtest.py --sensitivity
```

---

## Validating the model

Run the backtest script after any parameter change:

```bash
# Quick check with current settings
python scripts/backtest.py

# Find optimal STRENGTH_SCALE
python scripts/backtest.py --sweep

# Check sensitivity of floor/draw parameters
python scripts/backtest.py --sensitivity
```

The backtest uses completed matches from `data/bracket.json` and the team strength values in `data/teams.json`. It is most accurate when run after a round completes (team_strength values reflect pre-round ratings in the history snapshots).

**Brier score interpretation:**
- < 0.20: well-calibrated, better than baseline
- 0.20–0.25: reasonable, close to baseline
- \> 0.25: worse than always predicting 50/50 — something is wrong

---

## Limitations

- **Small tournament sample.** 7 matches maximum per team. A 70% predicted probability will still lose 30% of the time. Variance is inherent.
- **Tactical factors not captured.** Pressing, defensive shape, coach-specific setups are only partially reflected through xG.
- **Strength-of-schedule not adjusted.** A team's xG form in three group games against weak opponents may be inflated. No SOS correction is applied.
- **Betting market self-reinforcing bias.** 20% of the team_strength score comes from markets that are known to overweight prominent brands (Brazil, Argentina). The model is not fully independent of market sentiment. See Signal 4 above.
- **Injury floor and draw probability are round numbers.** `MIN_INJURY_MULTIPLIER = 0.75` and `DRAW_PROBABILITY = 0.27` are informed estimates, not precisely calibrated constants. Validate with `python scripts/backtest.py --sensitivity`.
- **Transfermarkt values lag.** Updated monthly. May not reflect very recent injuries.

---

## Future improvements

- [x] STRENGTH_SCALE separate from ELO_SCALE (v1.1)
- [x] Dynamic key player detection (v1.1)
- [x] Backtest script with Brier score and scale sweep (v1.1)
- [ ] Strength-of-schedule adjustment for xG form ratio
- [ ] Pre-match Elo snapshots in backtest (use history/ for more accurate pre-match ratings)
- [ ] Automated weight optimization using historical WC data
- [ ] Match-level Poisson goal distribution model (replaces binary win/loss simulation)
- [ ] Confederation adjustment for cross-region strength calibration

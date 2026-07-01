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

Weights must sum to 1.0 (excluding the injury multiplier). They can be tuned in `config.py` — see the [tuning section](#tuning-model-weights) below.

---

## Signal 1 — Elo rating

### What it is

Elo is a zero-sum rating system originally designed for chess. Every team starts with a rating. After each match, the winner gains points from the loser. The number of points exchanged depends on the expected outcome — beating a much stronger team earns more points than beating a weak one.

### Update formula

```
E_A = 1 / (1 + 10^((R_B - R_A) / 400))

R_A_new = R_A + K × (S_A - E_A)
```

Where:
- `R_A` = team A's current Elo rating
- `R_B` = team B's current Elo rating
- `E_A` = team A's expected score (probability of winning)
- `S_A` = actual match outcome: 1.0 (win), 0.5 (draw), 0.0 (loss)
- `K` = K-factor (controls how much ratings shift per match)

### K-factors

| Match type | K value | Rationale |
|---|---|---|
| World Cup knockout match | 60 | Highest-stakes international football |
| World Cup group stage | 50 | High stakes but less decisive |
| WC qualifier / major tournament | 40 | Important but not the main event |
| Friendly / pre-tournament | 20 | Low stakes, often rotated squads |

Only matches from the last 2 years are used to seed initial ratings. Older matches are discounted.

### Initial Elo values (WC 2026 start)

Starting Elo values are seeded from the most recent iteration of the [World Football Elo Ratings](https://www.eloratings.net/). These are stored in `data/teams.json` and updated in-place as the tournament progresses.

Approximate starting range:
- Elite (Brazil, France, Spain, Argentina): 1950–2100
- Strong (England, Germany, Portugal, Netherlands): 1800–1950
- Mid-tier (USA, Mexico, Senegal, Morocco): 1600–1800
- Lower (Curaçao, Haiti, Jordan): 1400–1600

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

Where averages are calculated across the **last 5 matches**, with WC group stage matches weighted 2× compared to pre-tournament matches.

- Result of 0.5 = team creates as many chances as they concede (neutral)
- Result above 0.5 = team dominates in chance creation (strong)
- Result below 0.5 = team is being out-chanced (weak)

### Score vs xG divergence adjustment

If a team's actual goals diverge significantly from their xG, we flag it as a luck adjustment:

```
luck_score = actual_goals_for / xg_for   # > 1.0 = overperforming, likely lucky
```

If `luck_score > 1.3` (scoring 30% more than expected), we cap the effective `xg_form_ratio` to prevent rewarding unsustainable finishing. This is a soft cap applied before normalization.

### Normalization

```
xg_form_ratio is already bounded [0, 1] by definition
```

---

## Signal 3 — Squad market value

### What it measures

The total transfer market value of a team's squad, pulled from Transfermarkt. This is a strong proxy for:
- Overall talent level
- Squad depth (a €1B squad absorbs injuries better)
- Player quality relative to international peers

### Normalization

```
squad_value_normalized = (V_team - V_min) / (V_max - V_min)
```

Where `V_min` and `V_max` are across all remaining teams in the tournament at the time of update.

Squad values are fetched once per round from Transfermarkt. Values do not change meaningfully mid-round.

---

## Signal 4 — Betting market implied probability

### Why this works

Betting markets aggregate thousands of models, analysts, and informed bettors — all with money at stake. Their consensus is empirically one of the strongest predictors of tournament outcomes. We are not betting. We are using their aggregate intelligence as one input signal.

### Conversion formula

Raw betting odds (decimal format) are converted to implied probability:

```
implied_prob_raw = 1 / decimal_odds
```

Because bookmakers include a margin (vig), the raw probabilities sum to more than 1.0. We normalize:

```
implied_prob = implied_prob_raw / sum(all_implied_prob_raw)
```

This gives a clean probability distribution across all remaining teams that sums to exactly 1.0.

### Data source

The Odds API — free tier. We fetch pre-match tournament winner odds once per round update.

---

## Signal 5 — Injury multiplier

### What it captures

The absence of key players — especially a first-choice goalkeeper or top striker — materially reduces a team's strength. This is applied as a multiplicative penalty on the combined score, not as an additive signal.

### Player importance score

For each player currently listed as injured or suspended:

```
player_importance = (player_xG_per90 + player_xA_per90) / (team_avg_xG_per90 + team_avg_xA_per90)
```

This is capped at `MAX_PLAYER_IMPORTANCE = 0.20` (20%) to prevent a single player from dominating the calculation.

Special case for goalkeepers: a first-choice goalkeeper being absent applies a fixed `0.05` penalty regardless of their attacking stats.

### Multiplier calculation

```
injury_multiplier = 1.0

for each injured_player in team.injured:
    if injured_player.is_starting_xi:
        injury_multiplier -= player_importance(injured_player)

injury_multiplier = max(injury_multiplier, MIN_MULTIPLIER)  # floor at 0.75
```

Example:
- France without Mbappé (estimated importance ~0.18): `1.0 - 0.18 = 0.82`
- France without Mbappé + starting GK: `1.0 - 0.18 - 0.05 = 0.77`

---

## Monte Carlo simulation

### Algorithm

```python
def simulate_tournament(teams, bracket, n=10_000):
    win_counts = {team_id: 0 for team_id in teams}

    for _ in range(n):
        winner = play_bracket(teams, bracket)
        win_counts[winner] += 1

    return {team_id: count / n for team_id, count in win_counts.items()}


def play_bracket(teams, bracket):
    remaining = dict(bracket)  # copy so we don't mutate

    for round in ["r16", "qf", "sf", "final"]:
        next_round = {}
        for match_id, (team_a, team_b) in remaining[round].items():
            winner = simulate_match(teams[team_a], teams[team_b])
            next_round[match_id] = winner
        remaining[round] = next_round

    return remaining["final"][0]  # the winner


def simulate_match(team_a, team_b):
    prob_a = win_probability(team_a.strength, team_b.strength)
    return team_a.id if random() < prob_a else team_b.id
```

### Win probability per match

```
prob_A_wins = 1 / (1 + 10^((strength_B - strength_A) / 400))
```

This is the standard Elo win expectancy formula, applied to our composite strength score rather than raw Elo.

For matches that may go to extra time and penalties: we add a small random draw probability (~25% of matches at knockout stages) which resolves via a coin-weighted flip.

### Simulation count

Default: `N_SIMULATIONS = 10_000` (set in `config.py`).

At 10,000 runs, the standard error on a 20% probability is ~0.4 percentage points — accurate enough for this purpose. Increasing to 100,000 reduces noise further but adds ~1 second of compute time.

---

## Tuning model weights

Weights can be adjusted in `config.py` under `WEIGHTS`. They must sum to 1.0.

To evaluate whether a weight change improves the model:

1. Pull historical WC 2026 group stage data (already in `data/bracket.json` after first run)
2. Run `python scripts/backtest.py` (backtest utility — see future improvements)
3. Compare predicted probabilities vs actual outcomes using Brier score or log-loss

Rough guidance:
- If the model is consistently over-rating favorites → decrease `W_ELO`, increase `W_XG`
- If upsets are being underestimated → decrease `W_ODDS` (markets underweight upsets)
- If injury impacts seem too strong or too weak → adjust `MAX_PLAYER_IMPORTANCE`

---

## Limitations

- **Small sample size.** A knockout tournament is 7 matches at most per team. Variance is inherently high. A model predicting a 70% win probability will still see that team lose 30% of the time in reality.
- **Tactical factors not captured.** Pressing intensity, defensive organization, and coach-specific strategies are not in the model. These are partially captured by xG but not fully.
- **Hot streaks are noisy.** xG form over 5 games can be influenced by opponent quality. We do not fully adjust for strength of schedule in the form calculation.
- **Transfermarkt values lag.** Squad values are updated ~monthly. They may not reflect very recent transfers or injuries that affect perceived value.
- **Betting markets are not perfectly efficient.** They can be slow to update on injury news and may overweight brand-name teams (Brazil, Argentina) due to public betting bias.

---

## Future improvements

- [ ] Strength-of-schedule adjustment for xG form ratio
- [ ] Backtesting script (`python scripts/backtest.py`) with Brier score output
- [ ] Automated weight optimization using historical tournament data
- [ ] Match-level xG expected goals model (Poisson distribution per match)
- [ ] Confederation adjustment (account for variation in competition quality by region)

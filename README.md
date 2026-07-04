# WC 2026 Prediction Engine

I built this to predict who wins the 2026 World Cup. Not vibes, not "Brazil always good." Five signals, Monte Carlo bracket sim, numbers you can argue with.

**Live site:** [aidaken.github.io/wc2026prediction/web](https://aidaken.github.io/wc2026prediction/web/)

---

## How it works (30 seconds)

1. **Strength score** per team from five signals (Elo, xG form, squad value, betting odds, injuries)
2. **Monte Carlo** simulates the full knockout bracket 10,000 times
3. **Output:** win probability per team + per-match advancement % on the bracket

Details: [`docs/MODEL.md`](docs/MODEL.md). Bracket math: [`docs/BRACKET_PREDICTIONS.md`](docs/BRACKET_PREDICTIONS.md).

---

## Quick start

**No API keys needed** for the main loop. Wikipedia + cached files get you most of the way.

```bash
git clone https://github.com/aidaken/wc2026prediction.git
cd wc2026prediction
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Pull latest results from Wikipedia → bracket + fixtures cache
python scripts/fetch_public.py

# Recalculate strengths + run Monte Carlo
python update.py
```

Open `web/index.html` locally or hit the GitHub Pages link above.

Optional keys in `.env` (see `.env.example`): API-Football, Odds API, Transfermarkt. Free tiers are limited for WC 2026. The engine degrades gracefully when they're missing or broken.

Full setup: [`docs/SETUP.md`](docs/SETUP.md).

---

## After each round (the workflow I actually use)

```bash
python scripts/fetch_public.py   # Wikipedia → data/bracket.json + data/fixtures_cache.json
python update.py                 # strengths + predictions.json
git add data/
git commit -m "data: post-round-N results"
git push
```

GitHub Pages redeploys from `main`. Site updates in ~1 min.

Missing data? Two manual overrides fill the gaps when the APIs won't serve 2026:

- **Odds:** `data/manual_odds.json` (copy the example) — implied win probs per 3-letter id, `1/decimal` or `100/(american+100)`. Fills the 20% odds slot.
- **xG:** `data/manual_xg.json` (copy the example) — per team `xg` / `xga` / `mp`, paste straight from FotMob's xG table. Overrides the goals fallback in form.

Both renormalize/merge on their own, so rough or partial is fine.

---

## Project layout

```
wc2026prediction/
├── config.py              # weights, STRENGTH_SCALE, sim count
├── update.py              # main orchestrator
├── scripts/
│   ├── fetch_public.py    # Wikipedia scrape (no keys)
│   └── backtest.py        # Brier score + STRENGTH_SCALE sweep
├── src/
│   ├── public_fetch.py    # MediaWiki parser for WC 2026 results
│   ├── strength.py        # combine signals (per-team weight fallback)
│   ├── simulate.py        # Monte Carlo + bracket topology
│   ├── fetch.py           # API-Football fixtures (optional)
│   └── ...
├── data/
│   ├── teams.json         # team list + FIFA ranks
│   ├── bracket.json       # full bracket + results
│   ├── fixtures_cache.json
│   ├── predictions.json   # output (committed for GitHub Pages)
│   └── manual_odds.json.example
├── web/
│   └── index.html         # bracket UI
└── docs/
```

---

## Model version

**v1.2.0** (current)

| Signal | Weight | Source |
|--------|--------|--------|
| Elo | 35% | ClubElo / FIFA fallback |
| xG form | 30% | Match xG from fixtures, or goals fallback |
| Squad value | 15% | Transfermarkt (cached) |
| Betting odds | 20% | Odds API or `manual_odds.json` |
| Injuries | multiplier | API-Football or static overrides |

`STRENGTH_SCALE = 0.68` (tuned via `backtest.py --sweep`). When a signal is missing for a team, its weight gets redistributed across what's left. No more France 33% / Brazil 27% because two teams had xG and everyone else didn't.

Weights and per-team breakdowns land in `predictions.json` under `_meta`.

---

## Docs

| Doc | What |
|-----|------|
| [`docs/MODEL.md`](docs/MODEL.md) | Signal math, Monte Carlo, backtest |
| [`docs/BRACKET_PREDICTIONS.md`](docs/BRACKET_PREDICTIONS.md) | Per-match advancement % |
| [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md) | Where each number comes from |
| [`docs/DATA_PIPELINE.md`](docs/DATA_PIPELINE.md) | fetch_public → update flow |
| [`docs/SETUP.md`](docs/SETUP.md) | Keys, venv, troubleshooting |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | ADRs (why Wikipedia-first, etc.) |
| [`CHANGELOG.md`](CHANGELOG.md) | Version history |

---

## Contributing

PRs welcome. Read [`CONTRIBUTING.md`](CONTRIBUTING.md) first. If you change model weights or `STRENGTH_SCALE`, run `backtest.py` and note Brier in the PR.

---

## License

MIT. Data sources have their own terms. See [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md).

# wc2026prediction

I built this to guess who's winning the 2026 World Cup after each knockout round. Pull match data, score the teams, run 10k sims, dump win % to JSON. GitHub Pages reads that file and draws the bracket

No database, no server, no bill. Python plus three JSON files

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Live:** [aidaken.github.io/wc2026prediction/web/](https://aidaken.github.io/wc2026prediction/web/)

---

## What `update.py` does

1. Grab results, xG, injuries, player stats from API-Football
2. Mash Elo, xG form, squad value, betting odds, and injuries into one **team strength** number
3. Sim the rest of the bracket 10,000 times
4. Write `data/predictions.json` (win %, per-match advance %, signal breakdown)
5. Dashboard fetches it and paints the tree

---

## After each round

```bash
python update.py
git add data/predictions.json data/bracket.json data/teams.json
git commit -m "chore: update predictions after Round of 16"
git push
```

Site picks up the new JSON in ~30 seconds.

No API keys? Demo mode still runs:

```bash
python update.py --demo
```

---

## Where stuff lives

```
wc2026prediction/
├── update.py              # run after every round
├── config.py              # weights, scales, api keys path
├── src/
│   ├── fetch.py           # API-Football
│   ├── elo.py, xg.py, injury.py, value.py, odds.py
│   ├── simulate.py        # monte carlo
│   ├── bracket_topology.py  # fixed wc tree, who feeds where
│   └── teams.py           # name/id mappings
├── data/
│   ├── teams.json
│   ├── bracket.json
│   ├── predictions.json   # web reads this
│   └── history/           # snapshot per round
└── web/index.html         # dashboard
```

---

## More docs

| File | What's in it |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | How the pieces connect |
| [docs/MODEL.md](docs/MODEL.md) | Formulas, STRENGTH_SCALE, the sim |
| [docs/BRACKET_PREDICTIONS.md](docs/BRACKET_PREDICTIONS.md) | Per-match advance % on the UI |
| [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) | APIs, scraping, rate limits |
| [docs/DATA_PIPELINE.md](docs/DATA_PIPELINE.md) | `update.py` step by step |
| [docs/SETUP.md](docs/SETUP.md) | Install, keys, GitHub Pages |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Why JSON not Postgres, etc. |
| [docs/VOICE.md](docs/VOICE.md) | How I want commits and docs to sound |
| [CONTRIBUTING.md](CONTRIBUTING.md) | If you're hacking on this |

---

## Stack

Python 3.10+, `requests`, `beautifulsoup4`, plain HTML/JS, GitHub Pages. MIT.

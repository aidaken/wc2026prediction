# 🏆 wc2026prediction

Real-time FIFA World Cup 2026 winner predictor. Pulls live match data after each round, calculates team strength across five signals, and runs 10,000 Monte Carlo simulations to surface win probabilities for every remaining team.

No database. No server. No monthly bills. Just Python, three JSON files, and a static site on GitHub Pages.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub Pages](https://img.shields.io/badge/hosted-GitHub%20Pages-orange.svg)](https://pages.github.com/)

---

## What it does

1. Fetches live results, xG, player stats, and injury reports from **API-Football**
2. Calculates a **Team Strength Score** combining Elo rating, xG form, squad market value, injury adjustments, and betting market data
3. Simulates the remaining bracket **10,000 times** via Monte Carlo
4. Writes win probabilities per team to `data/predictions.json`
5. A static dashboard at GitHub Pages reads that file and renders the live bracket

---

## Features

- **Real data** — match results, xG, injuries, and player stats from API-Football (free tier)
- **Multi-signal model** — five independent signals combined with tunable weights
- **Injury-aware** — key player absences reduce team strength automatically
- **Market signals** — betting implied probabilities as expert consensus input
- **Monte Carlo simulation** — 10,000 full tournament simulations per round update
- **Zero infrastructure** — JSON files only, no database, no server, no cost
- **One command update** — `python update.py` handles everything after each round

---

## Quick start

### Prerequisites

- Python 3.10 or higher
- Git
- Free API key from [API-Football](https://www.api-football.com/) (500 calls/day on free tier)
- Optional: free API key from [The Odds API](https://the-odds-api.com/) (500 calls/month free)

### Install

```bash
# Clone
git clone https://github.com/yourusername/wc2026prediction.git
cd wc2026prediction

# Virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Dependencies
pip install -r requirements.txt

# Environment variables
cp .env.example .env
# Open .env and fill in your API keys
```

### Run

```bash
python update.py
```

First run bootstraps everything — fetches all group stage results, builds initial team ratings, runs the simulation, and writes `data/predictions.json`. Open `web/index.html` in your browser to see the dashboard.

See [`docs/SETUP.md`](docs/SETUP.md) for the full walkthrough including GitHub Pages setup.

---

## Updating after each round

Once a round ends and all results are confirmed:

```bash
python update.py
git add data/predictions.json data/bracket.json data/teams.json
git commit -m "chore: update predictions after Round of 16"
git push
```

GitHub Pages picks up `predictions.json` and the live dashboard updates within ~30 seconds.

---

## Project structure

```
wc2026prediction/
│
├── update.py               # Orchestrator — run this after every round
├── config.py               # Weights, K-factors, API config, tournament IDs
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template (copy to .env)
│
├── src/
│   ├── fetch.py            # API-Football client
│   ├── elo.py              # Elo rating system
│   ├── xg.py               # xG form ratio calculator
│   ├── injury.py           # Injury/suspension strength multiplier
│   ├── value.py            # Transfermarkt squad value scraper
│   ├── odds.py             # Betting market probability converter
│   └── simulate.py         # Monte Carlo tournament simulation engine
│
├── data/
│   ├── teams.json          # Team registry: Elo, squad value, metadata
│   ├── bracket.json        # Live bracket: matches, results, current round
│   ├── predictions.json    # Output: win % per remaining team (read by web/)
│   └── history/            # Archived predictions snapshot per round
│       ├── round_32.json
│       ├── round_16.json
│       └── ...
│
├── web/
│   └── index.html          # Static dashboard (reads predictions.json via fetch)
│
└── docs/
    ├── SETUP.md            # Full installation and configuration guide
    ├── MODEL.md            # Prediction model — formulas, logic, weights
    ├── DATA_SOURCES.md     # APIs, scraping, rate limits, data contracts
    ├── DATA_PIPELINE.md    # Pipeline steps, JSON schemas, error handling
    └── DECISIONS.md        # Architecture decision records
```

---

## Documentation

| Document | What it covers |
|---|---|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | System design, layers, data flow, tech choices |
| [`docs/MODEL.md`](docs/MODEL.md) | Full model logic — Elo, xG, Monte Carlo, formulas |
| [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md) | Every data source, endpoints, rate limits |
| [`docs/DATA_PIPELINE.md`](docs/DATA_PIPELINE.md) | Pipeline steps, JSON schemas, error handling |
| [`docs/SETUP.md`](docs/SETUP.md) | Installation, API keys, GitHub Pages |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | Why we made each architectural choice |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | How to contribute or extend the model |
| [`CHANGELOG.md`](CHANGELOG.md) | Version history and round-by-round updates |

---

## Tech stack

| Layer | Tool | Reason |
|---|---|---|
| Language | Python 3.10+ | Excellent data libraries, readable |
| HTTP | `requests` | Simple, no overhead |
| Scraping | `beautifulsoup4` | Lightweight Transfermarkt scraper |
| Numerics | `numpy` | Fast Monte Carlo simulation arrays |
| Data storage | JSON files | Zero infrastructure, Git-versionable |
| Frontend | Vanilla HTML + JS | No build step, works on GitHub Pages |
| Hosting | GitHub Pages | Free, auto-updates on push |

---

## License

MIT — see [`LICENSE`](LICENSE).

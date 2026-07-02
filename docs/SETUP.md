# Setup

Get the predictor running locally and on GitHub Pages.

---

## Requirements

- Python 3.10+
- Git
- API keys (or use `--demo`)

---

## Local install

```bash
git clone https://github.com/aidaken/wc2026prediction.git
cd wc2026prediction
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## API keys

Copy the example env file and fill in keys:

```bash
cp .env.example .env
```

| Variable | Where to get it | Used for |
|---|---|---|
| `API_FOOTBALL_KEY` | [api-football.com](https://www.api-football.com/) | Fixtures, xG, players, injuries |
| `ODDS_API_KEY` | [the-odds-api.com](https://the-odds-api.com/) | Tournament winner odds |

Transfermarkt scraping doesn't need a key. It can break if they change HTML.

No keys? Demo mode uses cached/sample data:

```bash
python update.py --demo
```

---

## First run

```bash
python update.py
```

You should get:

- `data/teams.json` — strengths, Elo, signals
- `data/bracket.json` — remaining matches
- `data/predictions.json` — win % and match predictions
- `data/history/` — timestamped snapshot

Open the dashboard locally:

```bash
# from repo root, any static server works
python -m http.server 8000
# then http://localhost:8000/web/
```

Or just open `web/index.html` (some browsers block fetch to local files; server is safer).

---

## GitHub Pages

Repo Settings → Pages → Source: **Deploy from branch** → `main` → `/ (root)`.

The site lives at:

`https://<username>.github.io/wc2026prediction/web/`

There's a redirect at repo root if you hit the base URL without `/web/`.

After each round: run `update.py`, commit the three `data/*.json` files, push. Pages rebuilds in ~30s.

---

## Troubleshooting

**API rate limit** — API-Football free tier is tight. Wait or upgrade. `--demo` still works.

**Empty predictions** — Check `.env` keys. Run with verbose logging if you added it.

**Bracket looks wrong** — `data/bracket.json` must match FIFA combination 67. See `src/bracket_topology.py`.

**CORS on local file** — Use `python -m http.server`, don't double-click the HTML.

---

## Optional: cron after each round

If you host this on a VPS (I don't for this project), you could cron `update.py` and auto-push. For GitHub Pages I just run it manually post-round.

# Setup

Get the predictor running locally. GitHub Pages deploy is just push to `main`.

---

## Requirements

- Python 3.10+
- Git
- API keys **optional** (Wikipedia path needs none)

---

## Local install

```bash
git clone https://github.com/aidaken/wc2026prediction.git
cd wc2026prediction
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Always use the venv. System Python often lacks `python-dotenv`.

---

## First run (no keys)

```bash
python scripts/fetch_public.py   # Wikipedia → bracket + fixtures cache
python update.py                 # strengths + predictions
```

You should get:

- `data/bracket.json` — structure + results
- `data/fixtures_cache.json` — match history for form
- `data/teams.json` — strengths, Elo, signals
- `data/predictions.json` — win % and match predictions
- `data/history/` — timestamped snapshot (if enabled)

Open the dashboard:

```bash
python -m http.server 8000
# http://localhost:8000/web/
```

Don't double-click `web/index.html`. Browsers block `fetch()` to local files.

---

## Optional API keys

```bash
cp .env.example .env
```

| Variable | Where | Used for | Free tier catch |
|---|---|---|---|
| `API_FOOTBALL_KEY` | [api-football.com](https://www.api-football.com/) | xG, players, injuries | **Seasons 2022–2024 only.** WC 2026 often unavailable |
| `ODDS_API_KEY` | [the-odds-api.com](https://the-odds-api.com/) | Outright winner odds | Market may 422 until books post lines |

Transfermarkt scrape needs no key. It breaks when they change HTML.

### Manual odds (no Odds API)

```bash
cp data/manual_odds.json.example data/manual_odds.json
# edit decimal odds per team name
```

`update.py` picks this up automatically when the API path fails.

---

## Demo mode

```bash
python update.py --demo
```

Cached/sample data only. Skips most live API calls. Fine for tests, not for publishing post-round updates.

---

## GitHub Pages

Repo Settings → Pages → **Deploy from branch** → `main` → `/ (root)`.

Live URL: `https://aidaken.github.io/wc2026prediction/web/`

After each round:

```bash
python scripts/fetch_public.py && python update.py
git add data/
git commit -m "data: post-round-N"
git push
```

Rebuild ~30s.

---

## Troubleshooting

**`ModuleNotFoundError: dotenv`** — Activate `.venv` and `pip install -r requirements.txt`. Don't use bare `python3 update.py` on macOS system Python.

**API-Football returns empty for 2026** — Expected on free tier. Rely on `fetch_public.py` + `fixtures_cache.json`. xG may be missing; form uses goals fallback.

**Odds API 422** — No WC outright market yet. Use `manual_odds.json` or let engine redistribute the 20% odds weight.

**Transfermarkt 404/502** — Uses cached `squad_value_eur` from last good scrape.

**Bracket looks wrong** — `data/bracket.json` must match FIFA combination 67. See `src/bracket_topology.py`. Wikipedia merge is by pairing; weird edge cases get hand-edits.

**France/Brazil way ahead of everyone** — Old bug when two teams had xG and others didn't. v1.2 redistributes weights per team. Check `predictions.json` `_meta.strength_meta`.

**CORS on local file** — Use `python -m http.server`.

---

## Optional: cron on a VPS

I don't do this for GitHub Pages. If you host elsewhere you could cron `fetch_public.py && update.py` and auto-push. Knockout rounds are sparse; manual is fine.

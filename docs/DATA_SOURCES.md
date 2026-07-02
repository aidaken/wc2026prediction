# Data sources

All external data the model depends on, with endpoint details, rate limits, authentication, and the exact fields we extract.

---

## Summary

| Source | Used for | Cost | Calls per update | Daily limit |
|---|---|---|---|---|
| API-Football | Results, xG, players, injuries | Free tier | ~20 | 500/day |
| Transfermarkt | Squad market values | Free (scrape) | 16 (one per team) | No hard limit |
| The Odds API | Betting implied probabilities | Free tier | 1 | 500/month |
| FBref | Deep player stats (optional) | Free (scrape) | 16 | Throttle manually |

All API keys are stored in `.env` and read via `python-dotenv`. Never commit `.env` to Git — it is listed in `.gitignore`.

---

## API-Football

**Base URL:** `https://v3.football.api-sports.io`  
**Auth:** `X-RapidAPI-Key: YOUR_KEY` header  
**Registration:** [api-football.com](https://www.api-football.com/) — free tier, no credit card  
**Free limits:** 500 requests/day, 30 requests/minute  
**WC 2026 tournament ID:** `1` (confirm on first run via `/leagues` endpoint)

### Endpoints we use

#### GET /fixtures

Fetches match results for the current round.

```
GET /fixtures?league=1&season=2026&round=Round of 32
```

Fields we extract:
- `fixture.id` — match ID
- `fixture.date` — match date (UTC)
- `fixture.status.short` — `FT` (full time), `PEN` (after penalties), `NS` (not started)
- `teams.home.id`, `teams.home.name`
- `teams.away.id`, `teams.away.name`
- `goals.home`, `goals.away` — final score
- `score.penalty.home`, `score.penalty.away` — penalty shootout score (if applicable)

#### GET /fixtures/statistics

xG and match stats per fixture. Called once per completed match.

```
GET /fixtures/statistics?fixture=FIXTURE_ID
```

Fields we extract:
- `statistics[].statistics` → filter for `type: "expected_goals"` → `value`
- Also pulls: shots on target, possession, passes

#### GET /players

Player stats for key players. Called once per team per round.

```
GET /players?league=1&season=2026&team=TEAM_ID
```

Fields we extract per player:
- `player.id`, `player.name`, `player.position`
- `statistics[0].goals.total` — goals this tournament
- `statistics[0].goals.assists`
- Expected goals not always available at player level — supplemented by FBref if needed

#### GET /injuries

Current injury and suspension list per team.

```
GET /injuries?league=1&season=2026&team=TEAM_ID
```

Fields we extract:
- `player.id`, `player.name`
- `player.type` — `"Missing Fixture"` or `"Questionable"`
- `player.reason` — `"Injured"`, `"Suspended"`, etc.

---

## Transfermarkt

**URL:** `https://www.transfermarkt.com/wettbewerbe/teilnehmer/pokalwettbewerb/WM`  
**Auth:** None (public site, no API key required)  
**Rate limit:** No official limit. We throttle to 1 request/2 seconds and set a real browser User-Agent.  
**Scraping library:** `beautifulsoup4` + `requests`

### What we scrape

From the WC 2026 teams page, we extract for each team:
- Team name (must be mapped to our internal team IDs in `config.py`)
- `data-market-value` attribute on the squad value cell → total squad value in euros

We scrape this once per round update. Values are stored in `data/teams.json` under `squad_value_eur`.

### Important

Transfermarkt occasionally changes their HTML structure. If the scraper breaks after a site update, check `src/value.py` and update the CSS selector. The scrape is non-critical — if it fails, `src/value.py` returns the last known value from `data/teams.json` and logs a warning.

---

## The Odds API

**Base URL:** `https://api.the-odds-api.com/v4`  
**Auth:** `apiKey=YOUR_KEY` query parameter  
**Registration:** [the-odds-api.com](https://the-odds-api.com/) — free tier, no credit card  
**Free limits:** 500 requests/month (we use ~6 per month — one per round)

### Endpoint we use

#### GET /sports/soccer_fifa_world_cup/odds

Tournament winner (outright) odds across multiple bookmakers.

```
GET /sports/soccer_fifa_world_cup/odds?
    apiKey=YOUR_KEY&
    regions=eu&
    markets=outrights&
    oddsFormat=decimal
```

Fields we extract:
- `bookmakers[].markets[].outcomes[]` → for each team: `name` and `price` (decimal odds)

We average the decimal odds across all bookmakers (typically 5–8), then convert to implied probability and normalize. See [`docs/MODEL.md`](MODEL.md#signal-4--betting-market-implied-probability) for the conversion formula.

---

## FBref (optional, Tier 2 players)

**URL:** `https://fbref.com/en/comps/1/stats/World-Cup-Stats`  
**Auth:** None  
**Rate limit:** Aggressive — throttle to 1 request/5 seconds minimum. FBref blocks bots. Use `time.sleep(5)` between requests.  
**Library:** `beautifulsoup4` + `requests` with `pandas.read_html()`

### What we pull

Per-player stats table for the tournament:
- `player`, `team`, `90s` (90-minute equivalents played)
- `xg` (expected goals per player), `xag` (expected assists per player)
- `npxg` (non-penalty xG)

This supplements API-Football player data when player-level xG is not available there. We only call FBref for players flagged as key in `config.py` (`KEY_PLAYER_OVERRIDES` and auto-detected top scorers).

FBref is the most fragile data source. If the scraper fails, the model falls back to API-Football player goal/assist data. This is documented in `src/fetch.py`.

---

## Data freshness policy

| Signal | Freshness required | How we ensure it |
|---|---|---|
| Match results | After each match completes | Manual trigger (`update.py`) |
| xG per fixture | After each match completes | Same call as results |
| Player stats | Once per round | Called in `update.py` per team |
| Injuries | Once per round (before next match) | Called at start of `update.py` |
| Squad values | Once per round | Transfermarkt scrape in `update.py` |
| Betting odds | Once per round | OddsAPI call in `update.py` |

All fetched data is logged with a timestamp in `data/bracket.json` under `_meta.last_updated` so you can verify freshness.

---

## Error handling per source

Every external call is wrapped in a try/except in its respective `src/` module. Failures are logged to stderr and the pipeline continues with the last known good value from the JSON files.

```
API-Football down   → use scores from data/bracket.json (last known)
Transfermarkt down  → use squad_value_eur from data/teams.json (last known)
OddsAPI down        → skip betting signal, redistribute weight to Elo (see config.py FALLBACK_WEIGHTS)
FBref down          → fall back to API-Football player stats
```

This means `update.py` never crashes due to a single source failure. It logs a warning and produces a slightly degraded but still valid prediction.

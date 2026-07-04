# Data sources

Where every signal comes from, what we pull, rate limits, and what happens when something breaks.

**TL;DR:** I run `fetch_public.py` first (Wikipedia, no keys). APIs are optional enrichers. Free tiers mostly don't cover WC 2026 yet.

---

## Quick map

| Source | For | Cost | Keys? | Reality check |
|---|---|---|---|---|
| **Wikipedia** | Group + KO results, fixtures cache | Free | No | Primary. Updated by volunteers, usually fast post-match |
| API-Football | xG, players, injuries, extra fixtures | Free tier | Yes | **2022–2024 seasons only on free.** WC 2026 league often 404/empty |
| Transfermarkt | Squad € | Free scrape | No | Cached in `teams.json`. HTML changes = scrape dies |
| The Odds API | Winner odds | Free tier | Yes | `soccer_fifa_world_cup` market often 422 pre-tournament |
| **`manual_odds.json`** | Winner odds | You paste | No | Fills odds slot when API has no market |
| ClubElo CSV | Base Elo | Free | No | Public download, FIFA rank fallback |
| FBref | Deep player xG (optional) | Free scrape | No | Not wired in main path yet. Fragile |

Keys in `.env` via `python-dotenv`. Never commit `.env`.

---

## Wikipedia (primary)

**Module:** `src/public_fetch.py`  
**CLI:** `python scripts/fetch_public.py`  
**API:** MediaWiki action API on the 2026 World Cup article

### What we pull

- Group stage tables A–L (scores, winners)
- Knockout sections (R32, R16, QF, SF, Final as published)
- Match list → `data/fixtures_cache.json` for form/xG calculations

### What we write

- `data/bracket.json` — scores merged by team pairing against existing structure
- `data/fixtures_cache.json` — all finished matches with goals (xG null unless from API)

### Limits

- No auth, reasonable rate (one page fetch + parse)
- Depends on Wikipedia being up to date. If a result isn't there yet, update `bracket.json` by hand or re-run later

This is the path that actually works during the tournament without paying anyone.

---

## API-Football

**Base:** `https://v3.football.api-sports.io`  
**Auth:** `X-RapidAPI-Key` header  
**Sign up:** [api-football.com](https://www.api-football.com/)  
**Free tier:** 500/day, 30/min, **seasons 2022–2024 only** (dashboard says this explicitly)

### WC 2026 gotcha

League id `1`, season `2026` often returns nothing or errors on free tier. `update.py` falls back to `fixtures_cache.json` + `bracket.json` for results. You still might get injuries/player calls if they add 2026 to your plan later.

### Endpoints we use

**GET /fixtures** — scores, status, penalty shootouts  
**GET /fixtures/statistics** — `expected_goals` when available  
**GET /players** — goals, assists per team  
**GET /injuries** — out / doubtful flags

If the call fails: last cached data, stderr warning, pipeline continues.

---

## Transfermarkt

**Page:** WC teams on transfermarkt.com  
**Auth:** none  
**Rate:** ~2s between requests, real User-Agent

Scrape squad total €. Map names to our ids. Once per round → `squad_value_eur` in `teams.json`.

If HTML changes: `value.py` keeps last known value and warns. Non-fatal.

---

## The Odds API

**Base:** `https://api.the-odds-api.com/v4`  
**Auth:** `apiKey` query param  
**Free:** 500/month

### GET /sports/soccer_fifa_world_cup/odds

Often **422** or empty when books haven't posted outright markets yet. Not a bug in our code.

### Fallback: manual odds

Copy `data/manual_odds.json.example` → `data/manual_odds.json`:

```json
{
  "Brazil": 5.0,
  "France": 6.0
}
```

Team names must match `teams.json`. `odds.py` normalizes across active teams same as API path.

---

## ClubElo

Public CSV from [eloratings.net](https://www.eloratings.net/). Loaded in `elo.py`. National teams without ClubElo entry get FIFA rank proxy. Tournament results still update Elo in `update.py`.

---

## FBref (optional, future)

Player xG/xAG when API-Football is thin. Not in the default v1.2 path. If we add it: 5s+ between requests or they block you.

---

## Freshness

| Signal | When | How |
|---|---|---|
| Results | After matches finish | `fetch_public.py` then `update.py` |
| Fixtures cache | Same | `fetch_public.py` |
| xG per match | When API returns it | `update.py` / API-Football |
| Form (no xG) | Same fixtures | Goals fallback in `xg.py` |
| Player stats | Once per round | API-Football per team |
| Injuries | Start of round | API-Football or static overrides |
| Squad € | Once per round | Transfermarkt scrape |
| Odds | Once per round | Odds API or `manual_odds.json` |

Timestamp in `predictions.json` → `_meta.last_updated` (and bracket meta where set).

---

## When sources fail

Each module catches errors. Pipeline keeps going.

```
Wikipedia stale     → hand-edit bracket.json or wait and re-fetch
API-Football 2026   → fixtures_cache + bracket.json for results/form
Transfermarkt down  → last squad_value_eur
Odds API 422        → skip odds OR use manual_odds.json
Partial xG          → goals fallback + xG coverage shrink in strength.py
```

`strength.py` redistributes missing signal weights **per team**. France doesn't get 33% just because they had xG and Colombia didn't.

`update.py` shouldn't die because one source had a bad day. You get a degraded prediction, warnings on stderr, and `_meta.strength_meta` shows what each team actually used.

# Data sources

Where every signal comes from, what we pull, rate limits, and what happens when something breaks.

---

## Quick map

| Source | For | Cost | Per update | Limit |
|---|---|---|---|---|
| API-Football | Results, xG, players, injuries | Free | ~20 calls | 500/day |
| Transfermarkt | Squad € | Free scrape | 16 teams | throttle yourself |
| The Odds API | Winner odds | Free | 1 call | 500/month |
| FBref | Deep player xG (optional) | Free scrape | ~16 | slow down hard |

Keys in `.env` via `python-dotenv`. Never commit `.env`.

---

## API-Football

**Base:** `https://v3.football.api-sports.io`  
**Auth:** `X-RapidAPI-Key` header  
**Sign up:** [api-football.com](https://www.api-football.com/)  
**Free tier:** 500/day, 30/min  
**WC league id:** `1` (double-check `/leagues` on first run)

### GET /fixtures

```
GET /fixtures?league=1&season=2026&round=Round of 32
```

We grab:
- `fixture.id`, `fixture.date`, `fixture.status.short` (`FT`, `PEN`, `NS`)
- `teams.home/away.id`, `teams.home/away.name`
- `goals.home/away`
- `score.penalty` if pens

### GET /fixtures/statistics

Per finished match:

```
GET /fixtures/statistics?fixture=FIXTURE_ID
```

Look for `type: "expected_goals"`. Also shots on target, possession if we need them.

### GET /players

Per team per round:

```
GET /players?league=1&season=2026&team=TEAM_ID
```

Goals, assists, position. Player xG not always here; FBref backup.

### GET /injuries

```
GET /injuries?league=1&season=2026&team=TEAM_ID
```

Missing / questionable flags, reason (injury, suspension).

---

## Transfermarkt

**Page:** WC teams on transfermarkt.com  
**Auth:** none  
**Rate:** I sleep ~2s between requests, real User-Agent

Scrape squad total € from `data-market-value` on the team row. Map names to our ids in config/`teams.py`.

Once per round → `squad_value_eur` in `teams.json`.

If HTML changes and scrape dies: `value.py` keeps last known value and warns. Non-fatal.

---

## The Odds API

**Base:** `https://api.the-odds-api.com/v4`  
**Auth:** `apiKey` query param  
**Sign up:** [the-odds-api.com](https://the-odds-api.com/)  
**Free:** 500/month (~6 updates for a full knockout run)

### GET /sports/soccer_fifa_world_cup/odds

```
GET /sports/soccer_fifa_world_cup/odds?
    apiKey=YOUR_KEY&
    regions=eu&
    markets=outrights&
    oddsFormat=decimal
```

Average decimal prices across bookmakers, convert to implied prob, normalize. Math in `docs/MODEL.md`.

---

## FBref (optional)

**URL:** World Cup stats on fbref.com  
**Auth:** none  
**Rate:** 5s+ between requests or they block you

Player table: xG, xAG, npxG, minutes. Only for key players when API-Football is thin.

Most fragile source. Fail → fall back to goals/assists from API-Football. Logged in `fetch.py`.

---

## Freshness

| Signal | When | How |
|---|---|---|
| Results + xG | After matches finish | Manual `update.py` |
| Player stats | Once per round | Per-team fetch |
| Injuries | Start of round update | Before next kickoff |
| Squad € | Once per round | Scrape |
| Odds | Once per round | One Odds API call |

Timestamp in `data/bracket.json` → `_meta.last_updated`.

---

## When APIs fail

Each `src/` module catches errors. Pipeline keeps going with last good JSON.

```
API-Football down   → scores from bracket.json
Transfermarkt down  → last squad_value_eur
Odds API down       → skip odds, optional FALLBACK_WEIGHTS in config
FBref down          → API-Football player stats
```

`update.py` shouldn't die because one source had a bad day. You get a degraded prediction and a stderr warning.

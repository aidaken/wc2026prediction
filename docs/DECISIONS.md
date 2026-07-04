# Decisions

Why I built it this way. ADR style: context, choice, what I didn't pick, consequences. I don't edit old entries; if I flip a decision, I add a new ADR.

---

## ADR-001: JSON files, not a database

**Date:** 2026-06-01  
**Status:** Accepted

### Context

Need to store team ratings, bracket, predictions between runs.

### Decision

Three JSON files in `data/`. That's the database.

### Didn't use

| Option | Why not |
|---|---|
| SQLite | Schema, migrations, client. Overkill for three blobs. |
| Supabase / Firebase | Account, keys, network, cost creep. |
| Postgres | lol |

### Why JSON works here

- Tiny data (<100 KB total)
- Write pattern: overwrite whole file once per round
- Human readable, `cat predictions.json` and you're done
- Git history = automatic round-by-round archive
- Zero setup

### Tradeoffs

- One writer only (`update.py`). Fine for me.
- No SQL. Also fine, load all into memory.
- Write to temp file then rename so you don't corrupt mid-save.

---

## ADR-002: Elo as base rating

**Date:** 2026-06-01  
**Status:** Accepted

### Context

Need baseline strength that updates after each match and maps to win probability.

### Decision

Elo, seeded from [World Football Elo](https://www.eloratings.net/), updated in place during the tournament.

### Didn't use

| Option | Why not |
|---|---|
| FIFA ranking points | Not built for head-to-head win % |
| 538 SPI | Can't recompute it ourselves |
| Odds only | Good signal but brand-biased alone |
| Custom ML | Needs data pipeline and maintenance for marginal gain on 7 games |

### Why Elo

Simple math, one update per result, interpretable, proven in football prediction land.

---

## ADR-003: Manual updates

**Date:** 2026-06-01  
**Status:** Accepted

### Context

Pipeline should run after each knockout round. Could automate with cron or Actions.

### Decision

I run `fetch_public.py` then `update.py` by hand when the round is actually done.

### Didn't use

| Option | Why not |
|---|---|
| GitHub Actions cron | Burns API calls while games still playing |
| API-Football webhooks | Paid |
| Nightly auto-run | Round boundaries aren't at midnight |

### Why manual

Knockouts are every few days. I want complete verified results before publishing. One function in `update.py` if I ever wrap it in CI later.

---

## ADR-004: GitHub Pages

**Date:** 2026-06-01  
**Status:** Accepted

### Context

Dashboard needs a public URL.

### Decision

Static `web/index.html` on GitHub Pages from `main`.

### Didn't use

Vercel, Netlify, VPS. All fine products, all extra steps for a single HTML file that fetches JSON.

### Why Pages

Already on GitHub, free forever, rebuilds on push, URL is predictable.

---

## ADR-005: Monte Carlo, not closed-form math

**Date:** 2026-06-01  
**Status:** Accepted

### Context

Turn strengths into tournament win %.

### Decision

10,000 sims.

### Alternative

Multiply path probabilities analytically. Exact but painful with real bracket topology, variable opponents, draw compression. Nested loops nobody wants to maintain.

### Why MC

~0.4pp error at N=10k, runs in under a second, easy to add pen logic later, readable code.

---

## ADR-006: Fixed weights for five signals

**Date:** 2026-06-01  
**Status:** Accepted

### Context

Elo, xG, value, odds, injuries all exist. Need one number per team.

### Decision

Linear blend: Elo 0.35, xG 0.30, value 0.15, odds 0.20. Injury multiplies after.

### Alternatives

Learned weights need labeled history and infra. Equal weights ignore that Elo and xG are stronger signals. Elo-only is simpler but worse mid-tournament.

### Why fixed

Transparent, tunable in `config.py` without touching sim code, good enough for a 7-round sprint. Can optimize later if I care enough.

**v1.2 note:** Nominal weights are 35/30/15/20, but `strength.py` redistributes missing signals per team. UI reads `effective_weights` from `_meta.strength_meta`.

---

## ADR-007: Wikipedia-first results ingestion

**Date:** 2026-07-01  
**Status:** Accepted

### Context

API-Football free tier doesn't serve WC 2026 season. Odds API often has no outright market. I still need fresh scores and fixture history for form and Elo.

### Decision

`scripts/fetch_public.py` scrapes the Wikipedia 2026 World Cup page via MediaWiki API, updates `bracket.json` and `fixtures_cache.json`. Run before every `update.py`.

### Didn't use

| Option | Why not |
|---|---|
| Paid API-Football only | Cost + still want offline reproducibility |
| Manual bracket edits only | Too slow every match day, error-prone |
| FIFA official API | No public free API for live WC data |

### Why Wikipedia

Free, no keys, humans update it fast during the tournament, structured enough to parse. We already had bracket topology in JSON; Wikipedia fills scores and builds fixture history.

### Tradeoffs

- Parser breaks if Wikipedia reformats tables (fix and re-run)
- No match xG from Wikipedia (goals fallback + optional API-Football)
- Trust but verify weird scores against another source if something looks off

---

## ADR-008: Opponent-adjusted xG form

**Date:** 2026-07-03  
**Status:** Accepted

### Context

xG form was raw. A team that put up big xG numbers against a weak group looked the same as one that did it against real teams. Argentina (Algeria, Austria, Jordan, Cape Verde) and Canada (Bosnia, Qatar) were flattered, teams with tough draws were underrated. Elo already rewards beating strong sides, but the xG signal (0.30 weight) was schedule-blind.

### Decision

Rescale each team's xG by the quality of the opponents it actually played, using the opponents' own xG profiles:

- xG-for × (league avg xGA / opponents' avg xGA). Faced stingy defenses → boosted.
- xG-against × (league avg xG / opponents' avg xG). Faced strong attacks → forgiven.

Multipliers clamped 0.70–1.35 (`XG_ADJ_CLAMP_LO/HI`) so a small sample can't swing form. Toggle with `XG_OPPONENT_ADJUST`. Opponent list comes from completed group + knockout matches (`build_opponent_map`).

### Didn't use

| Option | Why not |
|---|---|
| Iterated ratings (solve for attack/defense strength) | More correct, but circular and heavy for 3–4 games per team |
| Just trust Elo for opponent quality | Leaves the xG signal naive, which was the whole complaint |
| Nothing (raw xG) | Rewards padding stats against weak teams |

### Why this

One pass, self-contained (uses the xG we already have), easy to read and clamp. Direction is right without pretending we have season-long data. Good enough for a 7-round run.

### Tradeoffs

- One-pass, not iterated, so opponent quality is measured from raw xG including the game against this team (minor circularity, fine at this scale)
- Clamps hide extreme schedules a bit on purpose
- Reads best with full xG coverage; sparse coverage makes the league average noisy

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

I run `python update.py` by hand when the round is actually done.

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

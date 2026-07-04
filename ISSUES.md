# Issues & gotchas

Running list of stuff that broke, why it broke, and how I worked around it. Read this before you touch the data pipeline or wonder why some numbers are typed in by hand instead of fetched. If you hit a new one, add it here so the next person (or the next me) doesn't rediscover it the hard way.

Status tags: **fixed** (done, won't recur), **workaround** (living with it, needs manual love each round), **open** (not done yet).

---

## Data sources: the whole reason half this thing is manual

The short version: almost none of the free APIs actually serve WC 2026 data. I found this out one endpoint at a time. So the model runs on Wikipedia for results plus a few files I paste by hand. Not elegant, but it's honest and it works.

### API-Football free tier has no 2026 World Cup — **workaround**
Free tier just doesn't return the 2026 season. So scores, fixtures, xG, injuries from there are all empty during the tournament.
- Workaround: `scripts/fetch_public.py` scrapes Wikipedia (MediaWiki API) for group + knockout results into `bracket.json` and `fixtures_cache.json`. Run it before `update.py` every round.
- If you ever get a paid key, the code still reads API-Football when it's available, it just doesn't depend on it.

### Odds API returns 422 for the WC winner market — **workaround**
The outright/winner market for the World Cup isn't there most of the time (422 or empty).
- Workaround: paste implied probabilities into `data/manual_odds.json`. Format is 3-letter team id → implied prob (not decimal odds, not full names). See `docs/SETUP.md`.
- Gotcha I already hit: the docs used to show the wrong format (decimal odds + full country names). Fixed, but double check the example if odds look weird.

### Transfermarkt squad-value scrape is dead (404) — **workaround**
The scrape URL 404s now, page structure changed.
- Workaround: `data/squad_values.json` holds pinned values for all 48 teams, pulled from web search. `value.py` prefers scrape → pinned → cached, so if the scrape ever comes back it wins automatically.
- These go stale. Refresh the active teams' numbers if a transfer window blew up any squad.

### FotMob xG is token-locked and the page is JS-rendered — **workaround**
Their API wants a token and the public page renders xG in JavaScript, so a plain fetch gets 404 or empty HTML. Same story with most xG sites.
- Workaround: paste per-team xG into `data/manual_xg.json` (`{"TID": {"xg", "xga", "mp"}}`). I built it from the FotMob xG table (group totals) plus xgscore.io per-match for the R32 games.
- This overrides the goals fallback so every team runs on real xG instead of a proxy.

---

## Model bugs I already fixed

### Elo was double-counting and resetting weird — **fixed**
Incremental in-place Elo updates meant re-running `update.py` in the same round could count a match twice, and ratings weren't reproducible.
- Fix: `recompute_from_seed` in `src/elo.py` replays the whole tournament from the pre-tournament seed every run (group stage, then each knockout round). Deterministic, no double count. Run it as many times as you want, same answer.

### `elo_change_this_round` was per-run, not per-round — **fixed**
Teams that won earlier in a round showed a 0 delta because the number reset each run.
- Fix: the replay gives an exact per-round delta for every team (each knockout team plays one match per round). UI reads the real number now.

### xG form ignored who you played — **fixed**
This was the big one. Form was raw xG, so 8 xG against Qatar counted the same as 8 against Brazil. Argentina and Canada looked elite off soft groups.
- Fix: strength-of-schedule adjustment in `src/xg.py` (`XG_OPPONENT_ADJUST`). Scales xG-for up when you faced stingy defenses and forgives xG-against when you faced strong attacks, using the opponents' own xG profiles. Clamped 0.70–1.35 so a tiny sample can't swing it.
- Effect: Argentina and France nudge down, England (tough run) and Paraguay (brutal group) nudge up. See ADR-008.

### Only 6 of 17 teams had xG, rest were on the goals proxy — **fixed**
Coverage was thin so most teams used goals-as-xG.
- Fix: `manual_xg.json` covers all 17 active teams (17/17 coverage now), so the shrink-toward-neutral barely kicks in.

---

## Stuff to remember every round (so it doesn't bite again)

- Run `fetch_public.py` **before** `update.py`. Order matters, form and Elo read the fixtures the fetch writes.
- After each round, update `data/manual_xg.json`: add the new knockout game to each surviving team and bump their `mp`. The xG override ignores any match you don't put in the file.
- Update `data/manual_odds.json` when the market moves. Stale odds quietly drag a team up or down.
- Commit the `data/*.json` after every run. GitHub Pages serves straight from the repo, so if you don't commit, the site shows old numbers.
- The opponent map assumes any two teams meet at most once (true for a World Cup). If the format ever changes, that dedup logic in `build_opponent_map` needs a rethink.

---

## Open

### Colombia and Ghana R32 xG missing — **open**
Their round of 32 game hadn't been played when I built `manual_xg.json`, so they're on group-only xG (`mp: 3`). Once they play, drop the two xG lines in, bump `mp` to 4, and re-run. Everyone else is on 4 matches.

### Manual data is manual — **open**
Squad values, odds, and xG are all typed in by hand right now because the sources are locked. If any of those APIs open up for 2026, wire them back in and delete the manual step. Until then, this is the deal.

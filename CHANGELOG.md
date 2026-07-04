# Changelog

All notable changes to this project. Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

---

## [1.2.2] - 2026-07-03

### Added
- `ISSUES.md`: running log of known issues, source failures, and per-round reminders so they don't recur
- Opponent-adjusted xG form (`XG_OPPONENT_ADJUST`): rescales xG by schedule strength using opponents' own xG profiles, clamped 0.70–1.35. New `build_opponent_map` in `src/xg.py`
- `data/manual_xg.json`: per-team xG for all 17 active teams (FotMob group totals + xgscore R32), so coverage is 17/17
- `sos_multiplier`, `adj_xg_for`, `adj_xg_against` in signals; UI shows schedule strength + adjusted xG per team
- ADR-008 for the opponent adjustment

### Changed
- xG form is no longer schedule-blind. Argentina 15.5% → 14.4% and France 25.3% → 24.3% (soft draws), England 9.9% → 10.7% (tough run)
- Fixed the wrong `manual_odds` example in README and setup docs (3-letter ids + implied probs, not decimal odds)

---

## [1.2.1] - 2026-07-03

### Added
- `data/squad_values.json`: pinned Transfermarkt WC 2026 squad values for all 48 teams (scrape URL is dead). `value.py` prefers scrape → pinned → cached
- `avg_xg_for` / `avg_xg_against` surfaced per team in `predictions.json` signals and shown in the UI detail panel

### Changed
- **Elo is now deterministic:** full replay from pre-tournament seed each run (group stage → each knockout round) instead of incremental in-place updates. Kills the double-count risk and makes ratings reproducible
- `elo_change_this_round` is now a correct **per-round** delta for every team (was per-run, so teams that won earlier in a round wrongly showed 0)
- `N_SIMULATIONS` 10k → 100k (~±0.13pp sampling noise vs ~±0.4pp)
- Squad values corrected to real figures (France €1.52B, Brazil €0.93B, etc.), shifting win %: France 24.5%, Brazil 15.3%, Argentina 13.8%
- `teams.json` `_meta` drops the long `elo_processed_matches` list for `elo_method: full_replay_from_seed`

---

## [1.2.0] - 2026-07-01

### Added
- `scripts/fetch_public.py` + `src/public_fetch.py`: Wikipedia MediaWiki API scrape for group and knockout results (no API keys)
- `data/fixtures_cache.json`: persisted fixtures for form/xG when APIs can't serve 2026
- `data/manual_odds.json.example`: optional manual betting odds when Odds API has no WC market
- `predictions.json` `_meta`: `weights`, `strength_scale`, `data_sources`, `strength_meta` (per-team effective weights)
- Goals-based form fallback in `src/xg.py` when match xG missing
- Per-team signal weight redistribution in `src/strength.py` when odds/form/value absent
- xG coverage shrink so partial xG data doesn't dominate the field

### Changed
- `STRENGTH_SCALE` default **0.68** (from `backtest.py --sweep`, was 0.50)
- `merge_fixtures()` keeps seed group matches without `match_id`
- `update.py` loads `manual_odds.json` when Odds API unavailable
- Web UI: reads real weights from `_meta`, expandable team breakdown, tiered list, watermarks
- Docs rewritten for Wikipedia-first workflow and API free-tier limits

### Fixed
- Safari crash: `const rows +=` → `let rows` in signal breakdown renderer
- UI strength formula mismatch when odds missing (now uses `effective_weights` per team)

---

## [1.1.0] - 2026-06

### Added
- `STRENGTH_SCALE` separate from `ELO_SCALE` (fixes ~50/50 knockout coin flips)
- Dynamic key player detection for injury signal
- `scripts/backtest.py`: Brier score, `--sweep`, `--sensitivity`
- Bracket topology (`bracket_topology.py`) + per-match advancement % in UI
- `docs/BRACKET_PREDICTIONS.md`

### Changed
- Monte Carlo uses feeder graph, not naive sequential pairing
- Elo dedup + betting normalization in `update.py`

---

## [1.0.0] - 2026-05

Initial public release: five-signal strength model, Monte Carlo bracket, GitHub Pages UI.

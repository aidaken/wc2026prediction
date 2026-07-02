# Changelog

All notable changes to this project. Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

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

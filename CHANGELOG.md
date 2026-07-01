# Changelog

All notable changes to this project are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).  
Versioning follows `MAJOR.MINOR.PATCH` — patch for prediction updates, minor for new signals or model changes, major for architecture changes.

---

## [Unreleased]

### Added
- Team registry (`src/teams.py`) for API name/ID → internal code mapping
- Bracket sync module — merges API results, marks eliminations, auto-detects round
- Unit tests (`tests/test_engine.py`) and CI workflow with GitHub Pages deploy
- Backtest script (`scripts/backtest.py`) with Brier score support
- Dashboard history panel and full team names in bracket view

### Fixed
- Centralize team name mappings in `src/teams.py`; remove stale Odds/Transfermarkt maps
- Delete outdated `data/history/round_16.json` snapshot from pre-2026 seed data
- Round of 32 bracket matches FIFA combination 67 with real results through July 1
- Predictions sorted with active teams first, group-stage eliminated at bottom
- Live mode now merges bracket fixture history for Elo/xG calculations
- Penalty shootout winner detection
- Player stats proxy for injury model in live mode

---

## [1.0.0] — 2026-06-30

Initial project scaffold and documentation.

---

## Upcoming round updates

### Round of 16 — expected 2026-07-04 to 2026-07-07
### Quarter-finals — expected 2026-07-10 to 2026-07-11
### Semi-finals — expected 2026-07-14 to 2026-07-15
### Final — 2026-07-19

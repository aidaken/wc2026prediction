# Changelog

What shipped and when. Patch = prediction refresh. Minor = model or features. Major = big structural change.

---

## [Unreleased]

### Added
- Per-match advance % on the bracket (`match_predictions`)
- `bracket_topology.py` for the real WC feeder tree
- `STRENGTH_SCALE` (v1.1), backtest script with Brier + sweep
- Auto key-player detection in `injury.py`
- Athletic-style bracket UI (flags, advance %)
- `docs/VOICE.md`

### Fixed
- Sim paired R32 winners sequentially instead of following the real tree
- Elo stacked on every `update.py` run (deduped via `elo_processed_matches` now)
- Betting odds not normalized across active teams
- Wrong teams/bracket (now combination 67 + real R32)
- GitHub Pages 404 without `/web/` redirect

### Changed
- Model version 1.1.0
- `DRAW_PROBABILITY` 0.25 → 0.27
- Comments and docs voice pass

---

## [1.0.0] — 2026-06-30

First version. Ingestion, engine, dashboard, docs.

---

## Round updates (manual log)

| Round | Dates |
|---|---|
| Round of 16 | 2026-07-04 – 07-07 |
| Quarter-finals | 2026-07-10 – 07-11 |
| Semi-finals | 2026-07-14 – 07-15 |
| Final | 2026-07-19 |

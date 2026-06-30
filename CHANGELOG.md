# Changelog

All notable changes to this project are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).  
Versioning follows `MAJOR.MINOR.PATCH` — patch for prediction updates, minor for new signals or model changes, major for architecture changes.

---

## [Unreleased]

---

## [1.0.0] — 2026-06-30

### Added
- Initial project setup
- API-Football integration: fixtures, xG, player stats, injuries
- Transfermarkt squad value scraper
- The Odds API betting probability integration
- Elo rating system seeded from World Football Elo Ratings
- xG form ratio calculation (last 5 games, WC games weighted 2×)
- Injury multiplier based on player xG/xA importance scores
- Monte Carlo simulation engine (10,000 runs)
- Five-signal weighted combination formula
- `data/teams.json`, `data/bracket.json`, `data/predictions.json` schemas
- Static HTML/JS dashboard in `web/index.html`
- GitHub Pages deployment
- Full documentation: MODEL.md, DATA_SOURCES.md, DATA_PIPELINE.md, SETUP.md, DECISIONS.md

### Predictions — Round of 32

Updated: 2026-06-30

Top 5 win probabilities after Round of 32 group stage completion:

| Team | Win % |
|---|---|
| Brazil | 18.4% |
| France | 12.1% |
| Spain | 11.8% |
| Argentina | 9.7% |
| England | 8.3% |

Eliminated after Round of 32: Germany, Netherlands, Japan, South Africa

---

## Upcoming round updates

### Round of 16 — expected 2026-07-04 to 2026-07-07
### Quarter-finals — expected 2026-07-10 to 2026-07-11
### Semi-finals — expected 2026-07-14 to 2026-07-15
### Final — 2026-07-19

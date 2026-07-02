# Contributing

Small repo on purpose. If you want to poke at it, here's the map.

---

## Read first

1. [ARCHITECTURE.md](ARCHITECTURE.md) — where things live
2. [docs/DATA_PIPELINE.md](docs/DATA_PIPELINE.md) — fetch_public → update flow
3. [docs/MODEL.md](docs/MODEL.md) — if you're touching the engine
4. [docs/VOICE.md](docs/VOICE.md) — how commits and comments should sound

---

## Setup

```bash
git clone https://github.com/aidaken/wc2026prediction.git
cd wc2026prediction
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional api keys
./scripts/install-git-hooks.sh   # optional, keeps commit messages clean
```

Full walkthrough: [docs/SETUP.md](docs/SETUP.md).

---

## Run it

```bash
python scripts/fetch_public.py  # wikipedia, no keys
python update.py --demo         # cached data, no keys
python update.py                # full pipeline (+ apis if keyed)
python -m pytest tests/
python scripts/backtest.py      # brier on finished knockouts
python scripts/backtest.py --sweep   # tune STRENGTH_SCALE
```

---

## What to edit for what

| Goal | Files |
|---|---|
| Public results ingest | `src/public_fetch.py`, `scripts/fetch_public.py` |
| New API source | `src/fetch.py` or new module + `update.py` |
| Manual odds format | `data/manual_odds.json.example`, `src/odds.py` |
| Model weights | `config.py`, `docs/MODEL.md` |
| Per-team weight logic | `src/strength.py` |
| Form / xG fallback | `src/xg.py` |
| Bracket pairing | `bracket_topology.py`, `data/bracket.json` |
| Dashboard | `web/index.html` |
| Pipeline order | `update.py` |

Don't let `src/` modules import each other in circles. `update.py` is the glue.

---

## Commits

Conventional commits. Lowercase type, sentence-case subject. One-line why if it's not obvious.

```
fix(simulate): use real feeder tree not sequential winners

brazil and france are opposite sides but sim was pairing r32 winners 1v2
```

Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `data`.

Never commit `.env` or keys.

Run `./scripts/install-git-hooks.sh` after clone if you want the commit message hook.

---

## PRs

1. Branch from `main`
2. Keep the diff focused
3. Update docs if behavior changed (especially `DATA_PIPELINE.md` and `DATA_SOURCES.md`)
4. If you change weights or `STRENGTH_SCALE`, run `backtest.py` and note Brier in the PR
5. Say what you changed and how you tested

---

## Post-round update (me)

```bash
python scripts/fetch_public.py
python update.py
git add data/bracket.json data/fixtures_cache.json data/predictions.json data/teams.json
git commit -m "data: post-round-N results"
git push
```

Site updates on its own.

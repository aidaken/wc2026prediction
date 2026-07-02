# Contributing

Small repo on purpose. If you want to poke at it, here's the map.

---

## Read first

1. [ARCHITECTURE.md](ARCHITECTURE.md) — where things live
2. [docs/MODEL.md](docs/MODEL.md) — if you're touching the engine
3. [docs/VOICE.md](docs/VOICE.md) — how commits and comments should sound

---

## Setup

```bash
git clone https://github.com/aidaken/wc2026prediction.git
cd wc2026prediction
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # drop your api keys in here
./scripts/install-git-hooks.sh   # optional, keeps commit messages clean
```

Full walkthrough: [docs/SETUP.md](docs/SETUP.md).

---

## Run it

```bash
python update.py --demo    # no keys needed
python update.py           # real data
python -m pytest tests/
python scripts/backtest.py # brier on finished knockouts
```

---

## What to edit for what

| Goal | Files |
|---|---|
| New data source | `src/fetch.py` or new module + `update.py` |
| Model weights | `config.py`, `docs/MODEL.md` |
| Bracket pairing | `bracket_topology.py`, `data/bracket.json` |
| Dashboard | `web/index.html` |
| Pipeline order | `update.py` |

Don't let `src/` modules import each other. `update.py` is the glue.

---

## Commits

Conventional commits. Lowercase type, sentence-case subject. One-line why if it's not obvious.

```
fix(simulate): use real feeder tree not sequential winners

brazil and france are opposite sides but sim was pairing r32 winners 1v2
```

Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`.

Never commit `.env` or keys.

Run `./scripts/install-git-hooks.sh` after clone if you want the commit message hook.

---

## PRs

1. Branch from `main`
2. Keep the diff focused
3. Update docs if behavior changed
4. Say what you changed and how you tested

---

## Post-round update (me)

```bash
python update.py
git add data/predictions.json data/bracket.json data/teams.json
git commit -m "chore: update predictions after quarter-finals"
git push
```

Site updates on its own.

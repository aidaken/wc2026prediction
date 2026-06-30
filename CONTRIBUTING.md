# Contributing

Thanks for looking at this. Here is everything you need to know to contribute to `wc2026prediction`.

---

## Getting started

1. Fork the repo and clone your fork
2. Follow the setup in [`docs/SETUP.md`](docs/SETUP.md) to get the project running locally
3. Create a branch for your change: `git checkout -b feat/your-feature-name`
4. Make your changes, test them, then open a pull request

---

## Code style

- **Python:** Follow [PEP 8](https://peps.python.org/pep-0008/). Use `black` for auto-formatting (`pip install black`, then `black .`)
- **Type hints:** All functions in `src/` must have type hints on arguments and return values
- **Docstrings:** Every public function needs a one-line docstring. Explain *what* it does, not *how*.
- **No magic numbers:** Any numeric constant (K-factor, weight, threshold) belongs in `config.py` with a clear name, not hardcoded inside a function

Example of expected style:

```python
def calculate_xg_form_ratio(fixtures: list[dict], team_id: str, n_games: int = 5) -> float:
    """Return xG form ratio for a team over their last n_games matches."""
    recent = [f for f in fixtures if team_id in (f["team_home"], f["team_away"])][-n_games:]
    if not recent:
        return 0.5  # neutral fallback
    xg_for = sum(f["xg_home"] if f["team_home"] == team_id else f["xg_away"] for f in recent)
    xg_against = sum(f["xg_away"] if f["team_home"] == team_id else f["xg_home"] for f in recent)
    return xg_for / (xg_for + xg_against) if (xg_for + xg_against) > 0 else 0.5
```

---

## How to add a new data signal

1. Create `src/your_signal.py`
2. Implement a function with this signature:
   ```python
   def get_signal(team_ids: list[str]) -> dict[str, float]:
       """Return signal values normalized to [0, 1] for each team."""
       ...
   ```
3. Add a weight to `WEIGHTS` in `config.py` (and adjust other weights so they still sum to 1.0)
4. Add a `FALLBACK_WEIGHTS` entry in `config.py` for when the source is unavailable
5. Add the call in `update.py` between the fetch and calculate steps
6. Add the signal to the `signals` field in `data/predictions.json` output (see schema in [`docs/DATA_PIPELINE.md`](docs/DATA_PIPELINE.md))
7. Document the source in [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md)
8. Document the signal logic in [`docs/MODEL.md`](docs/MODEL.md)

---

## How to tune model weights

Weights live in `config.py`:

```python
WEIGHTS = {
    "elo": 0.35,
    "xg_form": 0.30,
    "squad_value": 0.15,
    "betting_odds": 0.20,
}
```

Rules:
- Weights must sum to exactly 1.0
- The `injury_multiplier` is multiplicative and not part of the sum
- Document your reasoning in a comment next to the weight you changed

To evaluate whether a change improves accuracy, compare the model's predicted probabilities against actual outcomes using Brier score (lower is better):

```
Brier score = (1/N) × Σ (predicted_probability - actual_outcome)²
```

Where `actual_outcome` is 1 if the team won, 0 otherwise.

---

## Commit message format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add FBref player xG scraper
fix: handle Transfermarkt HTML structure change
chore: update Round of 16 predictions
docs: add squad value normalization formula
refactor: extract win_probability into separate function
```

Types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`

---

## Pull request checklist

Before opening a PR:

- [ ] Code follows PEP 8 and passes `black` formatting
- [ ] All functions have type hints and docstrings
- [ ] Any new constants are in `config.py`, not hardcoded
- [ ] Any new data source is documented in `docs/DATA_SOURCES.md`
- [ ] Any model change is documented in `docs/MODEL.md`
- [ ] `python update.py` runs without errors locally
- [ ] CHANGELOG.md is updated under `Unreleased`

---

## Reporting issues

Open a GitHub issue with:
- What you expected to happen
- What actually happened
- The full error output (from `update.py` or the browser console)
- Your Python version (`python --version`)
- The round and date you ran the update

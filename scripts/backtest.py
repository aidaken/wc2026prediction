#!/usr/bin/env python3
"""
see how well the model called completed matches (brier score, lower = better).

  python scripts/backtest.py
  python scripts/backtest.py --sweep
  python scripts/backtest.py --scale 0.4
  python scripts/backtest.py --sensitivity

rough guide: under 0.20 is solid, 0.25 is coin-flip baseline.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

try:
    import config
except ModuleNotFoundError:
    sys.exit("Could not import config.py. Run this script from the project root or scripts/ directory.")


def load_teams() -> dict:
    path = ROOT / "data" / "teams.json"
    if not path.exists():
        sys.exit("data/teams.json not found. Run: python update.py")
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data.get("teams", {})


def load_bracket() -> dict:
    path = ROOT / "data" / "bracket.json"
    if not path.exists():
        sys.exit("data/bracket.json not found. Run: python update.py")
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data.get("rounds", {})


def get_completed_matches(rounds: dict) -> list[dict]:
    completed = []
    for round_key, round_data in rounds.items():
        for match in round_data.get("matches", []):
            if match.get("status") in ("FT", "PEN", "AET") and match.get("winner"):
                completed.append({**match, "_round": round_key})
    return completed


def win_probability(strength_a: float, strength_b: float, scale: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((strength_b - strength_a) / scale))


def _team_strength(team: dict) -> float | None:
    if team.get("team_strength") is not None:
        return float(team["team_strength"])
    elo = team.get("elo")
    if elo is None:
        return None
    # eliminated teams might not have team_strength saved yet, rough elo fallback
    return max(0.15, min(0.85, (float(elo) - 1400.0) / 700.0))


def evaluate(
    matches: list[dict],
    teams: dict,
    scale: float,
) -> tuple[float | None, list[dict]]:
    squared_errors: list[float] = []
    details: list[dict] = []

    for match in matches:
        home_id = match.get("team_home")
        away_id = match.get("team_away")
        winner_id = match.get("winner")

        home = teams.get(home_id, {})
        away = teams.get(away_id, {})

        strength_home = _team_strength(home)
        strength_away = _team_strength(away)

        if strength_home is None or strength_away is None:
            continue

        prob_home_wins = win_probability(strength_home, strength_away, scale)
        actual = 1.0 if winner_id == home_id else 0.0
        error = (prob_home_wins - actual) ** 2

        squared_errors.append(error)
        details.append({
            "round": match["_round"].replace("_", " ").title(),
            "home": home.get("name", home_id),
            "away": away.get("name", away_id),
            "strength_home": round(strength_home, 3),
            "strength_away": round(strength_away, 3),
            "prob_home_wins": round(prob_home_wins, 3),
            "actual_winner": "home" if winner_id == home_id else "away",
            "model_correct": (prob_home_wins > 0.5) == (winner_id == home_id),
            "brier_error": round(error, 4),
        })

    if not squared_errors:
        return None, []

    return sum(squared_errors) / len(squared_errors), details


def sweep_scales(
    matches: list[dict],
    teams: dict,
    low: float = 0.10,
    high: float = 1.50,
    n_steps: int = 29,
) -> list[tuple[float, float]]:
    results = []
    step = (high - low) / n_steps

    scale = low
    while scale <= high + 1e-9:
        score, _ = evaluate(matches, teams, round(scale, 2))
        if score is not None:
            results.append((round(scale, 2), round(score, 5)))
        scale += step

    return sorted(results, key=lambda x: x[1])


def sensitivity_check(matches: list[dict], teams: dict) -> None:
    print(f"\n{'─' * 55}")
    print("  Sensitivity check — injury floor & draw probability")
    print(f"{'─' * 55}")

    base_score, _ = evaluate(matches, teams, config.STRENGTH_SCALE)
    if base_score is None:
        print("  No strength data. Run update.py first.")
        return

    tweaks = [
        ("MIN_INJURY_MULTIPLIER", config.MIN_INJURY_MULTIPLIER, [-0.05, +0.05]),
        ("DRAW_PROBABILITY", config.DRAW_PROBABILITY, [-0.05, +0.05]),
    ]

    print(f"  Base Brier score: {base_score:.5f}  (STRENGTH_SCALE={config.STRENGTH_SCALE})")
    print()

    for param_name, base_val, deltas in tweaks:
        print(f"  {param_name} (current: {base_val})")
        for delta in deltas:
            new_val = base_val + delta
            direction = (
                "looser floor → weaker teams gain" if delta > 0 and "INJURY" in param_name
                else "stricter floor → larger injury penalties" if delta < 0 and "INJURY" in param_name
                else "more draws → upsets more likely" if delta > 0
                else "fewer draws → strength matters more"
            )
            print(f"    {base_val:.2f} → {new_val:.2f}  ({direction})")
            print(f"    To quantify: set {param_name} = {new_val:.2f} in config.py, run update.py + backtest.py")
        print()

    print("  Rule of thumb: if changing a parameter by 10% shifts your top")
    print("  team's win% by more than 3pp, it deserves a cited source.")
    print("  If it barely moves (< 1pp), the round number is fine to keep.\n")


def print_match_results(details: list[dict], score: float, scale: float) -> None:
    print(f"\n{'─' * 65}")
    print(f"  Backtest — STRENGTH_SCALE = {scale}")
    print(f"{'─' * 65}")
    print(f"  Matches evaluated : {len(details)}")
    print(f"  Brier score       : {score:.4f}  (random baseline = 0.2500)")

    n_correct = sum(1 for d in details if d["model_correct"])
    print(f"  Directional acc.  : {n_correct}/{len(details)} = {n_correct / len(details) * 100:.0f}%")

    by_round: dict[str, list[dict]] = {}
    for d in details:
        by_round.setdefault(d["round"], []).append(d)

    for round_name, round_matches in by_round.items():
        print(f"\n  {round_name}")
        for d in round_matches:
            flag = "✓" if d["model_correct"] else "✗"
            print(
                f"    {flag}  {d['home']:<22} vs {d['away']:<22}  "
                f"model: {d['prob_home_wins']:.0%} home  "
                f"actual: {d['actual_winner']} won  "
                f"[err={d['brier_error']:.4f}]"
            )
    print()


def print_sweep_results(results: list[tuple[float, float]]) -> None:
    print(f"\n{'─' * 50}")
    print("  STRENGTH_SCALE sweep results")
    print(f"{'─' * 50}")
    print(f"  {'Scale':>8}  {'Brier Score':>12}  {'vs Baseline':>12}")
    print(f"  {'─' * 8}  {'─' * 12}  {'─' * 12}")

    for i, (scale, score) in enumerate(results[:15]):
        delta = score - 0.25
        flag = " ← best" if i == 0 else ""
        print(f"  {scale:>8.2f}  {score:>12.5f}  {delta:>+11.5f}{flag}")

    best_scale = results[0][0]
    best_score = results[0][1]
    current_score = next((s for sc, s in results if sc == config.STRENGTH_SCALE), None)

    print(f"\n  Best STRENGTH_SCALE  : {best_scale}")
    print(f"  Best Brier score     : {best_score:.5f}")
    if current_score is not None:
        improvement = current_score - best_score
        print(f"  Current ({config.STRENGTH_SCALE}) score : {current_score:.5f}  (improvement: {improvement:+.5f})")

    print(f"\n  → Set STRENGTH_SCALE = {best_scale} in config.py")
    print("    Then re-run: python update.py && python scripts/backtest.py\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backtest STRENGTH_SCALE against completed WC 2026 matches.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--scale", type=float, default=None,
        help="Test a specific STRENGTH_SCALE value (default: value from config.py)",
    )
    parser.add_argument(
        "--sweep", action="store_true",
        help="Sweep STRENGTH_SCALE from 0.10 to 1.50 and rank by Brier score",
    )
    parser.add_argument(
        "--sensitivity", action="store_true",
        help="Show sensitivity analysis for injury floor and draw probability",
    )
    args = parser.parse_args()

    os.chdir(ROOT)

    teams = load_teams()
    rounds = load_bracket()
    matches = get_completed_matches(rounds)

    if not matches:
        print("No completed matches found in data/bracket.json.")
        print("Wait until Round of 32 finishes and run update.py first.")
        sys.exit(0)

    print(f"Loaded {len(matches)} completed match(es) from bracket.json.")

    if args.sensitivity:
        sensitivity_check(matches, teams)
        return

    if args.sweep:
        results = sweep_scales(matches, teams)
        if not results:
            print("No team_strength values found. Run update.py first.")
            sys.exit(1)
        print_sweep_results(results)
        return

    scale = args.scale if args.scale is not None else config.STRENGTH_SCALE
    score, details = evaluate(matches, teams, scale)

    if score is None:
        print("\nNo team_strength values in data/teams.json yet.")
        print("Run python update.py first, then re-run this script.")
        sys.exit(1)

    print_match_results(details, score, scale)

    if args.scale is None:
        print("  Tip: run with --sweep to find the optimal STRENGTH_SCALE value.")
        print("  Tip: run with --sensitivity to check injury/draw parameter impact.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Backtest utility — compare historical prediction snapshots."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
HISTORY_DIR = DATA_DIR / "history"


def load_predictions(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def brier_score(predictions: list[dict], actual_winner: str | None) -> float | None:
    if not actual_winner:
        return None
    score = 0.0
    for p in predictions:
        prob = p["win_probability"] if not p.get("eliminated") else 0.0
        outcome = 1.0 if p["team_id"] == actual_winner else 0.0
        score += (prob - outcome) ** 2
    return score / len(predictions)


def main() -> None:
    parser = argparse.ArgumentParser(description="Backtest prediction snapshots")
    parser.add_argument("--winner", type=str, help="Actual tournament winner team ID (e.g. BRA)")
    parser.add_argument("--file", type=str, default="predictions.json", help="Snapshot file in data/ or history/")
    args = parser.parse_args()

    path = DATA_DIR / args.file
    if not path.exists():
        path = HISTORY_DIR / args.file
    if not path.exists():
        raise SystemExit(f"File not found: {args.file}")

    data = load_predictions(path)
    preds = data.get("predictions", [])
    meta = data.get("_meta", {})

    print(f"Snapshot: {path.name}")
    print(f"Round: {meta.get('round', '—')}")
    print(f"Generated: {meta.get('generated_at', '—')}")
    print()
    print("Top 5 predictions:")
    active = [p for p in preds if not p.get("eliminated")][:5]
    for i, p in enumerate(active, 1):
        print(f"  {i}. {p['team_name']:<16} {p['win_probability'] * 100:5.1f}%")

    if args.winner:
        score = brier_score(preds, args.winner)
        if score is not None:
            print(f"\nBrier score vs winner {args.winner}: {score:.4f}")


if __name__ == "__main__":
    main()

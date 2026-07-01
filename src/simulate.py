"""Monte Carlo tournament simulation engine."""

from __future__ import annotations

import random
from copy import deepcopy
from typing import Any

import config
from src.utils import win_probability

ROUND_ORDER = [
    "round_of_32",
    "round_of_16",
    "quarter_finals",
    "semi_finals",
    "final",
]

# Composite strength is on [0, 1]; map to Elo-like scale for match win formula.
STRENGTH_FLOOR = 1400.0
STRENGTH_CEILING = 2100.0


def _to_match_rating(strength: float) -> float:
    return STRENGTH_FLOOR + strength * (STRENGTH_CEILING - STRENGTH_FLOOR)


def _simulate_match(
    team_a: str,
    team_b: str,
    strengths: dict[str, float],
    rng: random.Random,
) -> str:
    sa = _to_match_rating(strengths.get(team_a, 0.5))
    sb = _to_match_rating(strengths.get(team_b, 0.5))
    prob_a = win_probability(sa, sb)

    if rng.random() < config.DRAW_PROBABILITY:
        prob_a = 0.5 + (prob_a - 0.5) * 0.6

    return team_a if rng.random() < prob_a else team_b


def _resolve_round(
    matches: list[dict[str, Any]],
    strengths: dict[str, float],
    rng: random.Random,
) -> list[str]:
    winners: list[str] = []
    for match in matches:
        home = match.get("team_home")
        away = match.get("team_away")
        if not home or not away:
            continue

        existing = match.get("winner")
        if existing:
            winners.append(existing)
            continue

        winner = _simulate_match(home, away, strengths, rng)
        winners.append(winner)
    return winners


def _advance_bracket(
    bracket: dict[str, Any],
    strengths: dict[str, float],
    rng: random.Random,
) -> tuple[str | None, str | None, set[str]]:
    """Play unresolved matches. Returns (champion, runner_up, semi_finalists)."""
    rounds = bracket.get("rounds", {})
    working = deepcopy(rounds)
    champion: str | None = None
    runner_up: str | None = None
    semi_finalists: set[str] = set()

    for round_key in ROUND_ORDER:
        round_data = working.get(round_key)
        if not round_data:
            continue

        matches = round_data.get("matches", [])
        if not matches:
            continue

        winners = _resolve_round(matches, strengths, rng)

        if round_key == "semi_finals":
            for match in matches:
                if match.get("team_home"):
                    semi_finalists.add(match["team_home"])
                if match.get("team_away"):
                    semi_finalists.add(match["team_away"])
            for w in winners:
                semi_finalists.add(w)

        if round_key == "final" and winners:
            champion = winners[0]
            if matches:
                m = matches[0]
                home, away = m.get("team_home"), m.get("team_away")
                runner_up = away if winners[0] == home else home
        elif winners and round_key != "final":
            next_idx = ROUND_ORDER.index(round_key) + 1
            if next_idx < len(ROUND_ORDER):
                next_key = ROUND_ORDER[next_idx]
                next_round = working.setdefault(next_key, {"status": "pending", "matches": []})
                next_matches = next_round.setdefault("matches", [])
                for i in range(0, len(winners), 2):
                    if i + 1 >= len(winners):
                        break
                    slot = i // 2
                    if slot < len(next_matches):
                        next_matches[slot]["team_home"] = winners[i]
                        next_matches[slot]["team_away"] = winners[i + 1]
                    else:
                        next_matches.append({
                            "match_id": f"{next_key}_m{i // 2 + 1:02d}",
                            "team_home": winners[i],
                            "team_away": winners[i + 1],
                            "winner": None,
                            "status": "NS",
                        })

    return champion, runner_up, semi_finalists


def run(
    team_strengths: dict[str, float],
    bracket: dict[str, Any],
    n: int | None = None,
    seed: int | None = 42,
) -> dict[str, dict[str, float]]:
    """
    Run Monte Carlo simulation.

    Returns per-team dict with win_probability, reach_final_probability,
    reach_semis_probability.
    """
    simulations = n or config.N_SIMULATIONS
    active_teams = [tid for tid, s in team_strengths.items() if s is not None]

    win_counts = {tid: 0 for tid in active_teams}
    final_counts = {tid: 0 for tid in active_teams}
    semi_counts = {tid: 0 for tid in active_teams}

    rng = random.Random(seed)
    strengths = {tid: team_strengths[tid] for tid in active_teams}

    for _ in range(simulations):
        champion, runner_up, semi_finalists = _advance_bracket(bracket, strengths, rng)
        if champion and champion in win_counts:
            win_counts[champion] += 1
        for tid in (champion, runner_up):
            if tid and tid in final_counts:
                final_counts[tid] += 1
        for tid in semi_finalists:
            if tid in semi_counts:
                semi_counts[tid] += 1

    result: dict[str, dict[str, float]] = {}
    for tid in active_teams:
        result[tid] = {
            "win_probability": round(win_counts[tid] / simulations, 4),
            "reach_final_probability": round(final_counts[tid] / simulations, 4),
            "reach_semis_probability": round(semi_counts[tid] / simulations, 4),
        }
    return result


def run_fast(
    team_strengths: dict[str, float],
    bracket: dict[str, Any],
    n: int | None = None,
    seed: int | None = 42,
) -> dict[str, dict[str, float]]:
    """Vectorized batch helper — delegates to run() for clarity at 10k sims."""
    return run(team_strengths, bracket, n=n, seed=seed)

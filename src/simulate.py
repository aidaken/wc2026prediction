"""knockout sim. runs the bracket 10k times, spits out win % and per-match advance %."""

from __future__ import annotations

import random
from collections import defaultdict
from copy import deepcopy
from typing import Any

import config
from src.bracket_topology import ROUND_ORDER, propagate_winner
from src.utils import win_probability


def match_win_probability(
    team_home: str,
    team_away: str,
    strengths: dict[str, float],
) -> tuple[float, float]:
    """Analytical home/away win probability (pre-draw adjustment)."""
    sa = strengths.get(team_home, 0.5)
    sb = strengths.get(team_away, 0.5)
    prob_home = win_probability(sa, sb, scale=config.STRENGTH_SCALE)
    return prob_home, 1.0 - prob_home


def _simulate_match(
    team_a: str,
    team_b: str,
    strengths: dict[str, float],
    rng: random.Random,
) -> str:
    sa = strengths.get(team_a, 0.5)
    sb = strengths.get(team_b, 0.5)
    prob_a = win_probability(sa, sb, scale=config.STRENGTH_SCALE)

    if rng.random() < config.DRAW_PROBABILITY:
        # pens vibes: pull prob toward 50/50, upsets happen more
        prob_a = 0.5 + (prob_a - 0.5) * 0.6

    return team_a if rng.random() < prob_a else team_b


def _play_bracket_once(
    bracket: dict[str, Any],
    strengths: dict[str, float],
    rng: random.Random,
    match_win_counts: dict[str, dict[str, int]] | None = None,
) -> tuple[str | None, str | None, set[str]]:
    """Play one full tournament simulation using fixed feeder topology."""
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

        for match in matches:
            home = match.get("team_home")
            away = match.get("team_away")
            if not home or not away:
                continue

            match_id = match.get("match_id")
            existing = match.get("winner")

            if existing:
                winner = existing
            else:
                winner = _simulate_match(home, away, strengths, rng)
                if match_id and match_win_counts is not None:
                    match_win_counts[match_id][winner] += 1

            if match_id:
                propagate_winner(working, match_id, winner)

            if round_key == "final":
                champion = winner
                runner_up = away if winner == home else home

        if round_key == "semi_finals":
            for match in matches:
                if match.get("team_home"):
                    semi_finalists.add(match["team_home"])
                if match.get("team_away"):
                    semi_finalists.add(match["team_away"])

    return champion, runner_up, semi_finalists


def _build_match_predictions(
    bracket: dict[str, Any],
    strengths: dict[str, float],
    match_win_counts: dict[str, dict[str, int]],
    simulations: int,
) -> dict[str, list[dict[str, Any]]]:
    """Build per-round match advancement probabilities for the dashboard."""
    rounds = bracket.get("rounds", {})
    result: dict[str, list[dict[str, Any]]] = {}

    for round_key in ROUND_ORDER:
        round_data = rounds.get(round_key, {})
        matches = round_data.get("matches", [])
        round_preds: list[dict[str, Any]] = []

        for match in matches:
            home = match.get("team_home")
            away = match.get("team_away")
            if not home or not away:
                continue

            match_id = match.get("match_id")
            winner = match.get("winner")
            status = match.get("status", "NS")

            if winner:
                prob_home = 1.0 if winner == home else 0.0
                prob_away = 1.0 if winner == away else 0.0
            elif match_id and match_id in match_win_counts:
                counts = match_win_counts[match_id]
                prob_home = counts.get(home, 0) / simulations
                prob_away = counts.get(away, 0) / simulations
            else:
                prob_home, prob_away = match_win_probability(home, away, strengths)

            round_preds.append({
                "match_id": match_id,
                "team_home": home,
                "team_away": away,
                "advance_probability_home": round(prob_home, 4),
                "advance_probability_away": round(prob_away, 4),
                "winner": winner,
                "status": status,
                "score_home": match.get("score_home"),
                "score_away": match.get("score_away"),
            })

        if round_preds:
            result[round_key] = round_preds

    return result


def run(
    team_strengths: dict[str, float],
    bracket: dict[str, Any],
    n: int | None = None,
    seed: int | None = 42,
) -> dict[str, Any]:
    """
    Run Monte Carlo simulation.

    Returns dict with:
      - team_predictions: per-team win / reach-final / reach-semis probabilities
      - match_predictions: per-round matchup advancement probabilities
    """
    simulations = n or config.N_SIMULATIONS
    active_teams = [tid for tid, s in team_strengths.items() if s is not None]

    win_counts = {tid: 0 for tid in active_teams}
    final_counts = {tid: 0 for tid in active_teams}
    semi_counts = {tid: 0 for tid in active_teams}
    match_win_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    rng = random.Random(seed)
    strengths = {tid: team_strengths[tid] for tid in active_teams}

    for _ in range(simulations):
        champion, runner_up, semi_finalists = _play_bracket_once(
            bracket, strengths, rng, match_win_counts,
        )
        if champion and champion in win_counts:
            win_counts[champion] += 1
        for tid in (champion, runner_up):
            if tid and tid in final_counts:
                final_counts[tid] += 1
        for tid in semi_finalists:
            if tid in semi_counts:
                semi_counts[tid] += 1

    team_predictions: dict[str, dict[str, float]] = {}
    for tid in active_teams:
        team_predictions[tid] = {
            "win_probability": round(win_counts[tid] / simulations, 4),
            "reach_final_probability": round(final_counts[tid] / simulations, 4),
            "reach_semis_probability": round(semi_counts[tid] / simulations, 4),
        }

    match_predictions = _build_match_predictions(
        bracket, strengths, match_win_counts, simulations,
    )

    return {
        "team_predictions": team_predictions,
        "match_predictions": match_predictions,
    }


def run_fast(
    team_strengths: dict[str, float],
    bracket: dict[str, Any],
    n: int | None = None,
    seed: int | None = 42,
) -> dict[str, Any]:
    """Alias for run() — kept for API compatibility."""
    return run(team_strengths, bracket, n=n, seed=seed)

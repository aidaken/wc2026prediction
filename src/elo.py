"""Elo rating system — update ratings and normalize for the combined model."""

from __future__ import annotations

from typing import Any

import config
from src.utils import normalize_minmax, win_probability


def expected_score(rating_a: float, rating_b: float) -> float:
    return win_probability(rating_a, rating_b, config.ELO_SCALE)


def k_factor_for_match(match: dict[str, Any]) -> int:
    stage = match.get("stage", "knockout")
    if stage == "group":
        return config.K_WORLD_CUP_GROUP
    if stage == "knockout":
        return config.K_WORLD_CUP_KNOCKOUT
    if stage == "qualifier":
        return config.K_QUALIFIER
    return config.K_FRIENDLY


def _match_outcome(home_id: str, away_id: str, match: dict[str, Any]) -> tuple[float, float]:
    winner = match.get("winner")
    if winner is None:
        return 0.5, 0.5
    if winner == home_id:
        return 1.0, 0.0
    if winner == away_id:
        return 0.0, 1.0
    return 0.5, 0.5


def update_ratings(
    teams: dict[str, dict[str, Any]],
    fixtures: list[dict[str, Any]],
) -> dict[str, float]:
    """Update Elo in-place for completed fixtures. Returns elo_change per team this run."""
    changes: dict[str, float] = {tid: 0.0 for tid in teams}

    for match in fixtures:
        status = match.get("status", "")
        if status not in ("FT", "PEN", "AET"):
            continue

        home_id = match.get("team_home")
        away_id = match.get("team_away")
        if not home_id or not away_id:
            continue
        if home_id not in teams or away_id not in teams:
            continue

        k = k_factor_for_match(match)
        r_home = teams[home_id]["elo"]
        r_away = teams[away_id]["elo"]
        e_home = expected_score(r_home, r_away)
        e_away = expected_score(r_away, r_home)
        s_home, s_away = _match_outcome(home_id, away_id, match)

        delta_home = k * (s_home - e_home)
        delta_away = k * (s_away - e_away)

        teams[home_id]["elo"] = round(r_home + delta_home, 1)
        teams[away_id]["elo"] = round(r_away + delta_away, 1)
        changes[home_id] += delta_home
        changes[away_id] += delta_away

    for tid, delta in changes.items():
        teams[tid]["elo_change_this_round"] = round(delta, 1)

    return changes


def normalize_elo(teams: dict[str, dict[str, Any]], active_only: bool = True) -> dict[str, float]:
    ratings = {
        tid: t["elo"]
        for tid, t in teams.items()
        if not active_only or not t.get("eliminated", False)
    }
    return normalize_minmax(ratings)

"""Injury multiplier — penalize teams missing key players."""

from __future__ import annotations

from typing import Any

import config


def _player_importance(player: dict[str, Any], team_avg: float) -> float:
    if player.get("position") == "Goalkeeper" and player.get("is_starting_xi"):
        return config.GK_PENALTY

    xg90 = player.get("xg_per90", 0.0) or 0.0
    xa90 = player.get("xa_per90", 0.0) or 0.0
    if team_avg <= 0:
        importance = 0.05
    else:
        importance = (xg90 + xa90) / team_avg
    return min(importance, config.MAX_PLAYER_IMPORTANCE)


def _team_offensive_avg(player_stats: list[dict[str, Any]]) -> float:
    totals = [(p.get("xg_per90", 0.0) or 0.0) + (p.get("xa_per90", 0.0) or 0.0) for p in player_stats]
    if not totals:
        return 0.0
    return sum(totals) / len(totals)


def calculate_multipliers(
    injuries_by_team: dict[str, list[dict[str, Any]]],
    player_stats_by_team: dict[str, list[dict[str, Any]]],
    team_ids: list[str],
) -> dict[str, float]:
    multipliers: dict[str, float] = {}

    for tid in team_ids:
        multiplier = 1.0
        team_players = player_stats_by_team.get(tid, [])
        team_avg = _team_offensive_avg(team_players)
        player_lookup = {p["player_id"]: p for p in team_players if "player_id" in p}

        for injury in injuries_by_team.get(tid, []):
            if injury.get("status") == "Questionable":
                continue
            player = player_lookup.get(injury.get("player_id"), {})
            merged = {**player, **injury}
            if not merged.get("is_starting_xi", True):
                continue
            multiplier -= _player_importance(merged, team_avg)

        multipliers[tid] = round(max(multiplier, config.MIN_INJURY_MULTIPLIER), 4)

    return multipliers

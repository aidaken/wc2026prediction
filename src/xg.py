"""xG form ratio — short-term chance-creation signal from recent matches."""

from __future__ import annotations

from typing import Any

import config


def _match_weight(match: dict[str, Any]) -> float:
    if match.get("stage") in ("group", "knockout"):
        return config.XG_WC_MATCH_WEIGHT
    return 1.0


def _collect_team_matches(fixtures: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_team: dict[str, list[dict[str, Any]]] = {}
    for match in fixtures:
        if match.get("status") not in ("FT", "PEN", "AET"):
            continue
        home = match.get("team_home")
        away = match.get("team_away")
        if home:
            by_team.setdefault(home, []).append({**match, "_perspective": "home"})
        if away:
            by_team.setdefault(away, []).append({**match, "_perspective": "away"})
    for team_id, matches in by_team.items():
        matches.sort(key=lambda m: m.get("date", ""), reverse=True)
        by_team[team_id] = matches[: config.XG_FORM_GAMES]
    return by_team


def _team_xg_totals(matches: list[dict[str, Any]]) -> tuple[float, float, float, float]:
    xg_for = xg_against = goals_for = weight_sum = 0.0
    for match in matches:
        w = _match_weight(match)
        weight_sum += w
        if match["_perspective"] == "home":
            xg_for += (match.get("xg_home") or 0.0) * w
            xg_against += (match.get("xg_away") or 0.0) * w
            goals_for += (match.get("score_home") or 0) * w
        else:
            xg_for += (match.get("xg_away") or 0.0) * w
            xg_against += (match.get("xg_home") or 0.0) * w
            goals_for += (match.get("score_away") or 0) * w
    if weight_sum == 0:
        return 0.0, 0.0, 0.0, 0.0
    return xg_for / weight_sum, xg_against / weight_sum, goals_for / weight_sum, weight_sum


def calculate_form_ratios(
    fixtures: list[dict[str, Any]],
    team_ids: list[str] | None = None,
) -> dict[str, float]:
    by_team = _collect_team_matches(fixtures)
    if team_ids:
        by_team = {tid: by_team.get(tid, []) for tid in team_ids}

    ratios: dict[str, float] = {}
    for tid, matches in by_team.items():
        if not matches:
            ratios[tid] = 0.5
            continue

        avg_xg_for, avg_xg_against, avg_goals_for, _ = _team_xg_totals(matches)
        denom = avg_xg_for + avg_xg_against
        ratio = avg_xg_for / denom if denom > 0 else 0.5

        if avg_xg_for > 0 and avg_goals_for / avg_xg_for > config.XG_LUCK_THRESHOLD:
            ratio = min(ratio, 0.55)

        ratios[tid] = round(ratio, 4)

    return ratios

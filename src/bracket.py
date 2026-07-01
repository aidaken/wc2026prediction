"""Bracket state management — sync from API, detect round, mark eliminations."""

from __future__ import annotations

from typing import Any

import config

ROUND_KEY_TO_NAME = {
    "round_of_32": "Round of 32",
    "round_of_16": "Round of 16",
    "quarter_finals": "Quarter-finals",
    "semi_finals": "Semi-finals",
    "final": "Final",
}

ROUND_NAME_TO_KEY = {v: k for k, v in ROUND_KEY_TO_NAME.items()}

ROUND_ORDER = list(ROUND_KEY_TO_NAME.keys())

FINISHED = frozenset({"FT", "PEN", "AET"})


def detect_current_round(bracket: dict[str, Any]) -> str:
    """Return the first round that is not fully complete."""
    rounds = bracket.get("rounds", {})
    for key in ROUND_ORDER:
        round_data = rounds.get(key, {})
        matches = round_data.get("matches", [])
        if not matches:
            continue
        if any(m.get("status") not in FINISHED for m in matches if m.get("team_home")):
            return ROUND_KEY_TO_NAME[key]
    return "Final"


def detect_last_completed_round(bracket: dict[str, Any]) -> str | None:
    last: str | None = None
    rounds = bracket.get("rounds", {})
    for key in ROUND_ORDER:
        round_data = rounds.get(key, {})
        matches = [m for m in round_data.get("matches", []) if m.get("team_home")]
        if matches and all(m.get("status") in FINISHED for m in matches):
            last = ROUND_KEY_TO_NAME[key]
    return last


def _match_key(match: dict[str, Any]) -> tuple[str, str] | None:
    home, away = match.get("team_home"), match.get("team_away")
    if not home or not away:
        return None
    return tuple(sorted((home, away)))


def sync_bracket_from_fixtures(
    bracket: dict[str, Any],
    fixtures: list[dict[str, Any]],
    round_name: str,
) -> list[dict[str, Any]]:
    """
    Merge API fixtures into bracket.json for the given round.
    Returns newly completed matches (for elimination processing).
    """
    round_key = ROUND_NAME_TO_KEY.get(round_name)
    if not round_key:
        return []

    rounds = bracket.setdefault("rounds", {})
    round_data = rounds.setdefault(round_key, {"status": "in_progress", "matches": []})
    existing = round_data.setdefault("matches", [])

    by_fixture_id = {m.get("api_fixture_id"): m for m in existing if m.get("api_fixture_id")}
    by_pair = {_match_key(m): m for m in existing if _match_key(m)}

    completed_new: list[dict[str, Any]] = []

    for fix in fixtures:
        target = None
        if fix.get("api_fixture_id") and fix["api_fixture_id"] in by_fixture_id:
            target = by_fixture_id[fix["api_fixture_id"]]
        else:
            pair = _match_key(fix)
            if pair and pair in by_pair:
                target = by_pair[pair]

        if target is None:
            target = {**fix, "match_id": fix.get("match_id") or f"{round_key}_{len(existing) + 1:02d}"}
            existing.append(target)
            if fix.get("api_fixture_id"):
                by_fixture_id[fix["api_fixture_id"]] = target
            pair = _match_key(fix)
            if pair:
                by_pair[pair] = target

        was_finished = target.get("status") in FINISHED
        for field in (
            "score_home", "score_away", "penalties_home", "penalties_away",
            "winner", "status", "xg_home", "xg_away", "date", "api_fixture_id",
            "team_home", "team_away",
        ):
            if fix.get(field) is not None:
                target[field] = fix[field]

        if not was_finished and target.get("status") in FINISHED:
            completed_new.append(target)

    statuses = [m.get("status") for m in existing if m.get("team_home")]
    if statuses and all(s in FINISHED for s in statuses):
        round_data["status"] = "completed"
    elif any(s in FINISHED for s in statuses):
        round_data["status"] = "in_progress"
    else:
        round_data["status"] = "pending"

    return completed_new


def mark_eliminations(
    teams: dict[str, dict[str, Any]],
    completed_matches: list[dict[str, Any]],
) -> list[str]:
    """Mark losing teams as eliminated. Returns list of newly eliminated team IDs."""
    eliminated: list[str] = []
    for match in completed_matches:
        winner = match.get("winner")
        home, away = match.get("team_home"), match.get("team_away")
        if not winner or not home or not away:
            continue
        loser = away if winner == home else home
        if loser in teams and not teams[loser].get("eliminated"):
            teams[loser]["eliminated"] = True
            eliminated.append(loser)
    return eliminated


def validate_round_complete(bracket: dict[str, Any], round_name: str) -> None:
    """Raise if the named round has unfinished matches."""
    from src.fetch import DataValidationError

    round_key = ROUND_NAME_TO_KEY.get(round_name)
    if not round_key:
        return
    matches = bracket.get("rounds", {}).get(round_key, {}).get("matches", [])
    unfinished = [
        m for m in matches
        if m.get("team_home") and m.get("status") not in FINISHED and m.get("status") != "NS"
    ]
    if unfinished:
        raise DataValidationError(
            f"Round '{round_name}' has {len(unfinished)} matches not fully complete"
        )

"""where r32 winners actually go in the bracket. fifa combo 67, fixed tree."""

from __future__ import annotations

from typing import Any

Feeder = tuple[str, str]

MATCH_FEEDERS: dict[str, Feeder] = {
    # r32 -> r16
    "r32_m73": ("r16_m90", "home"),   # houston
    "r32_m74": ("r16_m89", "home"),   # philly
    "r32_m75": ("r16_m90", "away"),
    "r32_m76": ("r16_m91", "home"),   # nyc
    "r32_m77": ("r16_m89", "away"),
    "r32_m78": ("r16_m91", "away"),
    "r32_m79": ("r16_m92", "home"),   # mexico city
    "r32_m80": ("r16_m92", "away"),
    "r32_m81": ("r16_m94", "home"),   # seattle
    "r32_m82": ("r16_m94", "away"),
    "r32_m83": ("r16_m93", "home"),   # dallas
    "r32_m84": ("r16_m93", "away"),
    "r32_m85": ("r16_m96", "home"),   # vancouver
    "r32_m86": ("r16_m95", "home"),   # atlanta
    "r32_m87": ("r16_m96", "away"),
    "r32_m88": ("r16_m95", "away"),
    # r16 -> qf
    "r16_m89": ("qf_m01", "home"),
    "r16_m90": ("qf_m01", "away"),
    "r16_m93": ("qf_m02", "home"),
    "r16_m94": ("qf_m02", "away"),
    "r16_m91": ("qf_m03", "home"),
    "r16_m92": ("qf_m03", "away"),
    "r16_m95": ("qf_m04", "home"),
    "r16_m96": ("qf_m04", "away"),
    # qf -> sf
    "qf_m01": ("sf_m01", "home"),
    "qf_m02": ("sf_m01", "away"),
    "qf_m03": ("sf_m02", "home"),
    "qf_m04": ("sf_m02", "away"),
    # sf -> final (winners)
    "sf_m01": ("final_m01", "home"),
    "sf_m02": ("final_m01", "away"),
}

# SF losers play for third place (Match 103, Miami)
MATCH_LOSER_FEEDERS: dict[str, Feeder] = {
    "sf_m01": ("third_m01", "home"),
    "sf_m02": ("third_m01", "away"),
}

ROUND_ORDER = [
    "round_of_32",
    "round_of_16",
    "quarter_finals",
    "semi_finals",
    "final",
    "third_place",
]


def find_match(working: dict[str, Any], match_id: str) -> dict[str, Any] | None:
    for round_key in ROUND_ORDER:
        for match in working.get(round_key, {}).get("matches", []):
            if match.get("match_id") == match_id:
                return match
    return None


def _slot_team(working: dict[str, Any], target_id: str, slot: str, team_id: str) -> None:
    target = find_match(working, target_id)
    if target is None:
        return
    slot_key = "team_home" if slot == "home" else "team_away"
    target[slot_key] = team_id


def propagate_winner(working: dict[str, Any], source_match_id: str, winner: str) -> None:
    feeder = MATCH_FEEDERS.get(source_match_id)
    if not feeder:
        return
    target_id, slot = feeder
    _slot_team(working, target_id, slot, winner)


def propagate_loser(working: dict[str, Any], source_match_id: str, loser: str) -> None:
    feeder = MATCH_LOSER_FEEDERS.get(source_match_id)
    if not feeder:
        return
    target_id, slot = feeder
    _slot_team(working, target_id, slot, loser)


def propagate_outcome(
    working: dict[str, Any],
    source_match_id: str,
    *,
    winner: str,
    home: str | None,
    away: str | None,
) -> None:
    """Push winner forward and SF loser into the third-place match."""
    propagate_winner(working, source_match_id, winner)
    if home and away and winner in (home, away):
        loser = away if winner == home else home
        propagate_loser(working, source_match_id, loser)

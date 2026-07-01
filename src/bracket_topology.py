"""WC 2026 knockout bracket topology — feeder links between matches.

Each feeder maps a source match winner into a specific slot (home/away) of the
next-round match. Derived from the fixed FIFA combination-67 bracket tree.
"""

from __future__ import annotations

from typing import Any

# (target_match_id, slot) where slot is "home" or "away"
Feeder = tuple[str, str]

MATCH_FEEDERS: dict[str, Feeder] = {
    # Round of 32 → Round of 16
    "r32_m73": ("r16_m90", "home"),   # RSA/CAN → Houston
    "r32_m74": ("r16_m89", "home"),   # GER/PAR → Philadelphia
    "r32_m75": ("r16_m90", "away"),   # NED/MAR → Houston
    "r32_m76": ("r16_m91", "home"),   # BRA/JPN → New York
    "r32_m77": ("r16_m89", "away"),   # FRA/SWE → Philadelphia
    "r32_m78": ("r16_m91", "away"),   # CIV/NOR → New York
    "r32_m79": ("r16_m92", "home"),   # MEX/ECU → Mexico City
    "r32_m80": ("r16_m92", "away"),   # ENG/COD → Mexico City
    "r32_m81": ("r16_m94", "home"),   # USA/BIH → Seattle
    "r32_m82": ("r16_m94", "away"),   # BEL/SEN → Seattle
    "r32_m83": ("r16_m93", "home"),   # POR/CRO → Dallas
    "r32_m84": ("r16_m93", "away"),   # ESP/AUT → Dallas
    "r32_m85": ("r16_m96", "home"),   # SUI/ALG → Vancouver
    "r32_m86": ("r16_m95", "home"),   # ARG/CPV → Atlanta
    "r32_m87": ("r16_m96", "away"),   # COL/GHA → Vancouver
    "r32_m88": ("r16_m95", "away"),   # AUS/EGY → Atlanta
    # Round of 16 → Quarter-finals
    "r16_m89": ("qf_m01", "home"),    # Philadelphia → Boston
    "r16_m90": ("qf_m01", "away"),    # Houston → Boston
    "r16_m93": ("qf_m02", "home"),    # Dallas → Los Angeles
    "r16_m94": ("qf_m02", "away"),    # Seattle → Los Angeles
    "r16_m91": ("qf_m03", "home"),    # New York → Miami
    "r16_m92": ("qf_m03", "away"),    # Mexico City → Miami
    "r16_m95": ("qf_m04", "home"),    # Atlanta → Kansas City
    "r16_m96": ("qf_m04", "away"),    # Vancouver → Kansas City
    # Quarter-finals → Semi-finals
    "qf_m01": ("sf_m01", "home"),
    "qf_m02": ("sf_m01", "away"),
    "qf_m03": ("sf_m02", "home"),
    "qf_m04": ("sf_m02", "away"),
    # Semi-finals → Final
    "sf_m01": ("final_m01", "home"),
    "sf_m02": ("final_m01", "away"),
}

ROUND_ORDER = [
    "round_of_32",
    "round_of_16",
    "quarter_finals",
    "semi_finals",
    "final",
]


def find_match(working: dict[str, Any], match_id: str) -> dict[str, Any] | None:
    for round_key in ROUND_ORDER:
        for match in working.get(round_key, {}).get("matches", []):
            if match.get("match_id") == match_id:
                return match
    return None


def propagate_winner(working: dict[str, Any], source_match_id: str, winner: str) -> None:
    """Place winner into the correct next-round slot via feeder link."""
    feeder = MATCH_FEEDERS.get(source_match_id)
    if not feeder:
        return
    target_id, slot = feeder
    target = find_match(working, target_id)
    if target is None:
        return
    slot_key = "team_home" if slot == "home" else "team_away"
    target[slot_key] = winner

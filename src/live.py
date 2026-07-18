"""In-play (live) win probability for a match still in progress.

Pre-match odds come from strength scores; once a match kicks off, the score and
clock matter more than any prior. This rolls the game forward from where it
stands: model each side's remaining goals as an independent Poisson draw off
their current scoring pace, add them to the score on the board, and see who is
ahead at full time. A level score resolves on penalties — knockout 3rd-place
and final games have no replay, and the World Cup 3rd-place match skips extra
time entirely, so a tie there goes straight to a shootout.
"""

from __future__ import annotations

import math

import config
from src.utils import win_probability

REGULATION_MINUTES = 90
DEFAULT_STOPPAGE = 5          # rough second-half stoppage cushion, in minutes
BASELINE_TEAM_RATE = 1.35 / 90.0   # goals/min when we have no live pace to read

LIVE_STATUSES = frozenset({"LIVE", "1H", "2H", "HT", "ET", "BT", "P", "INT"})


def _poisson_pmf(k: int, lam: float) -> float:
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * lam ** k / math.factorial(k)


def remaining_rate(xg_so_far: float | None, minute: int) -> float:
    """Goals-per-minute pace for the rest of the game.

    Uses live xG per minute played when available (it captures how the game is
    actually flowing), otherwise falls back to a neutral team baseline.
    """
    if xg_so_far is not None and minute and minute > 0:
        return float(xg_so_far) / float(minute)
    return BASELINE_TEAM_RATE


def penalty_edge(strength_home: float, strength_away: float) -> float:
    """Home side's share of a shootout — near coin-flip, mild strength tilt."""
    tilt = win_probability(strength_home, strength_away, scale=config.STRENGTH_SCALE) - 0.5
    return 0.5 + tilt * 0.5


def live_win_probability(
    score_home: int,
    score_away: int,
    minute: int,
    rate_home: float,
    rate_away: float,
    *,
    strength_home: float = 0.5,
    strength_away: float = 0.5,
    extra_time: bool = False,
    stoppage: int = DEFAULT_STOPPAGE,
    max_extra_goals: int = 12,
) -> tuple[float, float]:
    """Return (P(home wins), P(away wins)) from the current live state.

    A tie at full time is resolved on penalties (mildly strength-tilted).
    """
    minutes_left = max(0, REGULATION_MINUTES + stoppage - int(minute))
    if extra_time:
        minutes_left += 30

    lam_home = max(0.0, rate_home) * minutes_left
    lam_away = max(0.0, rate_away) * minutes_left
    pens_home = penalty_edge(strength_home, strength_away)

    p_home = 0.0
    p_away = 0.0
    for gh in range(max_extra_goals + 1):
        ph = _poisson_pmf(gh, lam_home)
        if ph < 1e-12:
            continue
        for ga in range(max_extra_goals + 1):
            pa = _poisson_pmf(ga, lam_away)
            if pa < 1e-12:
                continue
            joint = ph * pa
            final_home = score_home + gh
            final_away = score_away + ga
            if final_home > final_away:
                p_home += joint
            elif final_away > final_home:
                p_away += joint
            else:
                p_home += joint * pens_home
                p_away += joint * (1.0 - pens_home)

    total = p_home + p_away
    if total > 0:
        p_home /= total
        p_away /= total
    return p_home, p_away


def live_win_probability_from_match(
    match: dict,
    strengths: dict[str, float],
) -> tuple[float, float] | None:
    """Convenience wrapper: pull score/minute/xG straight off a bracket match."""
    if match.get("status") not in LIVE_STATUSES:
        return None
    minute = match.get("minute")
    if not minute:
        return None

    home = match.get("team_home")
    away = match.get("team_away")
    score_home = match.get("score_home") or 0
    score_away = match.get("score_away") or 0
    rate_home = remaining_rate(match.get("xg_home"), minute)
    rate_away = remaining_rate(match.get("xg_away"), minute)

    return live_win_probability(
        score_home,
        score_away,
        minute,
        rate_home,
        rate_away,
        strength_home=strengths.get(home, 0.5),
        strength_away=strengths.get(away, 0.5),
        extra_time=bool(match.get("extra_time")),
    )

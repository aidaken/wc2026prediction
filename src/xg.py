"""xG form ratio — recent chance-creation from last N matches (xG when available, goals fallback)."""

from __future__ import annotations

from typing import Any

import config
from src.utils import DATA_DIR, load_json

MANUAL_XG_PATH = DATA_DIR / "manual_xg.json"


def load_manual_xg() -> dict[str, dict[str, float]]:
    """
    Per-team tournament xG totals from data/manual_xg.json (e.g. pasted from FotMob's
    xG table). Shape: {"TID": {"xg": 9.2, "xga": 3.1, "mp": 4}}. Used to override the
    goals fallback when the stats API can't serve match xG.
    """
    doc = load_json(MANUAL_XG_PATH)
    raw = doc.get("xg") or doc.get("teams") or {}
    if not isinstance(raw, dict):
        return {}
    out: dict[str, dict[str, float]] = {}
    for tid, vals in raw.items():
        if not isinstance(vals, dict):
            continue
        try:
            xg = float(vals["xg"])
            xga = float(vals["xga"])
        except (KeyError, TypeError, ValueError):
            continue
        entry = {"xg": xg, "xga": xga}
        mp = vals.get("mp")
        if mp:
            try:
                entry["mp"] = int(mp)
            except (TypeError, ValueError):
                pass
        out[str(tid)] = entry
    return out


def apply_manual_xg(
    ratios: dict[str, float],
    meta: dict[str, dict[str, Any]],
    active: list[str] | None = None,
) -> int:
    """Overlay manual per-team xG onto computed form ratios. Returns count applied."""
    manual = load_manual_xg()
    applied = 0
    for tid, vals in manual.items():
        if active is not None and tid not in active:
            continue
        xg, xga = vals["xg"], vals["xga"]
        denom = xg + xga
        ratio = xg / denom if denom > 0 else 0.5
        mp = vals.get("mp") or 0
        ratios[tid] = round(ratio, 4)
        meta[tid] = {
            "has_xg_data": True,
            "matches_used": mp,
            "form_source": "xg_table",
            "avg_xg_for": round(xg / mp, 2) if mp else None,
            "avg_xg_against": round(xga / mp, 2) if mp else None,
        }
        applied += 1
    return applied


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


def _perspective_values(match: dict[str, Any]) -> tuple[float, float, float, bool]:
    """Return (for, against, goals_for, used_xg) for this team's perspective."""
    if match["_perspective"] == "home":
        xg_for = match.get("xg_home")
        xg_against = match.get("xg_away")
        goals_for = match.get("score_home")
        goals_against = match.get("score_away")
    else:
        xg_for = match.get("xg_away")
        xg_against = match.get("xg_home")
        goals_for = match.get("score_away")
        goals_against = match.get("score_home")

    if xg_for is not None and xg_against is not None:
        return float(xg_for), float(xg_against), float(goals_for or 0), True

    gf = float(goals_for or 0)
    ga = float(goals_against or 0)
    # score proxy: treat goals like a coarse xG stand-in when stats API didn't return xG
    return max(gf, 0.15), max(ga, 0.15), gf, False


def _team_form_totals(matches: list[dict[str, Any]]) -> tuple[float, float, float, float, bool]:
    val_for = val_against = goals_for = weight_sum = 0.0
    any_xg = False
    for match in matches:
        w = _match_weight(match)
        vf, va, gf, used_xg = _perspective_values(match)
        any_xg = any_xg or used_xg
        weight_sum += w
        val_for += vf * w
        val_against += va * w
        goals_for += gf * w
    if weight_sum == 0:
        return 0.0, 0.0, 0.0, 0.0, False
    return (
        val_for / weight_sum,
        val_against / weight_sum,
        goals_for / weight_sum,
        weight_sum,
        any_xg,
    )


def calculate_form_ratios(
    fixtures: list[dict[str, Any]],
    team_ids: list[str] | None = None,
) -> tuple[dict[str, float], dict[str, dict[str, Any]]]:
    """
    Returns (form_ratios, meta_per_team).
    meta includes has_xg_data, matches_used, form_source ('xg' | 'goals' | 'default').
    """
    by_team = _collect_team_matches(fixtures)
    if team_ids:
        by_team = {tid: by_team.get(tid, []) for tid in team_ids}

    ratios: dict[str, float] = {}
    meta: dict[str, dict[str, Any]] = {}

    for tid, matches in by_team.items():
        if not matches:
            ratios[tid] = 0.5
            meta[tid] = {
                "has_xg_data": False,
                "matches_used": 0,
                "form_source": "default",
                "avg_xg_for": None,
                "avg_xg_against": None,
            }
            continue

        avg_for, avg_against, avg_goals_for, _, any_xg = _team_form_totals(matches)
        denom = avg_for + avg_against
        ratio = avg_for / denom if denom > 0 else 0.5

        if any_xg and avg_for > 0 and avg_goals_for / avg_for > config.XG_LUCK_THRESHOLD:
            ratio = min(ratio, 0.55)

        source = "xg" if any_xg else "goals"
        ratios[tid] = round(ratio, 4)
        meta[tid] = {
            "has_xg_data": any_xg,
            "matches_used": len(matches),
            "form_source": source,
            "avg_xg_for": round(avg_for, 2) if any_xg else None,
            "avg_xg_against": round(avg_against, 2) if any_xg else None,
        }

    return ratios, meta

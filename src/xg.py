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


def build_opponent_map(
    fixtures: list[dict[str, Any]],
    bracket: dict[str, Any] | None = None,
) -> dict[str, list[str]]:
    """
    Map each team to the opponents it has actually played (completed matches only).
    Any pair meets at most once in a World Cup, so dedup by unordered pair keeps the
    knockout games from being double-counted when they live in both the fixture cache
    and the bracket.
    """
    opponents: dict[str, list[str]] = {}
    seen: set[frozenset[str]] = set()

    def add(home: str | None, away: str | None) -> None:
        if not home or not away:
            return
        key = frozenset((home, away))
        if key in seen:
            return
        seen.add(key)
        opponents.setdefault(home, []).append(away)
        opponents.setdefault(away, []).append(home)

    for match in fixtures or []:
        if match.get("status") in ("FT", "PEN", "AET"):
            add(match.get("team_home"), match.get("team_away"))
    for round_data in (bracket or {}).get("rounds", {}).values():
        for match in round_data.get("matches", []):
            if match.get("status") in ("FT", "PEN", "AET"):
                add(match.get("team_home"), match.get("team_away"))
    return opponents


def _schedule_rates(manual: dict[str, dict[str, float]]) -> tuple[dict[str, dict[str, float]], float, float]:
    """Per-game xG for/against for every team with games played, plus league averages."""
    rates = {
        tid: {"xgf": v["xg"] / v["mp"], "xga": v["xga"] / v["mp"]}
        for tid, v in manual.items()
        if v.get("mp")
    }
    if not rates:
        return {}, 0.0, 0.0
    league_xgf = sum(r["xgf"] for r in rates.values()) / len(rates)
    league_xga = sum(r["xga"] for r in rates.values()) / len(rates)
    return rates, league_xgf, league_xga


def apply_manual_xg(
    ratios: dict[str, float],
    meta: dict[str, dict[str, Any]],
    active: list[str] | None = None,
    opponents: dict[str, list[str]] | None = None,
) -> int:
    """
    Overlay manual per-team xG onto computed form ratios. Returns count applied.

    When opponent data is available and config.XG_OPPONENT_ADJUST is on, xG is rescaled
    for strength of schedule: a team that faced stingy defenses gets its xG-for boosted,
    and one that faced strong attacks gets its xG-against forgiven. Multipliers come from
    the opponents' own xG profiles, so racking up numbers vs Qatar counts for less than
    the same output vs Brazil.
    """
    manual = load_manual_xg()
    if not manual:
        return 0

    rates, league_xgf, league_xga = _schedule_rates(manual)
    do_adjust = bool(
        config.XG_OPPONENT_ADJUST and opponents and rates and league_xgf > 0 and league_xga > 0
    )

    applied = 0
    for tid, vals in manual.items():
        if active is not None and tid not in active:
            continue
        raw_xg, raw_xga = vals["xg"], vals["xga"]
        mp = vals.get("mp") or 0
        xg, xga = raw_xg, raw_xga
        sos = 1.0

        if do_adjust and mp:
            faced = [o for o in opponents.get(tid, []) if o in rates]
            if faced:
                opp_xga = sum(rates[o]["xga"] for o in faced) / len(faced)  # how leaky the D's faced were
                opp_xgf = sum(rates[o]["xgf"] for o in faced) / len(faced)  # how dangerous the A's faced were
                att_mult = _clamp(league_xga / opp_xga) if opp_xga > 0 else 1.0
                def_mult = _clamp(league_xgf / opp_xgf) if opp_xgf > 0 else 1.0
                xg = raw_xg * att_mult
                xga = raw_xga * def_mult
                sos = round((att_mult + 1.0 / def_mult) / 2.0, 3)  # >1 = tougher run

        denom = xg + xga
        ratio = xg / denom if denom > 0 else 0.5
        ratios[tid] = round(ratio, 4)
        meta[tid] = {
            "has_xg_data": True,
            "matches_used": mp,
            "form_source": "xg_table_adj" if (do_adjust and sos != 1.0) else "xg_table",
            "avg_xg_for": round(raw_xg / mp, 2) if mp else None,
            "avg_xg_against": round(raw_xga / mp, 2) if mp else None,
            "adj_xg_for": round(xg / mp, 2) if (do_adjust and mp and sos != 1.0) else None,
            "adj_xg_against": round(xga / mp, 2) if (do_adjust and mp and sos != 1.0) else None,
            "sos_multiplier": sos,
        }
        applied += 1
    return applied


def _clamp(value: float) -> float:
    return min(max(value, config.XG_ADJ_CLAMP_LO), config.XG_ADJ_CLAMP_HI)


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

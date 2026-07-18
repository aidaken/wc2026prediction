"""API-Football client — fixtures, player stats, injuries."""

from __future__ import annotations

import logging
import os
from typing import Any

import requests

import config
from src.teams import TeamRegistry
from src.utils import retry

logger = logging.getLogger("wc2026")


class FetchError(Exception):
    """Critical API-Football failure."""


class DataValidationError(Exception):
    """Raw data failed validation before calculation."""


def _api_key() -> str:
    key = os.getenv("API_FOOTBALL_KEY", "").strip()
    if not key:
        raise FetchError("API_FOOTBALL_KEY not set")
    return key


def _headers() -> dict[str, str]:
    return {"x-apisports-key": _api_key()}


@retry()
def _get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"{config.API_FOOTBALL_BASE}{path}"
    response = requests.get(url, headers=_headers(), params=params or {}, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if payload.get("errors"):
        raise FetchError(str(payload["errors"]))
    return payload


def _resolve_winner(
    registry: TeamRegistry,
    status: str,
    home: dict[str, Any],
    away: dict[str, Any],
    goals: dict[str, Any],
    score: dict[str, Any],
) -> str | None:
    if status not in ("FT", "PEN", "AET"):
        return None

    home_goals = goals.get("home") or 0
    away_goals = goals.get("away") or 0
    home_id = registry.resolve(home.get("id")) or registry.resolve(home.get("name"))
    away_id = registry.resolve(away.get("id")) or registry.resolve(away.get("name"))

    if home_goals > away_goals:
        return home_id
    if away_goals > home_goals:
        return away_id

    if status == "PEN":
        pen = score.get("penalty") or {}
        pen_home = pen.get("home") or 0
        pen_away = pen.get("away") or 0
        if pen_home > pen_away:
            return home_id
        if pen_away > pen_home:
            return away_id

    return None


def _normalize_fixture(
    item: dict[str, Any],
    registry: TeamRegistry,
    stage: str = "knockout",
) -> dict[str, Any]:
    fixture = item.get("fixture", {})
    teams = item.get("teams", {})
    goals = item.get("goals", {})
    score = item.get("score", {})
    status = fixture.get("status", {}).get("short", "NS")
    home = teams.get("home", {})
    away = teams.get("away", {})

    home_id = registry.resolve(home.get("id")) or registry.resolve(home.get("name"))
    away_id = registry.resolve(away.get("id")) or registry.resolve(away.get("name"))
    winner = _resolve_winner(registry, status, home, away, goals, score)

    return {
        "api_fixture_id": fixture.get("id"),
        "date": fixture.get("date"),
        "team_home": home_id,
        "team_away": away_id,
        "api_team_home_id": home.get("id"),
        "api_team_away_id": away.get("id"),
        "score_home": goals.get("home"),
        "score_away": goals.get("away"),
        "penalties_home": score.get("penalty", {}).get("home"),
        "penalties_away": score.get("penalty", {}).get("away"),
        "winner": winner,
        "status": status,
        "xg_home": None,
        "xg_away": None,
        "stage": stage,
    }


@retry()
def get_fixture_xg(
    fixture_id: int,
    home_api_id: int | None,
    away_api_id: int | None,
) -> tuple[float | None, float | None]:
    payload = _get("/fixtures/statistics", {"fixture": fixture_id})
    xg_home = xg_away = None
    for block in payload.get("response", []):
        team_id = block.get("team", {}).get("id")
        for stat in block.get("statistics", []):
            if stat.get("type") != "expected_goals":
                continue
            value = stat.get("value")
            if isinstance(value, str):
                value = float(value) if value else None
            if team_id == home_api_id:
                xg_home = value
            elif team_id == away_api_id:
                xg_away = value
    return xg_home, xg_away


def get_fixtures(
    round_name: str,
    registry: TeamRegistry,
    stage: str = "knockout",
) -> list[dict[str, Any]]:
    params = {
        "league": config.API_FOOTBALL_WC_ID,
        "season": config.API_FOOTBALL_SEASON,
        "round": round_name,
    }
    payload = _get("/fixtures", params)
    fixtures = [
        _normalize_fixture(item, registry, stage=stage)
        for item in payload.get("response", [])
    ]

    for match in fixtures:
        if match["status"] in ("FT", "PEN", "AET") and match.get("api_fixture_id"):
            try:
                xg_home, xg_away = get_fixture_xg(
                    match["api_fixture_id"],
                    match.get("api_team_home_id"),
                    match.get("api_team_away_id"),
                )
                match["xg_home"] = xg_home
                match["xg_away"] = xg_away
            except Exception as exc:
                logger.warning("xG unavailable for fixture %s: %s", match["api_fixture_id"], exc)

    return fixtures


def get_all_season_fixtures(
    registry: TeamRegistry,
    *,
    enrich_xg: bool = True,
) -> list[dict[str, Any]]:
    """Fetch every WC 2026 fixture (group + knockouts) for form / Elo history."""
    params = {
        "league": config.API_FOOTBALL_WC_ID,
        "season": config.API_FOOTBALL_SEASON,
    }
    payload = _get("/fixtures", params)
    fixtures: list[dict[str, Any]] = []
    for item in payload.get("response", []):
        round_name = (item.get("league", {}) or {}).get("round", "")
        stage = "group" if "group" in round_name.lower() else "knockout"
        fixtures.append(_normalize_fixture(item, registry, stage=stage))

    if enrich_xg:
        for match in fixtures:
            if match["status"] not in ("FT", "PEN", "AET"):
                continue
            if match.get("xg_home") is not None:
                continue
            fid = match.get("api_fixture_id")
            if not fid:
                continue
            try:
                xg_home, xg_away = get_fixture_xg(
                    fid,
                    match.get("api_team_home_id"),
                    match.get("api_team_away_id"),
                )
                match["xg_home"] = xg_home
                match["xg_away"] = xg_away
            except Exception as exc:
                logger.warning("xG unavailable for fixture %s: %s", fid, exc)

    return fixtures


def merge_fixtures(*lists: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge fixture lists; later entries override on match_id or api_fixture_id."""
    by_key: dict[str, dict[str, Any]] = {}
    for fixtures in lists:
        for match in fixtures:
            key = match.get("match_id")
            if not key and match.get("api_fixture_id"):
                key = f"api:{match['api_fixture_id']}"
            if not key and match.get("team_home") and match.get("team_away"):
                key = f"{match['team_home']}:{match['team_away']}:{match.get('date', '')}"
            if not key:
                continue
            if key in by_key:
                by_key[key] = {**by_key[key], **match}
            else:
                by_key[key] = dict(match)
    return sorted(by_key.values(), key=lambda m: m.get("date", ""))


def enrich_bracket_with_xg(
    bracket: dict[str, Any],
    registry: TeamRegistry,
) -> int:
    """Backfill xG on finished bracket matches via API. Returns count enriched."""
    enriched = 0
    for round_data in bracket.get("rounds", {}).values():
        for match in round_data.get("matches", []):
            if match.get("status") not in ("FT", "PEN", "AET"):
                continue
            if match.get("xg_home") is not None and match.get("xg_away") is not None:
                continue
            fid = match.get("api_fixture_id")
            if not fid:
                home_api = registry.api_id(match.get("team_home")) if match.get("team_home") else None
                away_api = registry.api_id(match.get("team_away")) if match.get("team_away") else None
                # can't fetch without fixture id
                _ = (home_api, away_api)
                continue
            try:
                xg_home, xg_away = get_fixture_xg(
                    fid,
                    match.get("api_team_home_id") or registry.api_id(match.get("team_home")),
                    match.get("api_team_away_id") or registry.api_id(match.get("team_away")),
                )
                if xg_home is not None or xg_away is not None:
                    match["xg_home"] = xg_home
                    match["xg_away"] = xg_away
                    enriched += 1
            except Exception as exc:
                logger.warning("Bracket xG backfill failed for %s: %s", fid, exc)
    return enriched


def get_player_stats(api_team_id: int, starting_player_ids: set[int] | None = None) -> list[dict[str, Any]]:
    params = {
        "league": config.API_FOOTBALL_WC_ID,
        "season": config.API_FOOTBALL_SEASON,
        "team": api_team_id,
    }
    payload = _get("/players", params)
    starting = starting_player_ids or set()
    players: list[dict[str, Any]] = []
    for block in payload.get("response", []):
        player = block.get("player", {})
        stats = (block.get("statistics") or [{}])[0]
        games = stats.get("games") or {}
        goals = stats.get("goals") or {}
        minutes = games.get("minutes") or 0
        played = max(minutes / 90.0, 0.01)
        player_id = player.get("id")
        appearances = games.get("appearences") or games.get("appearances") or 0
        players.append({
            "player_id": player_id,
            "name": player.get("name"),
            "position": games.get("position"),
            "goals": goals.get("total") or 0,
            "assists": goals.get("assists") or 0,
            "minutes": minutes,
            "xg_per90": (goals.get("total") or 0) / played,
            "xa_per90": (goals.get("assists") or 0) / played,
            "is_starting_xi": player_id in starting or appearances >= 2,
        })
    return players


def get_injuries(api_team_id: int, player_stats: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    params = {
        "league": config.API_FOOTBALL_WC_ID,
        "season": config.API_FOOTBALL_SEASON,
        "team": api_team_id,
    }
    payload = _get("/injuries", params)
    starters = {
        p["player_id"] for p in (player_stats or [])
        if p.get("is_starting_xi") and p.get("player_id")
    }
    injuries: list[dict[str, Any]] = []
    for item in payload.get("response", []):
        player = item.get("player", {})
        player_id = player.get("id")
        injuries.append({
            "player_id": player_id,
            "name": player.get("name"),
            "status": player.get("type", "Missing Fixture"),
            "reason": player.get("reason"),
            "is_starting_xi": player_id in starters or player_id in config.KEY_PLAYERS,
        })
    return injuries


def validate_raw_data(
    fixtures: list[dict[str, Any]],
    teams_remaining: int,
    require_complete: bool = False,
) -> None:
    if teams_remaining < 2:
        raise DataValidationError(f"Expected at least 2 teams remaining, got {teams_remaining}")

    from src.live import LIVE_STATUSES

    expected = {"FT", "PEN", "AET", "NS"} | set(LIVE_STATUSES)
    incomplete = [f for f in fixtures if f.get("status") not in expected]
    if incomplete:
        logger.warning("%d fixtures have unexpected status", len(incomplete))

    if require_complete:
        unfinished = [f for f in fixtures if f.get("status") == "NS" and f.get("team_home")]
        if unfinished:
            raise DataValidationError(
                f"{len(unfinished)} matches in the current fetch are not finished yet"
            )

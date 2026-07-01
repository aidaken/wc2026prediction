"""API-Football client — fixtures, player stats, injuries."""

from __future__ import annotations

import logging
import os
from typing import Any

import requests

import config
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


def _normalize_fixture(item: dict[str, Any], stage: str = "knockout") -> dict[str, Any]:
    fixture = item.get("fixture", {})
    teams = item.get("teams", {})
    goals = item.get("goals", {})
    score = item.get("score", {})
    status = fixture.get("status", {}).get("short", "NS")
    home = teams.get("home", {})
    away = teams.get("away", {})

    winner = None
    if status in ("FT", "PEN", "AET"):
        if goals.get("home", 0) > goals.get("away", 0):
            winner = home.get("name")
        elif goals.get("away", 0) > goals.get("home", 0):
            winner = away.get("name")

    return {
        "api_fixture_id": fixture.get("id"),
        "date": fixture.get("date"),
        "team_home": home.get("name"),
        "team_away": away.get("name"),
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
def get_fixture_xg(fixture_id: int) -> tuple[float | None, float | None]:
    payload = _get("/fixtures/statistics", {"fixture": fixture_id})
    xg_home = xg_away = None
    for block in payload.get("response", []):
        team_side = "home" if block.get("team", {}).get("id") else "away"
        for stat in block.get("statistics", []):
            if stat.get("type") == "expected_goals":
                value = stat.get("value")
                if isinstance(value, str):
                    value = float(value) if value else None
                if team_side == "home":
                    xg_home = value
                else:
                    xg_away = value
    return xg_home, xg_away


def get_fixtures(round_name: str, stage: str = "knockout") -> list[dict[str, Any]]:
    params = {
        "league": config.API_FOOTBALL_WC_ID,
        "season": config.API_FOOTBALL_SEASON,
        "round": round_name,
    }
    payload = _get("/fixtures", params)
    fixtures = [_normalize_fixture(item, stage=stage) for item in payload.get("response", [])]

    for match in fixtures:
        if match["status"] in ("FT", "PEN", "AET") and match.get("api_fixture_id"):
            try:
                xg_home, xg_away = get_fixture_xg(match["api_fixture_id"])
                match["xg_home"] = xg_home
                match["xg_away"] = xg_away
            except Exception as exc:
                logger.warning("xG unavailable for fixture %s: %s", match["api_fixture_id"], exc)

    return fixtures


def get_player_stats(api_team_id: int) -> list[dict[str, Any]]:
    params = {
        "league": config.API_FOOTBALL_WC_ID,
        "season": config.API_FOOTBALL_SEASON,
        "team": api_team_id,
    }
    payload = _get("/players", params)
    players: list[dict[str, Any]] = []
    for block in payload.get("response", []):
        player = block.get("player", {})
        stats = (block.get("statistics") or [{}])[0]
        games = stats.get("games") or {}
        goals = stats.get("goals") or {}
        minutes = games.get("minutes") or 0
        played = max(minutes / 90.0, 0.01)
        players.append({
            "player_id": player.get("id"),
            "name": player.get("name"),
            "position": games.get("position"),
            "goals": goals.get("total") or 0,
            "assists": goals.get("assists") or 0,
            "xg_per90": 0.0,
            "xa_per90": 0.0,
            "is_starting_xi": games.get("appearences", 0) >= 2,
        })
    return players


def get_injuries(api_team_id: int) -> list[dict[str, Any]]:
    params = {
        "league": config.API_FOOTBALL_WC_ID,
        "season": config.API_FOOTBALL_SEASON,
        "team": api_team_id,
    }
    payload = _get("/injuries", params)
    injuries: list[dict[str, Any]] = []
    for item in payload.get("response", []):
        player = item.get("player", {})
        injuries.append({
            "player_id": player.get("id"),
            "name": player.get("name"),
            "status": player.get("type", "Missing Fixture"),
            "reason": player.get("reason"),
            "is_starting_xi": True,
        })
    return injuries


def validate_raw_data(fixtures: list[dict[str, Any]], teams_remaining: int) -> None:
    if teams_remaining < 16:
        raise DataValidationError(f"Expected at least 16 teams remaining, got {teams_remaining}")

    incomplete = [f for f in fixtures if f.get("status") not in ("FT", "PEN", "AET", "NS")]
    if incomplete:
        logger.warning("%d fixtures have unexpected status", len(incomplete))

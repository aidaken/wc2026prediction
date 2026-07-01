"""Betting market implied probability converter."""

from __future__ import annotations

import logging
import os
from typing import Any

import requests

import config
from src.utils import retry

logger = logging.getLogger("wc2026")

# Maps Odds API team names to internal IDs
ODDS_NAME_TO_ID: dict[str, str] = {
    "Brazil": "BRA",
    "France": "FRA",
    "Argentina": "ARG",
    "Spain": "ESP",
    "England": "ENG",
    "Germany": "GER",
    "Portugal": "POR",
    "Netherlands": "NED",
    "Belgium": "BEL",
    "Italy": "ITA",
    "Croatia": "CRO",
    "Uruguay": "URU",
    "Colombia": "COL",
    "Mexico": "MEX",
    "USA": "USA",
    "United States": "USA",
    "Canada": "CAN",
    "Japan": "JPN",
    "South Korea": "KOR",
    "Korea Republic": "KOR",
    "Australia": "AUS",
    "Morocco": "MAR",
    "Senegal": "SEN",
    "Nigeria": "NGA",
    "Switzerland": "SUI",
    "Denmark": "DEN",
    "Norway": "NOR",
    "Poland": "POL",
    "Austria": "AUT",
    "Scotland": "SCO",
    "Ukraine": "UKR",
    "Turkey": "TUR",
    "Paraguay": "PAR",
    "Ecuador": "ECU",
    "Costa Rica": "CRC",
}


@retry(max_attempts=2)
def _fetch_odds() -> list[dict[str, Any]]:
    api_key = os.getenv("ODDS_API_KEY", "").strip()
    if not api_key:
        return []
    url = f"{config.ODDS_API_BASE}/sports/{config.ODDS_SPORT_KEY}/odds"
    params = {
        "apiKey": api_key,
        "regions": "eu",
        "markets": "outrights",
        "oddsFormat": "decimal",
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def get_implied_probs(active_team_ids: list[str]) -> dict[str, float] | None:
    """
    Fetch tournament winner odds and return normalized implied probabilities.
    Returns None if Odds API is unavailable.
    """
    try:
        events = _fetch_odds()
        if not events:
            logger.warning("OddsAPI unavailable, skipping betting signal")
            return None

        raw_probs: dict[str, list[float]] = {}
        for event in events:
            for bookmaker in event.get("bookmakers", []):
                for market in bookmaker.get("markets", []):
                    if market.get("key") != "outrights":
                        continue
                    for outcome in market.get("outcomes", []):
                        name = outcome.get("name", "")
                        price = outcome.get("price")
                        team_id = ODDS_NAME_TO_ID.get(name)
                        if not team_id or not price or price <= 1:
                            continue
                        raw_probs.setdefault(team_id, []).append(1.0 / price)

        averaged: dict[str, float] = {}
        for tid, probs in raw_probs.items():
            averaged[tid] = sum(probs) / len(probs)

        if not averaged:
            return None

        total = sum(averaged.values())
        normalized = {tid: prob / total for tid, prob in averaged.items() if tid in active_team_ids}
        return normalized or None
    except Exception as exc:
        logger.warning("OddsAPI fetch failed: %s", exc)
        return None

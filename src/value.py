"""Transfermarkt squad value scraper."""

from __future__ import annotations

import logging
import re
import time
from typing import Any

import requests
from bs4 import BeautifulSoup

import config
from src.teams import TM_SLUG_TO_ID
from src.utils import DATA_DIR, load_json, retry

logger = logging.getLogger("wc2026")

MANUAL_VALUES_PATH = DATA_DIR / "squad_values.json"


def load_manual_values() -> dict[str, int]:
    """Pinned Transfermarkt values from data/squad_values.json (scrape URL is dead)."""
    doc = load_json(MANUAL_VALUES_PATH)
    raw = doc.get("values_eur", {})
    out: dict[str, int] = {}
    for tid, val in raw.items():
        try:
            out[tid] = int(val)
        except (TypeError, ValueError):
            continue
    return out

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}

def _parse_market_value(raw: str) -> int | None:
    if not raw:
        return None
    raw = raw.strip().lower().replace("€", "").replace(",", ".")
    multiplier = 1
    if "bn" in raw or "mrd" in raw:
        multiplier = 1_000_000_000
        raw = re.sub(r"[^0-9.]", "", raw)
    elif "m" in raw:
        multiplier = 1_000_000
        raw = re.sub(r"[^0-9.]", "", raw)
    elif "k" in raw or "th." in raw:
        multiplier = 1_000
        raw = re.sub(r"[^0-9.]", "", raw)
    else:
        raw = re.sub(r"[^0-9.]", "", raw)
    try:
        return int(float(raw) * multiplier)
    except ValueError:
        return None


@retry(max_attempts=2)
def _fetch_page() -> str:
    response = requests.get(config.TRANSFERMARKT_WC_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


def get_squad_values(
    teams: dict[str, dict[str, Any]],
    fallback: dict[str, dict[str, Any]] | None = None,
) -> dict[str, int]:
    """Return squad_value_eur per team_id. Falls back to teams.json on failure."""
    fallback = fallback or teams
    values: dict[str, int] = {}

    try:
        html = _fetch_page()
        soup = BeautifulSoup(html, "lxml")
        rows = soup.select("table.items tbody tr")
        for row in rows:
            link = row.select_one("td.hauptlink a")
            value_cell = row.select_one("[data-market-value]")
            if not link or not value_cell:
                continue
            href = link.get("href", "")
            slug = href.split("/")[-1] if href else ""
            team_id = TM_SLUG_TO_ID.get(slug)
            if not team_id:
                for key, tid in TM_SLUG_TO_ID.items():
                    if key in href:
                        team_id = tid
                        break
            if not team_id:
                continue
            raw_value = value_cell.get("data-market-value") or value_cell.get_text(strip=True)
            parsed = _parse_market_value(str(raw_value))
            if parsed:
                values[team_id] = parsed
            time.sleep(config.TRANSFERMARKT_DELAY_S)
    except Exception as exc:
        logger.warning("Transfermarkt scrape failed: %s — using pinned/cached values", exc)

    # Precedence: live scrape > pinned data/squad_values.json > cached teams.json
    manual = load_manual_values()
    filled_manual = 0
    for tid in teams:
        if tid in values:
            continue
        if tid in manual:
            values[tid] = manual[tid]
            filled_manual += 1
    if filled_manual:
        logger.info("Squad values: %d pinned from data/squad_values.json", filled_manual)

    for tid, team in teams.items():
        if tid in values:
            continue
        cached = fallback.get(tid, {}).get("squad_value_eur")
        if cached:
            values[tid] = cached

    return values

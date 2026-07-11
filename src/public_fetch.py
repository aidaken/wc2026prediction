"""Pull WC 2026 results from public sources (Wikipedia) — no API key needed."""

from __future__ import annotations

import logging
import re
import time
from typing import Any

import requests
from bs4 import BeautifulSoup

from src.teams import TeamRegistry, build_name_map
from src.utils import DATA_DIR, load_json, write_json

logger = logging.getLogger("wc2026")

WIKI_API = "https://en.wikipedia.org/w/api.php"
USER_AGENT = "wc2026prediction/1.2 (https://github.com/aidaken/wc2026prediction; educational)"
GROUP_LETTERS = list("ABCDEFGHIJKL")

KNOCKOUT_SECTIONS = {
    "round_of_32": ("2026 FIFA World Cup knockout stage", "5"),
    "round_of_16": ("2026 FIFA World Cup knockout stage", "6"),
    "quarter_finals": ("2026 FIFA World Cup knockout stage", "15"),
}

SCORE_RE = re.compile(r"(\d+)\s*[–-]\s*(\d+)")


def _wiki_html(page: str, section: str | None = None) -> BeautifulSoup:
    params: dict[str, str] = {
        "action": "parse",
        "page": page,
        "format": "json",
        "prop": "text",
    }
    if section:
        params["section"] = section
    response = requests.get(
        WIKI_API,
        params=params,
        headers={"User-Agent": USER_AGENT},
        timeout=45,
    )
    response.raise_for_status()
    html = response.json()["parse"]["text"]["*"]
    return BeautifulSoup(html, "lxml")


def _team_label(cell) -> str:
    link = cell.select_one("a")
    return (link or cell).get_text(" ", strip=True)


def _parse_fevent(table) -> dict[str, Any] | None:
    home_cell = table.select_one("th.fhome")
    away_cell = table.select_one("th.faway")
    score_cell = table.select_one("th.fscore")
    if not home_cell or not away_cell or not score_cell:
        return None

    home = _team_label(home_cell)
    away = _team_label(away_cell)
    score_raw = score_cell.get_text(" ", strip=True)

    if "match" in score_raw.lower():
        return None

    m = SCORE_RE.search(score_raw)
    if not m:
        return None

    score_home = int(m.group(1))
    score_away = int(m.group(2))
    lower = score_raw.lower()
    status = "FT"
    if "a.e.t" in lower or "aet" in lower:
        status = "AET"

    penalties_home = penalties_away = None
    if "penalt" in table.get_text(" ", strip=True).lower():
        status = "PEN"
        for line in table.get_text("\n", strip=True).splitlines():
            pm = SCORE_RE.fullmatch(line.strip())
            if pm and len(line.strip()) <= 7:
                penalties_home = int(pm.group(1))
                penalties_away = int(pm.group(2))
                break

    winner = home if score_home > score_away else away if score_away > score_home else None
    if status == "PEN" and penalties_home is not None and penalties_away is not None:
        winner = home if penalties_home > penalties_away else away

    return {
        "team_home_name": home,
        "team_away_name": away,
        "score_home": score_home,
        "score_away": score_away,
        "penalties_home": penalties_home,
        "penalties_away": penalties_away,
        "winner_name": winner,
        "status": status,
    }


def _resolve(registry: TeamRegistry, name: str) -> str | None:
    tid = registry.resolve(name)
    if tid:
        return tid
    for alias, team_id in build_name_map(registry.teams).items():
        if alias.lower() == name.lower():
            return team_id
    return None


def _to_fixture(parsed: dict[str, Any], registry: TeamRegistry, *, stage: str) -> dict[str, Any] | None:
    home = _resolve(registry, parsed["team_home_name"])
    away = _resolve(registry, parsed["team_away_name"])
    if not home or not away:
        logger.warning("Unknown team(s): %s vs %s", parsed["team_home_name"], parsed["team_away_name"])
        return None

    winner = _resolve(registry, parsed["winner_name"]) if parsed.get("winner_name") else None
    if not winner and parsed["status"] in ("FT", "AET", "PEN"):
        if parsed["score_home"] > parsed["score_away"]:
            winner = home
        elif parsed["score_away"] > parsed["score_home"]:
            winner = away
        elif parsed.get("penalties_home") is not None:
            winner = home if parsed["penalties_home"] > parsed["penalties_away"] else away

    return {
        "team_home": home,
        "team_away": away,
        "score_home": parsed["score_home"],
        "score_away": parsed["score_away"],
        "penalties_home": parsed.get("penalties_home"),
        "penalties_away": parsed.get("penalties_away"),
        "winner": winner,
        "status": parsed["status"],
        "stage": stage,
    }


def fetch_group_fixtures(registry: TeamRegistry) -> list[dict[str, Any]]:
    fixtures: list[dict[str, Any]] = []
    for letter in GROUP_LETTERS:
        page = f"2026 FIFA World Cup Group {letter}"
        try:
            soup = _wiki_html(page)
        except Exception as exc:
            logger.warning("Group %s fetch failed: %s", letter, exc)
            continue
        for table in soup.select("table.fevent"):
            parsed = _parse_fevent(table)
            if not parsed:
                continue
            fix = _to_fixture(parsed, registry, stage="group")
            if fix:
                fixtures.append(fix)
        time.sleep(0.35)
    logger.info("Wikipedia groups: %d matches", len(fixtures))
    return fixtures


def fetch_knockout_fixtures(registry: TeamRegistry) -> list[dict[str, Any]]:
    fixtures: list[dict[str, Any]] = []
    for round_key, (page, section) in KNOCKOUT_SECTIONS.items():
        try:
            soup = _wiki_html(page, section=section)
        except Exception as exc:
            logger.warning("Knockout %s fetch failed: %s", round_key, exc)
            continue
        for table in soup.select("table.fevent"):
            parsed = _parse_fevent(table)
            if not parsed:
                continue
            fix = _to_fixture(parsed, registry, stage="knockout")
            if fix:
                fix["round_key"] = round_key
                fixtures.append(fix)
        time.sleep(0.35)
    logger.info("Wikipedia knockouts: %d matches", len(fixtures))
    return fixtures


def _pair_key(home: str, away: str) -> tuple[str, str]:
    return tuple(sorted((home, away)))


def apply_knockout_to_bracket(
    bracket: dict[str, Any],
    fixtures: list[dict[str, Any]],
) -> int:
    """Merge knockout fixtures into bracket.json by team pairing. Returns update count."""
    by_round: dict[str, dict[tuple[str, str], dict[str, Any]]] = {}
    for fix in fixtures:
        if fix.get("stage") != "knockout":
            continue
        rk = fix.get("round_key")
        if not rk:
            continue
        by_round.setdefault(rk, {})[_pair_key(fix["team_home"], fix["team_away"])] = fix

    updated = 0
    rounds = bracket.setdefault("rounds", {})
    for round_key, pair_map in by_round.items():
        round_data = rounds.setdefault(round_key, {"matches": []})
        for match in round_data.get("matches", []):
            home, away = match.get("team_home"), match.get("team_away")
            if not home or not away:
                continue
            fix = pair_map.get(_pair_key(home, away))
            if not fix:
                continue
            match["score_home"] = fix["score_home"]
            match["score_away"] = fix["score_away"]
            match["penalties_home"] = fix.get("penalties_home")
            match["penalties_away"] = fix.get("penalties_away")
            match["winner"] = fix["winner"]
            match["status"] = fix["status"]
            match["stage"] = "knockout"
            updated += 1
    return updated


def save_public_fixtures(all_fixtures: list[dict[str, Any]]) -> None:
    path = DATA_DIR / "fixtures_cache.json"
    write_json(path, {
        "_meta": {
            "source": "wikipedia",
            "count": len(all_fixtures),
        },
        "fixtures": all_fixtures,
    })


def load_manual_odds() -> dict[str, float] | None:
    path = DATA_DIR / "manual_odds.json"
    if not path.exists():
        return None
    doc = load_json(path)
    odds = doc.get("odds") or doc
    if not isinstance(odds, dict) or not odds:
        return None
    return {str(k): float(v) for k, v in odds.items() if v}


def run_public_fetch(
    registry: TeamRegistry,
    bracket: dict[str, Any],
    *,
    write_cache: bool = True,
) -> dict[str, Any]:
    groups = fetch_group_fixtures(registry)
    knockouts = fetch_knockout_fixtures(registry)
    all_fixtures = groups + knockouts
    bracket_updates = apply_knockout_to_bracket(bracket, knockouts)
    if write_cache:
        save_public_fixtures(all_fixtures)
    return {
        "group_matches": len(groups),
        "knockout_matches": len(knockouts),
        "bracket_rows_updated": bracket_updates,
    }

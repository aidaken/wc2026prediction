"""Central team registry — single source for all team ID / name mappings."""

from __future__ import annotations

from typing import Any

from src.seed import TEAMS

# Extra name variants used by Odds API, API-Football, or bookmakers
# (canonical names come from TEAMS; only add aliases here)
EXTRA_ALIASES: dict[str, str] = {
    "USA": "USA",
    "United States": "USA",
    "South Korea": "KOR",
    "Korea Republic": "KOR",
    "Turkey": "TUR",
    "Ivory Coast": "CIV",
    "Côte d'Ivoire": "CIV",
    "DR Congo": "COD",
    "Congo DR": "COD",
    "Democratic Republic of the Congo": "COD",
    "Cape Verde": "CPV",
    "Cabo Verde": "CPV",
    "IR Iran": "IRN",
    "Curaçao": "CUW",
    "Curacao": "CUW",
    "Bosnia and Herzegovina": "BIH",
    "Bosnia-Herzegovina": "BIH",
    "Bosnia & Herzegovina": "BIH",
    "Czech Republic": "CZE",
}


def build_name_map(teams: dict[str, dict[str, Any]] | None = None) -> dict[str, str]:
    """Map display names and aliases → internal team ID (WC 2026 squads only)."""
    teams = teams or TEAMS
    mapping = {team["name"]: tid for tid, team in teams.items()}
    mapping.update(EXTRA_ALIASES)
    return mapping


def build_transfermarkt_map(teams: dict[str, dict[str, Any]] | None = None) -> dict[str, str]:
    """Map Transfermarkt URL slugs → internal team ID."""
    teams = teams or TEAMS
    return {
        team["transfermarkt_id"]: tid
        for tid, team in teams.items()
        if team.get("transfermarkt_id")
    }


# Module-level maps derived from seed data (48 WC 2026 teams)
ODDS_NAME_TO_ID = build_name_map()
TM_SLUG_TO_ID = build_transfermarkt_map()


class TeamRegistry:
    def __init__(self, teams: dict[str, dict[str, Any]] | None = None):
        self.teams = teams or TEAMS
        self._by_api_id: dict[int, str] = {}
        self._by_name: dict[str, str] = {}
        self._rebuild()

    def _rebuild(self) -> None:
        self._by_api_id.clear()
        self._by_name.clear()
        for tid, team in self.teams.items():
            self._by_name[tid] = tid
            self._by_name[team.get("name", "")] = tid
            api_id = team.get("api_football_id")
            if api_id:
                self._by_api_id[int(api_id)] = tid
        self._by_name.update(build_name_map(self.teams))

    def resolve(self, value: str | int | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, int):
            return self._by_api_id.get(value)
        if value in self._by_name:
            return self._by_name[value]
        return None

    def name(self, team_id: str) -> str:
        return self.teams.get(team_id, {}).get("name", team_id)

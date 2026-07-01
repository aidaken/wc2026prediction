"""Central team registry — maps API-Football IDs and names to internal 3-letter codes."""

from __future__ import annotations

from typing import Any

from src.seed import TEAMS

NAME_ALIASES: dict[str, str] = {
    "Brazil": "BRA", "France": "FRA", "Argentina": "ARG", "Spain": "ESP", "England": "ENG",
    "Germany": "GER", "Portugal": "POR", "Netherlands": "NED", "USA": "USA", "United States": "USA",
    "Mexico": "MEX", "Canada": "CAN", "Morocco": "MAR", "Senegal": "SEN", "Japan": "JPN",
    "South Korea": "KOR", "Korea Republic": "KOR", "Uruguay": "URU", "Colombia": "COL",
    "Belgium": "BEL", "Croatia": "CRO", "Switzerland": "SUI", "Norway": "NOR", "Poland": "POL",
    "Austria": "AUT", "Scotland": "SCO", "Turkey": "TUR", "Türkiye": "TUR", "Paraguay": "PAR",
    "Ecuador": "ECU", "Australia": "AUS", "Nigeria": "NGA", "Czechia": "CZE", "Czech Republic": "CZE",
    "Bosnia and Herzegovina": "BIH", "Bosnia-Herzegovina": "BIH", "South Africa": "RSA",
    "Ivory Coast": "CIV", "Côte d'Ivoire": "CIV", "DR Congo": "COD", "Congo DR": "COD",
    "Cape Verde": "CPV", "Cabo Verde": "CPV", "Saudi Arabia": "KSA", "Egypt": "EGY",
    "Algeria": "ALG", "Ghana": "GHA", "Iraq": "IRQ", "Jordan": "JOR", "Qatar": "QAT",
    "Iran": "IRN", "IR Iran": "IRN", "Uzbekistan": "UZB", "Panama": "PAN", "Haiti": "HTI",
    "Curaçao": "CUW", "Curacao": "CUW", "Tunisia": "TUN", "New Zealand": "NZL",
    "Sweden": "SWE", "Bosnia & Herzegovina": "BIH",
}


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
        for name, tid in NAME_ALIASES.items():
            self._by_name[name] = tid

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

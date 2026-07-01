"""Demo / seed data for offline runs without API keys."""

from __future__ import annotations

from typing import Any

# Internal team registry — 32 teams at Round of 32
TEAMS: dict[str, dict[str, Any]] = {
    "BRA": {"id": "BRA", "name": "Brazil", "api_football_id": 6, "transfermarkt_id": "brasilien", "elo": 2062.0, "squad_value_eur": 1180000000, "eliminated": False, "group": "D", "group_position": 1},
    "FRA": {"id": "FRA", "name": "France", "api_football_id": 2, "transfermarkt_id": "frankreich", "elo": 2018.0, "squad_value_eur": 1050000000, "eliminated": False, "group": "E", "group_position": 1},
    "ARG": {"id": "ARG", "name": "Argentina", "api_football_id": 26, "transfermarkt_id": "argentinien", "elo": 1995.0, "squad_value_eur": 820000000, "eliminated": False, "group": "J", "group_position": 1},
    "ESP": {"id": "ESP", "name": "Spain", "api_football_id": 9, "transfermarkt_id": "spanien", "elo": 1988.0, "squad_value_eur": 980000000, "eliminated": False, "group": "B", "group_position": 1},
    "ENG": {"id": "ENG", "name": "England", "api_football_id": 10, "transfermarkt_id": "england", "elo": 1965.0, "squad_value_eur": 1400000000, "eliminated": False, "group": "C", "group_position": 1},
    "GER": {"id": "GER", "name": "Germany", "api_football_id": 25, "transfermarkt_id": "deutschland", "elo": 1920.0, "squad_value_eur": 890000000, "eliminated": True, "group": "A", "group_position": 2},
    "POR": {"id": "POR", "name": "Portugal", "api_football_id": 27, "transfermarkt_id": "portugal", "elo": 1910.0, "squad_value_eur": 760000000, "eliminated": False, "group": "F", "group_position": 1},
    "NED": {"id": "NED", "name": "Netherlands", "api_football_id": 1118, "transfermarkt_id": "niederlande", "elo": 1905.0, "squad_value_eur": 780000000, "eliminated": False, "group": "G", "group_position": 1},
    "USA": {"id": "USA", "name": "USA", "api_football_id": 2384, "transfermarkt_id": "usa", "elo": 1780.0, "squad_value_eur": 420000000, "eliminated": False, "group": "H", "group_position": 1},
    "MEX": {"id": "MEX", "name": "Mexico", "api_football_id": 16, "transfermarkt_id": "mexiko", "elo": 1765.0, "squad_value_eur": 210000000, "eliminated": False, "group": "I", "group_position": 1},
    "CAN": {"id": "CAN", "name": "Canada", "api_football_id": 5529, "transfermarkt_id": "kanada", "elo": 1680.0, "squad_value_eur": 185000000, "eliminated": False, "group": "K", "group_position": 2},
    "MAR": {"id": "MAR", "name": "Morocco", "api_football_id": 31, "transfermarkt_id": "marokko", "elo": 1845.0, "squad_value_eur": 380000000, "eliminated": False, "group": "L", "group_position": 1},
    "SEN": {"id": "SEN", "name": "Senegal", "api_football_id": 13, "transfermarkt_id": "senegal", "elo": 1770.0, "squad_value_eur": 290000000, "eliminated": False, "group": "M", "group_position": 1},
    "JPN": {"id": "JPN", "name": "Japan", "api_football_id": 12, "transfermarkt_id": "japan", "elo": 1810.0, "squad_value_eur": 320000000, "eliminated": False, "group": "N", "group_position": 1},
    "KOR": {"id": "KOR", "name": "South Korea", "api_football_id": 17, "transfermarkt_id": "sudkorea", "elo": 1740.0, "squad_value_eur": 195000000, "eliminated": False, "group": "O", "group_position": 2},
    "URU": {"id": "URU", "name": "Uruguay", "api_football_id": 7, "transfermarkt_id": "uruguay", "elo": 1860.0, "squad_value_eur": 410000000, "eliminated": False, "group": "P", "group_position": 1},
    "COL": {"id": "COL", "name": "Colombia", "api_football_id": 8, "transfermarkt_id": "kolumbien", "elo": 1830.0, "squad_value_eur": 350000000, "eliminated": True, "group": "Q", "group_position": 2},
    "BEL": {"id": "BEL", "name": "Belgium", "api_football_id": 1, "transfermarkt_id": "belgien", "elo": 1880.0, "squad_value_eur": 450000000, "eliminated": True, "group": "R", "group_position": 2},
    "CRO": {"id": "CRO", "name": "Croatia", "api_football_id": 3, "transfermarkt_id": "kroatien", "elo": 1855.0, "squad_value_eur": 280000000, "eliminated": True, "group": "S", "group_position": 2},
    "SUI": {"id": "SUI", "name": "Switzerland", "api_football_id": 15, "transfermarkt_id": "schweiz", "elo": 1800.0, "squad_value_eur": 260000000, "eliminated": False, "group": "T", "group_position": 2},
    "DEN": {"id": "DEN", "name": "Denmark", "api_football_id": 21, "transfermarkt_id": "danemark", "elo": 1790.0, "squad_value_eur": 340000000, "eliminated": True, "group": "U", "group_position": 3},
    "NOR": {"id": "NOR", "name": "Norway", "api_football_id": 1090, "transfermarkt_id": "norwegen", "elo": 1755.0, "squad_value_eur": 370000000, "eliminated": True, "group": "V", "group_position": 3},
    "AUS": {"id": "AUS", "name": "Australia", "api_football_id": 20, "transfermarkt_id": "australien", "elo": 1720.0, "squad_value_eur": 95000000, "eliminated": True, "group": "W", "group_position": 3},
    "NGA": {"id": "NGA", "name": "Nigeria", "api_football_id": 19, "transfermarkt_id": "nigeria", "elo": 1710.0, "squad_value_eur": 220000000, "eliminated": True, "group": "X", "group_position": 3},
    "ECU": {"id": "ECU", "name": "Ecuador", "api_football_id": 2389, "transfermarkt_id": "ecuador", "elo": 1735.0, "squad_value_eur": 180000000, "eliminated": True, "group": "Y", "group_position": 3},
    "POL": {"id": "POL", "name": "Poland", "api_football_id": 24, "transfermarkt_id": "polen", "elo": 1705.0, "squad_value_eur": 210000000, "eliminated": True, "group": "Z", "group_position": 3},
    "AUT": {"id": "AUT", "name": "Austria", "api_football_id": 775, "transfermarkt_id": "osterreich", "elo": 1785.0, "squad_value_eur": 240000000, "eliminated": True, "group": "AA", "group_position": 3},
    "SCO": {"id": "SCO", "name": "Scotland", "api_football_id": 1108, "transfermarkt_id": "schottland", "elo": 1690.0, "squad_value_eur": 175000000, "eliminated": True, "group": "AB", "group_position": 3},
    "UKR": {"id": "UKR", "name": "Ukraine", "api_football_id": 772, "transfermarkt_id": "ukraine", "elo": 1760.0, "squad_value_eur": 200000000, "eliminated": True, "group": "AC", "group_position": 3},
    "TUR": {"id": "TUR", "name": "Turkey", "api_football_id": 777, "transfermarkt_id": "turkei", "elo": 1745.0, "squad_value_eur": 230000000, "eliminated": True, "group": "AD", "group_position": 3},
    "PAR": {"id": "PAR", "name": "Paraguay", "api_football_id": 2379, "transfermarkt_id": "paraguay", "elo": 1675.0, "squad_value_eur": 120000000, "eliminated": True, "group": "AE", "group_position": 3},
    "CRC": {"id": "CRC", "name": "Costa Rica", "api_football_id": 29, "transfermarkt_id": "costa-rica", "elo": 1650.0, "squad_value_eur": 85000000, "eliminated": True, "group": "AF", "group_position": 3},
}

DEMO_FIXTURES: list[dict[str, Any]] = [
    {"team_home": "CAN", "team_away": "COL", "status": "FT", "winner": "CAN", "score_home": 1, "score_away": 0, "xg_home": 1.42, "xg_away": 0.67, "date": "2026-06-28T19:00:00Z", "stage": "knockout"},
    {"team_home": "BRA", "team_away": "KOR", "status": "FT", "winner": "BRA", "score_home": 3, "score_away": 1, "xg_home": 2.8, "xg_away": 0.9, "date": "2026-06-28T21:00:00Z", "stage": "knockout"},
    {"team_home": "FRA", "team_away": "ARG", "status": "FT", "winner": "FRA", "score_home": 2, "score_away": 1, "xg_home": 1.9, "xg_away": 1.4, "date": "2026-06-29T18:00:00Z", "stage": "knockout"},
    {"team_home": "ENG", "team_away": "SEN", "status": "FT", "winner": "ENG", "score_home": 2, "score_away": 0, "xg_home": 2.1, "xg_away": 0.5, "date": "2026-06-29T20:00:00Z", "stage": "knockout"},
    {"team_home": "ESP", "team_away": "GER", "status": "FT", "winner": "ESP", "score_home": 1, "score_away": 0, "xg_home": 1.3, "xg_away": 0.8, "date": "2026-06-30T18:00:00Z", "stage": "knockout"},
    {"team_home": "NED", "team_away": "USA", "status": "FT", "winner": "NED", "score_home": 2, "score_away": 1, "xg_home": 1.7, "xg_away": 1.2, "date": "2026-06-30T20:00:00Z", "stage": "knockout"},
    {"team_home": "POR", "team_away": "URU", "status": "FT", "winner": "POR", "score_home": 1, "score_away": 0, "xg_home": 1.1, "xg_away": 0.9, "date": "2026-07-01T18:00:00Z", "stage": "knockout"},
    {"team_home": "MEX", "team_away": "JPN", "status": "FT", "winner": "MEX", "score_home": 2, "score_away": 1, "xg_home": 1.5, "xg_away": 1.3, "date": "2026-07-01T20:00:00Z", "stage": "knockout"},
    {"team_home": "BRA", "team_away": "FRA", "status": "FT", "winner": "BRA", "score_home": 2, "score_away": 1, "xg_home": 2.0, "xg_away": 1.5, "date": "2026-06-15", "stage": "group"},
    {"team_home": "ESP", "team_away": "ENG", "status": "FT", "winner": "ESP", "score_home": 1, "score_away": 1, "xg_home": 1.4, "xg_away": 1.3, "date": "2026-06-18", "stage": "group"},
    {"team_home": "ARG", "team_away": "NED", "status": "FT", "winner": "ARG", "score_home": 2, "score_away": 0, "xg_home": 1.8, "xg_away": 0.7, "date": "2026-06-20", "stage": "group"},
]

DEMO_INJURIES: dict[str, list[dict[str, Any]]] = {
    "FRA": [{"player_id": 276, "name": "Kylian Mbappé", "status": "Missing Fixture", "is_starting_xi": True, "position": "Attacker", "xg_per90": 0.55, "xa_per90": 0.12}],
}

DEMO_PLAYER_STATS: dict[str, list[dict[str, Any]]] = {
    "FRA": [{"player_id": 276, "name": "Kylian Mbappé", "position": "Attacker", "xg_per90": 0.55, "xa_per90": 0.12, "is_starting_xi": True}],
}

DEMO_ODDS: dict[str, float] = {
    "BRA": 0.22, "FRA": 0.18, "ARG": 0.14, "ESP": 0.12, "ENG": 0.10,
    "POR": 0.06, "NED": 0.05, "USA": 0.03, "MEX": 0.02, "MAR": 0.02,
    "SEN": 0.02, "JPN": 0.02, "KOR": 0.01, "URU": 0.01, "CAN": 0.01,
}

DEMO_BRACKET: dict[str, Any] = {
    "_meta": {"current_round": "Round of 16", "wc_year": 2026},
    "rounds": {
        "round_of_32": {
            "status": "completed",
            "matches": [
                {"match_id": "r32_m01", "date": "2026-06-28T19:00:00Z", "team_home": "CAN", "team_away": "COL", "score_home": 1, "score_away": 0, "winner": "CAN", "xg_home": 1.42, "xg_away": 0.67, "status": "FT"},
                {"match_id": "r32_m02", "date": "2026-06-28T21:00:00Z", "team_home": "BRA", "team_away": "KOR", "score_home": 3, "score_away": 1, "winner": "BRA", "xg_home": 2.8, "xg_away": 0.9, "status": "FT"},
                {"match_id": "r32_m03", "date": "2026-06-29T18:00:00Z", "team_home": "FRA", "team_away": "BEL", "score_home": 2, "score_away": 0, "winner": "FRA", "xg_home": 2.0, "xg_away": 0.6, "status": "FT"},
                {"match_id": "r32_m04", "date": "2026-06-29T20:00:00Z", "team_home": "ENG", "team_away": "SEN", "score_home": 2, "score_away": 0, "winner": "ENG", "xg_home": 2.1, "xg_away": 0.5, "status": "FT"},
                {"match_id": "r32_m05", "date": "2026-06-30T18:00:00Z", "team_home": "ESP", "team_away": "GER", "score_home": 1, "score_away": 0, "winner": "ESP", "xg_home": 1.3, "xg_away": 0.8, "status": "FT"},
                {"match_id": "r32_m06", "date": "2026-06-30T20:00:00Z", "team_home": "NED", "team_away": "USA", "score_home": 2, "score_away": 1, "winner": "NED", "xg_home": 1.7, "xg_away": 1.2, "status": "FT"},
                {"match_id": "r32_m07", "date": "2026-07-01T18:00:00Z", "team_home": "POR", "team_away": "URU", "score_home": 1, "score_away": 0, "winner": "POR", "xg_home": 1.1, "xg_away": 0.9, "status": "FT"},
                {"match_id": "r32_m08", "date": "2026-07-01T20:00:00Z", "team_home": "MEX", "team_away": "JPN", "score_home": 2, "score_away": 1, "winner": "MEX", "xg_home": 1.5, "xg_away": 1.3, "status": "FT"},
                {"match_id": "r32_m09", "team_home": "ARG", "team_away": "CRO", "score_home": 2, "score_away": 1, "winner": "ARG", "status": "FT"},
                {"match_id": "r32_m10", "team_home": "MAR", "team_away": "SUI", "score_home": 1, "score_away": 0, "winner": "MAR", "status": "FT"},
                {"match_id": "r32_m11", "team_home": "USA", "team_away": "ECU", "score_home": 2, "score_away": 0, "winner": "USA", "status": "FT"},
                {"match_id": "r32_m12", "team_home": "URU", "team_away": "DEN", "score_home": 1, "score_away": 1, "winner": "URU", "status": "FT"},
                {"match_id": "r32_m13", "team_home": "JPN", "team_away": "NOR", "score_home": 2, "score_away": 1, "winner": "JPN", "status": "FT"},
                {"match_id": "r32_m14", "team_home": "SEN", "team_away": "POL", "score_home": 2, "score_away": 0, "winner": "SEN", "status": "FT"},
                {"match_id": "r32_m15", "team_home": "KOR", "team_away": "AUS", "score_home": 1, "score_away": 0, "winner": "KOR", "status": "FT"},
                {"match_id": "r32_m16", "team_home": "CAN", "team_away": "AUT", "score_home": 1, "score_away": 0, "winner": "CAN", "status": "FT"},
            ],
        },
        "round_of_16": {
            "status": "in_progress",
            "matches": [
                {"match_id": "r16_m01", "date": "2026-07-04T18:00:00Z", "team_home": "CAN", "team_away": "MAR", "score_home": None, "score_away": None, "winner": None, "status": "NS"},
                {"match_id": "r16_m02", "date": "2026-07-04T21:00:00Z", "team_home": "BRA", "team_away": "KOR", "score_home": None, "score_away": None, "winner": None, "status": "NS"},
                {"match_id": "r16_m03", "date": "2026-07-05T18:00:00Z", "team_home": "FRA", "team_away": "ARG", "score_home": None, "score_away": None, "winner": None, "status": "NS"},
                {"match_id": "r16_m04", "date": "2026-07-05T21:00:00Z", "team_home": "ENG", "team_away": "SEN", "score_home": None, "score_away": None, "winner": None, "status": "NS"},
                {"match_id": "r16_m05", "date": "2026-07-06T18:00:00Z", "team_home": "ESP", "team_away": "NED", "score_home": None, "score_away": None, "winner": None, "status": "NS"},
                {"match_id": "r16_m06", "date": "2026-07-06T21:00:00Z", "team_home": "POR", "team_away": "USA", "score_home": None, "score_away": None, "winner": None, "status": "NS"},
                {"match_id": "r16_m07", "date": "2026-07-07T18:00:00Z", "team_home": "MEX", "team_away": "URU", "score_home": None, "score_away": None, "winner": None, "status": "NS"},
                {"match_id": "r16_m08", "date": "2026-07-07T21:00:00Z", "team_home": "JPN", "team_away": "SUI", "score_home": None, "score_away": None, "winner": None, "status": "NS"},
            ],
        },
        "quarter_finals": {
            "status": "pending",
            "matches": [
                {"match_id": "qf_m01", "team_home": None, "team_away": None, "winner": None, "status": "NS"},
                {"match_id": "qf_m02", "team_home": None, "team_away": None, "winner": None, "status": "NS"},
                {"match_id": "qf_m03", "team_home": None, "team_away": None, "winner": None, "status": "NS"},
                {"match_id": "qf_m04", "team_home": None, "team_away": None, "winner": None, "status": "NS"},
            ],
        },
        "semi_finals": {
            "status": "pending",
            "matches": [
                {"match_id": "sf_m01", "team_home": None, "team_away": None, "winner": None, "status": "NS"},
                {"match_id": "sf_m02", "team_home": None, "team_away": None, "winner": None, "status": "NS"},
            ],
        },
        "final": {
            "status": "pending",
            "matches": [
                {"match_id": "final_m01", "team_home": None, "team_away": None, "winner": None, "status": "NS"},
            ],
        },
    },
}

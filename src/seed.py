"""Demo / seed data — accurate FIFA World Cup 2026 teams and bracket (July 2026)."""

from __future__ import annotations

from typing import Any

# All 48 qualified nations with group-stage metadata
# Sources: FIFA.com, Wikipedia 2026 WC knockout stage (combination 67)
TEAMS: dict[str, dict[str, Any]] = {
    # Group A
    "MEX": {"id": "MEX", "name": "Mexico", "api_football_id": 16, "transfermarkt_id": "mexiko", "elo": 1810.0, "squad_value_eur": 210000000, "eliminated": False, "group": "A", "group_position": 1},
    "CZE": {"id": "CZE", "name": "Czechia", "api_football_id": 770, "transfermarkt_id": "tschechien", "elo": 1720.0, "squad_value_eur": 280000000, "eliminated": True, "group": "A", "group_position": 4},
    "RSA": {"id": "RSA", "name": "South Africa", "api_football_id": 1530, "transfermarkt_id": "suedafrika", "elo": 1680.0, "squad_value_eur": 95000000, "eliminated": True, "group": "A", "group_position": 2},
    "KOR": {"id": "KOR", "name": "South Korea", "api_football_id": 17, "transfermarkt_id": "sudkorea", "elo": 1745.0, "squad_value_eur": 195000000, "eliminated": True, "group": "A", "group_position": 3},
    # Group B
    "CAN": {"id": "CAN", "name": "Canada", "api_football_id": 5529, "transfermarkt_id": "kanada", "elo": 1765.0, "squad_value_eur": 185000000, "eliminated": False, "group": "B", "group_position": 2},
    "BIH": {"id": "BIH", "name": "Bosnia and Herzegovina", "api_football_id": 1113, "transfermarkt_id": "bosnien-herzegowina", "elo": 1710.0, "squad_value_eur": 120000000, "eliminated": False, "group": "B", "group_position": 3},
    "QAT": {"id": "QAT", "name": "Qatar", "api_football_id": 1569, "transfermarkt_id": "katar", "elo": 1650.0, "squad_value_eur": 15000000, "eliminated": True, "group": "B", "group_position": 4},
    "SUI": {"id": "SUI", "name": "Switzerland", "api_football_id": 15, "transfermarkt_id": "schweiz", "elo": 1840.0, "squad_value_eur": 260000000, "eliminated": False, "group": "B", "group_position": 1},
    # Group C
    "BRA": {"id": "BRA", "name": "Brazil", "api_football_id": 6, "transfermarkt_id": "brasilien", "elo": 2065.0, "squad_value_eur": 1180000000, "eliminated": False, "group": "C", "group_position": 1},
    "HTI": {"id": "HTI", "name": "Haiti", "api_football_id": 2386, "transfermarkt_id": "haiti", "elo": 1580.0, "squad_value_eur": 12000000, "eliminated": True, "group": "C", "group_position": 4},
    "MAR": {"id": "MAR", "name": "Morocco", "api_football_id": 31, "transfermarkt_id": "marokko", "elo": 1875.0, "squad_value_eur": 380000000, "eliminated": False, "group": "C", "group_position": 2},
    "SCO": {"id": "SCO", "name": "Scotland", "api_football_id": 1108, "transfermarkt_id": "schottland", "elo": 1725.0, "squad_value_eur": 175000000, "eliminated": True, "group": "C", "group_position": 3},
    # Group D
    "USA": {"id": "USA", "name": "USA", "api_football_id": 2384, "transfermarkt_id": "usa", "elo": 1795.0, "squad_value_eur": 420000000, "eliminated": False, "group": "D", "group_position": 1},
    "AUS": {"id": "AUS", "name": "Australia", "api_football_id": 20, "transfermarkt_id": "australien", "elo": 1735.0, "squad_value_eur": 95000000, "eliminated": False, "group": "D", "group_position": 2},
    "PAR": {"id": "PAR", "name": "Paraguay", "api_football_id": 2379, "transfermarkt_id": "paraguay", "elo": 1755.0, "squad_value_eur": 120000000, "eliminated": False, "group": "D", "group_position": 3},
    "TUR": {"id": "TUR", "name": "Türkiye", "api_football_id": 777, "transfermarkt_id": "turkei", "elo": 1780.0, "squad_value_eur": 230000000, "eliminated": True, "group": "D", "group_position": 4},
    # Group E
    "CUW": {"id": "CUW", "name": "Curaçao", "api_football_id": 5527, "transfermarkt_id": "curacao", "elo": 1550.0, "squad_value_eur": 8000000, "eliminated": True, "group": "E", "group_position": 1},
    "ECU": {"id": "ECU", "name": "Ecuador", "api_football_id": 2389, "transfermarkt_id": "ecuador", "elo": 1760.0, "squad_value_eur": 180000000, "eliminated": True, "group": "E", "group_position": 3},
    "GER": {"id": "GER", "name": "Germany", "api_football_id": 25, "transfermarkt_id": "deutschland", "elo": 1945.0, "squad_value_eur": 890000000, "eliminated": True, "group": "E", "group_position": 1},
    "CIV": {"id": "CIV", "name": "Ivory Coast", "api_football_id": 1501, "transfermarkt_id": "elfenbeinkueste", "elo": 1775.0, "squad_value_eur": 290000000, "eliminated": True, "group": "E", "group_position": 2},
    # Group F
    "NED": {"id": "NED", "name": "Netherlands", "api_football_id": 1118, "transfermarkt_id": "niederlande", "elo": 1925.0, "squad_value_eur": 780000000, "eliminated": True, "group": "F", "group_position": 1},
    "JPN": {"id": "JPN", "name": "Japan", "api_football_id": 12, "transfermarkt_id": "japan", "elo": 1820.0, "squad_value_eur": 320000000, "eliminated": True, "group": "F", "group_position": 2},
    "SWE": {"id": "SWE", "name": "Sweden", "api_football_id": 5, "transfermarkt_id": "schweden", "elo": 1805.0, "squad_value_eur": 350000000, "eliminated": True, "group": "F", "group_position": 3},
    "TUN": {"id": "TUN", "name": "Tunisia", "api_football_id": 28, "transfermarkt_id": "tunesien", "elo": 1700.0, "squad_value_eur": 65000000, "eliminated": True, "group": "F", "group_position": 4},
    # Group G
    "BEL": {"id": "BEL", "name": "Belgium", "api_football_id": 1, "transfermarkt_id": "belgien", "elo": 1895.0, "squad_value_eur": 450000000, "eliminated": False, "group": "G", "group_position": 1},
    "EGY": {"id": "EGY", "name": "Egypt", "api_football_id": 32, "transfermarkt_id": "aegypten", "elo": 1740.0, "squad_value_eur": 110000000, "eliminated": False, "group": "G", "group_position": 2},
    "IRN": {"id": "IRN", "name": "Iran", "api_football_id": 22, "transfermarkt_id": "iran", "elo": 1715.0, "squad_value_eur": 45000000, "eliminated": True, "group": "G", "group_position": 3},
    "NZL": {"id": "NZL", "name": "New Zealand", "api_football_id": 4673, "transfermarkt_id": "neuseeland", "elo": 1620.0, "squad_value_eur": 22000000, "eliminated": True, "group": "G", "group_position": 4},
    # Group H
    "CPV": {"id": "CPV", "name": "Cape Verde", "api_football_id": 5528, "transfermarkt_id": "kap-verde", "elo": 1695.0, "squad_value_eur": 35000000, "eliminated": False, "group": "H", "group_position": 2},
    "KSA": {"id": "KSA", "name": "Saudi Arabia", "api_football_id": 23, "transfermarkt_id": "saudi-arabien", "elo": 1685.0, "squad_value_eur": 38000000, "eliminated": True, "group": "H", "group_position": 3},
    "ESP": {"id": "ESP", "name": "Spain", "api_football_id": 9, "transfermarkt_id": "spanien", "elo": 1995.0, "squad_value_eur": 980000000, "eliminated": False, "group": "H", "group_position": 1},
    "URU": {"id": "URU", "name": "Uruguay", "api_football_id": 7, "transfermarkt_id": "uruguay", "elo": 1860.0, "squad_value_eur": 410000000, "eliminated": True, "group": "H", "group_position": 4},
    # Group I
    "FRA": {"id": "FRA", "name": "France", "api_football_id": 2, "transfermarkt_id": "frankreich", "elo": 2025.0, "squad_value_eur": 1050000000, "eliminated": False, "group": "I", "group_position": 1},
    "NOR": {"id": "NOR", "name": "Norway", "api_football_id": 1090, "transfermarkt_id": "norwegen", "elo": 1835.0, "squad_value_eur": 370000000, "eliminated": False, "group": "I", "group_position": 2},
    "SEN": {"id": "SEN", "name": "Senegal", "api_football_id": 13, "transfermarkt_id": "senegal", "elo": 1785.0, "squad_value_eur": 290000000, "eliminated": False, "group": "I", "group_position": 3},
    "IRQ": {"id": "IRQ", "name": "Iraq", "api_football_id": 1567, "transfermarkt_id": "irak", "elo": 1660.0, "squad_value_eur": 25000000, "eliminated": True, "group": "I", "group_position": 4},
    # Group J
    "ALG": {"id": "ALG", "name": "Algeria", "api_football_id": 1502, "transfermarkt_id": "algerien", "elo": 1750.0, "squad_value_eur": 85000000, "eliminated": False, "group": "J", "group_position": 3},
    "ARG": {"id": "ARG", "name": "Argentina", "api_football_id": 26, "transfermarkt_id": "argentinien", "elo": 2005.0, "squad_value_eur": 820000000, "eliminated": False, "group": "J", "group_position": 1},
    "AUT": {"id": "AUT", "name": "Austria", "api_football_id": 775, "transfermarkt_id": "osterreich", "elo": 1815.0, "squad_value_eur": 240000000, "eliminated": False, "group": "J", "group_position": 2},
    "JOR": {"id": "JOR", "name": "Jordan", "api_football_id": 1568, "transfermarkt_id": "jordanien", "elo": 1640.0, "squad_value_eur": 18000000, "eliminated": True, "group": "J", "group_position": 4},
    # Group K
    "COL": {"id": "COL", "name": "Colombia", "api_football_id": 8, "transfermarkt_id": "kolumbien", "elo": 1850.0, "squad_value_eur": 350000000, "eliminated": False, "group": "K", "group_position": 1},
    "COD": {"id": "COD", "name": "DR Congo", "api_football_id": 1503, "transfermarkt_id": "demokratische-republik-kongo", "elo": 1705.0, "squad_value_eur": 95000000, "eliminated": True, "group": "K", "group_position": 3},
    "POR": {"id": "POR", "name": "Portugal", "api_football_id": 27, "transfermarkt_id": "portugal", "elo": 1915.0, "squad_value_eur": 760000000, "eliminated": False, "group": "K", "group_position": 2},
    "UZB": {"id": "UZB", "name": "Uzbekistan", "api_football_id": 1566, "transfermarkt_id": "usbekistan", "elo": 1630.0, "squad_value_eur": 28000000, "eliminated": True, "group": "K", "group_position": 4},
    # Group L
    "ENG": {"id": "ENG", "name": "England", "api_football_id": 10, "transfermarkt_id": "england", "elo": 1975.0, "squad_value_eur": 1400000000, "eliminated": False, "group": "L", "group_position": 1},
    "CRO": {"id": "CRO", "name": "Croatia", "api_football_id": 3, "transfermarkt_id": "kroatien", "elo": 1870.0, "squad_value_eur": 280000000, "eliminated": False, "group": "L", "group_position": 2},
    "GHA": {"id": "GHA", "name": "Ghana", "api_football_id": 1504, "transfermarkt_id": "ghana", "elo": 1720.0, "squad_value_eur": 210000000, "eliminated": False, "group": "L", "group_position": 3},
    "PAN": {"id": "PAN", "name": "Panama", "api_football_id": 11, "transfermarkt_id": "panama", "elo": 1665.0, "squad_value_eur": 32000000, "eliminated": True, "group": "L", "group_position": 4},
}

# Round of 32 completed results (through July 1, 2026) — Wikipedia / Sky Sports
R32_COMPLETED: list[dict[str, Any]] = [
    {"match_id": "r32_m73", "date": "2026-06-28T19:00:00Z", "team_home": "RSA", "team_away": "CAN", "score_home": 0, "score_away": 1, "winner": "CAN", "status": "FT", "stage": "knockout"},
    {"match_id": "r32_m74", "date": "2026-06-29T20:30:00Z", "team_home": "GER", "team_away": "PAR", "score_home": 1, "score_away": 1, "penalties_home": 3, "penalties_away": 4, "winner": "PAR", "status": "PEN", "stage": "knockout"},
    {"match_id": "r32_m75", "date": "2026-06-29T23:00:00Z", "team_home": "NED", "team_away": "MAR", "score_home": 1, "score_away": 1, "penalties_home": 2, "penalties_away": 3, "winner": "MAR", "status": "PEN", "stage": "knockout"},
    {"match_id": "r32_m76", "date": "2026-06-29T17:00:00Z", "team_home": "BRA", "team_away": "JPN", "score_home": 2, "score_away": 1, "winner": "BRA", "status": "FT", "stage": "knockout", "xg_home": 2.1, "xg_away": 1.3},
    {"match_id": "r32_m77", "date": "2026-06-30T17:00:00Z", "team_home": "FRA", "team_away": "SWE", "score_home": 3, "score_away": 0, "winner": "FRA", "status": "FT", "stage": "knockout", "xg_home": 2.4, "xg_away": 0.6},
    {"match_id": "r32_m78", "date": "2026-06-30T13:00:00Z", "team_home": "CIV", "team_away": "NOR", "score_home": 1, "score_away": 2, "winner": "NOR", "status": "FT", "stage": "knockout"},
    {"match_id": "r32_m79", "date": "2026-06-30T21:00:00Z", "team_home": "MEX", "team_away": "ECU", "score_home": 2, "score_away": 0, "winner": "MEX", "status": "FT", "stage": "knockout"},
    {"match_id": "r32_m80", "date": "2026-07-01T17:00:00Z", "team_home": "ENG", "team_away": "COD", "score_home": 2, "score_away": 1, "winner": "ENG", "status": "FT", "stage": "knockout"},
]

R32_UPCOMING: list[dict[str, Any]] = [
    {"match_id": "r32_m81", "date": "2026-07-02T01:00:00Z", "team_home": "USA", "team_away": "BIH", "score_home": None, "score_away": None, "winner": None, "status": "NS", "stage": "knockout"},
    {"match_id": "r32_m82", "date": "2026-07-01T21:00:00Z", "team_home": "BEL", "team_away": "SEN", "score_home": None, "score_away": None, "winner": None, "status": "NS", "stage": "knockout"},
    {"match_id": "r32_m83", "date": "2026-07-02T23:00:00Z", "team_home": "POR", "team_away": "CRO", "score_home": None, "score_away": None, "winner": None, "status": "NS", "stage": "knockout"},
    {"match_id": "r32_m84", "date": "2026-07-02T20:00:00Z", "team_home": "ESP", "team_away": "AUT", "score_home": None, "score_away": None, "winner": None, "status": "NS", "stage": "knockout"},
    {"match_id": "r32_m85", "date": "2026-07-03T08:00:00Z", "team_home": "SUI", "team_away": "ALG", "score_home": None, "score_away": None, "winner": None, "status": "NS", "stage": "knockout"},
    {"match_id": "r32_m86", "date": "2026-07-04T03:00:00Z", "team_home": "ARG", "team_away": "CPV", "score_home": None, "score_away": None, "winner": None, "status": "NS", "stage": "knockout"},
    {"match_id": "r32_m87", "date": "2026-07-04T06:30:00Z", "team_home": "COL", "team_away": "GHA", "score_home": None, "score_away": None, "winner": None, "status": "NS", "stage": "knockout"},
    {"match_id": "r32_m88", "date": "2026-07-03T19:00:00Z", "team_home": "AUS", "team_away": "EGY", "score_home": None, "score_away": None, "winner": None, "status": "NS", "stage": "knockout"},
]

DEMO_FIXTURES: list[dict[str, Any]] = R32_COMPLETED + [
    {"team_home": "FRA", "team_away": "IRQ", "status": "FT", "winner": "FRA", "score_home": 2, "score_away": 0, "xg_home": 1.8, "xg_away": 0.4, "date": "2026-06-15", "stage": "group"},
    {"team_home": "BRA", "team_away": "MAR", "status": "FT", "winner": "BRA", "score_home": 1, "score_away": 0, "xg_home": 1.4, "xg_away": 0.9, "date": "2026-06-18", "stage": "group"},
    {"team_home": "ESP", "team_away": "ENG", "status": "FT", "winner": "ESP", "score_home": 2, "score_away": 1, "xg_home": 1.6, "xg_away": 1.2, "date": "2026-06-20", "stage": "group"},
    {"team_home": "ARG", "team_away": "AUT", "status": "FT", "winner": "ARG", "score_home": 2, "score_away": 0, "xg_home": 1.7, "xg_away": 0.5, "date": "2026-06-22", "stage": "group"},
]

DEMO_INJURIES: dict[str, list[dict[str, Any]]] = {
    "FRA": [{"player_id": 276, "name": "Kylian Mbappé", "status": "Missing Fixture", "is_starting_xi": True, "position": "Attacker", "xg_per90": 0.55, "xa_per90": 0.12}],
}

DEMO_PLAYER_STATS: dict[str, list[dict[str, Any]]] = {
    "FRA": [{"player_id": 276, "name": "Kylian Mbappé", "position": "Attacker", "xg_per90": 0.55, "xa_per90": 0.12, "is_starting_xi": True}],
}

DEMO_ODDS: dict[str, float] = {
    "BRA": 0.20, "FRA": 0.17, "ARG": 0.14, "ESP": 0.12, "ENG": 0.10,
    "POR": 0.06, "NED": 0.04, "USA": 0.04, "MEX": 0.03, "COL": 0.03,
    "MAR": 0.02, "NOR": 0.02, "SUI": 0.02, "BEL": 0.02, "CAN": 0.01,
    "PAR": 0.01, "SEN": 0.01, "CRO": 0.01, "AUT": 0.01, "ALG": 0.01,
}

DEMO_BRACKET: dict[str, Any] = {
    "_meta": {"current_round": "Round of 32", "wc_year": 2026},
    "rounds": {
        "round_of_32": {
            "status": "in_progress",
            "matches": R32_COMPLETED + R32_UPCOMING,
        },
        "round_of_16": {
            "status": "pending",
            "matches": [
                {"match_id": "r16_m89", "team_home": "PAR", "team_away": "FRA", "winner": None, "status": "NS"},
                {"match_id": "r16_m90", "team_home": "CAN", "team_away": "MAR", "winner": None, "status": "NS"},
                {"match_id": "r16_m91", "team_home": "BRA", "team_away": "NOR", "winner": None, "status": "NS"},
                {"match_id": "r16_m92", "team_home": "MEX", "team_away": "ENG", "winner": None, "status": "NS"},
                {"match_id": "r16_m93", "team_home": None, "team_away": None, "winner": None, "status": "NS"},
                {"match_id": "r16_m94", "team_home": None, "team_away": None, "winner": None, "status": "NS"},
                {"match_id": "r16_m95", "team_home": None, "team_away": None, "winner": None, "status": "NS"},
                {"match_id": "r16_m96", "team_home": None, "team_away": None, "winner": None, "status": "NS"},
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

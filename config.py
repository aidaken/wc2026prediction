"""
config.py — all the knobs live here.
change weights, scales, sim count. don't hardcode this stuff in src/.
"""

# weights must sum to 1.0
WEIGHTS = {
    "elo":          0.35,
    "xg_form":      0.30,
    "squad_value":  0.15,
    "betting_odds": 0.20,
}

# if an api dies mid-update, fall back to these instead of crashing
FALLBACK_WEIGHTS = {
    "no_squad_value":  {"elo": 0.43, "xg_form": 0.37, "squad_value": 0.00, "betting_odds": 0.20},
    "no_odds":         {"elo": 0.45, "xg_form": 0.40, "squad_value": 0.15, "betting_odds": 0.00},
    "elo_xg_only":     {"elo": 0.55, "xg_form": 0.45, "squad_value": 0.00, "betting_odds": 0.00},
}

# raw elo ratings (~1400-2100). only for updating ratings after matches.
# simulate.py uses STRENGTH_SCALE. don't swap them.
ELO_SCALE = 400

# team_strength is 0-1. using ELO_SCALE here makes every match look like a coin flip.
# python scripts/backtest.py --sweep to tune this
STRENGTH_SCALE = 0.68

# when fewer than this share of active teams have real xG, shrink form toward 0.5
XG_COVERAGE_FULL = 0.75

MAX_PLAYER_IMPORTANCE   = 0.20
GK_PENALTY              = 0.05
MIN_INJURY_MULTIPLIER   = 0.75   # floor so one injury doesn't zero out a team

KEY_PLAYERS_PER_TEAM = 2

KEY_PLAYER_OVERRIDES = {
    276:  {"team_id": "FRA", "reason": "mbappe"},
    521:  {"team_id": "NOR", "reason": "haaland"},
    874:  {"team_id": "POR", "reason": "ronaldo"},
    2295: {"team_id": "ARG", "reason": "messi"},
    9971: {"team_id": "ESP", "reason": "yamal"},
    306:  {"team_id": "ENG", "reason": "kane"},
}

# fetch.py still reads this dict for deep stat lookups
KEY_PLAYERS = {pid: info["team_id"] for pid, info in KEY_PLAYER_OVERRIDES.items()}

K_WORLD_CUP_KNOCKOUT    = 60
K_WORLD_CUP_GROUP       = 50
K_QUALIFIER             = 40
K_FRIENDLY              = 20
ELO_HISTORY_YEARS       = 2

XG_FORM_GAMES           = 5
XG_WC_MATCH_WEIGHT      = 2.0
XG_LUCK_THRESHOLD       = 1.3

# strength-of-schedule: rescale a team's xG by opponent quality (their own xG profile).
# faced stingy defenses -> xG-for boosted; faced strong attacks -> xG-against forgiven.
XG_OPPONENT_ADJUST      = True
XG_ADJ_CLAMP_LO         = 0.70   # safety rails so a tiny sample can't swing form wildly
XG_ADJ_CLAMP_HI         = 1.35

N_SIMULATIONS           = 100_000   # ~±0.13pp sampling noise vs ~±0.4pp at 10k
DRAW_PROBABILITY        = 0.27   # rough share of knockouts that go to pens (1994-2022)

API_FOOTBALL_BASE       = "https://v3.football.api-sports.io"
API_FOOTBALL_WC_ID      = 1
API_FOOTBALL_SEASON     = 2026
ODDS_API_BASE           = "https://api.the-odds-api.com/v4"
ODDS_SPORT_KEY          = "soccer_fifa_world_cup"
TRANSFERMARKT_WC_URL    = "https://www.transfermarkt.com/wettbewerbe/teilnehmer/pokalwettbewerb/WM"
TRANSFERMARKT_DELAY_S   = 2.0
FBREF_BASE              = "https://fbref.com"
FBREF_DELAY_S           = 5.0

MAX_RETRIES             = 3
RETRY_BACKOFF_FACTOR    = 2.0

ROUND_NAMES = [
    "Round of 32",
    "Round of 16",
    "Quarter-finals",
    "Semi-finals",
    "Final",
]

HISTORY_FILENAMES = {
    "Round of 32":    "round_32.json",
    "Round of 16":    "round_16.json",
    "Quarter-finals": "quarter_finals.json",
    "Semi-finals":    "semi_finals.json",
    "Final":          "final.json",
}

import os
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

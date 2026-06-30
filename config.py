"""
config.py — single source of truth for all constants and settings.

To change how the model works (weights, K-factors, simulation count),
edit values here. Do not hardcode constants in src/ modules.
"""

# ─── Model weights ─────────────────────────────────────────────────────────────
# Must sum to exactly 1.0
WEIGHTS = {
    "elo":          0.35,   # Long-term team quality baseline
    "xg_form":      0.30,   # Recent form via expected goals
    "squad_value":  0.15,   # Squad depth proxy (Transfermarkt)
    "betting_odds": 0.20,   # Aggregated expert consensus via market
}

# Fallback weights when a signal source is unavailable.
# These are applied if the corresponding API fails after all retries.
FALLBACK_WEIGHTS = {
    # If Transfermarkt is down — redistribute squad_value weight to Elo
    "no_squad_value":  {"elo": 0.43, "xg_form": 0.37, "squad_value": 0.00, "betting_odds": 0.20},
    # If OddsAPI is down — redistribute betting weight to Elo + xG
    "no_odds":         {"elo": 0.45, "xg_form": 0.40, "squad_value": 0.15, "betting_odds": 0.00},
    # If both are down — pure Elo + xG
    "elo_xg_only":     {"elo": 0.55, "xg_form": 0.45, "squad_value": 0.00, "betting_odds": 0.00},
}

# ─── Injury multiplier ─────────────────────────────────────────────────────────
MAX_PLAYER_IMPORTANCE   = 0.20   # No single player can account for more than 20% of team strength
GK_PENALTY              = 0.05   # Fixed penalty for missing first-choice goalkeeper
MIN_INJURY_MULTIPLIER   = 0.75   # Floor — team strength never drops below 75% regardless of injuries

# ─── Elo settings ──────────────────────────────────────────────────────────────
ELO_SCALE           = 400        # Scale factor in win probability formula (standard: 400)

# K-factors — controls how much ratings shift per match
K_WORLD_CUP_KNOCKOUT    = 60     # Round of 32 onward — highest stakes
K_WORLD_CUP_GROUP       = 50     # Group stage matches
K_QUALIFIER             = 40     # WC qualifiers, major tournament games
K_FRIENDLY              = 20     # Friendlies and minor tournaments

# How far back to seed initial Elo from (years before tournament)
ELO_HISTORY_YEARS       = 2

# ─── xG form ───────────────────────────────────────────────────────────────────
XG_FORM_GAMES           = 5      # Number of recent games to use for form calculation
XG_WC_MATCH_WEIGHT      = 2.0    # WC group stage games count this much more than pre-tournament
XG_LUCK_THRESHOLD       = 1.3    # goals / xG ratio above this = overperforming (apply cap)

# ─── Monte Carlo simulation ─────────────────────────────────────────────────────
N_SIMULATIONS           = 10_000
DRAW_PROBABILITY        = 0.25   # Approximate probability a knockout match goes to extra time

# ─── API settings ──────────────────────────────────────────────────────────────
API_FOOTBALL_BASE       = "https://v3.football.api-sports.io"
API_FOOTBALL_WC_ID      = 1          # Tournament ID in API-Football for WC 2026
API_FOOTBALL_SEASON     = 2026

ODDS_API_BASE           = "https://api.the-odds-api.com/v4"
ODDS_SPORT_KEY          = "soccer_fifa_world_cup"

TRANSFERMARKT_WC_URL    = "https://www.transfermarkt.com/wettbewerbe/teilnehmer/pokalwettbewerb/WM"
TRANSFERMARKT_DELAY_S   = 2.0    # Seconds to wait between Transfermarkt requests

FBREF_BASE              = "https://fbref.com"
FBREF_DELAY_S           = 5.0    # Seconds to wait between FBref requests

# ─── Retry config ──────────────────────────────────────────────────────────────
MAX_RETRIES             = 3
RETRY_BACKOFF_FACTOR    = 2.0    # Waits: 1s, 2s, 4s

# ─── Round names (must match API-Football round strings) ───────────────────────
ROUND_NAMES = [
    "Round of 32",
    "Round of 16",
    "Quarter-finals",
    "Semi-finals",
    "Final",
]

# ─── History archive names (map round → filename) ──────────────────────────────
HISTORY_FILENAMES = {
    "Round of 32":    "round_32.json",
    "Round of 16":    "round_16.json",
    "Quarter-finals": "quarter_finals.json",
    "Semi-finals":    "semi_finals.json",
    "Final":          "final.json",
}

# ─── Logging ───────────────────────────────────────────────────────────────────
import os
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ─── Key players ───────────────────────────────────────────────────────────────
# Used by injury.py to identify high-impact players worth fetching deep stats for.
# Format: { api_football_player_id: team_id }
# Add players as the tournament progresses if relevant injury situations arise.
KEY_PLAYERS = {
    276:  "FRA",   # Kylian Mbappé
    521:  "NOR",   # Erling Haaland
    874:  "POR",   # Cristiano Ronaldo
    2295: "ARG",   # Lionel Messi
    9971: "ESP",   # Lamine Yamal
    306:  "ENG",   # Harry Kane
}

#!/usr/bin/env python3
"""
run this after each round to refresh predictions.

  python update.py           # live (needs API_FOOTBALL_KEY)
  python update.py --demo    # offline seed data
  python update.py --round "Round of 16"
"""

from __future__ import annotations

import argparse
import shutil
from datetime import datetime, timezone
from typing import Any

import config
from src.bracket import detect_current_round, mark_eliminations, sync_bracket_from_fixtures
from src.elo import normalize_elo, update_ratings
from src.fetch import DataValidationError, FetchError, get_fixtures, get_injuries, get_player_stats, validate_raw_data
from src.injury import calculate_multipliers
from src.odds import get_implied_probs
from src.seed import DEMO_BRACKET, DEMO_FIXTURES, DEMO_INJURIES, DEMO_ODDS, DEMO_PLAYER_STATS, TEAMS
from src.simulate import run as run_simulation
from src.teams import TeamRegistry
from src.utils import DATA_DIR, get_env_int, load_json, normalize_betting_probs, normalize_minmax, setup_logging, write_json
from src.value import get_squad_values
from src.xg import calculate_form_ratios

MODEL_VERSION = "1.1.0"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _active_teams(teams: dict[str, dict[str, Any]]) -> list[str]:
    return [tid for tid, t in teams.items() if not t.get("eliminated", False)]


def _collect_fixtures_from_bracket(bracket: dict[str, Any]) -> list[dict[str, Any]]:
    fixtures: list[dict[str, Any]] = []
    for round_data in bracket.get("rounds", {}).values():
        for match in round_data.get("matches", []):
            if match.get("team_home") and match.get("team_away"):
                fixtures.append({**match, "stage": "knockout"})
    return fixtures


def fetch_all_data(
    teams: dict[str, dict[str, Any]],
    bracket: dict[str, Any],
    round_name: str,
    registry: TeamRegistry,
    demo: bool = False,
) -> dict[str, Any]:
    if demo:
        return {
            "fixtures": DEMO_FIXTURES + _collect_fixtures_from_bracket(DEMO_BRACKET),
            "injuries": DEMO_INJURIES,
            "player_stats": DEMO_PLAYER_STATS,
            "squad_values": {tid: t["squad_value_eur"] for tid, t in TEAMS.items() if t.get("squad_value_eur")},
            "betting_probs": DEMO_ODDS,
            "api_fixtures": [],
        }

    api_fixtures: list[dict[str, Any]] = []
    try:
        api_fixtures = get_fixtures(round_name, registry)
    except FetchError as exc:
        logger = setup_logging()
        logger.warning("API fetch failed (%s) — using bracket fixture history", exc)

    bracket_fixtures = _collect_fixtures_from_bracket(bracket)
    seen_ids = {f.get("api_fixture_id") for f in api_fixtures if f.get("api_fixture_id")}
    merged = list(api_fixtures)
    for fix in bracket_fixtures:
        fid = fix.get("api_fixture_id")
        if fid and fid in seen_ids:
            continue
        merged.append(fix)

    injuries: dict[str, list] = {}
    player_stats: dict[str, list] = {}
    for tid, team in teams.items():
        if team.get("eliminated"):
            continue
        api_id = team.get("api_football_id")
        if not api_id:
            continue
        try:
            stats = get_player_stats(api_id, starting_player_ids=set(config.KEY_PLAYERS.keys()))
            player_stats[tid] = stats
            injuries[tid] = get_injuries(api_id, stats)
        except FetchError as exc:
            setup_logging().warning("Player/injury fetch failed for %s: %s", tid, exc)

    squad_values = get_squad_values(teams, fallback=teams)
    active = _active_teams(teams)
    betting_probs = get_implied_probs(active)
    return {
        "fixtures": merged,
        "injuries": injuries,
        "player_stats": player_stats,
        "squad_values": squad_values,
        "betting_probs": betting_probs,
        "api_fixtures": api_fixtures,
    }


def combine_strengths(
    teams: dict[str, dict[str, Any]],
    raw: dict[str, Any],
    weights: dict[str, float],
    processed_elo_ids: set[str] | None = None,
) -> tuple[dict[str, float], dict[str, dict[str, float]], list[str]]:
    active = _active_teams(teams)
    fixtures = raw["fixtures"]

    _, newly_processed = update_ratings(teams, fixtures, processed_ids=processed_elo_ids)
    elo_norm = normalize_elo(teams)
    xg_form = calculate_form_ratios(fixtures, active)
    injury_mult = calculate_multipliers(raw["injuries"], raw["player_stats"], active)

    squad_raw = {tid: raw["squad_values"].get(tid, teams[tid].get("squad_value_eur", 0)) for tid in active}
    squad_raw = {tid: v for tid, v in squad_raw.items() if v}
    squad_norm = normalize_minmax({tid: float(v) for tid, v in squad_raw.items()})

    betting = raw.get("betting_probs") or {}
    betting_active = normalize_betting_probs(betting, active)

    strengths: dict[str, float] = {}
    signals: dict[str, dict[str, float]] = {}

    strength_ids = list(teams.keys())
    for tid in strength_ids:
        if teams[tid].get("eliminated") and tid not in active:
            # keep last strength on file for backtest, don't recompute
            if teams[tid].get("team_strength") is not None:
                strengths[tid] = teams[tid]["team_strength"]
            continue

        components = {
            "elo_normalized": elo_norm.get(tid, 0.5),
            "xg_form_ratio": xg_form.get(tid, 0.5),
            "squad_value_normalized": squad_norm.get(tid, 0.5),
            "betting_implied_prob": betting_active.get(tid, 0.0),
            "injury_multiplier": injury_mult.get(tid, 1.0),
        }
        base = (
            components["elo_normalized"] * weights["elo"]
            + components["xg_form_ratio"] * weights["xg_form"]
            + components["squad_value_normalized"] * weights["squad_value"]
            + components["betting_implied_prob"] * weights["betting_odds"]
        )
        strengths[tid] = round(base * components["injury_multiplier"], 4)
        if tid in active:
            signals[tid] = components

    return strengths, signals, newly_processed


def _select_weights(raw: dict[str, Any]) -> dict[str, float]:
    has_squad = len(raw.get("squad_values") or {}) >= 12
    has_odds = bool(raw.get("betting_probs"))
    if not has_squad and not has_odds:
        return config.FALLBACK_WEIGHTS["elo_xg_only"]
    if not has_squad:
        return config.FALLBACK_WEIGHTS["no_squad_value"]
    if not has_odds:
        return config.FALLBACK_WEIGHTS["no_odds"]
    return config.WEIGHTS


def write_outputs(
    teams: dict[str, dict[str, Any]],
    bracket: dict[str, Any],
    strengths: dict[str, float],
    signals: dict[str, dict[str, float]],
    sim_results: dict[str, Any],
    round_name: str,
    n_sims: int,
    elo_processed_matches: list[str] | None = None,
) -> None:
    team_sim = sim_results.get("team_predictions", sim_results)
    match_predictions = sim_results.get("match_predictions", {})
    active_count = len(_active_teams(teams))
    for tid, strength in strengths.items():
        if tid in teams:
            teams[tid]["team_strength"] = strength

    teams_doc = {
        "_meta": {
            "last_updated": _utc_now(),
            "round": round_name,
            "teams_remaining": active_count,
            "elo_processed_matches": elo_processed_matches or [],
        },
        "teams": teams,
    }
    bracket["_meta"] = {
        **bracket.get("_meta", {}),
        "last_updated": _utc_now(),
        "current_round": round_name,
        "wc_year": 2026,
    }

    predictions_list = []
    active_rank = 0
    for tid, team in sorted(
        teams.items(),
        key=lambda x: team_sim.get(x[0], {}).get("win_probability", 0),
        reverse=True,
    ):
        sim = team_sim.get(tid, {})
        eliminated = team.get("eliminated", False)
        if not eliminated:
            active_rank += 1
        predictions_list.append({
            "team_id": tid,
            "team_name": team["name"],
            "win_probability": 0.0 if eliminated else sim.get("win_probability", 0.0),
            "reach_final_probability": 0.0 if eliminated else sim.get("reach_final_probability", 0.0),
            "reach_semis_probability": 0.0 if eliminated else sim.get("reach_semis_probability", 0.0),
            "signals": None if eliminated else signals.get(tid),
            "team_strength": None if eliminated else strengths.get(tid),
            "eliminated": eliminated,
            "rank": None if eliminated else active_rank,
        })

    # Active teams first (by win %), then eliminated
    predictions_list.sort(
        key=lambda p: (p["eliminated"], -p["win_probability"]),
    )

    predictions_doc = {
        "_meta": {
            "generated_at": _utc_now(),
            "round": round_name,
            "simulations": n_sims,
            "model_version": MODEL_VERSION,
        },
        "predictions": predictions_list,
        "match_predictions": match_predictions,
    }

    write_json(DATA_DIR / "teams.json", teams_doc)
    write_json(DATA_DIR / "bracket.json", bracket)
    write_json(DATA_DIR / "predictions.json", predictions_doc)


def archive_round(round_name: str) -> None:
    history_dir = DATA_DIR / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    filename = config.HISTORY_FILENAMES.get(round_name)
    if not filename:
        return
    src = DATA_DIR / "predictions.json"
    if src.exists():
        shutil.copy2(src, history_dir / filename)
    _update_history_index(history_dir)


def _update_history_index(history_dir) -> None:
    index = []
    for round_name, filename in config.HISTORY_FILENAMES.items():
        path = history_dir / filename
        if path.exists():
            data = load_json(path)
            index.append({
                "round": round_name,
                "file": filename,
                "generated_at": data.get("_meta", {}).get("generated_at"),
            })
    write_json(history_dir / "index.json", {"rounds": index})


def run_update(round_name: str | None = None, demo: bool = False) -> None:
    logger = setup_logging()
    n_sims = get_env_int("N_SIMULATIONS", config.N_SIMULATIONS)

    teams_doc = load_json(DATA_DIR / "teams.json")
    bracket = load_json(DATA_DIR / "bracket.json")
    processed_elo = set(teams_doc.get("_meta", {}).get("elo_processed_matches", []))

    if demo or not teams_doc.get("teams"):
        teams = {tid: dict(t) for tid, t in TEAMS.items()}
        bracket = DEMO_BRACKET
        round_name = round_name or bracket["_meta"]["current_round"]
        processed_elo = set()
    else:
        teams = teams_doc["teams"]
        round_name = round_name or detect_current_round(bracket)

    registry = TeamRegistry(teams)

    logger.info("Fetching data for %s...", round_name)
    raw = fetch_all_data(teams, bracket, round_name, registry, demo=demo)

    if raw.get("api_fixtures"):
        completed = sync_bracket_from_fixtures(bracket, raw["api_fixtures"], round_name)
        if completed:
            newly_out = mark_eliminations(teams, completed)
            if newly_out:
                logger.info("Marked eliminated: %s", ", ".join(newly_out))

    active_count = len(_active_teams(teams))
    validate_raw_data(raw["fixtures"], active_count)

    weights = _select_weights(raw)
    logger.info("Calculating team strengths (weights: %s)...", weights)
    strengths, signals, newly_processed = combine_strengths(
        teams, raw, weights, processed_elo_ids=processed_elo,
    )
    all_processed = sorted(processed_elo | set(newly_processed))

    for tid, value in raw.get("squad_values", {}).items():
        if tid in teams and value:
            teams[tid]["squad_value_eur"] = value

    logger.info("Running %s Monte Carlo simulations...", f"{n_sims:,}")
    active_strengths = {tid: s for tid, s in strengths.items() if tid in _active_teams(teams)}
    sim_results = run_simulation(active_strengths, bracket, n=n_sims)

    logger.info("Writing output files...")
    write_outputs(
        teams, bracket, strengths, signals, sim_results, round_name, n_sims,
        elo_processed_matches=all_processed,
    )
    archive_round(round_name)

    team_sim = sim_results.get("team_predictions", sim_results)
    top = max(
        ((tid, team_sim[tid]["win_probability"]) for tid in _active_teams(teams) if tid in team_sim),
        key=lambda x: x[1],
        default=(None, 0),
    )
    if top[0]:
        logger.info("Done. Top prediction: %s %.1f%%", teams[top[0]]["name"], top[1] * 100)


def main() -> None:
    parser = argparse.ArgumentParser(description="Update WC 2026 predictions")
    parser.add_argument("--demo", action="store_true", help="Run offline with seed data")
    parser.add_argument("--round", type=str, default=None, help="Force a specific round name")
    args = parser.parse_args()
    try:
        run_update(round_name=args.round, demo=args.demo)
    except (FetchError, DataValidationError) as exc:
        setup_logging().error("%s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()

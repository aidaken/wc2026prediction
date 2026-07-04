#!/usr/bin/env python3
"""
run this after each round to refresh predictions.

  python scripts/fetch_public.py   # wikipedia results first (no keys)
  python update.py                 # recalc strengths + sim
  python update.py --demo          # offline seed data, skip most apis
  python update.py --round "Round of 16"
"""

from __future__ import annotations

import argparse
import shutil
from datetime import datetime, timezone
from typing import Any

import config
from src.bracket import detect_current_round, mark_eliminations, sync_bracket_from_fixtures
from src.bracket_topology import ROUND_ORDER, propagate_winner
from src.elo import normalize_elo, recompute_from_seed
from src.fetch import (
    DataValidationError,
    FetchError,
    enrich_bracket_with_xg,
    get_all_season_fixtures,
    get_fixtures,
    get_injuries,
    get_player_stats,
    merge_fixtures,
    validate_raw_data,
)
from src.injury import calculate_multipliers
from src.odds import get_implied_probs
from src.public_fetch import load_manual_odds
from src.seed import DEMO_BRACKET, DEMO_FIXTURES, DEMO_INJURIES, DEMO_ODDS, DEMO_PLAYER_STATS, TEAMS
from src.simulate import run as run_simulation
from src.strength import compute_strength, shrink_xg_toward_neutral
from src.teams import TeamRegistry
from src.utils import DATA_DIR, get_env_int, load_json, normalize_betting_probs, normalize_minmax, setup_logging, write_json
from src.value import get_squad_values
from src.xg import calculate_form_ratios

MODEL_VERSION = "1.2.0"
FIXTURES_CACHE_PATH = DATA_DIR / "fixtures_cache.json"


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


def _apply_bracket_state(teams: dict[str, dict[str, Any]], bracket: dict[str, Any]) -> list[str]:
    """Propagate known winners into next-round slots and mark losers eliminated."""
    rounds = bracket.get("rounds", {})
    for round_key in ROUND_ORDER:
        for match in rounds.get(round_key, {}).get("matches", []):
            winner = match.get("winner")
            match_id = match.get("match_id")
            if winner and match_id:
                propagate_winner(rounds, match_id, winner)

    completed = [
        m
        for round_data in rounds.values()
        for m in round_data.get("matches", [])
        if m.get("winner") and m.get("team_home") and m.get("team_away")
    ]
    return mark_eliminations(teams, completed)


def _load_fixtures_cache() -> list[dict[str, Any]]:
    doc = load_json(FIXTURES_CACHE_PATH)
    return list(doc.get("fixtures", []))


def _save_fixtures_cache(fixtures: list[dict[str, Any]], source: str) -> None:
    write_json(FIXTURES_CACHE_PATH, {
        "_meta": {"last_updated": _utc_now(), "source": source, "count": len(fixtures)},
        "fixtures": fixtures,
    })


def fetch_all_data(
    teams: dict[str, dict[str, Any]],
    bracket: dict[str, Any],
    round_name: str,
    registry: TeamRegistry,
    demo: bool = False,
) -> dict[str, Any]:
    if demo:
        fixtures = merge_fixtures(
            DEMO_FIXTURES,
            _collect_fixtures_from_bracket(DEMO_BRACKET),
        )
        return {
            "fixtures": fixtures,
            "injuries": DEMO_INJURIES,
            "player_stats": DEMO_PLAYER_STATS,
            "squad_values": {tid: t["squad_value_eur"] for tid, t in TEAMS.items() if t.get("squad_value_eur")},
            "betting_probs": DEMO_ODDS,
            "api_fixtures": [],
            "data_sources": {
                "api_football": "demo",
                "odds_api": "demo",
                "transfermarkt": "demo",
                "fixtures_count": len(fixtures),
            },
        }

    logger = setup_logging()
    api_season_fixtures: list[dict[str, Any]] = []
    api_round_fixtures: list[dict[str, Any]] = []
    api_football_status = "unavailable"

    try:
        api_season_fixtures = get_all_season_fixtures(registry, enrich_xg=True)
        api_football_status = "ok"
        logger.info("API-Football: %d season fixtures (with xG backfill)", len(api_season_fixtures))
    except FetchError as exc:
        logger.warning("API-Football season fetch failed (%s)", exc)
        try:
            api_round_fixtures = get_fixtures(round_name, registry)
            api_football_status = "partial"
            logger.info("API-Football: %d fixtures for %s", len(api_round_fixtures), round_name)
        except FetchError as exc2:
            logger.warning("API-Football round fetch failed (%s) — using cache + bracket", exc2)

    if api_season_fixtures or api_round_fixtures:
        merged_api = merge_fixtures(api_season_fixtures, api_round_fixtures)
        _save_fixtures_cache(merged_api, source=api_football_status)
    else:
        merged_api = _load_fixtures_cache()
        if merged_api:
            logger.info("Using %d cached fixtures", len(merged_api))

    try:
        enriched = enrich_bracket_with_xg(bracket, registry)
        if enriched:
            logger.info("Backfilled xG on %d bracket matches", enriched)
    except FetchError:
        pass

    bracket_fixtures = _collect_fixtures_from_bracket(bracket)
    # Group-stage xG from seed when API cache is thin; bracket knockouts use goals fallback
    seed_group = [f for f in DEMO_FIXTURES if f.get("stage") == "group"]
    fixtures = merge_fixtures(seed_group, merged_api, bracket_fixtures)
    if fixtures and api_football_status == "unavailable" and not merged_api:
        _save_fixtures_cache(fixtures, source="bracket+seed")

    injuries: dict[str, list] = {}
    player_stats: dict[str, list] = {}
    injury_status = "skipped"
    if api_football_status != "unavailable":
        injury_status = "ok"
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
                injury_status = "partial"
                logger.warning("Player/injury fetch failed for %s: %s", tid, exc)

    squad_values = get_squad_values(teams, fallback=teams)
    squad_status = "ok" if len(squad_values) >= 12 else "partial"

    active = _active_teams(teams)
    betting_probs = get_implied_probs(active)
    odds_status = "ok" if betting_probs else "unavailable"
    if not betting_probs:
        betting_probs = load_manual_odds()
        if betting_probs:
            odds_status = "manual"

    return {
        "fixtures": fixtures,
        "injuries": injuries,
        "player_stats": player_stats,
        "squad_values": squad_values,
        "betting_probs": betting_probs,
        "api_fixtures": api_season_fixtures or api_round_fixtures,
        "data_sources": {
            "api_football": api_football_status,
            "odds_api": odds_status,
            "transfermarkt": squad_status,
            "fixtures_count": len(fixtures),
            "injuries_teams": len(injuries),
        },
    }


def combine_strengths(
    teams: dict[str, dict[str, Any]],
    raw: dict[str, Any],
    weights: dict[str, float],
) -> tuple[dict[str, float], dict[str, dict[str, float]], dict[str, Any]]:
    active = _active_teams(teams)
    fixtures = raw["fixtures"]

    # Elo is already set on `teams` by the deterministic replay in run_update.
    elo_norm = normalize_elo(teams)
    xg_form, xg_meta = calculate_form_ratios(fixtures, active)
    injury_mult = calculate_multipliers(raw["injuries"], raw["player_stats"], active)

    squad_raw = {tid: raw["squad_values"].get(tid, teams[tid].get("squad_value_eur", 0)) for tid in active}
    squad_raw = {tid: v for tid, v in squad_raw.items() if v}
    squad_norm = normalize_minmax({tid: float(v) for tid, v in squad_raw.items()})

    betting_raw = raw.get("betting_probs") or {}
    betting_available = bool(betting_raw)
    betting_active = normalize_betting_probs(betting_raw, active) if betting_available else {}

    xg_with_data = sum(1 for tid in active if xg_meta.get(tid, {}).get("has_xg_data"))
    xg_coverage = xg_with_data / len(active) if active else 0.0

    strengths: dict[str, float] = {}
    signals: dict[str, dict[str, float]] = {}

    strength_ids = list(teams.keys())
    for tid in strength_ids:
        if teams[tid].get("eliminated") and tid not in active:
            if teams[tid].get("team_strength") is not None:
                strengths[tid] = teams[tid]["team_strength"]
            continue

        meta = xg_meta.get(tid, {})
        has_xg = bool(meta.get("has_xg_data"))
        form_source = meta.get("form_source", "default")
        form_ratio = xg_form.get(tid, 0.5)
        if has_xg:
            form_ratio = shrink_xg_toward_neutral(
                form_ratio,
                has_xg=True,
                coverage=xg_coverage,
            )
        has_form = form_source != "default"
        has_team_odds = betting_available and tid in betting_raw and betting_raw.get(tid, 0) > 0

        components = {
            "elo_normalized": elo_norm.get(tid, 0.5),
            "xg_form_ratio": form_ratio,
            "squad_value_normalized": squad_norm.get(tid, 0.5),
            "betting_implied_prob": betting_active.get(tid, 0.0) if betting_available else 0.0,
            "injury_multiplier": injury_mult.get(tid, 1.0),
        }
        strength, eff_weights = compute_strength(
            components,
            weights,
            has_xg=has_form,
            has_betting=has_team_odds,
        )
        strengths[tid] = strength
        if tid in active:
            signals[tid] = {
                **components,
                "has_xg_data": has_xg,
                "form_source": meta.get("form_source", "default"),
                "matches_used": meta.get("matches_used", 0),
                "avg_xg_for": meta.get("avg_xg_for"),
                "avg_xg_against": meta.get("avg_xg_against"),
                "effective_weights": eff_weights,
            }

    strength_meta = {
        "xg_coverage": round(xg_coverage, 3),
        "betting_available": betting_available,
        "teams_with_xg": xg_with_data,
    }
    return strengths, signals, strength_meta


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
    *,
    weights: dict[str, float] | None = None,
    data_sources: dict[str, Any] | None = None,
    strength_meta: dict[str, Any] | None = None,
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
            "elo_method": "full_replay_from_seed",
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
            "weights": weights or config.WEIGHTS,
            "strength_scale": config.STRENGTH_SCALE,
            "data_sources": data_sources or {},
            "strength_meta": strength_meta or {},
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

    if demo or not teams_doc.get("teams"):
        teams = {tid: dict(t) for tid, t in TEAMS.items()}
        bracket = DEMO_BRACKET
        round_name = round_name or bracket["_meta"]["current_round"]
    else:
        teams = teams_doc["teams"]
        round_name = round_name or detect_current_round(bracket)

    registry = TeamRegistry(teams)

    _apply_bracket_state(teams, bracket)

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

    # Deterministic Elo: replay group stage + knockouts from pre-tournament seed.
    seed_elos = {tid: float(TEAMS.get(tid, {}).get("elo", t.get("elo", 1500.0))) for tid, t in teams.items()}
    group_fixtures = [f for f in raw["fixtures"] if f.get("stage") == "group"]
    current_elo, elo_round_deltas = recompute_from_seed(
        seed_elos, group_fixtures, bracket, ROUND_ORDER, config.ROUND_NAMES,
    )
    round_deltas = elo_round_deltas.get(round_name, {})
    for tid in teams:
        if tid in current_elo:
            teams[tid]["elo"] = current_elo[tid]
        teams[tid]["elo_change_this_round"] = round(round_deltas.get(tid, 0.0), 1)

    weights = _select_weights(raw)
    logger.info("Calculating team strengths (weights: %s)...", weights)
    strengths, signals, strength_meta = combine_strengths(teams, raw, weights)

    for tid, value in raw.get("squad_values", {}).items():
        if tid in teams and value:
            teams[tid]["squad_value_eur"] = value

    logger.info(
        "xG coverage: %s/%s teams | betting: %s | fixtures: %s",
        strength_meta.get("teams_with_xg"),
        active_count,
        raw.get("data_sources", {}).get("odds_api"),
        raw.get("data_sources", {}).get("fixtures_count"),
    )

    logger.info("Running %s Monte Carlo simulations...", f"{n_sims:,}")
    active_strengths = {tid: s for tid, s in strengths.items() if tid in _active_teams(teams)}
    sim_results = run_simulation(active_strengths, bracket, n=n_sims)

    logger.info("Writing output files...")
    write_outputs(
        teams, bracket, strengths, signals, sim_results, round_name, n_sims,
        weights=weights,
        data_sources=raw.get("data_sources"),
        strength_meta=strength_meta,
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

"""Unit tests for the prediction engine."""

import unittest

from src.bracket import detect_current_round, mark_eliminations
from src.bracket_topology import MATCH_FEEDERS, propagate_winner
from src.elo import update_ratings
from src.live import live_win_probability, live_win_probability_from_match
from src.seed import DEMO_BRACKET, TEAMS
from src.simulate import match_win_probability, run
from src.teams import ODDS_NAME_TO_ID, TM_SLUG_TO_ID, TeamRegistry
from src.utils import normalize_betting_probs
from src.xg import calculate_form_ratios


class TestTeamRegistry(unittest.TestCase):
    def test_resolve_by_id_and_name(self):
        reg = TeamRegistry(TEAMS)
        self.assertEqual(reg.resolve("Brazil"), "BRA")
        self.assertEqual(reg.resolve(6), "BRA")
        self.assertEqual(reg.resolve("BRA"), "BRA")

    def test_external_maps_only_wc2026_teams(self):
        valid = set(TEAMS.keys())
        for tid in ODDS_NAME_TO_ID.values():
            self.assertIn(tid, valid, f"Odds map contains non-WC2026 team: {tid}")
        for tid in TM_SLUG_TO_ID.values():
            self.assertIn(tid, valid, f"Transfermarkt map contains non-WC2026 team: {tid}")
        self.assertNotIn("POL", valid)
        self.assertNotIn("NGA", valid)


class TestElo(unittest.TestCase):
    def test_winner_gains_rating(self):
        teams = {
            "BRA": {"elo": 2000.0, "eliminated": False},
            "FRA": {"elo": 2000.0, "eliminated": False},
        }
        fixtures = [{
            "match_id": "test_m01",
            "team_home": "BRA", "team_away": "FRA", "status": "FT",
            "winner": "BRA", "stage": "knockout",
        }]
        update_ratings(teams, fixtures)
        self.assertGreater(teams["BRA"]["elo"], 2000.0)
        self.assertLess(teams["FRA"]["elo"], 2000.0)

    def test_no_double_counting(self):
        teams = {
            "BRA": {"elo": 2000.0, "eliminated": False},
            "FRA": {"elo": 2000.0, "eliminated": False},
        }
        fixtures = [{
            "match_id": "test_m01",
            "team_home": "BRA", "team_away": "FRA", "status": "FT",
            "winner": "BRA", "stage": "knockout",
        }]
        update_ratings(teams, fixtures)
        elo_after_first = teams["BRA"]["elo"]
        update_ratings(teams, fixtures, processed_ids={"test_m01"})
        self.assertEqual(teams["BRA"]["elo"], elo_after_first)


class TestBettingNormalization(unittest.TestCase):
    def test_normalizes_to_one(self):
        active = ["BRA", "FRA", "ARG"]
        raw = {"BRA": 0.20, "FRA": 0.17, "ARG": 0.14}
        normed = normalize_betting_probs(raw, active)
        self.assertAlmostEqual(sum(normed.values()), 1.0, places=4)


class TestXgForm(unittest.TestCase):
    def test_dominant_team_above_half(self):
        fixtures = [{
            "team_home": "BRA", "team_away": "KOR", "status": "FT",
            "xg_home": 2.0, "xg_away": 0.5, "date": "2026-06-28", "stage": "knockout",
        }]
        ratios, meta = calculate_form_ratios(fixtures, ["BRA", "KOR"])
        self.assertGreater(ratios["BRA"], 0.5)
        self.assertLess(ratios["KOR"], 0.5)
        self.assertTrue(meta["BRA"]["has_xg_data"])

    def test_goals_fallback_when_no_xg(self):
        fixtures = [{
            "team_home": "BRA", "team_away": "KOR", "status": "FT",
            "score_home": 3, "score_away": 0, "date": "2026-06-28", "stage": "knockout",
        }]
        ratios, meta = calculate_form_ratios(fixtures, ["BRA", "KOR"])
        self.assertGreater(ratios["BRA"], 0.5)
        self.assertEqual(meta["BRA"]["form_source"], "goals")


class TestBracket(unittest.TestCase):
    def test_detect_current_round(self):
        bracket = DEMO_BRACKET
        self.assertEqual(detect_current_round(bracket), "Round of 32")

    def test_mark_eliminations(self):
        teams = {"BRA": {"eliminated": False}, "FRA": {"eliminated": False}}
        matches = [{"team_home": "BRA", "team_away": "FRA", "winner": "BRA", "status": "FT"}]
        out = mark_eliminations(teams, matches)
        self.assertIn("FRA", out)
        self.assertTrue(teams["FRA"]["eliminated"])

    def test_feeder_preserves_r16_matchups(self):
        from copy import deepcopy

        working = deepcopy(DEMO_BRACKET["rounds"])
        propagate_winner(working, "r32_m74", "PAR")
        propagate_winner(working, "r32_m77", "FRA")
        r16_89 = next(
            m for m in working["round_of_16"]["matches"] if m["match_id"] == "r16_m89"
        )
        self.assertEqual(r16_89["team_home"], "PAR")
        self.assertEqual(r16_89["team_away"], "FRA")

    def test_all_r32_feeders_defined(self):
        for i in range(73, 89):
            self.assertIn(f"r32_m{i}", MATCH_FEEDERS)


class TestSimulate(unittest.TestCase):
    def test_favorite_wins_more_often(self):
        bracket = {
            "rounds": {
                "final": {
                    "matches": [{
                        "match_id": "final_m01",
                        "team_home": "BRA", "team_away": "CAN",
                        "winner": None, "status": "NS",
                    }],
                },
            },
        }
        strengths = {"BRA": 0.9, "CAN": 0.2}
        results = run(strengths, bracket, n=2000, seed=7)
        teams = results["team_predictions"]
        self.assertGreater(teams["BRA"]["win_probability"], teams["CAN"]["win_probability"])

    def test_match_predictions_returned(self):
        results = run({"BRA": 0.8, "FRA": 0.7}, DEMO_BRACKET, n=500, seed=1)
        self.assertIn("team_predictions", results)
        self.assertIn("match_predictions", results)
        r32 = results["match_predictions"].get("round_of_32", [])
        self.assertTrue(len(r32) > 0)
        por_cro = next((m for m in r32 if m["team_home"] == "POR"), None)
        self.assertIsNotNone(por_cro)
        self.assertAlmostEqual(
            por_cro["advance_probability_home"] + por_cro["advance_probability_away"],
            1.0, places=1,
        )

    def test_match_win_probability_favorite(self):
        prob_home, prob_away = match_win_probability("BRA", "CAN", {"BRA": 0.9, "CAN": 0.2})
        self.assertGreater(prob_home, prob_away)
        self.assertGreater(prob_home, 0.6)

    def test_strength_scale_not_coin_flip(self):
        prob_home, _ = match_win_probability("BRA", "FRA", {"BRA": 0.78, "FRA": 0.64})
        self.assertGreater(prob_home, 0.55)
        self.assertLess(prob_home, 0.85)


class TestLiveWinProbability(unittest.TestCase):
    def test_probs_sum_to_one(self):
        ph, pa = live_win_probability(3, 4, 70, 0.03, 0.023)
        self.assertAlmostEqual(ph + pa, 1.0, places=6)

    def test_leading_team_favored(self):
        # away side up a goal late should be the clear favorite
        ph, pa = live_win_probability(3, 4, 70, 0.03, 0.023)
        self.assertGreater(pa, ph)
        self.assertGreater(pa, 0.6)

    def test_lead_hardens_as_clock_runs(self):
        # same one-goal lead is worth more with less time left
        _, pa_70 = live_win_probability(3, 4, 70, 0.03, 0.023)
        _, pa_85 = live_win_probability(3, 4, 85, 0.03, 0.023)
        self.assertGreater(pa_85, pa_70)

    def test_level_game_near_coin_flip(self):
        ph, pa = live_win_probability(2, 2, 80, 0.02, 0.02)
        self.assertAlmostEqual(ph, pa, delta=0.05)

    def test_only_reads_live_statuses(self):
        self.assertIsNone(
            live_win_probability_from_match({"status": "NS", "minute": 70}, {})
        )
        probs = live_win_probability_from_match(
            {
                "status": "LIVE", "minute": 70,
                "team_home": "FRA", "team_away": "ENG",
                "score_home": 3, "score_away": 4,
                "xg_home": 2.10, "xg_away": 1.61,
            },
            {"FRA": 0.85, "ENG": 0.76},
        )
        self.assertIsNotNone(probs)
        self.assertAlmostEqual(sum(probs), 1.0, places=6)


if __name__ == "__main__":
    unittest.main()

"""Unit tests for the prediction engine."""

import unittest

from src.bracket import detect_current_round, mark_eliminations
from src.elo import update_ratings
from src.seed import DEMO_BRACKET, TEAMS
from src.simulate import run
from src.teams import ODDS_NAME_TO_ID, TM_SLUG_TO_ID, TeamRegistry
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
            "team_home": "BRA", "team_away": "FRA", "status": "FT",
            "winner": "BRA", "stage": "knockout",
        }]
        update_ratings(teams, fixtures)
        self.assertGreater(teams["BRA"]["elo"], 2000.0)
        self.assertLess(teams["FRA"]["elo"], 2000.0)


class TestXgForm(unittest.TestCase):
    def test_dominant_team_above_half(self):
        fixtures = [{
            "team_home": "BRA", "team_away": "KOR", "status": "FT",
            "xg_home": 2.0, "xg_away": 0.5, "date": "2026-06-28", "stage": "knockout",
        }]
        ratios = calculate_form_ratios(fixtures, ["BRA", "KOR"])
        self.assertGreater(ratios["BRA"], 0.5)
        self.assertLess(ratios["KOR"], 0.5)


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


class TestSimulate(unittest.TestCase):
    def test_favorite_wins_more_often(self):
        bracket = {
            "rounds": {
                "final": {
                    "matches": [{"team_home": "BRA", "team_away": "CAN", "winner": None, "status": "NS"}],
                },
            },
        }
        strengths = {"BRA": 0.9, "CAN": 0.2}
        results = run(strengths, bracket, n=2000, seed=7)
        self.assertGreater(results["BRA"]["win_probability"], results["CAN"]["win_probability"])


if __name__ == "__main__":
    unittest.main()

import copy
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from astroscript.cli import argparser, main, run_opportunity_search
from astroscript.opportunity_search import (
    AspectCondition,
    NatalAspectCondition,
    NatalChart,
    MoonPhaseCondition,
    OpportunitySearchQuery,
    OpportunityWindow,
    ConditionEvaluation,
    TransitNatalHouseCondition,
    load_opportunity_query,
    opportunity_query_from_dict,
    search_opportunities,
)


class OpportunitySearchTests(unittest.TestCase):
    def setUp(self):
        self.start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.end = self.start + timedelta(days=1)

    def test_conjunction_window_crosses_zero_degrees(self):
        def provider(when, body):
            days = (when - self.start).total_seconds() / 86400
            return ((359 + 2 * days) % 360, 2) if body == "Sun" else (0, 0)

        query = OpportunitySearchQuery(
            self.start,
            self.end,
            conditions=(
                AspectCondition(
                    "sun_moon", "Sun", "Moon", ("Conjunction",), 0.5
                ),
            ),
        )

        windows = search_opportunities(query, _position_provider=provider)

        self.assertEqual(len(windows), 1)
        self.assertLess(
            abs(windows[0].start - (self.start + timedelta(hours=6))),
            timedelta(seconds=1),
        )
        self.assertLess(
            abs(windows[0].peak - (self.start + timedelta(hours=12))),
            timedelta(seconds=1),
        )
        self.assertLess(
            abs(windows[0].end - (self.start + timedelta(hours=18))),
            timedelta(seconds=1),
        )
        self.assertAlmostEqual(windows[0].score, 100, places=5)

    def test_retrograde_motion_creates_separate_reentries(self):
        def provider(when, body):
            days = (when - self.start).total_seconds() / 86400
            phase = 10 * (days - 0.5) * (days - 1) * (days - 1.5)
            speed = 10 * (
                (days - 1) * (days - 1.5)
                + (days - 0.5) * (days - 1.5)
                + (days - 0.5) * (days - 1)
            )
            return (phase % 360, speed) if body == "Mercury" else (0, 0)

        query = OpportunitySearchQuery(
            self.start,
            self.start + timedelta(days=2),
            conditions=(
                AspectCondition(
                    "mercury_sun",
                    "Mercury",
                    "Sun",
                    ("Conjunction",),
                    0.05,
                ),
            ),
        )

        windows = search_opportunities(query, _position_provider=provider)

        self.assertEqual(len(windows), 3)
        expected = [
            self.start + timedelta(days=0.5),
            self.start + timedelta(days=1),
            self.start + timedelta(days=1.5),
        ]
        for window, exact_time in zip(
            sorted(windows, key=lambda item: item.peak), expected
        ):
            self.assertLess(abs(window.peak - exact_time), timedelta(seconds=1))

    def test_required_moon_phase_and_aspect_are_intersected(self):
        def provider(when, body):
            days = (when - self.start).total_seconds() / 86400
            values = {
                "Sun": (0, 0),
                "Moon": ((170 + 20 * days) % 360, 20),
                "Jupiter": (0, 0),
                "Venus": ((118 + 4 * days) % 360, 4),
            }
            return values[body]

        query = OpportunitySearchQuery(
            self.start,
            self.end,
            conditions=(
                MoonPhaseCondition("full_moon", "full", 2, weight=1),
                AspectCondition(
                    "venus_jupiter",
                    "Venus",
                    "Jupiter",
                    ("Trine",),
                    1,
                    weight=2,
                ),
            ),
        )

        windows = search_opportunities(query, _position_provider=provider)

        self.assertEqual(len(windows), 1)
        self.assertLess(
            abs(windows[0].start - (self.start + timedelta(hours=9, minutes=36))),
            timedelta(seconds=1),
        )
        self.assertLess(
            abs(windows[0].peak - (self.start + timedelta(hours=12))),
            timedelta(seconds=1),
        )
        self.assertEqual(len(windows[0].evaluations), 2)
        self.assertTrue(all(item.matched for item in windows[0].evaluations))

    def test_optional_condition_changes_score_but_not_eligibility(self):
        def provider(when, body):
            days = (when - self.start).total_seconds() / 86400
            values = {
                "Jupiter": (0, 0),
                "Saturn": (0, 0),
                "Venus": ((357 + 4 * days) % 360, 4),
                "Mars": (0, 0),
            }
            return values[body]

        conditions = (
            AspectCondition(
                "required", "Jupiter", "Saturn", ("Conjunction",), 1
            ),
            AspectCondition(
                "optional",
                "Venus",
                "Mars",
                ("Conjunction",),
                0.5,
                required=False,
            ),
        )
        query = OpportunitySearchQuery(self.start, self.end, conditions=conditions)

        windows = search_opportunities(query, _position_provider=provider)

        self.assertEqual(len(windows), 1)
        self.assertLess(
            abs(windows[0].peak - (self.start + timedelta(hours=18))),
            timedelta(seconds=1),
        )
        self.assertAlmostEqual(windows[0].score, 100, places=5)

        unavailable = (
            conditions[0],
            AspectCondition(
                "optional",
                "Venus",
                "Mars",
                ("Opposition",),
                0.5,
                required=False,
            ),
        )
        fallback = search_opportunities(
            OpportunitySearchQuery(self.start, self.end, conditions=unavailable),
            _position_provider=provider,
        )
        self.assertEqual(len(fallback), 1)
        self.assertAlmostEqual(fallback[0].score, 50, places=5)

    def test_multiple_aspects_can_select_a_minor_aspect(self):
        def provider(when, body):
            return (150, 0) if body == "Mercury" else (0, 0)

        condition = AspectCondition(
            "minor",
            "Mercury",
            "Jupiter",
            ("Trine", "Quincunx"),
            1,
        )
        windows = search_opportunities(
            OpportunitySearchQuery(self.start, self.end, conditions=(condition,)),
            _position_provider=provider,
        )

        self.assertEqual(len(windows), 1)
        self.assertEqual(windows[0].start, self.start)
        self.assertEqual(windows[0].end, self.end)
        self.assertIn("Quincunx", windows[0].evaluations[0].description)
        self.assertAlmostEqual(windows[0].score, 100, places=5)

    def test_first_and_last_quarter_are_oriented(self):
        def provider(when, body):
            return (270, 0) if body == "Moon" else (0, 0)

        first = OpportunitySearchQuery(
            self.start,
            self.end,
            conditions=(MoonPhaseCondition("phase", "first_quarter", 1),),
        )
        last = OpportunitySearchQuery(
            self.start,
            self.end,
            conditions=(MoonPhaseCondition("phase", "last-quarter", 1),),
        )

        self.assertEqual(
            search_opportunities(first, _position_provider=provider), []
        )
        self.assertEqual(
            len(search_opportunities(last, _position_provider=provider)), 1
        )

    def test_real_full_moon_uses_the_exact_clock_time(self):
        query = OpportunitySearchQuery(
            datetime(2026, 7, 28, tzinfo=timezone.utc),
            datetime(2026, 7, 31, tzinfo=timezone.utc),
            conditions=(MoonPhaseCondition("full", "full", 8),),
        )

        windows = search_opportunities(query)

        self.assertEqual(len(windows), 1)
        self.assertLess(windows[0].evaluations[0].deviation_degrees, 0.001)
        self.assertNotEqual(
            (windows[0].peak.hour, windows[0].peak.minute), (0, 0)
        )

    def test_equal_scores_choose_the_earliest_exact_time(self):
        def provider(when, body):
            days = (when - self.start).total_seconds() / 86400
            return (40 + 160 * days, 160) if body == "Sun" else (0, 0)

        condition = AspectCondition(
            "choice", "Sun", "Moon", ("Sextile", "Trine"), 40
        )
        windows = search_opportunities(
            OpportunitySearchQuery(self.start, self.end, conditions=(condition,)),
            _position_provider=provider,
        )

        self.assertEqual(len(windows), 1)
        self.assertLess(
            abs(windows[0].peak - (self.start + timedelta(hours=3))),
            timedelta(seconds=1),
        )

    def test_transit_to_fixed_natal_planet(self):
        natal_datetime = datetime(1990, 1, 1, tzinfo=timezone.utc)

        def provider(when, body):
            if when.year == 1990 and body == "Sun":
                return (100, 0)
            days = (when - self.start).total_seconds() / 86400
            return (99 + 2 * days, 2) if body == "Mercury" else (0, 0)

        query = OpportunitySearchQuery(
            self.start,
            self.end,
            conditions=(
                NatalAspectCondition(
                    "mercury_natal_sun",
                    "Mercury",
                    "Sun",
                    ("Conjunction",),
                    0.5,
                ),
            ),
            natal_chart=NatalChart(
                natal_datetime,
                57.7,
                11.9,
                time_unknown=True,
            ),
        )

        windows = search_opportunities(query, _position_provider=provider)

        self.assertEqual(len(windows), 1)
        self.assertLess(
            abs(windows[0].peak - (self.start + timedelta(hours=12))),
            timedelta(seconds=1),
        )
        self.assertEqual(
            windows[0].evaluations[0].condition_type, "natal_aspect"
        )
        self.assertIn("natal Sun", windows[0].evaluations[0].description)

    def test_transit_to_natal_angle_and_house_cusp(self):
        natal_datetime = datetime(1990, 1, 1, tzinfo=timezone.utc)
        cusps = tuple(range(0, 360, 30))
        angles = (0, 270)

        def angle_provider(when, body):
            days = (when - self.start).total_seconds() / 86400
            return ((359 + 2 * days) % 360, 2) if body == "Mars" else (0, 0)

        angle_query = OpportunitySearchQuery(
            self.start,
            self.end,
            conditions=(
                NatalAspectCondition(
                    "mars_asc",
                    "Mars",
                    "Ascendant",
                    ("Conjunction",),
                    0.5,
                ),
            ),
            natal_chart=NatalChart(natal_datetime, 57.7, 11.9),
        )
        with patch(
            "astroscript.opportunity_search.calculate_house_cusps",
            return_value=(cusps, angles),
        ):
            angle_windows = search_opportunities(
                angle_query, _position_provider=angle_provider
            )

        def cusp_provider(when, body):
            days = (when - self.start).total_seconds() / 86400
            return (119 + 2 * days, 2) if body == "Mars" else (0, 0)

        cusp_query = OpportunitySearchQuery(
            self.start,
            self.end,
            conditions=(
                NatalAspectCondition(
                    "mars_house_5",
                    "Mars",
                    "House 5",
                    ("Conjunction",),
                    0.5,
                ),
            ),
            natal_chart=NatalChart(natal_datetime, 57.7, 11.9),
        )
        with patch(
            "astroscript.opportunity_search.calculate_house_cusps",
            return_value=(cusps, angles),
        ):
            cusp_windows = search_opportunities(
                cusp_query, _position_provider=cusp_provider
            )

        self.assertEqual(len(angle_windows), 1)
        self.assertEqual(len(cusp_windows), 1)
        self.assertLess(
            abs(angle_windows[0].peak - (self.start + timedelta(hours=12))),
            timedelta(seconds=1),
        )
        self.assertLess(
            abs(cusp_windows[0].peak - (self.start + timedelta(hours=12))),
            timedelta(seconds=1),
        )

    def test_transit_inside_selected_natal_house(self):
        natal_datetime = datetime(1990, 1, 1, tzinfo=timezone.utc)
        cusps = tuple(range(0, 360, 30))

        def provider(when, body):
            days = (when - self.start).total_seconds() / 86400
            return (25 + 10 * days, 10) if body == "Mars" else (0, 0)

        query = OpportunitySearchQuery(
            self.start,
            self.end,
            conditions=(
                TransitNatalHouseCondition("mars_house_2", "Mars", (2,)),
            ),
            natal_chart=NatalChart(natal_datetime, 57.7, 11.9),
        )
        with patch(
            "astroscript.opportunity_search.calculate_house_cusps",
            return_value=(cusps, (0, 270)),
        ):
            windows = search_opportunities(query, _position_provider=provider)

        self.assertEqual(len(windows), 1)
        self.assertLess(
            abs(windows[0].start - (self.start + timedelta(hours=12))),
            timedelta(seconds=1),
        )
        self.assertEqual(windows[0].end, self.end)
        self.assertEqual(windows[0].score, 100)
        self.assertIn("natal house 2", windows[0].evaluations[0].description)

    def test_unknown_natal_time_uses_noon_and_rejects_houses(self):
        natal_datetime = datetime(1990, 1, 1, 5, tzinfo=timezone.utc)
        natal_calls = []

        def provider(when, body):
            if when.year == 1990:
                natal_calls.append(when)
                return (100, 0)
            return (100, 0)

        planet_query = OpportunitySearchQuery(
            self.start,
            self.end,
            conditions=(
                NatalAspectCondition(
                    "sun",
                    "Mercury",
                    "Sun",
                    ("Conjunction",),
                    1,
                ),
            ),
            natal_chart=NatalChart(
                natal_datetime, 57.7, 11.9, time_unknown=True
            ),
        )
        search_opportunities(planet_query, _position_provider=provider)
        self.assertTrue(natal_calls)
        self.assertTrue(all(value.hour == 12 for value in natal_calls))

        house_query = OpportunitySearchQuery(
            self.start,
            self.end,
            conditions=(
                TransitNatalHouseCondition("house", "Mars", (1,)),
            ),
            natal_chart=planet_query.natal_chart,
        )
        with self.assertRaisesRegex(ValueError, "known birth time"):
            search_opportunities(house_query, _position_provider=provider)

    def test_real_natal_example_finds_solar_return_window(self):
        query = load_opportunity_query(
            ROOT_DIR / "examples" / "natal_opportunity_rules.json"
        )

        windows = search_opportunities(query)

        self.assertEqual(len(windows), 1)
        self.assertGreater(windows[0].score, 99.9)
        self.assertEqual(
            {evaluation.condition_type for evaluation in windows[0].evaluations},
            {"natal_aspect", "transit_natal_house"},
        )
        self.assertLess(windows[0].evaluations[0].deviation_degrees, 0.001)


class OpportunityJsonTests(unittest.TestCase):
    def setUp(self):
        self.rules = {
            "start": "2026-07-01 00:00",
            "end": "2026-08-01 00:00",
            "timezone": "Europe/Stockholm",
            "conditions": [
                {
                    "id": "full_moon",
                    "type": "moon_phase",
                    "phase": "full",
                    "max_deviation_degrees": 8,
                    "required": True,
                    "weight": 1,
                },
                {
                    "id": "venus_jupiter",
                    "type": "aspect",
                    "body1": "Venus",
                    "body2": "Jupiter",
                    "aspects": ["Trine"],
                    "max_orb_degrees": 2,
                    "required": True,
                    "weight": 2,
                },
            ],
        }

    def test_json_rules_are_localized_and_typed(self):
        query = opportunity_query_from_dict(self.rules)

        self.assertEqual(query.timezone, "Europe/Stockholm")
        self.assertEqual(
            query.start.astimezone(timezone.utc),
            datetime(2026, 6, 30, 22, tzinfo=timezone.utc),
        )
        self.assertIsInstance(query.conditions[0], MoonPhaseCondition)
        self.assertIsInstance(query.conditions[1], AspectCondition)

    def test_rule_file_loader_reads_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rules.json"
            path.write_text(json.dumps(self.rules), encoding="utf-8")
            query = load_opportunity_query(path)
        self.assertEqual(len(query.conditions), 2)

    def test_json_supports_natal_aspects_houses_and_angles(self):
        rules = {
            "start": "2026-07-01 00:00",
            "end": "2026-08-01 00:00",
            "timezone": "Europe/Stockholm",
            "natal_chart": {
                "datetime": "1990-01-01 14:30",
                "timezone": "Europe/Stockholm",
                "latitude": 57.7,
                "longitude": 11.9,
                "house_system": "Placidus",
                "time_unknown": False,
            },
            "conditions": [
                {
                    "id": "jupiter_sun",
                    "type": "natal_aspect",
                    "transit_body": "Jupiter",
                    "natal_target": "Sun",
                    "aspects": ["Trine"],
                    "max_orb_degrees": 2,
                },
                {
                    "id": "mars_asc",
                    "type": "natal_aspect",
                    "transit_body": "Mars",
                    "natal_target": "Ascendant",
                    "aspects": ["Conjunction"],
                    "max_orb_degrees": 1,
                },
                {
                    "id": "venus_houses",
                    "type": "transit_natal_house",
                    "transit_body": "Venus",
                    "houses": [5, 7],
                    "required": False,
                },
            ],
        }

        query = opportunity_query_from_dict(rules)

        self.assertIsInstance(query.natal_chart, NatalChart)
        self.assertIsInstance(query.conditions[0], NatalAspectCondition)
        self.assertEqual(query.conditions[1].natal_target, "Ascendant")
        self.assertIsInstance(query.conditions[2], TransitNatalHouseCondition)

    def test_unknown_natal_time_is_normalized_to_local_noon(self):
        rules = copy.deepcopy(self.rules)
        rules["natal_chart"] = {
            "datetime": "1990-01-01 05:00",
            "timezone": "Europe/Stockholm",
            "latitude": 57.7,
            "longitude": 11.9,
            "time_unknown": True,
        }
        rules["conditions"] = [
            {
                "id": "natal_sun",
                "type": "natal_aspect",
                "transit_body": "Jupiter",
                "natal_target": "Sun",
                "aspects": ["Trine"],
                "max_orb_degrees": 2,
            }
        ]

        query = opportunity_query_from_dict(rules)

        self.assertEqual(query.natal_chart.datetime.hour, 12)
        self.assertTrue(query.natal_chart.time_unknown)

    def test_invalid_rules_are_rejected(self):
        cases = []
        unknown_body = copy.deepcopy(self.rules)
        unknown_body["conditions"][1]["body1"] = "Vulcan"
        cases.append(unknown_body)
        unknown_aspect = copy.deepcopy(self.rules)
        unknown_aspect["conditions"][1]["aspects"] = ["Not an aspect"]
        cases.append(unknown_aspect)
        unknown_phase = copy.deepcopy(self.rules)
        unknown_phase["conditions"][0]["phase"] = "blue"
        cases.append(unknown_phase)
        negative_orb = copy.deepcopy(self.rules)
        negative_orb["conditions"][1]["max_orb_degrees"] = -1
        cases.append(negative_orb)
        negative_weight = copy.deepcopy(self.rules)
        negative_weight["conditions"][0]["weight"] = -1
        cases.append(negative_weight)
        bad_timezone = copy.deepcopy(self.rules)
        bad_timezone["timezone"] = "Mars/Olympus"
        cases.append(bad_timezone)
        reversed_period = copy.deepcopy(self.rules)
        reversed_period["end"] = "2026-06-01 00:00"
        cases.append(reversed_period)
        unknown_field = copy.deepcopy(self.rules)
        unknown_field["conditions"][0]["orb"] = 8
        cases.append(unknown_field)
        duplicate_ids = copy.deepcopy(self.rules)
        duplicate_ids["conditions"][1]["id"] = "full_moon"
        cases.append(duplicate_ids)
        missing_natal = copy.deepcopy(self.rules)
        missing_natal["conditions"] = [
            {
                "id": "natal",
                "type": "natal_aspect",
                "transit_body": "Jupiter",
                "natal_target": "Sun",
                "aspects": ["Trine"],
                "max_orb_degrees": 2,
            }
        ]
        cases.append(missing_natal)
        invalid_house = copy.deepcopy(self.rules)
        invalid_house["natal_chart"] = {
            "datetime": "1990-01-01 12:00",
            "timezone": "UTC",
            "latitude": 57.7,
            "longitude": 11.9,
        }
        invalid_house["conditions"] = [
            {
                "id": "house",
                "type": "transit_natal_house",
                "transit_body": "Mars",
                "houses": [13],
            }
        ]
        cases.append(invalid_house)

        for rules in cases:
            with self.subTest(rules=rules), self.assertRaises((ValueError, KeyError)):
                opportunity_query_from_dict(rules)


class OpportunityCliTests(unittest.TestCase):
    def test_cli_option_is_parsed(self):
        with patch.object(
            sys,
            "argv",
            ["astro_script.py", "--opportunity-search", "rules.json"],
        ):
            arguments = argparser()
        self.assertEqual(arguments["Opportunity Search"], "rules.json")

    def test_cli_formats_ranked_windows(self):
        query = OpportunitySearchQuery(
            datetime(2026, 7, 1, tzinfo=timezone.utc),
            datetime(2026, 7, 2, tzinfo=timezone.utc),
            conditions=(MoonPhaseCondition("full", "full", 8),),
            timezone="Europe/Stockholm",
        )
        evaluation = ConditionEvaluation(
            "full",
            "moon_phase",
            True,
            True,
            100,
            0,
            8,
            "Moon phase full: deviation 0.0000° / 8.0000°",
        )
        window = OpportunityWindow(
            query.start,
            query.start + timedelta(hours=1),
            query.start + timedelta(hours=2),
            100,
            (evaluation,),
        )
        args = {"Opportunity Search": "rules.json", "Output": "return_text"}

        with patch(
            "astroscript.cli.load_opportunity_query", return_value=query
        ), patch(
            "astroscript.cli.search_opportunities", return_value=[window]
        ):
            result = run_opportunity_search(args)

        self.assertIn("Best time", result)
        self.assertIn("100.0", result)
        self.assertIn("2026-07-01 03:00:00 CEST", result)
        self.assertIn("Moon phase full", result)

    def test_main_routes_search_before_natal_flow(self):
        args = {"Opportunity Search": "rules.json", "Output": "return_text"}
        with patch(
            "astroscript.cli.run_opportunity_search", return_value="windows"
        ) as opportunity, patch("astroscript.cli.load_event") as load_event:
            result = main(args)

        self.assertEqual(result, "windows")
        opportunity.assert_called_once_with(args)
        load_event.assert_not_called()

    def test_main_rejects_combining_search_modes(self):
        args = {
            "Opportunity Search": "rules.json",
            "Aspect Period": ["2026-07-01 00:00", "2026-07-02 00:00"],
            "Output": "return_text",
        }
        self.assertIn("cannot be combined", main(args))


if __name__ == "__main__":
    unittest.main()

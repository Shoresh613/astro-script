import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytz


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from astroscript.aspect_search import (
    ASTEROID_BODY_IDS,
    DEFAULT_BODIES,
    SUPPORTED_BODY_IDS,
    AspectEvent,
    AspectSearchQuery,
    search_exact_aspects,
)
from astroscript.cli import argparser, main, run_aspect_period
from astroscript.constants import MAJOR_ASPECTS, PLANETS
from astroscript.aspects import find_exact_aspects_in_timeframe
from astroscript.fixed_stars import CURATED_FIXED_STAR_NAMES, read_fixed_stars


class AspectSearchTests(unittest.TestCase):
    def setUp(self):
        self.start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def _query(self, end_days=1, aspects=None):
        return AspectSearchQuery(
            self.start,
            self.start + timedelta(days=end_days),
            bodies=("Sun", "Moon"),
            aspect_types=aspects or {"Conjunction": 0},
        )

    def test_defaults_use_major_aspects_and_planets_without_angles(self):
        valid_planets = tuple(
            name for name, body_id in PLANETS.items() if isinstance(body_id, int)
        )
        self.assertEqual(DEFAULT_BODIES, valid_planets)
        self.assertNotIn("Ascendant", DEFAULT_BODIES)
        self.assertNotIn("Ceres", DEFAULT_BODIES)
        self.assertEqual(
            set(ASTEROID_BODY_IDS), {"Ceres", "Pholus", "Pallas", "Juno", "Vesta"}
        )
        self.assertIn("Juno", SUPPORTED_BODY_IDS)
        self.assertNotIn("Regulus", DEFAULT_BODIES)
        self.assertIn("Regulus", CURATED_FIXED_STAR_NAMES)
        self.assertEqual(
            set(CURATED_FIXED_STAR_NAMES), set(read_fixed_stars(all_stars=False))
        )
        self.assertEqual(set(MAJOR_ASPECTS), {
            "Conjunction", "Opposition", "Square", "Trine", "Sextile"
        })

    def test_conjunction_is_found_across_zero_degrees(self):
        def provider(when, body):
            days = (when - self.start).total_seconds() / 86400
            return ((359 + 2 * days) % 360, 2) if body == "Sun" else (0, 0)

        events = search_exact_aspects(
            self._query(), _position_provider=provider
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].aspect, "Conjunction")
        self.assertLess(
            abs(events[0].exact_at - (self.start + timedelta(hours=12))),
            timedelta(seconds=1),
        )

    def test_opposition_is_found_across_180_degrees(self):
        def provider(when, body):
            days = (when - self.start).total_seconds() / 86400
            return ((179 + 2 * days) % 360, 2) if body == "Sun" else (0, 0)

        events = search_exact_aspects(
            self._query(aspects={"Opposition": 180}),
            _position_provider=provider,
        )

        self.assertEqual(len(events), 1)
        self.assertLess(
            abs(events[0].exact_at - (self.start + timedelta(hours=12))),
            timedelta(seconds=1),
        )

    def test_boundary_hit_is_included_once(self):
        def provider(when, body):
            days = (when - self.start).total_seconds() / 86400
            return (days % 360, 1) if body == "Sun" else (0, 0)

        events = search_exact_aspects(
            self._query(), _position_provider=provider
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].exact_at, self.start)

    def test_end_boundary_hit_is_included(self):
        def provider(when, body):
            days = (when - self.start).total_seconds() / 86400
            return ((days - 1) % 360, 1) if body == "Sun" else (0, 0)

        events = search_exact_aspects(
            self._query(), _position_provider=provider
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].exact_at, self.start + timedelta(days=1))

    def test_retrograde_motion_can_produce_three_passages(self):
        def provider(when, body):
            days = (when - self.start).total_seconds() / 86400
            phase = 10 * (days - 0.5) * (days - 1) * (days - 1.5)
            speed = 10 * (
                (days - 1) * (days - 1.5)
                + (days - 0.5) * (days - 1.5)
                + (days - 0.5) * (days - 1)
            )
            return (phase % 360, speed) if body == "Sun" else (0, 0)

        events = search_exact_aspects(
            self._query(end_days=2), _position_provider=provider
        )

        expected = [
            self.start + timedelta(days=0.5),
            self.start + timedelta(days=1),
            self.start + timedelta(days=1.5),
        ]
        self.assertEqual(len(events), 3)
        for event, expected_time in zip(events, expected):
            self.assertLess(abs(event.exact_at - expected_time), timedelta(seconds=1))

    def test_tangential_hit_at_station_is_found(self):
        exact_time = self.start + timedelta(days=1.1)

        def provider(when, body):
            days = (when - exact_time).total_seconds() / 86400
            return ((days * days) % 360, 2 * days) if body == "Sun" else (0, 0)

        events = search_exact_aspects(
            self._query(end_days=2), _position_provider=provider
        )

        self.assertEqual(len(events), 1)
        self.assertLess(abs(events[0].exact_at - exact_time), timedelta(seconds=1))

    def test_invalid_period_and_naive_datetimes_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "timezone"):
            search_exact_aspects(
                AspectSearchQuery(
                    datetime(2026, 1, 1),
                    datetime(2026, 1, 2),
                    bodies=("Sun", "Moon"),
                ),
                _position_provider=lambda when, body: (0, 0),
            )
        with self.assertRaisesRegex(ValueError, "greater than"):
            search_exact_aspects(
                AspectSearchQuery(
                    self.start + timedelta(days=1),
                    self.start,
                    bodies=("Sun", "Moon"),
                ),
                _position_provider=lambda when, body: (0, 0),
            )

    def test_empty_and_unknown_filters_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "aspect"):
            search_exact_aspects(
                AspectSearchQuery(
                    self.start,
                    self.start,
                    bodies=("Sun", "Moon"),
                    aspect_types={},
                ),
                _position_provider=lambda when, body: (0, 0),
            )
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            search_exact_aspects(
                AspectSearchQuery(
                    self.start,
                    self.start,
                    bodies=("Sun", "Not a planet"),
                ),
                _position_provider=lambda when, body: (0, 0),
            )

    def test_real_ephemeris_result_is_exact(self):
        query = AspectSearchQuery(
            datetime(2026, 7, 5, tzinfo=timezone.utc),
            datetime(2026, 7, 6, tzinfo=timezone.utc),
            bodies=("Sun", "Moon"),
        )

        events = search_exact_aspects(query)

        trines = [event for event in events if event.aspect == "Trine"]
        self.assertEqual(len(trines), 1)
        separation = abs(trines[0].body1_longitude - trines[0].body2_longitude) % 360
        separation = min(separation, 360 - separation)
        self.assertAlmostEqual(separation, 120, delta=0.001)

    def test_explicit_asteroid_search_finds_exact_aspect(self):
        query = AspectSearchQuery(
            datetime(2026, 7, 9, tzinfo=timezone.utc),
            datetime(2026, 7, 10, tzinfo=timezone.utc),
            bodies=("Mars", "Juno"),
        )

        events = search_exact_aspects(query)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].aspect, "Trine")
        self.assertEqual((events[0].body1, events[0].body2), ("Mars", "Juno"))
        separation = abs(events[0].body1_longitude - events[0].body2_longitude) % 360
        separation = min(separation, 360 - separation)
        self.assertAlmostEqual(separation, 120, delta=0.001)

    def test_curated_fixed_star_search_finds_exact_conjunction(self):
        query = AspectSearchQuery(
            datetime(2026, 8, 22, tzinfo=timezone.utc),
            datetime(2026, 8, 24, tzinfo=timezone.utc),
            bodies=("Sun", "Regulus"),
        )

        events = search_exact_aspects(query)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].aspect, "Conjunction")
        self.assertEqual((events[0].body1, events[0].body2), ("Sun", "Regulus"))
        self.assertAlmostEqual(
            events[0].body1_longitude,
            events[0].body2_longitude,
            delta=0.001,
        )

    def test_non_curated_fixed_star_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            search_exact_aspects(
                AspectSearchQuery(
                    self.start,
                    self.start,
                    bodies=("Sun", "Betelgeuse"),
                )
            )

    def test_tropical_and_sidereal_find_same_sun_moon_time(self):
        values = dict(
            start=datetime(2026, 7, 5, tzinfo=timezone.utc),
            end=datetime(2026, 7, 6, tzinfo=timezone.utc),
            bodies=("Sun", "Moon"),
        )

        tropical = search_exact_aspects(AspectSearchQuery(**values))
        sidereal = search_exact_aspects(
            AspectSearchQuery(**values, zodiac="sidereal")
        )

        self.assertEqual(len(tropical), len(sidereal))
        self.assertLess(
            abs(tropical[0].exact_at - sidereal[0].exact_at),
            timedelta(seconds=1),
        )

    def test_legacy_wrapper_keeps_dictionary_response_without_printing(self):
        event = AspectEvent(
            exact_at=self.start,
            body1="Sun",
            body2="Moon",
            aspect="Trine",
            aspect_angle=120,
            body1_longitude=10,
            body2_longitude=250,
            body1_speed=1,
            body2_speed=13,
        )
        with patch(
            "astroscript.aspect_search.search_exact_aspects", return_value=[event]
        ) as search, patch("builtins.print") as output:
            result = find_exact_aspects_in_timeframe(
                datetime(2026, 1, 1),
                datetime(2026, 1, 2),
                57.7,
                11.9,
                0,
                {"Major": 6},
                "geocentric",
                output_type="text",
            )

        self.assertEqual(result[0]["planet1"], "Sun")
        self.assertEqual(result[0]["aspect"], "Trine")
        self.assertEqual(search.call_args.args[0].start.tzinfo, timezone.utc)
        output.assert_not_called()


class AspectSearchCliTests(unittest.TestCase):
    def test_cli_alias_is_parsed(self):
        argv = [
            "astro_script.py",
            "--aspect-period",
            "2026-07-01 00:00",
            "2026-07-02 00:00",
        ]
        with patch.object(sys, "argv", argv):
            arguments = argparser()
        self.assertEqual(
            arguments["Aspect Period"],
            ["2026-07-01 00:00", "2026-07-02 00:00"],
        )

    def test_cli_converts_local_period_and_formats_results(self):
        event = AspectEvent(
            exact_at=datetime(2026, 7, 1, 10, tzinfo=timezone.utc),
            body1="Sun",
            body2="Moon",
            aspect="Trine",
            aspect_angle=120,
            body1_longitude=100,
            body2_longitude=340,
            body1_speed=1,
            body2_speed=13,
        )
        args = {
            "Aspect Period": ["2026-07-01 00:00", "2026-07-02 00:00"],
            "Timezone": "Europe/Stockholm",
            "Output": "return_text",
            "Center": None,
            "Latitude": None,
            "Longitude": None,
            "Zodiac": None,
        }

        with patch(
            "astroscript.cli.search_exact_aspects", return_value=[event]
        ) as search:
            result = run_aspect_period(args)

        query = search.call_args.args[0]
        self.assertEqual(
            query.start.astimezone(timezone.utc),
            datetime(2026, 6, 30, 22, tzinfo=timezone.utc),
        )
        self.assertIn("2026-07-01 12:00:00 CEST", result)
        self.assertIn("Sun", result)
        self.assertIn("Trine", result)

    def test_cli_rejects_nonexistent_dst_time(self):
        args = {
            "Aspect Period": ["2026-03-29 02:30", "2026-03-29 04:00"],
            "Timezone": "Europe/Stockholm",
            "Output": "return_text",
        }
        with self.assertRaises(pytz.NonExistentTimeError):
            run_aspect_period(args)

    def test_topocentric_cli_requires_explicit_coordinates(self):
        args = {
            "Aspect Period": ["2026-07-01 00:00", "2026-07-02 00:00"],
            "Timezone": "Europe/Stockholm",
            "Output": "return_text",
            "Center": "topocentric",
            "Latitude": None,
            "Longitude": None,
        }
        with self.assertRaisesRegex(ValueError, "latitude"):
            run_aspect_period(args)

    def test_main_routes_period_before_natal_event_loading(self):
        args = {
            "Aspect Period": ["2026-07-01 00:00", "2026-07-02 00:00"],
            "Output": "return_text",
        }
        with patch(
            "astroscript.cli.run_aspect_period", return_value="period result"
        ) as period, patch("astroscript.cli.load_event") as load_event:
            result = main(args)

        self.assertEqual(result, "period result")
        period.assert_called_once_with(args)
        load_event.assert_not_called()

    def test_main_returns_readable_period_validation_errors(self):
        args = {
            "Aspect Period": ["2026-03-29 02:30", "2026-03-29 04:00"],
            "Timezone": "Europe/Stockholm",
            "Output": "return_text",
        }
        self.assertIn("Invalid aspect period", main(args))

        html_args = {
            "Aspect Period": ["2026-07-01 00:00", "2026-07-02 00:00"],
            "Output": "html",
        }
        with patch("builtins.print") as output:
            self.assertEqual(
                main(html_args),
                "Invalid aspect period: Aspect-period searches support "
                "output_type text or return_text.",
            )
        output.assert_called_once()


if __name__ == "__main__":
    unittest.main()

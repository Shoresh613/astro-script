import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import swisseph as swe

from astroscript import positions
from astroscript.cli import argparser
from astroscript.fixed_stars import get_fixed_star_position
from astroscript.houses import calculate_house_positions, find_house_number
from astroscript.zodiac import get_ayanamsha_ut, normalize_zodiac, zodiac_label


class ZodiacCalculationTests(unittest.TestCase):
    def setUp(self):
        self.when = datetime(1990, 1, 1, 12, 0, tzinfo=timezone.utc)
        self.latitude = 57.7
        self.longitude = 11.9
        self.jd = swe.julday(1990, 1, 1, 12.0)

    def _planet_positions(self, zodiac=None):
        kwargs = {}
        if zodiac is not None:
            kwargs["zodiac"] = zodiac
        bodies = {"Sun": swe.SUN, "North Node": swe.TRUE_NODE}
        with patch.dict(positions.PLANETS, bodies, clear=True):
            return positions.calculate_planet_positions(
                self.when,
                self.latitude,
                self.longitude,
                0,
                "return_text",
                center="geocentric",
                **kwargs,
            )

    def _asteroid_positions(self, zodiac):
        with patch.dict(positions.ASTEROIDS, {"Ceres": swe.CERES}, clear=True):
            return positions.calculate_planet_positions(
                self.when,
                self.latitude,
                self.longitude,
                0,
                "return_text",
                mode="asteroids",
                center="geocentric",
                zodiac=zodiac,
            )

    def test_tropical_default_is_unchanged(self):
        default = self._planet_positions()
        explicit = self._planet_positions("tropical")
        expected = swe.calc_ut(
            self.jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SPEED
        )[0][0]

        self.assertAlmostEqual(
            default["Sun"]["longitude"], explicit["Sun"]["longitude"], places=8
        )
        self.assertAlmostEqual(default["Sun"]["longitude"], expected, places=8)

    def test_sidereal_and_vedic_use_identical_lahiri_positions(self):
        tropical = self._planet_positions("tropical")
        sidereal = self._planet_positions("sidereal")
        vedic = self._planet_positions("vedic")
        ayanamsha = get_ayanamsha_ut(self.jd, "sidereal")
        expected_sun = (tropical["Sun"]["longitude"] - ayanamsha) % 360

        self.assertAlmostEqual(
            sidereal["Sun"]["longitude"], vedic["Sun"]["longitude"], places=8
        )
        self.assertAlmostEqual(sidereal["Sun"]["longitude"], expected_sun, delta=0.01)
        self.assertEqual(normalize_zodiac("vedic"), "sidereal")
        self.assertEqual(zodiac_label("vedic"), "Sidereal (Lahiri/Vedic)")

    def test_asteroids_follow_the_selected_zodiac(self):
        tropical = self._asteroid_positions("tropical")
        sidereal = self._asteroid_positions("sidereal")
        vedic = self._asteroid_positions("vedic")
        ayanamsha = get_ayanamsha_ut(self.jd, "sidereal")
        expected_ceres = (tropical["Ceres"]["longitude"] - ayanamsha) % 360

        self.assertAlmostEqual(
            sidereal["Ceres"]["longitude"], vedic["Ceres"]["longitude"], places=8
        )
        self.assertAlmostEqual(
            sidereal["Ceres"]["longitude"], expected_ceres, delta=0.01
        )
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        expected_cusps = swe.houses_ex(
            self.jd,
            self.latitude,
            self.longitude,
            b"P",
            swe.FLG_SIDEREAL,
        )[0]
        self.assertEqual(
            sidereal["Ceres"]["house"],
            find_house_number(sidereal["Ceres"]["longitude"], expected_cusps),
        )

    def test_sidereal_houses_and_angles_use_houses_ex(self):
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        expected_cusps, expected_angles = swe.houses_ex(
            self.jd,
            self.latitude,
            self.longitude,
            b"P",
            swe.FLG_SIDEREAL,
        )
        planet_longitude = 10.0
        house_positions, cusps = calculate_house_positions(
            self.when,
            self.latitude,
            self.longitude,
            0,
            {"Test Body": {"longitude": planet_longitude}},
            zodiac="vedic",
        )

        self.assertAlmostEqual(cusps[0], expected_cusps[0], places=8)
        self.assertAlmostEqual(
            house_positions["Ascendant"]["longitude"], expected_angles[0], places=8
        )
        self.assertEqual(
            house_positions["Test Body"]["house"],
            find_house_number(planet_longitude, expected_cusps),
        )

    def test_house_assignment_handles_zodiac_wraparound(self):
        cusps = [350, 20, 50, 80, 110, 140, 170, 200, 230, 260, 290, 320]
        self.assertEqual(find_house_number(355, cusps), 1)
        self.assertEqual(find_house_number(10, cusps), 1)
        self.assertEqual(find_house_number(340, cusps), 12)

    def test_fixed_stars_receive_sidereal_flags(self):
        fake_position = ((123.0, 0.0, 1.0, 0.0, 0.0, 0.0), "Spica")
        with patch(
            "astroscript.fixed_stars.swe.fixstar_ut", return_value=fake_position
        ) as fixstar_ut:
            longitude = get_fixed_star_position("Spica", self.jd, zodiac="vedic")

        flags = fixstar_ut.call_args.args[2]
        self.assertEqual(longitude, 123.0)
        self.assertTrue(flags & swe.FLG_SIDEREAL)

    def test_cli_accepts_vedic_alias(self):
        with patch.object(sys, "argv", ["astro_script.py", "--zodiac", "vedic"]):
            arguments = argparser()
        self.assertEqual(arguments["Zodiac"], "vedic")


if __name__ == "__main__":
    unittest.main()

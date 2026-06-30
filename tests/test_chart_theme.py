import sys
import tempfile
import types
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from charts import chart_output


class ChartThemeTests(unittest.TestCase):
    def test_dark_theme_is_passed_to_kerykeion_and_uses_dark_svg_name(self):
        class FakeSubject:
            def __init__(self, name, **kwargs):
                self.name = name

        class FakeChart:
            calls = []

            def __init__(self, subject, chart_type, *args, **kwargs):
                self.subject = subject
                self.chart_type = chart_type
                self.output_directory = Path(kwargs["new_output_directory"])
                FakeChart.calls.append(kwargs)

            def makeSVG(self):
                self.output_directory.mkdir(parents=True, exist_ok=True)
                chart_path = (
                    self.output_directory
                    / f"{self.subject.name} - {self.chart_type} Chart.svg"
                )
                chart_path.write_text("<svg></svg>")

        fake_kerykeion = types.SimpleNamespace(
            AstrologicalSubject=FakeSubject,
            KerykeionChartSVG=FakeChart,
        )

        original_file = chart_output.__file__
        with tempfile.TemporaryDirectory() as temp_dir, \
                patch.dict(sys.modules, {"kerykeion": fake_kerykeion}):
            try:
                chart_output.__file__ = str(
                    Path(temp_dir) / "src" / "charts" / "chart_output.py"
                )
                html = chart_output.chart_output(
                    "Dark Test",
                    datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
                    11.9,
                    57.7,
                    "UTC",
                    "Gothenburg",
                    "Natal",
                    "return_html",
                    None,
                    guid="theme-test",
                    chart_theme="dark",
                )
            finally:
                chart_output.__file__ = original_file

            generated_chart = (
                Path(temp_dir)
                / "static"
                / "theme-test"
                / "Dark Test - Natal Chart Dark.svg"
            )
            generated_chart_exists = generated_chart.exists()

        self.assertEqual(FakeChart.calls[0]["theme"], "dark")
        self.assertIn("Dark%20Test%20-%20Natal%20Chart%20Dark.svg", html)
        self.assertTrue(generated_chart_exists)

    def test_sidereal_chart_passes_lahiri_settings_to_kerykeion(self):
        class FakeSubject:
            calls = []

            def __init__(self, name, **kwargs):
                self.name = name
                FakeSubject.calls.append(kwargs)

        class FakeChart:
            def __init__(self, subject, chart_type, *args, **kwargs):
                self.subject = subject
                self.chart_type = chart_type
                self.output_directory = Path(kwargs["new_output_directory"])

            def makeSVG(self):
                self.output_directory.mkdir(parents=True, exist_ok=True)
                chart_path = (
                    self.output_directory
                    / f"{self.subject.name} - {self.chart_type} Chart.svg"
                )
                chart_path.write_text("<svg></svg>")

        fake_kerykeion = types.SimpleNamespace(
            AstrologicalSubject=FakeSubject,
            KerykeionChartSVG=FakeChart,
        )

        original_file = chart_output.__file__
        with tempfile.TemporaryDirectory() as temp_dir, patch.dict(
            sys.modules, {"kerykeion": fake_kerykeion}
        ):
            try:
                chart_output.__file__ = str(
                    Path(temp_dir) / "src" / "charts" / "chart_output.py"
                )
                chart_output.chart_output(
                    "Sidereal Test",
                    datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
                    11.9,
                    57.7,
                    "UTC",
                    "Gothenburg",
                    "Natal",
                    "return_html",
                    None,
                    guid="sidereal-test",
                    zodiac="vedic",
                )
            finally:
                chart_output.__file__ = original_file

        self.assertEqual(FakeSubject.calls[0]["zodiac_type"], "Sidereal")
        self.assertEqual(FakeSubject.calls[0]["sidereal_mode"], "LAHIRI")

    def test_legacy_kerykeion_without_theme_argument_falls_back_to_classic(self):
        class FakeSubject:
            def __init__(self, name, **kwargs):
                self.name = name

        class LegacyChart:
            def __init__(
                self,
                subject,
                chart_type,
                *args,
                new_output_directory,
            ):
                self.subject = subject
                self.chart_type = chart_type
                self.output_directory = Path(new_output_directory)

            def makeSVG(self):
                self.output_directory.mkdir(parents=True, exist_ok=True)
                chart_path = (
                    self.output_directory
                    / f"{self.subject.name} {self.chart_type}Chart.svg"
                )
                chart_path.write_text("<svg></svg>")

        fake_kerykeion = types.SimpleNamespace(
            AstrologicalSubject=FakeSubject,
            KerykeionChartSVG=LegacyChart,
        )

        original_file = chart_output.__file__
        with tempfile.TemporaryDirectory() as temp_dir, patch.dict(
            sys.modules, {"kerykeion": fake_kerykeion}
        ):
            try:
                chart_output.__file__ = str(
                    Path(temp_dir) / "src" / "charts" / "chart_output.py"
                )
                html = chart_output.chart_output(
                    "Legacy Test",
                    datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
                    11.9,
                    57.7,
                    "UTC",
                    "Gothenburg",
                    "Natal",
                    "return_html",
                    None,
                    guid="legacy-theme-test",
                    chart_theme="dark",
                    zodiac="sidereal",
                )
            finally:
                chart_output.__file__ = original_file

        self.assertIn("Legacy%20Test%20-%20Natal%20Chart.svg", html)
        self.assertNotIn("Chart%20Dark.svg", html)


if __name__ == "__main__":
    unittest.main()

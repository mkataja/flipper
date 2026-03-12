import os
import sys
import types
import unittest
from datetime import datetime
from unittest.mock import patch

import pytz

sys.path.insert(0, os.path.abspath("src"))

timezonefinder_module = types.ModuleType("timezonefinder")


class _TimezoneFinder:
    def timezone_at(self, lat=None, lng=None):
        _ = (lat, lng)
        return "UTC"


timezonefinder_module.TimezoneFinder = _TimezoneFinder
sys.modules["timezonefinder"] = timezonefinder_module

from lib import sun  # noqa: E402


class SunFormattingTest(unittest.TestCase):
    def test_sunrise_sunset_and_day_length_use_location_timezone(self):
        sunrise_utc = datetime(2026, 1, 15, 0, 0, 0)
        sunset_utc = datetime(2026, 1, 15, 10, 0, 0)

        with patch(
            "lib.sun.sun_times",
            return_value={"sunrise": sunrise_utc, "sunset": sunset_utc},
        ):
            sentence = sun.format_sun_times_sentence(
                datetime(2026, 1, 15),
                35.6762,
                139.6503,
                pytz.timezone("Asia/Tokyo"),
            )

        self.assertIn("Aurinko nousee 09:00", sentence)
        self.assertIn("laskee 19:00", sentence)
        self.assertIn("päivän pituus 10 h 00 min", sentence)

    def test_formats_when_sun_only_rises(self):
        sunrise_utc = datetime(2026, 1, 15, 0, 0, 0)

        with patch(
            "lib.sun.sun_times",
            return_value={"sunrise": sunrise_utc, "sunset": None},
        ):
            sentence = sun.format_sun_times_sentence(
                datetime(2026, 1, 15),
                35.6762,
                139.6503,
                pytz.timezone("Asia/Tokyo"),
            )

        self.assertEqual(
            sentence,
            "Aurinko nousee 09:00 ja yötön yö alkaa.",
        )

    def test_formats_when_sun_only_sets(self):
        sunset_utc = datetime(2026, 1, 15, 10, 0, 0)

        with patch(
            "lib.sun.sun_times",
            return_value={"sunrise": None, "sunset": sunset_utc},
        ):
            sentence = sun.format_sun_times_sentence(
                datetime(2026, 1, 15),
                35.6762,
                139.6503,
                pytz.timezone("Asia/Tokyo"),
            )

        self.assertEqual(
            sentence,
            "Yötön yö loppuu - aurinko laskee 19:00.",
        )

    def test_utsjoki_2026_05_16_midnight_sun_begins(self):
        sentence = sun.format_sun_times_sentence(
            datetime(2026, 5, 16),
            69.9087,
            27.0284,
            pytz.timezone("Europe/Helsinki"),
        )

        self.assertEqual(
            sentence,
            "Aurinko nousee 01:43 ja yötön yö alkaa.",
        )

    def test_utsjoki_2026_05_17_midnight_sun(self):
        sentence = sun.format_sun_times_sentence(
            datetime(2026, 5, 17),
            69.9087,
            27.0284,
            pytz.timezone("Europe/Helsinki"),
        )

        self.assertEqual(
            sentence,
            "Yötön yö eli polaaripäivä - aurinko ei laske kyseisenä päivänä.",
        )

    def test_utsjoki_2026_12_21_polar_night(self):
        sentence = sun.format_sun_times_sentence(
            datetime(2026, 12, 21),
            69.9087,
            27.0284,
            pytz.timezone("Europe/Helsinki"),
        )

        self.assertEqual(
            sentence,
            "Kaamos eli polaariyö - aurinko ei nouse kyseisenä päivänä.",
        )


if __name__ == "__main__":
    unittest.main()

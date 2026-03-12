import os
import sys
import unittest
from unittest.mock import patch

import pytz

sys.path.insert(0, os.path.abspath("src"))

from commands.openweathermapcommand import OpenWeatherMapCommand


def _sample_weather_data():
    return {
        "name": "Tokyo",
        "dt": 1736899200,  # 2025-01-15 00:00:00 UTC
        "sys": {"country": "JP", "sunrise": 1736906400, "sunset": 1736941200},
        "coord": {"lat": 35.6762, "lon": 139.6503},
        "weather": [{"id": 800}],
        "main": {
            "temp": 280.0,
            "temp_min": 279.0,
            "temp_max": 281.0,
            "humidity": 70,
            "pressure": 1012,
        },
        "wind": {"deg": 10, "speed": 3.5},
        "clouds": {"all": 20},
    }


class OpenWeatherMapTimezoneTest(unittest.TestCase):
    def test_main_timestamp_and_sun_times_use_same_location_timezone(self):
        command = OpenWeatherMapCommand()
        data = _sample_weather_data()

        with patch(
            "commands.openweathermapcommand.time_util.resolve_location_timezone",
            return_value=pytz.timezone("Asia/Tokyo"),
        ):
            result = command._get_weather_string(data)

        self.assertIn("15.01.2025 09:00", result)
        self.assertIn("Aurinko nousee 11:00 ja laskee 20:40", result)

    def test_raises_when_location_timezone_cannot_be_resolved(self):
        command = OpenWeatherMapCommand()
        data = _sample_weather_data()

        with patch(
            "commands.openweathermapcommand.time_util.resolve_location_timezone",
            side_effect=ValueError("Timezone lookup failed"),
        ):
            with self.assertRaises(ValueError):
                command._get_weather_string(data)


if __name__ == "__main__":
    unittest.main()

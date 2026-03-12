import datetime
import os
import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pytz

sys.path.insert(0, os.path.abspath("src"))

# Keep tests lightweight by stubbing runtime-only dependencies.
models_module = types.ModuleType("models")
address_cache_module = types.ModuleType("models.address_cache_entry")
user_module = types.ModuleType("models.user")


class _AddressCacheEntry:
    pass


class _User:
    @classmethod
    def get_or_create(cls, _sending_user):
        return None


address_cache_module.AddressCacheEntry = _AddressCacheEntry
user_module.User = _User
sys.modules["models"] = models_module
sys.modules["models.address_cache_entry"] = address_cache_module
sys.modules["models.user"] = user_module

services_module = types.ModuleType("services")
database_module = types.ModuleType("services.database")
accesscontrol_module = types.ModuleType("services.accesscontrol")
accesscontrol_module.has_admin_access = lambda _nickmask: True
services_module.database = database_module
sys.modules["services"] = services_module
sys.modules["services.database"] = database_module
sys.modules["services.accesscontrol"] = accesscontrol_module

from commands.fmiweathercommand import (  # noqa: E402
    FmiWeatherCommand,
    MAX_FORECAST_INTERVAL_HOURS,
    MAX_RANGE_FORECAST_ITEMS,
)
from lib import fmi  # noqa: E402


class _FixedDatetime(datetime.datetime):
    frozen_utcnow = datetime.datetime(2026, 1, 15, 12, 0, 0)

    @classmethod
    def utcnow(cls):
        return cls.frozen_utcnow


class _DummyLocation:
    def __init__(self, latitude, longitude, source="geocode", resolved_name="Testilä"):
        self.latitude = latitude
        self.longitude = longitude
        self.source = source
        self.resolved_name = resolved_name


class _DummyMessage:
    def __init__(self, sender="tester", commandword="sää", params=""):
        self.sender = sender
        self.commandword = commandword
        self.params = params
        self.replies = []

    def reply_to(self, text):
        self.replies.append(text)


def _forecast(model, timestamps, base_temp=0):
    return {
        "location_name": "Testilä",
        "country": "Finland",
        "region": "Testialue",
        "timestamps": timestamps,
        "data": [{"Temperature": base_temp + i} for i, _ in enumerate(timestamps)],
        "model": model,
    }


class FmiWeatherCommandFallbackFillTest(unittest.TestCase):
    def setUp(self):
        self.command = FmiWeatherCommand()
        self.now_utc = datetime.datetime(2026, 1, 15, 12, 0, 0)
        _FixedDatetime.frozen_utcnow = self.now_utc
        self._datetime_patcher = patch(
            "commands.fmiweathercommand.datetime.datetime",
            _FixedDatetime,
        )
        self._datetime_patcher.start()
        self.location = _DummyLocation(60.1699, 24.9384)

    def tearDown(self):
        self._datetime_patcher.stop()

    def test_prefers_primary_model_extension_before_other_model(self):
        primary_timestamps = [
            self.now_utc + datetime.timedelta(hours=i) for i in range(3)
        ]
        extended_primary_timestamps = [
            self.now_utc + datetime.timedelta(hours=i) for i in range(20)
        ]
        primary = _forecast("scandinavia", primary_timestamps, base_temp=1)
        extended_primary = _forecast(
            "scandinavia", extended_primary_timestamps, base_temp=1)
        message = _DummyMessage()

        with patch(
            "commands.fmiweathercommand.geocoding.resolve_location",
            return_value=self.location,
        ), patch(
            "commands.fmiweathercommand.fmi.fetch_forecast",
            return_value=primary,
        ), patch(
            "commands.fmiweathercommand.fmi.fetch_forecast_for_model",
            return_value=extended_primary,
        ) as fetch_other:
            self.command._handle_forecast_range(message, interval_hours=1, location_param="helsinki")

        self.assertEqual(fetch_other.call_count, 1)
        call_args = fetch_other.call_args_list[0].args
        self.assertEqual(call_args[0], (self.location.latitude, self.location.longitude))
        self.assertEqual(call_args[1], "scandinavia")
        self.assertEqual(len(message.replies), 1)
        self.assertIn("Ennuste", message.replies[0])

    def test_uses_other_model_when_primary_extension_is_still_insufficient(self):
        primary_timestamps = [
            self.now_utc + datetime.timedelta(hours=i) for i in range(3)
        ]
        extended_primary_timestamps = [
            self.now_utc + datetime.timedelta(hours=i) for i in range(4)
        ]
        secondary_timestamps = [
            self.now_utc + datetime.timedelta(hours=i) for i in range(4, 24)
        ]
        primary = _forecast("scandinavia", primary_timestamps, base_temp=1)
        extended_primary = _forecast(
            "scandinavia", extended_primary_timestamps, base_temp=1)
        secondary = _forecast("ecmwf", secondary_timestamps, base_temp=10)
        message = _DummyMessage()

        def _fetch_model(_latlon, model, **_kwargs):
            if model == "scandinavia":
                return extended_primary
            if model == "ecmwf":
                return secondary
            return None

        with patch(
            "commands.fmiweathercommand.geocoding.resolve_location",
            return_value=self.location,
        ), patch(
            "commands.fmiweathercommand.fmi.fetch_forecast",
            return_value=primary,
        ), patch(
            "commands.fmiweathercommand.fmi.fetch_forecast_for_model",
            side_effect=_fetch_model,
        ) as fetch_other:
            self.command._handle_forecast_range(message, interval_hours=1, location_param="helsinki")

        self.assertEqual(fetch_other.call_count, 2)
        first_model = fetch_other.call_args_list[0].args[1]
        second_model = fetch_other.call_args_list[1].args[1]
        self.assertEqual((first_model, second_model), ("scandinavia", "ecmwf"))
        self.assertEqual(len(message.replies), 1)
        self.assertIn("Ennuste", message.replies[0])

    def test_does_not_use_other_model_when_primary_points_are_enough(self):
        primary_timestamps = [
            self.now_utc + datetime.timedelta(hours=i) for i in range(20)
        ]
        primary = _forecast("scandinavia", primary_timestamps, base_temp=1)
        message = _DummyMessage()

        with patch(
            "commands.fmiweathercommand.geocoding.resolve_location",
            return_value=self.location,
        ), patch(
            "commands.fmiweathercommand.fmi.fetch_forecast",
            return_value=primary,
        ), patch(
            "commands.fmiweathercommand.fmi.fetch_forecast_for_model",
        ) as fetch_other:
            self.command._handle_forecast_range(message, interval_hours=1, location_param="helsinki")

        fetch_other.assert_not_called()
        self.assertEqual(len(message.replies), 1)
        self.assertIn("Ennuste", message.replies[0])

    def test_merge_keeps_primary_on_overlap_and_sorts(self):
        t0 = self.now_utc
        t1 = self.now_utc + datetime.timedelta(hours=1)
        t2 = self.now_utc + datetime.timedelta(hours=2)
        primary = _forecast("scandinavia", [t0, t2], base_temp=1)
        secondary = _forecast("ecmwf", [t1, t2], base_temp=10)

        merged = self.command._merge_forecast_data(primary, secondary)

        self.assertEqual(merged["timestamps"], [t0, t1, t2])
        overlap_index = merged["timestamps"].index(t2)
        self.assertEqual(merged["data"][overlap_index]["Temperature"], 2)
        selected = self.command._select_range_points(merged, interval_hours=1, now_utc=t0)
        self.assertLessEqual(len(selected), MAX_RANGE_FORECAST_ITEMS)

    def test_date_marker_is_only_once_per_day(self):
        now_utc = self.now_utc
        parsed = _forecast(
            "scandinavia",
            [
                now_utc,
                now_utc + datetime.timedelta(hours=12),
                now_utc + datetime.timedelta(hours=24),
                now_utc + datetime.timedelta(hours=36),
            ],
            base_temp=1,
        )

        with patch(
            "commands.fmiweathercommand.time_util.utc_to_local",
            side_effect=lambda dt, *_args: dt.replace(tzinfo=datetime.timezone.utc),
        ):
            result = self.command._format_forecast_range(
                parsed,
                interval_hours=12,
                timezone=datetime.timezone.utc,
                resolved_name="Testilä",
                now_utc=now_utc,
            )

        self.assertIsNotNone(result)
        self.assertIn("Ennuste", result)
        today = now_utc
        tomorrow = now_utc + datetime.timedelta(hours=24)
        day_after = now_utc + datetime.timedelta(hours=48)
        self.assertIn("[", result)
        self.assertEqual(result.count(f"{today.day}.{today.month}."), 1)
        self.assertEqual(result.count(f"{tomorrow.day}.{tomorrow.month}."), 1)
        self.assertEqual(result.count(f"{day_after.day}.{day_after.month}."), 1)

    def test_interval_over_max_returns_user_error(self):
        message = _DummyMessage()
        with patch("commands.fmiweathercommand.geocoding.resolve_location") as resolve_location:
            self.command._handle_forecast_range(
                message,
                interval_hours=MAX_FORECAST_INTERVAL_HOURS + 1,
                location_param="helsinki",
            )
        resolve_location.assert_not_called()
        self.assertEqual(len(message.replies), 1)
        self.assertIn("enintään", message.replies[0])

    def test_days_interval_over_max_returns_user_error(self):
        message = _DummyMessage(commandword="sää", params="4d helsinki")
        with patch("commands.fmiweathercommand.geocoding.resolve_location") as resolve_location:
            self.command.handle(message)
        resolve_location.assert_not_called()
        self.assertEqual(len(message.replies), 1)
        self.assertIn(f"{MAX_FORECAST_INTERVAL_HOURS}h", message.replies[0])

    def test_empty_rows_are_skipped_in_range_output(self):
        t0 = self.now_utc
        parsed = {
            "location_name": "Testilä",
            "country": "Finland",
            "region": "Testialue",
            "timestamps": [
                t0,
                t0 + datetime.timedelta(hours=72),
                t0 + datetime.timedelta(hours=144),
            ],
            "data": [
                {"Temperature": 5},
                {},
                {"Temperature": 3},
            ],
            "model": "scandinavia",
        }
        with patch(
            "commands.fmiweathercommand.time_util.utc_to_local",
            side_effect=lambda dt, *_args: dt.replace(tzinfo=datetime.timezone.utc),
        ):
            result = self.command._format_forecast_range(
                parsed,
                interval_hours=72,
                timezone=datetime.timezone.utc,
                resolved_name="Testilä",
                now_utc=t0,
            )
        self.assertIsNotNone(result)
        self.assertNotIn("14:   ", result)
        self.assertEqual(result.count("°C"), 2)


class FmiLibraryForecastFallbackTest(unittest.TestCase):
    def test_fallback_to_ecmwf_keeps_time_range(self):
        latlon = (60.1699, 24.9384)
        starttime = datetime.datetime(2026, 1, 1, 12, 0, 0)
        endtime = datetime.datetime(2026, 1, 2, 12, 0, 0)
        ecmwf_result = {"model": "ecmwf", "timestamps": [], "data": []}

        with patch(
            "lib.fmi._fetch_scandinavia_forecast",
            return_value=None,
        ), patch(
            "lib.fmi._fetch_ecmwf_forecast",
            return_value=ecmwf_result,
        ) as fetch_ecmwf:
            result = fmi.fetch_forecast(latlon, starttime=starttime, endtime=endtime)

        self.assertEqual(result, ecmwf_result)
        fetch_ecmwf.assert_called_once_with(
            latlon,
            starttime=starttime,
            endtime=endtime,
        )


class FmiWeatherEmojiPreferenceTest(unittest.TestCase):
    def test_format_forecast_hour_uses_emojis_when_enabled(self):
        command = FmiWeatherCommand()
        ts = datetime.datetime(2026, 1, 15, 12, 0, 0)
        row = {"WeatherSymbol3": 21, "Temperature": 2}

        with patch(
            "commands.fmiweathercommand.time_util.utc_to_local",
            side_effect=lambda dt, *_args: dt.replace(tzinfo=datetime.timezone.utc),
        ):
            output = command._format_forecast_hour(
                row, ts, timezone=datetime.timezone.utc, emoji_enabled=True)

        self.assertIsNotNone(output)
        self.assertIn("🌦️", output)

    def test_format_forecast_hour_uses_text_when_emojis_disabled(self):
        command = FmiWeatherCommand()
        ts = datetime.datetime(2026, 1, 15, 12, 0, 0)
        row = {"WeatherSymbol3": 21, "Temperature": 2}

        with patch(
            "commands.fmiweathercommand.time_util.utc_to_local",
            side_effect=lambda dt, *_args: dt.replace(tzinfo=datetime.timezone.utc),
        ):
            output = command._format_forecast_hour(
                row, ts, timezone=datetime.timezone.utc, emoji_enabled=False)

        self.assertIsNotNone(output)
        self.assertIn("sadekuuroja", output)
        self.assertNotIn("🌦️", output)

    def test_emoji_preference_reads_message_user_first(self):
        message = SimpleNamespace(
            user=SimpleNamespace(emoji_enabled=False),
            sender="tester",
        )
        self.assertFalse(FmiWeatherCommand._is_emoji_enabled(message))


class FmiWeatherTimezoneBehaviorTest(unittest.TestCase):
    def setUp(self):
        self.command = FmiWeatherCommand()

    def test_forecast_uses_location_timezone_for_timestamp(self):
        parsed = _forecast("scandinavia", [datetime.datetime(2026, 1, 15, 0, 0, 0)], base_temp=2)
        parsed.update(
            {
                "country": "Japan",
                "region": "Tokyo",
                "location_name": "Tokyo",
                "data": [{"Temperature": 2, "WeatherSymbol3": 1}],
            }
        )
        tokyo_tz = pytz.timezone("Asia/Tokyo")

        result = self.command._format_forecast(
            parsed, 0, timezone=tokyo_tz, resolved_name="Tokyo, Japan")

        self.assertIn("15.01.2026 09:00", result)

    def test_sun_times_use_forecast_location_local_date(self):
        parsed = {"lat": 60.1699, "lon": 24.9384}
        forecast_ts = datetime.datetime(2026, 1, 15, 0, 30, 0)
        timezone = pytz.timezone("America/New_York")
        expected_local_date = datetime.date(2026, 1, 14)
        sunrise_utc = datetime.datetime(2026, 1, 14, 12, 0, 0)
        sunset_utc = datetime.datetime(2026, 1, 14, 20, 0, 0)

        with patch(
            "commands.fmiweathercommand.sun_times",
            return_value={"sunrise": sunrise_utc, "sunset": sunset_utc},
        ) as mock_sun_times:
            result = self.command._format_sun_times(parsed, forecast_ts, timezone)

        self.assertIn("Aurinko nousee 07:00 ja laskee 15:00", result)
        self.assertEqual(mock_sun_times.call_args[0][0], expected_local_date)


if __name__ == "__main__":
    unittest.main()

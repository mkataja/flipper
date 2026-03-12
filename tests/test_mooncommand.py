import os
import sys
import types
import unittest
from datetime import datetime
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
services_module.database = database_module
sys.modules["services"] = services_module
sys.modules["services.database"] = database_module

from commands.mooncommand import MoonCommand


class _DummyLocation:
    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude


class _DummyMessage:
    def __init__(self, sender="tester", params=""):
        self.sender = sender
        self.params = params
        self.replies = []

    def reply_to(self, text):
        self.replies.append(text)


class MoonCommandTimezoneTest(unittest.TestCase):
    def test_moonrise_moonset_use_location_timezone(self):
        command = MoonCommand()
        message = _DummyMessage(params="2026-01-15 tokyo")
        moonrise_utc = datetime(2026, 1, 15, 0, 0, 0)
        moonset_utc = datetime(2026, 1, 15, 10, 0, 0)

        with patch(
            "commands.mooncommand.geocoding.resolve_location",
            return_value=_DummyLocation(35.6762, 139.6503),
        ), patch(
            "commands.mooncommand.moon.phase",
            return_value={"phase": 0.25, "illuminated": 0.5},
        ), patch(
            "commands.mooncommand.moon.moon_times",
            return_value={"moonrise": moonrise_utc, "moonset": moonset_utc},
        ), patch(
            "commands.mooncommand.time_util.resolve_location_timezone",
            return_value=pytz.timezone("Asia/Tokyo"),
        ):
            command.handle(message)

        self.assertEqual(len(message.replies), 1)
        self.assertIn("nousee 09:00", message.replies[0])
        self.assertIn("laskee 19:00", message.replies[0])


if __name__ == "__main__":
    unittest.main()

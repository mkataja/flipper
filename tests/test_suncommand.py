import os
import sys
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath("src"))

timezonefinder_module = types.ModuleType("timezonefinder")


class _TimezoneFinder:
    def timezone_at(self, lat=None, lng=None):
        _ = (lat, lng)
        return "UTC"


timezonefinder_module.TimezoneFinder = _TimezoneFinder
sys.modules["timezonefinder"] = timezonefinder_module

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

from commands.suncommand import SunCommand  # noqa: E402


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


class SunCommandTimezoneTest(unittest.TestCase):
    def test_formats_reply_via_sun_library(self):
        command = SunCommand()
        message = _DummyMessage(params="2026-01-15 tokyo")
        with patch(
            "commands.suncommand.geocoding.resolve_location",
            return_value=_DummyLocation(35.6762, 139.6503),
        ), patch(
            "commands.suncommand.time_util.resolve_location_timezone",
            return_value=object(),
        ), patch(
            "commands.suncommand.sun.format_sun_times_sentence",
            return_value="Aurinko nousee joskus.",
        ):
            command.handle(message)

        self.assertEqual(len(message.replies), 1)
        self.assertEqual(message.replies[0], "Aurinko nousee joskus.")

    def test_replies_when_location_is_not_found(self):
        command = SunCommand()
        message = _DummyMessage(params="EiOlePaikkaa")

        with patch(
            "commands.suncommand.geocoding.resolve_location",
            return_value=None,
        ):
            command.handle(message)

        self.assertEqual(len(message.replies), 1)
        self.assertIn("Sijaintia EiOlePaikkaa ei löydy", message.replies[0])

if __name__ == "__main__":
    unittest.main()

import datetime
import os
import sys
import types
import unittest
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

from commands.timecommand import TimeCommand


class _FixedDatetime(datetime.datetime):
    @classmethod
    def now(cls, tz=None):
        fixed = datetime.datetime(2026, 1, 15, 12, 34, 0, tzinfo=pytz.utc)
        if tz is None:
            return fixed.replace(tzinfo=None)
        return fixed.astimezone(tz)


class _DummyLocation:
    def __init__(self, latitude, longitude, resolved_name="Tokyo", source="geocode"):
        self.latitude = latitude
        self.longitude = longitude
        self.resolved_name = resolved_name
        self.source = source


class _DummyMessage:
    def __init__(self, sender="tester", params=""):
        self.sender = sender
        self.params = params
        self.replies = []

    def reply_to(self, text):
        self.replies.append(text)


class TimeCommandTest(unittest.TestCase):
    def test_aika_uses_geocoded_location_timezone(self):
        command = TimeCommand()
        message = _DummyMessage(params="tokyo")
        location = _DummyLocation(35.6762, 139.6503, resolved_name="Tokyo")

        with patch(
            "commands.timecommand.geocoding.resolve_location",
            return_value=location,
        ), patch(
            "commands.timecommand.time_util.resolve_location_timezone",
            return_value=pytz.timezone("Asia/Tokyo"),
        ), patch(
            "commands.timecommand.datetime.datetime",
            _FixedDatetime,
        ):
            command.handle(message)

        self.assertEqual(len(message.replies), 1)
        self.assertIn("Aika paikassa Tokyo", message.replies[0])
        self.assertIn("15.01.2026 21:34", message.replies[0])
        self.assertIn("(JST)", message.replies[0])

    def test_aika_replies_when_location_is_not_found(self):
        command = TimeCommand()
        message = _DummyMessage(params="EiOlePaikkaa")

        with patch(
            "commands.timecommand.geocoding.resolve_location",
            return_value=None,
        ):
            command.handle(message)

        self.assertEqual(len(message.replies), 1)
        self.assertIn("Sijaintia EiOlePaikkaa ei löydy", message.replies[0])


if __name__ == "__main__":
    unittest.main()

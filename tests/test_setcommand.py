import os
import sys
import types
import unittest
from unittest.mock import patch

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

from commands.setcommand import SetCommand, parse_bool


class _DummyUser:
    def __init__(self):
        self.location = None
        self.emoji_enabled = None

    def set_location(self, lat, lon):
        self.location = (lat, lon)

    def set_emoji_enabled(self, enabled):
        self.emoji_enabled = enabled


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


class SetCommandTest(unittest.TestCase):
    def setUp(self):
        self.command = SetCommand()

    def test_set_koti_updates_location(self):
        message = _DummyMessage(params="koti Tampere")
        dummy_user = _DummyUser()
        with patch("commands.setcommand.geocoding.geocode", return_value=_DummyLocation(61.5, 23.7)), patch(
            "commands.setcommand.User.get_or_create", return_value=dummy_user
        ):
            self.command.handle(message)

        self.assertEqual(dummy_user.location, (61.5, 23.7))
        self.assertIn("Ok, uusi kotisijainti asetettu", message.replies[0])

    def test_set_koti_returns_error_when_location_not_found(self):
        message = _DummyMessage(params="koti EiOlePaikkaa")
        with patch("commands.setcommand.geocoding.geocode", return_value=None):
            self.command.handle(message)

        self.assertEqual(len(message.replies), 1)
        self.assertIn("ei ole olemassa", message.replies[0])

    def test_set_emoji_true_updates_user_preference(self):
        message = _DummyMessage(params="emoji true")
        dummy_user = _DummyUser()
        with patch("commands.setcommand.User.get_or_create", return_value=dummy_user):
            self.command.handle(message)

        self.assertTrue(dummy_user.emoji_enabled)
        self.assertIn("käytössä", message.replies[0])

    def test_set_emoji_false_updates_user_preference(self):
        message = _DummyMessage(params="emoji false")
        dummy_user = _DummyUser()
        with patch("commands.setcommand.User.get_or_create", return_value=dummy_user):
            self.command.handle(message)

        self.assertFalse(dummy_user.emoji_enabled)
        self.assertIn("pois käytöstä", message.replies[0])

    def test_set_emoji_on_alias_updates_user_preference(self):
        message = _DummyMessage(params="emoji on")
        dummy_user = _DummyUser()
        with patch("commands.setcommand.User.get_or_create", return_value=dummy_user):
            self.command.handle(message)

        self.assertTrue(dummy_user.emoji_enabled)
        self.assertIn("käytössä", message.replies[0])

    def test_set_emoji_pois_alias_updates_user_preference(self):
        message = _DummyMessage(params="emoji pois")
        dummy_user = _DummyUser()
        with patch("commands.setcommand.User.get_or_create", return_value=dummy_user):
            self.command.handle(message)

        self.assertFalse(dummy_user.emoji_enabled)
        self.assertIn("pois käytöstä", message.replies[0])

    def test_set_emoji_requires_known_alias(self):
        message = _DummyMessage(params="emoji maybe")
        self.command.handle(message)

        self.assertEqual(len(message.replies), 1)
        self.assertIn("true/false", message.replies[0])


class ParseBoolTest(unittest.TestCase):
    def test_parse_bool_true_values(self):
        self.assertTrue(parse_bool("true"))
        self.assertTrue(parse_bool("on"))
        self.assertTrue(parse_bool("päälle"))

    def test_parse_bool_false_values(self):
        self.assertFalse(parse_bool("false"))
        self.assertFalse(parse_bool("off"))
        self.assertFalse(parse_bool("pois"))

    def test_parse_bool_unknown_value(self):
        with self.assertRaises(ValueError):
            parse_bool("maybe")


if __name__ == "__main__":
    unittest.main()

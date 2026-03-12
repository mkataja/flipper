import os
import sys
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath("src"))

# Keep tests lightweight by stubbing runtime-only dependencies.
config_module = types.ModuleType("config")
config_module.GOOGLE_API_KEY = "test-key"
config_module.LOCATION = "60.1699,24.9384"
sys.modules["config"] = config_module

lib_http_module = types.ModuleType("lib.http")
lib_http_module.try_json_request = lambda _url: None
sys.modules["lib.http"] = lib_http_module

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

from commands.geocodecommand import GeocodeCommand
from lib.geocoding import LocationResolution


class _DummyMessage:
    def __init__(self, params):
        self.params = params
        self.replies = []

    def reply_to(self, text):
        self.replies.append(text)


class GeocodeCommandTest(unittest.TestCase):
    def setUp(self):
        self.command = GeocodeCommand()

    def test_formats_decimal_coordinates_without_float_artifacts(self):
        message = _DummyMessage("Moi, Norja")
        with patch(
            "commands.geocodecommand.geocoding.geocode",
            return_value=LocationResolution(
                latitude=58.46091560000001,
                longitude=6.544376199999999,
                resolved_name="Moi, Norja",
                source="geocode",
            ),
        ):
            self.command.handle(message)

        self.assertEqual(len(message.replies), 1)
        self.assertIn("(58.460915,6.544376)", message.replies[0])
        self.assertNotIn("0000001", message.replies[0])


if __name__ == "__main__":
    unittest.main()

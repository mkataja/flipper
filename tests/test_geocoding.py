import os
import sys
import types
import unittest


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
services_module.database = database_module
sys.modules["services"] = services_module
sys.modules["services.database"] = database_module

from lib import geocoding, number_format


class GeocodingNameCleanupTest(unittest.TestCase):
    def test_format_decimal_degrees_truncates_float_artifacts(self):
        formatted = number_format.format_decimal_degrees(58.46091560000001)
        self.assertEqual(formatted, "58.460915")

    def test_format_coordinate_pair_truncates_to_six_decimals(self):
        formatted = number_format.format_coordinate_pair(
            58.46091560000001, 6.544376199999999
        )
        self.assertEqual(formatted, "58.460915,6.544376")

    def test_geocode_url_uses_finnish_by_default(self):
        url = geocoding._build_geocode_url("helsinki")
        self.assertIn("language=fi", url)

    def test_geocode_url_uses_configured_language(self):
        geocoding.config.GEOCODING_LANGUAGE = "sv"
        try:
            url = geocoding._build_geocode_url("helsinki")
            self.assertIn("language=sv", url)
        finally:
            delattr(geocoding.config, "GEOCODING_LANGUAGE")

    def test_removes_postal_code_from_structured_components(self):
        first_result = {
            "formatted_address": "111 64 Stockholm, Sweden",
            "address_components": [
                {"long_name": "111 64", "types": ["postal_code"]},
            ],
        }

        resolved = geocoding._resolve_display_name(first_result, "stockholm")

        self.assertEqual(resolved, "Stockholm, Sweden")

    def test_keeps_postal_code_when_query_contains_it(self):
        first_result = {
            "formatted_address": "111 64 Stockholm, Sweden",
            "address_components": [
                {"long_name": "111 64", "types": ["postal_code"]},
            ],
        }

        resolved = geocoding._resolve_display_name(first_result, "111 64 stockholm")

        self.assertEqual(resolved, "111 64 Stockholm, Sweden")

    def test_fallback_removes_leading_zip_like_prefix(self):
        resolved = geocoding._strip_fallback_leading_zip("28900 Pori", "pori")
        self.assertEqual(resolved, "Pori")

    def test_never_removes_trailing_street_number(self):
        resolved = geocoding._strip_fallback_leading_zip(
            "Mannerheimintie 4", "mannerheimintie")
        self.assertEqual(resolved, "Mannerheimintie 4")

    def test_fallback_display_name_capitalizes_words(self):
        resolved = geocoding._fallback_display_name("espoo keskus")
        self.assertEqual(resolved, "Espoo Keskus")

    def test_fallback_display_name_preserves_zip_only_queries(self):
        resolved = geocoding._fallback_display_name("00100")
        self.assertEqual(resolved, "00100")

    def test_strip_trailing_finland_from_resolved_name(self):
        first_result = {
            "formatted_address": "Helsinki, Finland",
            "address_components": [],
        }
        resolved = geocoding._resolve_display_name(first_result, "helsinki")
        normalized = geocoding._normalize_resolved_name(resolved, "helsinki")
        self.assertEqual(normalized, "Helsinki")

    def test_strip_trailing_finland_case_insensitive(self):
        normalized = geocoding._normalize_resolved_name(
            "Espoo, FINLAND", "espoo")
        self.assertEqual(normalized, "Espoo")


if __name__ == "__main__":
    unittest.main()

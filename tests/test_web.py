import os
import sys
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath("src"))

# Keep tests lightweight by stubbing runtime-only dependencies.
config_module = types.ModuleType("config")
config_module.USER_AGENT = "test-agent"
sys.modules["config"] = config_module

lib_http_module = types.ModuleType("lib.http")
lib_http_module.try_get_response = lambda *_args, **_kwargs: None
sys.modules["lib.http"] = lib_http_module

sys.modules.pop("lib.web", None)
from lib import web


class _DummyResponse:
    def __init__(self, status, title):
        self.status = status
        self.data = f"<html><head><title>{title}</title></head></html>".encode()


def _get_title(status, title):
    with patch("lib.web.try_get_response", return_value=_DummyResponse(status, title)):
        return web.get_title_text("https://example.com/")


class GetTitleTextTest(unittest.TestCase):
    def test_returns_title_for_successful_response(self):
        self.assertEqual(_get_title(200, "Example  Domain"), "Example Domain")

    def test_returns_none_for_error_status(self):
        for status in (404, 403, 500, 503):
            with self.subTest(status=status):
                self.assertIsNone(_get_title(status, "Example Domain"))

    def test_returns_none_when_request_fails(self):
        with patch("lib.web.try_get_response", return_value=None):
            self.assertIsNone(web.get_title_text("https://example.com/"))

    def test_returns_none_for_404_title_with_successful_status(self):
        for title in ("404 Not Found", "Error 404 (Not Found)!!1", "Page not found - 404"):
            with self.subTest(title=title):
                self.assertIsNone(_get_title(200, title))

    def test_keeps_titles_without_404_not_found(self):
        for title in ("Not Found", "404 Club", "Lost and Not Found"):
            with self.subTest(title=title):
                self.assertEqual(_get_title(200, title), title)


if __name__ == "__main__":
    unittest.main()

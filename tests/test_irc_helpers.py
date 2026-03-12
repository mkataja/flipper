import os
import sys
import unittest

sys.path.insert(0, os.path.abspath("src"))

from lib import irc_helpers


class _DummyConnection:
    def __init__(self, features=None):
        self.features = features


class IrcHelpersMessageLengthTest(unittest.TestCase):
    def test_get_server_line_limit_uses_default_when_missing(self):
        self.assertEqual(
            irc_helpers.get_server_line_limit_bytes(_DummyConnection()),
            irc_helpers.DEFAULT_IRC_LINE_LENGTH_BYTES,
        )

    def test_get_server_line_limit_reads_isupport_value(self):
        connection = _DummyConnection(features={"LINELEN": "2048"})
        self.assertEqual(irc_helpers.get_server_line_limit_bytes(connection), 2048)

    def test_get_server_line_limit_parses_embedded_numeric(self):
        connection = _DummyConnection(features={"MAXLINE": "len=1024"})
        self.assertEqual(irc_helpers.get_server_line_limit_bytes(connection), 1024)

    def test_get_max_privmsg_text_bytes_respects_target_overhead(self):
        max_text = irc_helpers.get_max_privmsg_text_bytes(
            target="#pitkakanava",
            line_limit_bytes=512,
        )
        self.assertLess(max_text, 512)
        self.assertGreater(max_text, 0)

    def test_split_privmsg_text_splits_long_text(self):
        text = "word " * 200
        chunks = irc_helpers.split_privmsg_text(text.strip(), max_bytes=120)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk.encode("utf-8")) <= 120 for chunk in chunks))
        self.assertEqual(" ".join(chunks), text.strip())

    def test_split_privmsg_text_handles_multibyte_characters(self):
        text = "äää äää äää äää äää äää äää äää äää äää"
        chunks = irc_helpers.split_privmsg_text(text, max_bytes=20)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk.encode("utf-8")) <= 20 for chunk in chunks))
        self.assertEqual(" ".join(chunks), text)

    def test_split_privmsg_text_hard_splits_single_long_token(self):
        text = "x" * 40
        chunks = irc_helpers.split_privmsg_text(text, max_bytes=15)
        self.assertEqual("".join(chunks), text)
        self.assertTrue(all(len(chunk.encode("utf-8")) <= 15 for chunk in chunks))

    def test_split_privmsg_text_limited_without_truncation(self):
        text = "word " * 20
        chunks, was_truncated = irc_helpers.split_privmsg_text_limited(
            text.strip(),
            max_bytes=120,
            max_chunks=2,
        )
        self.assertFalse(was_truncated)
        self.assertEqual(" ".join(chunks), text.strip())

    def test_split_privmsg_text_limited_truncates_overflow(self):
        text = "word " * 200
        chunks, was_truncated = irc_helpers.split_privmsg_text_limited(
            text.strip(),
            max_bytes=120,
            max_chunks=2,
        )
        self.assertTrue(was_truncated)
        self.assertEqual(len(chunks), 2)
        self.assertTrue(all(len(chunk.encode("utf-8")) <= 120 for chunk in chunks))
        self.assertLess(len(" ".join(chunks)), len(text.strip()))


if __name__ == "__main__":
    unittest.main()

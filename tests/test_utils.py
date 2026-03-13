import unittest

from utils import is_command_triggered, normalize_tts_text


class NormalizeTTSTextTests(unittest.TestCase):
    def test_strips_iso_utc_timestamp_lines(self):
        text = "你好呀～\n2026-03-12T12:17:28.248373923Z\n我是助手"
        self.assertEqual(normalize_tts_text(text), "你好呀～ 我是助手")

    def test_keeps_timestamp_when_disabled(self):
        text = "hi\n2026-03-12T12:17:28.248Z\nthere"
        self.assertEqual(
            normalize_tts_text(text, strip_timestamps=False),
            "hi 2026-03-12T12:17:28.248Z there",
        )

    def test_collapses_empty_lines_and_whitespace(self):
        text = "  a  \n\n  b\t\n"
        self.assertEqual(normalize_tts_text(text), "a b")

    def test_empty_input(self):
        self.assertEqual(normalize_tts_text(""), "")
        self.assertEqual(normalize_tts_text(None), "")  # type: ignore[arg-type]


class IsCommandTriggeredTests(unittest.TestCase):
    def test_returns_false_when_extras_is_not_dict(self):
        self.assertFalse(is_command_triggered(None))

    def test_returns_false_when_handlers_parsed_params_missing(self):
        self.assertFalse(is_command_triggered({}))

    def test_returns_false_when_handlers_parsed_params_is_not_dict(self):
        self.assertFalse(is_command_triggered({"handlers_parsed_params": []}))

    def test_returns_false_when_handlers_parsed_params_empty(self):
        self.assertFalse(is_command_triggered({"handlers_parsed_params": {}}))

    def test_returns_true_when_handlers_parsed_params_non_empty(self):
        self.assertTrue(
            is_command_triggered({"handlers_parsed_params": {"some.cmd": {}}}),
        )


if __name__ == "__main__":
    unittest.main()

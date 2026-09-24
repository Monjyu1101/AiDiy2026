from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock


BACKEND_TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_TOOLS_DIR))

from tools_proc.text_to_speech import TextToSpeech  # noqa: E402


class TextToSpeechEmptyStringTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tts = TextToSpeech.__new__(TextToSpeech)
        self.tts._generate_silence_mp3 = Mock(return_value=b"ID3-silence")
        self.tts._synthesize_provider = Mock(return_value=b"ID3-voice")
        self.tts._load_pronunciation_dictionary = Mock(return_value=[])

    def test_empty_string_generates_one_second_silence(self) -> None:
        audio, info = self.tts.synthesize("", provider="edge")

        self.assertEqual(audio, b"ID3-silence")
        self.tts._generate_silence_mp3.assert_called_once_with(1.0)
        self.tts._synthesize_provider.assert_not_called()
        self.assertTrue(info["is_silence"])
        self.assertEqual(info["used_provider"], "silence")
        self.assertEqual(info["silence_duration_sec"], 1.0)
        self.assertEqual(info["pause_count"], 1)

    def test_double_quotes_inside_text_are_not_a_pause_marker(self) -> None:
        text = '前半。""後半。'

        audio, info = self.tts.synthesize(text, provider="edge")

        self.assertEqual(audio, b"ID3-voice")
        self.tts._generate_silence_mp3.assert_not_called()
        self.tts._synthesize_provider.assert_called_once()
        self.assertEqual(self.tts._synthesize_provider.call_args.args[1], text)
        self.assertFalse(info["is_silence"])
        self.assertEqual(info["pause_count"], 0)


if __name__ == "__main__":
    unittest.main()

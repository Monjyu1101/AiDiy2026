# -*- coding: utf-8 -*-

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_proc.text_to_speech import TextToSpeech, TextToSpeechError


class StubTextToSpeech(TextToSpeech):
    def __init__(self, available_keys=None, failures=None):
        self.available_keys = set(available_keys or [])
        self.failures = set(failures or [])
        self.calls: list[str] = []

    def _get_api_key(self, provider: str):
        if provider in ("edge",):
            return None
        return "dummy-key" if provider in self.available_keys else None

    def normalize_for_speech(self, text: str):
        return text, []

    def _resolve_voice(self, voice: str, provider: str, language: str = "ja") -> str:
        return f"{provider}-voice"

    def _run_provider(self, provider: str) -> bytes:
        self.calls.append(provider)
        if provider in self.failures:
            raise TextToSpeechError(f"{provider} failed")
        return f"{provider}-audio".encode("ascii")

    def _synthesize_edge(self, text: str, voice: str, ratio: float = 1.0) -> bytes:
        return self._run_provider("edge")

    def _synthesize_openai(self, text: str, voice: str, model: str, ratio: float = 1.0) -> bytes:
        return self._run_provider("openai")

    def _synthesize_gemini(self, text: str, voice: str, model: str, provider: str, ratio: float = 1.0) -> bytes:
        return self._run_provider(provider)


class TextToSpeechFallbackTests(unittest.TestCase):
    def test_fallback_chain_matches_expected_rules(self):
        self.assertEqual(
            TextToSpeech.FALLBACK_CHAIN,
            {
                "auto": ["edge", "freeai"],
                "edge": ["edge", "freeai"],
                "openai": ["openai", "edge"],
                "gemini": ["gemini", "freeai", "edge"],
                "freeai": ["freeai", "gemini", "edge"],
            },
        )

    def test_auto_uses_edge_first(self):
        tts = StubTextToSpeech(available_keys={"freeai"})
        _, info = tts.synthesize("こんにちは", provider="auto")
        self.assertEqual(tts.calls, ["edge"])
        self.assertEqual(info["used_provider"], "edge")

    def test_auto_falls_back_to_freeai_after_edge_failure(self):
        tts = StubTextToSpeech(available_keys={"freeai"}, failures={"edge"})
        _, info = tts.synthesize("こんにちは", provider="auto")
        self.assertEqual(tts.calls, ["edge", "freeai"])
        self.assertEqual(info["used_provider"], "freeai")

    def test_edge_falls_back_to_freeai_after_edge_failure(self):
        tts = StubTextToSpeech(available_keys={"freeai"}, failures={"edge"})
        _, info = tts.synthesize("こんにちは", provider="edge")
        self.assertEqual(tts.calls, ["edge", "freeai"])
        self.assertEqual(info["used_provider"], "freeai")

    def test_freeai_falls_back_to_gemini_then_edge(self):
        tts = StubTextToSpeech(available_keys={"freeai", "gemini"}, failures={"freeai", "gemini"})
        _, info = tts.synthesize("こんにちは", provider="freeai")
        self.assertEqual(tts.calls, ["freeai", "gemini", "edge"])
        self.assertEqual(info["used_provider"], "edge")

    def test_gemini_falls_back_to_freeai_before_edge(self):
        tts = StubTextToSpeech(available_keys={"gemini", "freeai"}, failures={"gemini"})
        _, info = tts.synthesize("こんにちは", provider="gemini")
        self.assertEqual(tts.calls, ["gemini", "freeai"])
        self.assertEqual(info["used_provider"], "freeai")

    def test_openai_falls_back_to_edge(self):
        tts = StubTextToSpeech(available_keys={"openai"}, failures={"openai"})
        _, info = tts.synthesize("こんにちは", provider="openai")
        self.assertEqual(tts.calls, ["openai", "edge"])
        self.assertEqual(info["used_provider"], "edge")


if __name__ == "__main__":
    unittest.main()

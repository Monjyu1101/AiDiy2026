# -*- coding: utf-8 -*-

import asyncio
import importlib.util
import json
import logging
from pathlib import Path
import sys
import tempfile
import types as stdlib_types
import unittest
from unittest.mock import AsyncMock, Mock, patch

from google.genai import types


BACKEND_DIR = Path(__file__).resolve().parents[1]


def load_module(filename):
    logger_stub = stdlib_types.ModuleType("log_config")
    logger_stub.get_logger = logging.getLogger
    tools_stub = stdlib_types.ModuleType("AIコア.AI内部ツール")
    tools_stub.Tools = None
    spec = importlib.util.spec_from_file_location(
        f"live_test_{filename}", BACKEND_DIR / "AIコア" / filename,
    )
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {
        "log_config": logger_stub, "AIコア.AI内部ツール": tools_stub,
    }):
        spec.loader.exec_module(module)
    return module


class LiveTextResponseTest(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        # patch.dict の復元で NumPy の C 拡張を再インポートしないよう、先に読み込む。
        importlib.import_module("numpy")
        cls.gemini_module = load_module("AIライブ_gemini.py")
        cls.openai_module = load_module("AIライブ_openai.py")
        cls.live_module = load_module("AIライブ.py")
        cls.audio_module = load_module("AI音声処理.py")

    def gemini(self):
        ai = self.gemini_module.LiveAI.__new__(self.gemini_module.LiveAI)
        ai.parent_manager = None
        ai.SYSTEM_INSTRUCTION = "日本語で回答してください。"
        ai.LIVE_VOICE = "Kore"
        ai.tool_instance = None
        ai.音声受信Ｑ = asyncio.Queue()
        ai.テキスト受信Ｑ = asyncio.Queue()
        ai._出力字幕 = ""
        return ai

    async def test_audio_config_requests_transcription_including_fallback(self):
        ai = self.gemini()
        config = await ai._設定構成作成()
        self.assertEqual([types.Modality.AUDIO], config.response_modalities)
        self.assertIsNotNone(config.output_audio_transcription)
        original = types.LiveConnectConfig
        with patch.object(types, "LiveConnectConfig", side_effect=[
            ValueError("config failure"), original(response_modalities=["AUDIO"],
                output_audio_transcription=types.AudioTranscriptionConfig()),
        ]) as create, self.assertLogs(level="ERROR"):
            await ai._設定構成作成()
        self.assertIn("output_audio_transcription", create.call_args.kwargs)

    async def test_text_request_native_audio_transcript_reaches_channel_zero(self):
        ai = self.gemini()
        ai.live_session = stdlib_types.SimpleNamespace(send_client_content=AsyncMock())
        request = "このプロジェクトの内容を説明してほしい。\nコードエージェントに確認してもらってもよい。"
        self.assertTrue(await ai.テキスト送信(request))
        sent = ai.live_session.send_client_content.call_args.kwargs
        self.assertTrue(sent["turn_complete"])
        self.assertEqual(request, sent["turns"].parts[0].text)

        for fragment in ("AiDiy は、", "日本語で業務システムを開発するプロジェクトです。"):
            await ai._サーバーコンテンツ処理(types.LiveServerContent(
                model_turn=types.Content(parts=[types.Part.from_bytes(
                    data=b"\x00\x00", mime_type="audio/pcm;rate=24000",
                )]),
                output_transcription=types.Transcription(text=fragment),
            ))
        self.assertEqual(2, ai.音声受信Ｑ.qsize())
        self.assertTrue(ai.テキスト受信Ｑ.empty())
        await ai._サーバーコンテンツ処理(types.LiveServerContent(turn_complete=True))

        live = self.live_module.Live.__new__(self.live_module.Live)
        live.セッションID = "session"
        live.チャンネル = "0"
        messages = []

        async def send(channel, data):
            messages.append({**data, "チャンネル": channel})

        live.接続 = stdlib_types.SimpleNamespace(send_to_channel=send)
        self.assertTrue(await live._send_output_text(await ai.テキスト受信Ｑ.get()))
        self.assertEqual("output_text", messages[0]["メッセージ識別"])
        self.assertEqual("0", messages[0]["チャンネル"])
        self.assertEqual("AiDiy は、日本語で業務システムを開発するプロジェクトです。", messages[0]["メッセージ内容"])
        await ai._サーバーコンテンツ処理(types.LiveServerContent(turn_complete=True))
        self.assertTrue(ai.テキスト受信Ｑ.empty())

    async def test_interrupted_transcript_is_flushed_and_next_turn_is_separate(self):
        ai = self.gemini()
        await ai._サーバーコンテンツ処理(types.LiveServerContent(
            output_transcription=types.Transcription(text="途中の回答"), interrupted=True,
        ))
        await ai._サーバーコンテンツ処理(types.LiveServerContent(
            output_transcription=types.Transcription(text="次の回答"), turn_complete=True,
        ))
        self.assertEqual({"text": "途中の回答"}, await ai.テキスト受信Ｑ.get())
        self.assertEqual({"text": "次の回答"}, await ai.テキスト受信Ｑ.get())

    async def test_send_failures_report_error_instead_of_invisible_marker(self):
        for mode in ("stopped", "rejected", "exception"):
            with self.subTest(mode=mode):
                live = self.live_module.Live.__new__(self.live_module.Live)
                live.セッションID = "session"
                live.チャンネル = "0"
                send = AsyncMock()
                live.接続 = stdlib_types.SimpleNamespace(send_to_channel=send)
                live.AIインスタンス = None if mode == "stopped" else stdlib_types.SimpleNamespace(
                    is_alive=True, テキスト送信=AsyncMock(
                        return_value=False, side_effect=RuntimeError("failure") if mode == "exception" else None,
                    ),
                )
                self.assertFalse(await live.テキスト送信("説明してください。"))
                channel, packet = send.call_args.args
                self.assertEqual("0", channel)
                self.assertEqual("error", packet["メッセージ識別"])
                self.assertIn("送信できませんでした", packet["メッセージ内容"])

    async def test_send_during_connection_waits_for_provider_session(self):
        for module, session_field in ((self.gemini_module, "live_session"),
                                      (self.openai_module, "ws_session")):
            with self.subTest(provider=module.__name__):
                ai = module.LiveAI.__new__(module.LiveAI)
                ai.is_alive = False
                ai.中断停止フラグ = False
                ai.エラーフラグ = False
                ai.live_session = None
                ai.ws_session = None
                ai.client = object()
                session = stdlib_types.SimpleNamespace(send_client_content=AsyncMock(), send=Mock())
                live = self.live_module.Live.__new__(self.live_module.Live)
                live.セッションID = "session"
                live.チャンネル = "0"
                live.AIインスタンス = ai
                live.接続 = stdlib_types.SimpleNamespace(send_to_channel=AsyncMock())

                async def ready(_seconds):
                    setattr(ai, session_field, session)
                    ai.is_alive = True

                with patch.object(module.asyncio, "sleep", side_effect=ready) as wait:
                    self.assertTrue(await live.テキスト送信("接続直後の依頼"))
                wait.assert_awaited()
                live.接続.send_to_channel.assert_not_awaited()
                if session_field == "live_session":
                    session.send_client_content.assert_awaited_once()
                    self.assertEqual("接続直後の依頼", session.send_client_content.call_args.kwargs["turns"].parts[0].text)
                else:
                    self.assertEqual(2, session.send.call_count)
                    packet = json.loads(session.send.call_args_list[0].args[0])
                    self.assertEqual("接続直後の依頼", packet["item"]["content"][0]["text"])

    async def test_connection_timeout_still_reports_one_error(self):
        ai = self.gemini()
        ai.live_session = None
        ai.client = object()
        ai.is_alive = False
        ai.中断停止フラグ = False
        ai.エラーフラグ = False
        live = self.live_module.Live.__new__(self.live_module.Live)
        live.セッションID = "session"
        live.チャンネル = "0"
        live.AIインスタンス = ai
        live.接続 = stdlib_types.SimpleNamespace(send_to_channel=AsyncMock())
        with patch.object(self.gemini_module.asyncio, "sleep", new_callable=AsyncMock) as wait:
            self.assertFalse(await live.テキスト送信("接続できないときの依頼"))
        self.assertGreaterEqual(wait.await_count, 50)
        self.assertLessEqual(wait.await_count, 51)
        live.接続.send_to_channel.assert_awaited_once()
        packet = live.接続.send_to_channel.call_args.args[1]
        self.assertEqual("error", packet["メッセージ識別"])
        self.assertIn("接続状態", packet["メッセージ内容"])
        self.assertNotIn("APIキー", packet["メッセージ内容"])

    async def test_explicitly_stopped_provider_is_not_sent_text(self):
        live = self.live_module.Live.__new__(self.live_module.Live)
        live.セッションID = "session"
        live.チャンネル = "0"
        live.AIインスタンス = stdlib_types.SimpleNamespace(
            is_alive=False, 中断停止フラグ=True, テキスト送信=AsyncMock(return_value=True),
        )
        live.接続 = stdlib_types.SimpleNamespace(send_to_channel=AsyncMock())
        self.assertFalse(await live.テキスト送信("停止後の依頼"))
        live.AIインスタンス.テキスト送信.assert_not_awaited()
        live.接続.send_to_channel.assert_awaited_once()

    async def test_openai_credit_error_reaches_screen_and_stops_reconnect(self):
        module = self.openai_module
        ai = module.LiveAI(セッションID="session", api_key="test-key", live_model="gpt-realtime-2.1-mini", live_voice="marin")
        ai.テキスト受信Ｑ = asyncio.Queue()
        socket = Mock()
        socket.recv.return_value = json.dumps({"type": "error", "error": {
            "type": "insufficient_quota", "code": "credit_balance_exhausted",
            "message": "You have no credits remaining.",
        }})
        with patch.object(module.websocket, "create_connection", return_value=socket) as connect:
            await asyncio.wait_for(ai._ライブセッションワーカー(), timeout=3)
        connect.assert_called_once()
        self.assertIn("model=gpt-realtime-2.1-mini", connect.call_args.args[0])
        socket.close.assert_called_once()
        self.assertTrue(ai.中断停止フラグ)
        self.assertFalse(ai.is_alive)
        self.assertEqual(1, ai.テキスト受信Ｑ.qsize())
        live = self.live_module.Live.__new__(self.live_module.Live)
        live.セッションID = "session"
        live.チャンネル = "0"
        live.AIインスタンス = ai
        live.接続 = stdlib_types.SimpleNamespace(send_to_channel=AsyncMock())
        self.assertTrue(await live._send_output_text(await ai.テキスト受信Ｑ.get()))
        channel, packet = live.接続.send_to_channel.call_args.args
        self.assertEqual("0", channel)
        self.assertEqual("error", packet["メッセージ識別"])
        self.assertEqual("credit_balance_exhausted", packet["エラーコード"])
        self.assertIn("クレジット残高がありません", packet["メッセージ内容"])
        self.assertIn("Billing", packet["メッセージ内容"])
        self.assertNotIn("APIキー", packet["メッセージ内容"])
        # 続けて送信しても、残高不足の説明を共通エラーで上書きしない。
        self.assertFalse(await live.テキスト送信("依頼"))
        self.assertEqual(packet["メッセージ内容"], live.接続.send_to_channel.call_args.args[1]["メッセージ内容"])

    async def test_openai_non_quota_error_keeps_retry_and_redacts_key(self):
        ai = self.openai_module.LiveAI(セッションID="session", api_key="test-secret")
        ai.テキスト受信Ｑ = asyncio.Queue()
        await ai._APIエラー通知({
            "type": "invalid_request_error", "code": "invalid_value",
            "message": "Invalid value: test-secret sk-partially-masked for session.audio.output.voice",
        })
        self.assertFalse(ai.中断停止フラグ)
        error = await ai.テキスト受信Ｑ.get()
        self.assertEqual("invalid_value", error["code"])
        self.assertIn("session.audio.output.voice", error["error"])
        self.assertNotIn("test-secret", error["error"])
        self.assertNotIn("sk-partially-masked", error["error"])

    async def test_native_transcript_avoids_duplicate_output_recognition(self):
        audio = self.audio_module
        for provider, subtitles in (("gemini_live", True), ("gemini_live", False), ("openai_live", False)):
            with self.subTest(provider=provider, subtitles=subtitles):
                pcm = b"\x00" * audio.MIN_AUDIO_BYTES
                data = audio.初期化_音声データ()
                for name, prefix in (("音声入力データ", "音声入力"), ("音声出力データ", "音声出力")):
                    data[name][f"{prefix}バッファ"] = [pcm]
                    data[name][f"{prefix}最終時刻"] = 1
                recognize = AsyncMock()
                connection = stdlib_types.SimpleNamespace(
                    is_connected=True, セッションID="session", audio_data=data, output_audio_paused=False,
                    send_to_channel=AsyncMock(),
                    recognition_processor=stdlib_types.SimpleNamespace(音声認識要求=recognize),
                    live_processor=stdlib_types.SimpleNamespace(AIインスタンス=stdlib_types.SimpleNamespace(
                        LIVE_AI=provider, 音声出力字幕対応=subtitles,
                    )),
                )

                async def finish(_seconds):
                    connection.is_connected = False

                with patch.object(audio.time, "time", return_value=100), patch.object(audio.asyncio, "sleep", side_effect=finish):
                    await audio.統合音声分離ワーカー(connection)
                recognized = [call.args[0] for call in recognize.call_args_list]
                self.assertEqual(["input"] if subtitles or provider == "openai_live" else ["input", "output"], recognized)
                self.assertFalse(data["音声出力データ"]["音声出力バッファ"])

    async def test_project_context_reads_selected_folder_instead_of_aidiy_root(self):
        live = self.live_module
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            context_file = base / "context.json"
            context_file.write_text(json.dumps(live._context_template_payload()), encoding="utf-8")
            project = base / "別プロジェクト"
            project.mkdir()
            (project / "_AIDIY.md").write_text("このフォルダは写真整理アプリです。", encoding="utf-8-sig")
            with patch.object(live, "_LIVE_CONTEXT_JSON_PATH", str(context_file)):
                instruction = live._load_or_create_live_context(str(project))
            self.assertIn("このフォルダは写真整理アプリです。", instruction)
            self.assertNotIn("配車のサンプル実装内容教えて？", instruction)


if __name__ == "__main__":
    unittest.main()

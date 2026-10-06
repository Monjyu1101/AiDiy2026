# -*- coding: utf-8 -*-

import asyncio
from contextlib import asynccontextmanager
import importlib.util
import json
import logging
import queue
from pathlib import Path
import sys
import tempfile
import time
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

    async def test_thought_parts_are_not_forwarded_as_conversation_answers(self):
        ai = self.gemini()
        await ai._サーバーコンテンツ処理(types.LiveServerContent(
            model_turn=types.Content(parts=[
                types.Part(text="internal reasoning", thought=True),
                types.Part.from_bytes(data=b"\x00\x00", mime_type="audio/pcm;rate=24000"),
            ]),
            output_transcription=types.Transcription(text="こんにちは。"), turn_complete=True,
        ))
        self.assertEqual(1, ai.音声受信Ｑ.qsize())
        self.assertEqual({"text": "こんにちは。"}, await ai.テキスト受信Ｑ.get())
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
                ai = (module.LiveAI(セッションID="session", api_key="test-key")
                      if session_field == "ws_session" else module.LiveAI.__new__(module.LiveAI))
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

    @asynccontextmanager
    async def openai_events(self):
        ai = self.openai_module.LiveAI(セッションID="session", api_key="test-key")
        ai.session_start_time = time.time()
        ai.テキスト受信Ｑ = asyncio.Queue()
        ai.tool_instance = stdlib_types.SimpleNamespace(execute_tool_call=AsyncMock(return_value="依頼受付"))
        incoming = queue.Queue()
        ai.ws_session = Mock(recv=lambda: incoming.get(timeout=2))

        async def exchange(*events):
            for event in events:
                incoming.put(json.dumps(event))
            # 受信側が先行イベントを処理したことを確認する。
            incoming.put(json.dumps({"type": "response.output_audio_transcript.done", "transcript": "barrier"}))
            self.assertEqual("barrier", (await asyncio.wait_for(ai.テキスト受信Ｑ.get(), 2))["text"])

        async with asyncio.TaskGroup() as group:
            ai.task_group = group
            reader = group.create_task(ai._受信ワーカー())
            try:
                yield ai, exchange
            finally:
                ai.中断停止フラグ = True
                for task in tuple(ai._ツールタスク):
                    task.cancel()
                incoming.put("{}")
                await asyncio.wait_for(reader, 2)

    async def wait_until(self, predicate):
        async def wait():
            while not predicate():
                await asyncio.sleep(0.001)
        await asyncio.wait_for(wait(), 2)

    def function_call(self, call_id="call1", status="completed"):
        return {"type": "function_call", "status": status, "call_id": call_id,
                "name": "code_agent", "arguments": json.dumps({"依頼": "画像と文書流し込みを修正"})}

    def response_done(self, *calls, status="completed"):
        return {"type": "response.done", "response": {"id": "resp1", "status": status, "output": list(calls)}}

    async def test_openai_tools_wait_for_response_done_and_resume_once(self):
        async with self.openai_events() as (ai, exchange):
            await exchange({"type": "response.created", "response": {"id": "resp1"}},
                           {**self.function_call(), "type": "response.function_call_arguments.done"})
            ai.tool_instance.execute_tool_call.assert_not_awaited()
            ai.ws_session.send.assert_not_called()
            await exchange(self.response_done(self.function_call(), self.function_call("call2")))
            await self.wait_until(lambda: ai.ws_session.send.call_count == 3)
            packets = [json.loads(call.args[0]) for call in ai.ws_session.send.call_args_list]
            self.assertEqual(["conversation.item.create", "conversation.item.create", "response.create"],
                             [packet["type"] for packet in packets])
            self.assertEqual(["call1", "call2"], [packet["item"]["call_id"] for packet in packets[:2]])
            self.assertEqual(2, ai.tool_instance.execute_tool_call.await_count)
            self.assertFalse(ai.エラーフラグ)

    async def test_openai_does_not_execute_interrupted_or_incomplete_calls(self):
        async with self.openai_events() as (ai, exchange):
            for status in ("cancelled", "incomplete"):
                await exchange({**self.function_call(), "type": "response.function_call_arguments.done"},
                               self.response_done(self.function_call(), status=status))
            await exchange(self.response_done(self.function_call(status="incomplete")))
            ai.tool_instance.execute_tool_call.assert_not_awaited()
            ai.ws_session.send.assert_not_called()

    async def test_openai_additional_text_waits_for_active_response(self):
        async with self.openai_events() as (ai, exchange):
            # response.created をまだ受信していなくても2回目の開始を防ぐ。
            self.assertTrue(await ai.テキスト送信("最初の依頼"))
            self.assertTrue(await ai.テキスト送信("補足の依頼"))
            packets = [json.loads(call.args[0]) for call in ai.ws_session.send.call_args_list]
            self.assertEqual(1, sum(packet["type"] == "response.create" for packet in packets))
            await exchange({"type": "response.created"}, self.response_done())
            packets = [json.loads(call.args[0]) for call in ai.ws_session.send.call_args_list]
            self.assertEqual(2, sum(packet["type"] == "response.create" for packet in packets))

    async def test_openai_receives_while_tool_runs_and_waits_for_vad_response(self):
        async with self.openai_events() as (ai, exchange):
            gate = asyncio.Event()
            async def execute(*_args):
                await gate.wait()
                return "依頼受付"
            ai.tool_instance.execute_tool_call.side_effect = execute
            await exchange(self.response_done(self.function_call()))
            await self.wait_until(lambda: ai.tool_instance.execute_tool_call.await_count == 1)
            self.assertTrue(await ai.テキスト送信("追加の依頼"))
            # ツール実行中も自動応答の開始を受信し、ツール結果の回答開始を延期する。
            await exchange({"type": "response.created"})
            gate.set()
            await self.wait_until(lambda: not ai._ツールタスク)
            packets = [json.loads(call.args[0]) for call in ai.ws_session.send.call_args_list]
            self.assertFalse(any(packet["type"] == "response.create" for packet in packets))
            await exchange(self.response_done())
            packets = [json.loads(call.args[0]) for call in ai.ws_session.send.call_args_list]
            self.assertEqual(1, sum(packet["type"] == "response.create" for packet in packets))

    async def test_openai_active_response_conflict_keeps_connection_and_retries_after_done(self):
        async with self.openai_events() as (ai, exchange):
            await exchange({"type": "response.created"}, {"type": "error", "error": {
                "code": "conversation_already_has_active_response", "message": "active response"}})
            self.assertFalse(ai.エラーフラグ)
            ai.ws_session.send.assert_not_called()
            await exchange(self.response_done())
            self.assertEqual({"type": "response.create"}, json.loads(ai.ws_session.send.call_args.args[0]))

    async def test_openai_failed_tool_returns_error_and_resumes(self):
        async with self.openai_events() as (ai, exchange):
            ai.tool_instance.execute_tool_call.side_effect = RuntimeError("tool failure")
            with self.assertLogs(level="ERROR"):
                await exchange(self.response_done(self.function_call()))
                await self.wait_until(lambda: ai.ws_session.send.call_count == 2)
            packets = [json.loads(call.args[0]) for call in ai.ws_session.send.call_args_list]
            self.assertIn("error", json.loads(packets[0]["item"]["output"]))
            self.assertEqual("response.create", packets[1]["type"])

    async def test_openai_stop_cancels_tool_without_continuation(self):
        async with self.openai_events() as (ai, exchange):
            async def execute(*_args):
                await asyncio.Event().wait()
            ai.tool_instance.execute_tool_call.side_effect = execute
            await exchange(self.response_done(self.function_call()))
            await self.wait_until(lambda: ai.tool_instance.execute_tool_call.await_count == 1)
        self.assertFalse(ai._ツールタスク)
        ai.ws_session.send.assert_not_called()

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

    async def test_openai_failed_response_reports_reason_without_running_tools_or_retrying_response(self):
        for code in ("credit_balance_exhausted", "server_error", None):
            with self.subTest(code=code):
                ai = self.openai_module.LiveAI(セッションID="session", api_key="test-key")
                ai.テキスト受信Ｑ = asyncio.Queue()
                ai._応答生成待ち = True
                ai.tool_instance = stdlib_types.SimpleNamespace(execute_tool_call=AsyncMock())
                packet = self.response_done(self.function_call(), status="failed")
                if code:
                    packet["response"]["status_details"] = {"error": {"code": code, "message": "generation failed"}}
                def receive():
                    ai.中断停止フラグ = True  # 1イベントで受信テストを終了する。
                    return json.dumps(packet)
                ai.ws_session = Mock(recv=receive)
                await ai._受信ワーカー()
                result = await ai.テキスト受信Ｑ.get()
                self.assertEqual(code or "response_failed", result["code"])
                self.assertFalse(ai._応答生成待ち)
                ai.ws_session.send.assert_not_called()
                ai.tool_instance.execute_tool_call.assert_not_awaited()

    async def test_openai_handshake_credit_rejection_reaches_screen_and_stops_reconnect(self):
        module = self.openai_module
        ai = module.LiveAI(セッションID="session", api_key="test-key")
        ai.テキスト受信Ｑ = asyncio.Queue()
        error = module.websocket.WebSocketBadStatusException("private-response-headers", 429, resp_body=json.dumps({
            "error": {"code": "credit_balance_exhausted", "message": "no credits"},
        }))
        with patch.object(module.websocket, "create_connection", side_effect=error) as connect:
            await asyncio.wait_for(ai._ライブセッションワーカー(), 2)
        self.assertEqual(2, connect.call_count)  # 既存のヘッダdict / 配列による接続試行。
        self.assertTrue(ai.中断停止フラグ)
        result = await ai.テキスト受信Ｑ.get()
        self.assertEqual("credit_balance_exhausted", result["code"])
        self.assertIn("クレジット残高", result["error"])
        self.assertNotIn("private-response-headers", result["error"])

    async def test_openai_connection_exception_reports_type_without_headers_or_keys(self):
        module = self.openai_module
        ai = module.LiveAI(セッションID="session", api_key="test-key")
        ai.テキスト受信Ｑ = asyncio.Queue()
        for error, code in (
            (module.websocket.WebSocketBadStatusException("private-headers", 503, resp_body="<html>private-body</html>"), "http_503"),
            (TimeoutError("timed out test-key Bearer private-token"), "TimeoutError"),
        ):
            await ai._接続エラー通知(error)
            result = await ai.テキスト受信Ｑ.get()
            self.assertEqual(code, result["code"])
            self.assertNotIn("private-", result["error"])
            self.assertNotIn("test-key", result["error"])
            self.assertFalse(ai.中断停止フラグ)

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

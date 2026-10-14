# -*- coding: utf-8 -*-
"""Code専用セッションが音声リソースを起動しないことを実処理で検証する。"""
import ast
import asyncio
import base64
import importlib.util
import json
import logging
from pathlib import Path
import sys
import types
from typing import Optional
import unittest
from unittest.mock import AsyncMock, Mock, patch

import numpy  # patch.dictでNumPyのC拡張を再インポートしない。
from pydantic import BaseModel
from starlette.websockets import WebSocketDisconnect, WebSocketState


BACKEND = Path(__file__).resolve().parents[1]


def load_module(filename, stubs):
    spec = importlib.util.spec_from_file_location(
        "code_voice_test_" + filename, BACKEND / "AIコア" / filename,
    )
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, stubs):
        spec.loader.exec_module(module)
    return module


def load_router_functions(names, namespace):
    """DBや実Providerをimportせず、ルーターの実際の関数を実行する。"""
    tree = ast.parse((BACKEND / "core_router" / "AIコア.py").read_text(encoding="utf-8"))
    nodes = [node for node in tree.body if getattr(node, "name", "") in names]
    for node in nodes:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            node.decorator_list = []
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "AIコア.py", "exec"), namespace)
    return namespace


class Socket:
    """init後も接続を維持し、実ハンドラーの受信ループを操作する。"""

    def __init__(self, conf=None, packet=None):
        self.app = types.SimpleNamespace(conf=conf)
        self.application_state = WebSocketState.CONNECTED
        self.messages = []
        self.incoming = asyncio.Queue()
        self.initialized = asyncio.Event()
        self.receives = 0
        self.close_code = None
        if packet is not None:
            self.incoming.put_nowait(packet)

    async def accept(self):
        pass

    async def receive_json(self):
        self.receives += 1
        if self.receives > 1:
            self.initialized.set()
        packet = await self.incoming.get()
        if isinstance(packet, Exception):
            raise packet
        return packet

    async def send_json(self, data):
        self.messages.append(data)

    async def close(self, code=1000, **kwargs):
        self.close_code = code
        self.application_state = WebSocketState.DISCONNECTED
        self.incoming.put_nowait(WebSocketDisconnect(code))


def provider(**kwargs):
    instance = types.SimpleNamespace(
        is_alive=False, AIインスタンス=None,
        AI_NAME=kwargs.get("AI_NAME", ""), AI_MODEL=kwargs.get("AI_MODEL", ""),
        AI_VOICE=kwargs.get("AI_VOICE", ""), 絶対パス=kwargs.get("絶対パス", ""),
        接続時welcome送信=AsyncMock(), 待受準備確認=AsyncMock(), コード要求=AsyncMock(),
        システム指示更新=Mock(), _select_ai_module=Mock(return_value=None),
    )

    async def start():
        instance.is_alive = True

    async def stop():
        instance.is_alive = False
        instance.AIインスタンス = None

    instance.開始 = AsyncMock(side_effect=start)
    instance.終了 = AsyncMock(side_effect=stop)
    return instance


class VoiceResourceTest(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        log = types.ModuleType("log_config")
        log.get_logger = logging.getLogger
        stubs = {"log_config": log}
        cls.audio_module = load_module("AI音声処理.py", stubs)
        cls.stream_module = load_module("AIストリーミング処理.py", stubs)
        backup = types.ModuleType("AIコア.AIバックアップ")
        backup.コードベース絶対パス取得 = Mock(return_value=str(BACKEND))
        stubs.update({
            "AIコア.AI音声処理": cls.audio_module,
            "AIコア.AIストリーミング処理": cls.stream_module,
            "AIコア.AIバックアップ": backup,
        })
        cls.session_module = load_module("AIセッション管理.py", stubs)

    def setUp(self):
        self.manager = self.session_module.WebSocketManager()
        self.conf = types.SimpleNamespace(json={
            "CODE_BASE_PATH": "../", "CODE_AI1_NAME": "codex_cli",
            "CODE_AI1_MODEL": "auto", "LIVE_AI_NAME": "gemini_live",
            "LIVE_GEMINI_MODEL": "test-live-model", "LIVE_GEMINI_VOICE": "Kore",
        })
        self.logger = Mock()
        self.recognition = Mock(side_effect=lambda *args, **kwargs: provider(**kwargs))
        self.live = Mock(side_effect=lambda *args, **kwargs: provider(**kwargs))
        self.chat = Mock(side_effect=lambda *args, **kwargs: provider(**kwargs))
        self.code = Mock(side_effect=lambda *args, **kwargs: provider(**kwargs))
        self.split = AsyncMock()
        self.audio_input = AsyncMock()
        self.endpoint_tasks = []
        self.endpoint_sockets = []
        tools = types.ModuleType("AIコア.AI内部ツール")
        tools.Tools = Mock(return_value=object())
        self.module_patch = patch.dict(sys.modules, {"AIコア.AI内部ツール": tools})
        self.module_patch.start()
        self.addCleanup(self.module_patch.stop)
        namespace = {
            "WebSocket": object, "WebSocketDisconnect": WebSocketDisconnect,
            "AIセッション管理": self.manager, "logger": self.logger,
            "_ws_log": Mock(), "バックエンドディレクトリ": str(BACKEND),
            "コードベース絶対パス取得": Mock(return_value=str(BACKEND)),
            "バックアップ実行_共通ログ": Mock(return_value=None),
            "保存_会話履歴": Mock(), "welcome対象チャンネル一覧": (),
            "コードチャンネル一覧": [str(i) for i in range(1, 7)],
            "数値チャンネル一覧": [str(i) for i in range(7)],
            "Recognition": self.recognition, "Live": self.live,
            "Chat": self.chat, "CodeAgent": self.code,
            "StreamingProcessor": Mock(return_value=types.SimpleNamespace(start=AsyncMock(), stop=AsyncMock())),
            "統合音声分離ワーカー": self.split, "音声入力データ処理": self.audio_input,
            "asyncio": asyncio, "base64": base64, "json": json,
            "_is_disconnect_like_error": lambda exc: False,
            "_is_ws_connected": lambda ws: ws.application_state == WebSocketState.CONNECTED,
            "BaseModel": BaseModel, "Optional": Optional, "Request": object,
        }
        self.router = load_router_functions(
            {"websocket_endpoint", "モデル情報設定", "モデル設定リクエスト"}, namespace,
        )

    async def asyncTearDown(self):
        for socket in self.endpoint_sockets:
            await socket.close()
        if self.endpoint_tasks:
            await asyncio.wait_for(asyncio.gather(*self.endpoint_tasks), 2)
        for session in self.manager.sessions.values():
            await session.close()

    async def open_endpoint(self, socket_no="input", session_id=None, **extra):
        packet = {"type": "connect", "ソケット番号": socket_no, **extra}
        if session_id:
            packet["セッションID"] = session_id
        socket = Socket(self.conf, packet)
        self.endpoint_sockets.append(socket)
        task = asyncio.create_task(self.router["websocket_endpoint"](socket))
        self.endpoint_tasks.append(task)
        initialized = asyncio.create_task(socket.initialized.wait())
        try:
            done, _ = await asyncio.wait({task, initialized}, timeout=2, return_when=asyncio.FIRST_COMPLETED)
            self.assertTrue(done, "WebSocket初期化が完了しません")
            if task in done:
                await task
                self.fail(f"初期化前に終了: {socket.messages}; {self.logger.mock_calls}")
        finally:
            initialized.cancel()
            await asyncio.gather(initialized, return_exceptions=True)
        self.logger.error.assert_not_called()
        session_id = next(message["セッションID"] for message in socket.messages if message.get("メッセージ識別") == "init")
        return socket, self.manager.get_session(session_id), task

    async def model_session(self, voice=True, audio_connected=None):
        session_id = await self.manager.connect(Socket(), app_conf=self.conf, voice=voice)
        session = self.manager.get_session(session_id)
        session.ボタン状態.update({"マイク": True, "スピーカー": False, "イメージ": True})
        session.live_processor = provider()
        session.live_processor.is_alive = True
        session.live_processor.AIインスタンス = object()
        session.code_agent_processors = [provider() for _ in range(6)]
        if audio_connected is not None:
            audio = self.session_module.WebSocketConnection(Socket(), session_id, "audio")
            audio.is_connected = audio_connected
            session.set_socket("audio", audio)
        return session

    async def update_models(self, session, values):
        buttons = dict(session.ボタン状態)
        configuration = dict(self.conf.json)
        request = self.router["モデル設定リクエスト"](
            セッションID=session.セッションID, モデル設定=values,
        )
        result = await self.router["モデル情報設定"](
            types.SimpleNamespace(app=types.SimpleNamespace(conf=self.conf)), request,
        )
        self.assertEqual(result["status"], "OK", result)
        self.logger.exception.assert_not_called()
        self.assertEqual(session.ボタン状態, buttons)
        self.assertEqual(self.conf.json, configuration)
        for key, value in values.items():
            self.assertEqual(session.モデル設定[key], value)

    async def test_code_connect_and_reconnect_create_no_voice_resources(self):
        socket, session, task = await self.open_endpoint(voice=False)
        self.assertFalse(session.voice_enabled)
        self.assertIsNone(session.audio_data)
        self.assertIsNone(session.recognition_processor)
        self.assertIsNone(getattr(session, "live_processor", None))
        self.assertIsNone(session.audio_split_task)
        self.assertEqual(self.code.call_count, 6)
        self.assertEqual(self.chat.call_count, 1)
        session.ボタン状態.update({"マイク": True, "イメージ": True})
        session.update_model_settings({"CODE_AI1_MODEL": "selected-code-model"}, manager=self.manager)
        buttons = dict(session.ボタン状態)
        settings = dict(session.モデル設定)
        await socket.close()
        await asyncio.wait_for(task, 2)
        _, restored, _ = await self.open_endpoint(session_id=session.セッションID)
        self.assertFalse(restored.voice_enabled)
        self.assertIsNone(restored.audio_data)
        self.assertEqual(restored.ボタン状態, buttons)
        self.assertEqual(restored.モデル設定, settings)
        await self.open_endpoint(socket_no="core", session_id=session.セッションID, voice=False)
        self.recognition.assert_not_called()
        self.live.assert_not_called()
        self.split.assert_not_called()

    async def test_voice_disabled_code_request_still_routes_and_saves_history(self):
        socket, session, task = await self.open_endpoint(voice=False)
        output, _, _ = await self.open_endpoint(socket_no="1", session_id=session.セッションID, voice=False)
        socket.incoming.put_nowait({
            "メッセージ識別": "input_text", "チャンネル": "1",
            "メッセージ内容": "コードを確認してください", "self_check_loop": 1,
        })
        socket.incoming.put_nowait(WebSocketDisconnect())
        await asyncio.wait_for(task, 2)
        session.code_agent_processors[0].コード要求.assert_awaited_once()
        request = session.code_agent_processors[0].コード要求.call_args.args[0]
        self.assertEqual(request["メッセージ内容"], "コードを確認してください")
        self.assertEqual(request["self_check_loop"], 1)
        self.assertTrue(any(packet.get("メッセージ内容") == "コードを確認してください" for packet in output.messages))
        self.router["保存_会話履歴"].assert_called_once()
        self.recognition.assert_not_called()
        self.live.assert_not_called()
        self.logger.error.assert_not_called()

    async def test_last_audio_disconnect_and_reconnect_recreate_recognition(self):
        socket, session, task = await self.open_endpoint(socket_no="audio")
        recognition = session.recognition_processor
        live = session.live_processor
        await socket.close()
        await asyncio.wait_for(task, 2)
        recognition.終了.assert_awaited_once()
        self.assertIsNone(session.recognition_processor)
        self.assertIsNone(session.audio_split_task)
        _, restored, _ = await self.open_endpoint(socket_no="audio", session_id=session.セッションID)
        self.assertIs(restored, session)
        self.assertIsNot(restored.recognition_processor, recognition)
        restored.recognition_processor.開始.assert_awaited_once()
        self.assertEqual(self.recognition.call_count, 2)
        self.assertEqual(self.live.call_count, 1)
        self.assertEqual(live.開始.await_count, 2)
        self.logger.error.assert_not_called()

    async def test_legacy_voice_default_keeps_recognition_and_starts_live_only_on_audio(self):
        _, session, _ = await self.open_endpoint(socket_no="core")
        self.assertTrue(session.voice_enabled)
        self.assertIsNotNone(session.audio_data)
        self.recognition.assert_called_once()
        session.recognition_processor.開始.assert_awaited_once()
        self.live.assert_called_once()
        session.live_processor.開始.assert_not_awaited()
        self.assertIsNotNone(session.audio_split_task)
        _, reused, _ = await self.open_endpoint(socket_no="audio", session_id=session.セッションID)
        self.assertIs(reused, session)
        self.assertTrue(session.get_socket("audio").is_connected)
        session.live_processor.開始.assert_awaited_once()
        self.assertEqual(self.recognition.call_count, 1)
        self.assertEqual(self.live.call_count, 1)

    async def test_explicit_voice_true_audio_connection_starts_live(self):
        _, session, _ = await self.open_endpoint(socket_no="audio", voice=True)
        self.assertTrue(session.voice_enabled)
        session.live_processor.開始.assert_awaited_once()
        self.recognition.assert_called_once()

    async def test_disabled_audio_socket_is_rejected_without_voice_resources(self):
        original, session, _ = await self.open_endpoint(voice=False)
        socket = Socket(self.conf, {
            "type": "connect", "セッションID": session.セッションID,
            "ソケット番号": "audio", "Live準備確認": True,
        })
        await self.router["websocket_endpoint"](socket)
        self.assertEqual(socket.close_code, 1008)
        self.assertTrue(any(message.get("メッセージ識別") == "error" for message in socket.messages))
        self.assertIs(session.get_socket("input").websocket, original)
        self.assertIsNone(session.get_socket("audio"))
        self.recognition.assert_not_called()
        self.live.assert_not_called()
        self.split.assert_not_called()

    async def test_disabled_input_audio_is_ignored_and_input_socket_still_works(self):
        socket, session, task = await self.open_endpoint(voice=False)
        socket.incoming.put_nowait({"メッセージ識別": "input_audio", "ファイル名": base64.b64encode(bytes(960)).decode("ascii")})
        socket.incoming.put_nowait({"type": "ping"})
        socket.incoming.put_nowait(WebSocketDisconnect())
        await asyncio.wait_for(task, 2)
        self.audio_input.assert_not_awaited()
        self.assertIn({"type": "pong", "セッションID": session.セッションID}, socket.messages)
        self.logger.error.assert_not_called()

    async def test_code_settings_do_not_restart_active_shared_live(self):
        session = await self.model_session(audio_connected=True)
        live = session.live_processor
        before = dict(session.モデル設定)
        await self.update_models(session, {"CODE_AI1_NAME": "claude_cli", "CODE_AI1_MODEL": "chosen-model"})
        self.assertEqual(session.code_agent_processors[0].AI_NAME, "claude_cli")
        self.assertEqual(session.code_agent_processors[0].AI_MODEL, "chosen-model")
        self.assertEqual(session.モデル設定["LIVE_AI_NAME"], before["LIVE_AI_NAME"])
        live.終了.assert_not_awaited()
        live.開始.assert_not_awaited()
        live._select_ai_module.assert_not_called()

    async def test_unchanged_live_values_do_not_restart_active_live(self):
        session = await self.model_session(audio_connected=True)
        values = {key: value for key, value in session.モデル設定.items() if key.startswith("LIVE_") or key == "CODE_BASE_PATH"}
        await self.update_models(session, values)
        session.live_processor.終了.assert_not_awaited()
        session.live_processor.開始.assert_not_awaited()

    async def test_save_only_then_apply_same_live_settings_restarts_once(self):
        session = await self.model_session(audio_connected=True)
        before = dict(session.モデル設定)
        live = session.live_processor
        live.AI_MODEL = before["LIVE_GEMINI_MODEL"]
        live.AI_VOICE = before["LIVE_GEMINI_VOICE"]

        class SavedConfig(dict):
            def update(self, values):
                super().update(values)
                return True

        self.conf.json = SavedConfig(self.conf.json)
        values = {"LIVE_GEMINI_MODEL": "saved-model", "LIVE_GEMINI_VOICE": "Zephyr"}
        request = self.router["モデル設定リクエスト"](
            セッションID=session.セッションID, モデル設定=values, save=True,
        )
        result = await self.router["モデル情報設定"](
            types.SimpleNamespace(app=types.SimpleNamespace(conf=self.conf)), request,
        )
        self.assertEqual(result["status"], "OK", result)
        self.assertEqual(self.conf.json["LIVE_GEMINI_MODEL"], "saved-model")
        self.assertEqual(session.モデル設定, before)
        live.終了.assert_not_awaited()
        live.開始.assert_not_awaited()
        await self.update_models(session, values)
        live.終了.assert_awaited_once()
        live.開始.assert_awaited_once()
        self.assertEqual(live.AI_MODEL, "saved-model")
        self.assertEqual(live.AI_VOICE, "Zephyr")
        await self.update_models(session, values)
        live.開始.assert_awaited_once()

    async def test_changed_live_model_restarts_connected_audio(self):
        session = await self.model_session(audio_connected=True)
        await self.update_models(session, {"LIVE_GEMINI_MODEL": "updated-live-model", "LIVE_GEMINI_VOICE": "Zephyr"})
        session.live_processor.終了.assert_awaited_once()
        session.live_processor.開始.assert_awaited_once()
        self.assertEqual(session.live_processor.AI_MODEL, "updated-live-model")
        self.assertEqual(session.live_processor.AI_VOICE, "Zephyr")

    async def test_changed_live_settings_without_connected_audio_never_start_live(self):
        for audio_connected in (None, False):
            with self.subTest(audio_connected=audio_connected):
                session = await self.model_session(audio_connected=audio_connected)
                await self.update_models(session, {"LIVE_GEMINI_MODEL": "updated-live-model"})
                session.live_processor.開始.assert_not_awaited()

    async def test_changed_live_settings_never_restart_voice_disabled_session(self):
        # 防御的検証: 古いプロセッサやaudio参照があってもvoice=falseを優先する。
        session = await self.model_session(voice=False, audio_connected=True)
        await self.update_models(session, {"LIVE_GEMINI_MODEL": "updated-live-model"})
        session.live_processor.終了.assert_not_awaited()
        session.live_processor.開始.assert_not_awaited()
        session.live_processor._select_ai_module.assert_not_called()

    async def test_streaming_needs_voice_and_connected_audio_for_chat_and_image(self):
        for method in ("_process_chat_ai", "_process_image_ai"):
            for voice, connected in ((False, True), (False, None), (True, None), (True, False), (True, True)):
                with self.subTest(method=method, voice=voice, audio_connected=connected):
                    session = await self.model_session(voice=voice, audio_connected=connected)
                    session.live_processor.AIインスタンス = None
                    processor = self.stream_module.StreamingProcessor(session.セッションID, session)
                    await getattr(processor, method)()
                    self.assertEqual(session.live_processor.開始.await_count, int(voice and connected is True))

    async def test_streaming_keeps_existing_live_instance_without_restart(self):
        session = await self.model_session(audio_connected=True)
        processor = self.stream_module.StreamingProcessor(session.セッションID, session)
        await processor._process_chat_ai()
        await processor._process_image_ai()
        session.live_processor.開始.assert_not_awaited()

    async def test_audio_input_rejects_disabled_session_before_analysis_or_provider_send(self):
        for audio_data in (None, self.audio_module.初期化_音声データ()):
            with self.subTest(has_stale_audio_data=audio_data is not None):
                send = AsyncMock()
                session = types.SimpleNamespace(
                    voice_enabled=False, audio_data=audio_data,
                    live_processor=types.SimpleNamespace(AIインスタンス=types.SimpleNamespace(音声送信=send)),
                )
                with patch.object(self.audio_module, "_音声レベル分析") as analyze:
                    await self.audio_module.音声入力データ処理(session, bytes(960))
                analyze.assert_not_called()
                send.assert_not_awaited()

    async def test_audio_input_still_forwards_pcm_for_enabled_session(self):
        send = AsyncMock()
        session = types.SimpleNamespace(
            voice_enabled=True, audio_data=self.audio_module.初期化_音声データ(),
            live_processor=types.SimpleNamespace(AIインスタンス=types.SimpleNamespace(音声送信=send)),
        )
        pcm = bytes(960)
        await self.audio_module.音声入力データ処理(session, pcm)
        send.assert_awaited_once_with(pcm)


if __name__ == "__main__":
    unittest.main()

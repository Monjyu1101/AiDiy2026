# -*- coding: utf-8 -*-
"""セッション音声能力・切断時の停止を、外部APIなしで実装そのものに対して検証する。"""
import asyncio
import importlib.util
import logging
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import AsyncMock, Mock, patch

from starlette.websockets import WebSocketState

BACKEND = Path(__file__).resolve().parents[1]


def load(filename, stubs):
    spec = importlib.util.spec_from_file_location('voice_test_' + filename, BACKEND / 'AIコア' / filename)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, stubs):
        spec.loader.exec_module(module)
    return module


class Socket:
    application_state = WebSocketState.CONNECTED

    def __init__(self, accept_entered=None, accept_release=None, on_close=None):
        self.messages = []
        self.closed = False
        self.accept_entered = accept_entered
        self.accept_release = accept_release
        self.on_close = on_close

    async def accept(self):
        if self.accept_entered:
            self.accept_entered.set()
        if self.accept_release:
            await self.accept_release.wait()

    async def send_json(self, data):
        self.messages.append(data)

    async def close(self, code=1000, reason=''):
        self.closed = True
        self.close_code = code
        if self.on_close:
            self.on_close()


class Processor:
    """実タスクを持ち、停止回数と会話オブジェクトの保持を確認できる偽Processor。"""

    def __init__(self):
        self.history = ['keep conversation']
        self.is_alive = True
        self.stop_count = 0
        self.task = asyncio.create_task(asyncio.Event().wait())
        self.worker_task = self.task

    async def stop(self):
        self.stop_count += 1
        self.is_alive = False
        self.task.cancel()
        await asyncio.gather(self.task, return_exceptions=True)

    async def 終了(self):
        await self.stop()


class SessionVoiceTest(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        logger = types.ModuleType('log_config')
        logger.get_logger = logging.getLogger
        stream = types.ModuleType('AIコア.AIストリーミング処理')
        stream.StreamingProcessor = object
        audio = types.ModuleType('AIコア.AI音声処理')
        audio.初期化_音声データ = dict
        stubs = {'log_config': logger, 'AIコア.AIストリーミング処理': stream, 'AIコア.AI音声処理': audio}
        stubs['AIコア.AIバックアップ'] = load('AIバックアップ.py', stubs)
        cls.module = load('AIセッション管理.py', stubs)

    def setUp(self):
        self.manager = self.module.WebSocketManager()
        self.conf = types.SimpleNamespace(json={'LIVE_AI_NAME': 'gemini_live', 'CODE_AI1_NAME': 'codex_cli'})

    async def asyncTearDown(self):
        for session in self.manager.sessions.values():
            await session.close()

    async def test_legacy_connections_default_to_voice_enabled(self):
        sid = await self.manager.connect(Socket(), app_conf=self.conf)
        session = self.manager.sessions[sid]
        self.assertTrue(session.voice_enabled)
        self.assertIsInstance(session.audio_data, dict)
        self.assertIs(self.manager.session_states[sid]['voice'], True)
        audio = Socket()
        await self.manager.connect(audio, セッションID=sid, socket_no='audio')
        self.assertIs(session.get_socket('audio').websocket, audio)

    async def test_replaced_connection_is_closed_with_replaced_code(self):
        # 同じセッション・チャンネルへ新しい接続が来たら、旧接続を4000で閉じる。
        # クライアントは4000では再接続せず、互いに置き換え合う繰り返しを起こさない。
        first = Socket()
        sid = await self.manager.connect(first, socket_no='0')
        second = Socket()
        await self.manager.connect(second, セッションID=sid, socket_no='0')
        self.assertTrue(first.closed)
        self.assertEqual(first.close_code, self.module.REPLACED_CLOSE_CODE)
        self.assertEqual(self.module.REPLACED_CLOSE_CODE, 4000)
        self.assertFalse(second.closed)
        self.assertIs(self.manager.sessions[sid].get_socket('0').websocket, second)

    async def test_disabled_session_never_allocates_audio_data(self):
        with patch.object(self.module, '初期化_音声データ', Mock(return_value={})) as initialize_audio:
            sid = await self.manager.connect(Socket(), voice=False)
            session = self.manager.sessions[sid]
            self.assertFalse(session.voice_enabled)
            self.assertIsNone(session.audio_data)
            self.assertIsNone(session.recognition_processor)
            self.assertIsNone(session.audio_split_task)
            await self.manager.disconnect(sid, socket_no='input')
            await session.close()
            initialize_audio.assert_not_called()

    async def test_voice_requires_a_real_boolean_before_any_session_or_socket_change(self):
        for value in ['false', 'true', 0, 1, [], {}]:
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, 'voice'):
                    await self.manager.connect(Socket(), voice=value)
        self.assertEqual(self.manager.sessions, {})
        self.assertEqual(self.manager.session_states, {})
        original = Socket()
        sid = await self.manager.connect(original)
        with self.assertRaises(ValueError):
            await self.manager.connect(Socket(), セッションID=sid, voice='false')
        self.assertFalse(original.closed)
        self.assertTrue(self.manager.sessions[sid].voice_enabled)
        with self.assertRaises(ValueError):
            self.module.SessionConnection('invalid', voice_enabled=0)

    async def test_omitted_or_null_voice_inherits_existing_disabled_session(self):
        sid = await self.manager.connect(Socket(), voice=False)
        for socket_no, kwargs in [('0', {}), ('1', {'voice': None}), ('2', {'voice': False})]:
            await self.manager.connect(Socket(), セッションID=sid, socket_no=socket_no, **kwargs)
        self.assertFalse(self.manager.sessions[sid].voice_enabled)
        self.assertIs(self.manager.session_states[sid]['voice'], False)
        self.assertIsNone(self.manager.sessions[sid].audio_data)

    async def test_save_and_ensure_preserve_disabled_capability_and_settings(self):
        sid = await self.manager.connect(Socket(), voice=False, app_conf=self.conf)
        session = self.manager.sessions[sid]
        session.update_state({'マイク': True}, manager=self.manager)
        session.update_model_settings({'CODE_AI1_MODEL': 'custom'}, manager=self.manager)
        self.manager.save_session_state(sid, session.ボタン状態)
        self.assertFalse(self.manager.session_states[sid]['voice'])
        self.assertEqual('custom', self.manager.session_states[sid]['モデル設定']['CODE_AI1_MODEL'])
        await self.manager.disconnect(sid)
        del self.manager.sessions[sid]
        # セッションオブジェクト不在でも、保存済みvoiceは保持する。
        self.manager.save_session_state(sid, session.ボタン状態)
        with patch.object(self.module, '初期化_音声データ', Mock(return_value={})) as initialize_audio:
            self.assertEqual(sid, self.manager.ensure_session(sid, app_conf=self.conf))
            initialize_audio.assert_not_called()
        restored = self.manager.sessions[sid]
        self.assertFalse(restored.voice_enabled)
        self.assertTrue(restored.ボタン状態['マイク'])
        self.assertEqual('custom', restored.モデル設定['CODE_AI1_MODEL'])

    async def test_connect_restores_saved_capability_and_legacy_ensure_defaults_true(self):
        self.manager.session_states['saved'] = {'voice': False, 'ボタン': {'マイク': False}, 'モデル設定': {}}
        with patch.object(self.module, '初期化_音声データ', Mock(return_value={})) as initialize_audio:
            await self.manager.connect(Socket(), セッションID='saved')
            initialize_audio.assert_not_called()
        self.assertFalse(self.manager.sessions['saved'].voice_enabled)
        self.manager.session_states['legacy'] = {'ボタン': {}, 'モデル設定': {}}
        self.manager.ensure_session('legacy')
        self.assertTrue(self.manager.sessions['legacy'].voice_enabled)
        self.assertTrue(self.manager.session_states['legacy']['voice'])
        fresh = self.manager.ensure_session()
        self.assertTrue(self.manager.sessions[fresh].voice_enabled)
        self.assertTrue(self.manager.session_states[fresh]['voice'])

    async def test_partial_legacy_state_accepts_initial_model_binding(self):
        self.manager.session_states['partial'] = {'ボタン': {'マイク': False}, 'voice': False}
        await self.manager.connect(Socket(), セッションID='partial',
                                   live_model_settings={'LIVE_AI_NAME': 'gemini_live'})
        session = self.manager.sessions['partial']
        self.assertFalse(session.voice_enabled)
        self.assertEqual('gemini_live', session.モデル設定['LIVE_AI_NAME'])
        self.assertFalse(self.manager.session_states['partial']['voice'])

    async def test_active_voice_conflict_preserves_existing_socket_and_runtime(self):
        for existing_voice in (True, False):
            with self.subTest(existing_voice=existing_voice):
                original = Socket()
                sid = await self.manager.connect(original, voice=existing_voice)
                session = self.manager.sessions[sid]
                runtime = Processor()
                session.chat_processor = runtime
                with self.assertRaisesRegex(ValueError, '接続中'):
                    await self.manager.connect(Socket(), セッションID=sid, voice=not existing_voice)
                self.assertFalse(original.closed)
                self.assertIs(session.get_socket('input').websocket, original)
                self.assertIs(session.voice_enabled, existing_voice)
                self.assertEqual(0, runtime.stop_count)

    async def test_inactive_voice_change_waits_for_shutdown_and_keeps_conversation_identity(self):
        sid = self.manager.ensure_session(app_conf=self.conf)
        session = self.manager.sessions[sid]
        settings, buttons = session.モデル設定, session.ボタン状態
        chat, code, live = Processor(), Processor(), Processor()
        session.chat_processor = chat
        session.code_agent_processors = [code]
        session.live_processor = live
        session.recognition_processor = Processor()
        session.streaming_processor = Processor()
        session.audio_split_task = asyncio.create_task(asyncio.Event().wait())
        old_tasks = [session.recognition_processor.task, session.streaming_processor.task, session.audio_split_task,
                     chat.task, code.task, live.task]
        entered, release = asyncio.Event(), asyncio.Event()
        stop_live = live.終了

        async def wait_before_stopping_live():
            entered.set()
            await release.wait()
            await stop_live()

        live.終了 = wait_before_stopping_live
        change = asyncio.create_task(self.manager.connect(Socket(), セッションID=sid, voice=False))
        try:
            await asyncio.wait_for(entered.wait(), 2)
            self.assertTrue(session.voice_enabled)
            self.assertFalse(change.done())
            release.set()
            await asyncio.wait_for(change, 2)
        finally:
            release.set()
            if not change.done():
                change.cancel()
                await asyncio.gather(change, return_exceptions=True)
        self.assertIs(self.manager.sessions[sid], session)
        self.assertIs(session.モデル設定, settings)
        self.assertIs(session.ボタン状態, buttons)
        self.assertIs(session.chat_processor, chat)
        self.assertIs(session.code_agent_processors[0], code)
        self.assertEqual(['keep conversation'], chat.history)
        self.assertTrue(all(task.done() for task in old_tasks))
        self.assertFalse(session.voice_enabled)
        self.assertIsNone(session.audio_data)
        self.assertIsNone(session.live_processor)
        self.assertIsNone(session.recognition_processor)
        self.assertIsNone(session.streaming_processor)
        self.assertIsNone(session.audio_split_task)
        self.assertFalse(self.manager.session_states[sid]['voice'])

    async def test_inactive_disabled_session_can_enable_voice(self):
        sid = await self.manager.connect(Socket(), voice=False)
        await self.manager.disconnect(sid, socket_no='input')
        session = self.manager.sessions[sid]
        audio = Socket()
        await self.manager.connect(audio, セッションID=sid, socket_no='audio', voice=True)
        self.assertTrue(session.voice_enabled)
        self.assertIsInstance(session.audio_data, dict)
        self.assertIs(session.get_socket('audio').websocket, audio)
        self.assertTrue(self.manager.session_states[sid]['voice'])

    async def test_audio_disabled_rejection_precedes_creation_or_registration(self):
        with self.assertRaisesRegex(ValueError, 'audio'):
            await self.manager.connect(Socket(), voice=False, socket_no='audio')
        self.assertEqual({}, self.manager.sessions)
        self.assertEqual({}, self.manager.session_states)
        self.manager.session_states['saved'] = {'voice': False, 'モデル設定': {}}
        with self.assertRaises(ValueError):
            await self.manager.connect(Socket(), セッションID='saved', socket_no='audio')
        self.assertNotIn('saved', self.manager.sessions)
        sid = await self.manager.connect(Socket(), voice=False)
        session = self.manager.sessions[sid]
        with self.assertRaises(ValueError):
            await self.manager.connect(Socket(), セッションID=sid, socket_no='audio')
        self.assertIsNone(session.get_socket('audio'))
        self.assertFalse(session.voice_enabled)

    async def test_parallel_first_connections_settle_voice_once(self):
        entered, release = asyncio.Event(), asyncio.Event()
        first_socket = Socket(accept_entered=entered, accept_release=release)
        first = asyncio.create_task(self.manager.connect(first_socket, セッションID='parallel', voice=False))
        second = None
        try:
            await asyncio.wait_for(entered.wait(), 2)
            second = asyncio.create_task(self.manager.connect(Socket(), セッションID='parallel', socket_no='0', voice=True))
            await asyncio.sleep(0)
            self.assertFalse(second.done())
            self.assertEqual(1, len(self.manager.sessions))
            release.set()
            await asyncio.wait_for(first, 2)
            with self.assertRaisesRegex(ValueError, '接続中'):
                await asyncio.wait_for(second, 2)
            session = self.manager.sessions['parallel']
            self.assertFalse(session.voice_enabled)
            self.assertIs(session.get_socket('input').websocket, first_socket)
            self.assertIsNone(session.get_socket('0'))
        finally:
            release.set()
            await asyncio.gather(*[task for task in (first, second) if task], return_exceptions=True)

    async def test_parallel_connections_without_flag_inherit_first_flag(self):
        results = await asyncio.gather(
            self.manager.connect(Socket(), セッションID='parallel', socket_no='input', voice=False),
            self.manager.connect(Socket(), セッションID='parallel', socket_no='0'),
            self.manager.connect(Socket(), セッションID='parallel', socket_no='1'),
        )
        self.assertEqual(['parallel'] * 3, results)
        self.assertFalse(self.manager.sessions['parallel'].voice_enabled)
        self.assertEqual(3, sum(bool(conn) for conn in self.manager.sessions['parallel'].sockets.values()))

    async def test_replaced_socket_finally_cannot_disconnect_new_owner(self):
        cleanup = []
        original = Socket(on_close=lambda: cleanup.append(asyncio.create_task(
            self.manager.disconnect('replacement', socket_no='input', websocket=original))))
        await self.manager.connect(original, セッションID='replacement', voice=False)
        session = self.manager.sessions['replacement']
        session.chat_processor = Processor()
        replacement = Socket()
        await self.manager.connect(replacement, セッションID='replacement')
        await asyncio.gather(*cleanup)
        self.assertTrue(original.closed)
        self.assertFalse(replacement.closed)
        self.assertTrue(session.is_connected)
        self.assertIs(session.get_socket('input').websocket, replacement)
        self.assertEqual(0, session.chat_processor.stop_count)
        await self.manager.disconnect('replacement', socket_no='input', websocket=replacement)
        self.assertFalse(session.is_connected)
        self.assertEqual(1, session.chat_processor.stop_count)

    async def test_last_disconnect_cancels_audio_and_streaming_and_reconnect_is_clean(self):
        first, second = Socket(), Socket()
        sid = await self.manager.connect(first, socket_no='core')
        await self.manager.connect(second, セッションID=sid, socket_no='audio')
        session = self.manager.sessions[sid]
        stream, recognition, live, chat, code = [Processor() for _ in range(5)]
        session.streaming_processor = stream
        session.recognition_processor = recognition
        session.live_processor = live
        session.chat_processor = chat
        session.code_agent_processors = [code]
        split = asyncio.create_task(asyncio.Event().wait())
        session.audio_split_task = split
        await self.manager.disconnect(sid, socket_no='core', websocket=first)
        self.assertEqual(0, recognition.stop_count)
        self.assertFalse(split.done())
        await self.manager.disconnect(sid, socket_no='audio', websocket=second)
        for processor in (stream, recognition, live, chat, code):
            self.assertEqual(1, processor.stop_count)
            self.assertTrue(processor.task.done())
        self.assertTrue(split.cancelled())
        self.assertIsNone(session.streaming_processor)
        self.assertIsNone(session.recognition_processor)
        self.assertIsNone(session.audio_split_task)
        self.assertIs(session.chat_processor, chat)
        self.assertIs(session.code_agent_processors[0], code)
        await self.manager.connect(Socket(), セッションID=sid, socket_no='core')
        self.assertIsNone(session.streaming_processor)
        self.assertIsNone(session.recognition_processor)
        self.assertIsNone(session.audio_split_task)
        self.assertTrue(session.voice_enabled)
        self.assertIsInstance(session.audio_data, dict)

    async def test_reconnect_waits_for_last_disconnect_cleanup(self):
        old_socket = Socket()
        sid = await self.manager.connect(old_socket)
        session = self.manager.sessions[sid]
        entered, release = asyncio.Event(), asyncio.Event()

        async def stop():
            entered.set()
            await release.wait()

        session.chat_processor = types.SimpleNamespace(終了=AsyncMock(side_effect=stop))
        disconnect = asyncio.create_task(self.manager.disconnect(sid, socket_no='input', websocket=old_socket))
        connect = None
        new_socket = Socket()
        try:
            await asyncio.wait_for(entered.wait(), 2)
            connect = asyncio.create_task(self.manager.connect(new_socket, セッションID=sid))
            await asyncio.sleep(0)
            self.assertFalse(connect.done())
            self.assertIsNone(session.get_socket('input'))
            release.set()
            await asyncio.wait_for(asyncio.gather(disconnect, connect), 2)
            self.assertIs(session.get_socket('input').websocket, new_socket)
            self.assertTrue(session.is_connected)
        finally:
            release.set()
            await asyncio.gather(*[task for task in (disconnect, connect) if task], return_exceptions=True)

    async def test_cleanup_cancels_stream_task_waiting_for_same_lock(self):
        sid = await self.manager.connect(Socket(), voice=False)
        session = self.manager.sessions[sid]
        stream = Processor()
        await stream.stop()
        stream.stop_count = 0

        async def waiting_for_initialization():
            async with session.初期化ロック:
                self.fail('停止対象タスクが初期化ロックを取得しました')

        async with session.初期化ロック:
            stream.task = asyncio.create_task(waiting_for_initialization())
            stream.worker_task = stream.task
            session.streaming_processor = stream
            await asyncio.sleep(0)
            await asyncio.wait_for(session._stop_runtime_processors_locked(), 2)
        self.assertTrue(stream.task.cancelled())
        self.assertIsNone(session.streaming_processor)

    async def test_public_close_and_stop_share_initialization_lock(self):
        sid = await self.manager.connect(Socket(), voice=False)
        session = self.manager.sessions[sid]
        session.chat_processor = types.SimpleNamespace(終了=AsyncMock())
        async with session.初期化ロック:
            stopped = asyncio.create_task(session.stop_runtime_processors())
            closed = asyncio.create_task(session.close())
            await asyncio.sleep(0)
            self.assertFalse(stopped.done())
            self.assertFalse(closed.done())
            session.chat_processor.終了.assert_not_awaited()
        await asyncio.wait_for(asyncio.gather(stopped, closed), 2)
        self.assertFalse(session.is_connected)
        self.assertIsNone(session.audio_data)


if __name__ == '__main__':
    unittest.main()

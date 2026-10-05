# -*- coding: utf-8 -*-
"""音声接続のプロジェクト確定を、実際のセッション管理で検証する。"""
import importlib.util
import ast
import logging
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
from starlette.websockets import WebSocketState

BACKEND = Path(__file__).resolve().parents[1]


def load(filename, stubs):
    spec = importlib.util.spec_from_file_location('project_test_' + filename, BACKEND / 'AIコア' / filename)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, stubs):
        spec.loader.exec_module(module)
    return module


class Socket:
    application_state = WebSocketState.CONNECTED

    def __init__(self):
        self.messages = []
        self.closed = False

    async def accept(self):
        pass

    async def send_json(self, data):
        self.messages.append(data)

    async def close(self, **kwargs):
        self.closed = True


class ProjectConnectionTest(unittest.IsolatedAsyncioTestCase):
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
        self.folder = tempfile.TemporaryDirectory(prefix='別プロジェクト_')
        self.addCleanup(self.folder.cleanup)
        self.conf = types.SimpleNamespace(json={'CODE_BASE_PATH': '../', 'LIVE_AI_NAME': 'gemini_live'})

    async def test_folder_is_bound_before_init_and_audio_reuses_it(self):
        core = Socket()
        sid = await self.manager.connect(core, socket_no='core', app_conf=self.conf, code_base_path=self.folder.name)
        settings = core.messages[0]['メッセージ内容']['モデル設定']
        self.assertEqual(settings['CODE_BASE_PATH'], self.folder.name)
        self.assertEqual(settings['LIVE_AI_NAME'], 'gemini_live')
        audio = Socket()
        await self.manager.connect(audio, セッションID=sid, socket_no='audio', code_base_path=self.folder.name + '/')
        self.assertEqual(audio.messages[0]['セッションID'], sid)
        self.assertEqual(self.manager.session_states[sid]['モデル設定']['CODE_BASE_PATH'], self.folder.name)
        self.assertEqual(self.conf.json['CODE_BASE_PATH'], '../')

    async def test_mismatch_does_not_replace_current_audio(self):
        original = Socket()
        sid = await self.manager.connect(original, socket_no='audio', app_conf=self.conf, code_base_path=self.folder.name)
        with self.assertRaisesRegex(ValueError, '一致しません'):
            await self.manager.connect(Socket(), セッションID=sid, socket_no='audio', code_base_path=str(BACKEND))
        self.assertFalse(original.closed)
        self.assertIs(self.manager.sessions[sid].get_socket('audio').websocket, original)
        self.assertEqual(self.manager.sessions[sid].モデル設定['CODE_BASE_PATH'], self.folder.name)

    async def test_invalid_folder_creates_no_session(self):
        for path in [str(Path(self.folder.name) / 'missing'), '', 12, '\x00']:
            with self.assertRaises(ValueError):
                await self.manager.connect(Socket(), code_base_path=path)
        self.assertEqual(self.manager.sessions, {})
        self.assertEqual(self.manager.session_states, {})

    async def test_legacy_and_relative_config_accept_matching_absolute_folder(self):
        sid = await self.manager.connect(Socket(), app_conf=self.conf)
        self.assertEqual(self.manager.sessions[sid].モデル設定['CODE_BASE_PATH'], '../')
        audio = Socket()
        await self.manager.connect(audio, セッションID=sid, socket_no='audio', code_base_path=str(BACKEND.parent))
        self.assertEqual(audio.messages[0]['セッションID'], sid)

    async def test_selected_model_and_voice_are_bound_before_initialization(self):
        selection = {'LIVE_AI_NAME': 'openai_live', 'LIVE_OPENAI_MODEL': 'test-realtime', 'LIVE_OPENAI_VOICE': 'marin'}
        core = Socket()
        sid = await self.manager.connect(core, socket_no='core', app_conf=self.conf,
            code_base_path=self.folder.name, live_model_settings=selection)
        settings = core.messages[0]['メッセージ内容']['モデル設定']
        for key, value in selection.items():
            self.assertEqual(settings[key], value)
        self.assertEqual(settings['CODE_BASE_PATH'], self.folder.name)
        await self.manager.connect(Socket(), セッションID=sid, socket_no='audio', live_model_settings=selection)
        self.assertEqual(self.conf.json['LIVE_AI_NAME'], 'gemini_live')

    async def test_unspecified_values_keep_defaults_and_mismatch_requires_new_session(self):
        socket = Socket()
        sid = await self.manager.connect(socket, socket_no='audio', app_conf=self.conf, live_model_settings={'LIVE_AI_NAME': ''})
        self.assertEqual(self.manager.sessions[sid].モデル設定['LIVE_AI_NAME'], 'gemini_live')
        with self.assertRaisesRegex(ValueError, 'ライブモデルが一致しません'):
            await self.manager.connect(Socket(), セッションID=sid, socket_no='audio', live_model_settings={'LIVE_AI_NAME': 'freeai_live'})
        self.assertFalse(socket.closed)
        fresh = await self.manager.connect(Socket(), app_conf=self.conf, live_model_settings={'LIVE_AI_NAME': 'freeai_live'})
        self.assertNotEqual(fresh, sid)
        self.assertEqual(self.manager.sessions[fresh].モデル設定['LIVE_AI_NAME'], 'freeai_live')

    async def test_invalid_model_does_not_create_or_replace_session(self):
        for selection in ['gemini_live', {'CHAT_AI_NAME': 'freeai_chat'}, {'LIVE_AI_NAME': 1}, {'LIVE_AI_NAME': 'invalid'}]:
            with self.assertRaises(ValueError):
                await self.manager.connect(Socket(), app_conf=self.conf, live_model_settings=selection)
        self.assertEqual(self.manager.sessions, {})

    async def test_catalog_before_connect_uses_defaults_without_creating_session(self):
        # DB/起動処理を実行せず、実際のルーター関数とリクエスト型を検証する。
        from pydantic import BaseModel
        tree = ast.parse((BACKEND / 'core_router' / 'AIコア.py').read_text(encoding='utf-8'))
        nodes = [node for node in tree.body if getattr(node, 'name', '') in {'モデル情報取得リクエスト', 'モデル情報取得'}]
        for node in nodes:
            if isinstance(node, ast.AsyncFunctionDef):
                node.decorator_list = []
        namespace = {
            'BaseModel': BaseModel, 'Request': object, 'AIセッション管理': self.manager,
            '初期モデル設定生成': self.module.初期モデル設定生成, 'logger': logging.getLogger(__name__),
            '_backend_local稼働中': lambda conf: True, '取得_コードベース選択肢': lambda conf: {},
        }
        exec(compile(ast.Module(body=nodes, type_ignores=[]), 'AIコア.py', 'exec'), namespace)
        self.conf.models = types.SimpleNamespace(get_chat_models=lambda: {}, get_live_models=lambda: {'gemini_live': {'model': 'model'}}, get_live_voices=lambda: {}, get_code_models=lambda: {})
        http = types.SimpleNamespace(app=types.SimpleNamespace(conf=self.conf))
        result = await namespace['モデル情報取得'](http, namespace['モデル情報取得リクエスト']())
        self.assertEqual(result['status'], 'OK')
        self.assertEqual(result['data']['モデル設定']['LIVE_AI_NAME'], 'gemini_live')
        self.assertEqual(result['data']['available_models']['live_models']['gemini_live'], {'model': 'model'})
        self.assertEqual(self.manager.sessions, {})
        invalid = await namespace['モデル情報取得'](http, namespace['モデル情報取得リクエスト'](セッションID='missing'))
        self.assertEqual(invalid['status'], 'NG')

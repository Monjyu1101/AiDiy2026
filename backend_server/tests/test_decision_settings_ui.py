"""設定画面の取得・保存・再読込から判断モデル解決までを隔離環境で検証。"""
import ast
import asyncio
from datetime import datetime
import json
import logging
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from typing import Optional
import unittest
from unittest.mock import AsyncMock, Mock, patch

import httpx
from fastapi import FastAPI, Request
from pydantic import BaseModel

from test_conf_json_ports import _load_conf_json_module

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from AIコア.AI判断 import Decision, PROVIDERS
from conf.conf_model import conf_models


def extract(path, names, namespace):
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    nodes = [node for node in tree.body if getattr(node, "name", "") in names]
    for node in nodes:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            node.decorator_list = []
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)


class DecisionSettingsTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.path = self.root / 'AiDiy_key.json'
        self.conf = _load_conf_json_module().conf_json(json=str(self.path))
        self.session = SimpleNamespace(モデル設定={"CHAT_AI_NAME": "keep-chat", "LIVE_AI_NAME": "keep-live"}, voice_enabled=False)
        self.session.update_model_settings = Mock(side_effect=lambda settings, **kwargs: self.session.モデル設定.update(settings))
        self.session.初期化ロック = asyncio.Lock()
        self.scope = {
            'Request': Request, 'BaseModel': BaseModel, 'Optional': Optional,
            'logger': logging.getLogger(__name__), 'datetime': datetime, 'os': os,
            'AIセッション管理': SimpleNamespace(get_session=lambda sid: self.session),
            'モデル設定正規化': lambda values: values,
            '取得_コードベース選択肢': lambda conf: {}, '_backend_local稼働中': lambda conf: False,
            'コードベース絶対パス取得': Mock(return_value=str(self.root)),
            'バックアップ実行_共通ログ': Mock(return_value=None),
            'バックエンドディレクトリ': str(self.root / 'backend_server'),
            'プロジェクトルート': str(self.root),
        }
        extract(BACKEND / 'AIコア/AIセッション管理.py', {'初期モデル設定生成'}, self.scope)
        extract(BACKEND / 'core_router/AIコア.py', {'モデル情報取得', 'モデル情報設定', 'モデル情報取得リクエスト', 'モデル設定リクエスト'}, self.scope)
        self.http = SimpleNamespace(app=SimpleNamespace(conf=SimpleNamespace(json=self.conf, models=None)))

    async def read(self, sid='test'):
        result = await self.scope['モデル情報取得'](self.http, self.scope['モデル情報取得リクエスト'](セッションID=sid))
        self.assertEqual(result['status'], 'OK', result)
        return result['data']

    async def save(self, settings, **options):
        return await self.scope['モデル情報設定'](self.http, self.scope['モデル設定リクエスト'](セッションID='test', モデル設定=settings, save=True, **options))

    async def test_missing_old_keys_and_no_session_default_to_auto(self):
        self.http.app.conf.json = {}
        for sid in ('test', ''):
            data = await self.read(sid)
            self.assertEqual(data['モデル設定']['DECISION_AI_NAME'], 'auto')
            self.assertNotIn('DECISION_AI_MODEL', data['モデル設定'])
            for key in ('DECISION_OPENAI_MODEL','DECISION_OAUTH_MODEL','DECISION_GEMINI_MODEL','DECISION_FREEAI_MODEL'):
                self.assertEqual(data['モデル設定'][key], 'auto')
            self.assertIn('auto', data['available_models']['decision_models'])

    async def test_save_reload_and_decision_execution(self):
        before = self.conf.to_dict() if hasattr(self.conf, 'to_dict') else json.loads(self.path.read_text(encoding='utf-8'))
        settings = {'DECISION_AI_NAME': 'openai_decisions', 'DECISION_OPENAI_MODEL': 'saved-model'}
        self.assertEqual((await self.save(settings))['status'], 'OK')
        data = await self.read()
        for key, value in settings.items():
            self.assertEqual(data['モデル設定'][key], value)
        # 保存だけでは稼働中セッションのChat/Liveを変更しない。
        self.assertEqual(self.session.モデル設定, {'CHAT_AI_NAME': 'keep-chat', 'LIVE_AI_NAME': 'keep-live'})
        saved = json.loads(self.path.read_text(encoding='utf-8'))
        self.assertEqual({k: v for k, v in saved.items() if k not in settings}, {k: v for k, v in before.items() if k not in settings})
        fresh = _load_conf_json_module().conf_json(json=str(self.path))
        self.assertEqual(self.scope['初期モデル設定生成'](SimpleNamespace(json=fresh))['DECISION_OPENAI_MODEL'], 'saved-model')
        seen = []
        def handler(req):
            seen.append(json.loads(req.content)['model'])
            return httpx.Response(200, json={'answers': [{'type': 'predicate', 'name': 'ok', 'probability': 1}]})
        self.conf.update({'openai_key_id': 'test'})
        service = Decision(config_path=self.path, transport=httpx.MockTransport(handler))
        result = await service.実行({'input': 'test', 'questions': [{'type': 'predicate', 'name': 'ok', 'instructions': 'test'}]})
        self.assertEqual(result['data']['ai_model'], 'saved-model')
        self.assertEqual(seen, ['saved-model'])
        self.assertFalse(list(self.root.rglob('reboot*.txt')))

    async def test_json_api_round_trip_whitelist_and_restart_reload(self):
        app=FastAPI()
        app.conf=self.http.app.conf
        # 実ソースのエンドポイントをASGIへ登録し、シリアライズを含めて検証。
        app.post('/core/AIコア/モデル情報/取得')(self.scope['モデル情報取得'])
        app.post('/core/AIコア/モデル情報/設定')(self.scope['モデル情報設定'])
        settings={provider.model_key:name+'-saved' for name,provider in PROVIDERS.items()}
        settings['DECISION_AI_NAME']='openai_oauth'
        self.conf.update({'openai_key_id':'fixture-secret','CUSTOM_KEEP':'retained'})
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
            result=await client.post('/core/AIコア/モデル情報/設定',json={
                'セッションID':'test','モデル設定':{**settings,'openai_key_id':'rejected','CUSTOM_KEEP':'rejected'},
                'save':True,'再起動要求':{'reboot_tools':True}})
            self.assertEqual(result.status_code,200)
            self.assertEqual(result.json()['status'],'OK',result.text)
            self.assertTrue((self.root/'backend_tools/temp/reboot_tools.txt').is_file())
            app.conf.json=_load_conf_json_module().conf_json(json=str(self.path))
            response=await client.post('/core/AIコア/モデル情報/取得',json={'セッションID':'test'})
            self.assertEqual(response.status_code,200)
            data=response.json()['data']['モデル設定']
            initial=self.scope['初期モデル設定生成'](app.conf)
            for key,value in settings.items():
                self.assertEqual(data[key],value)
                self.assertEqual(initial[key],value)
            self.assertNotIn('DECISION_AI_MODEL',data)
        saved=json.loads(self.path.read_text(encoding='utf-8'))
        self.assertEqual(saved['openai_key_id'],'fixture-secret')
        self.assertEqual(saved['CUSTOM_KEEP'],'retained')
        self.assertEqual(Decision(config_path=self.path).get_config()['default_model'],'openai_oauth/openai_oauth-saved')

    async def test_save_and_restart_request_and_reset_use_isolated_flags(self):
        result = await self.save({'DECISION_AI_NAME': 'openai_oauth', 'DECISION_OAUTH_MODEL': 'custom'}, 再起動要求={'reboot_tools': True})
        self.assertEqual(result['status'], 'OK')
        self.assertTrue((self.root / 'backend_tools/temp/reboot_tools.txt').is_file())
        self.assertEqual(json.loads(self.path.read_text(encoding='utf-8'))['DECISION_OAUTH_MODEL'], 'custom')
        result = await self.save({}, リセット=True)
        self.assertEqual(result['status'], 'OK')
        self.assertEqual((await self.read())['モデル設定']['DECISION_AI_NAME'], 'auto')
        self.assertEqual((await self.read())['モデル設定']['DECISION_OAUTH_MODEL'], 'auto')

    def test_model_candidates_use_diag_values_without_runtime_fixed_filter(self):
        candidates = Decision.model_options({
            'openai_decisions': {'gpt-6-luna': 'API'}, 'openai_oauth': {'gpt-6-luna': 'OAuth'},
            'freeai_chat': {'wrong': 'Wrong', 'gemini-flash-lite-latest': 'Latest'},
            'gemini_chat': {'gemini-test': 'Gemini'}, 'unknown': {'injected': 'Unknown'},
        })
        self.assertEqual(list(candidates), ['auto', 'openai_oauth', 'freeai_chat', 'openai_decisions', 'gemini_chat'])
        self.assertEqual(candidates['openai_decisions'], {'auto': 'auto（方式別の既定モデル）', 'gpt-6-luna': 'API'})
        self.assertEqual(set(candidates['freeai_chat']), {'auto', 'wrong', 'gemini-flash-lite-latest'})
        self.assertNotIn('injected', candidates['auto'])
        self.assertIn('wrong', candidates['auto'])
        self.assertTrue(all(set(models) == {'auto'} for models in Decision.model_options().values()))

    async def test_api_reads_live_diag_file_and_keeps_saved_values_when_empty_or_invalid(self):
        config = self.root / '_config'
        config.mkdir()
        output = self.root / '_AIDIY/aidiy_diag'
        output.mkdir(parents=True)
        catalog = output / 'decisions_models_info.json'
        self.conf.update({'DECISION_AI_NAME': 'gemini_chat', 'DECISION_GEMINI_MODEL': 'saved-outside-list'})
        with patch.object(conf_models, '_config_dir_path', return_value=str(config)):
            self.http.app.conf.models = conf_models()
            self.scope['_backend_local稼働中'] = lambda conf: True
            catalog.write_text(json.dumps({'gemini_chat': {'models': {'gemini-flash-lite-latest': '2026/10/18 - gemini-flash-lite-latest'}}}), encoding='utf-8')
            data = await self.read()
            self.assertEqual(data['available_models']['decision_models']['gemini_chat']['gemini-flash-lite-latest'], '2026/10/18 - gemini-flash-lite-latest')
            self.assertNotIn('saved-outside-list', data['available_models']['decision_models']['gemini_chat'])
            for text in ('{}', 'broken', '{"gemini_chat":{"models":[]}}'):
                catalog.write_text(text, encoding='utf-8')
                data = await self.read()
                self.assertEqual(set(data['available_models']['decision_models']['gemini_chat']), {'auto'})
                self.assertEqual(data['モデル設定']['DECISION_GEMINI_MODEL'], 'saved-outside-list')
            catalog.unlink()
            self.assertEqual((await self.read())['モデル設定']['DECISION_AI_NAME'], 'gemini_chat')

    async def test_all_providers_and_legacy_values_save_without_changing_other_settings(self):
        self.conf.update({'CUSTOM_KEEP': 'retained', 'DECISION_FREEAI_MODEL': 'old-version'})
        for provider in ('auto', 'openai_oauth', 'freeai_chat', 'openai_decisions', 'gemini_chat', 'openai_jsonchat', 'future-provider'):
            before = json.loads(self.path.read_text(encoding='utf-8'))
            settings = {'DECISION_AI_NAME': provider, 'DECISION_AI_MODEL': 'retained-common'}
            self.assertEqual((await self.save(settings))['status'], 'OK')
            data = await self.read()
            self.assertEqual({key: data['モデル設定'][key] for key in settings}, settings)
            after = json.loads(self.path.read_text(encoding='utf-8'))
            self.assertEqual({k:v for k,v in before.items() if k not in settings}, {k:v for k,v in after.items() if k not in settings})
        self.assertFalse(list(self.root.rglob('reboot*.txt')))

    async def test_legacy_file_migrates_without_overwriting_provider_auto_and_api_changes_survive_reload(self):
        original={'DECISION_AI_NAME':'freeai_chat','DECISION_AI_MODEL':'old-common',
                  'DECISION_OPENAI_MODEL':'auto','CUSTOM_KEEP':'keep','openai_key_id':'fixture-secret'}
        self.path.write_text(json.dumps(original),encoding='utf-8')
        self.conf=_load_conf_json_module().conf_json(json=str(self.path))
        self.http.app.conf.json=self.conf
        data=(await self.read())['モデル設定']
        self.assertEqual(data['DECISION_FREEAI_MODEL'],'old-common')
        self.assertEqual(data['DECISION_OPENAI_MODEL'],'auto')
        self.assertEqual(Decision(config_path=self.path).get_config()['default_model'],'freeai_chat/old-common')
        settings={'DECISION_OPENAI_MODEL':'api-model','DECISION_OAUTH_MODEL':'oauth-model',
                  'DECISION_GEMINI_MODEL':'gemini-model','DECISION_FREEAI_MODEL':'free-model'}
        self.assertEqual((await self.save({**settings,'openai_key_id':'must-not-save'}))['status'],'OK')
        fresh=_load_conf_json_module().conf_json(json=str(self.path))
        self.http.app.conf.json=fresh
        data=(await self.read())['モデル設定']
        session=self.scope['初期モデル設定生成'](SimpleNamespace(json=fresh))
        for key,value in settings.items():
            self.assertEqual(data[key],value)
            self.assertEqual(session[key],value)
        saved=json.loads(self.path.read_text(encoding='utf-8'))
        for key in ('CUSTOM_KEEP','openai_key_id','DECISION_AI_MODEL'):
            self.assertEqual(saved[key],original[key])
        self.assertEqual(Decision(config_path=self.path).get_config()['default_model'],'freeai_chat/free-model')

    async def test_changed_diag_model_can_be_saved_reloaded_and_sent_for_all_providers(self):
        from test_decisions import sse
        config=self.root/'_config';config.mkdir()
        output=self.root/'_AIDIY/aidiy_diag';output.mkdir(parents=True)
        self.conf.update({'openai_key_id':'fixture','freeai_key_id':'fixture','gemini_key_id':'fixture'})
        seen=[]
        def handler(req):
            seen.append(req)
            if req.url.host=='generativelanguage.googleapis.com':
                self.assertEqual(req.url.path,'/v1beta/models/new-from-diag:generateContent')
                return httpx.Response(200,json={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'{"answers":[{"type":"predicate","name":"ok","probability":1}]}'}]}}]})
            self.assertEqual(json.loads(req.content)['model'],'new-from-diag')
            answers=[{'type':'predicate','name':'ok','probability':1}]
            return sse(answers=answers) if req.url.host=='chatgpt.com' else httpx.Response(200,json={'answers':answers})
        with patch.object(conf_models,'_config_dir_path',return_value=str(config)), patch('AIコア.AI判断_openai_jsonchat.oauth_headers',return_value={'Authorization':'Bearer fixture'}):
            self.http.app.conf.models=conf_models()
            self.scope['_backend_local稼働中']=lambda conf: True
            for name in ('openai_oauth','freeai_chat','openai_decisions','gemini_chat'):
                (output/'decisions_models_info.json').write_text(json.dumps({name:{'models':{'new-from-diag':'Retrieved'}}}),encoding='utf-8')
                self.assertIn('new-from-diag',(await self.read())['available_models']['decision_models'][name])
                self.assertEqual((await self.save({'DECISION_AI_NAME':name,PROVIDERS[name].model_key:'new-from-diag'}))['status'],'OK')
                self.assertEqual((await self.read())['モデル設定'][PROVIDERS[name].model_key],'new-from-diag')
                result=await Decision(config_path=self.path,transport=httpx.MockTransport(handler)).実行({'input':'test','questions':[{'type':'predicate','name':'ok','instructions':'test'}]})
                self.assertEqual(result['data']['model'],name+'/new-from-diag')
        self.assertEqual(len(seen),4)
        self.assertFalse(list(self.root.rglob('reboot*.txt')))


if __name__ == '__main__':
    unittest.main()

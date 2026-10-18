"""判断モデルの選択順・直接呼出し・Diag候補変更を実通信なしで検証する。"""
import copy
import importlib
import json
import unittest
from unittest.mock import patch

import httpx
from test_decisions import Decision, request, sse, ANSWERS
from test_decision_gemini import envelope
from AIコア.AI判断 import PROVIDERS

DEFAULTS = {'openai_oauth':'gpt-6-luna', 'freeai_chat':'gemini-flash-lite-latest',
            'openai_decisions':'gpt-6-luna', 'gemini_chat':'gemini-flash-lite-latest'}


class DecisionModelSelection(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.config={'openai_key_id':'fixture','freeai_key_id':'fixture','gemini_key_id':'fixture',
                     'DECISION_AI_MODEL':'common-model','CHAT_OPENAI_MODEL':'keep-chat',
                     **{p.model_key:'provider-model' for p in PROVIDERS.values()}}
        self.calls=[]
        self.expected='selected'

    def handler(self,req):
        self.calls.append(req)
        if req.url.host=='generativelanguage.googleapis.com':
            self.assertEqual(req.url.path,'/v1beta/models/'+self.expected+':generateContent')
            return httpx.Response(200,json=envelope())
        self.assertEqual(json.loads(req.content)['model'],self.expected)
        return sse() if req.url.host=='chatgpt.com' else httpx.Response(200,json={'answers':ANSWERS})

    async def test_direct_adapters_use_supplied_model(self):
        before=copy.deepcopy(self.config)
        with patch('AIコア.AI判断_openai_jsonchat.oauth_headers',return_value={'Authorization':'Bearer fixture'}):
            async with httpx.AsyncClient(transport=httpx.MockTransport(self.handler)) as client:
                for name in DEFAULTS:
                    adapter=importlib.import_module(PROVIDERS[name].module).DecisionAI()
                    await adapter.実行(request(ai_name=name),'selected',self.config,client)
        self.assertEqual(len(self.calls),4)
        self.assertEqual(self.config,before)

    async def test_explicit_provider_legacy_and_low_cost_default_precedence(self):
        before=copy.deepcopy(self.config)
        with patch('AIコア.AI判断_openai_jsonchat.oauth_headers',return_value={'Authorization':'Bearer fixture'}):
            for name,default in DEFAULTS.items():
                for params,config,expected in (
                    ({'ai_name':name,'model':'selected'},self.config,'selected'),
                    ({'ai_name':name,'ai_model':'selected'},self.config,'selected'),
                    ({'model':name+'/selected'},self.config,'selected'),
                    ({'ai_name':name},self.config,'provider-model'),
                    ({'ai_name':name},{k:v for k,v in self.config.items() if k != PROVIDERS[name].model_key},'common-model'),
                    ({'ai_name':name},{**self.config,'DECISION_AI_MODEL':'auto'},'provider-model'),
                    ({'ai_name':name},{**self.config,'DECISION_AI_MODEL':'old-ignored',PROVIDERS[name].model_key:'auto'},default),
                ):
                    self.expected=expected
                    service=Decision(config=config,transport=httpx.MockTransport(self.handler))
                    result=await service.実行(request(**params))
                    self.assertEqual(result['data']['model'],name+'/'+expected)
        self.assertEqual(len(self.calls),28)
        self.assertEqual(self.config,before)

    def test_auto_order_and_legacy_alias_keep_explicit_model(self):
        service=Decision(config=self.config)
        for index,name in enumerate(DEFAULTS):
            service.availability={key:{'ok':True} for key in list(DEFAULTS)[index:]}
            self.assertEqual(service.resolve(request(),self.config),(name,'provider-model'))
        self.assertEqual(service.resolve(request(model='openai_jsonchat/selected'),self.config),('openai_oauth','selected'))

    def test_api_accepts_updated_diag_candidates_without_hardcoded_model_filter(self):
        self.assertTrue(all(list(models)==['auto'] for models in Decision.model_options().values()))
        options=Decision.model_options({name:{'new-from-diag':'retrieved'} for name in DEFAULTS})
        for name in DEFAULTS:
            self.assertEqual(set(options[name]),{'auto','new-from-diag'})

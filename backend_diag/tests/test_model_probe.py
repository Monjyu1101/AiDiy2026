import datetime as dt
import importlib.util
import json
import io
from unittest.mock import patch
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace as Obj
import unittest

BASE = Path(__file__).resolve().parents[1]
def load(name):
    spec = importlib.util.spec_from_file_location(name, BASE / 'tests' / 'reference' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

catalog = load('model_catalog_copy')
bridge = load('model_probe')
NOW = dt.datetime(2026, 10, 15, 12)
def ago(days): return (NOW - dt.timedelta(days=days)).timestamp()
def reader(value): return lambda path: json.dumps(value)
def row(ident, days, count=42):
    return dict(id=ident, created=ago(days), context_length=count, architecture={'modality':'text->text'})

class CatalogParityTests(unittest.TestCase):
    def test_openrouter_each_cutoff_inclusive_and_missing_date(self):
        entries=[]
        for provider,limit in [('perplexity',365),('google',240),('openai',240),('anthropic',240),('x-ai',240),('other',90)]:
            entries.extend([row(provider+'/keep',limit),row(provider+'/drop',limit+1)])
        entries.append({'id':'google/no-date'})
        out=catalog.openrouter_catalog({'data':entries},now=NOW)
        self.assertEqual(len(out),6)
        self.assertTrue(all(name.endswith('/keep') for name in out))
        self.assertEqual(out['google/keep']['トークン数'],'42')
        self.assertEqual(out['google/keep']['モダリティ'],'text->text')
        self.assertEqual(out['google/keep']['作成日'],dt.datetime.fromtimestamp(ago(240)).strftime('%Y/%m/%d'))

    def test_google_supported_action_join_date_and_live_exception(self):
        items=[Obj(name='models/'+name,supported_actions=actions,input_token_limit=123)
               for name,actions in [('match',['generateContent']),('missing',['generateContent']),('live-missing',['generateContent']),('embed',['embedContent'])]]
        router={'google/match':{'作成日':'2026/10/01'}}
        out=catalog.google_catalog(items,router)
        self.assertEqual(set(out),{'match','live-missing'})
        self.assertEqual(out['match']['作成日'],'2026/10/01')
        self.assertIsNone(out['live-missing']['作成日'])
        self.assertEqual(set(catalog.google_catalog(items,{})),{'match','missing','live-missing'})

    def test_openai_date_always_applies_and_zero_token_filter(self):
        items=[Obj(id=name,created=ago(age)) for name,age in [('match',240),('old',241),('missing',1),('realtime-missing',1)]]
        out=catalog.openai_catalog(items,{},now=NOW)
        self.assertEqual(set(out),{'match','missing','realtime-missing'})
        out=catalog.openai_catalog(items,{'openai/match':{'トークン数':'123','モダリティ':'text'}},now=NOW)
        self.assertEqual(set(out),{'match','realtime-missing'})
        self.assertEqual(out['match']['トークン数'],'123')

    def test_claude_unknown_dates_retained_normalization_and_unmatched_kept(self):
        items=Obj(data=[Obj(id='claude-3-5-20241022',created_at=NOW),Obj(id='unknown',created_at=None),Obj(id='bad',created_at='not-a-date'),Obj(id='old',created_at=NOW-dt.timedelta(days=241))])
        out=catalog.claude_catalog(items,{'anthropic/claude-3.5':{'トークン数':'88','モダリティ':'text'}},now=NOW)
        self.assertEqual(set(out),{'claude-3-5-20241022','unknown','bad'})
        self.assertEqual(out['claude-3-5-20241022']['トークン数'],'88')
        self.assertIsNone(out['bad']['作成日'])

    def test_claude_iso_strings_z_offset_unknown_and_old(self):
        items=Obj(data=[Obj(id='new-z',created_at='2026-10-14T12:00:00Z'),
                        Obj(id='new-offset',created_at='2026-10-14T14:00:00+02:00'),
                        Obj(id='old-iso',created_at='2025-01-01T00:00:00Z'),
                        Obj(id='invalid',created_at='not-a-date')])
        out=catalog.claude_catalog(items,{},now=NOW)
        self.assertEqual(set(out),{'new-z','new-offset','invalid'})
        self.assertEqual(out['new-z']['作成日'],'2026/10/14')
        self.assertIsNone(out['invalid']['作成日'])

    def test_ollama_sort_and_known_date_required(self):
        out=catalog.ollama_catalog({'data':[row('older',240),row('newer',1),row('expired',241),{'id':'missing'}]},now=NOW)
        self.assertEqual(list(out),['newer','older'])

class BridgeTests(unittest.TestCase):
    def test_fixed_case_path_and_safe_status(self):
        def read(path):
            self.assertEqual(path.name,'AiDiy_key.json')
            self.assertEqual(path.parent.name,'_config')
            return json.dumps({'openai_key_id':'fixture-secret','gemini_key_id':' < placeholder > ','ollama_key_id':'ollama'})
        result=bridge.status(read)
        self.assertEqual(result['項目'][0]['id'],'gemini')
        self.assertNotIn('fixture-secret',json.dumps(result))
        rows={item['id']:item for item in result['項目']}
        self.assertTrue(rows['openai']['設定済み'])
        self.assertFalse(rows['gemini']['設定済み'])
        self.assertFalse(rows['ollama']['設定済み'])
        self.assertTrue(rows['openrt']['キー不要'])
        self.assertTrue(rows['openrt']['テスト可能'])

    def test_invalid_config_and_unset_no_fetch(self):
        def fail(*args): self.fail('No request permitted')
        self.assertEqual(bridge.status(lambda _: b'[]')['設定状態'],'読込不可')
        result=bridge.probe('gemini',reader({'freeai_key_id':'fixture-key'}),fail)
        self.assertEqual(result['状態'],'未実施')
        result=bridge.probe('azure',reader({'azure_key_id':'fixture-key'}),fail)
        self.assertEqual(result['状態'],'未実施')

    def test_public_anonymous_no_config_read_and_filter_applied(self):
        def fetch(provider,headers):
            self.assertEqual(provider,'openrouter')
            self.assertEqual(headers,{})
            return {'data':[row('other/new',1),row('other/old',91)]}
        with patch.object(bridge,'read_config',side_effect=AssertionError('config forbidden')):
            result=bridge.public_catalog(fetch,catalog,NOW)
        self.assertEqual(result['状態'],'OK')
        self.assertEqual(list(result['公開モデル']),['other/new'])
        self.assertIn('キーの有効性',result['説明'])
        def fail(*args): raise ValueError('untrusted body')
        with patch.object(bridge,'read_config',side_effect=AssertionError('config forbidden')):
            failed=bridge.public_catalog(fail,catalog,NOW)
        self.assertEqual(failed['状態'],'NG')
        self.assertEqual(failed['公開モデル'],{})
        self.assertNotIn('untrusted body',json.dumps(failed))

    def test_openrouter_reuses_cache_without_config_or_network(self):
        def fail(*args): self.fail('No config or network')
        cache={'公開状態':'取得済','公開モデル':catalog.openrouter_catalog({'data':[row('other/new',1)]},now=NOW)}
        result=bridge.probe('openrt',fail,fail,catalog,NOW,cache=cache)
        self.assertEqual(result['状態'],'OK')
        self.assertEqual(result['モデル'],['other/new'])
        for state in ['未取得','取得中','失敗']:
            result=bridge.probe('openrt',fail,fail,catalog,NOW,cache={'公開状態':state,'公開モデル':cache['公開モデル']})
            self.assertEqual(result['状態'],'未実施')

    def test_router_prerequisite_joins_selected_key_only(self):
        calls=[]
        def fetch(provider,headers):
            calls.append((provider,headers))
            if provider=='openrouter': return {'data':[row('google/match',20)]}
            return {'models':[{'name':'models/match','supportedGenerationMethods':['generateContent'],'inputTokenLimit':222},{'name':'models/missing','supportedGenerationMethods':['generateContent']}]}
        result=bridge.probe('freeai',reader({'gemini_key_id':'other-secret','freeai_key_id':'selected-secret'}),fetch,catalog,NOW,cache={'公開状態':'取得済','公開モデル':catalog.openrouter_catalog({'data':[row('google/match',20)]},now=NOW)})
        self.assertEqual(result['状態'],'OK')
        self.assertEqual(result['モデル'],['match'])
        self.assertEqual(calls,[('google',{'x-goog-api-key':'selected-secret'})])
        self.assertTrue(result['モデル詳細'][0]['作成日'])

    def test_router_failure_warns_preserves_empty_cache_path_selected_failure_ng(self):
        def fetch(provider,headers):
            if provider=='openrouter': raise ValueError('secret-error')
            return {'data':[{'id':'fresh','created':ago(2)}]}
        result=bridge.probe('openai',reader({'openai_key_id':'fixture-secret'}),fetch,catalog,NOW)
        self.assertEqual(result['状態'],'OK')
        self.assertEqual(result['モデル'],['fresh'])
        self.assertTrue(result['警告'])
        self.assertNotIn('secret-error',json.dumps(result))
        def fail(*args): raise ValueError('secret-error')
        result=bridge.probe('openai',reader({'openai_key_id':'fixture-secret'}),fail,catalog,NOW)
        self.assertEqual(result['状態'],'NG')
        self.assertEqual(result['モデル'],[])

    def test_isolated_stdlib_only_real_wire_iso_filter(self):
        # CLI status は実configを読むため呼ばず、注入fixtureのみでbridgeを実行する。
        code = """import importlib.util,json,datetime
spec=importlib.util.spec_from_file_location('bridge',%r)
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
def fetch(provider,headers):
    if provider=='openrouter': return {'data':[]}
    return {'data':[{'id':'old','created_at':'2025-01-01T00:00:00Z'},{'id':'new','created_at':'2026-10-14T12:00:00Z'}]}
r=b.probe('claude',reader=lambda _:json.dumps({'claude_key_id':'fixture-key'}),fetch=fetch,now=datetime.datetime(2026,10,15,12))
assert r['状態']=='OK',r
assert r['モデル']==['new'],r
print('PASS')
""" % str(BASE / 'tests' / 'reference' / 'model_probe.py')
        result=subprocess.run([sys.executable,'-I','-S','-B','-c',code],capture_output=True,text=True,timeout=5)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout.strip(),'PASS')

    def test_all_registered_secrets_removed_from_model_details(self):
        secrets=['selected-secret','other-secret']
        models={
            'selected-secret':{'モダリティ':'safe'},
            'other-secret':{'モダリティ':'safe'},
            'safe-model':{'作成日':'other-secret','トークン数':'selected-secret','モダリティ':'prefix-other-secret'},
        }
        out=bridge.safe_details(models,secrets)
        self.assertEqual(out,[{'model_id':'safe-model','作成日':None,'トークン数':None,'モダリティ':None}])
        self.assertTrue(all(secret not in json.dumps(out) for secret in secrets))

    def test_openai_organization_header_only_and_redaction(self):
        calls=[]
        def fetch(provider,headers):
            calls.append((provider,headers))
            if provider=='openrouter': return {'data':[]}
            return {'data':[{'id':'model-safe','created':ago(1)},{'id':'fixture-org','created':ago(1)}]}
        result=bridge.probe('openai',reader({'openai_key_id':'fixture-key','openai_organization':'fixture-org'}),fetch,catalog,NOW)
        self.assertEqual(len(calls),1)
        self.assertEqual(calls[0][0],'openai')
        self.assertEqual(calls[0][1]['OpenAI-Organization'],'fixture-org')
        self.assertEqual(result['モデル'],['model-safe'])
        self.assertNotIn('fixture-org',json.dumps(result))
        calls.clear()
        bridge.probe('openai',reader({'openai_key_id':'fixture-key','openai_organization':' < your organization > '}),fetch,catalog,NOW)
        self.assertNotIn('OpenAI-Organization',calls[0][1])

    def test_stdin_cache_bounded_and_schema_order(self):
        self.assertEqual(bridge.read_cache(io.BytesIO(b'not-json')),{})
        self.assertEqual(bridge.read_cache(io.BytesIO(b'x'*(bridge.RESPONSE_LIMIT+1))),{})
        cache={'公開状態':'取得済','公開モデル':{}}
        self.assertEqual(bridge.read_cache(io.BytesIO(json.dumps(cache).encode())),cache)
        self.assertEqual([r['id'] for r in bridge.status(reader({}))['項目']],['gemini','freeai','claude','openai','azure','copilot','openrt','ollama','huggingface_read','huggingface_write','discord'])

    def test_google_pagination_before_filter(self):
        def fetch(provider,headers,token=None):
            if provider=='openrouter': return {'data':[]}
            return {'models':[{'name':'models/'+('first' if token is None else 'second'),'supportedGenerationMethods':['generateContent']}],**({'nextPageToken':'token'} if token is None else {})}
        result=bridge.probe('gemini',reader({'gemini_key_id':'fixture-secret'}),fetch,catalog,NOW)
        self.assertEqual(result['状態'],'OK')
        self.assertEqual(result['モデル'],['first','second'])

if __name__ == '__main__': unittest.main()

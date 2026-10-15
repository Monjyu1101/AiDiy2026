"""Optional regeneration only: freeze outputs of the pre-TypeScript Python copy.
No provider requests or configuration reads. Run from any directory with Python 3.
"""
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import time
from types import SimpleNamespace as Obj

BASE = Path(__file__).resolve().parents[2]
SOURCE = BASE / 'tests/reference/model_catalog_copy.py'
if not SOURCE.exists():
    SOURCE = BASE / 'model_catalog_copy.py'
spec = importlib.util.spec_from_file_location('catalog_reference', SOURCE)
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)
results = []
for zone in ['UTC', 'Asia/Tokyo', 'America/New_York']:
    os.environ['TZ'] = zone
    time.tzset()
    now = dt.datetime(2026, 10, 15, 0, 30)
    def stamp(days=0, seconds=0):
        return (now - dt.timedelta(days=days, seconds=seconds)).timestamp()
    def add(name, kind, source, router=None):
        args = [source]
        if kind == 'google':
            args = [[Obj(**v) for v in source], router]
        elif kind == 'openai':
            args = [[Obj(**v) for v in source], router]
        elif kind == 'claude':
            args = [Obj(data=[Obj(**v) for v in source['data']]), router]
        fn = getattr(catalog, kind + '_catalog')
        expected = fn(*args, **({} if kind == 'google' else {'now': now}))
        results.append(dict(name=name, timezone=zone, now=now.isoformat(), kind=kind,
                            source=source, router=router, expected=expected,
                            order=list(expected)))
    rows = []
    for provider, days in [('perplexity',365), ('google',240), ('openai',240), ('anthropic',240), ('x-ai',240), ('other',90), ('GOOGLE',240)]:
        for suffix, seconds in [('edge',0), ('outside',1), ('inside',-1)]:
            rows.append(dict(id=provider+'/'+suffix, created=stamp(days,seconds), context_length=123, architecture={'modality':'text->text'}))
    rows += [dict(id='missing'), dict(id='other/duplicate',created=stamp(1),context_length=1),dict(id='other/duplicate',created=stamp(2),context_length=2),dict(id='other/none',created=stamp(),context_length=None),dict(id='other/bool',created=stamp(),context_length=True),dict(id='other/null-modality',created=stamp(),architecture={'modality':None})]
    add('provider cutoff inclusivity and duplicate insertion order','openrouter',{'data':rows})
    items=[dict(name='models/'+name,supported_actions=actions,**token) for name,actions,token in [
        ('match',['generateContent','countTokens'],{'input_token_limit':123}),
        ('missing',['generateContent'],{'input_token_limit':None}),
        ('LIVE-unlisted',['generateContent'],{}),
        ('embed',['embedContent'],{}),
        ('models/nested',['generateContent'],{}),
        ('match',['generateContent'],{'input_token_limit':456})]]
    add('google empty cache retains all generating models','google',items,{})
    add('google populated cache filters except live','google',items,{'google/match':{'作成日':'2026/10/01'}})
    ai=[dict(id=name,created=stamp(days,seconds)) for name,days,seconds in [('edge',240,0),('outside',240,1),('inside',240,-1),('REALTIME-old',241,0),('REALTIME-new',1,0),('zero',1,0),('numeric-zero',1,0),('duplicate',1,0),('duplicate',2,0)]]
    add('openai empty cache date cutoff','openai',ai,{})
    add('openai zero token exact type and realtime exemption','openai',ai,{f'openai/{name}':{'トークン数':tokens,'モダリティ':'text'} for name,tokens in [('edge','123'),('zero','0'),('numeric-zero',0)]})
    claude=[{'id':ident,'created_at':created} for ident,created in [
        ('claude-3-5-20241022','2026-10-15T00:30:00+09:00'),
        ('claude-4-1-20abcdef','2026-10-14T23:30:00-10:00'),
        ('unknown',None),('bad','not-a-date'),('invalid-calendar','2026-02-30T00:00:00Z'),
        ('old','2025-01-01T00:00:00Z'),('naive','2026-10-15T00:30:00'),
        ('edge', (now-dt.timedelta(days=240)).isoformat()),
        ('outside',(now-dt.timedelta(days=240,seconds=1)).isoformat())]]
    add('claude local offset unknown dates and normalization','claude',{'data':claude},{'anthropic/claude-3.5':{'トークン数':'88','モダリティ':'text'},'anthropic/claude-4.1':{'トークン数':'99','モダリティ':'text'}})
    add('ollama reverse stable order and duplicates','ollama',{'data':[{'id':'old','created':stamp(240)}, {'id':'new','created':stamp(1)}, {'id':'expired','created':stamp(240,1)}, {'id':'missing'},None,{'id':'duplicate','created':stamp(2)},{'id':'duplicate','created':stamp(3)},{'id':'equal-first','created':stamp(4)},{'id':'equal-second','created':stamp(4)}]})
Path(__file__).with_name('model-golden.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'Wrote {len(results)} offline Python-reference scenarios')

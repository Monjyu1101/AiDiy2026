"""資格情報・ネットワークを使わない Live 内部経路の契約テスト。"""
import asyncio
import ast
import types
import base64
import io
import wave
import json
import sys
import tempfile
import unittest
from pathlib import Path

import httpx
from fastapi import FastAPI

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools_proc.live_model_check import LiveModelCheck, DiagnosticOutput, register_live_model_check


class FakeLive:
    instances = []
    mode = 'ok'
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.live_session = None
        self.設定反映済み = False
        self.closed = False
        self.client = None
        self.instances.append(self)
    async def 開始(self, **kwargs):
        self.queue = kwargs['テキスト受信処理Q']
        assert kwargs['音声受信処理Q'] is self.queue
        self.live_session = object()
        self.設定反映済み = self.mode != 'not_ready'
        if self.mode == 'start_failure': return False
        if self.mode == 'exception': raise RuntimeError('secret-key-value')
        return True
    async def テキスト送信(self, text):
        assert text == 'おはよう'
        assert self.kwargs['parent_manager'] is None
        assert self.kwargs['diagnostic'] is True
        if self.mode == 'send_failure': return False
        await self.queue.put({'ready': True})
        await self.queue.put({'tool': 'ignore', 'text': 'not a reply'})
        if self.mode == 'ok':
            await self.queue.put({'text': 'おはようございます secret-key-value'})
            await self.queue.put({'diagnostic_turn_complete': True})
        return True
    async def 終了(self): self.closed = True


class LiveTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root/'_config').mkdir()
        self.config = {'LIVE_AI_NAME':'freeai_live', 'LIVE_FREEAI_MODEL':'test-live', 'LIVE_FREEAI_VOICE':'Zephyr', 'freeai_key_id':'secret-key-value'}
        self.save()
        FakeLive.mode = 'ok'
        FakeLive.instances = []
    def save(self):
        (self.root/'_config'/'AiDiy_key.json').write_text(json.dumps(self.config))
    def tearDown(self): self.temp.cleanup()
    def checker(self):
        async def sleep(delay):
            if delay != 15: await asyncio.sleep(delay)
        return LiveModelCheck(self.root, FakeLive, timeout=.04, sleep=sleep)
    async def test_real_text_only_and_cleanup(self):
        out = await self.checker().run()
        self.assertEqual(out['status'], 'OK')
        self.assertIn('[redacted]', out['reply'])
        self.assertNotIn('secret-key-value', json.dumps(out))
        self.assertTrue(FakeLive.instances[-1].closed)
    async def test_manual_override_prompt_audio_and_config_unchanged(self):
        events=[]
        class ManualLive(FakeLive):
            async def テキスト送信(inner, text):
                events.append(('prompt',text))
                await inner.queue.put({'text':'手動応答'})
                await inner.queue.put({'bytes_data':b'\x00\x00'*24000,'mime_type':'audio/pcm;rate=24000'})
                await inner.queue.put({'diagnostic_turn_complete':True})
                return True
        async def sleep(seconds): events.append(('settle',seconds))
        before=(self.root/'_config'/'AiDiy_key.json').read_bytes()
        checker=LiveModelCheck(self.root,ManualLive,timeout=.04,sleep=sleep)
        manual={'ai_name':'freeai_live','ai_model':'manual-model','voice':'Puck','prompt':'自由入力\n2行目'}
        app=FastAPI();register_live_model_check(app,checker)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app,client=('127.0.0.1',1234)),base_url='http://127.0.0.1') as client:
            response=await client.post('/internal/live_model_check',json=manual,headers={'X-AiDiy-Diag':'model-trial'})
            self.assertEqual(response.status_code,200)
            out=response.json();self.assertEqual(out['status'],'OK');self.assertEqual(out['model'],'manual-model')
            self.assertEqual(out['audio']['duration_ms'],1000)
            for invalid in [{**manual,'ai_name':[]},{**manual,'prompt':''},{**manual,'extra':'bad'}]:
                self.assertEqual((await client.post('/internal/live_model_check',json=invalid,headers={'X-AiDiy-Diag':'model-trial'})).status_code,400)
        self.assertEqual(events,[('settle',15),('prompt',manual['prompt'])])
        self.assertEqual(FakeLive.instances[-1].kwargs['live_voice'],'Puck')
        self.assertTrue(FakeLive.instances[-1].closed)
        self.assertEqual((self.root/'_config'/'AiDiy_key.json').read_bytes(),before)

    async def test_failures(self):
        for mode, reason in [('start_failure','connection_failed'), ('send_failure','send_failed'), ('exception','live_check_failed'), ('silence','timeout')]:
            with self.subTest(mode=mode):
                FakeLive.mode=mode
                result=await self.checker().run()
                self.assertEqual(result['reason'],reason)
                self.assertTrue(FakeLive.instances[-1].closed)
    async def test_missing_config_and_unsupported(self):
        for value, reason in [('unknown','unsupported_provider'), ('freeai_live','model_not_configured')]:
            self.config={'LIVE_AI_NAME':value}; self.save()
            self.assertEqual((await self.checker().run())['reason'], reason)
        (self.root/'_config'/'AiDiy_key.json').write_text('broken')
        self.assertEqual((await self.checker().run())['reason'],'config_unavailable')
    async def test_openai_readiness(self):
        self.config={'LIVE_AI_NAME':'openai_live','LIVE_OPENAI_MODEL':'test-openai','LIVE_OPENAI_VOICE':'marin','openai_key_id':'secret-key-value'}; self.save()
        self.assertEqual((await self.checker().run())['status'],'OK')
    async def test_cancel_and_busy(self):
        FakeLive.mode='silence'; checker=self.checker()
        task=asyncio.create_task(checker.run()); await asyncio.sleep(.005)
        self.assertEqual((await checker.run())['reason'],'busy')
        task.cancel()
        with self.assertRaises(asyncio.CancelledError): await task
        self.assertFalse(checker.busy)
        self.assertTrue(FakeLive.instances[-1].closed)
    async def test_route_security_and_schema(self):
        app=FastAPI(); register_live_model_check(app,self.checker())
        self.assertNotIn('/internal/live_model_check',app.openapi()['paths'])
        transport=httpx.ASGITransport(app=app,client=('127.0.0.1',1234))
        async with httpx.AsyncClient(transport=transport,base_url='http://127.0.0.1:8095') as client:
            hdr={'X-AiDiy-Diag':'model-trial'}
            response=await client.post('/internal/live_model_check',json={},headers=hdr)
            self.assertEqual(response.json()['status'],'OK')
            for extra in [{'Origin':'null'},{'X-Forwarded-For':'127.0.0.1'},{'Forwarded':'for=127.0.0.1'},{'Host':'localhost'},{'Host':'evil.example'},{'X-AiDiy-Diag':'bad'}]:
                response=await client.post('/internal/live_model_check',json={},headers={**hdr,**extra})
                self.assertEqual(response.status_code,403)
            for body in [{'prompt':'override'},[],None]:
                response=await client.post('/internal/live_model_check',content=json.dumps(body),headers={**hdr,'Content-Type':'application/json'})
                self.assertEqual(response.status_code,400)
            self.assertEqual((await client.post('/internal/live_model_check?model=x',json={},headers=hdr)).status_code,400)
            self.assertEqual((await client.post('/internal/live_model_check',content=' '*65537,headers={**hdr,'Content-Type':'application/json'})).status_code,413)
        transport=httpx.ASGITransport(app=app,client=('192.0.2.1',1234))
        async with httpx.AsyncClient(transport=transport,base_url='http://127.0.0.1:8095') as client:
            self.assertEqual((await client.post('/internal/live_model_check',json={},headers=hdr)).status_code,403)
    async def test_disconnect_cancels_and_closes(self):
        FakeLive.mode='silence'
        checker=self.checker(); app=FastAPI(); register_live_model_check(app,checker)
        received=0
        async def receive():
            nonlocal received
            received+=1
            if received==1: return {'type':'http.request','body':b'{}','more_body':False}
            await asyncio.sleep(.005)
            return {'type':'http.disconnect'}
        sent=[]
        async def send(message): sent.append(message)
        scope={'type':'http','asgi':{'version':'3.0'},'http_version':'1.1','method':'POST',
               'scheme':'http','path':'/internal/live_model_check','raw_path':b'/internal/live_model_check',
               'query_string':b'','root_path':'','server':('127.0.0.1',8095),'client':('127.0.0.1',2345),
               'headers':[(b'host',b'127.0.0.1:8095'),(b'content-type',b'application/json'),(b'x-aidiy-diag',b'model-trial')]}
        await app(scope,receive,send)
        self.assertEqual(sent[0]['status'],499)
        self.assertTrue(FakeLive.instances[-1].closed)
        self.assertFalse(checker.busy)
    async def test_openai_waits_for_settings(self):
        self.config={'LIVE_AI_NAME':'openai_live','LIVE_OPENAI_MODEL':'test','LIVE_OPENAI_VOICE':'marin','openai_key_id':'secret-key-value'}; self.save()
        FakeLive.mode='not_ready'
        self.assertEqual((await self.checker().run())['reason'],'timeout')
        self.assertTrue(FakeLive.instances[-1].closed)
    async def test_raw_config_size_and_keys(self):
        self.config.pop('freeai_key_id'); self.save()
        self.assertEqual((await self.checker().run())['reason'],'key_not_configured')
        (self.root/'_config'/'AiDiy_key.json').write_bytes(b' '*1048577)
        self.assertEqual((await self.checker().run())['reason'],'config_unavailable')
    async def test_ready_then_fifteen_second_settle_then_send(self):
        events=[]
        class Ordered(FakeLive):
            async def 開始(self,**kwargs):
                events.append('ready')
                return await super().開始(**kwargs)
            async def テキスト送信(self,text):
                events.append('send')
                return await super().テキスト送信(text)
        async def sleep(delay): events.append(('sleep',delay))
        result=await LiveModelCheck(self.root,Ordered,timeout=.04,sleep=sleep).run()
        self.assertEqual(result['status'],'OK')
        self.assertEqual(events,['ready',('sleep',15),'send'])
    async def test_cancel_during_settle(self):
        settling=asyncio.Event()
        async def sleep(delay):
            self.assertEqual(delay,15);settling.set();await asyncio.Event().wait()
        checker=LiveModelCheck(self.root,FakeLive,sleep=sleep)
        task=asyncio.create_task(checker.run());await settling.wait();task.cancel()
        with self.assertRaises(asyncio.CancelledError):await task
        self.assertTrue(FakeLive.instances[-1].closed);self.assertFalse(checker.busy)
    async def test_audio_exact_second_and_multiple_chunks(self):
        sink=DiagnosticOutput()
        for _ in range(4):
            await sink.put({'mime_type':'audio/pcm;rate=24000','bytes_data':b'\0'*12000})
        audio=sink.audio_result()
        self.assertEqual(audio['duration_ms'],1000)
        data=base64.b64decode(audio['data_base64'])
        self.assertEqual(len(data),48044)
        with wave.open(io.BytesIO(data),'rb') as wav:
            self.assertEqual((wav.getnchannels(),wav.getsampwidth(),wav.getframerate(),wav.getnframes()),(1,2,24000,24000))
    async def test_short_invalid_and_overflow_audio_not_returned(self):
        for mime,data in [('audio/pcm',b'\0'*47998),('audio/pcm;rate=16000',b'\0'*48000),
                          ('audio/pcm;channels=2',b'\0'*48000),('audio/mpeg',b'\0'*48000),
                          ('audio/pcm',b'\0'*48001),('audio/pcm',b'\0'*(DiagnosticOutput.MAX_PCM+2))]:
            sink=DiagnosticOutput();await sink.put({'mime_type':mime,'bytes_data':data})
            self.assertIsNone(sink.audio_result())
        sink=DiagnosticOutput()
        await sink.put({'mime_type':'audio/pcm','bytes_data':b'\0'*48000})
        await sink.put({'mime_type':'audio/pcm;rate=16000','bytes_data':b'\0'*48000})
        self.assertIsNone(sink.audio_result());self.assertEqual(len(sink.pcm),0)
    async def test_text_does_not_cut_off_following_audio(self):
        events=[]
        class WithAudio(FakeLive):
            async def テキスト送信(self,text):
                await self.queue.put({'text':'おはよう'})
                await asyncio.sleep(0)
                for _ in range(3):
                    await self.queue.put({'mime_type':'audio/pcm','bytes_data':b'\0'*24000})
                events.append('audio_complete')
                await self.queue.put({'diagnostic_turn_complete':True})
                return True
        async def sleep(delay): pass
        result=await LiveModelCheck(self.root,WithAudio,timeout=.04,sleep=sleep).run()
        self.assertEqual(result['status'],'OK');self.assertEqual(result['audio']['duration_ms'],1500)
        self.assertEqual(events,['audio_complete']);self.assertTrue(FakeLive.instances[-1].closed)
    async def test_audio_only_counts_response_without_fabricated_text(self):
        class AudioOnly(FakeLive):
            async def テキスト送信(self,text):
                await self.queue.put({'mime_type':'audio/pcm','bytes_data':b'\0'*48000})
                await self.queue.put({'diagnostic_turn_complete':True})
                return True
        async def sleep(delay): pass
        result=await LiveModelCheck(self.root,AudioOnly,timeout=.04,sleep=sleep).run()
        self.assertEqual(result['reason'],'audio_response_received');self.assertEqual(result['reply'],'')
        self.assertEqual(result['audio']['duration_ms'],1000)
    async def test_incomplete_audio_timeout_does_not_publish_partial(self):
        class Incomplete(FakeLive):
            async def テキスト送信(self,text):
                await self.queue.put({'text':'途中'})
                await self.queue.put({'mime_type':'audio/pcm','bytes_data':b'\0'*48000})
                return True
        async def sleep(delay): pass
        result=await LiveModelCheck(self.root,Incomplete,timeout=.01,sleep=sleep).run()
        self.assertEqual(result['reason'],'timeout');self.assertNotIn('audio',result)
        self.assertTrue(FakeLive.instances[-1].closed)
    async def test_audio_arrives_after_text_and_send_returns(self):
        class Delayed(FakeLive):
            async def テキスト送信(self,text):
                async def produce():
                    await self.queue.put({'text':'先に字幕'})
                    await asyncio.sleep(.005)
                    await self.queue.put({'mime_type':'audio/pcm','bytes_data':b'\0'*48000})
                    await self.queue.put({'diagnostic_turn_complete':True})
                self.producer=asyncio.create_task(produce())
                return True
            async def 終了(self):
                await super().終了()
                if hasattr(self,'producer'):
                    await self.producer
        async def sleep(delay): pass
        # 応答の到着順を確認する試験。OSのタイマー精度を40msの期限で判定しない。
        result=await LiveModelCheck(self.root,Delayed,timeout=1,sleep=sleep).run()
        self.assertEqual(result['status'],'OK')
        self.assertEqual(result['audio']['duration_ms'],1000)
        self.assertTrue(FakeLive.instances[-1].producer.done())
    async def test_cancel_during_audio_discards_partial(self):
        sent=asyncio.Event()
        class Partial(FakeLive):
            async def テキスト送信(self,text):
                await self.queue.put({'mime_type':'audio/pcm','bytes_data':b'\0'*48000})
                sent.set()
                return True
        async def sleep(delay): pass
        checker=LiveModelCheck(self.root,Partial,sleep=sleep)
        task=asyncio.create_task(checker.run());await sent.wait();task.cancel()
        with self.assertRaises(asyncio.CancelledError):await task
        self.assertTrue(FakeLive.instances[-1].closed);self.assertFalse(checker.busy)
    async def test_short_audio_with_text_has_no_attachment(self):
        class Short(FakeLive):
            async def テキスト送信(self,text):
                await self.queue.put({'text':'短い返答'})
                await self.queue.put({'mime_type':'audio/pcm','bytes_data':b'\0'*47998})
                await self.queue.put({'diagnostic_turn_complete':True})
                return True
        async def sleep(delay): pass
        result=await LiveModelCheck(self.root,Short,timeout=.04,sleep=sleep).run()
        self.assertEqual(result['status'],'OK');self.assertNotIn('audio',result)
    async def test_gemini_turn_marker_follows_audio_and_transcript(self):
        path=Path(__file__).resolve().parents[2]/'backend_server/AIコア/AIライブ_gemini.py'
        tree=ast.parse(path.read_text(encoding='utf-8'))
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='LiveAI')
        method=next(n for n in cls.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='_サーバーコンテンツ処理')
        namespace={}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),'adapter-test','exec'),namespace)
        sink=DiagnosticOutput()
        fake=types.SimpleNamespace(diagnostic=True,_出力字幕='',テキスト受信Q=sink,音声受信Q=sink)
        part=types.SimpleNamespace(text=None,inline_data=types.SimpleNamespace(data=b'\0'*48000,mime_type='audio/pcm;rate=24000'))
        content=types.SimpleNamespace(model_turn=types.SimpleNamespace(parts=[part]),turn_complete=True,interrupted=False,output_transcription=types.SimpleNamespace(text='おはよう'))
        await namespace['_サーバーコンテンツ処理'](fake,content)
        self.assertEqual(await sink.get(),{'text':'おはよう'})
        self.assertEqual(await sink.get(),{'diagnostic_turn_complete':True})
        self.assertEqual(sink.audio_result()['duration_ms'],1000)
    def test_registry_not_changed(self):
        text=(Path(__file__).resolve().parents[1]/'tools_main.py').read_text(encoding='utf-8')
        self.assertNotIn('mcp_live',text)
        self.assertEqual(text.count('register_live_model_check(app)'),1)

if __name__ == '__main__': unittest.main()

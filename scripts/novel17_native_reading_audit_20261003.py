# -*- coding: utf-8 -*-
"""17回のかな指定を、元の漢字で合成した短い比較音声で点検する。本番は変更しない。"""
import io
import json
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import speech_recognition as sr
import novel_minimal_reading_20261003 as current
import generate_novel_telop_timing as timing
from sudachipy import dictionary
from tools_proc.text_to_speech import TextToSpeech

WORK=current.base.ROOT/'_temp/novel17_native_reading_audit_20261003'
TERMS=('本好きの下剋上','九話','曾祖父','恭順','父娘','館','主','側仕え','石を吐','城にいる間')

def run():
    WORK.mkdir(exist_ok=True,parents=True)
    folder=current.base.VIDEO/'本好き_貴族院17_ja'
    scenario=json.loads((folder/'scenario.json').read_text(encoding='utf-8-sig'))
    selected=[]
    for term in TERMS:
        candidates=[]
        for scene in scenario['scenes']:
            for mode in ('long','short'):
                for sentence in timing.SENTENCE.findall(scene[mode+'_narration']):
                    if term in sentence and any(c['source']==term for c in current.convert(sentence,dictionary.Dictionary().tokenizer())[1]):
                        candidates.append((sentence,scene['id'],mode))
        assert candidates,term
        sentence,scene_id,mode=min(candidates,key=lambda row:len(row[0]))
        changed,overrides=current.convert(sentence,dictionary.Dictionary().tokenizer())
        for variant,text in [('native',sentence),('current',changed)]:
            selected.append({'term':term,'scene':scene_id,'mode':mode,'variant':variant,'text':text,'overrides':overrides})
    local=threading.local()
    def one(index,row):
        path=WORK/f'{index:02d}_{row["variant"]}.mp3'
        if not hasattr(local,'tts'):local.tts=TextToSpeech()
        data,info=local.tts.synthesize(row['text'],language='ja',provider='edge',voice='female')
        assert info['used_provider']=='edge'
        path.write_bytes(data)
        wav=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-af','adelay=1000,apad=pad_dur=1','-ac','1','-ar','16000','-f','wav','pipe:1'],capture_output=True,check=True).stdout
        recognizer=sr.Recognizer();recognizer.operation_timeout=30
        with sr.AudioFile(io.BytesIO(wav)) as source:audio=recognizer.record(source)
        asr=recognizer.recognize_google(audio,language='ja-JP')
        return {**row,'actual_input':info['speech_text'],'asr':asr,'audio_file':str(path),'audio_sha256':current.base.digest(data)}
    results=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(one,index,row) for index,row in enumerate(selected)]
        for future in as_completed(futures):
            row=future.result();results.append(row)
            print(json.dumps({k:row[k] for k in ('term','variant','text','asr')},ensure_ascii=False),flush=True)
    current.base.write_json(WORK/'native_vs_current.json',sorted(results,key=lambda row:(row['term'],row['variant'])))

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    run()

# -*- coding: utf-8 -*-
"""重ねたASRでも抜けた語を短い区間で確認。全編聴取の代わりにはしない。"""
import io
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
import speech_recognition as sr
import novel_minimal_reading_20261003 as audio


def probes():
    selected=[(17,'long_scene_005.mp3',start,7) for start in (64,69,74)]
    def one(job):
        number,name,start,length=job
        stage=audio.WORK/'staged'/f'本好き_貴族院{number}_ja'/name
        wave=subprocess.run(['ffmpeg','-v','error','-ss',str(start),'-t',str(length),'-i',str(stage),'-af','adelay=1000,apad=pad_dur=1','-ac','1','-ar','16000','-f','wav','pipe:1'],capture_output=True,check=True).stdout
        r=sr.Recognizer();r.operation_timeout=30
        with sr.AudioFile(io.BytesIO(wave)) as source:recording=r.record(source)
        return {'episode':number,'file':name,'audio_sha256':audio.base.digest(stage.read_bytes()),'start_sec':start,'window_sec':length,'text':r.recognize_google(recording,language='ja-JP')}
    with ThreadPoolExecutor(max_workers=3) as pool:result=list(pool.map(one,selected))
    audio.base.write_json(audio.WORK/'short_window_probes.json',result)
    for row in result:print(json.dumps(row,ensure_ascii=False))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    probes()

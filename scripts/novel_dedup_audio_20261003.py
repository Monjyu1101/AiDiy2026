# -*- coding: utf-8 -*-
"""今回の変更音声だけを退避先で再録・照合し、確認後に反映する。"""
import ast
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import novel_rerecord_review as base
import novel_prepare_tts_readings as reading
from sudachipy import dictionary

ROOT=base.ROOT
WORK=ROOT/'_temp/novel_dedup_20261003_17_19_original'
base.WORK=WORK

def prepare(numbers):
    for n in numbers:
        path=base.VIDEO/f'本好き_貴族院{n}_ja/tts_narration.json'
        if path.exists() and json.loads(path.read_text(encoding='utf-8')).get('version',1)>=2:
            raise RuntimeError('この旧処理の全文かな化は再適用できません。漢字を保つnovel_minimal_reading_20261003.pyを使用してください。')
    tok=dictionary.Dictionary().tokenizer()
    reading.TERMS.update({'気に入る':'きにいる','気に入り':'きにいり','十日後':'とおかご','荷台':'にだい'})
    reading.TERMS.update({'一日に':'いちにちに','一滴':'いってき','町へ降り':'まちへおり'})
    reading.SINGLE_NOUNS.update({'階':'かい'})
    reading.TERMS.update({'空を飛':'そらをと','空の農村':'からののうそん','空の魔術具':'からのまじゅつぐ','一口':'ひとくち','二口':'ふたくち','一撃':'いちげき','身を挺':'みをてい','名を受ける':'なをうける','火傷':'やけど','鍛冶':'かじ','主に仕える':'あるじにつかえる','主自身':'あるじじしん'})
    reading.TERMS.update({'第十七回':'だいじゅうななかい','祝詞':'のりと','曾祖父':'そうそふ','恭順':'きょうじゅん','三枚おろし':'さんまいおろし','実弟':'じってい','繊細':'せんさい','種になり':'たねになり','五神':'ごしん','七の鐘':'ななのかね','時の女神':'ときのめがみ','父娘':'おやこ','回復薬':'かいふくやく','名を捧げ':'なをささげ','名を受け':'なをうけ','実務':'じつむ','素材の実':'そざいのみ'})
    for n in numbers:
        folder=base.VIDEO/f'本好き_貴族院{n}_ja'
        data=json.loads((folder/'scenario.json').read_text(encoding='utf-8-sig'))
        previous=json.loads((folder/'tts_narration.json').read_text(encoding='utf-8')) if (folder/'tts_narration.json').exists() else {'tracks':{}}
        audit={}
        for s in data['scenes']:
            for mode in ('short','long'):
                name=f'{mode}_{s["id"]}.mp3'
                original=s[f'{mode}_narration'].strip()
                old=previous['tracks'].get(name)
                if n != 17 and old and old['narration_sha256']==base.digest(original): continue
                speech=reading.convert(original,tok,audit)
                previous['tracks'][name]={'narration_sha256':base.digest(original),'speech_text':speech,'speech_text_sha256':base.digest(speech)}
        previous.update(version=1,reviewed_date='2026-10-03',policy='重複整理後の原稿を文脈読みでかな指定。固有名詞と句読点を保持。')
        base.write_json(folder/'tts_narration.json',previous)
        base.write_json(WORK/f'reading_audit_{n}.json',{k:sorted(v) for k,v in sorted(audit.items())})
        # 第17回にも古い読みで再生成しないハッシュ確認を設ける。
        gen=folder/'_gen_audio.py'
        source=gen.read_text(encoding='utf-8-sig')
        if 'reading_path = ' not in source:
            source=source.replace('import json\n','import hashlib\nimport json\n',1)
            marker='def apply_pronunciation(text, out_path):\n'
            check='''    reading_path = os.path.join(_THIS_DIR, 'tts_narration.json')
    if os.path.isfile(reading_path):
        with open(reading_path, encoding='utf-8') as f:
            entry = json.load(f)['tracks'][os.path.basename(out_path)]
        if hashlib.sha256(text.strip().encode('utf-8')).hexdigest() != entry['narration_sha256']:
            raise ValueError('字幕原稿が変更されています。TTSの読みを再確認してください。')
        speech = entry['speech_text']
        if hashlib.sha256(speech.encode('utf-8')).hexdigest() != entry['speech_text_sha256']:
            raise ValueError('TTS原稿のハッシュが一致しません。')
        return speech
'''
            if marker not in source: raise ValueError('読み置換関数なし')
            source=source.replace(marker,marker+check,1)
            ast.parse(source)
            gen.write_text(source,encoding='utf-8')
        print('読み準備',n,flush=True)

def jobs():
    tasks=[]
    for n in (17,18,19):
        folder=base.VIDEO/f'本好き_貴族院{n}_ja'
        if not (folder/'tts_narration.json').exists(): continue
        current=json.loads((folder/'scenario.json').read_text(encoding='utf-8-sig'))
        original=json.loads((WORK/folder.name/'scenario.json').read_text(encoding='utf-8-sig'))
        readings=json.loads((folder/'tts_narration.json').read_text(encoding='utf-8'))['tracks']
        for s,old in zip(current['scenes'],original['scenes'],strict=True):
            for mode in ('short','long'):
                if n!=17 and s[f'{mode}_narration']==old[f'{mode}_narration']: continue
                name=f'{mode}_{s["id"]}.mp3'
                entry=readings[name]
                text=s[f'{mode}_narration'].strip()
                if base.digest(text)!=entry['narration_sha256'] or base.digest(entry['speech_text'])!=entry['speech_text_sha256'] or reading.KANJI.search(entry['speech_text']): raise ValueError((n,name,'原稿未確認'))
                stage=WORK/'staged'/folder.name/name
                stage.parent.mkdir(parents=True,exist_ok=True)
                tasks.append((folder,s,mode,name,entry,text,stage))
    return tasks

base.jobs=jobs

def publish():
    tasks=jobs()
    for folder,s,mode,name,entry,text,stage in tasks:
        result=json.loads(stage.with_suffix('.review.json').read_text(encoding='utf-8'))
        if result.get('verdict')!='ok' or result['audio_sha256']!=base.digest(stage.read_bytes()) or result['narration_sha256']!=base.digest(text) or result['local_speech_text_sha256']!=base.digest(entry['speech_text']) or any(w.get('error') for w in result.get('asr_windows',[])+result.get('supplemental_asr',[])): raise ValueError((folder.name,name,'未確認'))
    for n in (17,18,19):
        folder=base.VIDEO/f'本好き_貴族院{n}_ja'
        old=json.loads((WORK/folder.name/'audio_review.json').read_text(encoding='utf-8'))
        for f,s,mode,name,entry,text,stage in tasks:
            if f!=folder: continue
            target=folder/'audio'/name
            temp=target.with_suffix('.new.mp3')
            shutil.copy2(stage,temp)
            os.replace(temp,target)
            old['files'][name]=json.loads(stage.with_suffix('.review.json').read_text(encoding='utf-8'))
        old.update(reviewed_date='2026-10-03',source_revision='場面末尾の再説明を整理し、原作の未説明部分を加筆。変更音声をかな指定で再録・ASR照合。',tts_narration_path='tts_narration.json',unresolved=[],listening_review='全編の耳による確認は未実施。TTS原稿・ASR・音声のハッシュで照合。')
        old['asset_validation']='再検証待ち'
        base.write_json(folder/'audio_review.json',old)
        indexpath=folder/'index.html'
        index=indexpath.read_text(encoding='utf-8')
        index=re.sub(r'return `\$\{audioPath\}(?:\?v=[^`]*)?`;', 'return `${audioPath}?v=${encodeURIComponent(audioMode)}-20261003-dedup-1`;',index)
        index=re.sub(r'scenario.js(?:\?v=[^"\s]+)?','scenario.js?v=20261003-dedup-1',index)
        indexpath.write_text(index,encoding='utf-8')
        subprocess.run([sys.executable,str(ROOT/'scripts/novel_update_durations.py'),str(folder),'重複を整理し原作の未説明部分を加筆。MP3の実測尺・開始秒を反映済み。ロング版は{LONG}。'],check=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    phase=sys.argv[1]
    if phase=='prepare': prepare([int(n) for n in sys.argv[2:]])
    else: {'generate':base.generate,'review':base.review,'supplement':base.supplement,'publish':publish}[phase]()

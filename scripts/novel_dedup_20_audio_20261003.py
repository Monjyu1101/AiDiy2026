# -*- coding: utf-8 -*-
"""第20回だけをかな準備・退避先で再録・ASR照合・確認後に反映する。"""
import json
import os
import re
import shutil
import subprocess
import sys
import novel_dedup_audio_20261003 as shared

base=shared.base
WORK=base.ROOT/'_temp/novel_dedup_20261003_20_original'
FOLDER=base.VIDEO/'本好き_貴族院20_ja'
shared.WORK=WORK
base.WORK=WORK

def prepare():
    current_reading=FOLDER/'tts_narration.json'
    if current_reading.exists() and json.loads(current_reading.read_text(encoding='utf-8')).get('version',1)>=2:
        raise RuntimeError('第20回の全文かな化は廃止済みです。漢字を保つnovel_minimal_reading_20261003.pyを使用してください。')
    shared.reading.TERMS.update({'数日間':'すうじつかん','一区切り':'ひとくぎり','城へ':'しろへ','城に':'しろに','気に入っ':'きにいっ','有力者':'ゆうりょくしゃ'})
    shared.reading.TERMS.update({'名を返':'なをかえ','空へ':'そらへ','金色に':'きんいろに','手の裏':'てのうら','一族の一人':'いちぞくのひとり','名も':'なも','若い頃':'わかいころ','物の裏':'もののうら','早歩き':'はやあるき','部屋を':'へやを','主へ':'あるじへ','主が':'あるじが'})
    current=json.loads((FOLDER/'scenario.json').read_text(encoding='utf-8-sig'))
    original=json.loads((WORK/FOLDER.name/'scenario.json').read_text(encoding='utf-8-sig'))
    previous=json.loads((FOLDER/'tts_narration.json').read_text(encoding='utf-8'))
    for scene,old in zip(current['scenes'],original['scenes'],strict=True):
        for mode in ('short','long'):
            if scene[mode+'_narration']!=old[mode+'_narration']:
                previous['tracks'].pop(f'{mode}_{scene["id"]}.mp3',None)
    base.write_json(FOLDER/'tts_narration.json',previous)
    shared.prepare([20])

def jobs():
    current=json.loads((FOLDER/'scenario.json').read_text(encoding='utf-8-sig'))
    original=json.loads((WORK/FOLDER.name/'scenario.json').read_text(encoding='utf-8-sig'))
    readings=json.loads((FOLDER/'tts_narration.json').read_text(encoding='utf-8'))['tracks']
    result=[]
    for scene,old in zip(current['scenes'],original['scenes'],strict=True):
        for mode in ('short','long'):
            if scene[mode+'_narration']==old[mode+'_narration']:continue
            name=f'{mode}_{scene["id"]}.mp3';text=scene[mode+'_narration'].strip();entry=readings[name]
            assert base.digest(text)==entry['narration_sha256']
            assert base.digest(entry['speech_text'])==entry['speech_text_sha256']
            assert not shared.reading.KANJI.search(entry['speech_text'])
            stage=WORK/'staged'/FOLDER.name/name;stage.parent.mkdir(parents=True,exist_ok=True)
            result.append((FOLDER,scene,mode,name,entry,text,stage))
    return result

base.jobs=jobs

def supplement():
    # 長編の通常ASRには区間境界で文が抜けるため、22本ともずらして照合する。
    base.supplement({(20,job[3]) for job in jobs() if job[2]=='long'})

def publish():
    tasks=jobs()
    for folder,s,mode,name,entry,text,stage in tasks:
        d=json.loads(stage.with_suffix('.review.json').read_text(encoding='utf-8'))
        assert d['verdict']=='ok' and d['audio_sha256']==base.digest(stage.read_bytes())
        assert d['narration_sha256']==base.digest(text) and d['local_speech_text_sha256']==base.digest(entry['speech_text'])
        assert not any(w.get('error') for w in d['asr_windows']+d.get('supplemental_asr',[]))
    review=json.loads((WORK/FOLDER.name/'audio_review.json').read_text(encoding='utf-8'))
    for folder,s,mode,name,entry,text,stage in tasks:
        target=folder/'audio'/name;temp=target.with_suffix('.new.mp3');shutil.copy2(stage,temp);os.replace(temp,target)
        review['files'][name]=json.loads(stage.with_suffix('.review.json').read_text(encoding='utf-8'))
    review.update(reviewed_date='2026-10-03',source_revision='原作449〜454を確認し、重複整理と未説明の出来事の加筆、人物と時系列の訂正後に再録。',tts_narration_path='tts_narration.json',unresolved=[],listening_review='全編の耳による確認は未実施。かな指定・ASR・ハッシュで確認。',asset_validation='再検証待ち')
    base.write_json(FOLDER/'audio_review.json',review)
    path=FOLDER/'index.html';index=path.read_text(encoding='utf-8')
    index,count=re.subn(r'return `\$\{audioPath\}(?:\?v=[^`]*)?`;', 'return `${audioPath}?v=${encodeURIComponent(audioMode)}-20261003-dedup-1`;',index);assert count==1
    index=re.sub(r'scenario.js(?:\?v=[^"\s]+)?','scenario.js?v=20261003-dedup-1',index);path.write_text(index,encoding='utf-8')
    subprocess.run([sys.executable,str(base.ROOT/'scripts/novel_update_durations.py'),str(FOLDER),'重複を整理し原作の未説明部分を加筆。MP3の実測尺・開始秒を反映済み。ロング版は{LONG}。'],check=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    {'prepare':prepare,'generate':base.generate,'review':base.review,'supplement':supplement,'publish':publish}[sys.argv[1]]()

# -*- coding: utf-8 -*-
"""貴族院17〜20: 漢字交じり文を保ち、確認済みの誤読語だけ指定して再録する。"""
import ast
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor,as_completed
from sudachipy import dictionary,tokenizer
import novel_rerecord_review as base

WORK=base.ROOT/'_temp/novel_minimal_reading_20261003_original'
base.WORK=WORK
NUMBERS=(17,18,19,20)
CACHE='20261003-minimal-reading-1'
# 自動辞書の全語変換をしない。過去に確認した誤読と作品語に限る。
TERMS={
    '本好きの下剋上':'本ずきの下剋上',
    '祝詞':'のりと','神具':'しんぐ','騎獣':'きじゅう','側仕え':'そばづかえ',
    '名捧げ':'なささげ','養母':'ようぼ','養父':'ようふ',
    '曾祖父':'そうそふ','恭順':'きょうじゅん','父娘':'おやこ',
    'お父様':'おとうさま','奉納舞':'ほうのうまい','九話':'きゅうわ',
    'AiDiy':'アイディ',
    '名を捧げ':'なを捧げ','名を受け':'なを受け','名を返':'なを返','名を持つ':'なを持つ',
    '額を軽く弾':'ひたいを軽くはじ',
    'デュルの実':'デュルのみ','木の実':'木のみ','素材の実':'素材のみ',
    '実を結ぶ':'みを結ぶ','石を吐':'石をは',
    '城にいる間':'城にいるあいだ','貴族院にいる間':'貴族院にいるあいだ',
    '闇の神':'やみの神','空を飛':'そらを飛',
    '空の魔術具':'からの魔術具','空の農村':'からの農村',
}
# 単語境界を辞書で確認し、領主・図書館など別の熟語には波及させない。
SINGLE={'主':'あるじ','館':'やかた','宴':'うたげ','額':'ひたい'}

def convert(text,tok,episode=None):
    changes=[]
    spans=[]
    singles={**SINGLE,**({'城':'しろ'} if episode in (18,19,20) else {})}
    for word in tok.tokenize(text,tokenizer.Tokenizer.SplitMode.C):
        source=word.surface()
        # 「直接城へ」の城は辞書で接尾辞になるため、既知の文脈を明示する。
        direct_castle=source=='城' and episode in (18,19,20) and text[:word.begin()].endswith('直接')
        if source in singles and (word.part_of_speech()[0]=='名詞' or direct_castle):
            spans.append((word.begin(),word.end(),singles[source],source))
    pattern=re.compile('|'.join(re.escape(k) for k in sorted(TERMS,key=len,reverse=True)))
    # 長い文脈指定を優先し、そこで指定済みの単独語は重ねて変換しない。
    phrase_spans=[(m.start(),m.end(),TERMS[m[0]],m[0]) for m in pattern.finditer(text)]
    spans=[s for s in spans if not any(a<s[1] and s[0]<b for a,b,_,_ in phrase_spans)]+phrase_spans
    pieces=[];position=0
    for begin,end,reading,source in sorted(spans):
        assert position<=begin
        pieces.extend((text[position:begin],reading));position=end
        changes.append({'source':source,'reading':reading,'start':begin,'end':end})
    pieces.append(text[position:])
    return ''.join(pieces),changes

def prepare():
    WORK.mkdir(parents=True,exist_ok=True)
    tok=dictionary.Dictionary().tokenizer();report=[]
    production=base.VIDEO/'本好き__貴族院/動画作り方.md'
    if not (WORK/'production_before.md').exists():shutil.copy2(production,WORK/'production_before.md')
    for n in NUMBERS:
        folder=base.VIDEO/f'本好き_貴族院{n}_ja';saved=WORK/folder.name
        if not saved.exists():
            shutil.copytree(folder,saved)
            shutil.copy2(base.VIDEO/f'本好き__貴族院/本好き__貴族院_{n}.md',saved/'source.md')
        scenario=json.loads((folder/'scenario.json').read_text(encoding='utf-8-sig'))
        old=json.loads((saved/'tts_narration.json').read_text(encoding='utf-8'))['tracks']
        tracks={};kanji_before=kanji_after=0
        for scene in scenario['scenes']:
            for mode in ('short','long'):
                name=f'{mode}_{scene["id"]}.mp3';original=scene[mode+'_narration'].strip()
                speech,changes=convert(original,tok,n)
                kanji_before+=len(re.findall(r'[\u4e00-\u9fff々]',original))
                kanji_after+=len(re.findall(r'[\u4e00-\u9fff々]',speech))
                assert old[name]['speech_text']!=speech
                tracks[name]={'narration_sha256':base.digest(original),'speech_text':speech,'speech_text_sha256':base.digest(speech),'pronunciation_overrides':changes}
                report.append({'episode':n,'file':name,'changes':changes})
        path=WORK/'prepared'/folder.name/'tts_narration.json';path.parent.mkdir(parents=True,exist_ok=True)
        base.write_json(path,{'version':2,'reviewed_date':'2026-10-03','policy':'漢字交じり原稿を保ち、確認済みの誤読語・作品語・単独の主/館/宴/額と18〜20回の城だけ文脈指定。全文かな化・自動辞書読み変換はしない。','tracks':tracks})
        print(n,'漢字保持',kanji_after,'/',kanji_before,flush=True)
    base.write_json(WORK/'minimal_reading_audit.json',report)

def jobs():
    result=[]
    for n in NUMBERS:
        folder=base.VIDEO/f'本好き_貴族院{n}_ja'
        scenario=json.loads((folder/'scenario.json').read_text(encoding='utf-8-sig'))
        readings=json.loads((WORK/'prepared'/folder.name/'tts_narration.json').read_text(encoding='utf-8'))['tracks']
        for scene in scenario['scenes']:
            for mode in ('short','long'):
                name=f'{mode}_{scene["id"]}.mp3';original=scene[mode+'_narration'].strip();entry=readings[name]
                assert entry['narration_sha256']==base.digest(original)
                assert entry['speech_text_sha256']==base.digest(entry['speech_text'])
                stage=WORK/'staged'/folder.name/name;stage.parent.mkdir(parents=True,exist_ok=True)
                result.append((folder,scene,mode,name,entry,original,stage))
    assert len(result)==176
    return result

base.jobs=jobs

def sample():
    selection={(17,'long_scene_001.mp3'),(17,'long_scene_010.mp3'),(18,'long_scene_018.mp3'),(20,'long_scene_002.mp3')}
    base.jobs=lambda:[j for j in jobs() if (int(j[0].name.split('貴族院')[1][:2]),j[3]) in selection]
    base.generate();base.review()

def supplement():
    extra={(17,'long_scene_010.mp3'),(20,'long_scene_002.mp3')}
    audit_path=WORK/'asr_difference_audit.json'
    if audit_path.exists():
        for row in json.loads(audit_path.read_text(encoding='utf-8')):
            if row['ratio']<.9 or max((max(map(len,pair)) for pair in row['largest']),default=0)>=35:
                extra.add((int(row['episode'].split('貴族院')[1][:2]),row['file']))
    base.supplement(extra)

def captions(episodes=None):
    import generate_novel_telop_timing as timing
    tasks=[];cues={};mismatches=[];matched=0
    for folder,scene,mode,name,entry,original,stage in jobs():
        if episodes is not None and int(folder.name.split('貴族院')[1][:2]) not in episodes:
            matched+=1
            continue
        revised=dict(scene);revised[mode+'_audio']=name
        revised[mode+'_duration_sec']=json.loads(stage.with_suffix('.generation.json').read_text(encoding='utf-8'))['duration_sec']
        tasks.append((stage.parent,scene['id'],mode,revised));cues.setdefault(folder.name,{})
    with ThreadPoolExecutor(max_workers=8) as pool:
        for future in as_completed([pool.submit(timing.analyse,job) for job in tasks]):
            folder,scene_id,mode,anchors,sentences,silences=future.result()
            if anchors is not None:
                cues[folder.name].setdefault(scene_id,{})[mode]=anchors;matched+=1
            else:mismatches.append({'folder':folder.name,'scene':scene_id,'mode':mode,'sentences':sentences,'silences':silences})
    for folder,data in cues.items():base.write_json(WORK/'prepared'/folder/'telop_timing.json',data)
    summary={'matched':matched,'total':176,'mismatches':mismatches}
    if episodes is not None:
        previous=json.loads((WORK/'subtitle_summary.json').read_text(encoding='utf-8'))
        assert not previous['mismatches']
        summary['repairs']=previous.get('repairs',[])
    base.write_json(WORK/'subtitle_summary.json',summary)
    print('字幕',matched,'/',176,'不一致',mismatches)

def publish():
    tasks=jobs()
    for folder,scene,mode,name,entry,original,stage in tasks:
        current=json.loads((folder/'tts_narration.json').read_text(encoding='utf-8'))['tracks'][name]
        castle_readings=[c for c in current.get('pronunciation_overrides',[]) if c['source']=='城' and c['reading']=='しろ']
        if any(c not in entry.get('pronunciation_overrides',[]) for c in castle_readings):
            raise RuntimeError('単独の城の読み指定が新しい原稿より古い状態です。最新の読みを再準備・再録してから反映してください。')
        r=json.loads(stage.with_suffix('.review.json').read_text(encoding='utf-8'))
        assert r['verdict']=='ok' and r['audio_sha256']==base.digest(stage.read_bytes())
        assert r['narration_sha256']==base.digest(original) and r['local_speech_text_sha256']==base.digest(entry['speech_text'])
        assert not any(w.get('error') for w in r['asr_windows']+r.get('supplemental_asr',[]))
        import generate_novel_telop_timing as timing
        cues=json.loads((WORK/'prepared'/folder.name/'telop_timing.json').read_text(encoding='utf-8'))
        assert len(cues[scene['id']][mode])==len([v for v in timing.SENTENCE.findall(original) if v.strip()])
    for n in NUMBERS:
        folder=base.VIDEO/f'本好き_貴族院{n}_ja'
        review=json.loads((WORK/folder.name/'audio_review.json').read_text(encoding='utf-8'))
        for f,s,m,name,entry,original,stage in tasks:
            if f!=folder:continue
            target=folder/'audio'/name;tmp=target.with_suffix('.new.mp3');shutil.copy2(stage,tmp);os.replace(tmp,target)
            review['files'][name]=json.loads(stage.with_suffix('.review.json').read_text(encoding='utf-8'))
        shutil.copy2(WORK/'prepared'/folder.name/'tts_narration.json',folder/'tts_narration.json')
        shutil.copy2(WORK/'prepared'/folder.name/'telop_timing.json',folder/'telop_timing.json')
        review.update(reviewed_date='2026-10-03',source_revision='原稿は維持。全文かな化を撤回し、通常の漢字交じり文と最小限の読み指定で全44本を再録。',unresolved=[],listening_review='全編の耳による確認は未実施。TTS入力とASRを照合。',asset_validation='再検証待ち')
        base.write_json(folder/'audio_review.json',review)
        path=folder/'index.html';content=path.read_text(encoding='utf-8')
        content,count=re.subn(r'return `\$\{audioPath\}(?:\?v=[^`]*)?`;',f'return `${{audioPath}}?v=${{encodeURIComponent(audioMode)}}-{CACHE}`;',content);assert count==1
        content=re.sub(r'scenario.js(?:\?v=[^"\s]+)?','scenario.js?v='+CACHE,content);path.write_text(content,encoding='utf-8')
        subprocess.run([sys.executable,str(base.ROOT/'scripts/novel_update_durations.py'),str(folder),'漢字交じり文と最小限の文脈読みで再録。MP3の実測尺・開始秒を反映済み。ロング版は{LONG}。'],check=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    {'prepare':prepare,'sample':sample,'generate':base.generate,'review':base.review,'supplement':supplement,'captions':captions,'captions19':lambda:captions({19}),'publish':publish}[sys.argv[1]]()

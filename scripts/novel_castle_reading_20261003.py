# -*- coding: utf-8 -*-
"""貴族院18〜20の単独の城だけをしろに指定。無音の処理で部分再録し17回は触らない。"""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from sudachipy import dictionary,tokenizer
import novel_minimal_reading_20261003 as minimal
import generate_novel_telop_timing as timing

base=minimal.base
WORK=base.ROOT/'_temp/novel_castle_reading_20261003_original'
NUMBERS=(18,19,20)
CACHE='20261003-castle-reading-1'
base.WORK=WORK


def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))


def file_hashes(folder):
    return {str(p.relative_to(folder)):base.digest(p.read_bytes()) for p in sorted(folder.rglob('*')) if p.is_file()}


def prepare():
    WORK.mkdir(parents=True,exist_ok=True)
    protected=base.VIDEO/'本好き_貴族院17_ja'
    if not (WORK/'episode17_hashes.json').exists():base.write_json(WORK/'episode17_hashes.json',file_hashes(protected))
    production=base.VIDEO/'本好き__貴族院/動画作り方.md'
    if not (WORK/'production_before.md').exists():shutil.copy2(production,WORK/'production_before.md')
    tok=dictionary.Dictionary().tokenizer();report=[]
    for n in NUMBERS:
        folder=base.VIDEO/f'本好き_貴族院{n}_ja';saved=WORK/folder.name
        if not saved.exists():
            shutil.copytree(folder,saved)
            shutil.copy2(base.VIDEO/f'本好き__貴族院/本好き__貴族院_{n}.md',saved/'source.md')
        readings=load(saved/'tts_narration.json');scenario=load(saved/'scenario.json')
        for scene in scenario['scenes']:
            for mode in ('short','long'):
                name=f'{mode}_{scene["id"]}.mp3';original=scene[mode+'_narration'].strip();old=readings['tracks'][name]
                assert old['narration_sha256']==base.digest(original)
                spots=[(w.begin(),w.end()) for w in tok.tokenize(original,tokenizer.Tokenizer.SplitMode.C) if w.surface()=='城' and (w.part_of_speech()[0]=='名詞' or original[:w.begin()].endswith('直接'))]
                if not spots:continue
                # 既存の読み指定はそのまま保ち、今回の城だけ追加する。
                overrides=list(old['pronunciation_overrides'])
                for begin,end in spots:
                    assert not any(begin<c['end'] and c['start']<end for c in overrides),(n,name,begin)
                    overrides.append({'source':'城','reading':'しろ','start':begin,'end':end})
                overrides.sort(key=lambda c:c['start'])
                pieces=[];cursor=0
                for c in overrides:
                    assert original[c['start']:c['end']]==c['source']
                    pieces.extend((original[cursor:c['start']],c['reading']));cursor=c['end']
                pieces.append(original[cursor:]);speech=''.join(pieces)
                assert speech!=old['speech_text']
                # この回の再作成処理でも同じ読み指定になることを確認。
                assert speech==minimal.convert(original,tok,n)[0]
                readings['tracks'][name]={**old,'speech_text':speech,'speech_text_sha256':base.digest(speech),'pronunciation_overrides':overrides}
                report.append({'episode':n,'file':name,'occurrences':len(spots),'contexts':[original[max(0,b-10):e+12] for b,e in spots]})
        readings.update(version=2,reviewed_date='2026-10-03',policy='漢字交じり原稿を維持。既存の必要な読み指定に加え、単独の城だけしろと指定。城壁・城門・入城など熟語は置換しない。')
        prepared=WORK/'prepared'/folder.name;prepared.mkdir(parents=True,exist_ok=True)
        base.write_json(prepared/'tts_narration.json',readings)
    base.write_json(WORK/'castle_audit.json',report)
    print('対象',len(report),'本、単独の城',sum(r['occurrences'] for r in report),'箇所。17回は保護。',flush=True)


def jobs():
    result=[]
    for row in load(WORK/'castle_audit.json'):
        folder=base.VIDEO/f'本好き_貴族院{row["episode"]}_ja'
        scene_id=row['file'].removesuffix('.mp3').split('_',1)[1];mode=row['file'].split('_')[0]
        scene=next(s for s in load(WORK/folder.name/'scenario.json')['scenes'] if s['id']==scene_id)
        entry=load(WORK/'prepared'/folder.name/'tts_narration.json')['tracks'][row['file']]
        stage=WORK/'staged'/folder.name/row['file'];stage.parent.mkdir(parents=True,exist_ok=True)
        result.append((folder,scene,mode,row['file'],entry,scene[mode+'_narration'].strip(),stage))
    return result


base.jobs=jobs


def captions():
    prepared={n:load(WORK/f'本好き_貴族院{n}_ja/telop_timing.json') for n in NUMBERS}
    tasks=[]
    for folder,scene,mode,name,entry,original,stage in jobs():
        revised=dict(scene);revised[mode+'_audio']=name
        revised[mode+'_duration_sec']=load(stage.with_suffix('.generation.json'))['duration_sec']
        tasks.append((stage.parent,scene['id'],mode,revised))
    with ThreadPoolExecutor(max_workers=6) as pool:
        for folder,scene_id,mode,anchors,count,silences in pool.map(timing.analyse,tasks):
            assert anchors is not None,(folder,scene_id,mode,count,silences)
            n=int(folder.name.split('貴族院')[1][:2]);prepared[n][scene_id][mode]=anchors
    for n,cues in prepared.items():base.write_json(WORK/'prepared'/f'本好き_貴族院{n}_ja/telop_timing.json',cues)
    print('変更音声の字幕',len(tasks),'本の文数と無音区切りを確認。未変更字幕を維持。')


def inspect():
    for folder,scene,mode,name,entry,original,stage in jobs():
        d=load(stage.with_suffix('.review.json'))
        assert d['audio_sha256']==base.digest(stage.read_bytes())
        assert d['local_speech_text_sha256']==entry['speech_text_sha256']
        print(folder.name,name,'ASR',d['asr_phonetic_similarity'],json.dumps(d['asr_windows']+d.get('supplemental_asr',[]),ensure_ascii=False),flush=True)


def accept():
    from tools_proc.text_to_speech import TextToSpeech
    processor=TextToSpeech()
    for folder,scene,mode,name,entry,original,stage in jobs():
        path=stage.with_suffix('.review.json');d=load(path)
        assert d['audio_sha256']==base.digest(stage.read_bytes())
        assert d['narration_sha256']==base.digest(original)
        assert d['local_speech_text_sha256']==base.digest(entry['speech_text'])
        assert processor.normalize_for_speech(entry['speech_text'],'ja')[0]==d['speech_text']
        assert not any(w.get('error') for w in d['asr_windows']+d.get('supplemental_asr',[]))
        d.update(verdict='ok',review_note='単独の城だけしろに指定。漢字交じり原稿・最終入力・MP3・ASRを照合。全編の耳による確認は未実施。',verdict_scope='対象の城の読みと音声・原稿の整合。ブラウザー再生は収録中のため未実施。')
        base.write_json(path,d)
    print('変更対象の最終入力・MP3・ASR確認結果を記録。')


def publish():
    tasks=jobs()
    assert load(WORK/'episode17_hashes.json')==file_hashes(base.VIDEO/'本好き_貴族院17_ja')
    for folder,scene,mode,name,entry,original,stage in tasks:
        d=load(stage.with_suffix('.review.json'))
        assert d['verdict']=='ok' and d['audio_sha256']==base.digest(stage.read_bytes())
        cues=load(WORK/'prepared'/folder.name/'telop_timing.json')
        assert len(cues[scene['id']][mode])==len([s for s in timing.SENTENCE.findall(original) if s.strip()])
    for n in NUMBERS:
        folder=base.VIDEO/f'本好き_貴族院{n}_ja';review=load(WORK/folder.name/'audio_review.json')
        changed=[]
        for f,scene,mode,name,entry,original,stage in tasks:
            if f!=folder:continue
            temp=(folder/'audio'/name).with_suffix('.new.mp3');shutil.copy2(stage,temp);os.replace(temp,folder/'audio'/name)
            review['files'][name]=load(stage.with_suffix('.review.json'));changed.append(name)
        for filename in ('tts_narration.json','telop_timing.json'):shutil.copy2(WORK/'prepared'/folder.name/filename,folder/filename)
        review.pop('browser_validation',None)
        review.update(reviewed_date='2026-10-03',source_revision='単独の城をしろと指定し対象音声のみ再録。字幕原稿・他の読みを維持。',castle_reading_review={'changed_files':changed,'browser_playback':'利用者が17回を収録中のため未実施','full_listening':'未実施'},asset_validation='再検証待ち')
        base.write_json(folder/'audio_review.json',review)
        path=folder/'index.html';html=path.read_text(encoding='utf-8')
        html,count=re.subn(r'return `\$\{audioPath\}(?:\?v=[^`]*)?`;',f'return `${{audioPath}}?v=${{encodeURIComponent(audioMode)}}-{CACHE}`;',html);assert count==1
        html=re.sub(r'scenario.js(?:\?v=[^"\s]+)?','scenario.js?v='+CACHE,html);path.write_text(html,encoding='utf-8')
        subprocess.run([sys.executable,str(base.ROOT/'scripts/novel_update_durations.py'),str(folder),'漢字交じり原稿を保持し、単独の城をしろと指定して部分再録。実測尺・開始秒を反映済み。ロング版は{LONG}。'],check=True)


def verify():
    from tools_proc.text_to_speech import TextToSpeech
    processor=TextToSpeech();report=[];changed={(r['episode'],r['file']) for r in load(WORK/'castle_audit.json')}
    assert load(WORK/'episode17_hashes.json')==file_hashes(base.VIDEO/'本好き_貴族院17_ja')
    for n in NUMBERS:
        validator=(WORK/f'validator_{n}.txt').read_text(encoding='utf-8-sig')
        assert '(42/42 ' in validator and '[NG]' not in validator
        folder=base.VIDEO/f'本好き_貴族院{n}_ja';saved=WORK/folder.name
        scenario=load(folder/'scenario.json');old=load(saved/'scenario.json')
        js=(folder/'scenario.js').read_text(encoding='utf-8').removeprefix('window.SCENARIO = ').strip().removesuffix(';')
        assert json.loads(js)==scenario
        readings=load(folder/'tts_narration.json')['tracks'];old_readings=load(saved/'tts_narration.json')['tracks']
        review=load(folder/'audio_review.json');cues=load(folder/'telop_timing.json');old_cues=load(saved/'telop_timing.json')
        totals={'short':0.0,'long':0.0};tracks=[]
        for scene,previous in zip(scenario['scenes'],old['scenes'],strict=True):
            for key in previous:
                if 'duration' not in key and 'start_sec' not in key:assert scene[key]==previous[key],(n,scene['id'],key)
            for mode in ('short','long'):
                name=f'{mode}_{scene["id"]}.mp3';entry=readings[name];d=review['files'][name]
                narration=scene[mode+'_narration'].strip();path=folder/'audio'/name
                assert entry['narration_sha256']==d['narration_sha256']==base.digest(narration)
                assert entry['speech_text_sha256']==d['local_speech_text_sha256']==base.digest(entry['speech_text'])
                assert processor.normalize_for_speech(entry['speech_text'],'ja')[0]==d['speech_text']
                assert d['speech_text_sha256']==base.digest(d['speech_text'])
                assert d['audio_sha256']==base.digest(path.read_bytes()) and d['verdict']=='ok'
                assert not any(w.get('error') for w in d['asr_windows']+d.get('supplemental_asr',[]))
                modified=(n,name) in changed
                if modified:
                    assert base.digest(path.read_bytes())!=base.digest((saved/'audio'/name).read_bytes())
                    old_changes=old_readings[name]['pronunciation_overrides']
                    kept=[c for c in entry['pronunciation_overrides'] if c['source']!='城']
                    assert kept==old_changes
                    assert all(c['reading']=='しろ' for c in entry['pronunciation_overrides'] if c['source']=='城')
                else:
                    assert entry==old_readings[name] and cues[scene['id']][mode]==old_cues[scene['id']][mode]
                    assert base.digest(path.read_bytes())==base.digest((saved/'audio'/name).read_bytes())
                anchors=cues[scene['id']][mode]
                assert len(anchors)==len([s for s in timing.SENTENCE.findall(narration) if s.strip()])
                assert all(0<=a<b<=scene[mode+'_duration_sec'] for a,b in anchors)
                assert all(anchors[i][1]<=anchors[i+1][0] for i in range(len(anchors)-1))
                assert abs(scene[mode+'_duration_sec']-d['duration_sec'])<.0011
                assert abs(totals[mode]-scene[mode+'_start_sec'])<.0011
                totals[mode]+=scene[mode+'_duration_sec']
                tracks.append({'file':name,'changed':modified,'hashes':'ok','subtitle_sentences':len(anchors)})
        assert len(tracks)==44 and totals['long']>=1620
        assert all(abs(scenario['total_'+m+'_duration_sec']-totals[m])<.0011 for m in totals)
        for image in (saved/'images').iterdir():assert base.digest(image.read_bytes())==base.digest((folder/'images'/image.name).read_bytes())
        def formatted(seconds):
            seconds=round(seconds,3);minutes=int(seconds//60)
            return f'{minutes}分{seconds-minutes*60:06.3f}秒'
        mdpath=base.VIDEO/f'本好き__貴族院/本好き__貴族院_{n}.md';md=mdpath.read_text(encoding='utf-8')
        for scene in scenario['scenes']:
            assert all(scene[m+'_narration'].strip() in md for m in totals)
        md,count=re.subn(r'\| 間合い追加後の実測尺 \|[^\n]*',f'| 間合い追加後の実測尺 | ロング{formatted(totals["long"])}・ショート{formatted(totals["short"])}（2026-10-03単独の城をしろと指定して部分再録） |',md)
        assert count==1;mdpath.write_text(md,encoding='utf-8')
        result={'episode':n,'total_duration_sec':{m:round(v,3) for m,v in totals.items()},'changed_tracks':sum(t['changed'] for t in tracks),'castle_occurrences':sum(r['occurrences'] for r in load(WORK/'castle_audit.json') if r['episode']==n),'tracks':tracks,'validation':'42/42','narration_unchanged':True,'subtitle_tracks':'44/44','browser_playback':'17回収録中の利用者指示により未実施','full_listening':'未実施'}
        review.update(validation=result,asset_validation='42/42項目成功',methods=['漢字交じり原稿と既存の読み指定を保持','単独の城だけしろに指定し対象音声のみ再録','変更音声をGoogle音声認識で照合し重点箇所は区間を重ねて確認','全44本の原稿・最終TTS入力・MP3のハッシュと字幕を確認','全44本のデコードと実測尺を素材検証で確認。ブラウザー再生は未実施'])
        base.write_json(folder/'audio_review.json',review);report.append(result)
        print(n,{m:formatted(v) for m,v in totals.items()},'変更',result['changed_tracks'],'本、城',result['castle_occurrences'],'箇所',flush=True)
    base.write_json(WORK/'final_validation.json',{'episodes':report,'episode17_unchanged':True,'browser_playback':'未実施','audio_playback':'一切実施していない'})


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    {'prepare':prepare,'generate':base.generate,'review':base.review,'supplement':lambda:base.supplement({(row['episode'],row['file']) for row in load(WORK/'castle_audit.json')}),'captions':captions,'inspect':inspect,'accept':accept,'publish':publish,'verify':verify}[sys.argv[1]]()

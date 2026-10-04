# -*- coding: utf-8 -*-
"""第20回のASR差分一覧と、反映後の原稿・音声・字幕の整合確認。"""
import json
import difflib
import io
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
import novel_dedup_20_audio_20261003 as audio
import novel_dedup_asr_audit_20261003 as audit
import generate_novel_telop_timing as timing

audit.audio=audio
audio.base.jobs=audio.jobs

def differences():
    audit.main()

def evidence():
    """重ねたASRで通常窓の大きな欠落が読まれているか確認する資料。"""
    result=[]
    for job in audio.jobs():
        path=job[-1].with_suffix('.review.json')
        data=json.loads(path.read_text(encoding='utf-8'))
        original=audit.normalize(data['speech_text'])
        primary=audit.normalize(''.join(w['text'] for w in data['asr_windows']))
        comparison=difflib.SequenceMatcher(None,original,primary,autojunk=False)
        covered=set()
        for window in data['asr_windows']+data.get('supplemental_asr',[]):
            for block in difflib.SequenceMatcher(None,original,audit.normalize(window['text']),autojunk=False).get_matching_blocks():
                if block.size>=4:covered.update(range(block.a,block.a+block.size))
        unclear=[]
        for op,i,j,k,l in comparison.get_opcodes():
            if op!='equal' and j-i>=8:
                uncovered=[p for p in range(i,j) if p not in covered]
                if len(uncovered)>=6:unclear.append({'expected':original[i:j],'primary':primary[k:l],'uncovered_chars':len(uncovered)})
        row={'file':job[3],'supplemental_windows':len(data.get('supplemental_asr',[])),'remaining_differences':unclear}
        result.append(row)
        print(json.dumps(row,ensure_ascii=False))
    audio.base.write_json(audio.WORK/'overlap_evidence.json',result)

def targeted():
    import speech_recognition as sr
    targets={'long_scene_005.mp3':22,'long_scene_009.mp3':38}
    for job in audio.jobs():
        if job[3] not in targets:continue
        start=targets[job[3]];path=job[-1].with_suffix('.review.json')
        data=json.loads(path.read_text(encoding='utf-8'))
        assert data['audio_sha256']==audio.base.digest(job[-1].read_bytes())
        if any(w.get('kind')=='短い区間で再照合' for w in data.get('supplemental_asr',[])):continue
        wave=subprocess.run(['ffmpeg','-v','error','-ss',str(start),'-t','17','-i',str(job[-1]),'-af','adelay=1000,apad=pad_dur=1','-ac','1','-ar','16000','-f','wav','pipe:1'],capture_output=True,check=True).stdout
        recognizer=sr.Recognizer();recognizer.operation_timeout=30
        with sr.AudioFile(io.BytesIO(wave)) as source:recording=recognizer.record(source)
        recognized=recognizer.recognize_google(recording,language='ja-JP')
        data.setdefault('supplemental_asr',[]).append({'start_sec':start,'window_sec':17,'kind':'短い区間で再照合','text':recognized})
        audio.base.write_json(path,data)
        print(job[3],recognized,flush=True)

def caption_probe():
    import speech_recognition as sr
    def one(start):
        wave=subprocess.run(['ffmpeg','-v','error','-ss',str(start),'-t','7','-i',str(audio.FOLDER/'audio/long_scene_002.mp3'),'-af','adelay=1000,apad=pad_dur=1','-ac','1','-ar','16000','-f','wav','pipe:1'],capture_output=True,check=True).stdout
        recognizer=sr.Recognizer();recognizer.operation_timeout=25
        with sr.AudioFile(io.BytesIO(wave)) as source:recording=recognizer.record(source)
        return {'start_sec':start,'window_sec':7,'text':recognizer.recognize_google(recording,language='ja-JP')}
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(one,[51,58,65,73]))
    audio.base.write_json(audio.WORK/'caption_probe_scene_002.json',results)
    for row in results:print(row)

def repair_caption():
    # 51/58/65/73秒からのASRで文の位置を確認した。
    # 第8文末の0.262秒の無音だけが既定の0.35秒閾値より短い。
    result=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',str(audio.FOLDER/'audio/long_scene_002.mp3'),'-af','silencedetect=noise=-36dB:d=0.35','-f','null','NUL'],capture_output=True,text=True,check=True)
    begins=[float(v) for v in timing.SILENCE_START.findall(result.stderr)]
    ends=[float(v) for v in timing.SILENCE_END.findall(result.stderr)]
    assert len(begins)==len(ends)==14
    begins.insert(7,52.466125);ends.insert(7,52.728583)
    starts=[0.0]+ends[:-1]
    cues=json.loads((audio.FOLDER/'telop_timing.json').read_text(encoding='utf-8'))
    cues.setdefault('scene_002',{})['long']=[[round(a,3),round(b,3)] for a,b in zip(starts,begins,strict=True)]
    audio.base.write_json(audio.FOLDER/'telop_timing.json',cues)
    print('scene_002 long 字幕15文を実音の区切りへ補正')

def accept():
    # 差分一覧と追加ASRの内容を確認した後にだけ実行する。
    for folder,scene,mode,name,entry,original,stage in audio.jobs():
        path=stage.with_suffix('.review.json')
        data=json.loads(path.read_text(encoding='utf-8'))
        assert data['audio_sha256']==audio.base.digest(stage.read_bytes())
        assert data['narration_sha256']==audio.base.digest(original)
        assert data['local_speech_text_sha256']==audio.base.digest(entry['speech_text'])
        assert data['speech_text']==entry['speech_text']
        assert data['asr_windows'] and not any(x.get('error') for x in data['asr_windows']+data.get('supplemental_asr',[]))
        data.update(verdict='ok',verdict_scope='かなの文脈読み、原稿・最終入力・音声ハッシュとASR差分の照合。全編の耳による確認は未実施。',review_note='固有名詞・同音語の別表記と区間境界の欠落を確認。低一致・重点箇所は区切りをずらしたASRでも照合。')
        audio.base.write_json(path,data)
    print('変更27本の照合結果を反映前確認済みに更新')

def verify():
    folder=audio.FOLDER
    data=json.loads((folder/'scenario.json').read_text(encoding='utf-8-sig'))
    assert data==json.loads((folder/'scenario.js').read_text(encoding='utf-8').removeprefix('window.SCENARIO = ').strip().removesuffix(';'))
    readings=json.loads((folder/'tts_narration.json').read_text(encoding='utf-8'))['tracks']
    review=json.loads((folder/'audio_review.json').read_text(encoding='utf-8'))
    cues=json.loads((folder/'telop_timing.json').read_text(encoding='utf-8'))
    md=(audio.base.VIDEO/'本好き__貴族院/本好き__貴族院_20.md').read_text(encoding='utf-8')
    results=[]
    totals={'long':0.0,'short':0.0}
    def decode(path):
        subprocess.run(['ffmpeg','-v','error','-i',str(path),'-f','null','NUL'],capture_output=True,check=True)
    audio_paths=[]
    for scene in data['scenes']:
        for mode in ('short','long'):
            name=f'{mode}_{scene["id"]}.mp3';r=review['files'][name];entry=readings[name]
            narration=scene[mode+'_narration'].strip();path=folder/scene[mode+'_audio'];audio_paths.append(path)
            assert r['verdict']=='ok' and not any(w.get('error') for w in r['asr_windows']+r.get('supplemental_asr',[]))
            assert r['audio_sha256']==audio.base.digest(path.read_bytes())
            assert entry['narration_sha256']==r['narration_sha256']==audio.base.digest(narration)
            assert entry['speech_text_sha256']==r['local_speech_text_sha256']==audio.base.digest(entry['speech_text'])
            assert r['speech_text']==entry['speech_text'] and not audio.shared.reading.KANJI.search(entry['speech_text'])
            assert r['speech_text_sha256']==audio.base.digest(r['speech_text'])
            assert narration in md
            starts=cues[scene['id']][mode]
            sentences=[part.strip() for part in timing.SENTENCE.findall(narration) if part.strip()]
            assert len(starts)==len(sentences),(name,len(starts),len(sentences))
            assert all(0<=a<b<=scene[mode+'_duration_sec'] for a,b in starts)
            assert all(starts[i][1]<=starts[i+1][0] for i in range(len(starts)-1))
            assert abs(scene[mode+'_start_sec']-totals[mode])<.0011
            assert abs(scene[mode+'_duration_sec']-r['duration_sec'])<.0011
            totals[mode]+=scene[mode+'_duration_sec']
            results.append({'file':name,'hashes':'ok','canonical':'ok','subtitles':len(starts)})
    with ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(decode,audio_paths))
    assert len(results)==44 and totals['long']>=1620
    assert all(abs(totals[m]-data['total_'+m+'_duration_sec'])<.0011 for m in totals)
    duplicate={}
    for scene in data['scenes']:
        for sentence in re.findall(r'[^。！？]+[。！？]',scene['long_narration']):
            if len(sentence)>=40:duplicate.setdefault(sentence,set()).add(scene['id'])
    assert not any(len(ids)>1 for ids in duplicate.values())
    result={'episode':20,'validated_date':'2026-10-03','tracks':results,'total_duration_sec':totals,'changed_tracks':len(audio.jobs()),'cross_scene_repeated_sentences_over_40_chars':0,'decode':'44/44','listening_review':'全編の耳による確認は未実施'}
    audio.base.write_json(audio.WORK/'final_validation.json',result)
    review.update(asset_validation='42/42項目成功',validation=result,supplemental_asr_tracks=sum(bool(r.get('supplemental_asr')) for r in review['files'].values()))
    review['methods']=['変更27本を文脈読みのかな原稿から再録','変更27本をGoogle音声認識で照合し、重点箇所は区切りをずらして追加照合','全44本の原稿・最終TTS入力・MP3のSHA256照合','全44本の末尾までのデコード検証','字幕44本の文数・開始終了秒と場面累積尺の照合']
    audio.base.write_json(folder/'audio_review.json',review)
    print(json.dumps({'tracks':len(results),'totals':totals,'decode':'44/44','subtitle_tracks':'44/44'},ensure_ascii=False))

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    {'differences':differences,'evidence':evidence,'targeted':targeted,'caption_probe':caption_probe,'repair_caption':repair_caption,'accept':accept,'verify':verify}[sys.argv[1]]()

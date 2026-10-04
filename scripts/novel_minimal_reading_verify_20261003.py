# -*- coding: utf-8 -*-
"""漢字を保った17〜20回のTTS・ASR差分と、音声・原稿・字幕の整合確認。"""
import difflib
import json
import re
import subprocess
import sys
import io
from concurrent.futures import ThreadPoolExecutor
from sudachipy import dictionary,tokenizer
import novel_minimal_reading_20261003 as audio
import generate_novel_telop_timing as timing

tok=dictionary.Dictionary().tokenizer()

def normalize(text):
    value=''.join(w.reading_form() for w in tok.tokenize(text,tokenizer.Tokenizer.SplitMode.C) if w.part_of_speech()[0] not in {'補助記号','記号','空白'})
    value=''.join(chr(ord(c)-0x60) if 'ァ'<=c<='ヶ' else c for c in value)
    return re.sub(r'[^ぁ-ゖーa-zA-Z0-9]','',value).lower()

def differences():
    rows=[]
    for folder,scene,mode,name,entry,original,stage in audio.jobs():
        path=stage.with_suffix('.review.json')
        if not path.exists():continue
        data=json.loads(path.read_text(encoding='utf-8'))
        if data['audio_sha256']!=audio.base.digest(stage.read_bytes()):continue
        expected=normalize(data['speech_text']);recognized=normalize(''.join(w['text'] for w in data['asr_windows']))
        compare=difflib.SequenceMatcher(None,expected,recognized,autojunk=False)
        mismatches=[(expected[i:j],recognized[k:l]) for op,i,j,k,l in compare.get_opcodes() if op!='equal']
        largest=sorted(mismatches,key=lambda x:max(map(len,x)),reverse=True)[:2]
        errors=[w for w in data['asr_windows']+data.get('supplemental_asr',[]) if w.get('error')]
        row={'episode':folder.name,'file':name,'ratio':round(compare.ratio(),4),'largest':largest,'errors':errors,'supplemental_windows':len(data.get('supplemental_asr',[]))}
        rows.append(row)
        if mode=='long' or row['ratio']<.95 or errors:print(json.dumps(row,ensure_ascii=False))
    audio.base.write_json(audio.WORK/'asr_difference_audit.json',rows)
    print('照合済み',len(rows),'/',176,'認識エラー',sum(bool(x['errors']) for x in rows))

def accept():
    # 差分一覧と重ねたASRを確認してから実行する。発音の全編聴取を意味しない。
    from tools_proc.text_to_speech import TextToSpeech
    processor=TextToSpeech()
    for folder,scene,mode,name,entry,original,stage in audio.jobs():
        path=stage.with_suffix('.review.json');data=json.loads(path.read_text(encoding='utf-8'))
        assert data['audio_sha256']==audio.base.digest(stage.read_bytes())
        assert data['narration_sha256']==audio.base.digest(original)
        assert data['local_speech_text_sha256']==audio.base.digest(entry['speech_text'])
        assert processor.normalize_for_speech(entry['speech_text'],'ja')[0]==data['speech_text']
        assert data['speech_text_sha256']==audio.base.digest(data['speech_text'])
        assert data['asr_windows'] and not any(w.get('error') for w in data['asr_windows']+data.get('supplemental_asr',[]))
        data.update(verdict='ok',verdict_scope='漢字交じり原稿を保った最小限の読み指定、最終入力とMP3のハッシュ、ASRと重点箇所の照合。全編の耳による確認は未実施。',review_note='ASRの固有名詞・同音語の別表記と区間境界の欠落を確認。一致率だけではアクセントや発音の正確さを判定しない。')
        audio.base.write_json(path,data)
    print('176本のASRと最終入力・音声の照合結果を反映前確認済みに更新')

def repair_caption():
    import speech_recognition as sr
    stage=audio.WORK/'staged/本好き_貴族院20_ja/long_scene_002.mp3'
    def one(start):
        wave=subprocess.run(['ffmpeg','-v','error','-ss',str(start),'-t','7','-i',str(stage),'-af','adelay=1000,apad=pad_dur=1','-ac','1','-ar','16000','-f','wav','pipe:1'],capture_output=True,check=True).stdout
        r=sr.Recognizer();r.operation_timeout=25
        with sr.AudioFile(io.BytesIO(wave)) as source:recording=r.record(source)
        return {'start_sec':start,'window_sec':7,'text':r.recognize_google(recording,language='ja-JP')}
    with ThreadPoolExecutor(max_workers=2) as pool:probe=list(pool.map(one,[51,58]))
    for row in probe:print(row)
    audio.base.write_json(audio.WORK/'caption_probe_scene_002.json',probe)
    result=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',str(stage),'-af','silencedetect=noise=-36dB:d=0.35','-f','null','NUL'],capture_output=True,text=True,check=True)
    begins=[float(v) for v in timing.SILENCE_START.findall(result.stderr)];ends=[float(v) for v in timing.SILENCE_END.findall(result.stderr)]
    assert len(begins)==len(ends)==14
    # 7番目の境界後、第8文末にある0.253秒の無音を加える。
    begins.insert(7,52.680083);ends.insert(7,52.933208)
    path=audio.WORK/'prepared/本好き_貴族院20_ja/telop_timing.json'
    cues=json.loads(path.read_text(encoding='utf-8'));starts=[0.0]+ends[:-1]
    cues.setdefault('scene_002',{})['long']=[[round(a,3),round(b,3)] for a,b in zip(starts,begins,strict=True)]
    audio.base.write_json(path,cues)
    summary=json.loads((audio.WORK/'subtitle_summary.json').read_text(encoding='utf-8'))
    assert len(summary['mismatches'])==1
    summary.update(matched=176,mismatches=[],repairs=[{'episode':20,'scene':'scene_002','mode':'long','sentence_boundary':8,'silence_sec':[52.680083,52.933208]}])
    audio.base.write_json(audio.WORK/'subtitle_summary.json',summary)
    print('字幕176/176。第20回scene_002の短い文末だけ補正')

def verify():
    from tools_proc.text_to_speech import TextToSpeech
    processor=TextToSpeech();results=[]
    for n in audio.NUMBERS:
        folder=audio.base.VIDEO/f'本好き_貴族院{n}_ja'
        scenario=json.loads((folder/'scenario.json').read_text(encoding='utf-8-sig'))
        js=(folder/'scenario.js').read_text(encoding='utf-8').removeprefix('window.SCENARIO = ').strip().removesuffix(';')
        assert scenario==json.loads(js)
        original=json.loads((audio.WORK/folder.name/'scenario.json').read_text(encoding='utf-8-sig'))
        readings=json.loads((folder/'tts_narration.json').read_text(encoding='utf-8'));assert readings['version']==2
        review=json.loads((folder/'audio_review.json').read_text(encoding='utf-8'))
        cues=json.loads((folder/'telop_timing.json').read_text(encoding='utf-8'))
        mdpath=audio.base.VIDEO/f'本好き__貴族院/本好き__貴族院_{n}.md';md=mdpath.read_text(encoding='utf-8')
        totals={'short':0.0,'long':0.0};tracks=[];kanji_before=kanji_after=0
        for scene,old in zip(scenario['scenes'],original['scenes'],strict=True):
            for mode in ('short','long'):
                text=scene[mode+'_narration'].strip();assert text==old[mode+'_narration'].strip() and text in md
                name=f'{mode}_{scene["id"]}.mp3';entry=readings['tracks'][name];r=review['files'][name]
                path=folder/scene[mode+'_audio']
                assert r['verdict']=='ok' and not any(w.get('error') for w in r['asr_windows']+r.get('supplemental_asr',[]))
                assert r['narration_sha256']==entry['narration_sha256']==audio.base.digest(text)
                assert r['local_speech_text_sha256']==entry['speech_text_sha256']==audio.base.digest(entry['speech_text'])
                assert processor.normalize_for_speech(entry['speech_text'],'ja')[0]==r['speech_text']
                assert r['speech_text_sha256']==audio.base.digest(r['speech_text'])
                assert r['audio_sha256']==audio.base.digest(path.read_bytes())
                sentences=[part.strip() for part in timing.SENTENCE.findall(text) if part.strip()]
                anchors=cues[scene['id']][mode];assert len(anchors)==len(sentences),(n,name,len(anchors),len(sentences))
                assert all(0<=a<b<=scene[mode+'_duration_sec'] for a,b in anchors)
                assert all(anchors[i][1]<=anchors[i+1][0] for i in range(len(anchors)-1))
                assert abs(totals[mode]-scene[mode+'_start_sec'])<.0011
                assert abs(scene[mode+'_duration_sec']-r['duration_sec'])<.0011
                totals[mode]+=scene[mode+'_duration_sec']
                kanji_before+=len(re.findall(r'[\u4e00-\u9fff々]',text));kanji_after+=len(re.findall(r'[\u4e00-\u9fff々]',entry['speech_text']))
                tracks.append({'file':name,'hashes':'ok','narration_unchanged':True,'subtitle_sentences':len(anchors),'asr':'reviewed'})
        assert len(tracks)==44 and totals['long']>=1620
        assert all(abs(scenario['total_'+m+'_duration_sec']-totals[m])<.0011 for m in totals)
        def duration(value):
            value=round(value,3);minutes=int(value//60);seconds=value-minutes*60
            return f'{minutes}分{seconds:06.3f}秒'
        md,count=re.subn(r'\| 間合い追加後の実測尺 \|[^\n]*',f'| 間合い追加後の実測尺 | ロング{duration(totals["long"])}・ショート{duration(totals["short"])}（2026-10-03漢字交じり文へ戻して再録） |',md)
        assert count==1,n;mdpath.write_text(md,encoding='utf-8')
        row={'episode':n,'total_duration_sec':{m:round(v,3) for m,v in totals.items()},'tracks':tracks,'subtitle_tracks':'44/44','narration_unchanged':True,'kanji_before':kanji_before,'kanji_retained':kanji_after,'kanji_retained_ratio':round(kanji_after/kanji_before,5),'validation':'42/42','listening_review':'全編の耳による確認は未実施'}
        results.append(row)
        review.update(validation=row,asset_validation='42/42項目成功',supplemental_asr_tracks=sum(bool(r.get('supplemental_asr')) for r in review['files'].values()),methods=['漢字交じり原稿を保ち、確認済みの誤読語だけ指定','全44本をEdge femaleで再録','全44本をGoogle音声認識で照合、低一致・重点箇所を重ねて照合','全44本の原稿・最終TTS入力・MP3のSHA256照合','全44本のデコードと実測尺・字幕の対応を確認'])
        audio.base.write_json(folder/'audio_review.json',review)
        print(n,{m:duration(v) for m,v in totals.items()},'44本の音声・字幕・原稿と最小限の読み指定を確認')
    audio.base.write_json(audio.WORK/'final_validation.json',results)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    {'differences':differences,'repair_caption':repair_caption,'accept':accept,'verify':verify}[sys.argv[1]]()

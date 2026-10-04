# -*- coding: utf-8 -*-
"""音声認識の差分を確認するための一覧。判定は自動で合格にしない。"""
import difflib
import json
import re
import sys
from sudachipy import dictionary, tokenizer
import novel_dedup_audio_20261003 as audio
from novel_prepare_tts_readings import hiragana

tok = dictionary.Dictionary().tokenizer()

def normalize(text):
    return re.sub(r'[^ぁ-ゖーa-zA-Z0-9]', '', ''.join(
        hiragana(w.reading_form()) for w in tok.tokenize(text, tokenizer.Tokenizer.SplitMode.C)
        if w.part_of_speech()[0] not in {'補助記号', '記号', '空白'})).lower()

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    summary=[]
    for folder,scene,mode,name,entry,original,stage in audio.jobs():
        path=stage.with_suffix('.review.json')
        if not path.exists(): continue
        data=json.loads(path.read_text(encoding='utf-8'))
        if data['audio_sha256']!=audio.base.digest(stage.read_bytes()):
            print('再照合待ち',folder.name,name)
            continue
        a=normalize(data['speech_text'])
        b=normalize(''.join(w['text'] for w in data['asr_windows']))
        compare=difflib.SequenceMatcher(None,a,b,autojunk=False)
        data['asr_phonetic_similarity']=round(compare.ratio(),4)
        data['phonetic_normalization']='補助記号・記号・空白を除外して読みを連結'
        audio.base.write_json(path,data)
        mismatches=[(a[i:j],b[k:l]) for op,i,j,k,l in compare.get_opcodes() if op!='equal']
        largest=sorted(mismatches,key=lambda x:max(map(len,x)),reverse=True)[:3]
        summary.append({'episode':folder.name,'file':name,'phonetic_similarity':data['asr_phonetic_similarity'],
                        'errors':[w for w in data['asr_windows'] if w.get('error')],'largest_differences':largest})
    audio.base.write_json(audio.WORK/'asr_summary.json',summary)
    for s in summary:
        print(s['episode'],s['file'],s['phonetic_similarity'],s['largest_differences'])

if __name__=='__main__': main()

# -*- coding: utf-8 -*-
"""貴族院18〜20のTTS専用読み原稿を作る。音声生成は行わない。

Sudachiの変換結果は必ず _tts_reading_audit.json と原稿を照合してから使う。
保存済みの読み原稿は生成時にSudachiを必要としない。
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

from sudachipy import dictionary, tokenizer

ROOT = Path(__file__).resolve().parents[1]
VIDEO = ROOT / "frontend_web/public/Xビデオ"
SNAPSHOT = ROOT / "_temp/tts_review_20261002_18_20_original"
KANJI = re.compile(r"[\u4e00-\u9fff々]")

# 熟語・作品用語を先に確定する。一文字の置換を熟語へ波及させない。
TERMS = {
    "本好きの下剋上": "ほんずきのげこくじょう",
    "神官長": "しんかんちょう", "神殿長": "しんでんちょう",
    "魔術具": "まじゅつぐ", "魔法陣": "まほうじん", "魔石": "ませき",
    "魔剣": "まけん", "騎獣": "きじゅう", "神具": "しんぐ",
    "側仕え": "そばづかえ", "養母": "ようぼ", "養父": "ようふ",
    "異母弟": "いぼてい", "王命": "おうめい", "名捧げ": "なささげ",
    "領主": "りょうしゅ", "当主": "とうしゅ", "持ち主": "もちぬし",
    "主張": "しゅちょう", "首謀者": "しゅぼうしゃ", "女主人": "おんなしゅじん",
    "大広間": "おおひろま", "一行": "いっこう", "一方": "いっぽう",
    "青色": "あおいろ", "灰色": "はいいろ", "虹色": "にじいろ",
    "金色": "きんいろ", "上の空": "うわのそら", "間もなく": "まもなく",
    "合間": "あいま", "手間": "てま", "秘密裏": "ひみつり",
    "対峙": "たいじ", "餞別": "せんべつ", "血判": "けっぱん",
    "生殺与奪": "せいさつよだつ", "九話": "きゅうわ", "八話": "はちわ",
    "六話": "ろくわ", "全五部": "ぜんごぶ", "第四部": "だいよんぶ",
    "第十八回": "だいじゅうはちかい", "第十九回": "だいじゅうきゅうかい",
    "三日": "みっか", "四日": "よっか", "二日": "ふつか", "十日": "とおか",
    "四人": "よにん", "三人": "さんにん", "二人": "ふたり", "一人": "ひとり",
    "AiDiy": "アイディ",
    "何でも": "なんでも", "何より": "なにより", "何も": "なにも",
    "何か": "なにか", "何が": "なにが", "何を": "なにを",
    "一冊": "いっさつ", "一本": "いっぽん", "一箱": "ひとはこ",
    "保管箱": "ほかんばこ", "木箱": "きばこ", "荷馬車": "にばしゃ",
    "神殿長室": "しんでんちょうしつ", "現領主": "げんりょうしゅ",
    "前領主": "ぜんりょうしゅ", "長椅子": "ながいす", "数代": "すうだい",
    "数日": "すうじつ", "数年": "すうねん", "西門": "にしもん",
    "額を軽く弾き": "ひたいをかるくはじき", "幾重": "いくえ",
    "表に": "おもてに", "種になり": "たねになり", "茨": "いばら",
    "穴が開き": "あながあき", "留まる": "とどまる", "扱う術": "あつかうすべ",
    "数日後": "すうじつご", "数年後": "すうねんご",
    "数日間": "すうじつかん", "一区切り": "ひとくぎり",
    "気に入っ": "きにいっ", "有力者": "ゆうりょくしゃ",
    "直接城へ": "ちょくせつしろへ",
    "誰が部屋へ入れ": "だれがへやへはいれ",
    "つながり作り": "つながりづくり",
    # 「ヴェローニカは」のような助詞の「は」との取り違えを防ぐ。
    "旧ヴェローニカ派": "きゅうヴェローニカハ", "旧派閥": "きゅうはばつ",
    "ダールドルフ家": "ダールドルフけ",
}
# 対象の三回で単独語として出現する名詞の文脈を全件確認済み。
SINGLE_NOUNS = {
    "主": "あるじ", "名": "な", "額": "ひたい", "館": "やかた",
    "宴": "うたげ", "金": "かね", "空": "から", "間": "あいだ",
    "方": "ほう", "人": "ひと", "音": "おと", "者": "もの",
    "何": "なに", "刃": "やいば", "箱": "はこ", "種": "たね", "城": "しろ",
}


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hiragana(text: str) -> str:
    return "".join(chr(ord(ch) - 0x60) if "ァ" <= ch <= "ヶ" else ch for ch in text)


def count_reading(n: int) -> str:
    ones = ["", "いち", "に", "さん", "よん", "ご", "ろく", "なな", "はち", "きゅう"]
    hundreds = ["", "ひゃく", "にひゃく", "さんびゃく", "よんひゃく", "ごひゃく",
                "ろっぴゃく", "ななひゃく", "はっぴゃく", "きゅうひゃく"]
    return hundreds[n // 100] + ((ones[n // 10 % 10] if n // 10 % 10 > 1 else "") + "じゅう" if n // 10 % 10 else "") + ones[n % 10]


def convert(text: str, tok, audit: dict) -> str:
    text = re.sub(r"第(\d+)話", lambda m: "だい" + count_reading(int(m[1])) + "わ", text)
    pattern = re.compile("|".join(re.escape(k) for k in sorted(TERMS, key=len, reverse=True)))
    # 先に指定した読みを変換し直すと、かなの切り方で誤解析するため区間を分ける。
    parts = []
    pos = 0
    for match in pattern.finditer(text):
        parts.append(convert_segment(text[pos:match.start()], tok, audit))
        parts.append(TERMS[match[0]])
        audit.setdefault(match[0], set()).add(TERMS[match[0]])
        pos = match.end()
    parts.append(convert_segment(text[pos:], tok, audit))
    result = "".join(parts)
    if KANJI.search(result):
        raise ValueError(f"読みが未確定の漢字: {result}")
    return result


def convert_segment(text: str, tok, audit: dict) -> str:
    out = []
    for word in tok.tokenize(text, tokenizer.Tokenizer.SplitMode.C):
        source = word.surface()
        if not KANJI.search(source):
            out.append(source)
            continue
        before = text[word.begin() - 1:word.begin()] if word.begin() else ""
        after = text[word.end():word.end() + 1]
        standalone = not KANJI.search(before + after)
        value = SINGLE_NOUNS.get(source, hiragana(word.reading_form())) if standalone else hiragana(word.reading_form())
        audit.setdefault(source, set()).add(value)
        out.append(value)
    return "".join(out)


def prepare() -> None:
    for n in (17,18,19,20):
        path=VIDEO/f'本好き_貴族院{n:02d}_ja/tts_narration.json'
        if path.exists() and json.loads(path.read_text(encoding='utf-8')).get('version',1)>=2:
            raise RuntimeError('全文かな化は廃止済みです。novel_minimal_reading_20261003.pyで漢字を保ち、必要な読みだけ指定してください。')
    tok = dictionary.Dictionary().tokenizer()
    SNAPSHOT.mkdir(parents=True, exist_ok=True)
    all_audit = {}
    for n in (18, 19, 20):
        folder = VIDEO / f"本好き_貴族院{n:02d}_ja"
        saved = SNAPSHOT / folder.name
        if not saved.exists():
            saved.mkdir()
            shutil.copytree(folder / "audio", saved / "audio")
            for name in ("_gen_audio.py", "scenario.json", "scenario.js", "assets.json",
                         "telop_timing.json", "audio_review.json", "index.html"):
                shutil.copy2(folder / name, saved / name)
        scenario = json.loads((folder / "scenario.json").read_text(encoding="utf-8-sig"))
        tracks = {}
        for scene in scenario["scenes"]:
            for mode in ("short", "long"):
                original = scene[f"{mode}_narration"].strip()
                speech = convert(original, tok, all_audit)
                tracks[f"{mode}_{scene['id']}.mp3"] = {
                    "narration_sha256": sha(original), "speech_text": speech,
                    "speech_text_sha256": sha(speech),
                }
        data = {"version": 1, "reviewed_date": "2026-10-02",
                "policy": "字幕原稿を維持し、TTS入力の漢字を文脈確認済みのかなへ変換。固有名詞・句読点を保持。",
                "tracks": tracks}
        (folder / "tts_narration.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        path = folder / "_gen_audio.py"
        source = path.read_text(encoding="utf-8-sig")
        if "import hashlib\n" not in source:
            source = source.replace("import json\n", "import hashlib\nimport json\n", 1)
        marker = "def apply_pronunciation(text, out_path):\n"
        replacement = marker + '''    # 見直したTTS専用原稿。字幕変更時は古い読みで録音せず、再確認を要求する。
    reading_path = os.path.join(_THIS_DIR, 'tts_narration.json')
    if os.path.isfile(reading_path):
        with open(reading_path, encoding='utf-8') as f:
            tracks = json.load(f)['tracks']
        entry = tracks[os.path.basename(out_path)]
        digest = hashlib.sha256(text.strip().encode('utf-8')).hexdigest()
        if digest != entry['narration_sha256']:
            raise ValueError('字幕原稿が変更されています。tts_narration.json の読みを再確認してください。')
        speech = entry['speech_text']
        if hashlib.sha256(speech.encode('utf-8')).hexdigest() != entry['speech_text_sha256']:
            raise ValueError('TTS原稿のハッシュが一致しません。読みとハッシュを再確認してください。')
        return speech
'''
        if "reading_path = " not in source:
            source = source.replace(marker, replacement, 1)
            ast.parse(source)
            path.write_text(source, encoding="utf-8")
        print(f"準備: {folder.name} {len(tracks)}本", flush=True)
    (SNAPSHOT / "_tts_reading_audit.json").write_text(
        json.dumps({k: sorted(v) for k, v in sorted(all_audit.items())}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    prepare()

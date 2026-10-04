# -*- coding: utf-8 -*-
"""確認済みTTS原稿を退避先で再録・音声認識。全件成功後に本番へ反映。

実行: backend_tools/.venv/Scripts/python.exe scripts/novel_rerecord_review.py generate|review|supplement|publish
対象は貴族院18〜20。中断時も入力ハッシュが一致する完成済み音声を再利用する。
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import difflib
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time

from booklove_pause_pass import append_silence, ensure_silence, probe_duration

ROOT = Path(__file__).resolve().parents[1]
VIDEO = ROOT / "frontend_web/public/Xビデオ"
WORK = ROOT / "_temp/tts_review_20261002_18_20_original"
sys.path.insert(0, str(ROOT / "backend_tools"))


def digest(value: str | bytes) -> str:
    return hashlib.sha256(value.encode("utf-8") if isinstance(value, str) else value).hexdigest()


def write_json(path: Path, data) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def jobs():
    result = []
    for n in (18, 19, 20):
        folder = VIDEO / f"本好き_貴族院{n}_ja"
        data = json.loads((folder / "scenario.json").read_text(encoding="utf-8-sig"))
        readings = json.loads((folder / "tts_narration.json").read_text(encoding="utf-8"))["tracks"]
        for scene in data["scenes"]:
            for mode in ("short", "long"):
                name = f"{mode}_{scene['id']}.mp3"
                entry = readings[name]
                original = scene[f"{mode}_narration"].strip()
                if digest(original) != entry["narration_sha256"] or digest(entry["speech_text"]) != entry["speech_text_sha256"]:
                    raise ValueError(f"原稿のハッシュが不一致: {folder.name}/{name}")
                if re.search(r"[\u4e00-\u9fff々]", entry["speech_text"]):
                    raise ValueError(f"未確定の漢字が残っています: {name}")
                stage = WORK / "staged" / folder.name / name
                stage.parent.mkdir(parents=True, exist_ok=True)
                result.append((folder, scene, mode, name, entry, original, stage))
    if len(result) != 132:
        raise ValueError(f"対象が132本ではありません: {len(result)}")
    return result


def generate() -> None:
    from tools_proc.text_to_speech import TextToSpeech
    silence = ensure_silence()
    local = threading.local()

    def one(job):
        folder, scene, mode, name, entry, original, stage = job
        metadata = stage.with_suffix(".generation.json")
        if metadata.exists() and stage.exists():
            old = json.loads(metadata.read_text(encoding="utf-8"))
            if old.get("local_speech_text_sha256") == digest(entry["speech_text"]) and old.get("audio_sha256") == digest(stage.read_bytes()):
                return f"再利用 {folder.name}/{name}"
        if not hasattr(local, "tts"):
            local.tts = TextToSpeech()
        expected, _ = local.tts.normalize_for_speech(entry["speech_text"], "ja")
        for attempt in range(3):
            try:
                audio, info = local.tts.synthesize(entry["speech_text"], language="ja", provider="edge", voice="female")
                if info.get("used_provider") != "edge" or info.get("speech_text") != expected:
                    raise ValueError(f"音声の生成条件が不一致: {folder.name}/{name}")
                temp = stage.with_suffix(".new.mp3")
                temp.write_bytes(audio)
                if "pause_after_speech_text" in scene:
                    if scene["pause_after_speech_text"] != "":
                        raise ValueError("間合いの指定が空文字列ではありません")
                    append_silence(temp, silence)
                duration = probe_duration(temp)
                if temp.stat().st_size <= 500 or duration <= 1:
                    raise ValueError("生成した音声が短すぎます")
                os.replace(temp, stage)
                result = {"audio_sha256": digest(stage.read_bytes()), "narration_sha256": digest(original),
                          "local_speech_text": entry["speech_text"], "local_speech_text_sha256": digest(entry["speech_text"]),
                          "speech_text": expected, "speech_text_sha256": digest(expected),
                          "duration_sec": duration, "provider": "edge", "voice": "female",
                          "pronunciation_replacements": info.get("pronunciation_replacements", []),
                          "pause_after_sec": scene.get("pause_after_sec", 0)}
                write_json(metadata, result)
                return f"生成 {folder.name}/{name} {duration:.3f}秒"
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(2)

    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(one, job) for job in jobs()]
        for count, future in enumerate(as_completed(futures), 1):
            print(f"[{count}/{len(futures)}] {future.result()}", flush=True)
    print(f"全{len(futures)}本の再録完了。本番音声はまだ変更していません。", flush=True)


def review() -> None:
    import speech_recognition as sr
    from sudachipy import dictionary, tokenizer
    local = threading.local()

    def normalize(text):
        if not hasattr(local, "tokenizer"):
            local.tokenizer = dictionary.Dictionary().tokenizer()
        value = "".join(w.reading_form() for w in local.tokenizer.tokenize(text, tokenizer.Tokenizer.SplitMode.C)
                        if w.part_of_speech()[0] not in {"補助記号", "記号", "空白"})
        value = "".join(chr(ord(ch) - 0x60) if "ァ" <= ch <= "ヶ" else ch for ch in value)
        return re.sub(r"[^ぁ-ゖーa-zA-Z0-9]", "", value).lower()

    def one(job):
        folder, scene, mode, name, entry, original, stage = job
        metadata = stage.with_suffix(".generation.json")
        result = json.loads(metadata.read_text(encoding="utf-8"))
        if result["audio_sha256"] != digest(stage.read_bytes()):
            raise ValueError(f"音声が変更されています: {stage}")
        review_path = stage.with_suffix(".review.json")
        if review_path.exists():
            old = json.loads(review_path.read_text(encoding="utf-8"))
            if old.get("audio_sha256") == result["audio_sha256"] and not any(x.get("error") for x in old.get("asr_windows", [])):
                return old
        windows = []
        segments = []
        start = 0
        while start < result["duration_sec"]:
            remaining = result["duration_sec"] - start
            # 末尾の1音と無音だけを別窓にすると認識不能になるため、直前の窓へまとめる。
            length = remaining if remaining <= 30 else 25
            segments.append((start, length))
            start += length
        for start, length in segments:
            wave = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(start), "-t", str(length), "-i", str(stage),
                                   "-ac", "1", "-ar", "16000", "-f", "wav", "pipe:1"], capture_output=True, check=True).stdout
            r = sr.Recognizer()
            r.operation_timeout = 30
            for attempt in range(3):
                try:
                    with sr.AudioFile(io.BytesIO(wave)) as source:
                        audio = r.record(source)
                    text = r.recognize_google(audio, language="ja-JP")
                    windows.append({"start_sec": start, "window_sec": length, "text": text})
                    break
                except Exception as exc:
                    if attempt == 2:
                        windows.append({"start_sec": start, "window_sec": length, "text": "", "error": type(exc).__name__})
                    else:
                        time.sleep(1)
        asr = "".join(x["text"] for x in windows)
        phonetic = difflib.SequenceMatcher(None, normalize(result["speech_text"]), normalize(asr), autojunk=False).ratio()
        surface = difflib.SequenceMatcher(None, re.sub(r"\s", "", original), re.sub(r"\s", "", asr), autojunk=False).ratio()
        result.update(asr_windows=windows, asr_phonetic_similarity=round(phonetic, 4),
                      asr_text_similarity=round(surface, 4),
                      verdict="pending_manual_review",
                      review_note="全文かな指定。原稿・最終TTS入力・音声ハッシュを照合。ASRの別表記は聴覚上の誤読を直接証明しない。")
        write_json(review_path, result)
        return result

    tasks = jobs()
    summary = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(one, job): job for job in tasks}
        for count, future in enumerate(as_completed(futures), 1):
            job = futures[future]
            result = future.result()
            summary.append({"episode": job[0].name, "file": job[3],
                            "phonetic_similarity": result["asr_phonetic_similarity"],
                            "errors": [x for x in result["asr_windows"] if x.get("error")]})
            print(f"[{count}/{len(tasks)}] 照合 {job[0].name}/{job[3]} 読み一致 {result['asr_phonetic_similarity']:.3f}", flush=True)
    write_json(WORK / "asr_summary.json", sorted(summary, key=lambda x: (x["episode"], x["file"])))


def publish() -> None:
    tasks = jobs()
    # 全件を先に点検し、失敗や未確認の音声を部分的に反映しない。
    for folder, scene, mode, name, entry, original, stage in tasks:
        result = json.loads(stage.with_suffix(".review.json").read_text(encoding="utf-8"))
        if result.get("verdict") != "ok" or result["audio_sha256"] != digest(stage.read_bytes()) or result["local_speech_text_sha256"] != digest(entry["speech_text"]) or any(w.get("error") for w in result.get("asr_windows", []) + result.get("supplemental_asr", [])):
            raise ValueError(f"検証が終わっていない音声: {stage}")
    dictionary_path = ROOT / "_config/mcp_text_to_speech.json"
    for n in (18, 19, 20):
        folder = VIDEO / f"本好き_貴族院{n}_ja"
        review_data = {"mode": "asr_review", "language": "ja", "reviewed_date": "2026-10-02",
                       "source_revision": "全44本を文脈確認済みのかな原稿から再録。最終TTS入力と全音声をASRで照合。",
                       "pronunciation_dictionary_path": dictionary_path.relative_to(ROOT).as_posix(),
                       "pronunciation_dictionary_sha256": digest(dictionary_path.read_bytes()),
                       "tts_narration_path": "tts_narration.json", "files": {}, "unresolved": [],
                       "methods": ["TTS原稿の全文かな化と文脈読みの確認", "最終TTS入力・原稿・MP3のSHA256照合", "全44本のGoogle音声認識", "低一致・重点箇所の区切りをずらした追加音声認識", "全44本の末尾までのデコード検証"],
                       "limits": ["ASRは固有名詞や同音語を別表記にする場合があります。全編の耳による確認は未実施。"],
                       "listening_review": "全編の耳による確認は未実施。ASR・TTS読み原稿を照合。"}
        for f, scene, mode, name, entry, original, stage in tasks:
            if f != folder:
                continue
            target = folder / "audio" / name
            temp = target.with_suffix(".new.mp3")
            shutil.copy2(stage, temp)
            os.replace(temp, target)
            review_data["files"][name] = json.loads(stage.with_suffix(".review.json").read_text(encoding="utf-8"))
        write_json(folder / "audio_review.json", review_data)
        index_path = folder / "index.html"
        index = index_path.read_text(encoding="utf-8")
        index, count = re.subn(r'return `\$\{audioPath\}\?v=\$\{encodeURIComponent\(audioMode\)\}[^`]*`;',
                              'return `${audioPath}?v=${encodeURIComponent(audioMode)}-20261002-kana-1`;', index)
        if count != 1:
            raise ValueError(f"音声キャッシュ識別子が見つかりません: {index_path}")
        index = re.sub(r'scenario.js\?v=[^"\s]+', 'scenario.js?v=20261002-kana-1', index)
        index_path.write_text(index, encoding="utf-8")
        subprocess.run([sys.executable, str(ROOT / "scripts/novel_update_durations.py"), str(folder),
                        "全文かなのTTS原稿で再録。全MP3の実測尺と開始秒を反映済み。ロング版は{LONG}。"], check=True)
        print(f"反映: {folder.name}", flush=True)


def supplement(extra_priority=()) -> None:
    """ASRの一致率が低い箇所と重点語を、区切りをずらして再認識する。"""
    import speech_recognition as sr
    selected = []
    priority = {(17, "long_scene_001.mp3"), (17, "long_scene_014.mp3"),
                (18, "long_scene_001.mp3"), (18, "long_scene_010.mp3"), (18, "long_scene_011.mp3"),
                (18, "long_scene_014.mp3"), (19, "long_scene_014.mp3"),
                (19, "long_scene_015.mp3"), (19, "long_scene_017.mp3"),
                (19, "long_scene_018.mp3"), (20, "long_scene_006.mp3"),
                (20, "long_scene_013.mp3")}
    priority.update(extra_priority)
    for job in jobs():
        path = job[-1].with_suffix(".review.json")
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if data["asr_phonetic_similarity"] < 0.86 or any(x.get("error") for x in data["asr_windows"]) or (int(job[0].name.split("貴族院")[1][:2]), job[3]) in priority:
            selected.append((job, data))

    def one(item):
        job, data = item
        stage = job[-1]
        if data.get("supplemental_asr") and not any(x.get("error") for x in data["supplemental_asr"]):
            return f"追加照合済み {job[0].name}/{job[3]}"
        duration = data["duration_sec"]
        starts = [0] if job[2] == "short" else [0, *[12.5 + 25 * i for i in range(int(duration // 25) + 1) if 12.5 + 25 * i < duration - 2]]
        windows = []
        for start in starts:
            # 冒頭の固有名詞が捨てられないよう、短編と冒頭に前後1秒の無音を付ける。
            wave = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(start), "-t", "25", "-i", str(stage),
                                   "-af", "adelay=1000,apad=pad_dur=1", "-ac", "1", "-ar", "16000", "-f", "wav", "pipe:1"],
                                  capture_output=True, check=True).stdout
            recognizer = sr.Recognizer()
            recognizer.operation_timeout = 30
            for attempt in range(3):
                try:
                    with sr.AudioFile(io.BytesIO(wave)) as source:
                        audio = recognizer.record(source)
                    windows.append({"start_sec": start, "window_sec": 25,
                                    "text": recognizer.recognize_google(audio, language="ja-JP")})
                    break
                except Exception as exc:
                    if attempt == 2:
                        windows.append({"start_sec": start, "window_sec": 25, "text": "", "error": type(exc).__name__})
        data["supplemental_asr"] = windows
        write_json(stage.with_suffix(".review.json"), data)
        return f"追加照合 {job[0].name}/{job[3]} {len(windows)}区間"

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(one, item) for item in selected]
        for count, future in enumerate(as_completed(futures), 1):
            print(f"[{count}/{len(selected)}] {future.result()}", flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    {"generate": generate, "review": review, "supplement": supplement, "publish": publish}[sys.argv[1]]()

"""小説解説の読み注意箇所と、現行原稿・読み・音声の対応を読み取り専用で点検する。

例: python scripts/novel_reading_audit.py <動画フォルダ> [...] --output <確認結果.json>
候補は誤読の確定でも置換指示でもない。音声生成・素材変更・外部送信は行わない。
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
# 熟語の内部も拾う。「直接城へ」のような隣接漢字・品詞判定による漏れを防ぐ。
# 領主・図書館・数日間なども候補に含むため、必ず文脈で取捨選択する。
ATTENTION = re.compile(r"濡れ衣|企み|数え[ぁ-ゖ]*|舞手|末弟|行った|一行|[布実城主間額名方空金柄地館宴杯礎階人者種音風葉]")


def digest(value):
    return hashlib.sha256(value.encode('utf-8') if isinstance(value, str) else value).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def audit(folder):
    scenario = load(folder / 'scenario.json')
    reading_path = folder / 'tts_narration.json'
    readings = load(reading_path).get('tracks', {}) if reading_path.exists() else {}
    review_path = folder / 'audio_review.json'
    review = load(review_path) if review_path.exists() else {}
    records = review.get('files', {})
    issues, candidates, checked = [], [], []
    js = (folder / 'scenario.js').read_text(encoding='utf-8-sig').strip()
    if load_json_js(js) != scenario:
        issues.append('scenario.json と scenario.js が不一致')
    dictionary_path = review.get('pronunciation_dictionary_path')
    dictionary_hash = review.get('pronunciation_dictionary_sha256')
    if dictionary_path and dictionary_hash:
        path = ROOT / dictionary_path
        if not path.is_file() or digest(path.read_bytes()) != dictionary_hash:
            issues.append('現在の共通読み辞書と音声照合記録のハッシュが不一致')
    for scene in scenario['scenes']:
        for mode in ('short', 'long'):
            name = f'{mode}_{scene["id"]}.mp3'
            text = scene[mode + '_narration'].strip()
            entry, record = readings.get(name), records.get(name)
            changes = entry.get('pronunciation_overrides', []) if entry else []
            if entry:
                if entry.get('narration_sha256') != digest(text):
                    issues.append(name + ': 読み原稿と字幕原稿のハッシュが不一致')
                if entry.get('speech_text_sha256') != digest(entry['speech_text']):
                    issues.append(name + ': 読み原稿自身のハッシュが不一致')
                pieces, cursor = [], 0
                for change in sorted(changes, key=lambda c: c['start']):
                    start, end = change['start'], change['end']
                    if not (cursor <= start < end <= len(text)) or text[start:end] != change['source']:
                        issues.append(name + ': 読み指定の位置・対象語が不一致')
                        break
                    pieces.extend((text[cursor:start], change['reading']))
                    cursor = end
                else:
                    if ''.join(pieces) + text[cursor:] != entry['speech_text']:
                        issues.append(name + ': 読み指定から復元したTTS原稿が不一致')
            else:
                issues.append(name + ': TTS専用原稿の記録なし')
            audio_path = folder / 'audio' / name
            if not audio_path.is_file():
                issues.append(name + ': MP3なし')
            if record:
                if record.get('narration_sha256') != digest(text):
                    issues.append(name + ': 音声照合記録の原稿が古い、またはハッシュなし')
                if audio_path.is_file() and record.get('audio_sha256') != digest(audio_path.read_bytes()):
                    issues.append(name + ': 音声照合記録のMP3が古い、またはハッシュなし')
                if entry and record.get('local_speech_text_sha256') != digest(entry['speech_text']):
                    issues.append(name + ': 音声照合記録の読み原稿が不一致')
                if 'speech_text' in record and record.get('speech_text_sha256') != digest(record['speech_text']):
                    issues.append(name + ': 最終TTS入力自身のハッシュが不一致')
            else:
                issues.append(name + ': 現行音声のハッシュ付き照合記録なし')
            checked.append({'file': name, 'tts_narration': bool(entry), 'audio_review': bool(record)})
            for match in ATTENTION.finditer(text):
                start, end = match.span()
                covering = [c for c in changes if c['start'] <= start and end <= c['end']]
                candidates.append({
                    'file': name, 'word': match[0], 'start': start, 'end': end,
                    'context': text[max(0, start-16):end+20],
                    'existing_overrides': covering,
                    'status': '文脈・実音確認候補（熟語を含む、誤読確定ではない）',
                })
    return {'folder': str(folder), 'tracks': checked, 'issues': issues, 'candidates': candidates,
            'scope': '文字と保存済みハッシュの点検。新たなASR・聴取・原作照合は実施しない。',
            'limitations': '注意語以外の誤読は検出しない。読み指定があっても実音の正読を保証しない。'}


def load_json_js(text):
    return json.loads(text.removeprefix('window.SCENARIO =').strip().removesuffix(';'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folders', nargs='+', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    reports = [audit(folder.resolve()) for folder in args.folders]
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(reports, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for report in reports:
        print(f'{Path(report["folder"]).name}: {len(report["tracks"])}本、'
              f'整合の要確認 {len(report["issues"])}件、読み注意候補 {len(report["candidates"])}箇所')
        for issue in report['issues']:
            print('  ' + issue)
    return int(any(report['issues'] for report in reports))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(main())

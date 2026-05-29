# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# See LICENSE for full terms.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""
ビデオページ生成_紹介.py — 一人アバター（AiDiy）による紹介ビデオ自動生成スクリプト

◆ このスクリプトが作るビデオ:
    AiDiy アバター（女性、一人）が機能・ツール・仕組みを 1 体で紹介する「紹介・ガイド型」動画。
    scenario.js の version は "mcp"。
    各シーンは short_narration（短い要約）と long_narration（詳しい説明）の 2 段階ナレーションを持ち、
    音声ファイルは short_scene_NNN.mp3 / long_scene_NNN.mp3 の形式で生成する。
    テンプレートは "AiDiy紹介__all_ja" フォルダを使用。

◆ 対比: ビデオページ生成_解説.py
    二人アバター（男女）の掛け合いで解説するニュース・解説型動画を生成する。
    scenario.js の version は "duo-v2"。

このスクリプトの目的:
    AiDiy の Xビデオ用テンプレートをもとに、一人アバター紹介型の動画素材を
    半自動で作成する。フォルダ作成、シナリオ作成、HTML修正、画像生成、
    中間確認、音声生成、再生時間更新、最終確認、完成案内までを 9 ステップで進める。

主な機能:
    00. 初期確認（設定、テンプレート、API、CodeAgents）
    01. テンプレート動画フォルダをコピーして、新しい動画フォルダを作成する。
    02. テーマ説明から scenario.js を生成する（version: "mcp"、short/long narration 形式）。
    03. scenario.js の内容に合わせて index.html の表示文言を修正する。
    04. scenario.js の各シーンに対応する images/scene_*.png を生成する。
    05. シナリオ、HTML、画像の内容を中間確認し、問題があれば修正する。
    06. scenario.js の short_narration / long_narration から short_audio / long_audio の MP3 を生成する。
    07. 生成済み audio/*.mp3 の実再生時間で scenario.js の short_duration_sec / long_duration_sec を更新する。
    08. 必須ファイル、画像数、音声数を最終確認する。
    99. 実行完了ステップを確認し、完成案内だけを行う。

設計方針:
    - ファイル作成や内容更新などの具体的な作業は CodeAgents に依頼する。
    - この Python 本体は「手順の指示」「存在確認」「リトライ制御」を担当する。
    - 各ステップは再実行可能にし、既に成果物がある場合も内容検証して必要なら修正する。
    - 各 CodeAgents 実行後は検証を挟み、POST /aidiy_backup/save/run で差分バックアップを保存する。
    - 差分バックアップ後に差分がなくなるまで、同じステップの検証を継続する。
    - 重要な区切りでは POST /tts play=true で音声案内を挟み、実行状況を知らせる。
    - ビデオページ生成__状況.json に 99 が記録されたら、動画素材一式が完成した合図として処理を終了する。
    - 途中失敗しても、実行ステップ番号（00、01〜08、99）を指定して任意ステップだけ再実行できる。

注意:
    - ビデオページ生成__設定.json の template_dir は "AiDiy紹介__all_ja" 形式（version: "mcp"）の動画フォルダを前提にしている。
    - ビデオページ生成__設定.json の video_base_dir 配下に <フォルダ名> の出力フォルダを作成する。
    - ビデオページ生成__設定.json の folder_name と topic で題材と生成先を定義する。
    - Chrome 再描写の有無は ビデオページ生成__設定.json の browser_preview で指定する。
    - 画像生成と音声生成は MCP 側の image_generation / text_to_speech 実装に依存する。

使い方:
    cd backend_tools
    .venv\\Scripts\\python aidiy_automations\\ビデオページ生成_紹介.py [実行ステップ番号]

例:
    .venv\\Scripts\\python aidiy_automations\\ビデオページ生成_紹介.py

    .venv\\Scripts\\python aidiy_automations\\ビデオページ生成_紹介.py 04
"""

import asyncio
import json
import os
import subprocess
import sys
import textwrap
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass

# UTF-8 出力強制（Windows cp932 文字化け対策）
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

MCP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_DIR = os.path.dirname(MCP_DIR)
sys.path.insert(0, MCP_DIR)

# ================================================================== #
# 定数
# ================================================================== #

# このスクリプトの種別（setting.json の読み込みキーに使う）
SCRIPT_TYPE = "紹介"

SCRIPT_FILE_NAME = os.path.basename(__file__)
SCRIPT_BASE_NAME = os.path.splitext(SCRIPT_FILE_NAME)[0]
SETTING_JSON_NAME = "ビデオページ生成__設定.json"
STEPS_JSON_NAME = "ビデオページ生成__状況.json"

# setting.json のパス（同ディレクトリに置く）
SETTING_JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), SETTING_JSON_NAME)

# 解説 / 紹介の実行完了ステップを共有管理する JSON。
STEPS_JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), STEPS_JSON_NAME)

NEWS_VIDEO_KNOWLEDGE_PATH = os.path.join(REPO_DIR, ".aidiy", "knowledge", "backend_server,backend_tools,MCP活用手順.md")
AUTO_VIDEO_KNOWLEDGE_PATH = os.path.join(REPO_DIR, ".aidiy", "knowledge", "共通,mcp利用による自動ビデオ生成手順.md")
@dataclass
class AutomationConfig:
    """ビデオページ生成の実行設定。設定 JSON と CLI 引数から組み立てる。"""

    folder_name: str
    topic: str
    start_step: int
    stop_step: int
    step_specified: bool
    template_dir: str
    video_base_dir: str
    backup_api_url: str
    tts_api_url: str
    image_gen_api_url: str
    code_agents_api_url: str
    chrome_api_url: str
    ffmpeg_api_url: str
    tts_guide: bool
    frontend_base_url: str
    browser_preview: bool
    chrome_debug_port: int
    max_retries: int
    retry_wait_sec: int
    max_backup_stabilize: int

    @property
    def output_dir(self) -> str:
        return os.path.join(self.video_base_dir, self.folder_name)

# backend_tools 専用 venv の Python。生成補助スクリプトはこの Python で実行する。
MCP_PYTHON = os.path.join(MCP_DIR, ".venv", "Scripts", "python.exe")
if not os.path.isfile(MCP_PYTHON):
    MCP_PYTHON = sys.executable

# 実行時設定。__main__ で設定 JSON と CLI 引数から作り、ここへ反映する。
CONFIG: AutomationConfig | None = None

# 既存のステップ関数から参照する実行時値。configure_runtime() で設定ファイル値を反映する。
TEMPLATE_DIR = ""
VIDEO_BASE_DIR = ""
BACKUP_API_URL = ""
TTS_API_URL = ""
IMAGE_GEN_API_URL = ""
CODE_AGENTS_API_URL = ""
CHROME_API_URL = ""
FFMPEG_API_URL = ""
TTS_GUIDE = True
MAX_RETRIES = 0
RETRY_WAIT_SEC = 0
MAX_BACKUP_STABILIZE = 0


# ================================================================== #
# ユーティリティ
# ================================================================== #

def load_setting_json() -> dict:
    """ビデオページ生成__設定.json を読み込んで返す。ファイルが無ければ空辞書。"""
    if not os.path.isfile(SETTING_JSON_PATH):
        return {}
    try:
        with open(SETTING_JSON_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"WARNING: {SETTING_JSON_NAME} の読み込みに失敗しました: {e}")
        return {}


def save_steps_json(data: dict) -> None:
    """ビデオページ生成__状況.json を UTF-8 JSON として保存する。"""
    with open(STEPS_JSON_PATH, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def ensure_steps_json() -> dict:
    """実行完了ステップ JSON を初期化し、紹介 / 解説キーを必ず持つ dict を返す。"""
    data: dict = {}
    if os.path.isfile(STEPS_JSON_PATH):
        try:
            with open(STEPS_JSON_PATH, encoding="utf-8-sig") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                data = loaded
        except Exception as e:
            print(f"WARNING: {STEPS_JSON_NAME} の読み込みに失敗しました。初期化します: {e}")

    changed = False
    for key in ("紹介", "解説"):
        if key not in data or not isinstance(data.get(key), str):
            data[key] = ""
            changed = True
    if changed or not os.path.isfile(STEPS_JSON_PATH):
        save_steps_json(data)
    return data


def step_no_to_value(step_no: int) -> str:
    """ステップ番号を JSON 保存値へ変換する。"""
    return "99" if step_no == 99 else f"{step_no:02d}"


def step_value_to_int(value: str) -> int:
    """JSON 保存値を比較用の整数へ変換する。未実行は -1。"""
    text = str(value or "").strip()
    if not text:
        return -1
    try:
        return int(text)
    except ValueError:
        return -1


def next_step_after(value: str) -> int:
    """完了済みステップ値から次に実行するステップ番号を返す。"""
    current = step_value_to_int(value)
    if current < 0:
        return 0
    if 0 <= current < 8:
        return current + 1
    if current == 8:
        return 99
    return 99


def get_completed_step() -> str:
    """このスクリプト種別の実行完了ステップを返す。"""
    return str(ensure_steps_json().get(SCRIPT_TYPE, "") or "")


def set_completed_step(step_no: int) -> None:
    """このスクリプト種別の実行完了ステップを JSON へ保存する。"""
    data = ensure_steps_json()
    value = step_no_to_value(step_no)
    data[SCRIPT_TYPE] = value
    save_steps_json(data)
    print(f"  [steps] {SCRIPT_TYPE} 実行完了ステップ = {value}")


def require_mapping(data: dict, key: str) -> dict:
    """設定 JSON の dict セクションを必須値として取り出す。"""
    value = data.get(key)
    if not isinstance(value, dict):
        raise RuntimeError(f"{SETTING_JSON_NAME} に {key} セクションが必要です")
    return value


def require_string(data: dict, key: str) -> str:
    """設定 JSON の文字列値を必須値として取り出す。"""
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"{SETTING_JSON_NAME} に文字列 {key} が必要です")
    return value


def require_bool(data: dict, key: str) -> bool:
    """設定 JSON の bool 値を必須値として取り出す。"""
    value = data.get(key)
    if not isinstance(value, bool):
        raise RuntimeError(f"{SETTING_JSON_NAME} に bool {key} が必要です")
    return value


def require_int(data: dict, key: str) -> int:
    """設定 JSON の int 値を必須値として取り出す。"""
    value = data.get(key)
    if not isinstance(value, int):
        raise RuntimeError(f"{SETTING_JSON_NAME} に int {key} が必要です")
    return value


def build_config(argv: list[str]) -> AutomationConfig:
    """
    設定の優先度: 実行ステップCLI引数 > ビデオページ生成__状況.json / ビデオページ生成__設定.json

    OS 環境変数は使用しない。プログラム規定値は ビデオページ生成__設定.json に置く。
    """
    valid_steps = {0, 1, 2, 3, 4, 5, 6, 7, 8, 99}
    setting = load_setting_json()
    s_type   = require_mapping(setting, SCRIPT_TYPE)
    s_shared = require_mapping(setting, "shared")

    if len(argv) > 2:
        print("ERROR: 引数は実行ステップ番号を 1 つだけ指定できます（00、01〜08、99）")
        sys.exit(1)

    step_specified = len(argv) == 2
    if step_specified:
        try:
            start_step = int(argv[1])
        except ValueError:
            print(f"ERROR: 実行ステップは整数で指定してください（指定値: {argv[1]}）")
            sys.exit(1)
        if start_step not in valid_steps:
            print(f"ERROR: 実行ステップは 00、01〜08、99 で指定してください（指定値: {start_step}）")
            sys.exit(1)
    else:
        start_step = next_step_after(get_completed_step())
    stop_step = start_step

    # 題材と生成先は設定 JSON から読む。CLI では上書きしない。
    folder_name = require_string(s_type, "folder_name")
    topic = require_string(setting, "topic")

    return AutomationConfig(
        folder_name=folder_name,
        topic=topic,
        start_step=start_step,
        stop_step=stop_step,
        step_specified=step_specified,
        template_dir=require_string(s_type, "template_dir"),
        video_base_dir=require_string(s_shared, "video_base_dir"),
        backup_api_url=require_string(s_shared, "backup_api_url"),
        tts_api_url=require_string(s_shared, "tts_api_url"),
        image_gen_api_url=require_string(s_shared, "image_gen_api_url"),
        code_agents_api_url=require_string(s_shared, "code_agents_api_url"),
        chrome_api_url=require_string(s_shared, "chrome_api_url"),
        ffmpeg_api_url=require_string(s_shared, "ffmpeg_api_url"),
        tts_guide=require_bool(s_shared, "tts_guide"),
        frontend_base_url=require_string(s_shared, "frontend_base_url"),
        browser_preview=require_bool(s_shared, "browser_preview"),
        chrome_debug_port=require_int(s_shared, "chrome_debug_port"),
        max_retries=require_int(s_shared, "max_retries"),
        retry_wait_sec=require_int(s_shared, "retry_wait_sec"),
        max_backup_stabilize=require_int(s_shared, "max_backup_stabilize"),
    )


def configure_runtime(config: AutomationConfig) -> None:
    """既存ステップ関数が参照する実行時設定を config から反映する。"""
    global CONFIG
    global TEMPLATE_DIR
    global VIDEO_BASE_DIR
    global BACKUP_API_URL
    global TTS_API_URL
    global IMAGE_GEN_API_URL
    global CODE_AGENTS_API_URL
    global CHROME_API_URL
    global FFMPEG_API_URL
    global TTS_GUIDE
    global MAX_RETRIES
    global RETRY_WAIT_SEC
    global MAX_BACKUP_STABILIZE

    CONFIG = config
    TEMPLATE_DIR = config.template_dir
    VIDEO_BASE_DIR = config.video_base_dir
    BACKUP_API_URL = config.backup_api_url
    TTS_API_URL = config.tts_api_url
    IMAGE_GEN_API_URL = config.image_gen_api_url
    CODE_AGENTS_API_URL = config.code_agents_api_url
    CHROME_API_URL = config.chrome_api_url
    FFMPEG_API_URL = config.ffmpeg_api_url
    TTS_GUIDE = config.tts_guide
    MAX_RETRIES = config.max_retries
    RETRY_WAIT_SEC = config.retry_wait_sec
    MAX_BACKUP_STABILIZE = config.max_backup_stabilize


def print_usage() -> None:
    print(f"使い方: python aidiy_automations\\{SCRIPT_FILE_NAME} [実行ステップ番号]")
    print()
    print("  実行ステップ番号を指定した場合は、そのステップだけを実行します。")
    print(f"  引数を省略した場合は {STEPS_JSON_NAME} の次ステップを実行します。")
    print("  OS 環境変数は使用しません。")
    print("  主な設定キー:")
    print("    topic                         題材、動画テーマ")
    print("    紹介.folder_name              出力フォルダ名")
    print("    紹介.template_dir             テンプレートフォルダ")
    print("    shared.video_base_dir         生成先ルートフォルダ")
    print("    shared.tts_guide              音声案内 ON/OFF")
    print("    shared.browser_preview        Chrome 再描写 ON/OFF")
    print("    shared.*_api_url              各 localhost:8095 HTTP API")
    print()
    print("  実行ステップ番号:")
    print("    00: 初期確認")
    print("    01: フォルダ作成")
    print("    02: シナリオ作成")
    print("    03: HTML修正")
    print("    04: 画像生成")
    print("    05: 中間確認")
    print("    06: 音声生成")
    print("    07: 再生時間更新")
    print("    08: 最終確認")
    print("    99: 完成案内")
    print()
    print("例:")
    print(f"  python aidiy_automations\\{SCRIPT_FILE_NAME}")
    print(f"  python aidiy_automations\\{SCRIPT_FILE_NAME} 04")


def print_automation_flow(config: AutomationConfig) -> None:
    sep(f"AiDiy Automation: {SCRIPT_BASE_NAME}")
    print("  00. 初期確認（設定、テンプレート、API、CodeAgents）")
    print("  01. フォルダ作成")
    print("  02. シナリオ作成")
    print("  03. HTML修正")
    print("  04. 画像生成")
    print("  05. 中間確認")
    print("  06. 音声生成")
    print("  07. 再生時間更新")
    print("  08. 最終確認")
    print("  99. 完成案内")
    print("  ※ 各 CodeAgents 実行後に検証と POST /aidiy_backup/save/run の差分ゼロ確認を行う")
    print()
    print(f"フォルダ名     : {config.folder_name}")
    print(f"トピック       : {config.topic}")
    print(f"生成先         : {config.output_dir}")
    print(f"テンプレート   : {config.template_dir}")
    print(f"実行ステップ   : {step_no_to_value(config.start_step)}")
    print(f"ステップ指定   : {'あり' if config.step_specified else 'なし（次ステップ自動）'}")
    print(f"バックアップAPI: {config.backup_api_url}")
    print(f"TTS API        : {config.tts_api_url}")
    print(f"画像生成API    : {config.image_gen_api_url}")
    print(f"CodeAgents API : {config.code_agents_api_url}")
    print(f"Chrome API     : {config.chrome_api_url}")
    print(f"ffmpeg API     : {config.ffmpeg_api_url}")
    print(f"TTS案内        : {'ON' if config.tts_guide else 'OFF'}")
    print(f"ブラウザ再描写 : {'ON' if config.browser_preview else 'OFF'}")
    print(f"表示URL        : {preview_url(config)}")


def preview_url(config: AutomationConfig) -> str:
    """生成中ビデオを frontend_web 経由で表示する URL を返す。"""
    base = config.frontend_base_url.rstrip("/")
    folder = urllib.parse.quote(config.folder_name.replace("\\", "/"), safe="")
    return f"{base}/Xビデオ/{folder}/index.html?auto=loop"


async def refresh_browser_preview(
    config: AutomationConfig,
    step_label: str,
    *,
    require_existing_index: bool = True,
) -> None:
    """
    aidiy_chrome_devtools HTTP API で、生成中ビデオを ?auto=loop 表示する。

    step01 以降は参照フォルダコピーで index.html があるため、各ステップ後に再描写する。
    """
    if not config.browser_preview:
        return
    index_path = os.path.join(config.output_dir, "index.html")
    if require_existing_index and not os.path.isfile(index_path):
        print(f"  [browser] index.html 未作成のため再描写をスキップ: {index_path}")
        return

    url = preview_url(config)
    try:
        result = await asyncio.to_thread(
            post_mcp_method,
            config.chrome_api_url,
            "navigate",
            {"url": url, "show_automation_banner": False},
            90,
        )
        print(f"  [browser] {step_label}: {result}")
    except Exception as e:
        print(f"  [browser] 再描写をスキップしました: {e}")


def sep(title: str) -> None:
    """コンソール上でステップの区切りを見やすく表示する。"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def check(label: str, ok: bool) -> bool:
    """検証結果を統一フォーマットで出力し、呼び出し元へ真偽値を返す。"""
    mark = "✓" if ok else "✗"
    print(f"  [{mark}] {label}")
    return ok


def ensure_step_markdown(md_path: str, folder_name: str, topic: str) -> None:
    """進捗 Markdown が無ければ Step 01 と同じ形式で再生成する。"""
    if os.path.isfile(md_path):
        return

    md_content = (
        f"# {folder_name}\n"
        f"テーマ: {topic}\n\n"
        "## 進捗\n"
        "- [x] フォルダ作成\n"
        "- [ ] シナリオ作成\n"
        "- [ ] HTML修正\n"
        "- [ ] 画像生成\n"
        "- [ ] 中間確認\n"
        "- [ ] 音声生成\n"
        "- [ ] 再生時間更新\n"
        "- [ ] 完成\n"
    )
    if not os.path.isfile(md_path):
        with open(md_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(md_content)
        return

    with open(md_path, encoding="utf-8") as f:
        content = f.read()

    required_steps = [
        "フォルダ作成",
        "シナリオ作成",
        "HTML修正",
        "画像生成",
        "中間確認",
        "音声生成",
        "再生時間更新",
        "完成",
    ]
    updated = content
    for step_label in required_steps:
        if f"- [ ] {step_label}" in updated or f"- [x] {step_label}" in updated:
            continue
        if "- [ ] 完成" in updated:
            updated = updated.replace("- [ ] 完成", f"- [ ] {step_label}\n- [ ] 完成", 1)
        elif "- [x] 完成" in updated:
            updated = updated.replace("- [x] 完成", f"- [ ] {step_label}\n- [x] 完成", 1)

    if updated != content:
        with open(md_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(updated)


def mark_step_done(md_path: str, step_label: str) -> None:
    """進捗 Markdown の対象行を [x] に更新する。"""
    if not os.path.isfile(md_path):
        print(f"  [md] 進捗ファイルが無いため更新をスキップ: {md_path}")
        return

    with open(md_path, encoding="utf-8") as f:
        content = f.read()

    if f"- [ ] {step_label}" in content:
        updated = content.replace(f"- [ ] {step_label}", f"- [x] {step_label}", 1)
    elif f"- [x] {step_label}" in content:
        return
    else:
        if "- [ ] 完成" in content:
            updated = content.replace("- [ ] 完成", f"- [x] {step_label}\n- [ ] 完成", 1)
        elif "- [x] 完成" in content:
            updated = content.replace("- [x] 完成", f"- [x] {step_label}\n- [x] 完成", 1)
        else:
            updated = content.rstrip() + f"\n- [x] {step_label}\n"

    with open(md_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(updated)


def render_scene_image_script(output_dir: str) -> str:
    """Step 04 用の _gen_scene_images.py 本文を返す。"""
    return textwrap.dedent(
        f"""\
        # -*- coding: utf-8 -*-
        \"\"\"
        シーン画像生成スクリプト

        scenario.js の各 scene から images/scene_*.png を生成します。
        既存の画像ファイル（1000 bytes 超）は自動スキップします。
        \"\"\"

        import json
        import os
        import time
        import urllib.error
        import urllib.request

        OUTPUT_DIR = {output_dir!r}
        IMAGE_GEN_API_URL = {IMAGE_GEN_API_URL!r}
        os.makedirs(OUTPUT_DIR, exist_ok=True)


        def _clean_text(value):
            return " ".join(str(value or "").replace("\\\\n", " ").replace("\\n", " ").split()).strip()


        def load_scenes():
            scenario_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scenario.js")
            with open(scenario_file, encoding="utf-8-sig") as f:
                content = f.read()

            json_str = content.strip()
            if json_str.startswith("window.SCENARIO ="):
                json_str = json_str[len("window.SCENARIO ="):].strip()
            json_str = json_str.rstrip(";").strip()

            data = json.loads(json_str)
            scenes = data.get("scenes", [])
            return scenes if isinstance(scenes, list) else []


        def build_prompt(scene):
            title = _clean_text(scene.get("title", ""))
            headline = _clean_text(scene.get("headline", ""))
            kicker = _clean_text(scene.get("kicker", ""))
            lead = _clean_text(scene.get("lead", ""))
            subtitle = _clean_text(scene.get("subtitle", ""))

            lines = [
                "Create a high-quality, professional widescreen illustration/concept-art for a technology introduction presentation.",
            ]
            if kicker:
                lines.append(f"Topic: {{kicker}}.")
            if title:
                lines.append(f"Title: {{title}}.")
            if headline:
                lines.append(f"Headline: {{headline}}.")
            if lead:
                lines.append(f"Details: {{lead}}.")
            if subtitle:
                lines.append(f"Concept: {{subtitle}}.")
            lines.append("Style: modern technical slide illustration, clean design, gradient background, futuristic, beautiful, no text overlay baked into the image.")
            return "\\n".join(lines).strip()


        def post_json(url, payload, timeout_sec=600):
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={{"Content-Type": "application/json"}},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=timeout_sec) as res:
                    raw = res.read().decode("utf-8", errors="replace")
            except urllib.error.URLError as e:
                raise RuntimeError(f"HTTP API に接続できません: {{url}} ({{e}})") from e
            result = json.loads(raw)
            if isinstance(result, dict) and result.get("error"):
                raise RuntimeError(result["error"])
            return result


        def generate_one(prompt, out_path):
            attempts = [
                ("openai", "gpt-image-2", "1536x1024", "medium"),
                ("freeai", "auto", "1920x1080", "auto"),
                ("auto", "auto", "1024x1024", "auto"),
            ]
            last_error = None
            for provider, model, size, quality in attempts:
                try:
                    result = post_json(IMAGE_GEN_API_URL, {{
                        "prompt": prompt,
                        "provider": provider,
                        "model": model,
                        "size": size,
                        "quality": quality,
                        "save_path": out_path,
                    }})
                    return {{
                        "provider": provider,
                        "model": model,
                        "save_path": result.get("save_path", out_path),
                    }}
                except Exception as e:
                    last_error = f"{{provider}}/{{model}}/{{size}}: {{e}}"
            raise RuntimeError(last_error or "image generation failed")


        def main():
            scenes = load_scenes()
            total = len(scenes)
            done = 0
            skip = 0
            fail = 0

            for i, scene in enumerate(scenes):
                if not isinstance(scene, dict):
                    continue
                scene_id = str(scene.get("id", f"scene_{{i:03d}}") or f"scene_{{i:03d}}")
                num_str = scene_id.replace("scene_", "")
                out_path = os.path.join(OUTPUT_DIR, f"scene_{{num_str}}.png")

                if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
                    print(f"  [SKIP] {{os.path.basename(out_path)}}")
                    skip += 1
                    continue

                prompt = build_prompt(scene)
                title = _clean_text(scene.get("title", scene_id))
                print(f"  [GEN ] {{os.path.basename(out_path)}} : {{title}}")
                try:
                    info = generate_one(prompt, out_path)
                    size = os.path.getsize(out_path) if os.path.exists(out_path) else 0
                    if size > 1000:
                        print(
                            f"         -> OK ({{size:,}} bytes) "
                            f"[{{info.get('provider', '?')}}/{{info.get('model', '?')}}]"
                        )
                        done += 1
                    else:
                        print("         -> FAIL (empty or too small)")
                        fail += 1
                except Exception as e:
                    print(f"         -> ERROR: {{e}}")
                    fail += 1

                time.sleep(1)

            print(f"\\n完了: {{done}} 生成, {{skip}} スキップ, {{fail}} 失敗 (合計 {{total}} 件)")
            if fail:
                raise SystemExit(1)


        if __name__ == "__main__":
            main()
        """
    )

def ensure_scene_image_script(gen_img_py: str, output_dir: str) -> None:
    """Step 04 用の補助スクリプトを現在の設定で再生成する。"""
    content = render_scene_image_script(output_dir)
    with open(gen_img_py, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def render_dialogue_audio_script(output_dir: str) -> str:
    """Step 06 用の _gen_audio.py 本文を返す。mcp 形式の short/long ナレーションから MP3 を生成する。"""
    return textwrap.dedent(
        f"""\
        # -*- coding: utf-8 -*-
        \"\"\"
        ナレーション音声生成スクリプト（mcp 形式）

        scenario.js の short_narration / long_narration から
        short_scene_NNN.mp3 / long_scene_NNN.mp3 を生成します。
        既存の音声ファイル（500 bytes 超）は自動スキップします。
        \"\"\"

        import json
        import os
        import urllib.error
        import urllib.request

        OUTPUT_DIR = {output_dir!r}
        TTS_API_URL = {TTS_API_URL!r}
        os.makedirs(OUTPUT_DIR, exist_ok=True)


        def load_narrations():
            scenario_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scenario.js")
            with open(scenario_file, encoding="utf-8-sig") as f:
                content = f.read()

            json_str = content.strip()
            if json_str.startswith("window.SCENARIO ="):
                json_str = json_str[len("window.SCENARIO ="):].strip()
            json_str = json_str.rstrip(";").strip()

            data = json.loads(json_str)
            narrations = []
            for scene in data.get("scenes", []):
                scene_num = str(scene.get("id", "")).replace("scene_", "")
                short_text = str(scene.get("short_narration", "") or "").strip()
                long_text  = str(scene.get("long_narration",  "") or "").strip()
                if short_text:
                    narrations.append((scene_num, "short", short_text))
                if long_text:
                    narrations.append((scene_num, "long",  long_text))
            return narrations

        NARRATIONS = load_narrations()


        def post_json(url, payload, timeout_sec=300):
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={{"Content-Type": "application/json"}},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=timeout_sec) as res:
                    raw = res.read().decode("utf-8", errors="replace")
            except urllib.error.URLError as e:
                raise RuntimeError(f"HTTP API に接続できません: {{url}} ({{e}})") from e
            result = json.loads(raw)
            if isinstance(result, dict) and result.get("error"):
                raise RuntimeError(result["error"])
            return result


        def synthesize_one(text, out_path):
            return post_json(TTS_API_URL, {{
                "speech_text": text,
                "language": "ja",
                "provider": "freeai",
                "voice": "female",
                "save_path": out_path,
            }})


        def main():
            total = len(NARRATIONS)
            done = 0
            skip = 0
            fail = 0

            for scene_num, kind, text in NARRATIONS:
                fname = f"{{kind}}_scene_{{scene_num}}.mp3"
                fpath = os.path.join(OUTPUT_DIR, fname)

                if os.path.exists(fpath) and os.path.getsize(fpath) > 500:
                    print(f"  [SKIP] {{fname}}")
                    skip += 1
                    continue

                print(f"  [GEN ] {{fname}}")
                try:
                    synthesize_one(text, fpath)
                    size = os.path.getsize(fpath) if os.path.exists(fpath) else 0
                    if size > 500:
                        print(f"         -> OK ({{size:,}} bytes)")
                        done += 1
                    else:
                        print("         -> FAIL (empty or too small)")
                        fail += 1
                except Exception as e:
                    print(f"         -> ERROR: {{e}}")
                    fail += 1

            print(f"\\n完了: {{done}} 生成, {{skip}} スキップ, {{fail}} 失敗 (合計 {{total}} 件)")
            if fail:
                raise SystemExit(1)


        if __name__ == "__main__":
            main()
        """
    )

def ensure_dialogue_audio_script(gen_aud_py: str, output_dir: str) -> None:
    """Step 06 用の補助スクリプトを現在の設定で再生成する。"""
    content = render_dialogue_audio_script(output_dir)
    with open(gen_aud_py, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def run_python_script(script_path: str) -> None:
    """backend_tools の Python で補助スクリプトを実行する。"""
    result = subprocess.run(
        [MCP_PYTHON, script_path],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.stdout.strip():
        print(result.stdout.rstrip())
    if result.stderr.strip():
        print(result.stderr.rstrip())
    if result.returncode != 0:
        raise RuntimeError(f"スクリプト実行に失敗しました: {script_path} (exit={result.returncode})")


def load_scenario_object(scenario_path: str) -> dict:
    """window.SCENARIO = {...}; 形式の scenario.js を dict として読む。"""
    with open(scenario_path, encoding="utf-8-sig") as f:
        content = f.read()

    json_str = content.strip()
    if json_str.startswith("window.SCENARIO ="):
        json_str = json_str[len("window.SCENARIO ="):].strip()
    json_str = json_str.rstrip(";").strip()
    data = json.loads(json_str)
    if not isinstance(data, dict):
        raise RuntimeError(f"scenario.js の内容が object ではありません: {scenario_path}")
    return data


def save_scenario_object(scenario_path: str, data: dict) -> None:
    """scenario.js を window.SCENARIO 形式で保存する。"""
    with open(scenario_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("window.SCENARIO = ")
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write(";\n")


async def probe_media_duration_sec(media_path: str) -> float:
    """aidiy_ffmpeg_control HTTP API でメディア再生時間を取得する。"""
    result = await asyncio.to_thread(
        post_mcp_method,
        FFMPEG_API_URL,
        "media_duration",
        {"input_path": media_path, "timeout_sec": 60},
        120,
    )
    raw = result.get("duration_sec")
    try:
        return round(float(raw), 3)
    except (TypeError, ValueError) as e:
        raise RuntimeError(f"ffmpeg API の duration_sec を数値化できません: {repr(raw)}") from e


async def update_scenario_audio_durations(scenario_path: str, new_dir: str) -> dict:
    """音声ファイルの実再生時間で scenario.js の short/long duration_sec を更新する（mcp 形式）。"""
    data = load_scenario_object(scenario_path)
    updated_audio = 0
    updated_scenes = 0
    total_short_sec = 0.0
    total_long_sec = 0.0

    for scene in data.get("scenes", []):
        scene_id = str(scene.get("id", "") or "")
        scene_num = scene_id.replace("scene_", "")

        for kind in ("short", "long"):
            audio_ref = str(scene.get(f"{kind}_audio", "") or "").strip()
            if not audio_ref:
                audio_ref = f"audio/{kind}_scene_{scene_num}.mp3"
                scene[f"{kind}_audio"] = audio_ref

            audio_path = audio_ref.replace("/", os.sep)
            if not os.path.isabs(audio_path):
                audio_path = os.path.join(new_dir, audio_path)
            audio_path = os.path.abspath(audio_path)
            if not os.path.isfile(audio_path):
                raise RuntimeError(f"音声ファイルが見つかりません: {audio_path}")

            duration_sec = await probe_media_duration_sec(audio_path)
            scene[f"{kind}_duration_sec"] = duration_sec
            if kind == "short":
                total_short_sec += duration_sec
            else:
                total_long_sec += duration_sec
            updated_audio += 1

        updated_scenes += 1

    data["total_short_duration_sec"] = round(total_short_sec, 3)
    data["total_long_duration_sec"] = round(total_long_sec, 3)
    save_scenario_object(scenario_path, data)
    return {
        "audio_count": updated_audio,
        "scene_count": updated_scenes,
        "total_short_duration_sec": round(total_short_sec, 3),
        "total_long_duration_sec": round(total_long_sec, 3),
    }

def collect_scenario_duration_stats(scenario_path: str) -> dict:
    """scenario.js の short/long duration_sec が設定されているか確認する（mcp 形式）。"""
    data = load_scenario_object(scenario_path)
    audio_count = 0
    audio_ok = 0
    scene_count = 0
    scene_ok = 0
    total_short_sec = 0.0
    total_long_sec = 0.0

    for scene in data.get("scenes", []):
        scene_count += 1
        short_ok = False
        long_ok = False
        for kind in ("short", "long"):
            audio_count += 1
            try:
                dur = float(scene.get(f"{kind}_duration_sec", 0) or 0)
            except (TypeError, ValueError):
                dur = 0.0
            if dur > 0:
                audio_ok += 1
                if kind == "short":
                    short_ok = True
                    total_short_sec += dur
                else:
                    long_ok = True
                    total_long_sec += dur
        if short_ok and long_ok:
            scene_ok += 1

    return {
        "audio_count": audio_count,
        "audio_ok": audio_ok,
        "scene_count": scene_count,
        "scene_ok": scene_ok,
        "total_short_duration_sec": round(total_short_sec, 3),
        "total_long_duration_sec": round(total_long_sec, 3),
    }

def count_scenario_dialogues(scenario_path: str) -> int:
    """scenario.js に含まれる音声ファイルの期待件数を返す（mcp 形式: シーンごとに short + long の 2 件）。"""
    data = load_scenario_object(scenario_path)
    count = 0
    for scene in data.get("scenes", []):
        if str(scene.get("short_narration", "") or "").strip():
            count += 1
        if str(scene.get("long_narration", "") or "").strip():
            count += 1
    return count

def count_scenario_scenes(scenario_path: str) -> int:
    """scenario.js に含まれる scene 件数を返す。"""
    data = load_scenario_object(scenario_path)
    scenes = data.get("scenes", [])
    if not isinstance(scenes, list):
        return 0
    return sum(1 for scene in scenes if isinstance(scene, dict))


def index_html_matches_theme(index_path: str, scenario_path: str, folder_name: str, topic: str) -> bool:
    """index.html が今回テーマ向けに更新済みかをざっくり判定する。"""
    if not os.path.isfile(index_path):
        return False

    with open(index_path, encoding="utf-8") as f:
        html = f.read()

    if "<title>" not in html or "scenario.js" not in html:
        return False

    markers = {folder_name.strip(), topic.strip()}
    if os.path.isfile(scenario_path):
        try:
            data = load_scenario_object(scenario_path)
            for key in ("title", "project_name"):
                value = str(data.get(key, "") or "").strip()
                if value:
                    markers.add(value)
        except Exception:
            pass

    return any(marker and marker in html for marker in markers)


def post_json(url: str, payload: dict, timeout_sec: int = 120) -> dict:
    """HTTP API へ JSON を POST し、JSON レスポンスを dict として返す。"""
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as res:
            raw = res.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as e:
        raise RuntimeError(f"HTTP API に接続できません: {url} ({e})") from e

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"HTTP API の JSON 解析に失敗しました: {raw[:200]}") from e
    if isinstance(result, dict) and result.get("error"):
        raise RuntimeError(f"HTTP API エラー: {result['error']}")
    return result


def post_mcp_method(base_url: str, method_name: str, payload: dict | None = None, timeout_sec: int = 120) -> dict:
    """HTTP Transport の /{mcp_name}/{method_name} を POST で呼ぶ。"""
    url = f"{base_url.rstrip('/')}/{method_name.lstrip('/')}"
    return post_json(url, payload or {}, timeout_sec=timeout_sec)


def guide_tts(message: str, *, voice: str = "female") -> None:
    """
    aidiy_text_to_speech API で実行状況を読み上げる。

    TTS サーバー未起動や音声再生失敗で自動化全体を止めない。
    """
    if not TTS_GUIDE:
        return
    text = message.strip()
    if not text:
        return
    payload = {
        "speech_text": text,
        "language": "ja",
        "provider": "edge",
        "voice": voice,
        "play": True,
        "local_play": True,
    }
    try:
        post_json(TTS_API_URL, payload, timeout_sec=90)
    except Exception as e:
        print(f"  [tts] 案内音声をスキップしました: {e}")


async def agent_run(ca: dict, prompt: str, timeout_sec: int = 300) -> str:
    """
    aidiy_code_agents HTTP API に作業指示を投げる共通ラッパー。

    本スクリプトは直接ファイル編集を行わず、具体的な生成・更新処理は
    CodeAgents に委譲する。ここでは実行結果の状態と応答長だけを出力し、
    成否の最終判断は各 step_* 関数のファイル存在確認で行う。
    使用 AI の選択は MCP サーバー側の共通ロジックへ委譲するが、
    自動化では対話待ちで止まらないよう fresh session + full permissions で実行する。
    """
    api_url = ca.get("api_url", CODE_AGENTS_API_URL)
    payload = {
        "prompt": prompt,
        "project_path": REPO_DIR,
        "ai_name": "auto",
        "ai_model": "auto",
        "max_turns": 15,
        "code_plan": "off",
        "code_verify": "off",
        "code_permissions": "full",
        "resume": False,
        "timeout_sec": timeout_sec,
    }
    result = await asyncio.to_thread(
        post_mcp_method,
        api_url,
        "run",
        payload,
        max(timeout_sec + 60, 180),
    )
    status = result.get("status", "NG")
    text = result.get("result", "（応答なし）")
    used_ai = result.get("ai_name", "auto")
    print(f"  [agent] ai={used_ai} status={status}  result_length={len(text)}")
    return text


def step_instruction_header(step_name: str, step_summary: str) -> str:
    """
    CodeAgents への各作業指示に必ず付ける共通ヘッダー。

    既存成果物がある再実行時でも、単純スキップではなく内容検証を促す。
    問題があれば修正し、問題がなければ上書きしない方針を明示する。
    """
    return (
        "以下は AiDiy の自動ビデオ生成ワークフローの 1 ステップです。\n\n"
        "【今やっていること】\n"
        f"  {step_name} を実行しています。\n\n"
        "【今回のステップ内容】\n"
        f"{step_summary}\n\n"
        "【既存成果物の扱い】\n"
        "  対象ファイルやフォルダが既にある場合は、存在だけで完了扱いにせず、内容を検証してください。\n"
        "  今回のフォルダ名・テーマ・scenario.js と整合しない、必須項目が足りない、破損している、\n"
        "  テンプレート元の文言が残っている、生成途中の空ファイルがある場合は修正してください。\n"
        "  問題がない場合は不要な上書きや再生成をせず、確認結果を表示してください。\n\n"
    )


async def agent_verify_step(
    ca: dict,
    step_name: str,
    step_summary: str,
    target_paths: list[str],
    timeout_sec: int = 300,
) -> None:
    """
    作業後に CodeAgents へ検証専用の確認を依頼する。

    この検証で軽微な不足を直せるようにし、その後 Python 側の機械的チェックと
    差分バックアップ確認を行う。
    """
    target_list = "\n".join(f"  - {path}" for path in target_paths)
    prompt = (
        step_instruction_header(step_name, step_summary)
        + "以下の対象を検証してください。\n\n"
        "【検証対象】\n"
        f"{target_list}\n\n"
        "【検証・修正方針】\n"
        "  1. 今回のステップで作られるべき成果物が存在するか確認してください。\n"
        "  2. 既に存在する場合も内容を読み、今回のフォルダ名・テーマと合っているか確認してください。\n"
        "  3. 問題があればこの場で修正してください。\n"
        "  4. 問題がなければ変更せず、OK と判断した根拠を短く表示してください。\n"
        "  5. 最後に、修正したファイルと未修正で OK としたファイルを一覧表示してください。\n"
    )
    await agent_run(ca, prompt, timeout_sec=timeout_sec)


def post_backup_api(backup_url: str, dry_run: bool) -> dict:
    """aidiy_backup API へ POST し、差分スキャンまたは差分バックアップを実行する。
    dry_run=True → /save/scan（コピーなし）、dry_run=False → /save/run（差分コピー）
    """
    method = "scan" if dry_run else "run"
    url = f"{backup_url}/{method}"
    try:
        return post_json(url, {}, timeout_sec=120)
    except RuntimeError as e:
        raise RuntimeError(str(e).replace("HTTP API", "backup API")) from e


def backup_diff_count(backup_url: str) -> int:
    """POST /aidiy_backup/save/scan で、現時点の差分バックアップ対象ファイル数を返す。"""
    result = post_backup_api(backup_url, dry_run=True)
    count = int(result.get("count", 0))
    files = result.get("差分ファイル", []) or []
    print(f"  [backup] dry_run 差分ファイル数: {count}")
    if files:
        for path in files[:10]:
            print(f"    - {path}")
        if len(files) > 10:
            print(f"    ... 他 {len(files) - 10} 件")
    return count


def backup_save_once(backup_url: str) -> bool:
    """POST /aidiy_backup/save/run で差分バックアップを 1 回実行し、成功可否を返す。"""
    result = post_backup_api(backup_url, dry_run=False)
    ok = bool(result.get("ok"))
    print(
        "  [backup] "
        f"ok={ok} バックアップ件数={result.get('バックアップ件数')} "
        f"差分なし={result.get('差分なし')} 先={result.get('バックアップ先')}"
    )
    return ok


async def verify_and_backup_until_stable(
    ca: dict,
    backup_url: str,
    step_name: str,
    step_summary: str,
    target_paths: list[str],
    validate: Callable[[], bool],
    verify_timeout_sec: int = 300,
    attempt: int = 1,
) -> bool:
    """
    CodeAgents 作業後の安定化処理。

    1. 検証専用の CodeAgents 実行で内容を確認・必要なら修正する。
    2. Python 側の機械的チェックを通す。
    3. POST /aidiy_backup/save/scan で差分を確認する。
    4. 差分があれば POST /aidiy_backup/save/run で差分バックアップを保存する。
    5. バックアップ保存後はもう一度検証へ戻り、差分がゼロになるまで続ける。
    """
    for round_no in range(1, MAX_BACKUP_STABILIZE + 1):
        print(f"  [verify] {step_name} 検証 {round_no}/{MAX_BACKUP_STABILIZE}")
        guide_tts(f"{step_name} の検証を開始します。試行 {attempt}回目です。")
        await agent_verify_step(
            ca,
            step_name=step_name,
            step_summary=step_summary,
            target_paths=target_paths,
            timeout_sec=verify_timeout_sec,
        )

        if not validate():
            print("  [verify] Python 側検証が NG です")
            guide_tts(f"{step_name} の検証で問題が見つかりました。同じステップをやり直します。", voice="male")
            return False

        diff_count = backup_diff_count(backup_url)
        if diff_count == 0:
            print("  [backup] 差分なし。次のステップへ進みます")
            guide_tts(f"{step_name} の差分はありません。次のステップへ進みます。")
            return True

        print("  [backup] 差分あり。POST /aidiy_backup/save/run で保存して同ステップを再確認します")
        guide_tts(f"{step_name} で差分が {diff_count} 件あります。差分バックアップを保存して、もう一度確認します。", voice="male")
        if not backup_save_once(backup_url):
            guide_tts(f"{step_name} の差分バックアップに失敗しました。", voice="male")
            return False

        after_count = backup_diff_count(backup_url)
        if after_count != 0:
            print("  [backup] バックアップ後も差分が残っています。同ステップを継続します")
            guide_tts(f"バックアップ後も差分が {after_count} 件残っています。同じステップを継続します。", voice="male")

    print(f"  [backup] 差分ゼロ確認が {MAX_BACKUP_STABILIZE} 回以内に完了しませんでした")
    guide_tts(f"{step_name} の差分ゼロ確認が完了しませんでした。処理を確認してください。", voice="male")
    return False


# ================================================================== #
# Step 00: 初期確認
# ================================================================== #

async def step00_preflight(
    ca: dict,
    backup_url: str,
    new_dir: str,
    folder_name: str,
    topic: str,
    attempt: int = 1,
) -> bool:
    """
    Step 00: 自動化を始める前の初期確認。

    設定 JSON / CLI 引数から組み立てた設定、テンプレート、出力先、
    backup / tts HTTP API、CodeAgents の利用可否を確認する。
    """
    step_name = "Step 00: 初期確認"
    sep(step_name)
    guide_tts("ステップゼロ、初期確認を開始します。設定、テンプレート、API、AIの利用可否を確認します。")

    ok_template = check(f"テンプレート存在: {TEMPLATE_DIR}", os.path.isdir(TEMPLATE_DIR))
    ok_base = check(f"生成先ルート存在: {VIDEO_BASE_DIR}", os.path.isdir(VIDEO_BASE_DIR))
    ok_folder = check("フォルダ名指定", bool(folder_name.strip()))
    ok_topic = check("トピック指定", bool(topic.strip()))
    version_info = ca.get("version_info", {})
    ok_agents = check("CodeAgents HTTP API 利用可能", bool([k for k, v in version_info.items() if v.get("ok")]))

    try:
        post_backup_api(backup_url, dry_run=True)
        ok_backup = check(f"backup API 疎通: {backup_url}", True)
    except Exception as e:
        print(f"  [backup] 疎通確認 NG: {e}")
        ok_backup = check(f"backup API 疎通: {backup_url}", False)

    if TTS_GUIDE:
        try:
            guide_tts("音声案内の確認です。AiDiy 自動化ソリューションを開始できます。")
            ok_tts = check(f"tts API 案内: {TTS_API_URL}", True)
        except Exception as e:
            print(f"  [tts] 疎通確認 NG: {e}")
            ok_tts = check(f"tts API 案内: {TTS_API_URL}", False)
    else:
        ok_tts = check("tts API 案内: OFF", True)

    print(f"  出力予定: {new_dir}")
    return ok_template and ok_base and ok_folder and ok_topic and ok_agents and ok_backup and ok_tts


# ================================================================== #
# Step 01: フォルダ作成
# ================================================================== #

async def step_create_folder(
    ca: dict,
    backup_url: str,
    new_dir: str,
    folder_name: str,
    topic: str,
    attempt: int = 1,
) -> bool:
    """
    Step 01: 出力フォルダの土台を作成する。

    テンプレートフォルダをコピーし、images/・audio/ と進捗管理 Markdown を用意する。
    index.html / scenario.js / images / audio / <フォルダ名>.md が揃えば次ステップへ進める。
    """
    sep("Step 01: フォルダ作成")
    step_name = "Step 01: フォルダ作成"
    step_summary = (
        f'  テーマ「{topic}」の動画フォルダ "{new_dir}" を作成します。\n'
        "  テンプレートから index.html / scenario.js などをコピーし、images/・audio/ と進捗 Markdown を用意します。"
    )

    md_path    = os.path.join(new_dir, f"{folder_name}.md")
    index_path = os.path.join(new_dir, "index.html")
    guide_tts(f"AiDiy 自動化ソリューションを開始します。{step_name}、動画フォルダを準備します。")

    # ── 既完了チェック ──
    # フォルダ作成済みで主要ファイルが揃っている場合は、再実行時に上書きしない。
    folder_already_exists = (
        os.path.isdir(new_dir)
        and os.path.isfile(index_path)
        and os.path.isfile(os.path.join(new_dir, "scenario.js"))
    )
    if folder_already_exists:
        print("  [既存] コピー先に index.html / scenario.js が存在。テンプレートからの再コピーはスキップします")
    else:
        print("  [新規] フォルダを作成します")

    images_dir = os.path.join(new_dir, "images")
    audio_dir = os.path.join(new_dir, "audio")
    md_content = (
        f"# {folder_name}\n"
        f"テーマ: {topic}\n\n"
        f"## 進捗\n"
        f"- [x] フォルダ作成\n"
        f"- [ ] シナリオ作成\n"
        f"- [ ] HTML修正\n"
        f"- [ ] 画像生成\n"
        f"- [ ] 中間確認\n"
        f"- [ ] 音声生成\n"
        f"- [ ] 再生時間更新\n"
        f"- [ ] 完成\n"
    )

    prompt = (
        step_instruction_header(step_name, step_summary)
        +
        "以下の手順を実行してください。\n\n"
        "【目的】\n"
        f'「{topic}」というテーマの動画フォルダを作成する。\n\n'
        "【参考ナレッジ】\n"
        f'  - "{NEWS_VIDEO_KNOWLEDGE_PATH}"\n'
        f'  - "{AUTO_VIDEO_KNOWLEDGE_PATH}"\n\n'
        + (
            "【手順 1】テンプレートフォルダをコピー\n"
            f'  robocopy "{TEMPLATE_DIR}" "{new_dir}" /E /XD audio /XD images /XD __pycache__ /NP /NDL\n'
            "  ※ robocopy は成功時に終了コード 1〜7 を返す（エラーは 8 以上）。\n"
            "  ※ images/ は各動画で生成するため除外する。\n\n"
            if not folder_already_exists else
            "【手順 1】テンプレートフォルダのコピー — スキップ\n"
            f'  コピー先 "{new_dir}" に index.html と scenario.js が存在するため\n'
            "  テンプレートからの再コピーは絶対に行わないでください。\n"
            "  既存ファイルの上書き・削除も禁止です。\n\n"
        )
        + "【手順 2】images / audio フォルダを確認・作成\n"
        f'  フォルダが存在しなければ作成: "{images_dir}"\n\n'
        f'  フォルダが存在しなければ作成: "{audio_dir}"\n\n'
        "【手順 3】進捗管理ファイルを作成\n"
        f'  パス: "{md_path}"\n'
        "  内容:\n"
        f"{md_content}\n"
        "【手順 4】作成後のファイル一覧を表示して確認\n"
    )
    await agent_run(ca, prompt, timeout_sec=180)

    # CodeAgent が作成を省略した場合に備えて Python 側で確実に補完する
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)
    ensure_step_markdown(md_path, folder_name, topic)

    def validate() -> bool:
        return check(f"フォルダ存在: {new_dir}", os.path.isdir(new_dir))

    return await verify_and_backup_until_stable(
        ca=ca,
        backup_url=backup_url,
        step_name=step_name,
        step_summary=step_summary,
        # images/ ・ audio/ はステップ01では空のままが正しい。エージェントに渡すとテンプレートから不要なコピーを誕発するため除外。
        target_paths=[new_dir, index_path, os.path.join(new_dir, "scenario.js"), md_path],
        validate=validate,
        verify_timeout_sec=180,
        attempt=attempt,
    )


# ================================================================== #
# Step 02: シナリオ作成
# ================================================================== #

async def step_create_scenario(
    ca: dict,
    backup_url: str,
    new_dir: str,
    folder_name: str,
    topic: str,
    attempt: int = 1,
) -> bool:
    """
    Step 02: 動画の台本を作成する。

    scenario.js は画面表示、字幕、読み上げ、画像、音声ファイル名をまとめる
    動画生成の中心データ。scene_000〜scene_006 と scene_999 の 8 シーン構成を
    CodeAgents に生成させる。index.html の表示修正は Step 03 で独立して行う。
    """
    sep("Step 02: シナリオ作成")
    step_name = "Step 02: シナリオ作成"
    step_summary = (
        f'  "{folder_name}" の scenario.js を作成・更新します。\n'
        "  8 シーン構成、short/long ナレーション、画像・音声パス、AiDiy 説明入りのまとめを整えます。"
    )

    scenario_path = os.path.join(new_dir, "scenario.js")
    md_path       = os.path.join(new_dir, f"{folder_name}.md")
    template_scen = os.path.join(TEMPLATE_DIR, "scenario.js")
    guide_tts(f"{step_name} を開始します。テーマに沿った台本を作成します。")

    # ── 既完了チェック ──
    # window.SCENARIO / scene_999 / folder_name を含めば、このテーマ用の台本作成済みとみなす。
    if os.path.isfile(scenario_path):
        with open(scenario_path, encoding="utf-8") as f:
            c = f.read()
        if "window.SCENARIO" in c and "scene_999" in c and folder_name in c:
            print("  [既存] scenario.js は作成済みです。内容検証を行い、問題があれば修正します")

    prompt = (
        step_instruction_header(step_name, step_summary)
        +
        "以下の手順を実行してください。\n\n"
        "【参考ナレッジ】\n"
        f'  - "{NEWS_VIDEO_KNOWLEDGE_PATH}"\n'
        f'  - "{AUTO_VIDEO_KNOWLEDGE_PATH}"\n\n'
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "【作業 A】scenario.js の作成\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f'参照テンプレート: "{template_scen}"\n'
        f'出力先: "{scenario_path}"\n\n'
        "■ 必須要件（構造）\n"
        '- window.SCENARIO = { ... } 形式を維持\n'
        '- "version": "mcp" を維持（duo-v2 にしないこと）\n'
        '- "project_name" と top-level の "title" を今回テーマに合わせて更新\n'
        '- assets_policy は以下を維持:\n'
        '    "visual_style": "left_avatar_38_right_content_62"\n'
        '    "audio_dir": "audio"\n'
        '    "image_dir": "images"\n'
        '    "avatar": "../vrm/VRM_AiDiy.vrm"\n'
        '    "tts_provider": "freeai:female"\n\n'
        "■ scenes 構成（8シーン）\n"
        "  scene_000: イントロ（テーマ全体の概要）\n"
        "  scene_001〜006: 各テーマ（機能・特徴ごと）\n"
        "  scene_999: まとめ\n\n"
        "■ 各シーンの必須フィールド\n"
        '  "id", "title", "expression", "accent", "accent_soft",\n'
        '  "kicker", "headline", "image": "images/scene_NNN.png",\n'
        '  "chips", "metrics", "cards", "facts", "evidence",\n'
        '  "short_narration", "long_narration",\n'
        '  "short_audio": "audio/short_scene_NNN.mp3",\n'
        '  "long_audio": "audio/long_scene_NNN.mp3",\n'
        '  "short_start_sec": 0.0, "short_duration_sec": 10.0,\n'
        '  "long_start_sec": 0.0, "long_duration_sec": 30.0\n\n'
        "  - short_narration: 短い要約ナレーション（40〜80文字程度）\n"
        "  - long_narration: 詳しい読み上げテキスト（200〜400文字）\n"
        "  - short/long の duration_sec は仮値（0.0 等）でよい\n"
        "  - evidence: [{source: '...', text: '...'}] 形式で根拠を記載\n\n"
        "■ scene_000 の冒頭要件\n"
        "  - short_narration にテーマの概要を簡潔に入れる\n"
        "  - long_narration の冒頭に\n"
        "    「この動画は AiDiy の video_generation機能 で自動生成されました」\n"
        "    という趣旨を必ず入れる\n\n"
        "■ scene_999 の long_narration に必ず含めること\n"
        "  (1) この動画は AiDiy で作られたという説明\n"
        "  (2) チャンネル登録のお願い\n"
        "  (3) 視聴者が AiDiy を使ってみたくなる誘導フレーズ\n"
        "  (4) 楽しく前向きで、見た人が『自分でも試してみたい』と思える終わり方\n\n"
        "■ 内容面の注意\n"
        "  - 各 scene の evidence / facts と、headline / narration / image_prompt を整合させる\n"
        "  - 画像生成で使えるよう、image_prompt には facts の要点を反映する\n"
        "  - 全体の語り口は、親しみやすく楽しいが軽薄すぎないトーンにする\n"
        "  - 難しい専門用語は必要最小限にし、高校生でも自然に理解しやすい日本語へ言い換える\n"
        "  - ただし『高校生向けに説明します』のようなメタ説明は書かない\n\n"
        f"■ テーマ: {topic}\n\n"
        "【作業 B】進捗更新\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f'"{md_path}" の「シナリオ作成」チェックを [x] にしてください。\n\n'
        "【完了確認】scenario.js の先頭10行を表示してください。\n"
    )
    await agent_run(ca, prompt, timeout_sec=600)

    def validate() -> bool:
        ok1 = check("scenario.js 存在", os.path.isfile(scenario_path))
        ok2 = False
        if ok1:
            with open(scenario_path, encoding="utf-8") as f:
                c = f.read()
            ok2 = check(
                "scenario.js 内容（SCENARIO + scene_999 + folder_name）",
                "window.SCENARIO" in c and "scene_999" in c and folder_name in c,
            )
        return ok1 and ok2

    return await verify_and_backup_until_stable(
        ca=ca,
        backup_url=backup_url,
        step_name=step_name,
        step_summary=step_summary,
        target_paths=[scenario_path, md_path],
        validate=validate,
        verify_timeout_sec=300,
        attempt=attempt,
    )


# ================================================================== #
# Step 03: HTML修正
# ================================================================== #

async def step_update_html(
    ca: dict,
    backup_url: str,
    new_dir: str,
    folder_name: str,
    topic: str,
    attempt: int = 1,
) -> bool:
    """
    Step 03: index.html の表示文言をシナリオに合わせて修正する。

    テンプレートからコピーされた HTML は別テーマのタイトルや説明を持つため、
    scenario.js 作成後に <title>、トップバー、説明文などを現在の動画テーマへ
    更新する。構造、CSS、JS 読み込みは維持し、表示テキストだけを中心に修正する。
    """
    sep("Step 03: HTML修正")
    step_name = "Step 03: HTML修正"
    step_summary = (
        f'  "{folder_name}" の index.html を scenario.js と今回テーマに合わせて修正します。\n'
        "  <title>、.brand、.top-note、見出しなどのテンプレート元文言を置き換えます。"
    )

    index_path    = os.path.join(new_dir, "index.html")
    scenario_path = os.path.join(new_dir, "scenario.js")
    md_path       = os.path.join(new_dir, f"{folder_name}.md")
    guide_tts(f"{step_name} を開始します。画面のタイトルと説明を修正します。")

    # ── 既完了チェック ──
    # フォルダ名そのものではなく、今回テーマか scenario タイトルが HTML に反映されていれば更新済みとみなす。
    if index_html_matches_theme(index_path, scenario_path, folder_name, topic):
        print("  [既存] index.html は修正済みです。内容検証を行い、問題があれば修正します")

    prompt = (
        step_instruction_header(step_name, step_summary)
        +
        "以下の手順で index.html を修正してください。\n\n"
        "【参考ナレッジ】\n"
        f'  - "{NEWS_VIDEO_KNOWLEDGE_PATH}"\n\n'
        "【目的】\n"
        "scenario.js 作成後の動画テーマに合わせて、HTML の表示文言を更新する。\n\n"
        "【対象ファイル】\n"
        f'  index.html: "{index_path}"\n'
        f'  scenario.js: "{scenario_path}"\n\n'
        "【修正方針】\n"
        "  - HTML/CSS/JavaScript の構造は維持する。\n"
        "  - scenario.js の読み込み、再生制御、音声・画像表示ロジックは壊さない。\n"
        "  - 1アバター（シングル）表示、リップシンク、字幕表示ロジックは維持する。\n"
        "  - short_narration / long_narration の切り替え、short_audio / long_audio 再生ロジックは維持する。\n"
        "  - テンプレート元テーマの文言だけを、今回のテーマへ置き換える。\n\n"
        "【更新箇所】\n"
        f"  1. <title> タグにフォルダ名またはテーマ名を含める: {folder_name}\n"
        "  2. .brand div の中身を今回の動画ブランド表示へ更新する。\n"
        "  3. .top-note の中身をテーマの簡潔な説明文（1〜2文）へ更新する。\n"
        "  4. 見出し、サブタイトル、説明文などにテンプレート元テーマが残っていれば置き換える。\n"
        "  5. 可能なら scenario.js の scene_000.headline / kicker を参考に文言を揃える。\n\n"
        "【今回のテーマ】\n"
        f"  フォルダ名: {folder_name}\n"
        f"  テーマ詳細: {topic}\n\n"
        "【進捗更新】\n"
        f'  "{md_path}" の「HTML修正」チェックを [x] にしてください。\n\n'
        "【完了確認】index.html の <title> と .brand と .top-note 周辺を表示してください。\n"
    )
    await agent_run(ca, prompt, timeout_sec=300)

    def validate() -> bool:
        ok1 = check("index.html 存在", os.path.isfile(index_path))
        ok2 = False
        if ok1:
            ok2 = check(
                "index.html 内容（title + scenario.js + テーマ反映）",
                index_html_matches_theme(index_path, scenario_path, folder_name, topic),
            )
        return ok1 and ok2

    return await verify_and_backup_until_stable(
        ca=ca,
        backup_url=backup_url,
        step_name=step_name,
        step_summary=step_summary,
        target_paths=[index_path, scenario_path, md_path],
        validate=validate,
        verify_timeout_sec=240,
        attempt=attempt,
    )


# ================================================================== #
# Step 04: 画像生成
# ================================================================== #

async def step_generate_images(
    ca: dict,
    backup_url: str,
    new_dir: str,
    folder_name: str,
    topic: str,
    attempt: int = 1,
) -> bool:
    """
    Step 04: シーン画像を生成する。

    CodeAgents に _gen_scene_images.py を作成・実行させる。補助スクリプトは
    scenario.js からシーン情報を読み取り、aidiy_image_generation HTTP API を使って
    images/scene_000.png などを保存する。
    """
    sep("Step 04: 画像生成")
    step_name = "Step 04: 画像生成"
    step_summary = (
        f'  "{folder_name}" の scenario.js から各シーン画像を生成します。\n'
        "  _gen_scene_images.py を作成・実行し、images/scene_*.png を 8 枚以上揃えます。"
    )

    images_dir    = os.path.join(new_dir, "images")
    scenario_path = os.path.join(new_dir, "scenario.js")
    gen_img_py    = os.path.join(new_dir, "_gen_scene_images.py")
    md_path       = os.path.join(new_dir, f"{folder_name}.md")
    guide_tts(f"{step_name} を開始します。シーン画像を生成します。")

    # ── 既完了チェック（シナリオより新しい画像が 8 枚以上あれば完了とみなす）──
    # scenario.js 更新後に古い画像が残っているケースを避けるため、mtime も見る。
    if os.path.isdir(images_dir) and os.path.isfile(scenario_path):
        scen_mtime = os.path.getmtime(scenario_path)
        existing = [
            f for f in os.listdir(images_dir)
            if f.endswith(".png")
            and os.path.getsize(os.path.join(images_dir, f)) > 1000
            and os.path.getmtime(os.path.join(images_dir, f)) >= scen_mtime
        ]
        if len(existing) >= 8:
            print(f"  [既存] images/*.png が {len(existing)} 件存在します。内容検証を行い、問題があれば修正します")
    ensure_step_markdown(md_path, folder_name, topic)
    ensure_scene_image_script(gen_img_py, images_dir)
    print(f"  [image] 補助スクリプトを生成しました: {gen_img_py}")
    print(f'  [image] 実行コマンド: "{MCP_PYTHON}" "{gen_img_py}"')
    run_python_script(gen_img_py)
    mark_step_done(md_path, "画像生成")

    def validate() -> bool:
        if not os.path.isdir(images_dir):
            check("images フォルダ存在", False)
            return False
        expected_image_count = count_scenario_scenes(scenario_path) if os.path.isfile(scenario_path) else 8
        pngs = [
            f for f in os.listdir(images_dir)
            if f.endswith(".png") and os.path.getsize(os.path.join(images_dir, f)) > 1000
        ]
        return check(
            f"images/*.png 生成数: {len(pngs)} 件（期待 {expected_image_count} 件以上）",
            expected_image_count > 0 and len(pngs) >= expected_image_count,
        )

    return await verify_and_backup_until_stable(
        ca=ca,
        backup_url=backup_url,
        step_name=step_name,
        step_summary=step_summary,
        target_paths=[scenario_path, gen_img_py, images_dir, md_path],
        validate=validate,
        verify_timeout_sec=300,
        attempt=attempt,
    )


# ================================================================== #
# Step 05: 中間確認
# ================================================================== #


async def recover_mid_review_sources(
    ca: dict,
    backup_url: str,
    new_dir: str,
    folder_name: str,
    topic: str,
    *,
    reason: str,
    attempt: int = 1,
) -> bool:
    """Step 05 失敗時の回復として、Step 02〜04 を順に再実行する。"""
    print(f"  [recover] {reason}")
    guide_tts(
        "中間確認の前提をリカバリします。シナリオ訂正、HTML修正、画像生成を順番にやり直します。",
        voice="male",
    )

    if not await step_create_scenario(ca, backup_url, new_dir, folder_name, topic, attempt=attempt):
        return False
    if not await step_update_html(ca, backup_url, new_dir, folder_name, topic, attempt=attempt):
        return False
    if not await step_generate_images(ca, backup_url, new_dir, folder_name, topic, attempt=attempt):
        return False
    return True

async def step_mid_review(
    ca: dict,
    backup_url: str,
    new_dir: str,
    folder_name: str,
    topic: str,
    attempt: int = 1,
) -> bool:
    """
    Step 05: シナリオ・HTML・画像の中間確認を行う。

    音声生成に進む前に、scenario.js と index.html の記述を点検し、
    事実と大きく異なる内容や不適切な言葉があれば修正する。
    画像については、CodeAgents 側で確認可能なら scene ごとの不適切・不一致な
    画像を再生成してよい。中間確認の前提が壊れていた場合は、
    Step 02〜04 を回復処理として再実行してから再試行する。
    """
    sep("Step 05: 中間確認")
    step_name = "Step 05: 中間確認"
    step_summary = (
        f'  "{folder_name}" のシナリオ、HTML、画像を音声生成前に中間確認します。\n'
        "  事実と異なる内容、不適切な言葉、問題のある画像があれば修正します。"
    )

    scenario_path = os.path.join(new_dir, "scenario.js")
    index_path = os.path.join(new_dir, "index.html")
    images_dir = os.path.join(new_dir, "images")
    gen_img_py = os.path.join(new_dir, "_gen_scene_images.py")
    md_path = os.path.join(new_dir, f"{folder_name}.md")
    guide_tts(f"{step_name} を開始します。内容の中間確認を行います。")
    ensure_step_markdown(md_path, folder_name, topic)
    expected_image_count = count_scenario_scenes(scenario_path) if os.path.isfile(scenario_path) else 8

    def count_valid_images() -> int:
        if not os.path.isdir(images_dir):
            return 0
        return sum(
            1
            for f in os.listdir(images_dir)
            if f.endswith(".png") and os.path.getsize(os.path.join(images_dir, f)) > 1000
        )

    current_image_count = count_valid_images()
    if (
        not os.path.isfile(scenario_path)
        or not os.path.isfile(index_path)
        or current_image_count < expected_image_count
    ):
        reason = (
            "Step 05 の前提不足を検知したため、"
            f"Step 02〜04 を再実行します "
            f"(scenario={os.path.isfile(scenario_path)}, index={os.path.isfile(index_path)}, "
            f"images={current_image_count}/{expected_image_count})"
        )
        if not await recover_mid_review_sources(
            ca,
            backup_url,
            new_dir,
            folder_name,
            topic,
            reason=reason,
            attempt=attempt,
        ):
            return False

    prompt = (
        step_instruction_header(step_name, step_summary)
        +
        "以下の観点で中間確認を行い、必要な箇所だけ修正してください。\n\n"
        "【参考ナレッジ】\n"
        f'  - "{NEWS_VIDEO_KNOWLEDGE_PATH}"\n'
        f'  - "{AUTO_VIDEO_KNOWLEDGE_PATH}"\n\n'
        "【確認対象】\n"
        f'  scenario.js: "{scenario_path}"\n'
        f'  index.html: "{index_path}"\n'
        f'  images フォルダ: "{images_dir}"\n'
        f'  画像生成スクリプト: "{gen_img_py}"\n\n'
        "【確認の目的】\n"
        "  音声生成に進む前に、動画内容の品質を中間確認する。\n\n"
        "【確認・修正方針】\n"
        "  1. scenario.js を読み、テーマと照らして事実と大きく異なる内容、\n"
        "     誤解を招く断定、不適切な言葉、攻撃的・差別的・過度に不快な表現があれば修正する。\n"
        "  2. scene_000 の long_narration に、AiDiy の video_generation機能 で作られた旨が入っているか確認し、\n"
        "     short_narration にも概要が反映されているか確認する。無ければ補う。\n"
        "  3. short_narration は短い要約、long_narration は詳しい読み上げ、という役割分担になっているか確認する。\n"
        "     単純コピペなら short_narration を短く整える。\n"
        "  4. 全体の言い回しが、親しみやすく高校生にも伝わる平易さになっているか確認する。\n"
        "     難解な言い回しはやさしく直すが、『高校生向け』のようなメタ説明は追加しない。\n"
        "  5. scene_999 の締めが、楽しく前向きで、AiDiy を試してみたくなる終わり方になっているか確認する。\n"
        "  6. facts / evidence が scene ごとに揃い、\n"
        "     headline・narration・画像内容と矛盾しないか確認する。\n"
        "  7. index.html の title、brand、top-note、説明文も同じ観点で確認し、必要なら修正する。\n"
        "     字幕・音声フォールバックの実装を壊さない。\n"
        "  8. images/*.png は、可能であれば内容を確認し、シーン内容と明らかに合わない画像、\n"
        "     不適切な描写、誤認を招く画像があれば、その画像だけ再生成する。\n"
        "  9. 画像確認が難しい場合は、無理に変更せず、確認できなかった旨を短く報告する。\n"
        "  10. 問題がなければ不要な全面書き換えや再生成はしない。\n\n"
        "【今回のテーマ】\n"
        f"  フォルダ名: {folder_name}\n"
        f"  テーマ詳細: {topic}\n\n"
        "【進捗更新】\n"
        f'  "{md_path}" の「中間確認」チェックを [x] にしてください。\n\n'
        "【完了確認】\n"
        "  最後に、確認した観点、修正したファイル、未修正で問題なしと判断した対象を一覧で表示してください。\n"
    )
    await agent_run(ca, prompt, timeout_sec=600)
    mark_step_done(md_path, "中間確認")

    def validate() -> bool:
        ok1 = check("scenario.js 存在", os.path.isfile(scenario_path))
        ok2 = check("index.html 存在", os.path.isfile(index_path))
        ok3 = check("images フォルダ存在", os.path.isdir(images_dir))
        ok4 = False
        if ok3:
            png_count = count_valid_images()
            ok4 = check(
                f"images/*.png 生成数: {png_count} 件（期待 {expected_image_count} 件以上）",
                expected_image_count > 0 and png_count >= expected_image_count,
            )
        ok5 = False
        if os.path.isfile(md_path):
            with open(md_path, encoding="utf-8-sig") as f:
                ok5 = check("進捗 Markdown に中間確認反映", "- [x] 中間確認" in f.read())
        else:
            check("進捗 Markdown に中間確認反映", False)
        return ok1 and ok2 and ok3 and ok4 and ok5

    ok = await verify_and_backup_until_stable(
        ca=ca,
        backup_url=backup_url,
        step_name=step_name,
        step_summary=step_summary,
        target_paths=[scenario_path, index_path, images_dir, gen_img_py, md_path],
        validate=validate,
        verify_timeout_sec=300,
        attempt=attempt,
    )
    if ok:
        return True

    await recover_mid_review_sources(
        ca,
        backup_url,
        new_dir,
        folder_name,
        topic,
        reason="Step 05 の検証が NG だったため、Step 02〜04 を再実行して次回再試行に備えます",
        attempt=attempt,
    )
    return False


# ================================================================== #
# Step 06: 音声生成
# ================================================================== #

async def step_generate_audio(
    ca: dict,
    backup_url: str,
    new_dir: str,
    folder_name: str,
    topic: str,
    attempt: int = 1,
) -> bool:
    """
    Step 06: ナレーション音声を生成する（mcp 形式）。

    _gen_audio.py をこの Python から確定的に再生成し、その場で実行する。
    補助スクリプトは scenario.js の全シーンの short_narration / long_narration を読み取り、
    audio/short_scene_NNN.mp3 / audio/long_scene_NNN.mp3 として出力する。
    """
    sep("Step 06: 音声生成")
    step_name = "Step 06: 音声生成"
    step_summary = (
        f'  "{folder_name}" の scenario.js からナレーション音声を生成します。\n'
        "  _gen_audio.py を作成・実行し、short/long の MP3 をシーン数ぶん揃えます。"
    )

    audio_dir  = os.path.join(new_dir, "audio")
    scenario_path = os.path.join(new_dir, "scenario.js")
    gen_aud_py = os.path.join(new_dir, "_gen_audio.py")
    md_path    = os.path.join(new_dir, f"{folder_name}.md")
    guide_tts(f"{step_name} を開始します。ナレーション音声を生成します。")
    expected_count = count_scenario_dialogues(scenario_path)

    # ── 既完了チェック ──
    # 最低限の音声数とファイルサイズを見て、空ファイルや生成途中の成果物を除外する。
    if os.path.isdir(audio_dir):
        existing = [
            f for f in os.listdir(audio_dir)
            if f.endswith(".mp3") and os.path.getsize(os.path.join(audio_dir, f)) > 500
        ]
        if len(existing) >= expected_count:
            print(f"  [既存] audio/*.mp3 が {len(existing)} 件存在します。内容検証を行い、問題があれば修正します")

    ensure_step_markdown(md_path, folder_name, topic)
    ensure_dialogue_audio_script(gen_aud_py, audio_dir)
    print(f"  [audio] 補助スクリプトを生成しました: {gen_aud_py}")
    print(f'  [audio] 実行コマンド: "{MCP_PYTHON}" "{gen_aud_py}"')
    run_python_script(gen_aud_py)
    mark_step_done(md_path, "音声生成")

    def validate() -> bool:
        if not os.path.isdir(audio_dir):
            check("audio フォルダ存在", False)
            return False
        mp3s = [
            f for f in os.listdir(audio_dir)
            if f.endswith(".mp3") and os.path.getsize(os.path.join(audio_dir, f)) > 500
        ]
        return check(
            f"audio/*.mp3 生成数: {len(mp3s)} 件（期待 {expected_count} 件）",
            len(mp3s) >= expected_count,
        )

    return await verify_and_backup_until_stable(
        ca=ca,
        backup_url=backup_url,
        step_name=step_name,
        step_summary=step_summary,
        target_paths=[scenario_path, gen_aud_py, audio_dir, md_path],
        validate=validate,
        verify_timeout_sec=300,
        attempt=attempt,
    )


# ================================================================== #
# Step 07: 再生時間更新
# ================================================================== #

async def step_update_durations(
    ca: dict,
    backup_url: str,
    new_dir: str,
    folder_name: str,
    topic: str,
    attempt: int = 1,
) -> bool:
    """
    Step 07: 音声ナレーションの実時間で scenario.js の short/long duration_sec を更新する（mcp 形式）。

    各シーンの short_duration_sec / long_duration_sec を各 MP3 の実再生時間へ置き換え、
    total_short_duration_sec / total_long_duration_sec も再計算する。
    音声が更新済みなら何度実行しても同じ結果になる。
    """
    sep("Step 07: 再生時間更新")
    step_name = "Step 07: 再生時間更新"
    step_summary = (
        f'  "{folder_name}" の音声ファイル実時間で scenario.js の再生時間欄を更新します。\n'
        "  short_duration_sec / long_duration_sec を揃えます。"
    )

    scenario_path = os.path.join(new_dir, "scenario.js")
    audio_dir = os.path.join(new_dir, "audio")
    md_path = os.path.join(new_dir, f"{folder_name}.md")
    guide_tts(f"{step_name} を開始します。音声ナレーションの再生時間を反映します。")

    ensure_step_markdown(md_path, folder_name, topic)
    if not os.path.isfile(scenario_path):
        raise RuntimeError(f"scenario.js が見つかりません: {scenario_path}")
    if not os.path.isdir(audio_dir):
        raise RuntimeError(f"audio フォルダが見つかりません: {audio_dir}")

    result = await update_scenario_audio_durations(scenario_path, new_dir)
    print(
        "  [duration] "
        f"audio={result['audio_count']}件 "
        f"scene={result['scene_count']}件 "
        f"short={result['total_short_duration_sec']}s "
        f"long={result['total_long_duration_sec']}s"
    )
    mark_step_done(md_path, "再生時間更新")

    def validate() -> bool:
        stats = collect_scenario_duration_stats(scenario_path)
        ok1 = check(
            f"short/long duration_sec 更新数: {stats['audio_ok']}/{stats['audio_count']}",
            stats["audio_count"] > 0 and stats["audio_ok"] == stats["audio_count"],
        )
        ok2 = check(
            f"scene short+long 整合数: {stats['scene_ok']}/{stats['scene_count']}",
            stats["scene_count"] > 0 and stats["scene_ok"] == stats["scene_count"],
        )
        ok3 = check(
            "total_short/long_duration_sec 設定済み",
            stats["total_short_duration_sec"] > 0 and stats["total_long_duration_sec"] > 0,
        )
        return ok1 and ok2 and ok3

    return await verify_and_backup_until_stable(
        ca=ca,
        backup_url=backup_url,
        step_name=step_name,
        step_summary=step_summary,
        target_paths=[scenario_path, audio_dir, md_path],
        validate=validate,
        verify_timeout_sec=300,
        attempt=attempt,
    )


# ================================================================== #
# Step 08: 最終確認
# ================================================================== #

async def step_final_review(
    ca: dict,
    backup_url: str,
    new_dir: str,
    folder_name: str,
    topic: str,
    attempt: int = 1,
) -> bool:
    """
    Step 08: 成果物一式を最終確認する。

    scenario.js、画像、音声、index.html、生成補助スクリプトの存在を確認する。
    不足があれば CodeAgents に修正を依頼し、すべて OK のときだけ Step 08 完了として扱う。
    """
    sep("Step 08: 最終確認")
    step_name = "Step 08: 最終確認"
    step_summary = (
        f'  "{folder_name}" の動画素材一式を最終検証します。\n'
        "  scenario.js、index.html、images、audio、生成補助スクリプトを確認します。"
    )

    md_path       = os.path.join(new_dir, f"{folder_name}.md")
    scenario_path = os.path.join(new_dir, "scenario.js")
    images_dir    = os.path.join(new_dir, "images")
    audio_dir     = os.path.join(new_dir, "audio")
    gen_img_py    = os.path.join(new_dir, "_gen_scene_images.py")
    gen_aud_py    = os.path.join(new_dir, "_gen_audio.py")
    expected_audio_count = count_scenario_dialogues(scenario_path) if os.path.isfile(scenario_path) else 0
    expected_image_count = count_scenario_scenes(scenario_path) if os.path.isfile(scenario_path) else 8
    guide_tts(f"{step_name} を開始します。成果物を最終確認します。")
    ensure_step_markdown(md_path, folder_name, topic)

    # ── 既完了チェック ──
    # ビデオページ生成__状況.json が 08 以上の場合、この最終確認は完了済みとして扱う。
    if step_value_to_int(get_completed_step()) >= 8:
        print("  [SKIP] Step 08 は既に完了済みです")
        return True

    prompt = (
        step_instruction_header(step_name, step_summary)
        +
        "以下の手順で最終確認・修正を行ってください。\n\n"
        "【参考ナレッジ】\n"
        f'  - "{NEWS_VIDEO_KNOWLEDGE_PATH}"\n'
        f'  - "{AUTO_VIDEO_KNOWLEDGE_PATH}"\n\n'
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "【確認対象フォルダ】\n"
        f'  "{new_dir}"\n\n'
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "【手順 1】検証スクリプトを書いて実行\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "以下を確認する Python スクリプトを作成して実行してください。\n"
        "実行時は結果を print で出力し、不足項目があれば NG として表示すること。\n\n"
        "  確認 1: scenario.js が存在し 'window.SCENARIO' と 'scene_999' が含まれるか\n"
        f'    パス: "{scenario_path}"\n\n'
        f"  確認 2: images フォルダに *.png が {expected_image_count} 枚以上あるか（各 1000 バイト超）\n"
        f'    パス: "{images_dir}"\n\n'
        f"  確認 3: audio フォルダに *.mp3 が {expected_audio_count} 個以上あるか（各 500 バイト超）\n"
        f'    パス: "{audio_dir}"\n\n'
        "  確認 4: index.html が存在し、今回のフォルダ名が含まれるか\n"
        f'    パス: "{os.path.join(new_dir, "index.html")}"\n\n'
        "  確認 5: _gen_audio.py が存在するか\n"
        f'    パス: "{gen_aud_py}"\n\n'
        "  確認 6: scene_000 の long_narration に、AiDiy の video_generation機能 で作られた旨があるか\n"
        "  確認 7: 各 scene に short_narration / long_narration / short_audio / long_audio があるか\n"
        "  確認 8: index.html に字幕・音声フォールバックの実装が残っているか\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "【手順 2】不足があれば修正\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "手順 1 で NG になった項目があれば、以下の方法で修正してください。\n\n"
        "  ・images/*.png が不足している場合:\n"
        f'      "{MCP_PYTHON}" "{gen_img_py}" を実行して不足分を生成\n'
        "      gen_img_py が存在しなければ新規作成してから実行\n\n"
        "  ・audio/*.mp3 が不足している場合:\n"
        f'      "{MCP_PYTHON}" "{gen_aud_py}" を実行して不足分を生成\n'
        "      _gen_audio.py が存在しなければ新規作成してから実行\n\n"
        "  ・scenario.js に内容不足がある場合:\n"
        f'      "{scenario_path}" を開いて不足フィールドを補完\n\n'
        "  ・index.html が未修正、または今回のフォルダ名が含まれていない場合:\n"
        f'      "{os.path.join(new_dir, "index.html")}" を開いて <title>、.brand、.top-note を修正\n'
        f'      HTML 内に "{folder_name}" が含まれる状態にする\n\n'
        "修正後、手順 1 の検証を再度実行して全項目 OK であることを確認してください。\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "【手順 3】進捗更新と完了確認\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  最後に、修正したファイルと未修正で OK と判断したファイルを一覧表示してください。\n"
    )
    await agent_run(ca, prompt, timeout_sec=600)

    def validate() -> bool:
        ok1 = check("scenario.js 存在", os.path.isfile(scenario_path))
        ok2 = check("index.html 存在", os.path.isfile(os.path.join(new_dir, "index.html")))
        ok3 = check("_gen_scene_images.py 存在", os.path.isfile(gen_img_py))
        ok4 = check("_gen_audio.py 存在", os.path.isfile(gen_aud_py))
        ok5 = check(f"進捗 Markdown 存在: {md_path}", os.path.isfile(md_path))

        ok6 = False
        if os.path.isdir(images_dir):
            pngs = [
                f for f in os.listdir(images_dir)
                if f.endswith(".png") and os.path.getsize(os.path.join(images_dir, f)) > 1000
            ]
            ok6 = check(
                f"images/*.png 生成数: {len(pngs)} 件（期待 {expected_image_count} 件以上）",
                expected_image_count > 0 and len(pngs) >= expected_image_count,
            )
        else:
            check("images フォルダ存在", False)

        ok7 = False
        if os.path.isdir(audio_dir):
            mp3s = [
                f for f in os.listdir(audio_dir)
                if f.endswith(".mp3") and os.path.getsize(os.path.join(audio_dir, f)) > 500
            ]
            required = expected_audio_count if expected_audio_count > 0 else 1
            ok7 = check(f"audio/*.mp3 生成数: {len(mp3s)} 件（期待 {required} 件）", len(mp3s) >= required            )
        else:
            check("audio フォルダ存在", False)

        return ok1 and ok2 and ok3 and ok4 and ok5 and ok6 and ok7

    ok = await verify_and_backup_until_stable(
        ca=ca,
        backup_url=backup_url,
        step_name=step_name,
        step_summary=step_summary,
        target_paths=[
            scenario_path,
            os.path.join(new_dir, "index.html"),
            images_dir,
            audio_dir,
            gen_img_py,
            gen_aud_py,
            md_path,
        ],
        validate=validate,
        verify_timeout_sec=300,
        attempt=attempt,
    )
    if not ok:
        return False

    mark_step_done(md_path, "完成")
    print("  [complete] 最終確認が完了しました")
    return True


# ================================================================== #
# Step 99: 完成案内
# ================================================================== #

async def step_completion_notice(
    ca: dict,
    backup_url: str,
    new_dir: str,
    folder_name: str,
    attempt: int = 1,
) -> bool:
    """
    Step 99: 完成案内だけを行う。

    Step 08 の完了記録を確認し、完了メッセージと音声案内だけを出す。
    """
    sep("Step 99: 完成案内")
    step_name = "Step 99: 完成案内"

    completed_step = get_completed_step()
    if step_value_to_int(completed_step) < 8:
        print(f"  [NG] Step 08 が未完了です（現在: {completed_step or '未実行'}）")
        print("  Step 08: 最終確認 を先に実行してください。")
        return False

    print(f"  [complete] {step_name}: {folder_name}")
    guide_tts("ビデオ生成が完了しました。成果物の確認をお願いします。")
    return True


# ================================================================== #
# main
# ================================================================== #

async def run_automation(config: AutomationConfig) -> None:
    """
    設定済みの AutomationConfig に従い、自動ビデオ生成ワークフローを実行する。
    """
    folder_name = config.folder_name
    topic       = config.topic
    start_step  = config.start_step
    stop_step   = config.stop_step
    new_dir     = config.output_dir
    ensure_steps_json()

    valid_steps = {0, 1, 2, 3, 4, 5, 6, 7, 8, 99}
    if start_step not in valid_steps:
        print(f"ERROR: 実行ステップは 00、01〜08、99 で指定してください（指定値: {start_step}）")
        sys.exit(1)
    if stop_step not in valid_steps:
        print(f"ERROR: 実行ステップは 00、01〜08、99 で指定してください（指定値: {stop_step}）")
        sys.exit(1)
    if start_step > stop_step:
        print(f"ERROR: 実行ステップ指定が不正です（開始={start_step}, 停止={stop_step}）")
        sys.exit(1)

    # ステップ指定なしで既に 99 なら、再実行方法を案内して終了する。
    completed_step = get_completed_step()
    if completed_step == "99" and not config.step_specified:
        message = (
            f"{SCRIPT_TYPE} は既に完了しています。"
            f"再実行する場合は {STEPS_JSON_NAME} の {SCRIPT_TYPE} を空文字にしてください。"
        )
        print(f"\n{STEPS_JSON_NAME} は {SCRIPT_TYPE}=99 です。完了済みとして終了します。")
        print(f"再実行する場合は {SCRIPT_TYPE} を \"\" にしてください: {STEPS_JSON_PATH}")
        guide_tts(message)
        return

    guide_tts(f"AiDiy ビデオ生成を開始します。フォルダ名は {folder_name} です。")

    # ── code_agents HTTP API 初期化 ──
    # auto で利用できる AI CLI / Provider を MCP サーバー側で確認する。
    try:
        ca_info = await asyncio.to_thread(
            post_mcp_method,
            config.code_agents_api_url,
            "config",
            {"project_path": REPO_DIR},
            120,
        )
    except Exception as e:
        print(f"ERROR: CodeAgents HTTP API に接続できません: {e}")
        guide_tts("コードエージェント API に接続できません。処理を中断します。", voice="male")
        sys.exit(1)
    version_info = ca_info.get("version_info", {}) if isinstance(ca_info, dict) else {}
    ca = {
        "api_url": config.code_agents_api_url,
        "version_info": version_info,
    }

    available = [k for k, v in version_info.items() if v.get("ok")]
    if not available:
        print("ERROR: 利用可能な AI がありません")
        guide_tts("利用可能な AI がありません。処理を中断します。", voice="male")
        sys.exit(1)
    print(f"利用可能 AI  : {available}")

    # ── 差分バックアップ API ──
    # 各 CodeAgents 実行後に、検証と POST /aidiy_backup/save/run による差分バックアップ保存を挟む。
    backup_url = config.backup_api_url
    print(f"バックアップAPI: {backup_url}")

    # ── ステップ定義 ──
    # 00: 初期確認、01〜08: 実処理、99: 完成案内、というパターンで並べる。
    steps = [
        (0,  "初期確認",       step00_preflight,     (backup_url, new_dir, folder_name, topic)),
        (1,  "フォルダ作成",   step_create_folder,   (backup_url, new_dir, folder_name, topic)),
        (2,  "シナリオ作成",   step_create_scenario, (backup_url, new_dir, folder_name, topic)),
        (3,  "HTML修正",       step_update_html,     (backup_url, new_dir, folder_name, topic)),
        (4,  "画像生成",       step_generate_images, (backup_url, new_dir, folder_name, topic)),
        (5,  "中間確認",       step_mid_review,      (backup_url, new_dir, folder_name, topic)),
        (6,  "音声生成",       step_generate_audio,  (backup_url, new_dir, folder_name, topic)),
        (7,  "再生時間更新",   step_update_durations,(backup_url, new_dir, folder_name, topic)),
        (8,  "最終確認",       step_final_review,    (backup_url, new_dir, folder_name, topic)),
        (99, "完成案内",       step_completion_notice,(backup_url, new_dir, folder_name)),
    ]

    for step_no, step_name, fn, args in steps:
        if step_no < start_step:
            print(f"\n[Step {step_no:02d}: {step_name}] SKIP（実行ステップ {step_no_to_value(start_step)} より前）")
            continue
        if step_no > stop_step:
            print(f"\n[Step {step_no:02d}: {step_name}] STOP（実行ステップ {step_no_to_value(stop_step)} より後）")
            break
        success = False
        for attempt in range(1, MAX_RETRIES + 1):
            # 各ステップは「作業指示 → Python 側検証」の形に統一する。
            # 検証 NG のときだけ同じステップを再試行し、上限到達で全体を停止する。
            print(f"\n[Step {step_no:02d}: {step_name}] 試行 {attempt}/{MAX_RETRIES}")
            try:
                success = await fn(ca, *args, attempt=attempt)
            except Exception as e:
                print(f"  ERROR: {e}")
                guide_tts(f"{step_name} でエラーが発生しました。再試行します。", voice="male")
                success = False

            if success:
                print(f"  → [Step {step_no:02d}: {step_name}] 完了")
                set_completed_step(step_no)
                if 1 <= step_no <= 8:
                    await refresh_browser_preview(config, f"Step {step_no:02d}: {step_name}")
                break
            else:
                if attempt < MAX_RETRIES:
                    print(f"  → 検証NG。{RETRY_WAIT_SEC}秒後にリトライします...")
                    time.sleep(RETRY_WAIT_SEC)
                else:
                    print(f"\nERROR: [Step {step_no:02d}: {step_name}] が {MAX_RETRIES} 回失敗しました。処理を中断します。")
                    guide_tts(f"{step_name} が {MAX_RETRIES} 回失敗しました。処理を中断します。", voice="male")
                    sys.exit(1)

    # ── 単一ステップ実行の完了確認 ──
    if stop_step < 99:
        print(f"\n実行ステップ {step_no_to_value(stop_step)} の検証を完了しました。")
        guide_tts(f"実行ステップ {step_no_to_value(stop_step)} の検証を完了しました。")
        return

    # ── 完了確認 ──
    completed_step = get_completed_step()
    if completed_step == "99":
        print(f"\n{'=' * 60}")
        print("  ビデオ生成完了!")
        print(f"  フォルダ  : {new_dir}")
        print(f"  ステップ  : {SCRIPT_TYPE}={completed_step}")
        print(f"  管理JSON  : {STEPS_JSON_PATH}")
        print(f"{'=' * 60}")
    else:
        print(f"\nERROR: 完了ステップが 99 ではありません（現在: {completed_step or '未実行'}）")
        guide_tts("完了ステップが記録されませんでした。処理を確認してください。", voice="male")
        sys.exit(1)


def main(argv: list[str] | None = None) -> None:
    """
    AiDiy 自動化ソリューションとしての入口。

    ここに大きな流れを集約し、個別ステップの詳細は step_* 関数へ委譲する。
    """
    args = argv if argv is not None else sys.argv
    if len(args) >= 2 and args[1] in ("-h", "--help", "/?"):
        print_usage()
        return

    # 1. 設定 JSON と CLI 引数から題材、生成先、API、リトライ条件を読み込む。
    config = build_config(args)
    configure_runtime(config)

    # 2. この自動化ソリューションの全体フローと設定を最初に表示する。
    print_automation_flow(config)

    # 3. CodeAgents、TTS、backup API を使いながら、9 ステップの動画生成を進める。
    asyncio.run(run_automation(config))


if __name__ == "__main__":
    main()

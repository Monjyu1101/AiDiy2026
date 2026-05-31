# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# See LICENSE for full terms.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""
ビデオページ生成_解説.py — 二人アバターによる掛け合い解説ビデオ自動生成スクリプト

◆ このスクリプトが作るビデオ:
    女性アバター（AiDiy）と男性アバター（Hermes）の 2 体が掛け合いでニュース・トピックを解説する
    「解説・ニュース型」動画。scenario.js の version は "duo-v2"。
    各シーンは dialogue 配列（speaker: "female"/"male" の交互発言）で構成し、
    音声ファイルは dlg_NNN_NN_speaker.mp3 形式（edge:female / edge:male）で生成する。
    テンプレートは "AiDiy解説__all_ja" フォルダを使用。

使い方:
    cd backend_tools
    .venv\\Scripts\\python aidiy_automations\\ビデオページ生成\\ビデオページ生成_解説.py [実行ステップ番号]
"""

import asyncio
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

MCP_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPO_DIR = os.path.dirname(MCP_DIR)
sys.path.insert(0, MCP_DIR)

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)

from utils.ctx import VideoGenCtx
from utils.runner import VideoGenRunner
from utils.infra import (
    sep, check,
    agent_run, verify_and_backup_until_stable,
    step_instruction_header, guide_tts,
    step_no_to_value, step_value_to_int, get_completed_step,
    ensure_preview_minimum_duration_duo,
    run_python_script,
)
from utils.generation import (
    ensure_scene_image_script, ensure_dialogue_audio_script,
    load_scenario_object, validate_scene_id_range,
    index_html_matches_theme, ensure_step_markdown, mark_step_done,
    backup_images_for_fix_mode, count_scenario_scenes, count_scenario_dialogues,
)
from utils.steps import (
    step00_preflight, step_create_folder, step_generate_audio,
    step_update_durations, step_completion_notice,
)

# ================================================================== #
# 定数
# ================================================================== #

SCRIPT_TYPE = "解説"
SCRIPT_FILE_NAME = os.path.basename(__file__)
SETTING_JSON_NAME = "_ビデオページ生成_解説_設定.json"
STEPS_JSON_NAME = "_ビデオページ生成_解説_状況.json"

SETTING_JSON_PATH = os.path.join(_SCRIPT_DIR, SETTING_JSON_NAME)
STEPS_JSON_PATH = os.path.join(_SCRIPT_DIR, STEPS_JSON_NAME)

NEWS_VIDEO_KNOWLEDGE_PATH = os.path.join(REPO_DIR, ".aidiy", "knowledge", "frontend_web,X系ニュース型掛け合いビデオ.md")
AUTO_VIDEO_KNOWLEDGE_PATH = os.path.join(REPO_DIR, ".aidiy", "knowledge", "共通,mcp利用による自動ビデオ生成手順.md")


# ================================================================== #
# 解説固有: 補助スクリプト生成
# ================================================================== #

def _build_scene_image_prompt_body() -> str:
    return (
        "def build_prompt(scene):\n"
        "    def _clean(v):\n"
        '        return " ".join(str(v or "").replace("\\\\n", " ").replace("\\n", " ").split()).strip()\n'
        "    title = _clean(scene.get('title', ''))\n"
        "    headline = _clean(scene.get('headline', ''))\n"
        "    kicker = _clean(scene.get('kicker', ''))\n"
        "    source_summary = _clean(scene.get('source_summary', ''))\n"
        "    factual = [_clean(x) for x in (scene.get('factual_bullets') or []) if _clean(x)]\n"
        "    forbidden = [_clean(x) for x in (scene.get('forbidden_elements') or []) if _clean(x)]\n"
        "    image_prompt = _clean(scene.get('image_prompt', ''))\n"
        "    lines = ['Create a clean, modern widescreen illustration for a Japanese technology news video.']\n"
        "    if kicker: lines.append(f'Kicker: {kicker}.')\n"
        "    if title: lines.append(f'Title: {title}.')\n"
        "    if headline: lines.append(f'Headline: {headline}.')\n"
        "    if source_summary: lines.append(f'Factual summary: {source_summary}.')\n"
        "    if factual: lines.append('Required elements: ' + '; '.join(factual) + '.')\n"
        "    if image_prompt: lines.append(f'Scene direction: {image_prompt}.')\n"
        "    lines.append('Style: polished product-news visual, cinematic lighting, readable composition, no text overlay baked into the image.')\n"
        "    if forbidden: lines.append('Avoid: ' + '; '.join(forbidden) + '.')\n"
        "    return '\\n'.join(lines).strip()\n"
    )


def _build_dialogue_audio_bodies() -> tuple[str, str, str]:
    load_tasks_body = (
        "def load_tasks():\n"
        '    scenario_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scenario.js")\n'
        '    with open(scenario_file, encoding="utf-8-sig") as f:\n'
        "        content = f.read()\n"
        "    json_str = content.strip()\n"
        '    if json_str.startswith("window.SCENARIO ="):\n'
        '        json_str = json_str[len("window.SCENARIO ="):].strip()\n'
        '    json_str = json_str.rstrip(";").strip()\n'
        "    data = json.loads(json_str)\n"
        "    dialogues = []\n"
        '    for scene in data.get("scenes", []):\n'
        '        scene_num = str(scene.get("id", "")).replace("scene_", "")\n'
        '        for turn, dlg in enumerate(scene.get("dialogue", []), start=1):\n'
        '            speaker = str(dlg.get("speaker", "female") or "female")\n'
        '            text = str(dlg.get("naration_text", "") or "").strip()\n'
        "            if not text:\n"
        "                continue\n"
        "            dialogues.append((scene_num, turn, speaker, text))\n"
        "    return dialogues\n\n"
        "NARRATIONS = load_tasks()\n"
    )
    synthesize_body = (
        "def synthesize_one(text, speaker, out_path):\n"
        "    return post_json(TTS_API_URL, {\n"
        '        "speech_text": text,\n'
        '        "language": TTS_LANGUAGE,\n'
        '        "provider": "edge",\n'
        '        "voice": speaker,\n'
        '        "save_path": out_path,\n'
        "    })\n"
    )
    main_loop_body = (
        "    total = len(NARRATIONS)\n"
        "    done = 0\n"
        "    skip = 0\n"
        "    fail = 0\n"
        "    for scene, turn, speaker, text in NARRATIONS:\n"
        '        fname = f"dlg_{scene}_{turn:02d}_{speaker}.mp3"\n'
        "        fpath = os.path.join(OUTPUT_DIR, fname)\n"
        "        if os.path.exists(fpath) and os.path.getsize(fpath) > 500:\n"
        '            print(f"  [SKIP] {fname}")\n'
        "            skip += 1\n"
        "            continue\n"
        '        print(f"  [GEN ] {fname}")\n'
        "        try:\n"
        "            synthesize_one(text, speaker, fpath)\n"
        "            size = os.path.getsize(fpath) if os.path.exists(fpath) else 0\n"
        "            if size > 500:\n"
        '                print(f"         -> OK ({size:,} bytes)")\n'
        "                done += 1\n"
        "            else:\n"
        '                print("         -> FAIL (empty or too small)")\n'
        "                fail += 1\n"
        "        except Exception as e:\n"
        '            print(f"         -> ERROR: {e}")\n'
        "            fail += 1\n"
        '    print(f"\\n完了: {done} 生成, {skip} スキップ, {fail} 失敗 (合計 {total} 件)")\n'
        "    if fail:\n"
        "        raise SystemExit(1)\n"
    )
    return load_tasks_body, synthesize_body, main_loop_body


# ================================================================== #
# Step 02: シナリオ作成
# ================================================================== #

async def step_create_scenario(ctx: VideoGenCtx, ca: dict, attempt: int = 1) -> bool:
    sep("Step 02: シナリオ作成")
    step_name = "Step 02: シナリオ作成"
    new_dir = ctx.output_dir
    folder_name = ctx.folder_name
    topic = ctx.topic

    step_summary = (
        f'  "{folder_name}" の scenario.js を作成・更新します。\n'
        "  8 シーン構成、掛け合い dialogue、画像・音声パス、AiDiy 説明入りのまとめを整えます。"
    )
    scenario_path = os.path.join(new_dir, "scenario.js")
    md_path       = os.path.join(new_dir, f"{folder_name}.md")
    template_scen = os.path.join(ctx.template_dir, "scenario.js")
    audio_out_dir = f"frontend_web/public/Xビデオ/{folder_name}/audio"
    guide_tts(ctx, f"{step_name} を開始します。テーマに沿った台本を作成します。")

    if os.path.isfile(scenario_path):
        with open(scenario_path, encoding="utf-8") as f:
            c = f.read()
        if "window.SCENARIO" in c and "scene_999" in c and folder_name in c:
            print("  [既存] scenario.js は作成済みです。内容検証を行い、問題があれば修正します")

    fix_mode_prefix = ""
    if ctx.fix_mode and os.path.isfile(scenario_path):
        with open(scenario_path, encoding="utf-8") as _f:
            _existing = _f.read()
        fix_mode_prefix = (
            "【修正モード】\n"
            "  構造（scene ID・音声ファイル名・version・dialogue 形式）は維持してください。\n\n"
            f"【修正前 scenario.js の内容】\n```\n{_existing[:3000]}\n```\n"
            f"【修正の基準となる topic】\n{topic}\n\n"
        )

    prompt = (
        step_instruction_header(ctx, step_name, step_summary)
        + fix_mode_prefix
        + "以下の手順を実行してください。\n\n"
        "【参考ナレッジ】\n"
        f'  - "{NEWS_VIDEO_KNOWLEDGE_PATH}"\n'
        f'  - "{AUTO_VIDEO_KNOWLEDGE_PATH}"\n\n'
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "【作業 A】scenario.js の作成\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f'参照テンプレート: "{template_scen}"\n'
        f'出力先: "{scenario_path}"\n\n'
        '- window.SCENARIO = { ... } 形式を維持\n'
        '- "version": "duo-v2" を維持\n'
        '- "project_name" と top-level の "title" を今回テーマに合わせて更新\n'
        f'- assets_policy.audio_output_dir を "{audio_out_dir}" に変更\n'
        '- tts_male="edge:male", tts_female="edge:female" のまま\n\n'
        "■ scenes 構成（最小7ページ、最大22ページ）\n"
        "  - scene_000: イントロ（掛け合い 4〜5 発言）\n"
        "  - scene_001〜scene_005: 各テーマ（4〜5 発言ずつ）\n"
        "  - scene_999: まとめ（最終発言は female）\n\n"
        "■ 各 dialogue エントリの必須フィールド\n"
        '  "speaker": "female"/"male", "expression": "neutral"\n'
        '  "telop_text": 40〜60文字, "naration_text": 200〜400文字\n'
        '  "audio": "audio/dlg_NNN_NN_speaker.mp3", "duration_sec": 20.0\n\n'
        "■ scene_000 の冒頭要件\n"
        "  - 最初の dialogue は female にする\n"
        "  - AiDiy のビデオページ生成機能で自動生成された旨を naration_text に含める\n\n"
        "■ scene_999 最後の female dialogue に必ず含めること\n"
        "  (1) AiDiy で作られたという説明  (2) チャンネル登録のお願い\n"
        "  (3) AiDiy を使ってみたくなる誘導フレーズ  (4) 楽しく前向きな終わり方\n\n"
        f"■ テーマ: {topic}\n\n"
        f'【作業 B】"{md_path}" の「シナリオ作成」チェックを [x] にしてください。\n\n'
        "【完了確認】scenario.js の先頭10行を表示してください。\n"
    )
    await agent_run(ctx, ca, prompt, timeout_sec=600)

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
        ok3 = validate_scene_id_range(scenario_path, min_mid=5, max_mid=20, label="解説シナリオ") if ok1 else False
        return ok1 and ok2 and ok3

    return await verify_and_backup_until_stable(
        ctx=ctx, ca=ca, backup_url=ctx.backup_api_url,
        step_name=step_name, step_summary=step_summary,
        target_paths=[scenario_path, md_path],
        validate=validate, verify_timeout_sec=300, attempt=attempt,
    )


# ================================================================== #
# Step 03: HTML修正
# ================================================================== #

async def step_update_html(ctx: VideoGenCtx, ca: dict, attempt: int = 1) -> bool:
    sep("Step 03: HTML修正")
    step_name = "Step 03: HTML修正"
    new_dir = ctx.output_dir
    folder_name = ctx.folder_name
    topic = ctx.topic

    step_summary = (
        f'  "{folder_name}" の index.html を scenario.js と今回テーマに合わせて修正します。\n'
        "  <title>、.brand、.top-note、見出しなどのテンプレート元文言を置き換えます。"
    )
    index_path    = os.path.join(new_dir, "index.html")
    scenario_path = os.path.join(new_dir, "scenario.js")
    md_path       = os.path.join(new_dir, f"{folder_name}.md")
    guide_tts(ctx, f"{step_name} を開始します。画面のタイトルと説明を修正します。")

    if index_html_matches_theme(index_path, scenario_path, folder_name, topic):
        print("  [既存] index.html は修正済みです。内容検証を行い、問題があれば修正します")

    fix_mode_prefix_html = ""
    if ctx.fix_mode and os.path.isfile(index_path):
        with open(index_path, encoding="utf-8") as _f:
            _existing_html = _f.read()
        fix_mode_prefix_html = (
            "【修正モード】\n"
            "  HTML/CSS/JS の構造は維持してください。\n\n"
            f"【修正前 index.html の関連部分（先頭抜粋）】\n```\n{_existing_html[:2000]}\n```\n"
            f"【修正の基準となる topic】\n{topic}\n\n"
        )

    prompt = (
        step_instruction_header(ctx, step_name, step_summary)
        + fix_mode_prefix_html
        + "以下の手順で index.html を修正してください。\n\n"
        "【参考ナレッジ】\n"
        f'  - "{NEWS_VIDEO_KNOWLEDGE_PATH}"\n\n'
        "【修正方針】\n"
        "  - HTML/CSS/JavaScript の構造は維持する。\n"
        "  - 2アバター固定表示、無話者の暗転、ステレオパン、リップシンク、字幕表示ロジックは維持する。\n"
        "  - テンプレート元テーマの文言だけを今回のテーマへ置き換える。\n\n"
        "【更新箇所】\n"
        f"  1. <title> タグにフォルダ名またはテーマ名を含める: {folder_name}\n"
        "  2. .brand div の中身を今回の動画ブランド表示へ更新する。\n"
        "  3. .top-note の中身をテーマの簡潔な説明文（1〜2文）へ更新する。\n"
        "  4. 見出し、サブタイトル、説明文などにテンプレート元テーマが残っていれば置き換える。\n\n"
        "【今回のテーマ】\n"
        f"  フォルダ名: {folder_name}\n"
        f"  テーマ詳細: {topic}\n\n"
        f'"{md_path}" の「HTML修正」チェックを [x] にしてください。\n\n'
        "【完了確認】index.html の <title> と .brand と .top-note 周辺を表示してください。\n"
    )
    await agent_run(ctx, ca, prompt, timeout_sec=300)

    def validate() -> bool:
        ok1 = check("index.html 存在", os.path.isfile(index_path))
        ok2 = (
            check("index.html 内容（title + scenario.js + テーマ反映）",
                  index_html_matches_theme(index_path, scenario_path, folder_name, topic))
            if ok1 else False
        )
        return ok1 and ok2

    return await verify_and_backup_until_stable(
        ctx=ctx, ca=ca, backup_url=ctx.backup_api_url,
        step_name=step_name, step_summary=step_summary,
        target_paths=[index_path, scenario_path, md_path],
        validate=validate, verify_timeout_sec=240, attempt=attempt,
    )


# ================================================================== #
# Step 04: 画像生成
# ================================================================== #

async def step_generate_images(ctx: VideoGenCtx, ca: dict, attempt: int = 1) -> bool:
    sep("Step 04: 画像生成")
    step_name = "Step 04: 画像生成"
    new_dir = ctx.output_dir
    folder_name = ctx.folder_name
    topic = ctx.topic

    step_summary = (
        f'  "{folder_name}" の scenario.js から各シーン画像を生成します。\n'
        "  _gen_scene_images.py を作成・実行し、images/scene_*.png を揃えます。"
    )
    images_dir    = os.path.join(new_dir, "images")
    scenario_path = os.path.join(new_dir, "scenario.js")
    gen_img_py    = os.path.join(new_dir, "_gen_scene_images.py")
    md_path       = os.path.join(new_dir, f"{folder_name}.md")
    guide_tts(ctx, f"{step_name} を開始します。シーン画像を生成します。")

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

    orig_images_dir = backup_images_for_fix_mode(ctx, images_dir) if ctx.fix_mode and os.path.isdir(images_dir) else ""

    ensure_scene_image_script(
        ctx, gen_img_py,
        output_dir=os.path.join(new_dir, "images"),
        template_image_dir=orig_images_dir,
        build_prompt_fn=_build_scene_image_prompt_body(),
    )
    print(f"  [image] 補助スクリプトを生成しました: {gen_img_py}")
    print(f'  [image] 実行コマンド: "{ctx.mcp_python}" "{gen_img_py}"')
    run_python_script(ctx.mcp_python, gen_img_py)
    mark_step_done(md_path, "画像生成")

    def validate() -> bool:
        if not os.path.isdir(images_dir):
            check("images フォルダ存在", False)
            return False
        expected = count_scenario_scenes(scenario_path) if os.path.isfile(scenario_path) else 8
        pngs = [f for f in os.listdir(images_dir) if f.endswith(".png") and os.path.getsize(os.path.join(images_dir, f)) > 1000]
        return check(f"images/*.png 生成数: {len(pngs)} 件（期待 {expected} 件以上）", expected > 0 and len(pngs) >= expected)

    return await verify_and_backup_until_stable(
        ctx=ctx, ca=ca, backup_url=ctx.backup_api_url,
        step_name=step_name, step_summary=step_summary,
        target_paths=[scenario_path, gen_img_py, images_dir, md_path],
        validate=validate, verify_timeout_sec=300, attempt=attempt,
    )


# ================================================================== #
# Step 05: 中間確認
# ================================================================== #

async def _recover_sources(ctx: VideoGenCtx, ca: dict, *, reason: str, attempt: int = 1) -> bool:
    print(f"  [recover] {reason}")
    guide_tts(ctx, "中間確認の前提をリカバリします。シナリオ訂正、HTML修正、画像生成を順番にやり直します。", voice="male")
    return (
        await step_create_scenario(ctx, ca, attempt=attempt)
        and await step_update_html(ctx, ca, attempt=attempt)
        and await step_generate_images(ctx, ca, attempt=attempt)
    )


async def step_mid_review(ctx: VideoGenCtx, ca: dict, attempt: int = 1) -> bool:
    sep("Step 05: 中間確認")
    step_name = "Step 05: 中間確認"
    new_dir = ctx.output_dir
    folder_name = ctx.folder_name
    topic = ctx.topic

    step_summary = (
        f'  "{folder_name}" のシナリオ、HTML、画像を音声生成前に中間確認します。\n'
        "  事実と異なる内容、不適切な言葉、問題のある画像があれば修正します。"
    )
    scenario_path = os.path.join(new_dir, "scenario.js")
    index_path    = os.path.join(new_dir, "index.html")
    images_dir    = os.path.join(new_dir, "images")
    gen_img_py    = os.path.join(new_dir, "_gen_scene_images.py")
    md_path       = os.path.join(new_dir, f"{folder_name}.md")
    guide_tts(ctx, f"{step_name} を開始します。内容の中間確認を行います。")
    ensure_step_markdown(md_path, folder_name, topic)
    expected_image_count = count_scenario_scenes(scenario_path) if os.path.isfile(scenario_path) else 8

    def _count_valid_images() -> int:
        return sum(1 for f in os.listdir(images_dir) if f.endswith(".png") and os.path.getsize(os.path.join(images_dir, f)) > 1000) if os.path.isdir(images_dir) else 0

    if not os.path.isfile(scenario_path) or not os.path.isfile(index_path) or _count_valid_images() < expected_image_count:
        reason = (f"Step 05 の前提不足 (scenario={os.path.isfile(scenario_path)}, "
                  f"index={os.path.isfile(index_path)}, images={_count_valid_images()}/{expected_image_count})")
        if not await _recover_sources(ctx, ca, reason=reason, attempt=attempt):
            return False

    prompt = (
        step_instruction_header(ctx, step_name, step_summary)
        + "以下の観点で中間確認を行い、必要な箇所だけ修正してください。\n\n"
        "【参考ナレッジ】\n"
        f'  - "{NEWS_VIDEO_KNOWLEDGE_PATH}"\n'
        f'  - "{AUTO_VIDEO_KNOWLEDGE_PATH}"\n\n'
        "【確認対象】\n"
        f'  scenario.js: "{scenario_path}"\n'
        f'  index.html: "{index_path}"\n'
        f'  images フォルダ: "{images_dir}"\n\n'
        "【確認・修正方針】\n"
        "  1. テーマと照らして事実と大きく異なる内容、不適切な言葉があれば修正する。\n"
        "  2. scene_000 の最初の female 発話に AiDiy ビデオページ生成機能で作られた旨があるか確認する。\n"
        "  3. telop_text は短い字幕、naration_text は詳しい読み上げになっているか確認する。\n"
        "  4. scene_999 の締めが楽しく前向きで AiDiy を試してみたくなるか確認する。\n"
        "  5. index.html の title、brand、top-note も確認し、必要なら修正する。\n"
        "  6. 問題がなければ不要な全面書き換えや再生成はしない。\n\n"
        "【今回のテーマ】\n"
        f"  フォルダ名: {folder_name}\n"
        f"  テーマ詳細: {topic}\n\n"
        f'"{md_path}" の「中間確認」チェックを [x] にしてください。\n'
    )
    await agent_run(ctx, ca, prompt, timeout_sec=600)
    mark_step_done(md_path, "中間確認")

    def validate() -> bool:
        ok1 = check("scenario.js 存在", os.path.isfile(scenario_path))
        ok2 = check("index.html 存在", os.path.isfile(index_path))
        ok3 = check("images フォルダ存在", os.path.isdir(images_dir))
        ok4 = check(f"images/*.png 生成数: {_count_valid_images()}/{expected_image_count}",
                    expected_image_count > 0 and _count_valid_images() >= expected_image_count) if ok3 else False
        ok5 = False
        if os.path.isfile(md_path):
            with open(md_path, encoding="utf-8-sig") as f:
                ok5 = check("進捗 Markdown に中間確認反映", "- [x] 中間確認" in f.read())
        else:
            check("進捗 Markdown に中間確認反映", False)
        return ok1 and ok2 and ok3 and ok4 and ok5

    ok = await verify_and_backup_until_stable(
        ctx=ctx, ca=ca, backup_url=ctx.backup_api_url,
        step_name=step_name, step_summary=step_summary,
        target_paths=[scenario_path, index_path, images_dir, gen_img_py, md_path],
        validate=validate, verify_timeout_sec=300, attempt=attempt,
    )
    if ok:
        return True
    await _recover_sources(ctx, ca, reason="Step 05 の検証が NG だったため Step 02〜04 を再実行します", attempt=attempt)
    return False


# ================================================================== #
# Step 08: 最終確認
# ================================================================== #

async def step_final_review(ctx: VideoGenCtx, ca: dict, attempt: int = 1) -> bool:
    sep("Step 08: 最終確認")
    step_name = "Step 08: 最終確認"
    new_dir = ctx.output_dir
    folder_name = ctx.folder_name

    step_summary = (
        f'  "{folder_name}" の動画素材一式を最終検証します。\n'
        "  scenario.js、index.html、images、audio、生成補助スクリプトを確認します。"
    )
    md_path       = os.path.join(new_dir, f"{folder_name}.md")
    scenario_path = os.path.join(new_dir, "scenario.js")
    images_dir    = os.path.join(new_dir, "images")
    audio_dir     = os.path.join(new_dir, "audio")
    gen_img_py    = os.path.join(new_dir, "_gen_scene_images.py")
    gen_aud_py    = os.path.join(new_dir, "_gen_dialogue_audio.py")
    expected_audio_count = count_scenario_dialogues(scenario_path) if os.path.isfile(scenario_path) else 0
    expected_image_count = count_scenario_scenes(scenario_path) if os.path.isfile(scenario_path) else 8
    guide_tts(ctx, f"{step_name} を開始します。成果物を最終確認します。")
    ensure_step_markdown(md_path, folder_name, ctx.topic)

    if step_value_to_int(get_completed_step(ctx)) >= 8:
        print("  [SKIP] Step 08 は既に完了済みです")
        return True

    prompt = (
        step_instruction_header(ctx, step_name, step_summary)
        + "以下の手順で最終確認・修正を行ってください。\n\n"
        "【参考ナレッジ】\n"
        f'  - "{NEWS_VIDEO_KNOWLEDGE_PATH}"\n'
        f'  - "{AUTO_VIDEO_KNOWLEDGE_PATH}"\n\n'
        "【確認対象フォルダ】\n"
        f'  "{new_dir}"\n\n'
        "【手順 1】検証スクリプトを書いて実行\n"
        "  確認 1: scenario.js が存在し 'window.SCENARIO' と 'scene_999' が含まれるか\n"
        f"  確認 2: images フォルダに *.png が {expected_image_count} 枚以上あるか\n"
        f"  確認 3: audio フォルダに *.mp3 が {expected_audio_count} 個以上あるか\n"
        "  確認 4: index.html が存在し、今回のフォルダ名が含まれるか\n"
        f"  確認 5: _gen_dialogue_audio.py が存在するか\n"
        "  確認 6: scene_000 の最初の female 発話に AiDiy のビデオページ生成機能で作られた旨があるか\n\n"
        "【手順 2】不足があれば修正\n"
        f'  images 不足: "{ctx.mcp_python}" "{gen_img_py}" を実行\n'
        f'  audio 不足:  "{ctx.mcp_python}" "{gen_aud_py}" を実行\n\n'
        "  最後に、修正したファイルと未修正で OK と判断したファイルを一覧表示してください。\n"
    )
    await agent_run(ctx, ca, prompt, timeout_sec=600)

    def validate() -> bool:
        ok1 = check("scenario.js 存在", os.path.isfile(scenario_path))
        ok2 = check("index.html 存在", os.path.isfile(os.path.join(new_dir, "index.html")))
        ok3 = check("_gen_scene_images.py 存在", os.path.isfile(gen_img_py))
        ok4 = check("_gen_dialogue_audio.py 存在", os.path.isfile(gen_aud_py))
        ok5 = check(f"進捗 Markdown 存在: {md_path}", os.path.isfile(md_path))
        ok6 = False
        if os.path.isdir(images_dir):
            pngs = [f for f in os.listdir(images_dir) if f.endswith(".png") and os.path.getsize(os.path.join(images_dir, f)) > 1000]
            ok6 = check(f"images/*.png 生成数: {len(pngs)}/{expected_image_count}", expected_image_count > 0 and len(pngs) >= expected_image_count)
        else:
            check("images フォルダ存在", False)
        ok7 = False
        if os.path.isdir(audio_dir):
            mp3s = [f for f in os.listdir(audio_dir) if f.endswith(".mp3") and os.path.getsize(os.path.join(audio_dir, f)) > 500]
            required = expected_audio_count if expected_audio_count > 0 else 1
            ok7 = check(f"audio/*.mp3 生成数: {len(mp3s)}/{required}", len(mp3s) >= required)
        else:
            check("audio フォルダ存在", False)
        return ok1 and ok2 and ok3 and ok4 and ok5 and ok6 and ok7

    ok = await verify_and_backup_until_stable(
        ctx=ctx, ca=ca, backup_url=ctx.backup_api_url,
        step_name=step_name, step_summary=step_summary,
        target_paths=[scenario_path, os.path.join(new_dir, "index.html"), images_dir, audio_dir, gen_img_py, gen_aud_py, md_path],
        validate=validate, verify_timeout_sec=300, attempt=attempt,
    )
    if not ok:
        return False
    mark_step_done(md_path, "完成")
    print("  [complete] 最終確認が完了しました")
    return True


# ================================================================== #
# main
# ================================================================== #

def main(argv: list | None = None) -> None:
    args = argv if argv is not None else sys.argv
    if len(args) >= 2 and args[1] in ("-h", "--help", "/?"):
        print(f"使い方: python aidiy_automations\\ビデオページ生成\\{SCRIPT_FILE_NAME} [実行ステップ番号]")
        return

    runner = VideoGenRunner.from_argv(
        args, SCRIPT_TYPE, SETTING_JSON_PATH, STEPS_JSON_PATH,
        mcp_dir=MCP_DIR, repo_dir=REPO_DIR,
        progress_tts_language="ja", progress_tts_provider="edge",
        use_english_voice=False,
    )
    runner.print_flow()
    ctx = runner.ctx
    new_dir = ctx.output_dir
    gen_aud_py = os.path.join(new_dir, "_gen_dialogue_audio.py")

    load_tasks_body, synthesize_body, main_loop_body = _build_dialogue_audio_bodies()

    async def _step_gen_audio(ca: dict, attempt: int = 1) -> bool:
        ensure_dialogue_audio_script(
            ctx, gen_aud_py,
            output_dir=os.path.join(new_dir, "audio"),
            load_tasks_body=load_tasks_body,
            synthesize_body=synthesize_body,
            main_loop_body=main_loop_body,
            script_docstring="掛け合い音声生成スクリプト（duo-v2 形式）",
        )
        return await step_generate_audio(ctx, ca, gen_aud_py, "_gen_dialogue_audio.py", attempt=attempt)

    steps = [
        (0,  "初期確認",     lambda ca, attempt=1: step00_preflight(ctx, ca, attempt=attempt)),
        (1,  "フォルダ作成", lambda ca, attempt=1: step_create_folder(ctx, ca, (NEWS_VIDEO_KNOWLEDGE_PATH, AUTO_VIDEO_KNOWLEDGE_PATH), attempt=attempt)),
        (2,  "シナリオ作成", lambda ca, attempt=1: step_create_scenario(ctx, ca, attempt=attempt)),
        (3,  "HTML修正",     lambda ca, attempt=1: step_update_html(ctx, ca, attempt=attempt)),
        (4,  "画像生成",     lambda ca, attempt=1: step_generate_images(ctx, ca, attempt=attempt)),
        (5,  "中間確認",     lambda ca, attempt=1: step_mid_review(ctx, ca, attempt=attempt)),
        (6,  "音声生成",     _step_gen_audio),
        (7,  "再生時間更新", lambda ca, attempt=1: step_update_durations(ctx, ca, attempt=attempt)),
        (8,  "最終確認",     lambda ca, attempt=1: step_final_review(ctx, ca, attempt=attempt)),
        (99, "完成案内",     lambda ca, attempt=1: step_completion_notice(ctx, ca, attempt=attempt)),
    ]

    asyncio.run(runner.run(steps, ensure_fn=ensure_preview_minimum_duration_duo))


if __name__ == "__main__":
    main()

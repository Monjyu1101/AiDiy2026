# -*- coding: utf-8 -*-
"""
steps.py — 3 スクリプト共通ステップ実装

step00_preflight, step_create_folder, step_generate_audio,
step_update_durations, step_mid_review, step_final_review,
step_completion_notice を提供する。

各関数は ctx: VideoGenCtx を受け取り、グローバル変数に依存しない。
"""

from __future__ import annotations

import os
import shutil
import sys
import time

from .ctx import VideoGenCtx
from .log_config import get_logger

_logger = get_logger("video_gen.steps")
from .infra import (
    sep, check, run_python_script,
    step_no_to_value, step_value_to_int,
    get_completed_step, set_completed_step, ensure_steps_json,
    guide_tts, refresh_browser_preview, start_final_playback,
    agent_run, step_instruction_header,
    verify_and_backup_until_stable,
    post_backup_api,
)
from .generation import (
    ensure_step_markdown, mark_step_done,
    count_scenario_scenes, count_scenario_dialogues,
    collect_scenario_duration_stats, update_scenario_audio_durations,
)


# ================================================================== #
# Step 00: 初期確認
# ================================================================== #

async def step00_preflight(ctx: VideoGenCtx, ca: dict, attempt: int = 1) -> bool:
    """Step 00: 自動化を始める前の初期確認。"""
    from .infra import _post_backup_api  # noqa: PLC0415
    step_name = "Step 00: 初期確認"
    sep(step_name)

    tts_msg = (
        "Step zero, preflight is starting. I will check the settings, template, APIs, and available AI agents."
        if ctx.use_english_voice else
        "ステップゼロ、初期確認を開始します。設定、テンプレート、API、AIの利用可否を確認します。"
    )
    guide_tts(ctx, tts_msg)

    ok_template = check(f"テンプレート存在: {ctx.template_dir}", os.path.isdir(ctx.template_dir))
    ok_base = check(f"生成先ルート存在: {ctx.video_base_dir}", os.path.isdir(ctx.video_base_dir))
    ok_folder = check("フォルダ名指定", bool(ctx.folder_name.strip()))
    ok_topic = check("トピック指定", bool(ctx.topic.strip()))
    version_info = ca.get("version_info", {})
    ok_agents = check("CodeAgents HTTP API 利用可能", bool([k for k, v in version_info.items() if v.get("ok")]))

    try:
        post_backup_api(ctx.backup_api_url, dry_run=True)
        ok_backup = check(f"backup API 疎通: {ctx.backup_api_url}", True)
    except Exception as e:
        print(f"  [backup] 疎通確認 NG: {e}")
        ok_backup = check(f"backup API 疎通: {ctx.backup_api_url}", False)

    if ctx.tts_guide:
        try:
            tts_check_msg = (
                "This is the progress voice check. The AiDiy automation can start."
                if ctx.use_english_voice else
                "音声案内の確認です。AiDiy 自動化ソリューションを開始できます。"
            )
            guide_tts(ctx, tts_check_msg)
            ok_tts = check(f"tts API 案内: {ctx.tts_api_url}", True)
        except Exception as e:
            print(f"  [tts] 疎通確認 NG: {e}")
            ok_tts = check(f"tts API 案内: {ctx.tts_api_url}", False)
    else:
        ok_tts = check("tts API 案内: OFF", True)

    print(f"  出力予定: {ctx.output_dir}")
    return ok_template and ok_base and ok_folder and ok_topic and ok_agents and ok_backup and ok_tts


# ================================================================== #
# Step 01: フォルダ作成
# ================================================================== #

def _テンプレートを機械コピー(template_dir: str, new_dir: str) -> tuple[list[str], list[str]]:
    """テンプレートフォルダを Python で直接コピーする。

    以前は AI へ robocopy を実行させていたが、コマンドの成否がエージェント任せになり
    フォルダ作成が失敗することがあったため、コピー自体はここで機械的に済ませる
    （AI には結果の確認だけを依頼する）。

    - audio / images / __pycache__ の中身はコピーしない（各動画で生成するため）
    - テンプレート側の進捗 Markdown はコピーしない（今回のテーマで作り直すため）
    - 既存ファイルは上書きしない（作りかけの成果物を壊さないため）

    戻り値: (コピーしたファイル名, 既存のため据え置いたファイル名)
    """
    除外フォルダ = {"audio", "images", "__pycache__", ".git"}
    コピー済: list[str] = []
    据え置き: list[str] = []
    for root, dirs, files in os.walk(template_dir):
        dirs[:] = [d for d in dirs if d not in 除外フォルダ]
        相対 = os.path.relpath(root, template_dir)
        出力先 = new_dir if 相対 == "." else os.path.join(new_dir, 相対)
        os.makedirs(出力先, exist_ok=True)
        for name in files:
            if name.lower().endswith(".md"):
                continue  # 進捗 Markdown は ensure_step_markdown が今回のテーマで作る
            dst = os.path.join(出力先, name)
            if os.path.isfile(dst):
                据え置き.append(name)
                continue
            shutil.copy2(os.path.join(root, name), dst)
            コピー済.append(name)
    return コピー済, 据え置き


async def step_create_folder(
    ctx: VideoGenCtx,
    ca: dict,
    knowledge_paths: tuple[str, str],
    attempt: int = 1,
) -> bool:
    """Step 01: 出力フォルダの土台を作成する。

    テンプレートのコピー・images/audio の作成・進捗 Markdown の作成は Python 側で機械的に行い、
    AI には「揃っているか」「テンプレート由来の文言が残っていないか」の確認だけを依頼する。
    """
    sep("Step 01: フォルダ作成")
    step_name = "Step 01: フォルダ作成"
    new_dir = ctx.output_dir
    folder_name = ctx.folder_name
    topic = ctx.topic
    template_dir = ctx.template_dir
    # knowledge_paths は他ステップと同じ引数で受けるが、このステップでは渡さない。
    # 存在確認だけの作業にナレッジは不要で、読ませると調査が始まりタイムアウトの原因になる。
    _ = knowledge_paths

    # topic 全文（2000字超）は貼らない。フォルダの存在確認に内容は要らず、
    # 長い指示ほど AI が余計な調査を始めてタイムアウトしやすくなるため。
    step_summary = (
        f'  動画フォルダ "{new_dir}" を用意します。\n'
        "  テンプレートからのコピー、images/・audio/ の作成、進捗 Markdown の用意は\n"
        "  このスクリプトが Python で実行済みです。AI 側はファイルの存在確認だけを行ってください。"
    )

    md_path    = os.path.join(new_dir, f"{folder_name}.md")
    index_path = os.path.join(new_dir, "index.html")
    tts_msg = (
        "AiDiy automation is starting. Step one, folder preparation will prepare the video folder."
        if ctx.use_english_voice else
        f"AiDiy 自動化ソリューションを開始します。{step_name}、動画フォルダを準備します。"
    )
    guide_tts(ctx, tts_msg)

    folder_already_exists = (
        os.path.isdir(new_dir)
        and os.path.isfile(index_path)
        and os.path.isfile(os.path.join(new_dir, "scenario.js"))
    )
    if folder_already_exists:
        print("  [既存] コピー先に index.html / scenario.js が存在します。テンプレートからのコピーは行いません")
    else:
        print("  [新規] テンプレートからフォルダを作成します")

    images_dir = os.path.join(new_dir, "images")
    audio_dir = os.path.join(new_dir, "audio")

    # テンプレートのコピーは AI に任せず機械的に行う。ただし出力フォルダが既にある場合は一切コピーしない
    # （途中まで作った scenario.js などをテンプレートで壊さないため）
    os.makedirs(new_dir, exist_ok=True)
    if not folder_already_exists:
        try:
            コピー済, 据え置き = _テンプレートを機械コピー(template_dir, new_dir)
            print(f"  [copy] テンプレートから {len(コピー済)} 件コピーしました（既存のため据え置き {len(据え置き)} 件）")
            if コピー済:
                表示 = ", ".join(コピー済[:12]) + (" ..." if len(コピー済) > 12 else "")
                print(f"         {表示}")
        except Exception as e:
            print(f"  [copy] テンプレートのコピーに失敗しました: {e}")
            _logger.exception("テンプレートのコピーに失敗しました")

    # images / audio と進捗 Markdown も AI を待たずに用意する（AI 側は確認だけ）
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)
    ensure_step_markdown(md_path, folder_name, topic)

    # 指示は「存在確認だけ」に絞る。調査・修正の余地を残すと AI が読み込みや点検を始め、
    # フォルダ作成ステップが実行タイムアウトまで伸びるため。
    prompt = (
        step_instruction_header(ctx, step_name, step_summary)
        + "このステップで行うのは、下記ファイルの存在確認だけです。\n"
        "コピー・作成・修正・調査は一切行わないでください。ファイルの中身を開く必要もありません。\n\n"
        "【確認するもの】次の 5 つがあるかどうかだけを見てください\n"
        f'  "{index_path}"\n'
        f'  "{os.path.join(new_dir, "scenario.js")}"\n'
        f'  "{images_dir}"（この時点では空でよい）\n'
        f'  "{audio_dir}"（この時点では空でよい）\n'
        f'  "{md_path}"\n\n'
        "【やらないこと】\n"
        "  - robocopy / copy などでのコピー（Python 側で実行済みです）\n"
        "  - 既存ファイルの上書き・削除・内容修正\n"
        "  - index.html や scenario.js の中身の確認\n"
        "    （テンプレートのテーマのままで正常です。Step 03 で更新します）\n"
        "  - 参考資料・ナレッジ・設定ファイルの読み込み\n"
        "  - 他フォルダの調査\n"
        + (
            ""
            if not folder_already_exists else
            f'  - テンプレートからのコピー（"{new_dir}" には作りかけの内容が入っています）\n'
        )
        + "\n"
        "【報告】フォルダ直下のファイル一覧を表示し、上の 5 つが揃っているかだけ答えてください。\n"
        "  足りないものがあれば名前を挙げるだけにしてください（補完は不要です）。\n"
    )
    await agent_run(ctx, ca, prompt, timeout_sec=180)

    # AI が誤って消した場合に備えて、確認後にもう一度だけ整える（既存は壊さない）
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)
    ensure_step_markdown(md_path, folder_name, topic)

    def validate() -> bool:
        ok1 = check(f"フォルダ存在: {new_dir}", os.path.isdir(new_dir))
        ok2 = check("index.html 存在", os.path.isfile(index_path))
        ok3 = check("scenario.js 存在", os.path.isfile(os.path.join(new_dir, "scenario.js")))
        ok4 = check("images / audio フォルダ存在",
                    os.path.isdir(images_dir) and os.path.isdir(audio_dir))
        ok5 = check("進捗 Markdown 存在", os.path.isfile(md_path))
        return ok1 and ok2 and ok3 and ok4 and ok5

    return await verify_and_backup_until_stable(
        ctx=ctx, ca=ca,
        step_name=step_name, step_summary=step_summary,
        target_paths=[new_dir, index_path, os.path.join(new_dir, "scenario.js"), md_path],
        # 存在確認だけのステップなので検証エージェントにも長い時間を与えない
        validate=validate, verify_timeout_sec=180, attempt=attempt,
    )


# ================================================================== #
# Step 06: 音声生成
# ================================================================== #

async def step_generate_audio(
    ctx: VideoGenCtx,
    ca: dict,
    gen_aud_py: str,
    audio_script_name: str,
    attempt: int = 1,
) -> bool:
    """Step 06: ナレーション / 掛け合い音声を生成する。"""
    sep("Step 06: 音声生成")
    step_name = "Step 06: 音声生成"
    new_dir = ctx.output_dir
    folder_name = ctx.folder_name
    topic = ctx.topic
    audio_dir = os.path.join(new_dir, "audio")
    scenario_path = os.path.join(new_dir, "scenario.js")
    md_path = os.path.join(new_dir, f"{folder_name}.md")

    step_summary = (
        f'  "{folder_name}" の scenario.js からナレーション音声を生成します。\n'
        f"  {audio_script_name} を作成・実行し、音声 MP3 を全件揃えます。"
    )

    tts_msg = (
        "Step six, audio generation is starting. I will generate the narration audio."
        if ctx.use_english_voice else
        f"{step_name} を開始します。ナレーション音声を生成します。"
    )
    guide_tts(ctx, tts_msg)
    expected_count = count_scenario_dialogues(scenario_path)

    if os.path.isdir(audio_dir):
        existing = [
            f for f in os.listdir(audio_dir)
            if f.endswith(".mp3") and os.path.getsize(os.path.join(audio_dir, f)) > 500
        ]
        if len(existing) >= expected_count:
            print(f"  [既存] audio/*.mp3 が {len(existing)} 件存在します。内容検証を行い、問題があれば修正します")

    ensure_step_markdown(md_path, folder_name, topic)
    print(f"  [audio] 補助スクリプトを生成しました: {gen_aud_py}")
    print(f'  [audio] 実行コマンド: "{ctx.mcp_python}" "{gen_aud_py}"')
    run_python_script(ctx.mcp_python, gen_aud_py)
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
        ctx=ctx, ca=ca,
        step_name=step_name, step_summary=step_summary,
        target_paths=[scenario_path, gen_aud_py, audio_dir, md_path],
        validate=validate, verify_timeout_sec=300, attempt=attempt,
    )


# ================================================================== #
# Step 07: 再生時間更新
# ================================================================== #

async def step_update_durations(ctx: VideoGenCtx, ca: dict, attempt: int = 1) -> bool:
    """Step 07: 音声ナレーションの実時間で scenario.js の duration_sec を更新する。"""
    sep("Step 07: 再生時間更新")
    step_name = "Step 07: 再生時間更新"
    new_dir = ctx.output_dir
    folder_name = ctx.folder_name
    topic = ctx.topic
    scenario_path = os.path.join(new_dir, "scenario.js")
    audio_dir = os.path.join(new_dir, "audio")
    md_path = os.path.join(new_dir, f"{folder_name}.md")

    step_summary = (
        f'  "{folder_name}" の音声ファイル実時間で scenario.js の再生時間欄を更新します。\n'
        "  duration_sec / short_duration_sec / long_duration_sec を揃えます。"
    )

    tts_msg = (
        "Step seven, duration update is starting. I will update the playback durations from the generated audio."
        if ctx.use_english_voice else
        f"{step_name} を開始します。音声ナレーションの再生時間を反映します。"
    )
    guide_tts(ctx, tts_msg)

    ensure_step_markdown(md_path, folder_name, topic)
    if not os.path.isfile(scenario_path):
        raise RuntimeError(f"scenario.js が見つかりません: {scenario_path}")
    if not os.path.isdir(audio_dir):
        raise RuntimeError(f"audio フォルダが見つかりません: {audio_dir}")

    result = await update_scenario_audio_durations(ctx, scenario_path, new_dir)

    if "dialogue_count" in result and result.get("total_duration_sec", 0) > 0:
        print(
            "  [duration] "
            f"dialogue={result['dialogue_count']}件 "
            f"scene={result['scene_count']}件 "
            f"total_duration_sec={result['total_duration_sec']}"
        )
    else:
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
            f"duration_sec 更新数: {stats['audio_ok']}/{stats['audio_count']}",
            stats["audio_count"] > 0 and stats["audio_ok"] == stats["audio_count"],
        )
        ok2 = check(
            f"scene duration 整合数: {stats['scene_ok']}/{stats['scene_count']}",
            stats["scene_count"] > 0 and stats["scene_ok"] == stats["scene_count"],
        )
        ok3 = check(
            "total duration 設定済み",
            stats["total_short_duration_sec"] > 0 and stats["total_long_duration_sec"] > 0,
        )
        return ok1 and ok2 and ok3

    return await verify_and_backup_until_stable(
        ctx=ctx, ca=ca,
        step_name=step_name, step_summary=step_summary,
        target_paths=[scenario_path, audio_dir, md_path],
        validate=validate, verify_timeout_sec=300, attempt=attempt,
    )


# ================================================================== #
# Step 99: 完成案内
# ================================================================== #

async def step_completion_notice(ctx: VideoGenCtx, ca: dict, attempt: int = 1) -> bool:
    """Step 99: 完成案内だけを行う。"""
    sep("Step 99: 完成案内")

    completed_step = get_completed_step(ctx)
    if step_value_to_int(completed_step) < 8:
        print(f"  [NG] Step 08 が未完了です（現在: {completed_step or '未実行'}）")
        print("  Step 08: 最終確認 を先に実行してください。")
        return False

    print(f"  [complete] Step 99: 完成案内: {ctx.folder_name}")
    tts_msg = (
        "Video generation is complete. Please review the output artifacts."
        if ctx.use_english_voice else
        "ビデオ生成が完了しました。成果物の確認をお願いします。"
    )
    guide_tts(ctx, tts_msg)
    return True


# ================================================================== #
# メインループ
# ================================================================== #

async def run_automation_loop(
    ctx: VideoGenCtx,
    ca: dict,
    steps: list,
    ensure_fn,
) -> None:
    """
    steps リストに従ってステップを順次実行する共通ループ。

    Parameters
    ----------
    ctx : VideoGenCtx
    ca : dict
        CodeAgents 情報 {"api_url": ..., "version_info": ...}
    steps : list of (step_no, step_name, async_fn)
        async_fn は (ca, attempt=1) -> bool のシグネチャ
    ensure_fn : callable
        index.html にプレビューパッチを当てる関数
    """
    start_step = ctx.start_step
    stop_step  = ctx.stop_step
    is_fix_mode = ctx.fix_mode

    if is_fix_mode:
        print(f"  [修正モード] コピー元とコピー先が同じフォルダのため Step 01 を自動スキップします: {ctx.template_dir}")

    for step_no, step_name, fn in steps:
        if step_no < start_step:
            print(f"\n[Step {step_no:02d}: {step_name}] SKIP（実行ステップ {step_no_to_value(start_step)} より前）")
            continue
        if step_no == 1 and is_fix_mode:
            print("\n[Step 01: フォルダ作成] AUTO-SKIP（修正モード: コピー元 = コピー先）")
            set_completed_step(ctx, 1)
            continue
        if step_no > stop_step:
            print(f"\n[Step {step_no:02d}: {step_name}] STOP（実行ステップ {step_no_to_value(stop_step)} より後）")
            break

        success = False
        for attempt in range(1, ctx.max_retries + 1):
            print(f"\n[Step {step_no:02d}: {step_name}] 試行 {attempt}/{ctx.max_retries}")
            _logger.info("Step %02d [%s] 試行 %d/%d 開始", step_no, step_name, attempt, ctx.max_retries)
            try:
                success = await fn(ca, attempt=attempt)
            except Exception as e:
                print(f"  ERROR: {e}")
                _logger.error("Step %02d [%s] 例外: %s", step_no, step_name, e, exc_info=True)
                err_msg = (
                    f"Step {step_no:02d} raised an error. Retrying."
                    if ctx.use_english_voice else
                    f"{step_name} でエラーが発生しました。再試行します。"
                )
                guide_tts(ctx, err_msg, voice="male")
                success = False

            if success:
                print(f"  → [Step {step_no:02d}: {step_name}] 完了")
                _logger.info("Step %02d [%s] 完了", step_no, step_name)
                set_completed_step(ctx, step_no)
                # 生成途中は無音プレビュー、最終チェックが通ったら音声つきループ再生へ切り替える
                if 1 <= step_no <= 7:
                    await refresh_browser_preview(
                        ctx,
                        f"Step {step_no:02d}: {step_name}",
                        ensure_fn=ensure_fn,
                        speaker_enabled=False,
                    )
                elif step_no in (8, 99):
                    await start_final_playback(ctx, f"Step {step_no:02d}: {step_name}")
                break
            else:
                if attempt < ctx.max_retries:
                    print(f"  → 検証NG。{ctx.retry_wait_sec}秒後にリトライします...")
                    _logger.warning("Step %02d [%s] 検証NG: %d秒後リトライ", step_no, step_name, ctx.retry_wait_sec)
                    time.sleep(ctx.retry_wait_sec)
                else:
                    print(f"\nERROR: [Step {step_no:02d}: {step_name}] が {ctx.max_retries} 回失敗しました。処理を中断します。")
                    _logger.error("Step %02d [%s] %d回失敗で中断", step_no, step_name, ctx.max_retries)
                    fail_msg = (
                        f"Step {step_no:02d} failed {ctx.max_retries} times. Stopping."
                        if ctx.use_english_voice else
                        f"{step_name} が {ctx.max_retries} 回失敗しました。処理を中断します。"
                    )
                    guide_tts(ctx, fail_msg, voice="male")
                    sys.exit(1)

    if stop_step < 99:
        done_val = step_no_to_value(stop_step)
        print(f"\n実行ステップ {done_val} の検証を完了しました。")
        done_msg = (
            f"Verification for requested step {done_val} is complete."
            if ctx.use_english_voice else
            f"実行ステップ {done_val} の検証を完了しました。"
        )
        guide_tts(ctx, done_msg)
        return

    completed_step = get_completed_step(ctx)
    if completed_step == "99":
        new_dir = ctx.output_dir
        print(f"\n{'=' * 60}")
        print("  ビデオ生成完了!")
        print(f"  フォルダ  : {new_dir}")
        print(f"  ステップ  : complete_steps={completed_step}")
        print(f"  管理JSON  : {ctx.steps_json_path}")
        print(f"{'=' * 60}")
    else:
        print(f"\nERROR: 完了ステップが 99 ではありません（現在: {completed_step or '未実行'}）")
        guide_tts(ctx, "完了ステップが記録されませんでした。処理を確認してください。", voice="male")
        sys.exit(1)

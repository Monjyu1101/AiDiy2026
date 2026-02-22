#!/usr/bin/env python
# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101
# -------------------------------------------------------------------------

from log_config import get_logger
logger = get_logger(__name__)

import os
import time
import datetime
import asyncio
import base64
from pathlib import Path
from typing import Optional
from PIL import Image
import io


class CodeAI:
    """
    CLI (subprocess) ベース CodeAI統合クラス
    claude code などのコマンドラインツールをsubprocessで実行
    """

    def __init__(self, 親=None, セッションID: str = "", チャンネル: int = 0, 絶対パス: str = None,
                 AI_NAME: str = "claude_cli", AI_MODEL: str = "auto", max_turns: int = 999,
                 code_plan: str = "auto", code_verify: str = "auto", system_instruction: str = None):
        """初期化"""

        # セッションID・チャンネル
        self.セッションID = セッションID
        self.チャンネル = チャンネル

        # 親参照（セッションマネージャー）
        self.parent_manager = 親
        self.親 = 親

        # プロバイダー設定
        self.code_ai = AI_NAME
        self.code_model = AI_MODEL
        self.max_turns = max_turns
        self.code_plan = code_plan
        self.code_verify = code_verify
        self.system_instruction = system_instruction if isinstance(system_instruction, str) and system_instruction else None

        # 作業ディレクトリ設定
        work_dir_input = 絶対パス if isinstance(絶対パス, str) else None
        if work_dir_input and isinstance(work_dir_input, str):
            work_dir = Path(work_dir_input)
        else:
            work_dir = Path.cwd()

        self.cwd_str = work_dir.resolve().as_posix()  # "/" 区切りに統一
        self.base_abs_path = self.cwd_str

        # システムプロンプトを構築
        self.system_prompt = self._システムプロンプト構築()

        # 履歴管理システム(ローカル保管)
        self.履歴最終番号 = 0
        self.履歴最終時刻 = time.time()
        self.履歴辞書 = {}

        # 生存状態管理
        self.is_alive = True
        self._停止マーカー送信済み = False

        # セッション状態管理（初回判定用）
        self.session_started = False

        # codex専用：セッションID管理
        self.codex_セッションID = None

        # 最終実行のstderr出力（セッションID抽出用）
        self.last_stderr_output = ""

        # 現在実行中のsubprocess（強制終了用）
        self.current_process: Optional[asyncio.subprocess.Process] = None

    def _コマンド構築(self, プロンプト: str, 初回: bool = False, repo_path: str = None, 読取専用: bool = False) -> list:
        """
        プロバイダー別のコマンドを構築

        Args:
            プロンプト: 送信するプロンプト
            初回: 初回送信かどうか

        Returns:
            コマンド配列
        """
        # プロンプトから改行削除
        プロンプト = プロンプト.replace('\n', ' ').replace('\r', ' ').strip()

        # 環境変数からカスタムコマンドパスを取得（オプション）
        custom_cmd = os.environ.get(f'{self.code_ai.upper()}_CLI_PATH')

        if self.code_ai == "copilot_cli":
            # GitHub Copilot CLI
            if custom_cmd:
                cmd = custom_cmd
            else:
                if os.name == 'nt':
                    # Windows: %USERPROFILE%\AppData\Roaming\npm\copilot.cmd
                    userprofile = os.environ.get('USERPROFILE', os.path.expanduser('~'))
                    cmd = os.path.join(userprofile, 'AppData', 'Roaming', 'npm', 'copilot.cmd')
                else:
                    # Linux/Mac: PATH経由でコマンド直接実行
                    cmd = 'copilot'

            # copilot
            common = [cmd, "--allow-all-tools"]
            # モデルがautoの場合はモデル指定を省略
            if self.code_model and self.code_model.lower() != "auto":
                common.extend(["--model", self.code_model])
            if repo_path:
                common.extend(["--add-dir", repo_path])
            if 初回:
                return common + ["-p", プロンプト]
            else:
                return common + ["--continue", "-p", プロンプト]

        elif self.code_ai == "gemini_cli":
            # Google Gemini CLI
            if custom_cmd:
                cmd = custom_cmd
            else:
                if os.name == 'nt':
                    # Windows: %USERPROFILE%\AppData\Roaming\npm\gemini.cmd
                    userprofile = os.environ.get('USERPROFILE', os.path.expanduser('~'))
                    cmd = os.path.join(userprofile, 'AppData', 'Roaming', 'npm', 'gemini.cmd')
                else:
                    # Linux/Mac: PATH経由でコマンド直接実行
                    cmd = 'gemini'

            # gemini
            base_args = [cmd, "--yolo"]
            # モデルがautoの場合はモデル指定を省略
            if self.code_model and self.code_model.lower() != "auto":
                base_args.extend(["--model", self.code_model])
            base_args.extend(["--prompt", プロンプト])
            return base_args

        elif self.code_ai == "codex_cli":
            # OpenAI Codex CLI
            if custom_cmd:
                cmd = custom_cmd
            else:
                if os.name == 'nt':
                    # Windows: %USERPROFILE%\AppData\Roaming\npm\codex.cmd
                    userprofile = os.environ.get('USERPROFILE', os.path.expanduser('~'))
                    cmd = os.path.join(userprofile, 'AppData', 'Roaming', 'npm', 'codex.cmd')
                else:
                    # Linux/Mac: PATH経由でコマンド直接実行
                    cmd = 'codex'

            # openai codex
            # 注意:
            #   --sandbox danger-full-access が環境によって read-only に固定されることがあるため、
            #   書込モードでは bypass フラグを優先する。
            if 読取専用:
                base_args = [cmd, "exec", "--skip-git-repo-check", "--sandbox", "read-only"]
            else:
                base_args = [cmd, "exec", "--skip-git-repo-check", "--dangerously-bypass-approvals-and-sandbox"]
            # モデルがautoの場合はモデル指定を省略
            if self.code_model and self.code_model.lower() != "auto":
                base_args.extend(["--model", self.code_model])

            # 継続の場合は resume <session-id> を追加
            if not 初回 and self.codex_セッションID:
                base_args.extend(["resume", self.codex_セッションID])

            base_args.append(プロンプト)
            return base_args

        else:
            # デフォルト claude_cli
            if custom_cmd:
                cmd = custom_cmd
            else:
                if os.name == 'nt':
                    # Windows: %USERPROFILE%\AppData\Roaming\npm\claude.cmd
                    userprofile = os.environ.get('USERPROFILE', os.path.expanduser('~'))
                    cmd = os.path.join(userprofile, 'AppData', 'Roaming', 'npm', 'claude.cmd')
                else:
                    # Linux/Mac: PATH経由でコマンド直接実行
                    cmd = 'claude'

            # copilot
            common = [cmd, "--allow-dangerously-skip-permissions", "--permission-mode", "bypassPermissions"]
            # モデルがautoの場合はモデル指定を省略
            if self.code_model and self.code_model.lower() != "auto":
                common.extend(["--model", self.code_model])
            if repo_path:
                common.extend(["--add-dir", repo_path])
            if 初回:
                return common + ["-p", プロンプト]
            else:
                return common + ["--continue", "-p", プロンプト]

    def _システムプロンプト構築(self) -> str:
        """
        システムプロンプトを構築（【システム情報】セクション付き）

        Returns:
            システム情報を含む完全なシステムプロンプト
        """
        try:
            if self.system_instruction:
                base_prompt = self.system_instruction.strip()
            else:
                # 上位コンテキスト未定義時（テスト等）は簡素な既定文を使用
                base_prompt = "あなたは、美しい日本語を話す、賢いコードエージェントです。"

            # Windows文言は常に文末へ自動付加（重複は除去）
            if os.name == 'nt':
                windows_suffix = "Windows環境で動作していることを考慮して、適切なコマンドを使用してください。"
                normalized = base_prompt.replace(windows_suffix, "").strip()
                base_prompt = f"{normalized}\n{windows_suffix}" if normalized else windows_suffix

            return base_prompt

        except Exception as e:
            logger.error(f"システムプロンプト構築エラー: {e}")
            return base_prompt

    async def 開始(self):
        """CodeAI開始"""
        try:
            self.is_alive = True
            pass
            return True
        except Exception as e:
            logger.error(f"CodeAI開始:エラー {e}")
            self.is_alive = False
            return False

    async def 終了(self):
        """CodeAI終了"""
        try:
            self.is_alive = False
            # 実行中のsubprocessがあれば終了
            await self.強制終了()
        except Exception as e:
            logger.error(f"CodeAI終了:エラー {e}")
            self.is_alive = False

    async def 強制終了(self):
        """実行中のsubprocessを強制終了"""
        self.is_alive = False  # ストリーム送信を即座に停止
        if self.current_process and self.current_process.returncode is None:
            try:
                self.current_process.kill()
                await self.current_process.wait()
                logger.info(f"[CodeAI] subprocess強制終了完了")
            except Exception as e:
                logger.warning(f"[CodeAI] subprocess強制終了エラー: {e}")
            finally:
                self.current_process = None

    def _強制停止要求あり(self) -> bool:
        """親側フラグも含めて強制停止要求を判定"""
        if not self.is_alive:
            return True
        if self.parent_manager and getattr(self.parent_manager, "強制停止フラグ", False):
            return True
        return False

    async def _停止マーカー送信(self) -> None:
        """強制停止時のストリーム終端マーカー（!）を1回だけ送信"""
        if self._停止マーカー送信済み:
            return
        self._停止マーカー送信済み = True
        if self.parent_manager and hasattr(self.parent_manager, '接続'):
            try:
                await self.parent_manager.接続.send_to_channel(self.チャンネル, {
                    "セッションID": self.セッションID,
                    "チャンネル": self.チャンネル,
                    "メッセージ識別": "output_stream",
                    "メッセージ内容": "!",
                    "ファイル名": None,
                    "サムネイル画像": None
                })
            except Exception as e:
                logger.error(f"[CodeCli] 停止マーカー送信エラー: {e}")

    def _履歴追加(self, text: str, type: str):
        """履歴に項目を追加"""
        self.履歴最終番号 += 1
        self.履歴最終時刻 = time.time()
        key = str(self.履歴最終番号)

        self.履歴辞書[key] = {
            "seq": str(self.履歴最終番号),
            "time": self.履歴最終時刻,
            "type": type,
            "text": text
        }

    def _履歴取得(self) -> str:
        """過去の会話履歴を取得してフォーマット"""
        if not self.履歴辞書:
            return ""

        履歴テキスト = "【過去の会話履歴】\n"

        # 番号順にソートして履歴を構築
        sorted_keys = sorted(self.履歴辞書.keys(), key=lambda x: int(x))

        for key in sorted_keys:
            item = self.履歴辞書[key]
            if item["type"] == "system":
                履歴テキスト += f"```system\n{item['text']}\n```\n"
            elif item["type"] == "user":
                履歴テキスト += f"```user\n{item['text']}\n```\n"
            elif item["type"] == "agent":
                履歴テキスト += f"```agent\n{item['text']}\n```\n"

        return 履歴テキスト

    def _codex出力抽出(self, full_output: str) -> str:
        """
        codexコマンドの出力から実際の応答部分のみを抽出

        codexの出力形式:
        実際の応答（最初の行）
        OpenAI Codex v0.47.0 (research preview)
        --------
        workdir: ...
        model: ...
        ...
        --------
        user
        質問内容

        thinking
        思考内容
        codex
        実際の応答（繰り返し）
        tokens used
        数値

        Args:
            full_output: codexコマンドの完全な出力

        Returns:
            抽出された応答部分（最初の行から「OpenAI Codex」の直前まで）
        """
        try:
            lines = full_output.split('\n')
            result_lines = []

            for i, line in enumerate(lines):
                # "OpenAI Codex" で始まる行を検出したら終了
                if line.strip().startswith('OpenAI Codex'):
                    break

                # それ以外の行を収集
                result_lines.append(line)

            # 抽出できた場合はそれを返す
            if result_lines:
                result = '\n'.join(result_lines).strip()
                if result:
                    return result

            # 抽出できなかった場合は全出力を返す
            logger.warning("codex出力抽出失敗: 有効な応答が見つかりませんでした")
            return full_output

        except Exception as e:
            logger.error(f"codex出力抽出エラー: {e}")
            return full_output

    def _codexセッションID抽出(self, full_output: str) -> Optional[str]:
        """
        codexコマンドの出力からセッションIDを抽出

        Args:
            full_output: codexコマンドの完全な出力

        Returns:
            セッションID（見つからない場合はNone）
        """
        try:
            import re
            # パターン: session id: <uuid>
            pattern = r'session id:\s*([a-f0-9\-]+)'
            match = re.search(pattern, full_output, re.IGNORECASE)

            if match:
                セッションID = match.group(1)
                logger.debug(f"codexセッションID抽出成功: {セッションID}")
                return セッションID
            else:
                logger.debug("codexセッションID抽出: セッションIDが見つかりませんでした")
                return None

        except Exception as e:
            logger.error(f"codexセッションID抽出エラー: {e}")
            return None

    async def 実行(self, 要求テキスト: str, タイムアウト秒数: int = 1200,
                   resume: bool = True, 読取専用: bool = False, 絶対パス: str = None, file_path: str = None, 変更ファイル一覧: list = None, 再プラン要求: bool = False) -> str:
        """
        CLI (subprocess) 実行

        Args:
            要求テキスト: ユーザーからの要求
            タイムアウト秒数: タイムアウト時間
            resume: セッション継続（履歴利用）
            読取専用: 読み取り専用モード
            絶対パス: 実行ディレクトリ
            file_path: 添付ファイルの絶対パス（オプション）
            変更ファイル一覧: 変更されたファイルのリスト（検証用、オプション）
            再プラン要求: 修正内容の再プラン要求フラグ（オプション）

        Returns:
            実行結果テキスト
        """
        try:
            self._停止マーカー送信済み = False
            # 添付ファイル（絶対パス）がある場合は先に付与
            if file_path:
                try:
                    abs_path_str = Path(file_path).resolve().as_posix()
                    要求テキスト += f"\n\n添付ファイル: `{abs_path_str}`"
                except Exception as e:
                    logger.error(f"最終ファイル添付エラー: {e}")

            # 再プラン要求がある場合は追加
            if 再プラン要求:
                try:
                    replan_prompt = """

修正が正しいことを検証するために、
修正概要、修正手順を再プランしてください。
"""
                    要求テキスト += replan_prompt
                    logger.info("CodeAI: 再プラン要求をプロンプトに追加")
                except Exception as e:
                    logger.error(f"CodeAI: 再プラン要求処理エラー: {e}")

            # 変更ファイル一覧がある場合は検証モード（元の依頼は実施済みとして検証のみ）
            if 変更ファイル一覧 and len(変更ファイル一覧) > 0:
                try:
                    ファイル一覧文字列 = '\n'.join([f"- {ファイル名}" for ファイル名 in 変更ファイル一覧])
                    元の要求 = 要求テキスト
                    要求テキスト = f"""前回の依頼「{元の要求}」は実施済みです。

以下のファイルが変更されました：
{ファイル一覧文字列}

これらのファイルの変更内容を検証し、問題があれば追加修正を行ってください。
問題がなければ「検証完了」と報告してください。"""
                    logger.info(f"CodeAI: 検証モード - 変更ファイル {len(変更ファイル一覧)}件")
                except Exception as e:
                    logger.error(f"CodeAI: 変更ファイル一覧処理エラー: {e}")

            # 90秒以内の最終イメージがあれば要求テキストに追加（file_pathがない場合の補完）
            if self.parent_manager and hasattr(self.parent_manager, 'セッションデータ'):
                last_image_time = self.parent_manager.セッションデータ.get('最終イメージ時刻')
                if last_image_time and (time.time() - last_image_time) <= 90:
                    last_image_base64 = self.parent_manager.セッションデータ.get('最終イメージ')
                    if last_image_base64:
                        try:
                            # 画像をデコード
                            image_data = base64.b64decode(last_image_base64)

                            # Pillowを使って画像を開き、JPEGとして保存
                            image_stream = io.BytesIO(image_data)
                            with Image.open(image_stream) as img:
                                # JPEGはアルファチャンネルをサポートしないため、RGBに変換
                                rgb_img = img.convert('RGB')

                                # 保存先パスを構築
                                base_path = Path(絶対パス if 絶対パス else self.cwd_str)
                                save_dir = base_path / "temp" / "input"
                                save_dir.mkdir(parents=True, exist_ok=True)

                                # ファイル名を生成
                                timestamp = datetime.datetime.now().strftime("%Y%m%d.%H%M%S")
                                file_name = f"{timestamp}.jpg"
                                save_path = save_dir / file_name

                                # 画像をファイルに書き込み
                                rgb_img.save(save_path, format='JPEG')

                                abs_path_str = save_path.resolve().as_posix()
                                image_prompt_addition = f"\n\n添付ファイル: `{abs_path_str}`"
                                要求テキスト += image_prompt_addition
                                logger.info(f"最終イメージを添付: {abs_path_str}")

                        except Exception as e:
                                logger.error(f"最終イメージの処理中にエラーが発生しました: {e}")

            # 送信コンテキスト側で「今回の依頼」を必ず明示（要求テキスト自体は改変しない）
            依頼本文 = (要求テキスト or "").strip()
            if 依頼本文.startswith("【今回の依頼】"):
                送信用要求テキスト = 依頼本文
            else:
                送信用要求テキスト = f"【今回の依頼】\n{依頼本文}\n"

            # 生存状態チェック（停止中なら自動再開始を試行）
            if not self.is_alive:
                logger.warning("CodeAI実行:停止状態を検出。自動再開始を試行します")
                try:
                    開始成功 = await self.開始()
                    if (開始成功 is False) or (not self.is_alive):
                        logger.warning("CodeAI実行:自動再開始に失敗")
                        return "CodeAIが停止状態です。開始してください。"
                    logger.info("CodeAI実行:自動再開始に成功")
                except Exception as start_error:
                    logger.error(f"CodeAI実行:自動再開始エラー {start_error}")
                    return "CodeAIが停止状態です。開始してください。"

            # 履歴管理
            if len(self.履歴辞書) == 0:
                self._履歴追加(self.system_prompt, "system")

            # 初回判定（resumeがFalseまたはセッション未開始）
            初回送信 = not resume or not self.session_started

            # 完全なプロンプト構築（プロバイダー別）
            if self.code_ai in ["claude_cli", "copilot_cli", "gemini_cli", "codex_cli"]:
                # copilot: 履歴送信不要。ただし初回のみ system_prompt（base_prompt）を付与して方針を伝える
                if 初回送信:
                    完全プロンプト = f"{self.system_prompt}\n\n{送信用要求テキスト}"
                    self.session_started = True
                else:
                    完全プロンプト = 送信用要求テキスト
            else:
                if 初回送信:
                    # 初回: システムプロンプト + 要求
                    完全プロンプト = f"{self.system_prompt}\n\n{送信用要求テキスト}"
                    self.session_started = True
                else:
                    # 2回目以降: 履歴 + 要求
                    履歴テキスト = self._履歴取得()
                    完全プロンプト = f"{履歴テキスト}\n\n{送信用要求テキスト}"

            # 履歴に今回の要求を追加（完全プロンプト生成後：重複送信を避ける）
            self._履歴追加(要求テキスト, "user")

            # コマンド構築（プロバイダー別・初回判定付き）
            作業ディレクトリ = 絶対パス if 絶対パス else self.cwd_str
            repo_path = Path(作業ディレクトリ).resolve().as_posix()
            command = self._コマンド構築(
                プロンプト=完全プロンプト,
                初回=初回送信,
                repo_path=repo_path,
                読取専用=読取専用
            )

            # テスト用：送信コンテキスト（完全プロンプト）を標準出力に表示（平文）
            try:
                print("\n" + "=" * 80)
                print("送信コンテキスト（完全プロンプト）")
                print(f"AI={self.code_ai} model={self.code_model} resume={resume} 初回送信={初回送信}")
                print("-" * 80)
                print(完全プロンプト)
                print("=" * 80 + "\n")
            except Exception:
                pass

            # subprocess実行
            result_text = await self._subprocess実行(
                command=command,
                cwd=作業ディレクトリ,
                timeout=タイムアウト秒数
            )

            # codexの場合、セッションIDを抽出して保存（stderr から抽出）
            if self.code_ai == "codex_cli":
                セッションID = self._codexセッションID抽出(self.last_stderr_output)
                if セッションID:
                    self.codex_セッションID = セッションID
                    logger.info(f"codexセッションID保存: {セッションID}")

            # 履歴に結果を追加
            final_result = result_text.strip() if result_text.strip() else "!"
            self._履歴追加(final_result, "agent")

            return final_result

        except Exception as e:
            # ツールエラーログ（必須）
            logger.error(
                f"CodeAI実行エラー: {e} 要求=[{要求テキスト[:10]}...] AI={self.code_ai} モデル={self.code_model}"
            )
            エラーメッセージ = f"実行エラー: {str(e)}"

            return エラーメッセージ

    async def _subprocess実行(self, command: list, cwd: str, timeout: int) -> str:
        """
        subprocessでコマンドを実行し、stdoutをリアルタイムで監視
        ストリーム出力のみ行い、開始/終了/中断通知は親側で行う

        Args:
            command: 実行コマンド配列
            cwd: 作業ディレクトリ
            timeout: タイムアウト秒数

        Returns:
            実行結果の全テキスト
        """
        try:
            self._停止マーカー送信済み = False
            # プロセス起動
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=os.environ.copy()
            )
            # 強制終了用に参照を保持
            self.current_process = process

            result_lines = []
            stderr_lines = []
            last_output_time = time.time()

            # stdout監視タスク
            async def stdout_reader():
                nonlocal last_output_time
                try:
                    while True:
                        # 強制停止チェック（is_aliveがFalseならストリーム中断）
                        if self._強制停止要求あり():
                            logger.info("[CodeAI] 強制停止要求検出、stdout読み取り中断")
                            await self._停止マーカー送信()
                            break

                        line = await process.stdout.readline()
                        if not line:
                            break

                        last_output_time = time.time()
                        line_text = line.decode('utf-8', errors='replace').rstrip()
                        result_lines.append(line_text)

                        # 強制停止チェック（送信前にも再確認）
                        if self._強制停止要求あり():
                            logger.info("[CodeAI] 強制停止要求検出、stdout送信スキップ")
                            await self._停止マーカー送信()
                            break

                        # parent_manager経由でoutput_stream送信（ストリーム出力のみ）
                        if self.parent_manager and hasattr(self.parent_manager, '接続'):
                            try:
                                await self.parent_manager.接続.send_to_channel(self.チャンネル, {
                                    "セッションID": self.セッションID,
                                    "チャンネル": self.チャンネル,
                                    "メッセージ識別": "output_stream",
                                    "メッセージ内容": line_text,
                                    "ファイル名": None,
                                    "サムネイル画像": None
                                })
                            except Exception as e:
                                logger.error(f"[CodeCli] output_stream送信エラー(stream): {e}")
                except Exception as e:
                    logger.error(f"stdout読み取りエラー: {e}")

            # stderr監視タスク
            async def stderr_reader():
                nonlocal last_output_time
                try:
                    while True:
                        # 強制停止チェック（is_aliveがFalseならストリーム中断）
                        if self._強制停止要求あり():
                            logger.info("[CodeAI] 強制停止要求検出、stderr読み取り中断")
                            await self._停止マーカー送信()
                            break

                        line = await process.stderr.readline()
                        if not line:
                            break

                        last_output_time = time.time()
                        line_text = line.decode('utf-8', errors='replace').rstrip()
                        stderr_lines.append(line_text)

                        # 強制停止チェック（送信前にも再確認）
                        if self._強制停止要求あり():
                            logger.info("[CodeAI] 強制停止要求検出、stderr送信スキップ")
                            await self._停止マーカー送信()
                            break

                        # parent_manager経由でoutput_stream送信（stderr）
                        if self.parent_manager and hasattr(self.parent_manager, '接続'):
                            try:
                                await self.parent_manager.接続.send_to_channel(self.チャンネル, {
                                    "セッションID": self.セッションID,
                                    "チャンネル": self.チャンネル,
                                    "メッセージ識別": "output_stream",
                                    "メッセージ内容": line_text,
                                    "ファイル名": None,
                                    "サムネイル画像": None
                                })
                            except Exception as e:
                                logger.error(f"[CodeCli] output_stream送信エラー(stderr): {e}")
                except Exception as e:
                    logger.error(f"stderr読み取りエラー: {e}")

            # タイムアウト監視タスク
            async def timeout_monitor():
                while True:
                    await asyncio.sleep(1)
                    if self._強制停止要求あり():
                        logger.info("[CodeAI] 強制停止要求検出（monitor）")
                        await self._停止マーカー送信()
                        return
                    if time.time() - last_output_time > timeout:
                        raise asyncio.TimeoutError(f"タイムアウト({timeout}秒)")

            # タスク実行
            stdout_task = asyncio.create_task(stdout_reader())
            stderr_task = asyncio.create_task(stderr_reader())
            monitor_task = asyncio.create_task(timeout_monitor())

            # プロセス完了待機（タイムアウト監視付き）
            done, pending = await asyncio.wait(
                [stdout_task, stderr_task, monitor_task, asyncio.create_task(process.wait())],
                return_when=asyncio.FIRST_COMPLETED
            )

            # 未完了タスクをキャンセル
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # プロセスが生きていればキル
            if process.returncode is None:
                process.kill()
                await process.wait()

            # プロセス参照をクリア
            self.current_process = None

            # 結果を結合（stdout全体をそのまま返す - 抽出処理は行わない）
            full_output = "\n".join(result_lines)

            # stderr を保存（セッションID抽出用）
            self.last_stderr_output = "\n".join(stderr_lines)

            # stdout全体を結果として返す（フィルタリングなし）
            if self._停止マーカー送信済み:
                return "!"
            return full_output.strip() if full_output.strip() else "（応答なし）"

        except asyncio.TimeoutError as e:
            logger.warning(f"subprocess タイムアウト: {e}")
            return f"処理タイムアウト({timeout}秒)が発生しました。"

        except Exception as e:
            logger.error(f"subprocess実行エラー (command={command}, cwd={cwd}): {e}")
            return f"subprocess実行エラー: {str(e)}"


# ===== 使用例とテストコード =====

async def session_test(AI_NAME="openai", AI_MODEL="auto"):
    """
    セッション管理テスト（CLI版）
    - セッション開始
    - 1回目: 近藤の自己紹介
    - 2回目: 名前を覚えているか確認
    - 3回目: Pythonコードの質問
    - 4回目: 続けて質問
    - 履歴表示
    """
    print("=" * 50)
    print("CodeAI セッション管理テスト")
    print("=" * 50)

    # CodeAIインスタンス作成
    codeai = CodeAI(親=None, セッションID="test_session", AI_NAME=AI_NAME, AI_MODEL=AI_MODEL, max_turns=10)

    try:
        # セッション開始
        print("\n[セッション開始]")
        start_result = await codeai.開始()
        print(f"セッション開始結果: {start_result}")

        # 1回目実行
        print("\n[1回目] 自己紹介")
        result1 = await codeai.実行(
            要求テキスト="私の名前は近藤です。覚えておいてください。",
            タイムアウト秒数=30,
            resume=False
        )
        print(f"結果: {result1[:100]}...")
        print(f"履歴件数: {len(codeai.履歴辞書)}件")

        # 2回目実行
        time.sleep(3)
        print("\n[2回目] 名前確認")
        result2 = await codeai.実行(
            要求テキスト="私の名前を教えてください",
            タイムアウト秒数=30,
            resume=True
        )
        print(f"結果: {result2[:100]}...")
        print(f"履歴件数: {len(codeai.履歴辞書)}件")

        # 3回目実行
        time.sleep(3)
        print("\n[3回目] Pythonコード質問")
        result3 = await codeai.実行(
            要求テキスト="if文の使い方を教えて",
            タイムアウト秒数=30,
            resume=True
        )
        print(f"結果: {result3[:100]}...")
        print(f"履歴件数: {len(codeai.履歴辞書)}件")

        # 4回目実行
        time.sleep(3)
        print("\n[4回目] 続けて質問")
        result4 = await codeai.実行(
            要求テキスト="for文との違いは何ですか？",
            タイムアウト秒数=30,
            resume=True
        )
        print(f"結果: {result4[:100]}...")
        print(f"履歴件数: {len(codeai.履歴辞書)}件")

        # 履歴表示
        print("\n[履歴表示]")
        formatted_history = codeai._履歴取得()
        print(formatted_history)

    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # セッション終了
        await codeai.終了()

    print("=" * 50)
    print("テスト完了")
    print("=" * 50)


async def simple_test(AI_NAME="openai", AI_MODEL="auto"):
    """キューなしのシンプルテスト"""
    print("\n" + "=" * 30)
    print("シンプルテスト開始")
    print("=" * 30)

    # CodeAIインスタンス作成
    codeai = CodeAI(親=None, セッションID="simple_test", AI_NAME=AI_NAME, AI_MODEL=AI_MODEL, max_turns=10)

    try:
        # セッション開始
        await codeai.開始()

        # キューなしでの実行
        time.sleep(3)
        result = await codeai.実行("こんにちは、現在の時刻を教えてください。")
        print(f"シンプル実行結果: {result}")

        # 追加プロンプト：AI に作業をやらせる
        time.sleep(3)
        result2 = await codeai.実行("temp/hello.txt というファイルを作成して、Hello World と書いて。")
        print(f"作業実行結果: {result2}")

    except Exception as e:
        print(f"シンプルテストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await codeai.終了()

    print("=" * 30)
    print("シンプルテスト完了")
    print("=" * 30)


if __name__ == "__main__":

    # プロバイダーとモデルの設定
    #AI_NAME, AI_MODEL = "claude_cli", "auto"
    #AI_NAME, AI_MODEL = "copilot_cli", "auto"
    #AI_NAME, AI_MODEL = "gemini_cli", "auto"
    AI_NAME, AI_MODEL = "codex_cli", "auto"

    print("履歴テスト")
    asyncio.run(session_test(AI_NAME=AI_NAME, AI_MODEL=AI_MODEL))

    print("\nシンプルテスト")
    asyncio.run(simple_test(AI_NAME=AI_NAME, AI_MODEL=AI_MODEL))

# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""
AIコア コードエージェント処理プロセッサ
非同期キューでコード要求を受け取り、AI応答を生成してWebSocketへ返す
エージェント1-4（チャンネル1-4）専用
"""

import asyncio
import importlib
import json
import os
import shutil
import random
from typing import Optional, Any
from types import ModuleType
from AIコア.AIバックアップ import バックアップ実行

from log_config import get_logger

logger = get_logger(__name__)

_CODE_CONTEXT_JSON_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_config", "AiDiy_code__context.json")
)

_CODE_CONTEXT_TEMPLATE_LINES = [
    "あなたは、美しい日本語を話す、賢いコードエージェントです。",
    "このプロジェクトの概要は _AIDIY.md を確認してください。",
    "上記以外の *.md の記載内容は必要に応じて確認してください。",
    "概要が不明な場合は、プログラムコードの説明、分析、実装支援を行います。",
    "機能追加、修正操作時は、同類のソースを参考にしてください。",
    "AiDiy自体の改造時、reboot_core.txt,reboot_apps.txtでシステム再起動できますが、再起動はユーザー判断にゆだねてください。"
]


def _context_template_payload() -> dict:
    return {
        "version": 1,
        "description": "AIコア CodeAI 定型コンテキスト",
        "system_instruction_lines": _CODE_CONTEXT_TEMPLATE_LINES,
    }


def _compose_instruction(lines: list[str]) -> str:
    text = "\n".join(lines)
    if not text.endswith("\n"):
        text += "\n"
    return text


def _load_or_create_code_context() -> str:
    """CodeAI定型コンテキストを読み込む。無ければひな形JSONを作成。"""
    template_payload = _context_template_payload()
    template_instruction = _compose_instruction(template_payload["system_instruction_lines"])

    try:
        os.makedirs(os.path.dirname(_CODE_CONTEXT_JSON_PATH), exist_ok=True)

        if not os.path.exists(_CODE_CONTEXT_JSON_PATH):
            with open(_CODE_CONTEXT_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(template_payload, f, indent=2, ensure_ascii=False)
            logger.info(f"[CodeAgent] 定型コンテキストJSONを作成: {_CODE_CONTEXT_JSON_PATH}")
            return template_instruction

        with open(_CODE_CONTEXT_JSON_PATH, "r", encoding="utf-8-sig") as f:
            payload = json.load(f)

        lines = payload.get("system_instruction_lines") if isinstance(payload, dict) else None
        if isinstance(lines, list):
            normalized = [str(line) for line in lines]
            return _compose_instruction(normalized)

        logger.warning(f"[CodeAgent] 定型コンテキストJSONの形式不正。ひな形を再作成します: {_CODE_CONTEXT_JSON_PATH}")
        with open(_CODE_CONTEXT_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(template_payload, f, indent=2, ensure_ascii=False)
        return template_instruction
    except Exception as e:
        logger.error(f"[CodeAgent] 定型コンテキスト読込エラー: {e}")
        return template_instruction


class CodeAgent:
    """コードエージェント処理クラス（キュー処理）- エージェント1-4（チャンネル1-4）専用"""

    def __init__(
        self,
        親=None,
        セッションID: str = "",
        チャンネル: str = "0",
        絶対パス: str = "",
        AI_NAME: str = "",
        AI_MODEL: str = "",
        接続=None,
        保存関数=None,
    ):
        self.セッションID = セッションID
        self.チャンネル = チャンネル
        self.接続 = 接続
        self.保存関数 = 保存関数
        self.AI_NAME = AI_NAME
        self.AI_MODEL = AI_MODEL
        self.絶対パス = 絶対パス
        self.親 = 親
        self.システム指示 = _load_or_create_code_context()
        self.AIモジュール = self._select_ai_module()
        self.AIインスタンス = None
        self.is_alive = False
        self.コード処理Ｑ = asyncio.Queue()
        self.worker_task: Optional[asyncio.Task] = None
        self.会話履歴 = []  # エージェント専用の会話履歴
        self.累積変更ファイル: list[str] = []  # 検証対象ファイルを累積
        self._累積変更ファイルキー: set[str] = set()  # パス正規化キーで重複排除
        self.強制停止フラグ = False  # cancel_run用
        self.現在タスク: Optional[asyncio.Task] = None  # 実行中の処理タスク

    def _配下パス判定(self, 対象パス: str, 基準パス: str) -> bool:
        """対象パスが基準パス配下（同一含む）かを返す"""
        if not 対象パス or not 基準パス:
            return False
        try:
            return os.path.commonpath([os.path.abspath(対象パス), os.path.abspath(基準パス)]) == os.path.abspath(基準パス)
        except ValueError:
            return False

    def _添付ファイルパス解決(self, ファイルパス: str) -> Optional[str]:
        """
        添付ファイルの実パスを解決する。
        - 現在の実行プロジェクト配下ならそのまま返す
        - backend_server/temp 配下で、かつ実行プロジェクト外なら実行先 temp 配下へコピーして返す
        """
        if not ファイルパス:
            return None

        絶対元パス = os.path.abspath(ファイルパス)
        if not os.path.exists(絶対元パス):
            logger.warning(f"[CodeAgent] 添付ファイルが見つかりません: {ファイルパス}")
            return None

        実行基準パス = os.path.abspath(self.絶対パス) if self.絶対パス else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if self._配下パス判定(絶対元パス, 実行基準パス):
            return 絶対元パス

        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        backend_temp_dir = os.path.join(backend_dir, "temp")
        if not self._配下パス判定(絶対元パス, backend_temp_dir):
            return 絶対元パス

        try:
            相対パス = os.path.relpath(絶対元パス, backend_dir)
            コピー先パス = os.path.abspath(os.path.join(実行基準パス, 相対パス))

            if os.path.normcase(os.path.normpath(絶対元パス)) == os.path.normcase(os.path.normpath(コピー先パス)):
                return 絶対元パス

            os.makedirs(os.path.dirname(コピー先パス), exist_ok=True)

            コピー要否 = True
            if os.path.exists(コピー先パス):
                try:
                    コピー要否 = (
                        os.path.getsize(絶対元パス) != os.path.getsize(コピー先パス)
                        or os.path.getmtime(絶対元パス) > os.path.getmtime(コピー先パス)
                    )
                except OSError:
                    コピー要否 = True

            if コピー要否:
                shutil.copy2(絶対元パス, コピー先パス)
                logger.info(f"[CodeAgent] temp添付ファイルを作業先へコピー: {絶対元パス} -> {コピー先パス}")

            return コピー先パス
        except Exception as e:
            logger.warning(f"[CodeAgent] temp添付ファイルのコピー失敗。元パスを使用します: {絶対元パス} error={e}")
            return 絶対元パス

    def _添付ファイル一覧解決(self, 添付ファイル一覧: list[str]) -> list[str]:
        """添付ファイル一覧を実行可能なパスへ解決する"""
        解決後一覧: list[str] = []
        for ファイルパス in 添付ファイル一覧 or []:
            解決後パス = self._添付ファイルパス解決(ファイルパス)
            if 解決後パス and 解決後パス not in 解決後一覧:
                解決後一覧.append(解決後パス)
        return 解決後一覧

    def _変更ファイルキー(self, ファイルパス: str) -> str:
        """重複判定用の正規化キーを返す"""
        if not ファイルパス:
            return ""
        return os.path.normcase(os.path.normpath(ファイルパス.replace("/", os.sep)))

    def _累積変更ファイル追加(self, 変更ファイル一覧: list[str]) -> int:
        """累積変更ファイルへ重複なしで追加し、追加件数を返す"""
        追加件数 = 0
        for ファイル in 変更ファイル一覧:
            キー = self._変更ファイルキー(ファイル)
            if not キー:
                continue
            if キー in self._累積変更ファイルキー:
                continue
            self._累積変更ファイルキー.add(キー)
            self.累積変更ファイル.append(ファイル)
            追加件数 += 1
        return 追加件数

    def _aidiyフォルダ取得(self) -> str:
        """現在の作業先に対応する .aidiy フォルダの絶対パスを返す"""
        実行基準パス = os.path.abspath(self.絶対パス) if self.絶対パス else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(実行基準パス, ".aidiy")

    def _自己改善プロンプト生成(self, 元要求: str, 最終応答: str) -> str:
        """自己改善書き込み依頼のプロンプトを生成する"""
        aidiy_dir = self._aidiyフォルダ取得()
        aidiy_index = os.path.join(aidiy_dir, "_index.md")
        aidiy_last = os.path.join(aidiy_dir, "_最終修正")
        変更ファイル一覧 = "\n".join(f"- {path}" for path in self.累積変更ファイル) if self.累積変更ファイル else "- なし"
        return (
            "自己改善書き込みを実施してください。\n"
            "今回の修正処理は完了済みで、ユーザー向けの完了通知も終わっています。\n"
            "これ以降は、次回以降の改造精度を上げるための知見整理だけを行ってください。\n\n"
            f"作業対象フォルダ: `{aidiy_dir}`\n"
            f"更新必須ファイル: `{aidiy_index}`, `{aidiy_last}`\n"
            "加えて、今回の修正テーマを表す .md を .aidiy 配下に1件以上作成または更新してください。\n"
            "テーマ名は内容がわかる日本語ファイル名にしてください。\n\n"
            "更新内容の要件:\n"
            "1. `.aidiy/_index.md` に今回の修正知見の索引を追記・更新\n"
            "2. `.aidiy/_最終変更.md` に今回の最終変更内容を上書きまたは更新\n"
            "3. テーマ別 .md に、修正内容・関連ファイル・関連箇所・次回の注意点を整理\n"
            "4. 既存の .aidiy 記録があれば読み、重複ではなく知見を統合\n"
            "5. アプリ本体の仕様変更や追加修正は行わず、.aidiy 配下の記録更新だけを実施\n\n"
            f"【今回の依頼】\n{(元要求 or '').strip()}\n\n"
            f"【最終応答】\n{(最終応答 or '').strip()}\n\n"
            f"【変更ファイル一覧】\n{変更ファイル一覧}\n"
        )

    async def _自己改善書き込み実行(self, ai_instance: Any, 元要求: str, 最終応答: str) -> None:
        """検証・通知完了後に .aidiy へ知見を書き込ませる"""
        if self.強制停止フラグ:
            logger.info(f"[CodeAgent] チャンネル{self.チャンネル} 強制停止中のため自己改善をスキップ")
            return
        if not ai_instance:
            logger.warning(f"[CodeAgent] チャンネル{self.チャンネル} AIインスタンス未初期化のため自己改善をスキップ")
            return
        if not self.累積変更ファイル:
            logger.info(f"[CodeAgent] チャンネル{self.チャンネル} 変更ファイルなしのため自己改善をスキップ")
            return

        aidiy_dir = self._aidiyフォルダ取得()
        try:
            os.makedirs(aidiy_dir, exist_ok=True)
        except Exception as e:
            logger.warning(f"[CodeAgent] .aidiy フォルダ作成エラー: {e}")

        自己改善プロンプト = self._自己改善プロンプト生成(元要求=元要求, 最終応答=最終応答)
        logger.info(f"[CodeAgent] チャンネル{self.チャンネル} 自己改善書き込みを開始: {aidiy_dir}")

        try:
            await self.接続.send_to_channel(self.チャンネル, {
                "セッションID": self.セッションID,
                "メッセージ識別": "output_text",
                "メッセージ内容": "\n【自己改善開始】\n.aidiy の知見整理を継続します。\n"
            })
        except Exception as e:
            logger.warning(f"[CodeAgent] 自己改善開始通知送信エラー: {e}")

        try:
            await self._ストリーム開始通知送信()
            自己改善結果 = await ai_instance.実行(
                要求テキスト=自己改善プロンプト,
                絶対パス=self.絶対パス or None,
            ) or "（応答なし）"
            await self._ストリーム終了通知送信()

            if 自己改善結果 and 自己改善結果 != "!":
                await self.接続.send_to_channel(self.チャンネル, {
                    "セッションID": self.セッションID,
                    "メッセージ識別": "output_text",
                    "メッセージ内容": f"\n【自己改善完了】\n{自己改善結果}"
                })
                if self.保存関数:
                    self.保存関数(
                        セッションID=self.セッションID,
                        チャンネル=self.チャンネル,
                        メッセージ識別="output_text",
                        メッセージ内容=f"【自己改善完了】\n{自己改善結果}",
                        ファイル名=None,
                        サムネイル画像=None
                    )
        except Exception as e:
            logger.error(f"[CodeAgent] 自己改善書き込みエラー: {e}")

    def _select_ai_module(self) -> Optional[ModuleType]:
        """AI_NAMEに応じたコードモジュールを選択してインポート"""
        module_name = "AIコア.AIコード_cli"
        if self.AI_NAME == "claude_sdk":
            module_name = "AIコア.AIコード_claude"
        try:
            return importlib.import_module(module_name)
        except Exception as e:
            logger.error(f"[CodeAgent] AIモジュールのインポート失敗: {module_name} error={e}")
            return None

    async def _ensure_ai_instance(self) -> Optional[Any]:
        """AIモジュールのCodeAIインスタンスを生成・開始"""
        if not self.AIモジュール:
            return None
        if self.AIインスタンス:
            if not getattr(self.AIインスタンス, "is_alive", False):
                logger.info(f"[CodeAgent] チャンネル{self.チャンネル} CodeAI停止状態を検出。再開始します")
                try:
                    開始成功 = await self.AIインスタンス.開始()
                    if (開始成功 is False) or (not getattr(self.AIインスタンス, "is_alive", False)):
                        logger.warning(f"[CodeAgent] チャンネル{self.チャンネル} CodeAI再開始失敗。再生成します")
                        self.AIインスタンス = None
                    else:
                        return self.AIインスタンス
                except Exception as e:
                    logger.warning(f"[CodeAgent] チャンネル{self.チャンネル} CodeAI再開始エラー: {e}")
                    self.AIインスタンス = None
            else:
                return self.AIインスタンス
        try:
            CodeAI = getattr(self.AIモジュール, "CodeAI", None)
            if CodeAI is None:
                logger.error("[CodeAgent] CodeAIクラスが見つかりません")
                return None
            self.AIインスタンス = CodeAI(
                親=self,
                セッションID=self.セッションID,
                チャンネル=self.チャンネル,
                AI_NAME=self.AI_NAME,
                AI_MODEL=self.AI_MODEL,
                絶対パス=self.絶対パス or None,
                system_instruction=self.システム指示,
            )
            開始成功 = await self.AIインスタンス.開始()
            if (開始成功 is False) or (not getattr(self.AIインスタンス, "is_alive", False)):
                logger.error(
                    f"[CodeAgent] CodeAI開始失敗: AI={self.AI_NAME} モデル={self.AI_MODEL} "
                    f"セッション={self.セッションID} チャンネル={self.チャンネル}"
                )
                self.AIインスタンス = None
                return None
            return self.AIインスタンス
        except Exception as e:
            logger.error(f"[CodeAgent] CodeAI初期化エラー: {e}")
            self.AIインスタンス = None
            return None

    async def 開始(self) -> None:
        """コード処理ワーカーを開始"""
        self.is_alive = True
        if self.worker_task is None or self.worker_task.done():
            self.worker_task = asyncio.create_task(self._コード処理ワーカー())
            logger.debug(f"[CodeAgent] チャンネル{self.チャンネル} 開始")

    async def 終了(self) -> None:
        """コード処理ワーカーを終了"""
        self.is_alive = False
        if self.worker_task and not self.worker_task.done():
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        logger.debug(f"[CodeAgent] チャンネル{self.チャンネル} 終了")

    async def 接続時welcome送信(self) -> None:
        """チャンネル接続時にCodeAI初期化を試み、結果をwelcome_textで送信"""
        await asyncio.sleep(0.3)  # welcome_info / 会話履歴の後に送信
        ai_label = f"[{self.AI_NAME or f'Agent{self.チャンネル}'}]"

        try:
            instance = await self._ensure_ai_instance()
            if instance and getattr(instance, "is_alive", False):
                バージョン = getattr(instance, "バージョン", "") or ""
                if バージョン:
                    メッセージ = f"{ai_label}準備できました。({バージョン})"
                else:
                    メッセージ = f"{ai_label}会話準備ができました。"
            else:
                バージョン = getattr(instance, "バージョン", "") if instance else ""
                if not バージョン:
                    ai_name = self.AI_NAME or ""
                    if ai_name in ("claude_sdk", "claude_cli"):
                        tool = "claude code"
                    elif ai_name == "copilot_cli":
                        tool = "copilot"
                    elif ai_name == "gemini_cli":
                        tool = "gemini"
                    elif ai_name == "codex_cli":
                        tool = "codex"
                    elif ai_name == "hermes_cli":
                        tool = "hermes"
                    else:
                        tool = ai_name or "コマンド"
                    メッセージ = f"{ai_label}{tool}が利用できません。（{tool}未インストール?)"
                else:
                    メッセージ = f"{ai_label}初期化に失敗しました。"
        except Exception:
            メッセージ = f"{ai_label}初期化に失敗しました。"

        if self.接続:
            try:
                await self.接続.send_to_channel(self.チャンネル, {
                    "セッションID": self.セッションID,
                    "チャンネル": self.チャンネル,
                    "メッセージ識別": "welcome_text",
                    "メッセージ内容": メッセージ,
                    "ファイル名": None,
                    "サムネイル画像": None,
                })
            except Exception as e:
                logger.error(f"[CodeAgent] welcome_text送信エラー: {e}")

    async def 強制停止(self) -> bool:
        """
        現在実行中のタスクを強制停止

        Returns:
            True: タスクをキャンセルした
            False: 実行中のタスクがなかった
        """
        # 1. フラグを立てる（互換性のため - subprocess内のポーリング用）
        self.強制停止フラグ = True

        # 2. 実行中のタスクをキャンセル
        if self.現在タスク and not self.現在タスク.done():
            # 即時に中断通知を送信（停止処理完了を待たない）
            await self._中断通知送信()

            # 3. AIインスタンスのis_aliveをFalseに（ストリーム送信を即座に停止）
            if self.AIインスタンス and hasattr(self.AIインスタンス, '強制終了'):
                try:
                    await self.AIインスタンス.強制終了()
                except Exception as e:
                    logger.warning(f"[CodeAgent] AIインスタンス強制終了エラー: {e}")

            # 4. タスクをキャンセル
            self.現在タスク.cancel()
            try:
                await asyncio.wait_for(asyncio.shield(self.現在タスク), timeout=5.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
            except Exception as e:
                logger.warning(f"[CodeAgent] タスクキャンセル待機エラー: {e}")

            # 5. 次回実行のためにAIインスタンスを再開（claude_sdkはis_aliveをTrueに戻す）
            if self.AIインスタンス and hasattr(self.AIインスタンス, '開始'):
                try:
                    await self.AIインスタンス.開始()
                    logger.info(f"[CodeAgent] チャンネル{self.チャンネル} AIインスタンス再開完了")
                except Exception as e:
                    logger.warning(f"[CodeAgent] AIインスタンス再開エラー: {e}")

            logger.info(f"[CodeAgent] チャンネル{self.チャンネル} 強制停止完了")
            return True

        # 実行中タスクが無くても、前回中断でCodeAIが停止状態なら復帰させる
        if self.AIインスタンス and (not getattr(self.AIインスタンス, "is_alive", False)) and hasattr(self.AIインスタンス, '開始'):
            try:
                await self.AIインスタンス.開始()
                logger.info(f"[CodeAgent] チャンネル{self.チャンネル} 実行タスクなしだがAIインスタンスを再開")
            except Exception as e:
                logger.warning(f"[CodeAgent] 実行タスクなし時のAIインスタンス再開エラー: {e}")

        logger.info(f"[CodeAgent] チャンネル{self.チャンネル} 実行中のタスクなし")
        return False

    async def _ストリーム開始通知送信(self) -> None:
        """ストリーム開始通知をクライアントに送信"""
        try:
            await self.接続.send_to_channel(self.チャンネル, {
                "セッションID": self.セッションID,
                "チャンネル": self.チャンネル,
                "メッセージ識別": "output_stream",
                "メッセージ内容": "<<< 処理開始 >>>",
                "ファイル名": None,
                "サムネイル画像": None
            })
            logger.info(f"[CodeAgent] チャンネル{self.チャンネル} <<< 処理開始 >>>")
        except Exception as e:
            logger.error(f"[CodeAgent] ストリーム開始通知送信エラー: {e}")

    async def _ストリーム終了通知送信(self) -> None:
        """ストリーム終了通知をクライアントに送信"""
        try:
            await self.接続.send_to_channel(self.チャンネル, {
                "セッションID": self.セッションID,
                "チャンネル": self.チャンネル,
                "メッセージ識別": "output_stream",
                "メッセージ内容": "<<< 処理終了 >>>",
                "ファイル名": None,
                "サムネイル画像": None
            })
            logger.info(f"[CodeAgent] チャンネル{self.チャンネル} <<< 処理終了 >>>")
        except Exception as e:
            logger.error(f"[CodeAgent] ストリーム終了通知送信エラー: {e}")

    async def _中断通知送信(self) -> None:
        """中断通知をクライアントに送信"""
        try:
            await self.接続.send_to_channel(self.チャンネル, {
                "セッションID": self.セッションID,
                "チャンネル": self.チャンネル,
                "メッセージ識別": "output_stream",
                "メッセージ内容": "<<< 処理中断 >>>",
                "ファイル名": None,
                "サムネイル画像": None
            })
            await self.接続.send_to_channel(self.チャンネル, {
                "セッションID": self.セッションID,
                "チャンネル": self.チャンネル,
                "メッセージ識別": "output_text",
                "メッセージ内容": "処理は強制中断しました。",
                "ファイル名": None,
                "サムネイル画像": None
            })
            logger.info(f"[CodeAgent] チャンネル{self.チャンネル} <<< 処理中断 >>>")
        except Exception as e:
            logger.error(f"[CodeAgent] 中断通知送信エラー: {e}")

    async def コード要求(self, 受信データ: dict) -> None:
        """コード要求をキューに追加（受信データ構造体をそのまま投入）"""
        if not 受信データ:
            return
        await self.コード処理Ｑ.put(受信データ)

    async def _コード処理ワーカー(self) -> None:
        """コード処理ワーカー（キューから取り出して処理）"""
        while self.is_alive:
            try:
                try:
                    受信データ = await asyncio.wait_for(self.コード処理Ｑ.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    await asyncio.sleep(0.2)
                    continue

                if not isinstance(受信データ, dict):
                    continue
                    
                メッセージ識別 = 受信データ.get("メッセージ識別", "")

                if メッセージ識別 == "input_text":
                    # テキスト処理: [ECHO]付きoutput_text送信 → 会話履歴保存
                    await self._処理_input_text(受信データ)
                elif メッセージ識別 == "input_request":
                    # リクエスト処理: 前後処理付きでAI実行
                    await self._処理_input_request(受信データ)
                elif メッセージ識別 == "input_file":
                    # ファイル処理: temp/outputコピー → output_file送信 → 会話履歴保存
                    await self._処理_input_file(受信データ)
                
                self.コード処理Ｑ.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[CodeAgent] チャンネル{self.チャンネル} 処理エラー: {e}")
                await asyncio.sleep(0.2)

    async def _処理_input_text(self, 受信データ: dict) -> None:
        """
        input_text処理:
        1. AI実行 + output_stream/output_text送信
        2. バックアップ検証ループ（最大5回）
        3. 生成ファイル通知
        4. update_info送信

        asyncio.Taskでラップし、強制停止時にキャンセル可能
        """
        # 強制停止フラグをリセット
        self.強制停止フラグ = False
        # 累積変更ファイルをクリア
        self.累積変更ファイル = []
        self._累積変更ファイルキー = set()

        # タスク化して実行
        self.現在タスク = asyncio.create_task(self._基本AI処理(受信データ))
        try:
            最終応答 = await self.現在タスク
            ai_instance = await self._ensure_ai_instance()
            await self._自己改善書き込み実行(
                ai_instance=ai_instance,
                元要求=受信データ.get("メッセージ内容", ""),
                最終応答=最終応答 or "",
            )
        except asyncio.CancelledError:
            # 中断通知は強制停止()で即時送信済み
            logger.info(f"[CodeAgent] チャンネル{self.チャンネル} タスクがキャンセルされました")
        finally:
            self.現在タスク = None

    async def _処理_input_request(self, 受信データ: dict) -> None:
        """
        input_request処理:
        1. inputチャンネルへ開始通知（音声付き）
        2. input_text処理（_基本AI処理）- タスク化
        3. output_request送信（チャンネル0へ）
        4. inputチャンネルへ完了通知（音声付き）

        asyncio.Taskでラップし、強制停止時にキャンセル可能
        """
        # 強制停止フラグをリセット
        self.強制停止フラグ = False
        メッセージ内容 = ""
        try:
            メッセージ内容 = 受信データ.get("メッセージ内容", "")

            # 添付ファイル一覧があればメッセージに追記
            添付ファイル一覧 = 受信データ.get("添付ファイル一覧", [])
            if 添付ファイル一覧:
                有効ファイル = self._添付ファイル一覧解決(添付ファイル一覧)
                if 有効ファイル:
                    受信データ["添付ファイル一覧"] = 有効ファイル
                    添付テキスト = "\n``` 添付ファイル\n"
                    for パス in 有効ファイル:
                        添付テキスト += f"{パス}\n"
                    添付テキスト += "```"
                    メッセージ内容 = メッセージ内容 + 添付テキスト
                    受信データ["メッセージ内容"] = メッセージ内容

            # 1. inputチャンネルへ処理開始を連絡
            # 累積変更ファイルをクリア
            self.累積変更ファイル = []
            self._累積変更ファイルキー = set()

            開始メッセージ = (
                f"コードエージェント{self.チャンネル}です。\n"
                f"処理要求を開始しました。\n"
                f"詳細を省き、端的に音声で処理の開始を伝えてください。\n"
                f"``` 要求\n"
                f"{メッセージ内容}\n"
                f"```"
            )
            try:
                await self.接続.send_to_channel("input", {
                    "セッションID": self.セッションID,
                    "チャンネル": "input",
                    "メッセージ識別": "input_text",
                    "メッセージ内容": 開始メッセージ
                })
            except Exception as e:
                logger.warning(f"[CodeAgent] inputチャンネルへの開始メッセージ送信エラー: {e}")
            try:
                lp = getattr(self.接続, "live_processor", None)
                if lp and getattr(getattr(lp, "AIインスタンス", None), "live_session", None):
                    await lp.開始()
                    await lp.テキスト送信(開始メッセージ)
            except Exception as e:
                logger.warning(f"[CodeAgent] LiveAI開始メッセージ送信エラー: {e}")

            # 2. 基本AI処理（タスク化して実行）
            self.現在タスク = asyncio.create_task(self._基本AI処理(受信データ))
            try:
                出力メッセージ内容 = await self.現在タスク
            except asyncio.CancelledError:
                # 中断通知は強制停止()で即時送信済み
                logger.info(f"[CodeAgent] チャンネル{self.チャンネル} タスクがキャンセルされました(request)")
                # 中断メッセージをinputチャンネルへ通知
                中断メッセージ = (
                    f"コードエージェント{self.チャンネル}です。\n"
                    f"処理要求が中断されました。\n"
                )
                try:
                    await self.接続.send_to_channel("input", {
                        "セッションID": self.セッションID,
                        "チャンネル": "input",
                        "メッセージ識別": "input_text",
                        "メッセージ内容": 中断メッセージ
                    })
                except Exception:
                    pass
                return
            finally:
                self.現在タスク = None

            # 3. output_request送信（チャンネル0へ）
            await self.接続.send_to_channel("0", {
                "セッションID": self.セッションID,
                "メッセージ識別": "output_request",
                "メッセージ内容": 出力メッセージ内容,
                "ファイル名": None,
                "サムネイル画像": None
            })

            # 会話履歴保存（チャンネル0）
            if self.保存関数:
                self.保存関数(
                    セッションID=self.セッションID,
                    チャンネル="0",
                    メッセージ識別="output_request",
                    メッセージ内容=出力メッセージ内容,
                    ファイル名=None,
                    サムネイル画像=None
                )

            # 4. inputチャンネルへ処理終了を連絡
            完了メッセージ = (
                f"コードエージェント{self.チャンネル}です。\n"
                f"処理要求が完了しました。\n"
                f"詳細を省き、端的に音声で処理の完了を伝えてください。\n"
                f"``` 要求\n"
                f"{メッセージ内容}\n"
                f"```\n"
                f"``` 結果\n"
                f"{出力メッセージ内容}\n"
                f"```"
            )
            try:
                await self.接続.send_to_channel("input", {
                    "セッションID": self.セッションID,
                    "チャンネル": "input",
                    "メッセージ識別": "input_text",
                    "メッセージ内容": 完了メッセージ
                })
            except Exception as e:
                logger.warning(f"[CodeAgent] inputチャンネルへの完了メッセージ送信エラー: {e}")
            try:
                lp = getattr(self.接続, "live_processor", None)
                if lp and getattr(getattr(lp, "AIインスタンス", None), "live_session", None):
                    await lp.開始()
                    await lp.テキスト送信(完了メッセージ)
            except Exception as e:
                logger.warning(f"[CodeAgent] LiveAI完了メッセージ送信エラー: {e}")

            ai_instance = await self._ensure_ai_instance()
            await self._自己改善書き込み実行(
                ai_instance=ai_instance,
                元要求=受信データ.get("メッセージ内容", ""),
                最終応答=出力メッセージ内容,
            )

        except Exception as e:
            logger.error(f"[CodeAgent] チャンネル{self.チャンネル} input_request処理エラー: {e}")

    async def _基本AI処理(self, 受信データ: dict) -> str:
        """
        基本AI処理（input_text/input_request共通）:
        1. ストリーム開始通知
        2. AI実行 + output_text送信
        3. ストリーム終了通知
        4. バックアップ検証ループ（最大5回）
        5. 生成ファイル通知
        6. update_info送信

        Returns:
            出力メッセージ内容（output_requestで使用）
        """
        出力メッセージ内容 = ""
        受信種別 = ""
        try:
            メッセージ内容 = 受信データ.get("メッセージ内容", "")
            受信種別 = 受信データ.get("メッセージ識別", "")

            # 添付ファイル一覧があればメッセージに追記
            添付ファイル一覧 = 受信データ.get("添付ファイル一覧", [])
            if 添付ファイル一覧:
                有効ファイル = self._添付ファイル一覧解決(添付ファイル一覧)
                if 有効ファイル:
                    受信データ["添付ファイル一覧"] = 有効ファイル
                    添付テキスト = "\n``` 添付ファイル\n"
                    for パス in 有効ファイル:
                        添付テキスト += f"{パス}\n"
                    添付テキスト += "```"
                    メッセージ内容 = メッセージ内容 + 添付テキスト
                    logger.info(f"[CodeAgent] 添付ファイル追記: {len(有効ファイル)}件")
            else:
                # 60s以内のファイルがなく、ファイルパネルで選択中のパスがある場合はメッセージに追加
                選択ファイル情報 = 受信データ.get("選択ファイル情報")
                if 選択ファイル情報:
                    メッセージ内容 = メッセージ内容 + f"\n[{選択ファイル情報}]"
                    logger.info(f"[CodeAgent] 選択ファイル情報をメッセージに追加: {選択ファイル情報}")

            # 処理要求ログ
            セッションID_短縮 = self.セッションID[:10] if self.セッションID else '不明'
            logger.info(f"[CodeAgent] 実行パス: {self.絶対パス}")
            logger.info(
                f"処理要求: チャンネル={self.チャンネル}, ソケット={セッションID_短縮}...,\n{メッセージ内容.rstrip()}\n"
            )

            # ストリーム開始通知
            await self._ストリーム開始通知送信()

            # AI実行
            try:
                ai_instance = await self._ensure_ai_instance()
                if ai_instance:
                    出力メッセージ内容 = await ai_instance.実行(
                        要求テキスト=メッセージ内容,
                        絶対パス=self.絶対パス or None,
                    )
            except Exception as e:
                logger.error(f"[CodeAgent] AI実行エラー: {e}")
                出力メッセージ内容 = "!"
            if not 出力メッセージ内容:
                出力メッセージ内容 = "!"

            # 強制停止フラグチェック → 中断通知は強制停止()で送信済みなのでここでは戻り値のみ設定
            if self.強制停止フラグ:
                logger.info(f"[CodeAgent] チャンネル{self.チャンネル} 強制停止フラグ検出（AI実行後）")
                出力メッセージ内容 = "処理は強制中断しました。"
                # _中断通知送信は強制停止()で既に送信済みのため、ここでは呼ばない
                return 出力メッセージ内容

            # ストリーム終了通知
            await self._ストリーム終了通知送信()

            # 処理応答ログ
            logger.info(
                f"処理応答: チャンネル={self.チャンネル}, ソケット={セッションID_短縮}...,\n{出力メッセージ内容.rstrip()}\n"
            )

            # output_text送信（自チャンネル）
            await self.接続.send_to_channel(self.チャンネル, {
                "セッションID": self.セッションID,
                "メッセージ識別": "output_text",
                "メッセージ内容": 出力メッセージ内容
            })

            # 会話履歴保存（自チャンネル）
            if self.保存関数:
                self.保存関数(
                    セッションID=self.セッションID,
                    チャンネル=self.チャンネル,
                    メッセージ識別="output_text",
                    メッセージ内容=出力メッセージ内容,
                    ファイル名=None,
                    サムネイル画像=None
                )

            # バックアップ＋自己検証ループ
            今回更新あり = False
            try:
                logger.info("[CodeAgent] バックアップ検証ループを開始します")
                今回更新あり = await self._バックアップ検証ループ(ai_instance)
                logger.info(f"[CodeAgent] バックアップ検証ループ完了: 更新あり={今回更新あり}")
            except Exception as e:
                logger.error(f"[CodeAgent] バックアップ検証ループエラー: {e}")

            # 生成されたファイルをチェックしてinputチャンネルに通知
            try:
                await self._生成ファイル通知()
            except Exception as e:
                logger.error(f"[CodeAgent] 生成ファイル通知エラー: {e}")

            # update_info送信（今回更新があった場合のみ）
            if 今回更新あり:
                try:
                    通知チャンネル一覧 = [self.チャンネル]
                    # input_text経由の処理はチャット側（チャンネル0）にも更新完了を通知
                    if 受信種別 == "input_text" and self.チャンネル != "0":
                        通知チャンネル一覧.append("0")
                    await self._update_info送信(通知チャンネル一覧=通知チャンネル一覧)
                except Exception as e:
                    logger.error(f"[CodeAgent] update_info送信エラー: {e}")

        except Exception as e:
            logger.error(f"[CodeAgent] 基本AI処理エラー: {e}")
        
        return 出力メッセージ内容

    async def _バックアップ検証ループ(self, ai_instance: Any) -> bool:
        """バックアップ→検証→修正を繰り返すシンプルループ（最大5回）"""


        # プロジェクトルート（backend_serverの親ディレクトリ）を対象とする
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        アプリ設定 = getattr(self.親, "conf", None)
        # セッション固有のCODE_BASE_PATHを使用
        セッション設定 = self.接続.モデル設定 if self.接続 and hasattr(self.接続, "モデル設定") else None
        今回更新あり = False

        logger.info("[検証ループ] 開始（最大5回）")

        # 初回バックアップ前に少し待機（ファイル書き込み完了を待つ）
        await asyncio.sleep(0.5)

        for n in range(1, 6):  # 最大5回
            # 強制停止フラグチェック
            if self.強制停止フラグ:
                logger.info(f"[検証ループ] 強制停止フラグ検出 → 検証中断")
                break

            # バックアップ実行（差分のみ、セッション固有のCODE_BASE_PATHを使用）
            logger.debug(f"[検証{n}回目] バックアップ実行を呼び出します")
            result = バックアップ実行(アプリ設定=アプリ設定, backend_dir=backend_dir, セッション設定=セッション設定)
            
            # エラー → 終了
            if result is None:
                logger.info(f"[検証{n}回目] バックアップエラー → 検証終了")
                break
            
            最終時刻, 全ファイル, 差分ファイル, 全件フラグ, バックアップフォルダ = result

            # 差分なし → 終了
            if not 差分ファイル:
                logger.info(f"[検証{n}回目] 差分なし → 検証終了")
                break

            今回更新あり = True
            
            # 累積変更ファイルに追加
            追加件数 = self._累積変更ファイル追加(差分ファイル)
            logger.info(f"[検証{n}回目] 総ファイル数={len(全ファイル)}, 差分={len(差分ファイル)}件, 累積={len(self.累積変更ファイル)}件, 全件={全件フラグ}")
            
            # 検証メッセージ送信
            フォルダ名 = os.path.basename(バックアップフォルダ)
            ファイル一覧 = "\n".join(f"・{f}" for f in 差分ファイル)
            
            await self.接続.send_to_channel(self.チャンネル, {
                "セッションID": self.セッションID,
                "メッセージ識別": "output_text",
                "メッセージ内容": f"\n【検証開始】({n}回目)\n\n"
            })

            # 検証プロンプト
            プロンプトファイル一覧 = "\n".join(f"- {f}" for f in 差分ファイル)
            検証プロンプト = (
                f"【{n}回目の検証】\n"
                f"差分ファイル{len(差分ファイル)}件:\n{プロンプトファイル一覧}\n\n"
                f"バックアップフォルダ「{フォルダ名}」を変更内容でリネームし、\n"
                f"ファイルの検証を行い、問題があれば修正してください。\n"
                f"問題がなければ「検証完了」とだけ回答してください。"
            )

            # ストリーム開始通知（検証）
            await self._ストリーム開始通知送信()

            # AI検証実行
            検証結果 = await ai_instance.実行(
                要求テキスト=検証プロンプト,
                変更ファイル一覧=差分ファイル,
                絶対パス=self.絶対パス or None,
            ) or "（応答なし）"

            # ストリーム終了通知（検証）
            await self._ストリーム終了通知送信()

            # 検証結果送信
            await self.接続.send_to_channel(self.チャンネル, {
                "セッションID": self.セッションID,
                "メッセージ識別": "output_text",
                "メッセージ内容": 検証結果
            })
            
            # 会話履歴保存
            if self.保存関数:
                self.保存関数(
                    セッションID=self.セッションID,
                    チャンネル=self.チャンネル,
                    メッセージ識別="output_text",
                    メッセージ内容=検証結果,
                    ファイル名=None,
                    サムネイル画像=None
                )

        # 検証完了メッセージ送信（強制停止でなく、かつ検証を実行した場合のみ）
        if not self.強制停止フラグ and 今回更新あり:
            await self.接続.send_to_channel(self.チャンネル, {
                "セッションID": self.セッションID,
                "メッセージ識別": "output_text",
                "メッセージ内容": "\n【検証完了】\n\n"
            })

        return 今回更新あり

    async def _生成ファイル通知(self) -> None:
        """生成された画像などのファイルをチェックしてinputチャンネルに通知"""
        import glob
        import time

        # チェック対象ディレクトリと画像拡張子
        チェックディレクトリ = ["output", "temp/output", "images", "assets"]
        画像拡張子 = ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp", "*.webp"]

        # 現在時刻から1分以内に作成されたファイルを検出
        現在時刻 = time.time()
        検出時間範囲秒 = 60  # 1分

        検出ファイル一覧 = []

        for ディレクトリ in チェックディレクトリ:
            if not os.path.exists(ディレクトリ):
                continue

            for 拡張子 in 画像拡張子:
                パターン = os.path.join(ディレクトリ, "**", 拡張子)
                for ファイルパス in glob.glob(パターン, recursive=True):
                    try:
                        # ファイルの作成時刻を確認
                        ファイル作成時刻 = os.path.getctime(ファイルパス)
                        if 現在時刻 - ファイル作成時刻 <= 検出時間範囲秒:
                            検出ファイル一覧.append(ファイルパス)
                    except Exception as e:
                        logger.warning(f"[CodeAgent] ファイル時刻チェックエラー: {ファイルパス}, {e}")

        # 検出されたファイルをinputチャンネルに通知
        for ファイルパス in 検出ファイル一覧:
            try:
                # サムネイル生成（オプション：ここでは省略し、Noneを送信）
                サムネイル = None

                通知メッセージ = f"ファイルが生成されました: {ファイルパス}"

                # inputチャンネルにoutput_file送信
                await self.接続.send_to_channel("input", {
                    "セッションID": self.セッションID,
                    "チャンネル": "input",
                    "メッセージ識別": "output_file",
                    "メッセージ内容": 通知メッセージ,
                    "ファイル名": ファイルパス,
                    "サムネイル画像": サムネイル
                })

                logger.info(f"[CodeAgent] ファイル生成通知送信: {ファイルパス}")

            except Exception as e:
                logger.error(f"[CodeAgent] ファイル通知送信エラー: {ファイルパス}, {e}")

    async def _update_info送信(self, 通知チャンネル一覧=None) -> None:
        """累積変更ファイルがある場合、update_infoメッセージを送信"""
        if not self.累積変更ファイル:
            logger.debug("[CodeAgent] 累積変更ファイルなし、update_info送信スキップ")
            return

        # 相対パス一覧（重複排除）
        相対パス一覧 = list(dict.fromkeys(self.累積変更ファイル))

        if not 通知チャンネル一覧:
            通知チャンネル一覧 = [self.チャンネル]
        送信先チャンネル一覧 = list(dict.fromkeys(通知チャンネル一覧))

        # update_infoメッセージ送信
        for 送信先チャンネル in 送信先チャンネル一覧:
            await self.接続.send_to_channel(送信先チャンネル, {
                "セッションID": self.セッションID,
                "メッセージ識別": "update_info",
                "メッセージ内容": {
                    "update_files": 相対パス一覧
                },
                "ファイル名": None,
                "サムネイル画像": None
            })

        logger.info(
            f"[CodeAgent] update_info送信完了: {len(相対パス一覧)}件のファイル, "
            f"送信先={送信先チャンネル一覧}"
        )

        # 注意: 累積変更ファイルはクリアしない（次回のリクエストでも累積し続ける）
        # クリアが必要な場合は、ユーザーがアプリ再起動またはリセット再起動を実行する


    async def _処理_input_file(self, 受信データ: dict) -> None:
        """input_file処理: temp/outputコピー → output_file送信"""
        try:

            
            # 受信データから相対パスを取得
            入力ファイル名 = 受信データ.get("ファイル名")  # "temp/input/20260128.123456.xxx.png"
            サムネイル = 受信データ.get("サムネイル画像")
            
            if not 入力ファイル名:
                return
            
            if not os.path.exists(入力ファイル名):
                logger.warning(f"[CodeAgent] 入力ファイルが見つかりません: {入力ファイル名}")
                return
            
            # AI処理を模倣（1～10秒のランダムsleep）
            待機時間 = random.uniform(1.0, 10.0)
            await asyncio.sleep(待機時間)
            
            # 同じファイル名でtemp/outputへコピー
            ファイル名のみ = os.path.basename(入力ファイル名)  # "20260128.123456.xxx.png"
            os.makedirs("temp/output", exist_ok=True)
            出力ファイル名 = f"temp/output/{ファイル名のみ}"
            shutil.copyfile(入力ファイル名, 出力ファイル名)
            
            # 1) output_file送信（チャンネル登録されている場合のみ）
            await self.接続.send_to_channel(self.チャンネル, {
                "セッションID": self.セッションID,
                "メッセージ識別": "output_file",
                "メッセージ内容": f"ファイル出力: {ファイル名のみ}",
                "ファイル名": 出力ファイル名,
                "サムネイル画像": サムネイル
            })
            
            # 2) 会話履歴保存
            if self.保存関数:
                self.保存関数(
                    セッションID=self.セッションID,
                    チャンネル=self.チャンネル,
                    メッセージ識別="output_file",
                    メッセージ内容=f"ファイル出力: {ファイル名のみ}",
                    ファイル名=出力ファイル名,
                    サムネイル画像=サムネイル
                )
        except Exception as e:
            logger.error(f"[CodeAgent] チャンネル{self.チャンネル} input_file処理エラー: {e}")

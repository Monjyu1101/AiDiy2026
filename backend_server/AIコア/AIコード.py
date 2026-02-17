# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101
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
    "このプロジェクトの概要は`_AiDiy.md`を確認してください。",
    "概要以外にも`*.md`の記載内容は必要に応じて確認してください。",
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
        self.強制停止フラグ = False  # cancel_agent用

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

    def _select_ai_module(self) -> Optional[ModuleType]:
        """AI_NAMEに応じたコードモジュールを選択してインポート"""
        module_name = "AIコア.AIコード_etc"
        if self.AI_NAME == "claude-sdk":
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
            await self.AIインスタンス.開始()
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
        """
        # 強制停止フラグをリセット
        self.強制停止フラグ = False
        # 累積変更ファイルをクリア
        self.累積変更ファイル = []
        self._累積変更ファイルキー = set()
        
        await self._基本AI処理(受信データ)

    async def _処理_input_request(self, 受信データ: dict) -> None:
        """
        input_request処理:
        1. inputチャンネルへ開始通知（音声付き）
        2. input_text処理（_基本AI処理）
        3. output_request送信（チャンネル0へ）
        4. inputチャンネルへ完了通知（音声付き）
        """
        # 強制停止フラグをリセット
        self.強制停止フラグ = False
        try:
            メッセージ内容 = 受信データ.get("メッセージ内容", "")
            
            # 添付ファイル一覧があればメッセージに追記
            添付ファイル一覧 = 受信データ.get("添付ファイル一覧", [])
            if 添付ファイル一覧:
                有効ファイル = [p for p in 添付ファイル一覧 if os.path.exists(p)]
                if 有効ファイル:
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
                    "メッセージ内容": 開始メッセージ,
                    "ファイル名": None,
                    "サムネイル画像": None
                })
            except Exception as e:
                logger.warning(f"[CodeAgent] inputチャンネルへの開始メッセージ送信エラー: {e}")
            try:
                if hasattr(self.接続, "live_processor") and self.接続.live_processor:
                    await self.接続.live_processor.開始()
                    await self.接続.live_processor.テキスト送信(開始メッセージ)
            except Exception as e:
                logger.warning(f"[CodeAgent] LiveAI開始メッセージ送信エラー: {e}")

            # 2. 基本AI処理（input_text処理と同じ）
            出力メッセージ内容 = await self._基本AI処理(受信データ)

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
                    "メッセージ内容": 完了メッセージ,
                    "ファイル名": None,
                    "サムネイル画像": None
                })
            except Exception as e:
                logger.warning(f"[CodeAgent] inputチャンネルへの完了メッセージ送信エラー: {e}")
            try:
                if hasattr(self.接続, "live_processor") and self.接続.live_processor:
                    await self.接続.live_processor.開始()
                    await self.接続.live_processor.テキスト送信(完了メッセージ)
            except Exception as e:
                logger.warning(f"[CodeAgent] LiveAI完了メッセージ送信エラー: {e}")

        except Exception as e:
            logger.error(f"[CodeAgent] チャンネル{self.チャンネル} input_request処理エラー: {e}")

    async def _基本AI処理(self, 受信データ: dict) -> str:
        """
        基本AI処理（input_text/input_request共通）:
        1. AI実行 + output_text送信
        2. バックアップ検証ループ（最大5回）
        3. 生成ファイル通知
        4. update_info送信

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
                有効ファイル = [p for p in 添付ファイル一覧 if os.path.exists(p)]
                if 有効ファイル:
                    添付テキスト = "\n``` 添付ファイル\n"
                    for パス in 有効ファイル:
                        添付テキスト += f"{パス}\n"
                    添付テキスト += "```"
                    メッセージ内容 = メッセージ内容 + 添付テキスト
                    logger.info(f"[CodeAgent] 添付ファイル追記: {len(有効ファイル)}件")

            # 処理要求ログ
            セッションID_短縮 = self.セッションID[:10] if self.セッションID else '不明'
            logger.info(f"[CodeAgent] 実行パス: {self.絶対パス}")
            logger.info(
                f"処理要求: チャンネル={self.チャンネル}, ソケット={セッションID_短縮}...,\n{メッセージ内容.rstrip()}\n"
            )

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

            # 強制停止フラグチェック
            if self.強制停止フラグ:
                logger.info(f"[CodeAgent] チャンネル{self.チャンネル} 強制停止フラグ検出（AI実行後）")
                出力メッセージ内容 = "処理は強制中断しました。"
                # output_stream で中断通知
                await self.接続.send_to_channel(self.チャンネル, {
                    "セッションID": self.セッションID,
                    "チャンネル": self.チャンネル,
                    "メッセージ識別": "output_stream",
                    "メッセージ内容": "<<< 処理中断 >>>",
                    "ファイル名": None,
                    "サムネイル画像": None
                })

            # 処理応答ログ
            logger.info(
                f"処理応答: チャンネル={self.チャンネル}, ソケット={セッションID_短縮}...,\n{出力メッセージ内容.rstrip()}\n"
            )

            # output_text送信（自チャンネル）
            await self.接続.send_to_channel(self.チャンネル, {
                "セッションID": self.セッションID,
                "メッセージ識別": "output_text",
                "メッセージ内容": 出力メッセージ内容,
                "ファイル名": None,
                "サムネイル画像": None
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

            # 強制停止時はバックアップ検証・ファイル通知・update_infoをスキップ
            if self.強制停止フラグ:
                logger.info(f"[CodeAgent] チャンネル{self.チャンネル} 強制停止のため後続処理スキップ")
                return 出力メッセージ内容

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
            
            # 差分なし → 終了
            if not result:
                logger.info(f"[検証{n}回目] 差分なし → 検証終了")
                break
            
            最終時刻, 全ファイル, 差分ファイル, 全件フラグ, バックアップフォルダ = result
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
                "メッセージ内容": f"【{n}回目の検証】\n差分ファイル{len(差分ファイル)}件:\n{ファイル一覧}",
                "ファイル名": None,
                "サムネイル画像": None
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
            
            # AI検証実行
            検証結果 = await ai_instance.実行(
                要求テキスト=検証プロンプト,
                変更ファイル一覧=差分ファイル,
                絶対パス=self.絶対パス or None,
            ) or "（応答なし）"
            
            # 検証結果送信
            await self.接続.send_to_channel(self.チャンネル, {
                "セッションID": self.セッションID,
                "メッセージ識別": "output_text",
                "メッセージ内容": 検証結果,
                "ファイル名": None,
                "サムネイル画像": None
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

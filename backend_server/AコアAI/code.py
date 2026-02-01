# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

"""
AコアAI コードエージェント処理プロセッサ
非同期キューでコード要求を受け取り、AI応答を生成してWebSocketへ返す
エージェント1-4（チャンネル1-4）専用
"""

import asyncio
import importlib
from typing import Optional

from log_config import get_logger

logger = get_logger(__name__)


class CodeAgent:
    """コードエージェント処理クラス（キュー処理）- エージェント1-4（チャンネル1-4）専用"""

    def __init__(
        self,
        親=None,
        ソケットID: str = "",
        チャンネル: int = 0,
        絶対パス: str = "",
        AI_NAME: str = "",
        AI_MODEL: str = "",
        接続=None,
        保存関数=None,
    ):
        self.ソケットID = ソケットID
        self.チャンネル = チャンネル
        self.接続 = 接続
        self.保存関数 = 保存関数
        self.AI_NAME = AI_NAME
        self.AI_MODEL = AI_MODEL
        self.絶対パス = 絶対パス
        self.親 = 親
        self.AIモジュール = self._select_ai_module()
        self.AIインスタンス = None
        self.is_alive = False
        self.コード処理Ｑ = asyncio.Queue()
        self.worker_task: Optional[asyncio.Task] = None
        self.会話履歴 = []  # エージェント専用の会話履歴

    def _select_ai_module(self):
        """AI_NAMEに応じたコードモジュールを選択してインポート"""
        module_name = "AコアAI.code_etc"
        if self.AI_NAME == "claude-sdk":
            module_name = "AコアAI.code_claude"
        try:
            return importlib.import_module(module_name)
        except Exception as e:
            logger.error(f"[CodeAgent] AIモジュールのインポート失敗: {module_name} error={e}")
            return None

    async def _ensure_ai_instance(self):
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
                ソケットID=self.ソケットID,
                チャンネル=self.チャンネル,
                AI_NAME=self.AI_NAME,
                AI_MODEL=self.AI_MODEL,
                絶対パス=self.絶対パス or None,
            )
            await self.AIインスタンス.開始()
            return self.AIインスタンス
        except Exception as e:
            logger.error(f"[CodeAgent] CodeAI初期化エラー: {e}")
            self.AIインスタンス = None
            return None

    async def 開始(self):
        """コード処理ワーカーを開始"""
        self.is_alive = True
        if self.worker_task is None or self.worker_task.done():
            self.worker_task = asyncio.create_task(self._コード処理ワーカー())
            logger.debug(f"[CodeAgent] チャンネル{self.チャンネル} 開始")

    async def 終了(self):
        """コード処理ワーカーを終了"""
        self.is_alive = False
        if self.worker_task and not self.worker_task.done():
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        logger.debug(f"[CodeAgent] チャンネル{self.チャンネル} 終了")

    async def コード要求(self, 受信データ: dict):
        """コード要求をキューに追加（受信データ構造体をそのまま投入）"""
        if not 受信データ:
            return
        await self.コード処理Ｑ.put(受信データ)

    async def _コード処理ワーカー(self):
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

    async def _処理_input_text(self, 受信データ: dict):
        """input_text処理: [ECHO]付きoutput_text送信"""
        try:
            メッセージ内容 = 受信データ.get("メッセージ内容", "")

            # 処理要求ログ
            ソケットID_短縮 = self.ソケットID[:10] if self.ソケットID else '不明'
            logger.info(
                f"処理要求: チャンネル={self.チャンネル}, ソケット={ソケットID_短縮}...,\n{メッセージ内容.rstrip()}\n"
            )

            出力メッセージ内容 = ""
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

            # 処理応答ログ
            logger.info(
                f"処理応答: チャンネル={self.チャンネル}, ソケット={ソケットID_短縮}...,\n{出力メッセージ内容.rstrip()}\n"
            )

            # 1) output_text送信（チャンネル登録されている場合のみ）
            await self.接続.send_to_channel(self.チャンネル, {
                "ソケットID": self.ソケットID,
                "メッセージ識別": "output_text",
                "メッセージ内容": 出力メッセージ内容,
                "ファイル名": None,
                "サムネイル画像": None
            })
            
            # 2) 会話履歴保存
            if self.保存関数:
                self.保存関数(
                    ソケットID=self.ソケットID,
                    チャンネル=self.チャンネル,
                    メッセージ識別="output_text",
                    メッセージ内容=出力メッセージ内容,
                    ファイル名=None,
                    サムネイル画像=None
                )
        except Exception as e:
            logger.error(f"[CodeAgent] チャンネル{self.チャンネル} input_text処理エラー: {e}")

    async def _処理_input_request(self, 受信データ: dict):
        """input_request処理: 前後処理付きでAI実行"""
        try:
            メッセージ内容 = 受信データ.get("メッセージ内容", "")
            ソケットID_短縮 = self.ソケットID[:10] if self.ソケットID else '不明'

            # 処理要求ログ
            logger.info(
                f"処理要求(input_request): チャンネル={self.チャンネル}, ソケット={ソケットID_短縮}...,\n{メッセージ内容.rstrip()}\n"
            )

            # 通常処理の前: チャンネル-1へ処理開始を連絡
            開始メッセージ = (
                f"コードエージェント{self.チャンネル}です。\n"
                f"処理要求を開始しました。\n"
                f"詳細を省き、端的に音声で処理の開始を伝えてください。\n"
                f"``` 要求\n"
                f"{メッセージ内容}\n"
                f"```"
            )
            try:
                await self.接続.send_to_channel(-1, {
                    "ソケットID": self.ソケットID,
                    "チャンネル": -1,
                    "メッセージ識別": "input_text",
                    "メッセージ内容": 開始メッセージ,
                    "ファイル名": None,
                    "サムネイル画像": None
                })
            except Exception as e:
                logger.warning(f"[CodeAgent] チャンネル-1への開始メッセージ送信エラー: {e}")
            try:
                if hasattr(self.接続, "live_processor") and self.接続.live_processor:
                    await self.接続.live_processor.開始()
                    await self.接続.live_processor.テキスト送信(開始メッセージ)
            except Exception as e:
                logger.warning(f"[CodeAgent] LiveAI開始メッセージ送信エラー: {e}")

            # 通常処理: AI実行
            出力メッセージ内容 = ""
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

            # 処理応答ログ
            logger.info(
                f"処理応答(input_request): チャンネル={self.チャンネル}, ソケット={ソケットID_短縮}...,\n{出力メッセージ内容.rstrip()}\n"
            )

            # 通常のoutput_text送信
            await self.接続.send_to_channel(self.チャンネル, {
                "ソケットID": self.ソケットID,
                "メッセージ識別": "output_text",
                "メッセージ内容": 出力メッセージ内容,
                "ファイル名": None,
                "サムネイル画像": None
            })

            # 会話履歴保存
            if self.保存関数:
                self.保存関数(
                    ソケットID=self.ソケットID,
                    チャンネル=self.チャンネル,
                    メッセージ識別="output_text",
                    メッセージ内容=出力メッセージ内容,
                    ファイル名=None,
                    サムネイル画像=None
                )

            # 通常処理の後: チャンネル-1へ処理終了を連絡
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
                await self.接続.send_to_channel(-1, {
                    "ソケットID": self.ソケットID,
                    "チャンネル": -1,
                    "メッセージ識別": "input_text",
                    "メッセージ内容": 完了メッセージ,
                    "ファイル名": None,
                    "サムネイル画像": None
                })
            except Exception as e:
                logger.warning(f"[CodeAgent] チャンネル-1への完了メッセージ送信エラー: {e}")
            try:
                if hasattr(self.接続, "live_processor") and self.接続.live_processor:
                    await self.接続.live_processor.開始()
                    await self.接続.live_processor.テキスト送信(完了メッセージ)
            except Exception as e:
                logger.warning(f"[CodeAgent] LiveAI完了メッセージ送信エラー: {e}")

        except Exception as e:
            logger.error(f"[CodeAgent] チャンネル{self.チャンネル} input_request処理エラー: {e}")

    async def _処理_input_file(self, 受信データ: dict):
        """input_file処理: temp/outputコピー → output_file送信"""
        try:
            import shutil
            import os
            import random
            
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
                "ソケットID": self.ソケットID,
                "メッセージ識別": "output_file",
                "メッセージ内容": f"ファイル出力: {ファイル名のみ}",
                "ファイル名": 出力ファイル名,
                "サムネイル画像": サムネイル
            })
            
            # 2) 会話履歴保存
            if self.保存関数:
                self.保存関数(
                    ソケットID=self.ソケットID,
                    チャンネル=self.チャンネル,
                    メッセージ識別="output_file",
                    メッセージ内容=f"ファイル出力: {ファイル名のみ}",
                    ファイル名=出力ファイル名,
                    サムネイル画像=サムネイル
                )
        except Exception as e:
            logger.error(f"[CodeAgent] チャンネル{self.チャンネル} input_file処理エラー: {e}")

# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

"""
AIコア チャット処理プロセッサ
非同期キューでチャット要求を受け取り、AI応答を生成してWebSocketへ返す
"""

import asyncio
import importlib
from typing import Optional

from log_config import get_logger

logger = get_logger(__name__)


class Chat:
    """チャット処理クラス（キュー処理）- チャンネル0専用"""

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
        self.チャット処理Ｑ = asyncio.Queue()
        self.worker_task: Optional[asyncio.Task] = None
        self.会話履歴 = []  # チャンネル専用の会話履歴

    def _select_ai_module(self):
        """AI_NAMEに応じたチャットモジュールを選択してインポート"""
        module_name = "AIコア.AIチャット_openrt"
        if self.AI_NAME in ("gemini", "freeai"):
            module_name = "AIコア.AIチャット_gemini"
        try:
            return importlib.import_module(module_name)
        except Exception as e:
            logger.error(f"[Chat] AIモジュールのインポート失敗: {module_name} error={e}")
            return None

    async def _ensure_ai_instance(self):
        """AIモジュールのChatAIインスタンスを生成・開始"""
        if not self.AIモジュール:
            return None
        if self.AIインスタンス:
            return self.AIインスタンス
        try:
            api_key = ""
            try:
                conf_json = getattr(self.親, "conf", None)
                if conf_json and hasattr(conf_json, "json"):
                    if self.AI_NAME in ("gemini", "freeai"):
                        api_key = conf_json.json.get("gemini_key_id", "")
                        if self.AI_NAME == "freeai":
                            api_key = conf_json.json.get("freeai_key_id", "") or api_key
                    else:
                        api_key = conf_json.json.get("openrt_key_id", "")
            except Exception:
                api_key = ""
            ChatAI = getattr(self.AIモジュール, "ChatAI", None)
            if ChatAI is None:
                logger.error("[Chat] ChatAIクラスが見つかりません")
                return None
            self.AIインスタンス = ChatAI(
                親=self.親,
                ソケットID=self.ソケットID,
                チャンネル=self.チャンネル,
                AI_NAME=self.AI_NAME,
                AI_MODEL=self.AI_MODEL,
                絶対パス=self.絶対パス or None,
                api_key=api_key or None,
            )
            await self.AIインスタンス.開始()
            return self.AIインスタンス
        except Exception as e:
            logger.error(f"[Chat] ChatAI初期化エラー: {e}")
            self.AIインスタンス = None
            return None

    async def 開始(self):
        """チャット処理ワーカーを開始"""
        self.is_alive = True
        if self.worker_task is None or self.worker_task.done():
            self.worker_task = asyncio.create_task(self._チャット処理ワーカー())
            logger.debug(f"[Chat] チャンネル{self.チャンネル} 開始")

    async def 終了(self):
        """チャット処理ワーカーを終了"""
        self.is_alive = False
        if self.worker_task and not self.worker_task.done():
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        logger.debug(f"[Chat] チャンネル{self.チャンネル} 終了")

    async def チャット要求(self, 受信データ: dict):
        """チャット要求をキューに追加（受信データ構造体をそのまま投入）"""
        if not 受信データ:
            return
        await self.チャット処理Ｑ.put(受信データ)

    async def _チャット処理ワーカー(self):
        """チャット処理ワーカー（キューから取り出して処理）"""
        while self.is_alive:
            try:
                try:
                    受信データ = await asyncio.wait_for(self.チャット処理Ｑ.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    await asyncio.sleep(0.2)
                    continue

                if not isinstance(受信データ, dict):
                    continue
                    
                メッセージ識別 = 受信データ.get("メッセージ識別", "")
                
                if メッセージ識別 == "input_text":
                    # テキスト処理: [ECHO]付きoutput_text送信 → 会話履歴保存
                    await self._処理_input_text(受信データ)
                elif メッセージ識別 == "input_file":
                    # ファイル処理: temp/outputコピー → output_file送信 → 会話履歴保存
                    await self._処理_input_file(受信データ)
                
                self.チャット処理Ｑ.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Chat] チャンネル{self.チャンネル} 処理エラー: {e}")
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
                    logger.info(
                        f"[Chat] AI実行開始: AI={self.AI_NAME} モデル={self.AI_MODEL} チャンネル={self.チャンネル}"
                    )
                    出力メッセージ内容 = await ai_instance.実行(
                        要求テキスト=メッセージ内容,
                    )
                    logger.info(
                        f"[Chat] AI実行結果: 文字数={len(出力メッセージ内容) if 出力メッセージ内容 is not None else 'None'}"
                    )
            except Exception as e:
                logger.error(f"[Chat] AI実行エラー: {e}")
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
            logger.error(f"[Chat] チャンネル{self.チャンネル} input_text処理エラー: {e}")

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
                logger.warning(f"[Chat] 入力ファイルが見つかりません: {入力ファイル名}")
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
            logger.error(f"[Chat] チャンネル{self.チャンネル} input_file処理エラー: {e}")


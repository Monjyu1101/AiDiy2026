# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

"""
AIコア コードエージェント処理プロセッサ
非同期キューでコード要求を受け取り、AI応答を生成してWebSocketへ返す
エージェント1-4（チャンネル1-4）専用
"""

import asyncio
import importlib
import os
from typing import Optional

from log_config import get_logger

logger = get_logger(__name__)


class CodeAgent:
    """コードエージェント処理クラス（キュー処理）- エージェント1-4（チャンネル1-4）専用"""

    def __init__(
        self,
        親=None,
        セッションID: str = "",
        チャンネル: int = 0,
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
        self.AIモジュール = self._select_ai_module()
        self.AIインスタンス = None
        self.is_alive = False
        self.コード処理Ｑ = asyncio.Queue()
        self.worker_task: Optional[asyncio.Task] = None
        self.会話履歴 = []  # エージェント専用の会話履歴

    def _select_ai_module(self):
        """AI_NAMEに応じたコードモジュールを選択してインポート"""
        module_name = "AIコア.AIコード_etc"
        if self.AI_NAME == "claude-sdk":
            module_name = "AIコア.AIコード_claude"
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
                セッションID=self.セッションID,
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
            セッションID_短縮 = self.セッションID[:10] if self.セッションID else '不明'
            logger.info(
                f"処理要求: チャンネル={self.チャンネル}, ソケット={セッションID_短縮}...,\n{メッセージ内容.rstrip()}\n"
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
                f"処理応答: チャンネル={self.チャンネル}, ソケット={セッションID_短縮}...,\n{出力メッセージ内容.rstrip()}\n"
            )

            # 1) output_text送信（チャンネル登録されている場合のみ）
            await self.接続.send_to_channel(self.チャンネル, {
                "セッションID": self.セッションID,
                "メッセージ識別": "output_text",
                "メッセージ内容": 出力メッセージ内容,
                "ファイル名": None,
                "サムネイル画像": None
            })
            
            # 2) 会話履歴保存
            if self.保存関数:
                self.保存関数(
                    セッションID=self.セッションID,
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
            セッションID_短縮 = self.セッションID[:10] if self.セッションID else '不明'

            # 処理要求ログ
            logger.info(
                f"処理要求(input_request): チャンネル={self.チャンネル}, ソケット={セッションID_短縮}...,\n{メッセージ内容.rstrip()}\n"
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
                    "セッションID": self.セッションID,
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
                f"処理応答(input_request): チャンネル={self.チャンネル}, ソケット={セッションID_短縮}...,\n{出力メッセージ内容.rstrip()}\n"
            )

            # 通常のoutput_text送信
            await self.接続.send_to_channel(self.チャンネル, {
                "セッションID": self.セッションID,
                "メッセージ識別": "output_text",
                "メッセージ内容": 出力メッセージ内容,
                "ファイル名": None,
                "サムネイル画像": None
            })

            # 会話履歴保存
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
            try:
                await self._バックアップ検証ループ(ai_instance)
            except Exception as e:
                logger.error(f"[CodeAgent] バックアップ検証ループエラー: {e}")

            # 生成されたファイルをチェックしてチャンネル-1に通知
            try:
                await self._生成ファイル通知()
            except Exception as e:
                logger.error(f"[CodeAgent] 生成ファイル通知エラー: {e}")

            # 通常のoutput_request送信

            await self.接続.send_to_channel(0, {
                "セッションID": self.セッションID,
                "メッセージ識別": "output_request",
                "メッセージ内容": 出力メッセージ内容,
                "ファイル名": None,
                "サムネイル画像": None
            })

            # 会話履歴保存
            if self.保存関数:
                self.保存関数(
                    セッションID=self.セッションID,
                    チャンネル=0,
                    メッセージ識別="output_request",
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
                    "セッションID": self.セッションID,
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

    async def _バックアップ検証ループ(self, ai_instance):
        """バックアップ実行 → 変更ファイルがあればAIに自己検証させる（最大5回）"""
        from AIコア.AIバックアップ import バックアップ実行

        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        アプリ設定 = getattr(self.親, "conf", None)

        最大検証回数 = 5
        for n in range(1, 最大検証回数 + 1):
            # バックアップ実行
            try:
                result = バックアップ実行(アプリ設定=アプリ設定, backend_dir=backend_dir)
            except Exception as e:
                logger.error(f"[CodeAgent] バックアップ実行エラー: {e}")
                break

            # バックアップファイルがなければ終了
            if result is None:
                logger.info("[CodeAgent] バックアップ: 対象なし（スキップ）")
                break
            最大日時, 全ファイル, バックアップファイル, 全件フラグ, バックアップフォルダ絶対パス = result
            if not バックアップファイル:
                logger.info("[CodeAgent] バックアップ: 差分ファイルなし（検証終了）")
                break

            # 検証開始メッセージ送信
            検証開始テキスト = f"{n}回目の検証作業を開始します。"
            logger.info(f"[CodeAgent] {検証開始テキスト}")
            await self.接続.send_to_channel(self.チャンネル, {
                "セッションID": self.セッションID,
                "メッセージ識別": "output_text",
                "メッセージ内容": 検証開始テキスト,
                "ファイル名": None,
                "サムネイル画像": None
            })

            # 検証プロンプト構築
            変更ファイル一覧テキスト = "\n".join(f"- {f}" for f in バックアップファイル)
            バックアップフォルダ名 = os.path.basename(バックアップフォルダ絶対パス)
            検証プロンプト = (
                f"{n}回目の検証作業を開始します。\n"
                f"\n"
                f"変更ファイル一覧:\n"
                f"{変更ファイル一覧テキスト}\n"
                f"\n"
                f"バックアップ先: {バックアップフォルダ絶対パス}\n"
                f"\n"
                f"以下の作業を行ってください:\n"
                f"1) バックアップフォルダ「{バックアップフォルダ名}」を変更点の要約名にリネームしてください（例: {バックアップフォルダ名}.リブートファイル名変更）\n"
                f"2) 並行開発の可能性もあるため、上記の変更ファイルが自分の変更として正しいか検証してください。問題があれば修正してください。\n"
            )

            # AI検証実行
            検証結果 = ""
            try:
                検証結果 = await ai_instance.実行(
                    要求テキスト=検証プロンプト,
                    変更ファイル一覧=バックアップファイル,
                    絶対パス=self.絶対パス or None,
                )
            except Exception as e:
                logger.error(f"[CodeAgent] 検証AI実行エラー: {e}")
                検証結果 = f"検証中にエラーが発生しました: {e}"
            if not 検証結果:
                検証結果 = "（検証結果なし）"

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

        else:
            logger.warning(f"[CodeAgent] 検証ループが最大回数({最大検証回数})に到達しました")

    async def _生成ファイル通知(self):
        """生成された画像などのファイルをチェックしてチャンネル-1に通知"""
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
        
        # 検出されたファイルをチャンネル-1に通知
        for ファイルパス in 検出ファイル一覧:
            try:
                # サムネイル生成（オプション：ここでは省略し、Noneを送信）
                サムネイル = None
                
                通知メッセージ = f"ファイルが生成されました: {ファイルパス}"
                
                # チャンネル-1にoutput_file送信
                await self.接続.send_to_channel(-1, {
                    "セッションID": self.セッションID,
                    "チャンネル": -1,
                    "メッセージ識別": "output_file",
                    "メッセージ内容": 通知メッセージ,
                    "ファイル名": ファイルパス,
                    "サムネイル画像": サムネイル
                })
                
                logger.info(f"[CodeAgent] ファイル生成通知送信: {ファイルパス}")
                
            except Exception as e:
                logger.error(f"[CodeAgent] ファイル通知送信エラー: {ファイルパス}, {e}")


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


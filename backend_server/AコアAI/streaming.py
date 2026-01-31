# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

"""
ストリーミング処理プロセッサ
各WebSocketセッション専用のストリーミングタスクを管理
"""

import asyncio
from typing import Optional, TYPE_CHECKING
from log_config import get_logger

if TYPE_CHECKING:
    from ws_manager import SessionConnection

logger = get_logger(__name__)


class StreamingProcessor:
    """ストリーミング処理を担当するクラス"""

    def __init__(self, socket_id: str, connection: "SessionConnection"):
        """
        初期化

        Args:
            socket_id: ソケットID
            connection: WebSocket接続オブジェクト
        """
        self.socket_id = socket_id
        self.connection = connection
        self.is_running = False
        self.task: Optional[asyncio.Task] = None

    async def start(self):
        """ストリーミング処理を開始"""
        if self.is_running:
            logger.warning(f"既にストリーミング処理が実行中です: {self.socket_id}")
            return

        self.is_running = True
        self.task = asyncio.create_task(self._process())
        logger.debug(f"ストリーミング処理開始: {self.socket_id}")

    async def stop(self):
        """ストリーミング処理を停止"""
        self.is_running = False

        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        logger.debug(f"ストリーミング処理停止: {self.socket_id}")

    async def _process(self):
        """
        ストリーミング処理のメインループ
        各セッション専用のストリーミングタスクとして動作
        """
        logger.debug(f"ストリーミングタスク起動: {self.socket_id}")

        try:
            # ストリーミング開始通知
            await self.connection.send_json({
                "メッセージ識別": "streaming_started",
                "ソケットID": self.socket_id,
                "メッセージ内容": "ストリーミング処理を開始しました"
            })

            # メインループ
            counter = 0
            while self.is_running and self.connection.is_connected:
                await asyncio.sleep(5)  # 5秒ごと
                counter += 1

                # ハートビートメッセージ
                await self.connection.send_json({
                    "メッセージ識別": "heartbeat",
                    "ソケットID": self.socket_id,
                    "メッセージ内容": {
                        "カウント": counter,
                        "時刻": asyncio.get_event_loop().time()
                    }
                })

                # ここで実際のAI処理を実装
                # 例: チャットAI応答のストリーミング
                # 例: 画像認識結果の段階的送信
                # 例: エージェント出力のリアルタイム表示
                await self._process_ai_tasks()

        except asyncio.CancelledError:
            logger.debug(f"ストリーミングタスクキャンセル: {self.socket_id}")
            raise
        except Exception as e:
            logger.error(f"ストリーミングエラー ({self.socket_id}): {e}")
            await self.connection.send_json({
                "メッセージ識別": "error",
                "ソケットID": self.socket_id,
                "メッセージ内容": str(e)
            })
        finally:
            self.is_running = False
            logger.debug(f"ストリーミングタスク終了: {self.socket_id}")

    async def _process_ai_tasks(self):
        """
        AI処理タスク
        画面状態に応じて適切なAI処理を実行
        """
        画面状態 = self.connection.画面状態
        ボタン状態 = self.connection.ボタン状態
        モデル設定 = self.connection.モデル設定

        # チャットAI処理
        if 画面状態.get("チャット", False):
            await self._process_chat_ai()

        # イメージAI処理
        if 画面状態.get("イメージ", False) and ボタン状態.get("カメラ", False):
            await self._process_image_ai()

        # エージェントAI処理
        for i in range(1, 5):
            if 画面状態.get(f"エージェント{i}", False):
                await self._process_agent_ai(i)

    async def _process_chat_ai(self):
        """チャットAI処理（実装予定）"""
        # TODO: ChatAIの実装
        # モデル設定: self.connection.モデル設定["CHAT_AI"]
        # 音声入力: self.connection.ボタン状態["マイク"]
        # 音声出力: self.connection.ボタン状態["スピーカー"]
        pass

    async def _process_image_ai(self):
        """イメージAI処理（実装予定）"""
        # TODO: 画像認識AIの実装
        pass

    async def _process_agent_ai(self, agent_number: int):
        """エージェントAI処理（実装予定）"""
        # TODO: CodeAI/エージェントの実装
        # モデル設定: self.connection.モデル設定[f"CODE_AI{agent_number}"]
        pass

    async def send_message(self, message_type: str, data: dict):
        """
        クライアントにメッセージを送信

        Args:
            message_type: メッセージタイプ
            data: 送信データ
        """
        await self.connection.send_json({
            "メッセージ識別": message_type,
            "ソケットID": self.socket_id,
            **data
        })

    async def send_output_audio(self, base64_audio: str, mime_type: str = "audio/pcm", チャンネル: int = -1):
        """
        音声出力メッセージを送信

        Args:
            base64_audio: Base64エンコードされた音声データ
            mime_type: MIMEタイプ（デフォルト: audio/pcm）
            チャンネル: チャンネル番号（デフォルト: -1、ストリーム処理用）
        """
        # 音声出力が一時停止中（人間の音声入力中）はスキップ
        if self.connection.output_audio_paused:
            logger.debug(f"音声出力スキップ（一時停止中）: {self.socket_id}")
            return

        await self.connection.send_json({
            "ソケットID": self.socket_id,
            "チャンネル": チャンネル,
            "メッセージ識別": "output_audio",
            "メッセージ内容": mime_type,
            "ファイル名": base64_audio,
            "サムネイル画像": None
        })

    async def handle_client_message(self, message: dict):
        """
        クライアントからのメッセージを処理

        Args:
            message: 受信メッセージ
        """
        msg_type = message.get("メッセージ識別")

        if msg_type == "chat_input":
            # チャット入力を処理
            await self._handle_chat_input(message.get("メッセージ内容", ""))
        elif msg_type == "image_input":
            # 画像入力を処理
            await self._handle_image_input(message.get("画像") or message.get("メッセージ内容"))
        elif msg_type == "agent_command":
            # エージェントコマンドを処理
            await self._handle_agent_command(
                message.get("エージェント番号"),
                message.get("コマンド")
            )
        else:
            logger.warning(f"未知のメッセージタイプ: {msg_type}")

    async def _handle_chat_input(self, text: str):
        """チャット入力の処理（実装予定）"""
        # TODO: チャット入力の処理
        pass

    async def _handle_image_input(self, image_data):
        """画像入力の処理（実装予定）"""
        # TODO: 画像入力の処理
        pass

    async def _handle_agent_command(self, agent_number: int, command: str):
        """エージェントコマンドの処理（実装予定）"""
        # TODO: エージェントコマンドの処理
        pass

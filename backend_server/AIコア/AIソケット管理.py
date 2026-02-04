# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

"""
WebSocket接続管理システム
AIコアのセッション管理とストリーミング処理を担当
"""
from typing import Dict, Optional
from fastapi import WebSocket
import asyncio
import json
import uuid
from log_config import get_logger
from AIコア.AIストリーミング処理 import StreamingProcessor
from AIコア.AI音声処理 import 初期化_音声データ

# ロガー取得
logger = get_logger(__name__)


class WebSocketConnection:
    """
    個別のWebSocket接続を管理するクラス
    セッション内のソケット(-1,0-4)単位で保持
    """

    def __init__(self, websocket: WebSocket, session_id: str, socket_no: int):
        self.websocket = websocket
        self.session_id = session_id
        self.socket_no = socket_no
        self.is_connected = False

    async def accept(self):
        """WebSocket接続を受け入れる"""
        await self.websocket.accept()
        self.is_connected = True
        logger.debug(f"接続確立: session={self.session_id} socket={self.socket_no}")

    async def send_json(self, data: dict):
        """JSONデータを送信"""
        if self.is_connected:
            try:
                await self.websocket.send_json(data)
            except Exception as e:
                logger.error(f"送信エラー (session={self.session_id} socket={self.socket_no}): {e}")
                self.is_connected = False

    async def receive_json(self) -> Optional[dict]:
        """JSONデータを受信"""
        if self.is_connected:
            try:
                return await self.websocket.receive_json()
            except Exception as e:
                logger.error(f"受信エラー (session={self.session_id} socket={self.socket_no}): {e}")
                self.is_connected = False
                return None
        return None

    async def close(self):
        """接続を閉じる"""
        if self.is_connected:
            try:
                await self.websocket.close()
            except Exception:
                pass
            self.is_connected = False
            logger.debug(f"接続クローズ: session={self.session_id} socket={self.socket_no}")


class SessionConnection:
    """
    セッション構造体
    ソケット構造体:
    -1: 共通入力チャンネル（音声、画像）
     0: チャット出力チャンネル
     1: エージェント1出力チャンネル
     2: エージェント2出力チャンネル
     3: エージェント3出力チャンネル
     4: エージェント4出力チャンネル
    """

    def __init__(self, session_id: str):
        self.socket_id = session_id
        self.sockets: Dict[int, Optional[WebSocketConnection]] = {
            -1: None,
            0: None,
            1: None,
            2: None,
            3: None,
            4: None
        }
        self.output_audio_paused = False
        self.画面状態 = {
            "チャット": True,
            "イメージ": False,
            "エージェント1": False,
            "エージェント2": False,
            "エージェント3": False,
            "エージェント4": False
        }
        self.ボタン状態 = {
            "スピーカー": True,
            "マイク": False,
            "カメラ": False
        }
        self.モデル設定 = {}
        self.ソース最終更新日時 = None
        self.streaming_processor: Optional[StreamingProcessor] = None
        self.recognition_processor = None
        self.audio_split_task: Optional[asyncio.Task] = None
        self.audio_data = 初期化_音声データ()

        self.チャンネル別キュー: Dict[int, asyncio.Queue] = {}
        self.チャンネル別処理中: Dict[int, bool] = {}

        self.チャンネル登録状態: Dict[int, bool] = {
            -1: True,
            0: False,
            1: False,
            2: False,
            3: False,
            4: False
        }

    @property
    def is_connected(self) -> bool:
        return any(conn and conn.is_connected for conn in self.sockets.values())

    def set_socket(self, socket_no: int, connection: Optional[WebSocketConnection]):
        self.sockets[socket_no] = connection

    def get_socket(self, socket_no: int) -> Optional[WebSocketConnection]:
        return self.sockets.get(socket_no)

    async def send_json(self, data: dict):
        """チャンネルに応じて送信先ソケットを決定"""
        チャンネル = data.get("チャンネル", None)
        if チャンネル is None:
            チャンネル = -1
        connection = self.sockets.get(チャンネル)
        if not connection or not connection.is_connected:
            logger.warning(f"送信先ソケット未接続: session={self.socket_id} ch={チャンネル}")
            return
        await connection.send_json(data)

    async def send_to_channel(self, チャンネル: int, data: dict):
        既存チャンネル = data.get("チャンネル", None)
        if 既存チャンネル is not None and 既存チャンネル != チャンネル:
            logger.error(
                f"送信チャンネル不一致: send_to_channel={チャンネル}, data.チャンネル={既存チャンネル}"
            )
        data["チャンネル"] = チャンネル
        await self.send_json(data)
        logger.debug(f"チャンネル{チャンネル}に送信: {data.get('メッセージ識別', 'unknown')}")

    def register_channel(self, チャンネル: int):
        logger.info(f"チャンネル{チャンネル}登録通知: {self.socket_id}")

    def unregister_channel(self, チャンネル: int):
        logger.info(f"チャンネル{チャンネル}解除通知: {self.socket_id}")

    def is_channel_registered(self, チャンネル: int) -> bool:
        return True

    def get_or_create_queue(self, チャンネル: int) -> asyncio.Queue:
        if チャンネル not in self.チャンネル別キュー:
            self.チャンネル別キュー[チャンネル] = asyncio.Queue()
            self.チャンネル別処理中[チャンネル] = False
            logger.debug(f"チャンネル{チャンネル}のキューを作成: {self.socket_id}")
        return self.チャンネル別キュー[チャンネル]

    def is_channel_processing(self, チャンネル: int) -> bool:
        return self.チャンネル別処理中.get(チャンネル, False)

    def set_channel_processing(self, チャンネル: int, 処理中: bool):
        self.チャンネル別処理中[チャンネル] = 処理中
        logger.debug(f"チャンネル{チャンネル}の処理状態: {処理中} ({self.socket_id})")

    def update_state(self, 画面: dict, ボタン: dict, manager=None):
        self.画面状態.update(画面)
        self.ボタン状態.update(ボタン)
        if manager:
            manager.save_session_state(self.socket_id, self.画面状態, self.ボタン状態, self.モデル設定, self.ソース最終更新日時)

    def update_model_settings(self, 設定: dict, manager=None):
        self.モデル設定.update(設定)
        if manager:
            manager.save_session_state(self.socket_id, self.画面状態, self.ボタン状態, self.モデル設定, self.ソース最終更新日時)

    async def close(self):
        """セッション全体をクローズ"""
        if self.streaming_processor:
            await self.streaming_processor.stop()
            self.streaming_processor = None
        if self.recognition_processor:
            try:
                await self.recognition_processor.終了()
            except Exception:
                pass
            self.recognition_processor = None
        if self.audio_split_task and not self.audio_split_task.done():
            self.audio_split_task.cancel()
            try:
                await self.audio_split_task
            except asyncio.CancelledError:
                pass
        self.audio_split_task = None
        self.audio_data = 初期化_音声データ()

        for チャンネル, キュー in self.チャンネル別キュー.items():
            while not キュー.empty():
                try:
                    キュー.get_nowait()
                except asyncio.QueueEmpty:
                    break
        self.チャンネル別キュー.clear()
        self.チャンネル別処理中.clear()

        for socket_no, connection in self.sockets.items():
            if connection:
                await connection.close()
                self.sockets[socket_no] = None


class WebSocketManager:
    """WebSocket接続を一元管理するクラス"""

    def __init__(self):
        self.sessions: Dict[str, SessionConnection] = {}
        self.session_states: Dict[str, dict] = {}

    def generate_socket_id(self) -> str:
        """新しいソケットIDを生成（プロセスIDベース）"""
        import os
        import time
        # PID + タイムスタンプ + UUIDの組み合わせで一意性を保証
        pid = os.getpid()
        timestamp = int(time.time() * 1000)
        unique_id = str(uuid.uuid4())[:8]
        socket_id = f"ws-{pid}-{timestamp}-{unique_id}"
        return socket_id

    async def connect(self, websocket: WebSocket, socket_id: Optional[str] = None, socket_no: int = -1, app_conf=None, accept_in_connect: bool = True) -> str:
        """
        WebSocket接続を登録（セッション単位）

        Args:
            websocket: WebSocket接続
            socket_id: 既存のソケットID（リロード時）。Noneの場合は新規生成
            app_conf: アプリケーション設定（新規接続時にコピー）

        Returns:
            socket_id: 使用するソケットID
        """
        # セッションID決定
        if socket_id and socket_id in self.sessions:
            logger.debug(f"既存セッション再接続: {socket_id}")
        else:
            socket_id = socket_id if socket_id else self.generate_socket_id()
            logger.debug(f"新規セッション作成: {socket_id}")

        # セッション作成または取得
        if socket_id not in self.sessions:
            session = SessionConnection(socket_id)

            # セッション状態を復元または初期化
            if socket_id in self.session_states:
                saved_state = self.session_states[socket_id]
                session.画面状態 = saved_state.get("画面", session.画面状態)
                session.ボタン状態 = saved_state.get("ボタン", session.ボタン状態)
                session.モデル設定 = saved_state.get("モデル設定", {})
                session.ソース最終更新日時 = saved_state.get("ソース最終更新日時")
                logger.debug(f"セッション状態を復元: {socket_id}")
            else:
                if app_conf and hasattr(app_conf, 'json'):
                    session.モデル設定 = {
                        # ChatAI設定
                        "CHAT_AI": app_conf.json.get("CHAT_AI", "freeai"),
                        "CHAT_GEMINI_MODEL": app_conf.json.get("CHAT_GEMINI_MODEL", "gemini-3-pro-image-preview"),
                        "CHAT_FREEAI_MODEL": app_conf.json.get("CHAT_FREEAI_MODEL", "gemini-2.5-flash"),
                        "CHAT_OPENRT_MODEL": app_conf.json.get("CHAT_OPENRT_MODEL", "google/gemini-3-pro-image-preview"),
                        # LiveAI設定
                        "LIVE_AI": app_conf.json.get("LIVE_AI", "freeai_live"),
                        "LIVE_GEMINI_MODEL": app_conf.json.get("LIVE_GEMINI_MODEL", "gemini-2.5-flash-native-audio-preview-09-2025"),
                        "LIVE_GEMINI_VOICE": app_conf.json.get("LIVE_GEMINI_VOICE", "Zephyr"),
                        "LIVE_FREEAI_MODEL": app_conf.json.get("LIVE_FREEAI_MODEL", "gemini-2.5-flash-native-audio-preview-09-2025"),
                        "LIVE_FREEAI_VOICE": app_conf.json.get("LIVE_FREEAI_VOICE", "Zephyr"),
                        "LIVE_OPENAI_MODEL": app_conf.json.get("LIVE_OPENAI_MODEL", "gpt-realtime-mini"),
                        "LIVE_OPENAI_VOICE": app_conf.json.get("LIVE_OPENAI_VOICE", "marin"),
                        # CodeAI設定
                        "CODE_AI1": app_conf.json.get("CODE_AI1", "copilot"),
                        "CODE_AI1_MODEL": app_conf.json.get("CODE_AI1_MODEL", "auto"),
                        "CODE_AI2": app_conf.json.get("CODE_AI2", "auto"),
                        "CODE_AI2_MODEL": app_conf.json.get("CODE_AI2_MODEL", "auto"),
                        "CODE_AI3": app_conf.json.get("CODE_AI3", "auto"),
                        "CODE_AI3_MODEL": app_conf.json.get("CODE_AI3_MODEL", "auto"),
                        "CODE_AI4": app_conf.json.get("CODE_AI4", "auto"),
                        "CODE_AI4_MODEL": app_conf.json.get("CODE_AI4_MODEL", "auto"),
                        "CODE_CLAUDE_SDK_MODEL": app_conf.json.get("CODE_CLAUDE_SDK_MODEL", "auto"),
                        "CODE_CLAUDE_CLI_MODEL": app_conf.json.get("CODE_CLAUDE_CLI_MODEL", "auto"),
                        "CODE_COPILOT_CLI_MODEL": app_conf.json.get("CODE_COPILOT_CLI_MODEL", "auto"),
                        "CODE_GEMINI_CLI_MODEL": app_conf.json.get("CODE_GEMINI_CLI_MODEL", "auto"),
                        "CODE_CODEX_CLI_MODEL": app_conf.json.get("CODE_CODEX_CLI_MODEL", "auto"),
                        "CODE_MAX_TURNS": app_conf.json.get("CODE_MAX_TURNS", 999),
                        "CODE_PLAN": app_conf.json.get("CODE_PLAN", "auto"),
                        "CODE_VERIFY": app_conf.json.get("CODE_VERIFY", "auto"),
                        "CODE_BASE_PATH": app_conf.json.get("CODE_BASE_PATH", "../"),
                    }
                    logger.debug(f"app.confからモデル設定をコピー: {socket_id}")

                self.session_states[socket_id] = {
                    "画面": session.画面状態.copy(),
                    "ボタン": session.ボタン状態.copy(),
                    "モデル設定": session.モデル設定.copy(),
                    "ソース最終更新日時": session.ソース最終更新日時
                }
            self.sessions[socket_id] = session
        else:
            session = self.sessions[socket_id]

        logger.debug(f"セッションに接続: {socket_id}")

        # 既存の同一ソケットがあれば切断
        old_conn = session.get_socket(socket_no)
        if old_conn:
            logger.debug(f"既存接続を切断: session={socket_id} socket={socket_no}")
            await old_conn.close()

        # 接続を作成
        connection = WebSocketConnection(websocket, socket_id, socket_no)
        if accept_in_connect:
            await connection.accept()
        else:
            connection.is_connected = True
        session.set_socket(socket_no, connection)

        # 初期化メッセージを送信（各ソケット共通）
        init_payload = {
            "ソケットID": socket_id,
            "ソケット番号": socket_no,
            "チャンネル": socket_no,
            "メッセージ識別": "init",
            "メッセージ内容": {}
        }
        if socket_no == -1:
            init_payload["メッセージ内容"] = {
                "画面": session.画面状態,
                "ボタン": session.ボタン状態,
                "モデル設定": session.モデル設定
            }
        await connection.send_json(init_payload)

        logger.info(f"接続登録完了: チャンネル={socket_no}, ソケットID={socket_id}")
        return socket_id

    def ensure_session(self, socket_id: Optional[str] = None, app_conf=None) -> str:
        """
        セッションを確実に作成（WebSocket未接続でも状態だけ確保）
        """
        if socket_id and socket_id in self.sessions:
            return socket_id

        socket_id = socket_id if socket_id else self.generate_socket_id()
        if socket_id in self.sessions:
            return socket_id

        session = SessionConnection(socket_id)
        if socket_id in self.session_states:
            saved_state = self.session_states[socket_id]
            session.画面状態 = saved_state.get("画面", session.画面状態)
            session.ボタン状態 = saved_state.get("ボタン", session.ボタン状態)
            session.モデル設定 = saved_state.get("モデル設定", {})
            session.ソース最終更新日時 = saved_state.get("ソース最終更新日時")
        else:
            if app_conf and hasattr(app_conf, 'json'):
                session.モデル設定 = {
                    "CHAT_AI": app_conf.json.get("CHAT_AI", "freeai"),
                    "CHAT_GEMINI_MODEL": app_conf.json.get("CHAT_GEMINI_MODEL", "gemini-3-pro-image-preview"),
                    "CHAT_FREEAI_MODEL": app_conf.json.get("CHAT_FREEAI_MODEL", "gemini-2.5-flash"),
                    "CHAT_OPENRT_MODEL": app_conf.json.get("CHAT_OPENRT_MODEL", "google/gemini-3-pro-image-preview"),
                    "LIVE_AI": app_conf.json.get("LIVE_AI", "freeai_live"),
                    "LIVE_GEMINI_MODEL": app_conf.json.get("LIVE_GEMINI_MODEL", "gemini-2.5-flash-native-audio-preview-09-2025"),
                    "LIVE_GEMINI_VOICE": app_conf.json.get("LIVE_GEMINI_VOICE", "Zephyr"),
                    "LIVE_FREEAI_MODEL": app_conf.json.get("LIVE_FREEAI_MODEL", "gemini-2.5-flash-native-audio-preview-09-2025"),
                    "LIVE_FREEAI_VOICE": app_conf.json.get("LIVE_FREEAI_VOICE", "Zephyr"),
                    "LIVE_OPENAI_MODEL": app_conf.json.get("LIVE_OPENAI_MODEL", "gpt-realtime-mini"),
                    "LIVE_OPENAI_VOICE": app_conf.json.get("LIVE_OPENAI_VOICE", "marin"),
                    "CODE_AI1": app_conf.json.get("CODE_AI1", "copilot"),
                    "CODE_AI1_MODEL": app_conf.json.get("CODE_AI1_MODEL", "auto"),
                    "CODE_AI2": app_conf.json.get("CODE_AI2", "auto"),
                    "CODE_AI2_MODEL": app_conf.json.get("CODE_AI2_MODEL", "auto"),
                    "CODE_AI3": app_conf.json.get("CODE_AI3", "auto"),
                    "CODE_AI3_MODEL": app_conf.json.get("CODE_AI3_MODEL", "auto"),
                    "CODE_AI4": app_conf.json.get("CODE_AI4", "auto"),
                    "CODE_AI4_MODEL": app_conf.json.get("CODE_AI4_MODEL", "auto"),
                    "CODE_CLAUDE_SDK_MODEL": app_conf.json.get("CODE_CLAUDE_SDK_MODEL", "auto"),
                    "CODE_CLAUDE_CLI_MODEL": app_conf.json.get("CODE_CLAUDE_CLI_MODEL", "auto"),
                    "CODE_COPILOT_CLI_MODEL": app_conf.json.get("CODE_COPILOT_CLI_MODEL", "auto"),
                    "CODE_GEMINI_CLI_MODEL": app_conf.json.get("CODE_GEMINI_CLI_MODEL", "auto"),
                    "CODE_CODEX_CLI_MODEL": app_conf.json.get("CODE_CODEX_CLI_MODEL", "auto"),
                    "CODE_MAX_TURNS": app_conf.json.get("CODE_MAX_TURNS", 999),
                    "CODE_PLAN": app_conf.json.get("CODE_PLAN", "auto"),
                    "CODE_VERIFY": app_conf.json.get("CODE_VERIFY", "auto"),
                    "CODE_BASE_PATH": app_conf.json.get("CODE_BASE_PATH", "../"),
                }
            self.session_states[socket_id] = {
                "画面": session.画面状態.copy(),
                "ボタン": session.ボタン状態.copy(),
                "モデル設定": session.モデル設定.copy(),
                "ソース最終更新日時": session.ソース最終更新日時
            }
        self.sessions[socket_id] = session
        logger.info(f"セッションを作成(ensure): {socket_id}")
        return socket_id

    def save_session_state(self, socket_id: str, 画面: dict, ボタン: dict, モデル設定: dict = None, ソース最終更新日時: Optional[str] = None):
        """セッション状態を保存"""
        state = {
            "画面": 画面.copy(),
            "ボタン": ボタン.copy()
        }
        if モデル設定 is not None:
            state["モデル設定"] = モデル設定.copy()
        if ソース最終更新日時 is not None:
            state["ソース最終更新日時"] = ソース最終更新日時

        self.session_states[socket_id] = state
        logger.debug(f"セッション状態保存: {socket_id}")

    async def disconnect(self, socket_id: str, socket_no: Optional[int] = None, keep_session: bool = True):
        """
        WebSocket接続を切断（セッション内のソケット単位）

        Args:
            socket_id: ソケットID
            keep_session: セッション状態を保持するか（デフォルト: True）
        """
        session = self.sessions.get(socket_id)
        if not session:
            return

        if keep_session:
            self.save_session_state(
                socket_id,
                session.画面状態,
                session.ボタン状態,
                session.モデル設定,
                session.ソース最終更新日時
            )

        if socket_no is None:
            await session.close()
        else:
            connection = session.get_socket(socket_no)
            if connection:
                await connection.close()
                session.set_socket(socket_no, None)

        logger.info(f"接続切断: session={socket_id} socket={socket_no} (セッション保持: {keep_session})")

    def get_session(self, socket_id: str) -> Optional[SessionConnection]:
        """セッションIDからセッションを取得"""
        return self.sessions.get(socket_id)

    def get_connection(self, socket_id: str, socket_no: int = -1) -> Optional[WebSocketConnection]:
        """セッションIDとソケット番号から接続を取得"""
        session = self.get_session(socket_id)
        if not session:
            return None
        return session.get_socket(socket_no)

    async def send_to_socket(self, socket_id: str, data: dict):
        """特定のソケットにデータを送信"""
        session = self.get_session(socket_id)
        if session:
            await session.send_json(data)
    
    async def send_to_channel(self, socket_id: str, チャンネル: int, data: dict):
        """
        特定のソケットの指定チャンネルにデータを送信
        チャンネルが登録されている場合のみ送信
        """
        session = self.get_session(socket_id)
        if session:
            await session.send_to_channel(チャンネル, data)
    
    def register_channel(self, socket_id: str, チャンネル: int):
        """チャンネルを登録"""
        session = self.get_session(socket_id)
        if session:
            session.register_channel(チャンネル)
    
    def unregister_channel(self, socket_id: str, チャンネル: int):
        """チャンネルを解除"""
        session = self.get_session(socket_id)
        if session:
            session.unregister_channel(チャンネル)

    async def broadcast(self, data: dict):
        """全ての接続にデータをブロードキャスト"""
        for session in self.sessions.values():
            await session.send_json(data)

    async def handle_message(self, socket_id: str, message: dict):
        """
        クライアントからのメッセージをチャンネル別キューに追加

        Args:
            socket_id: ソケットID
            message: 受信メッセージ
        """
        session = self.get_session(socket_id)
        if not session:
            logger.warning(f"メッセージ処理失敗: 接続が見つかりません ({socket_id})")
            return
        
        # チャンネルを取得（デフォルト: 0）
        チャンネル = message.get("チャンネル", 0)
        
        # チャンネル別キューに追加
        キュー = session.get_or_create_queue(チャンネル)
        await キュー.put(message)
        logger.debug(f"メッセージをキューに追加: チャンネル={チャンネル}, socket_id={socket_id}, キューサイズ={キュー.qsize()}")
        
        # ストリーミングプロセッサに処理を委譲
        if session.streaming_processor:
            await session.streaming_processor.handle_client_message(message)
        else:
            logger.warning(f"メッセージ処理失敗: プロセッサが見つかりません ({socket_id})")

    def get_session_count(self) -> int:
        """アクティブなセッション数を取得"""
        return len(self.sessions)

    def get_session_list(self) -> list:
        """アクティブなセッションのリストを取得"""
        return [
            {
                "ソケットID": session.socket_id,
                "is_connected": session.is_connected,
                "画面状態": session.画面状態,
                "ボタン状態": session.ボタン状態,
                "モデル設定": session.モデル設定,
                "ソース最終更新日時": session.ソース最終更新日時,
                "チャンネル登録状態": session.チャンネル登録状態,
                "チャンネル別処理中": session.チャンネル別処理中,
                "チャンネル別キューサイズ": {
                    ch: q.qsize() for ch, q in session.チャンネル別キュー.items()
                },
                "ソケット接続状態": {
                    ch: (conn.is_connected if conn else False) for ch, conn in session.sockets.items()
                }
            }
            for session in self.sessions.values()
        ]


# グローバルなWebSocketマネージャーインスタンス
AIソケット管理 = WebSocketManager()


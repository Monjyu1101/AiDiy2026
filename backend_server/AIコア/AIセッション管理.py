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
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from fastapi import WebSocket
import asyncio
import json
import os
import uuid
from log_config import get_logger
from AIコア.AIストリーミング処理 import StreamingProcessor
from AIコア.AI音声処理 import 初期化_音声データ

# ロガー取得
logger = get_logger(__name__)

def 初期モデル設定生成(app_conf) -> dict:
    if not (app_conf and hasattr(app_conf, 'json')):
        return {}

    return {
        # ChatAI設定
        "CHAT_AI_NAME": app_conf.json.get("CHAT_AI_NAME", "freeai"),
        "CHAT_GEMINI_MODEL": app_conf.json.get("CHAT_GEMINI_MODEL", "gemini-3-pro-image-preview"),
        "CHAT_FREEAI_MODEL": app_conf.json.get("CHAT_FREEAI_MODEL", "gemini-2.5-flash"),
        "CHAT_OPENRT_MODEL": app_conf.json.get("CHAT_OPENRT_MODEL", "google/gemini-3-pro-image-preview"),
        # LiveAI設定
        "LIVE_AI_NAME": app_conf.json.get("LIVE_AI_NAME", "freeai_live"),
        "LIVE_GEMINI_MODEL": app_conf.json.get("LIVE_GEMINI_MODEL", "gemini-2.5-flash-native-audio-preview-09-2025"),
        "LIVE_GEMINI_VOICE": app_conf.json.get("LIVE_GEMINI_VOICE", "Zephyr"),
        "LIVE_FREEAI_MODEL": app_conf.json.get("LIVE_FREEAI_MODEL", "gemini-2.5-flash-native-audio-preview-09-2025"),
        "LIVE_FREEAI_VOICE": app_conf.json.get("LIVE_FREEAI_VOICE", "Zephyr"),
        "LIVE_OPENAI_MODEL": app_conf.json.get("LIVE_OPENAI_MODEL", "gpt-realtime-mini"),
        "LIVE_OPENAI_VOICE": app_conf.json.get("LIVE_OPENAI_VOICE", "marin"),
        # CodeAI設定
        "CODE_AI1_NAME": app_conf.json.get("CODE_AI1_NAME", "copilot"),
        "CODE_AI1_MODEL": app_conf.json.get("CODE_AI1_MODEL", "auto"),
        "CODE_AI2_NAME": app_conf.json.get("CODE_AI2_NAME", "auto"),
        "CODE_AI2_MODEL": app_conf.json.get("CODE_AI2_MODEL", "auto"),
        "CODE_AI3_NAME": app_conf.json.get("CODE_AI3_NAME", "auto"),
        "CODE_AI3_MODEL": app_conf.json.get("CODE_AI3_MODEL", "auto"),
        "CODE_AI4_NAME": app_conf.json.get("CODE_AI4_NAME", "auto"),
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


class WebSocketConnection:
    """
    個別のWebSocket接続を管理するクラス
    セッション内のソケット(-1,0-4)単位で保持
    """

    def __init__(self, websocket: WebSocket, セッションID: str, socket_no: int):
        self.websocket = websocket
        self.セッションID = セッションID
        self.socket_no = socket_no
        self.is_connected = False

    async def accept(self):
        """WebSocket接続を受け入れる"""
        await self.websocket.accept()
        self.is_connected = True
        logger.debug(f"接続確立: session={self.セッションID} socket={self.socket_no}")

    async def send_json(self, data: dict):
        """JSONデータを送信"""
        if self.is_connected:
            try:
                await self.websocket.send_json(data)
            except Exception as e:
                logger.error(f"送信エラー (session={self.セッションID} socket={self.socket_no}): {e}")
                self.is_connected = False

    async def receive_json(self) -> Optional[dict]:
        """JSONデータを受信"""
        if self.is_connected:
            try:
                return await self.websocket.receive_json()
            except Exception as e:
                logger.error(f"受信エラー (session={self.セッションID} socket={self.socket_no}): {e}")
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
            logger.debug(f"接続クローズ: session={self.セッションID} socket={self.socket_no}")


class SessionConnection:
    """
    セッション構造体
    ソケット構造体:
    -2: 音声入力チャンネル
    -1: 共通入力チャンネル（テキスト、画像、操作）
     0: チャット出力チャンネル
     1: エージェント1出力チャンネル
     2: エージェント2出力チャンネル
     3: エージェント3出力チャンネル
     4: エージェント4出力チャンネル
    """

    def __init__(self, セッションID: str):
        self.セッションID = セッションID
        self.sockets: Dict[int, Optional[WebSocketConnection]] = {
            -2: None,
            -1: None,
            0: None,
            1: None,
            2: None,
            3: None,
            4: None
        }
        self.output_audio_paused = False
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
            -2: True,
            -1: True,
            0: False,
            1: False,
            2: False,
            3: False,
            4: False
        }

        # チャンネル別ファイルリスト: {チャンネル: [{パス: str, 時刻: datetime}, ...]}
        self.チャンネル別ファイルリスト: Dict[int, List[dict]] = {}

    def ファイル登録(self, チャンネル: int, ファイルパス: str):
        """チャンネルのファイルリストにファイルを追加"""
        if チャンネル not in self.チャンネル別ファイルリスト:
            self.チャンネル別ファイルリスト[チャンネル] = []
        self.チャンネル別ファイルリスト[チャンネル].append({
            "パス": ファイルパス,
            "時刻": datetime.now()
        })
        logger.debug(f"ファイル登録: ch={チャンネル} path={ファイルパス}")

    def 最近のファイル取得(self, チャンネル: int, 秒数: int = 60) -> List[str]:
        """指定チャンネル＋チャンネル0の最近のファイルを絶対パスで取得"""
        基準時刻 = datetime.now() - timedelta(seconds=秒数)
        結果 = []
        対象チャンネル = [チャンネル] if チャンネル == 0 else [チャンネル, 0]
        for ch in 対象チャンネル:
            for item in self.チャンネル別ファイルリスト.get(ch, []):
                if item["時刻"] >= 基準時刻:
                    パス = item["パス"]
                    if not os.path.isabs(パス):
                        パス = os.path.abspath(パス)
                    if パス not in 結果:
                        結果.append(パス)
        return 結果

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
            logger.warning(f"送信先ソケット未接続: session={self.セッションID} ch={チャンネル}")
            return
        await connection.send_json(data)

    async def send_to_channel(self, チャンネル: int, data: dict):
        # output_fileの自動追跡
        if data.get("メッセージ識別") == "output_file" and data.get("ファイル名"):
            self.ファイル登録(チャンネル, data["ファイル名"])

        既存チャンネル = data.get("チャンネル", None)
        if 既存チャンネル is not None and 既存チャンネル != チャンネル:
            logger.error(
                f"送信チャンネル不一致: send_to_channel={チャンネル}, data.チャンネル={既存チャンネル}"
            )
        data["チャンネル"] = チャンネル
        await self.send_json(data)
        logger.debug(f"チャンネル{チャンネル}に送信: {data.get('メッセージ識別', 'unknown')}")

    def register_channel(self, チャンネル: int):
        logger.info(f"チャンネル{チャンネル}登録通知: {self.セッションID}")

    def unregister_channel(self, チャンネル: int):
        logger.info(f"チャンネル{チャンネル}解除通知: {self.セッションID}")

    def is_channel_registered(self, チャンネル: int) -> bool:
        return True

    def get_or_create_queue(self, チャンネル: int) -> asyncio.Queue:
        if チャンネル not in self.チャンネル別キュー:
            self.チャンネル別キュー[チャンネル] = asyncio.Queue()
            self.チャンネル別処理中[チャンネル] = False
            logger.debug(f"チャンネル{チャンネル}のキューを作成: {self.セッションID}")
        return self.チャンネル別キュー[チャンネル]

    def is_channel_processing(self, チャンネル: int) -> bool:
        return self.チャンネル別処理中.get(チャンネル, False)

    def set_channel_processing(self, チャンネル: int, 処理中: bool):
        self.チャンネル別処理中[チャンネル] = 処理中
        logger.debug(f"チャンネル{チャンネル}の処理状態: {処理中} ({self.セッションID})")

    def update_state(self, ボタン: dict, manager=None):
        if isinstance(ボタン, dict):
            self.ボタン状態.update(ボタン)
        if manager:
            manager.save_session_state(self.セッションID, self.ボタン状態, self.モデル設定, self.ソース最終更新日時)

    def update_model_settings(self, 設定: dict, manager=None):
        self.モデル設定.update(設定)
        if manager:
            manager.save_session_state(self.セッションID, self.ボタン状態, self.モデル設定, self.ソース最終更新日時)

    async def stop_runtime_processors(self):
        """WebSocket切断後に残る実行系プロセッサを停止（セッション状態は保持）"""
        if hasattr(self, "live_processor") and self.live_processor:
            try:
                await self.live_processor.終了()
            except Exception:
                pass
        if hasattr(self, "chat_processor") and self.chat_processor:
            try:
                await self.chat_processor.終了()
            except Exception:
                pass
        if hasattr(self, "code_agent_processors") and self.code_agent_processors:
            for agent in self.code_agent_processors:
                try:
                    await agent.終了()
                except Exception:
                    pass

    async def close(self):
        """セッション全体をクローズ"""
        await self.stop_runtime_processors()
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

    def _short_sid(self, セッションID: Optional[str]) -> str:
        if not セッションID:
            return "-"
        sid = str(セッションID)
        if len(sid) <= 23:
            return sid
        return f"{sid[:10]}...{sid[-10:]}"

    def _fmt_log(self, ch: int, 内容: str, セッションID: Optional[str] = None) -> str:
        sid = self._short_sid(セッションID)
        return f"チャンネル={ch}, {内容}, セッションID={sid}"

    def セッションID生成(self) -> str:
        """新しいセッションIDを生成（プロセスIDベース）"""
        import os
        import time
        # PID + タイムスタンプ + UUIDの組み合わせで一意性を保証
        pid = os.getpid()
        timestamp = int(time.time() * 1000)
        unique_id = str(uuid.uuid4())[:8]
        セッションID = f"ws-{pid}-{timestamp}-{unique_id}"
        return セッションID

    async def connect(self, websocket: WebSocket, セッションID: Optional[str] = None, socket_no: int = -1, app_conf=None, accept_in_connect: bool = True) -> str:
        """
        WebSocket接続を登録（セッション単位）

        Args:
            websocket: WebSocket接続
            セッションID: 既存のセッションID（リロード時）。Noneの場合は新規生成
            app_conf: アプリケーション設定（新規接続時にコピー）

        Returns:
            セッションID: 使用するセッションID
        """
        # セッションID決定
        if セッションID and セッションID in self.sessions:
            logger.debug(f"既存セッション再接続: {セッションID}")
        else:
            セッションID = セッションID if セッションID else self.セッションID生成()
            logger.debug(f"新規セッション作成: {セッションID}")

        # セッション作成または取得
        if セッションID not in self.sessions:
            session = SessionConnection(セッションID)

            # セッション状態を復元または初期化
            if セッションID in self.session_states:
                saved_state = self.session_states[セッションID]
                session.ボタン状態 = saved_state.get("ボタン", session.ボタン状態)
                session.モデル設定 = saved_state.get("モデル設定", {})
                session.ソース最終更新日時 = saved_state.get("ソース最終更新日時")
                logger.debug(f"セッション状態を復元: {セッションID}")
            else:
                session.モデル設定 = 初期モデル設定生成(app_conf)
                if session.モデル設定:
                    logger.debug(f"app.confからモデル設定をコピー: {セッションID}")

                self.session_states[セッションID] = {
                    "ボタン": session.ボタン状態.copy(),
                    "モデル設定": session.モデル設定.copy(),
                    "ソース最終更新日時": session.ソース最終更新日時
                }
            self.sessions[セッションID] = session
        else:
            session = self.sessions[セッションID]

        logger.debug(f"セッションに接続: {セッションID}")

        # 既存の同一ソケットがあれば切断
        old_conn = session.get_socket(socket_no)
        if old_conn:
            logger.debug(f"既存接続を切断: session={セッションID} socket={socket_no}")
            await old_conn.close()

        # 接続を作成
        connection = WebSocketConnection(websocket, セッションID, socket_no)
        if accept_in_connect:
            await connection.accept()
        else:
            connection.is_connected = True
        session.set_socket(socket_no, connection)

        # 初期化メッセージを送信（各ソケット共通）
        init_payload = {
            "セッションID": セッションID,
            "ソケット番号": socket_no,
            "チャンネル": socket_no,
            "メッセージ識別": "init",
            "メッセージ内容": {}
        }
        if socket_no == -1:
            init_payload["メッセージ内容"] = {
                "ボタン": session.ボタン状態,
                "モデル設定": session.モデル設定
            }
        await connection.send_json(init_payload)

        logger.info(self._fmt_log(ch=socket_no, 内容="接続登録", セッションID=セッションID))
        return セッションID

    def ensure_session(self, セッションID: Optional[str] = None, app_conf=None) -> str:
        """
        セッションを確実に作成（WebSocket未接続でも状態だけ確保）
        """
        if セッションID and セッションID in self.sessions:
            return セッションID

        セッションID = セッションID if セッションID else self.セッションID生成()
        if セッションID in self.sessions:
            return セッションID

        session = SessionConnection(セッションID)
        if セッションID in self.session_states:
            saved_state = self.session_states[セッションID]
            session.ボタン状態 = saved_state.get("ボタン", session.ボタン状態)
            session.モデル設定 = saved_state.get("モデル設定", {})
            session.ソース最終更新日時 = saved_state.get("ソース最終更新日時")
        else:
            session.モデル設定 = 初期モデル設定生成(app_conf)
            self.session_states[セッションID] = {
                "ボタン": session.ボタン状態.copy(),
                "モデル設定": session.モデル設定.copy(),
                "ソース最終更新日時": session.ソース最終更新日時
            }
        self.sessions[セッションID] = session
        logger.info(f"セッションを作成(ensure): {セッションID}")
        return セッションID

    def save_session_state(self, セッションID: str, ボタン: dict, モデル設定: dict = None, ソース最終更新日時: Optional[str] = None):
        """セッション状態を保存"""
        state = {
            "ボタン": ボタン.copy()
        }
        if モデル設定 is not None:
            state["モデル設定"] = モデル設定.copy()
        if ソース最終更新日時 is not None:
            state["ソース最終更新日時"] = ソース最終更新日時

        self.session_states[セッションID] = state
        logger.debug(f"セッション状態保存: {セッションID}")

    async def disconnect(self, セッションID: str, socket_no: Optional[int] = None, keep_session: bool = True):
        """
        WebSocket接続を切断（セッション内のソケット単位）

        Args:
            セッションID: セッションID
            keep_session: セッション状態を保持するか（デフォルト: True）
        """
        session = self.sessions.get(セッションID)
        if not session:
            return

        if keep_session:
            self.save_session_state(
                セッションID,
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
            # セッションは保持しても、接続がゼロなら実行系ループは停止
            if not session.is_connected:
                await session.stop_runtime_processors()

        ch = socket_no if socket_no is not None else -99
        logger.info(self._fmt_log(ch=ch, 内容="接続切断", セッションID=セッションID))

    def get_session(self, セッションID: str) -> Optional[SessionConnection]:
        """セッションIDからセッションを取得"""
        return self.sessions.get(セッションID)

    def get_connection(self, セッションID: str, socket_no: int = -1) -> Optional[WebSocketConnection]:
        """セッションIDとソケット番号から接続を取得"""
        session = self.get_session(セッションID)
        if not session:
            return None
        return session.get_socket(socket_no)

    async def send_to_socket(self, セッションID: str, data: dict):
        """特定のソケットにデータを送信"""
        session = self.get_session(セッションID)
        if session:
            await session.send_json(data)
    
    async def send_to_channel(self, セッションID: str, チャンネル: int, data: dict):
        """
        特定のソケットの指定チャンネルにデータを送信
        チャンネルが登録されている場合のみ送信
        """
        session = self.get_session(セッションID)
        if session:
            await session.send_to_channel(チャンネル, data)
    
    def register_channel(self, セッションID: str, チャンネル: int):
        """チャンネルを登録"""
        session = self.get_session(セッションID)
        if session:
            session.register_channel(チャンネル)
    
    def unregister_channel(self, セッションID: str, チャンネル: int):
        """チャンネルを解除"""
        session = self.get_session(セッションID)
        if session:
            session.unregister_channel(チャンネル)

    async def broadcast(self, data: dict):
        """全ての接続にデータをブロードキャスト"""
        for session in self.sessions.values():
            await session.send_json(data)

    async def handle_message(self, セッションID: str, message: dict):
        """
        クライアントからのメッセージをチャンネル別キューに追加

        Args:
            セッションID: セッションID
            message: 受信メッセージ
        """
        session = self.get_session(セッションID)
        if not session:
            logger.warning(f"メッセージ処理失敗: 接続が見つかりません ({セッションID})")
            return
        
        # チャンネルを取得（デフォルト: 0）
        チャンネル = message.get("チャンネル", 0)
        
        # チャンネル別キューに追加
        キュー = session.get_or_create_queue(チャンネル)
        await キュー.put(message)
        logger.debug(f"メッセージをキューに追加: チャンネル={チャンネル}, セッションID={セッションID}, キューサイズ={キュー.qsize()}")
        
        # ストリーミングプロセッサに処理を委譲
        if session.streaming_processor:
            await session.streaming_processor.handle_client_message(message)
        else:
            logger.warning(f"メッセージ処理失敗: プロセッサが見つかりません ({セッションID})")

    def get_session_count(self) -> int:
        """アクティブなセッション数を取得"""
        return len(self.sessions)

    def get_session_list(self) -> list:
        """アクティブなセッションのリストを取得"""
        return [
            {
                "セッションID": session.セッションID,
                "is_connected": session.is_connected,
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


# グローバルなセッションマネージャーインスタンス
AIセッション管理 = WebSocketManager()

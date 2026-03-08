# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101
# -------------------------------------------------------------------------

from __future__ import annotations

import json
import queue
import threading
import time
from urllib import parse as urllib_parse

import websocket

from util import AuthSession, AvatarSettings, CoreEvent

AIコアソケット番号一覧 = ("audio", "input", "0")
AIコア再接続秒数 = 3


def AIコアWSURLを構築(settings: AvatarSettings) -> str:
    parsed = urllib_parse.urlparse(settings.auth_base_url)
    scheme = "wss" if parsed.scheme == "https" else "ws"
    host = parsed.hostname or "localhost"
    port = parsed.port or 8091
    path = urllib_parse.quote("/core/ws/AIコア", safe="/")
    return urllib_parse.urlunparse((scheme, f"{host}:{port}", path, "", "", ""))


class AIAvatarConnector:
    def __init__(
        self,
        settings: AvatarSettings,
        auth_session: AuthSession,
        event_queue: queue.Queue[CoreEvent],
    ) -> None:
        self.settings = settings
        self.auth_session = auth_session
        self.event_queue = event_queue
        self.ws_url = AIコアWSURLを構築(settings)
        self.stop_event = threading.Event()
        self.socket_lock = threading.Lock()
        self.connections: dict[str, websocket.WebSocket] = {}
        self.threads: list[threading.Thread] = []

    def 開始(self) -> None:
        for socket_no in AIコアソケット番号一覧:
            thread = threading.Thread(
                target=self._ソケットループを実行,
                args=(str(socket_no),),
                name=f"avatar-core-{socket_no}",
                daemon=True,
            )
            self.threads.append(thread)
            thread.start()

    def 停止(self) -> None:
        self.stop_event.set()
        with self.socket_lock:
            active_connections = list(self.connections.values())
            self.connections.clear()
        for connection in active_connections:
            try:
                connection.close()
            except Exception:
                pass

    def JSONを送信(self, socket_no: str, payload: dict) -> bool:
        with self.socket_lock:
            connection = self.connections.get(socket_no)
        if connection is None:
            return False
        try:
            connection.send(json.dumps(payload, ensure_ascii=False))
            return True
        except Exception as exc:
            self._イベントを積む(CoreEvent(kind="status", socket_no=socket_no, message=f"error:{self.ws_url}:{exc}"))
            return False

    def _イベントを積む(self, event: CoreEvent) -> None:
        try:
            self.event_queue.put_nowait(event)
        except queue.Full:
            pass

    def _接続を登録(self, socket_no: str, connection: websocket.WebSocket) -> None:
        with self.socket_lock:
            self.connections[socket_no] = connection

    def _接続登録を解除(self, socket_no: str, connection: websocket.WebSocket | None) -> None:
        with self.socket_lock:
            current = self.connections.get(socket_no)
            if current is connection:
                self.connections.pop(socket_no, None)

    def _ソケットループを実行(self, socket_no: str) -> None:
        reconnect_delay = AIコア再接続秒数
        while not self.stop_event.is_set():
            connection: websocket.WebSocket | None = None
            try:
                connection = websocket.create_connection(self.ws_url, timeout=10)
                connection.settimeout(1.0)
                self._接続を登録(socket_no, connection)
                self._イベントを積む(CoreEvent(kind="status", socket_no=socket_no, message=f"connected:{self.ws_url}"))

                init_message = {
                    "type": "connect",
                    "セッションID": self.auth_session.user_id,
                    "ソケット番号": socket_no,
                }
                connection.send(json.dumps(init_message, ensure_ascii=False))

                while not self.stop_event.is_set():
                    try:
                        raw_message = connection.recv()
                    except websocket.WebSocketTimeoutException:
                        continue

                    if raw_message is None:
                        raise RuntimeError("WebSocketが切断されました。")

                    if isinstance(raw_message, bytes):
                        try:
                            raw_message = raw_message.decode("utf-8")
                        except UnicodeDecodeError:
                            continue

                    try:
                        payload = json.loads(raw_message)
                    except ValueError:
                        continue

                    self._イベントを積む(CoreEvent(kind="message", socket_no=socket_no, payload=payload))
            except Exception as exc:
                if not self.stop_event.is_set():
                    self._イベントを積む(CoreEvent(kind="status", socket_no=socket_no, message=f"error:{self.ws_url}:{exc}"))
                    time.sleep(reconnect_delay)
            finally:
                self._接続登録を解除(socket_no, connection)
                if connection is not None:
                    try:
                        connection.close()
                    except Exception:
                        pass
                if not self.stop_event.is_set():
                    self._イベントを積む(CoreEvent(kind="status", socket_no=socket_no, message="disconnected"))

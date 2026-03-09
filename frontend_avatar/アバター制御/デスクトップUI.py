# -*- coding: utf-8 -*-
#
# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101
# -------------------------------------------------------------------------

from __future__ import annotations

import queue
import random
import tkinter as tk
import time
from collections import deque
from tkinter import filedialog
from pathlib import Path

from 通信制御 import AIAvatarConnector
from 画像制御 import 画像プレビューイベント, 画像送信制御
from 音声制御 import AudioOutputPlayer, MicrophoneInputStreamer
from log_config import get_logger
from util import AuthSession, AvatarSettings, CoreEvent, システムアイドル秒数を取得

from .メインパネル import アバター表示バックエンド, 表示イベントコールバック, 表示バックエンドを生成

logger = get_logger(__name__)


class DesktopAvatarApp:
    初期移動モード = "pose"
    スプライト倍率 = 5
    初期自走状態 = True
    自動発話間隔秒 = 25
    待機ポーズ間隔秒 = 6
    初期吹き出し表示 = False
    移動間隔ミリ秒 = 140
    歩行速度 = 4
    走行速度 = 7
    休止確率 = 0.28
    睡眠確率 = 0.12
    利用者操作待機秒 = 60
    あくび確率 = 0.22
    メニュー終了待機ミリ秒 = 260
    ダイアログ切替待機ミリ秒 = 160
    入力ダイアログ開始待機ミリ秒 = 60
    吹き出しキュー開始待機ミリ秒 = 5000
    吹き出し最短表示ミリ秒 = 1000
    吹き出し単独表示ミリ秒 = 10000
    ダイアログ影色 = "#07060d"
    ダイアログ背景色 = "#111019"
    ダイアログ面色 = "#1a1826"
    ダイアログ境界色 = "#3a3556"
    ダイアログ文字色 = "#f5f3ff"
    ダイアログ補助色 = "#b8b2d9"
    ダイアログ強調色 = "#667eea"
    ダイアログ入力背景色 = "#0d0c14"
    ダイアログ透過率 = 0.96
    既定メッセージ = (
        "にゃ。",
        "デスクトップ巡回中です。",
        "昔の xneko っぽく走り回ります。",
        "右クリックで動きを止められます。",
        "つかまえても、また動き出します。",
    )

    def __init__(
        self,
        settings: AvatarSettings,
        auth_session: AuthSession,
        demo_seconds: float | None = None,
        skip_core_connect: bool = False,
    ) -> None:
        self.settings = settings
        self.auth_session = auth_session
        self.demo_seconds = demo_seconds
        self.skip_core_connect = skip_core_connect
        self.sprite_mode = False
        self.is_closing = False
        self.吹き出し表示有効 = self.初期吹き出し表示

        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.drag_moved = False
        self.dragging = False
        self.roaming_enabled = self.初期自走状態 and self.sprite_mode
        self.animation_index = 0
        self.current_animation = "stand_right"
        self.state_ticks_remaining = 0
        self.human_hold_ticks = 0
        self.velocity_x = 0
        self.velocity_y = 0
        self.facing = "right"
        self.motion_job: str | None = None
        self.bubble_job: str | None = None
        self.bubble_min_job: str | None = None
        self.message_job: str | None = None
        self.pose_job: str | None = None
        self.core_job: str | None = None
        self.welcome_job: str | None = None
        self._last_message = ""
        self._last_core_message = ""
        self._core_status = "offline"
        self._welcome_text受信済み = False
        self._吹き出し取り出し開始時刻 = time.monotonic() + (self.吹き出しキュー開始待機ミリ秒 / 1000.0)
        self._吹き出し表示中 = False
        self._吹き出し最短表示経過済み = False
        self._吹き出し表示キュー: deque[tuple[str, bool]] = deque()
        self._保留中のサーバー初期設定: dict[str, object] | None = None
        self.選択入力モード = "live"
        self.入力ダイアログ表示中 = False
        self.アバター入力抑止中 = False
        self.button_state = {
            "スピーカー": True,
            "マイク": False,
            "イメージ": False,
        }
        self.model_settings: dict[str, object] = {}
        self.core_event_queue: queue.Queue[CoreEvent] = queue.Queue()
        self.image_preview_queue: queue.Queue[画像プレビューイベント] = queue.Queue(maxsize=4)
        self.core_connector: AIAvatarConnector | None = None
        self.audio_player = AudioOutputPlayer()
        self.audio_player.スピーカー有効を設定(self.button_state["スピーカー"])
        self.microphone_streamer: MicrophoneInputStreamer | None = None
        self.image_streamer: 画像送信制御 | None = None

        self.display: アバター表示バックエンド = 表示バックエンドを生成(
            settings=self.settings,
        )
        self.animations = self.display.animations
        self.current_animation = getattr(self.display, "current_animation", self.current_animation)
        self.current_frames = self.display.current_frames
        self.audio_player.lip_sync_callback = self.display.リップシンクを更新

        self.display.メニューとイベントを構築(
            auth_user_id=self.auth_session.user_id,
            callbacks=表示イベントコールバック(
                マイク切替=self.マイク切替,
                スピーカー切替=self.スピーカー切替,
                イメージ切替=self.イメージ切替,
                自走切替=self.自走切替,
                ランダム発話=self.ランダム発話,
                最新会話を表示=self.最新会話を表示,
                次のポーズ=self.次のポーズ,
                吹き出し切替=self.吹き出し切替,
                最前面切替=self.最前面切替,
                終了=self.終了,
                ドラッグ開始=self._ドラッグ開始,
                ドラッグ移動=self._ドラッグ移動,
                クリック解放=self._クリック解放,
                メニューを開く=self._メニューを開く,
                ダブルクリック=self._ダブルクリック,
            ),
        )
        self.display.イメージUI状態を設定(self.button_state["イメージ"])
        self.display.初期位置へ配置()
        self._ランダム発話を予約()
        self._コア接続を開始()

        if self.sprite_mode:
            self._次の動きを選ぶ(force_run=True)
            self._移動処理を予約()
        else:
            self._待機ポーズを予約()

        if self.skip_core_connect and self.吹き出し表示有効 and self.既定メッセージ:
            self.メッセージ表示(self.既定メッセージ[0])
        else:
            self.吹き出しを隠す()

        if self.demo_seconds and self.demo_seconds > 0:
            self.display.予約する(int(self.demo_seconds * 1000), self.終了)

    def _コア接続を開始(self) -> None:
        if self.skip_core_connect:
            return
        self.core_connector = AIAvatarConnector(self.settings, self.auth_session, self.core_event_queue)
        self.microphone_streamer = MicrophoneInputStreamer(self.auth_session, self.core_connector)
        self.image_streamer = 画像送信制御(self.auth_session.user_id, self.core_connector, self.image_preview_queue)
        self.core_connector.開始()
        self._コアイベント監視を予約()

    def _コアイベント監視を予約(self) -> None:
        if self.is_closing:
            return
        self.display.予約解除(self.core_job)
        self.core_job = self.display.予約する(250, self._コアイベントを処理)

    def _コアイベントを処理(self) -> None:
        if self.is_closing:
            return
        while True:
            try:
                event = self.core_event_queue.get_nowait()
            except queue.Empty:
                break

            bubble_message = self._コアイベントを捌く(event)
            if bubble_message:
                self._last_core_message = bubble_message
                self.メッセージ表示(bubble_message, force_visible=True)

        while True:
            try:
                preview_event = self.image_preview_queue.get_nowait()
            except queue.Empty:
                break
            self.display.プレビューを表示(preview_event.image, preview_event.source_label, flash=preview_event.flash)

        if self.core_connector is not None:
            self._コアイベント監視を予約()

    def _コアイベントを捌く(self, event: CoreEvent) -> str:
        if event.kind == "status":
            if event.message.startswith("connected:"):
                self._core_status = "connected"
                logger.info("AIコア接続: %s", event.socket_no)
            elif event.message == "disconnected":
                self._core_status = "disconnected"
                logger.warning("AIコア切断: %s", event.socket_no)
            elif event.message.startswith("error:"):
                logger.error("AIコアエラー: %s", event.message)
            return ""

        payload = event.payload or {}
        channel = str(payload.get("チャンネル", event.socket_no))
        message_type = str(payload.get("メッセージ識別") or payload.get("type") or "")
        message_text = payload.get("メッセージ内容")
        base64_audio = payload.get("ファイル名")

        if message_type == "init":
            if event.socket_no == "0":
                self._core_status = "ready"
            if event.socket_no == "input" and isinstance(message_text, dict):
                self._保留中のサーバー初期設定 = dict(message_text)
                logger.info("input/init の初期設定を保留しました。welcome_text 到着後に反映します。")
            return ""

        if not self._welcome_text受信済み:
            if channel == "0" and message_type == "welcome_text" and isinstance(message_text, str):
                self._welcome_text受信済み = True
                logger.info("welcome_text を受信しました。以後のイベント処理を開始します。")
                self._保留中のサーバー初期設定を反映()
                return self._コアメッセージを整形(message_text)
            return ""

        if message_type == "operations" and isinstance(message_text, dict):
            self._サーバーボタン状態を反映(message_text.get("ボタン"))
            return ""

        if event.socket_no == "audio":
            if message_type == "output_audio" and isinstance(base64_audio, str):
                self.audio_player.base64音声を追加(base64_audio, str(message_text or "audio/pcm"))
            elif message_type == "cancel_audio":
                self.audio_player.再生停止(clear_queue=True)
            else:
                logger.info("audio/%s を受信しました", message_type or "unknown")
            return ""

        if channel != "0":
            return ""
        if message_type not in {"welcome_text", "output_text", "recognition_output"}:
            return ""
        if not isinstance(message_text, str):
            return ""

        normalized = self._コアメッセージを整形(message_text)
        logger.info("メッセージ受信: type=%s\n%s", message_type, normalized)
        return normalized

    def _コアメッセージを整形(self, message: str) -> str:
        lines = [line.strip() for line in message.replace("\r\n", "\n").split("\n")]
        visible_lines = [line for line in lines if line]
        if not visible_lines:
            return ""
        normalized = "\n".join(visible_lines[:3])
        if len(normalized) > 180:
            normalized = normalized[:177].rstrip() + "..."
        return normalized

    def _ログ用メッセージを整形(self, message: str) -> str:
        normalized = message.replace("\r\n", "\n").replace("\n", " / ").strip()
        if len(normalized) > 120:
            return normalized[:117].rstrip() + "..."
        return normalized

    def _サーバーボタン状態を反映(
        self,
        server_state: object,
        マイクを自動開始する: bool = True,
        イメージを起動時オフにする: bool = False,
    ) -> None:
        if not isinstance(server_state, dict):
            return
        corrected = False
        if "スピーカー" in server_state:
            self.button_state["スピーカー"] = bool(server_state.get("スピーカー"))
            if not self.audio_player.スピーカー有効を設定(self.button_state["スピーカー"]):
                self.button_state["スピーカー"] = False
                corrected = True
                self.メッセージ表示("スピーカーは使えません。", force_visible=True, error=True)
            self.display.スピーカーUI状態を設定(self.button_state["スピーカー"])
        if "マイク" in server_state:
            new_microphone_state = bool(server_state.get("マイク"))
            changed = new_microphone_state != self.button_state["マイク"]
            self.button_state["マイク"] = new_microphone_state
            if changed and マイクを自動開始する:
                if not self._マイク送信を同期():
                    self.button_state["マイク"] = False
                    corrected = True
                    self.メッセージ表示("マイクは使えません。", force_visible=True, error=True)
            elif changed and new_microphone_state:
                logger.warning("サーバー初期値でマイクONを受信しましたが、自動開始はスキップしました。必要なら右クリックで再開してください。")
            self.display.マイクUI状態を設定(self.button_state["マイク"])
        if "イメージ" in server_state:
            self.button_state["イメージ"] = bool(server_state.get("イメージ"))
            if イメージを起動時オフにする and self.button_state["イメージ"]:
                self.button_state["イメージ"] = False
                corrected = True
            self.display.イメージUI状態を設定(self.button_state["イメージ"])
            self._画像送信を同期()
        if corrected:
            self._ボタン状態を送信()

    def _サーバーモデル設定を反映(self, model_settings: object) -> None:
        if not isinstance(model_settings, dict):
            return
        self.model_settings = dict(model_settings)
        if self.microphone_streamer is not None:
            self.microphone_streamer.LiveAI名を設定(str(self.model_settings.get("LIVE_AI_NAME", "")))

    def _保留中のサーバー初期設定を反映(self) -> None:
        if not isinstance(self._保留中のサーバー初期設定, dict):
            return
        logger.info("保留中のサーバー初期設定を反映します")
        initial_settings = self._保留中のサーバー初期設定
        self._保留中のサーバー初期設定 = None
        self._サーバーボタン状態を反映(
            initial_settings.get("ボタン"),
            マイクを自動開始する=True,
            イメージを起動時オフにする=True,
        )
        self._サーバーモデル設定を反映(initial_settings.get("モデル設定"))

    def _マイク送信を同期(self) -> bool:
        if self.microphone_streamer is None:
            return False
        if self.button_state["マイク"]:
            return self.microphone_streamer.開始()
        self.microphone_streamer.停止()
        return True

    def _ボタン状態を送信(self) -> None:
        if self.core_connector is None:
            return
        payload = {
            "セッションID": self.auth_session.user_id,
            "チャンネル": None,
            "メッセージ識別": "operations",
            "メッセージ内容": {
                "ボタン": {
                    "スピーカー": self.button_state["スピーカー"],
                    "マイク": self.button_state["マイク"],
                    "イメージ": self.button_state["イメージ"],
                }
            },
        }
        self.core_connector.JSONを送信("input", payload)

    def _入力テキストを送信(self, text: str, selected_mode: str) -> bool:
        if self.core_connector is None:
            self.メッセージ表示("AIコア未接続のため送信できません。", force_visible=True)
            return False

        normalized = text.strip()
        if not normalized:
            return False

        current_mode = selected_mode.lower()
        code_mode = current_mode.startswith("code")
        code_number = current_mode.replace("code", "") if code_mode else ""
        send_mode = f"Code{code_number or '1'}" if code_mode else ("Live" if current_mode == "live" else "Chat")
        payload = {
            "セッションID": self.auth_session.user_id,
            "チャンネル": "0",
            "送信モード": send_mode,
            "メッセージ識別": "input_text",
            "メッセージ内容": normalized,
            "ファイル名": None,
            "サムネイル画像": None,
        }
        if self.core_connector.JSONを送信("input", payload):
            return True

        self.メッセージ表示("テキスト送信に失敗しました。", force_visible=True)
        return False

    def マイク切替(self) -> None:
        self.button_state["マイク"] = self.display.マイクUI状態を取得()
        if not self._マイク送信を同期():
            self.button_state["マイク"] = False
            self.display.マイクUI状態を設定(False)
            self.メッセージ表示("マイクは使えません。", force_visible=True, error=True)
        self._ボタン状態を送信()

    def スピーカー切替(self) -> None:
        self.button_state["スピーカー"] = self.display.スピーカーUI状態を取得()
        if not self.audio_player.スピーカー有効を設定(self.button_state["スピーカー"]):
            self.button_state["スピーカー"] = False
            self.display.スピーカーUI状態を設定(False)
            self.メッセージ表示("スピーカーは使えません。", force_visible=True, error=True)
        self._ボタン状態を送信()

    def イメージ切替(self) -> None:
        self.display.コンテキストメニューを閉じる()
        if self.button_state["イメージ"]:
            self.button_state["イメージ"] = False
            self.display.イメージUI状態を設定(False)
            self._画像送信を同期()
            self._ボタン状態を送信()
            return
        self.button_state["イメージ"] = True
        self.display.イメージUI状態を設定(True)
        self.display.予約する(self.メニュー終了待機ミリ秒, self._イメージ開始フローを実行)

    def _イメージ開始フローを実行(self) -> None:
        if self.is_closing:
            return
        content_type = self._コンテンツ選択ダイアログを表示()
        selection = self._コンテンツ選択を確定する(content_type)
        if selection is None:
            self.button_state["イメージ"] = False
            self.display.イメージUI状態を設定(False)
            self._ボタン状態を送信()
            return
        source_type, screen_index, desktop_mode, window_handle = selection

        if not self.コンテンツ選択(
            source_type,
            screen_index=screen_index,
            desktop_mode=desktop_mode,
            window_handle=window_handle,
        ):
            self.button_state["イメージ"] = False
            self.display.イメージUI状態を設定(False)
            self.メッセージ表示("画像コンテンツを設定できませんでした。", force_visible=True)
            self._ボタン状態を送信()
            return

        self.button_state["イメージ"] = True
        self.display.イメージUI状態を設定(True)
        if not self._画像送信を同期():
            self.button_state["イメージ"] = False
            self.display.イメージUI状態を設定(False)
            self.メッセージ表示("画像送信を開始できませんでした。", force_visible=True)
        self._ボタン状態を送信()

    def _コンテンツ選択を確定する(
        self,
        content_type: str | None,
    ) -> tuple[str, int | None, str | None, int | None] | None:
        if content_type is None:
            return None
        if content_type == "file":
            return ("file", None, None, None)
        if content_type == "camera":
            return ("camera", None, None, None)
        if content_type == "desktop_screen":
            self._UI反映を待つ(self.ダイアログ切替待機ミリ秒)
            selection = self._スクリーン選択ダイアログを表示()
            if selection is None:
                return None
            return ("desktop", selection, "screen", None)
        if content_type == "desktop_window":
            self._UI反映を待つ(self.ダイアログ切替待機ミリ秒)
            selection = self._フォーム選択ダイアログを表示()
            if selection is None:
                return None
            return ("desktop", None, "window", selection)
        return None

    def _UI反映を待つ(self, delay_ms: int) -> None:
        if delay_ms <= 0:
            return
        root = self.display.root
        done = tk.BooleanVar(master=root, value=False)
        root.after(delay_ms, lambda: done.set(True))
        root.wait_variable(done)

    def _ダークダイアログを準備(
        self,
        title: str,
        on_close,
        *,
        resizable: tuple[bool, bool] = (False, False),
        枠なし: bool = True,
        タイトル行表示: bool = True,
        影表示: bool = True,
    ) -> tuple[tk.Toplevel, tk.Frame]:
        root = self.display.root
        dialog = tk.Toplevel(root)
        dialog.withdraw()
        dialog.overrideredirect(枠なし)
        dialog.transient(root)
        dialog.title(title)
        dialog.attributes("-topmost", True)
        if 枠なし:
            dialog.attributes("-alpha", self.ダイアログ透過率)
        dialog.configure(bg=self.ダイアログ影色)
        dialog.resizable(*resizable)
        dialog.lift()

        panel = tk.Frame(
            dialog,
            bg=self.ダイアログ背景色,
            highlightbackground=self.ダイアログ境界色,
            highlightthickness=1,
            bd=0,
        )
        panel.pack(padx=(0, 8) if 影表示 else 0, pady=(0, 8) if 影表示 else 0)

        if タイトル行表示:
            header = tk.Frame(panel, bg=self.ダイアログ背景色, padx=14, pady=12)
            header.pack(fill="x")
            tk.Label(
                header,
                text=title,
                bg=self.ダイアログ背景色,
                fg=self.ダイアログ文字色,
                font=("Yu Gothic UI", 11, "bold"),
                anchor="w",
            ).pack(side="left")
            tk.Button(
                header,
                text="×",
                command=on_close,
                bg=self.ダイアログ背景色,
                fg=self.ダイアログ補助色,
                activebackground=self.ダイアログ面色,
                activeforeground=self.ダイアログ文字色,
                relief="flat",
                bd=0,
                highlightthickness=0,
                font=("Yu Gothic UI", 15, "bold"),
                width=2,
                padx=8,
                pady=2,
                cursor="hand2",
            ).pack(side="right")

        body = tk.Frame(
            panel,
            bg=self.ダイアログ背景色,
            padx=14,
            pady=14 if タイトル行表示 else 10,
        )
        body.pack(fill="both", expand=True)
        dialog.protocol("WM_DELETE_WINDOW", on_close)
        dialog.bind("<Escape>", lambda _event: on_close())
        return dialog, body

    def _ダークダイアログを中央配置(self, dialog: tk.Toplevel) -> None:
        root = self.display.root
        root.update_idletasks()
        dialog.update_idletasks()
        dw = max(dialog.winfo_reqwidth(), dialog.winfo_width())
        dh = max(dialog.winfo_reqheight(), dialog.winfo_height())
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = max(0, (screen_width - dw) // 2)
        y = max(0, (screen_height - dh) // 2)
        dialog.geometry(f"+{x}+{y}")
        dialog.deiconify()
        dialog.lift()

    def _入力フォーカスを固定する(self, dialog: tk.Toplevel, focus_widget: tk.Widget) -> None:
        dialog.update_idletasks()
        dialog.deiconify()
        dialog.lift()
        dialog.wait_visibility()
        dialog.grab_set()
        dialog.focus_force()
        focus_widget.focus_force()
        focus_widget.focus_set()
        dialog.after(30, focus_widget.focus_force)
        dialog.after(60, focus_widget.focus_set)

    def _アバター入力抑止を設定(self, enabled: bool) -> None:
        self.アバター入力抑止中 = enabled
        try:
            self.display.root.attributes("-disabled", enabled)
        except tk.TclError:
            pass
        if enabled:
            self.display.root.bind("<KeyPress>", lambda _event: "break")
            self.display.root.bind("<KeyRelease>", lambda _event: "break")
        else:
            self.display.root.unbind("<KeyPress>")
            self.display.root.unbind("<KeyRelease>")

    def _ダークボタンを作成(
        self,
        parent: tk.Misc,
        text: str,
        command,
        *,
        width: int,
        primary: bool = False,
    ) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            width=width,
            command=command,
            bg=self.ダイアログ強調色 if primary else self.ダイアログ面色,
            fg="#081016" if primary else self.ダイアログ文字色,
            activebackground="#5a6fd8" if primary else "#242036",
            activeforeground="#081016" if primary else self.ダイアログ文字色,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=self.ダイアログ強調色 if primary else self.ダイアログ境界色,
            font=("Yu Gothic UI", 10, "bold"),
            padx=10,
            pady=8,
            cursor="hand2",
        )

    def _コンテンツ選択ダイアログを表示(self) -> str | None:
        result = {"value": None}

        def cancel() -> None:
            dialog.destroy()

        dialog, frame = self._ダークダイアログを準備(
            "コンテンツ選択",
            cancel,
            枠なし=False,
            タイトル行表示=False,
            影表示=False,
        )

        def choose_file() -> None:
            result["value"] = "file"
            dialog.destroy()

        def choose_camera() -> None:
            result["value"] = "camera"
            dialog.destroy()

        def choose_desktop_screen() -> None:
            result["value"] = "desktop_screen"
            dialog.destroy()

        def choose_desktop_window() -> None:
            result["value"] = "desktop_window"
            dialog.destroy()
        tk.Label(
            frame,
            text="送信するコンテンツを選択",
            bg=self.ダイアログ背景色,
            fg=self.ダイアログ補助色,
            font=("Yu Gothic UI", 10, "bold"),
        ).pack(pady=(0, 12), anchor="w")
        button_specs = [
            ("画像ファイル", choose_file),
            ("カメラキャプチャ", choose_camera),
            ("デスクトップ(スクリーン)", choose_desktop_screen),
            ("デスクトップ(フォーム)", choose_desktop_window),
            ("キャンセル", cancel),
        ]
        for index, (label, command) in enumerate(button_specs):
            self._ダークボタンを作成(frame, label, command, width=24, primary=index < 4).pack(fill="x", pady=4)

        self._ダークダイアログを中央配置(dialog)
        dialog.focus_force()
        dialog.grab_set()
        self.display.root.wait_window(dialog)
        return result["value"]

    def _スクリーン選択ダイアログを表示(self) -> int | None:
        screens = self.image_streamer.スクリーン一覧を取得() if self.image_streamer is not None else []
        if not screens:
            return None
        result = {"value": None}
        selected_var = tk.IntVar(value=screens[0].index)

        def cancel() -> None:
            dialog.destroy()

        dialog, frame = self._ダークダイアログを準備(
            "スクリーン選択",
            cancel,
            枠なし=False,
            タイトル行表示=False,
            影表示=False,
        )

        def confirm() -> None:
            result["value"] = selected_var.get()
            dialog.destroy()
        tk.Label(frame, text="スクリーンを選択", bg=self.ダイアログ背景色, fg=self.ダイアログ補助色, font=("Yu Gothic UI", 10, "bold")).pack(pady=(0, 10), anchor="w")
        for screen in screens:
            tk.Radiobutton(
                frame,
                text=screen.label,
                value=screen.index,
                variable=selected_var,
                bg=self.ダイアログ面色,
                fg=self.ダイアログ文字色,
                selectcolor=self.ダイアログ面色,
                activebackground=self.ダイアログ面色,
                activeforeground=self.ダイアログ文字色,
                highlightthickness=0,
                bd=0,
                anchor="w",
                width=34,
                padx=10,
                pady=8,
            ).pack(anchor="w")
        button_frame = tk.Frame(frame, bg=self.ダイアログ背景色)
        button_frame.pack(fill="x", pady=(10, 0))
        self._ダークボタンを作成(button_frame, "開始", confirm, width=12, primary=True).pack(side="left")
        self._ダークボタンを作成(button_frame, "キャンセル", cancel, width=12).pack(side="right")

        self._ダークダイアログを中央配置(dialog)
        dialog.focus_force()
        dialog.grab_set()
        self.display.root.wait_window(dialog)
        return result["value"]

    def _フォーム選択ダイアログを表示(self) -> int | None:
        windows = self.image_streamer.フォーム一覧を取得() if self.image_streamer is not None else []
        if not windows:
            self.メッセージ表示("選択可能なフォームが見つかりません。", force_visible=True)
            return None
        result = {"value": None}
        selected_var = tk.IntVar(value=windows[0].hwnd)

        def cancel() -> None:
            dialog.destroy()

        dialog, frame = self._ダークダイアログを準備(
            "フォーム選択",
            cancel,
            枠なし=False,
            タイトル行表示=False,
            影表示=False,
        )

        def confirm() -> None:
            selection = listbox.curselection()
            if selection:
                selected_var.set(windows[selection[0]].hwnd)
            result["value"] = selected_var.get()
            dialog.destroy()
        tk.Label(frame, text="フォームを選択", bg=self.ダイアログ背景色, fg=self.ダイアログ補助色, font=("Yu Gothic UI", 10, "bold")).pack(pady=(0, 10), anchor="w")
        list_frame = tk.Frame(frame, bg=self.ダイアログ背景色)
        list_frame.pack(fill="both", expand=True)
        listbox = tk.Listbox(
            list_frame,
            height=min(10, max(4, len(windows))),
            exportselection=False,
            width=52,
            bg=self.ダイアログ入力背景色,
            fg=self.ダイアログ文字色,
            selectbackground=self.ダイアログ強調色,
            selectforeground="#081016",
            highlightbackground=self.ダイアログ境界色,
            highlightcolor=self.ダイアログ強調色,
            relief="flat",
            bd=0,
        )
        scrollbar = tk.Scrollbar(
            list_frame,
            orient="vertical",
            command=listbox.yview,
            troughcolor=self.ダイアログ面色,
            bg=self.ダイアログ境界色,
            activebackground=self.ダイアログ強調色,
            relief="flat",
            bd=0,
        )
        listbox.configure(yscrollcommand=scrollbar.set)
        for index, window in enumerate(windows):
            listbox.insert("end", window.label)
            if index == 0:
                listbox.selection_set(0)
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        button_frame = tk.Frame(frame, bg=self.ダイアログ背景色)
        button_frame.pack(fill="x", pady=(10, 0))
        self._ダークボタンを作成(button_frame, "開始", confirm, width=12, primary=True).pack(side="left")
        self._ダークボタンを作成(button_frame, "キャンセル", cancel, width=12).pack(side="right")

        self._ダークダイアログを中央配置(dialog)
        dialog.focus_force()
        dialog.grab_set()
        self.display.root.wait_window(dialog)
        return result["value"]

    def コンテンツ選択(
        self,
        source_type: str,
        screen_index: int | None = None,
        desktop_mode: str | None = None,
        window_handle: int | None = None,
    ) -> bool:
        if self.image_streamer is None:
            return False
        file_path: Path | None = None
        if source_type == "file":
            selected_path = filedialog.askopenfilename(
                title="画像ファイルを選択",
                filetypes=[
                    ("画像ファイル", "*.png;*.jpg;*.jpeg;*.bmp;*.webp"),
                    ("すべてのファイル", "*.*"),
                ],
            )
            if not selected_path:
                return False
            file_path = Path(selected_path)
        return self.image_streamer.コンテンツ種別を設定(
            source_type,
            file_path=file_path,
            screen_index=screen_index,
            desktop_mode=desktop_mode,
            window_handle=window_handle,
        )

    def _画像送信を同期(self) -> bool:
        if self.image_streamer is None:
            return False
        if self.button_state["イメージ"]:
            return self.image_streamer.開始()
        self.image_streamer.停止()
        self.display.プレビューを隠す()
        return True

    def _ドラッグ開始(self, event: tk.Event) -> None:
        if self.入力ダイアログ表示中 or self.アバター入力抑止中:
            return
        window_x, window_y = self.display.現在位置を取得()
        self.drag_offset_x = event.x_root - window_x
        self.drag_offset_y = event.y_root - window_y
        self.dragging = True
        self.drag_moved = False

    def _ドラッグ移動(self, event: tk.Event) -> None:
        if self.入力ダイアログ表示中 or self.アバター入力抑止中:
            return
        self.drag_moved = True
        x = event.x_root - self.drag_offset_x
        y = event.y_root - self.drag_offset_y
        self.display.位置を設定(x, y)

    def _クリック解放(self, _event: tk.Event) -> None:
        if self.is_closing or self.入力ダイアログ表示中 or self.アバター入力抑止中:
            return
        was_drag = self.drag_moved
        self.dragging = False
        self.drag_moved = False
        if was_drag:
            if self.sprite_mode and self.roaming_enabled:
                self._次の動きを選ぶ(force_run=True)
        return

    def _入力ダイアログを開く(self) -> None:
        if self.is_closing or self.入力ダイアログ表示中:
            return
        self.入力ダイアログ表示中 = True
        try:
            result = self._入力ダイアログを表示()
        finally:
            self.入力ダイアログ表示中 = False
        if result is None:
            return
        text, selected_mode = result
        self.選択入力モード = selected_mode
        self._入力テキストを送信(text, selected_mode)

    def _入力ダイアログを表示(self) -> tuple[str, str] | None:
        result = {"value": None}
        mode_var = tk.StringVar(value=self.選択入力モード or "live")

        def cancel() -> None:
            dialog.destroy()

        dialog, frame = self._ダークダイアログを準備(
            "AI入力",
            cancel,
            resizable=(True, False),
            枠なし=False,
            タイトル行表示=False,
            影表示=False,
        )
        frame.configure(pady=6)
        self._アバター入力抑止を設定(True)

        text_widget = tk.Text(
            frame,
            width=34,
            height=5,
            wrap="word",
            font=("Yu Gothic UI", 10),
            bg=self.ダイアログ入力背景色,
            fg=self.ダイアログ文字色,
            insertbackground=self.ダイアログ強調色,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=self.ダイアログ境界色,
            highlightcolor=self.ダイアログ強調色,
            padx=10,
            pady=10,
        )
        text_widget.pack(fill="both", expand=True)

        mode_frame = tk.Frame(frame, bg=self.ダイアログ背景色)
        mode_frame.pack(fill="x", pady=(8, 0))
        for value, label in (
            ("chat", "Chat"),
            ("live", "Live"),
            ("code1", "Code1"),
            ("code2", "Code2"),
            ("code3", "Code3"),
            ("code4", "Code4"),
        ):
            tk.Radiobutton(
                mode_frame,
                text=label,
                value=value,
                variable=mode_var,
                bg=self.ダイアログ面色,
                fg=self.ダイアログ文字色,
                selectcolor=self.ダイアログ強調色,
                activebackground=self.ダイアログ面色,
                activeforeground=self.ダイアログ文字色,
                indicatoron=False,
                relief="flat",
                bd=0,
                highlightthickness=1,
                highlightbackground=self.ダイアログ境界色,
                font=("Yu Gothic UI", 11, "bold"),
                anchor="center",
                justify="center",
                padx=6,
                pady=1,
                height=1,
                width=6,
                cursor="hand2",
            ).pack(side="left", padx=(0, 5))

        button_frame = tk.Frame(frame, bg=self.ダイアログ背景色)
        button_frame.pack(fill="x", pady=(12, 0))

        def submit() -> None:
            input_text = text_widget.get("1.0", "end").strip()
            if not input_text:
                return
            result["value"] = (input_text, mode_var.get())
            dialog.destroy()

        self._ダークボタンを作成(button_frame, "送信", submit, width=10, primary=True).pack(side="right")
        self._ダークボタンを作成(button_frame, "キャンセル", cancel, width=10).pack(side="right", padx=(0, 8))

        def on_return(event: tk.Event) -> str | None:
            if (event.state & 0x0001) != 0:
                return None
            submit()
            return "break"

        def on_dialog_click(_event: tk.Event) -> None:
            text_widget.focus_force()

        text_widget.bind("<Control-Return>", lambda _event: (submit(), "break")[1])
        text_widget.bind("<Return>", on_return)
        dialog.bind("<Button-1>", on_dialog_click)
        frame.bind("<Button-1>", on_dialog_click)
        self._ダークダイアログを中央配置(dialog)
        self._入力フォーカスを固定する(dialog, text_widget)
        try:
            self.display.root.wait_window(dialog)
        finally:
            self._アバター入力抑止を設定(False)
        return result["value"]

    def _ダブルクリック(self, _event: tk.Event) -> None:
        if self.is_closing or self.入力ダイアログ表示中 or self.アバター入力抑止中:
            return
        self.display.予約する(self.入力ダイアログ開始待機ミリ秒, self._入力ダイアログを開く)

    def _メニューを開く(self, event: tk.Event) -> None:
        if self.is_closing or self.入力ダイアログ表示中 or self.アバター入力抑止中:
            return
        self.display.コンテキストメニューを表示(event.x_root, event.y_root)

    def _ランダム発話を予約(self) -> None:
        if self.is_closing:
            return
        self.display.予約解除(self.message_job)
        interval = max(5, self.自動発話間隔秒) * 1000
        self.message_job = self.display.予約する(interval, self._ランダム発話して再予約)

    def _ランダム発話して再予約(self) -> None:
        self.ランダム発話()
        self._ランダム発話を予約()

    def _待機ポーズを予約(self) -> None:
        if self.sprite_mode or self.is_closing or not self.current_frames:
            return
        self.display.予約解除(self.pose_job)
        interval = max(2, self.待機ポーズ間隔秒) * 1000
        self.pose_job = self.display.予約する(interval, self._ポーズを進めて再予約)

    def _ポーズを進めて再予約(self) -> None:
        self.次のポーズ()
        self._待機ポーズを予約()

    def _移動処理を予約(self) -> None:
        if not self.sprite_mode or self.is_closing:
            return
        self.display.予約解除(self.motion_job)
        self.motion_job = self.display.予約する(max(30, self.移動間隔ミリ秒), self._移動処理を進める)

    def _移動処理を進める(self) -> None:
        if not self.sprite_mode:
            return
        if self.dragging or not self.roaming_enabled:
            self._移動処理を予約()
            return

        if self._利用者操作中は待機すべき():
            self._利用者操作中状態を反映()
            self._移動処理を予約()
            return

        if self.state_ticks_remaining <= 0:
            self._次の動きを選ぶ()

        if self.velocity_x or self.velocity_y:
            self._アバターを移動()

        self.state_ticks_remaining -= 1
        self._アニメを進める()
        self._移動処理を予約()

    def _利用者操作中は待機すべき(self) -> bool:
        idle_seconds = システムアイドル秒数を取得()
        if idle_seconds is None:
            return False
        return idle_seconds < max(5, self.利用者操作待機秒)

    def _利用者操作中状態を反映(self) -> None:
        self.velocity_x = 0
        self.velocity_y = 0

        if self.human_hold_ticks > 0:
            self.human_hold_ticks -= 1
            self._アニメを進める()
            return

        if random.random() < self.あくび確率:
            self._アニメーションを切り替える(f"yawn_{self.facing}")
            self.human_hold_ticks = random.randint(4, 8)
            if random.random() < 0.18:
                self.メッセージ表示("ふぁ...")
        else:
            self._アニメーションを切り替える(f"sit_{self.facing}")
            self.human_hold_ticks = random.randint(10, 22)
        self.animation_index = 0
        self._現在フレームを反映()

    def _アバターを移動(self) -> None:
        width, height = self.display.表示サイズを取得()
        screen_width, screen_height = self.display.画面サイズを取得()
        current_x, current_y = self.display.現在位置を取得()

        x = current_x + self.velocity_x
        y = current_y + self.velocity_y
        bounced = False

        if x <= 0 or x + width >= screen_width:
            self.velocity_x *= -1
            x = max(0, min(x, screen_width - width))
            bounced = True
        if y <= 0 or y + height >= screen_height:
            self.velocity_y *= -1
            y = max(0, min(y, screen_height - height))
            bounced = True

        self.display.位置を設定(x, y)
        if bounced:
            self._次の動きを選ぶ(force_run=True)

    def _次の動きを選ぶ(self, force_run: bool = False) -> None:
        self.facing = "right" if self.velocity_x >= 0 else "left"
        self.human_hold_ticks = 0

        if force_run:
            speed = self.走行速度
            self.velocity_x = random.choice([-speed, speed])
            self.velocity_y = random.choice([-speed // 3, 0, speed // 3])
            self.facing = "right" if self.velocity_x >= 0 else "left"
            self._アニメーションを切り替える(f"run_{self.facing}")
            self.state_ticks_remaining = random.randint(18, 28)
            return

        roll = random.random()
        if roll < self.睡眠確率:
            self.velocity_x = 0
            self.velocity_y = 0
            self._アニメーションを切り替える(f"sleep_{self.facing}")
            self.state_ticks_remaining = random.randint(28, 54)
        elif roll < self.睡眠確率 + self.休止確率:
            self.velocity_x = 0
            self.velocity_y = 0
            self._アニメーションを切り替える(f"sit_{self.facing}")
            self.state_ticks_remaining = random.randint(18, 36)
        else:
            speed = self.走行速度 if random.random() < 0.35 else self.歩行速度
            self.velocity_x = random.choice([-speed, speed])
            vertical_speed = max(1, speed // 3)
            self.velocity_y = random.choice([-vertical_speed, 0, vertical_speed])
            self.facing = "right" if self.velocity_x >= 0 else "left"
            prefix = "run" if speed >= self.走行速度 else "walk"
            self._アニメーションを切り替える(f"{prefix}_{self.facing}")
            self.state_ticks_remaining = random.randint(26, 72)

    def _アニメーションを切り替える(self, animation_name: str) -> None:
        self.current_animation = animation_name
        self.current_frames = self.animations[self.current_animation]
        self.animation_index = 0
        self._現在フレームを反映()

    def _アニメを進める(self) -> None:
        if not self.current_frames:
            return
        self.animation_index = (self.animation_index + 1) % len(self.current_frames)
        self._現在フレームを反映()

    def _現在フレームを反映(self) -> None:
        self.display.現在フレームを表示(self.current_frames, self.animation_index)

    def 自走切替(self) -> None:
        self.roaming_enabled = not self.roaming_enabled
        if self.roaming_enabled:
            self._次の動きを選ぶ(force_run=True)
            return
        self.velocity_x = 0
        self.velocity_y = 0
        self._アニメーションを切り替える(f"sit_{self.facing}")

    def ランダム発話(self) -> None:
        if not self.既定メッセージ:
            return
        candidates = [message for message in self.既定メッセージ if message != self._last_message]
        pool = candidates or list(self.既定メッセージ)
        self.メッセージ表示(random.choice(pool))

    def 最新会話を表示(self) -> None:
        if self._last_core_message:
            self.メッセージ表示(self._last_core_message, force_visible=True)
            return
        self.メッセージ表示("まだ会話メッセージはありません。", force_visible=True)

    def _吹き出し最短表示を完了する(self) -> None:
        self.bubble_min_job = None
        self._吹き出し最短表示経過済み = True
        if self._吹き出し表示キュー and self._吹き出し表示中 and self.bubble_job is not None:
            self.display.予約解除(self.bubble_job)
            self.bubble_job = None
            self.吹き出しを隠す()

    def _次の吹き出しを表示する(self) -> None:
        if self.is_closing or self._吹き出し表示中 or not self._吹き出し表示キュー:
            return
        message, _error = self._吹き出し表示キュー[0]
        wait_ms = max(0, int((self._吹き出し取り出し開始時刻 - time.monotonic()) * 1000))
        if wait_ms > 0:
            if self.bubble_job is not None:
                return
            self.bubble_job = self.display.予約する(wait_ms, self._次の吹き出しを表示する)
            return
        self.bubble_job = None
        if self.is_closing or self._吹き出し表示中 or not self._吹き出し表示キュー:
            return
        message, error = self._吹き出し表示キュー.popleft()
        self._last_message = message
        self._吹き出し表示中 = True
        self._吹き出し最短表示経過済み = False
        self.display.吹き出しを表示(message, error=error)
        self.display.予約解除(self.bubble_min_job)
        self.bubble_min_job = self.display.予約する(self.吹き出し最短表示ミリ秒, self._吹き出し最短表示を完了する)
        display_ms = self.吹き出し最短表示ミリ秒 if self._吹き出し表示キュー else self.吹き出し単独表示ミリ秒
        logger.info(
            "吹き出し表示: display_ms=%s pending=%s error=%s message=%s",
            display_ms,
            len(self._吹き出し表示キュー),
            error,
            self._ログ用メッセージを整形(message),
        )
        self.bubble_job = self.display.予約する(display_ms, self.吹き出しを隠す)

    def メッセージ表示(self, message: str, force_visible: bool = False, error: bool = False) -> None:
        if self.is_closing:
            return
        if not self.吹き出し表示有効 and not force_visible:
            return
        self._吹き出し表示キュー.append((message, error))
        if self._吹き出し表示中 and self.bubble_job is not None and self._吹き出し最短表示経過済み:
            self.display.予約解除(self.bubble_job)
            self.bubble_job = None
            self.吹き出しを隠す()
            return
        self._次の吹き出しを表示する()

    def 吹き出しを隠す(self) -> None:
        if self.is_closing:
            return
        self.display.吹き出しを隠す()
        self.display.予約解除(self.bubble_min_job)
        self.bubble_min_job = None
        self.bubble_job = None
        self._吹き出し表示中 = False
        self._吹き出し最短表示経過済み = False
        self._次の吹き出しを表示する()

    def 吹き出し切替(self) -> None:
        self.吹き出し表示有効 = not self.吹き出し表示有効
        if self.吹き出し表示有効 and self._last_message:
            self.メッセージ表示(self._last_message)
        else:
            self.吹き出しを隠す()

    def 最前面切替(self) -> None:
        self.display.最前面UI状態を設定(self.display.最前面UI状態を取得())

    def 次のポーズ(self) -> None:
        if self.sprite_mode:
            cycle = [
                f"walk_{self.facing}",
                f"run_{self.facing}",
                f"sit_{self.facing}",
                f"sleep_{self.facing}",
            ]
            current_index = cycle.index(self.current_animation) if self.current_animation in cycle else 0
            self._アニメーションを切り替える(cycle[(current_index + 1) % len(cycle)])
            return
        if not self.current_frames:
            return
        self.animation_index = (self.animation_index + 1) % len(self.current_frames)
        self._現在フレームを反映()

    def 終了(self) -> None:
        if self.is_closing:
            return
        self.is_closing = True
        for job_name in ("motion_job", "bubble_job", "bubble_min_job", "message_job", "pose_job", "core_job", "welcome_job"):
            self.display.予約解除(getattr(self, job_name))
        if self.core_connector is not None:
            self.core_connector.停止()
            self.core_connector = None
        if self.microphone_streamer is not None:
            self.microphone_streamer.停止()
            self.microphone_streamer = None
        if self.image_streamer is not None:
            self.image_streamer.終了()
            self.image_streamer = None
        self.audio_player.終了()
        self.display.破棄する()

    def 実行(self) -> None:
        self.display.イベントループ開始()

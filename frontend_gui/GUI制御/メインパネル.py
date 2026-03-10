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

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol, Sequence

import tkinter as tk
from PIL import Image, ImageTk

from util import GuiSettings
from .GUI表示 import ThreeVRMViewerLauncher, ThreeVRMViewerProcess
from log_config import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class 表示イベントコールバック:
    マイク切替: Callable[[], None]
    スピーカー切替: Callable[[], None]
    イメージ切替: Callable[[], None]
    自走切替: Callable[[], None]
    ランダム発話: Callable[[], None]
    最新会話を表示: Callable[[], None]
    次のポーズ: Callable[[], None]
    吹き出し切替: Callable[[], None]
    最前面切替: Callable[[], None]
    終了: Callable[[], None]
    ドラッグ開始: Callable[[tk.Event], None]
    ドラッグ移動: Callable[[tk.Event], None]
    クリック解放: Callable[[tk.Event], None]
    メニューを開く: Callable[[tk.Event], None]
    ダブルクリック: Callable[[tk.Event], None]


class GUI表示バックエンド(Protocol):
    root: tk.Tk

    def メニューとイベントを構築(self, auth_user_id: str, callbacks: 表示イベントコールバック) -> None: ...
    def 初期位置へ配置(self) -> None: ...
    def 予約する(self, delay_ms: int, callback: Callable[[], None]) -> str: ...
    def 予約解除(self, job_id: str | None) -> None: ...
    def イベントループ開始(self) -> None: ...
    def 破棄する(self) -> None: ...
    def 現在位置を取得(self) -> tuple[int, int]: ...
    def 位置を設定(self, x: int, y: int) -> None: ...
    def 表示サイズを取得(self) -> tuple[int, int]: ...
    def 必要サイズを取得(self) -> tuple[int, int]: ...
    def 画面サイズを取得(self) -> tuple[int, int]: ...
    def 現在フレームを表示(self, frames: Sequence[ImageTk.PhotoImage], index: int) -> None: ...
    def 吹き出しを表示(self, message: str, error: bool = False) -> None: ...
    def 吹き出しを隠す(self) -> None: ...
    def コンテキストメニューを表示(self, x_root: int, y_root: int) -> None: ...
    def コンテキストメニューを閉じる(self) -> None: ...
    def プレビューを表示(self, image: Image.Image | None, label_text: str = "", flash: bool = False) -> None: ...
    def プレビューを隠す(self) -> None: ...
    def マイクUI状態を設定(self, value: bool) -> None: ...
    def マイクUI状態を取得(self) -> bool: ...
    def スピーカーUI状態を設定(self, value: bool) -> None: ...
    def スピーカーUI状態を取得(self) -> bool: ...
    def イメージUI状態を設定(self, value: bool) -> None: ...
    def イメージUI状態を取得(self) -> bool: ...
    def イメージメニュー表示を設定(self, value: bool) -> None: ...
    def 最前面UI状態を取得(self) -> bool: ...
    def 最前面UI状態を設定(self, value: bool) -> None: ...
    def リップシンクを更新(self, value: float) -> None: ...


class 三次元表示バックエンド:
    吹き出し横幅 = 300
    吹き出し内側余白 = 12
    吹き出し背景色 = "#000000"
    吹き出し通常色 = "#39ff14"
    吹き出し異常色 = "#ff5a5a"
    プレビュー下端余白 = 10
    プレビュー最大横幅比率 = 0.60
    プレビュー最大高さ比率 = 0.30
    プレビュー通常枠太さ = 1
    プレビューフラッシュ枠太さ = 3
    メニュー後実行待機ミリ秒 = 180
    プレビューフラッシュ時間ミリ秒 = 180
    タイトル高さ = 34
    タイトル文字サイズ = 13
    タイトル幅比率 = 0.8
    表示領域上部オフセット = 22
    タイトル枠間隔 = 4
    枠線外側余白 = 3
    枠線操作幅 = 6
    リサイズハンドルサイズ = 18
    メニュー背景色 = "#111019"
    メニュー面色 = "#1a1826"
    メニュー文字色 = "#f5f3ff"
    メニュー補助色 = "#b8b2d9"
    メニュー強調色 = "#667eea"
    メニュー境界色 = "#3a3556"

    def __init__(
        self,
        settings: GuiSettings,
    ) -> None:
        self.settings = settings
        self.sprite_mode = False
        self.animations: dict[str, list[ImageTk.PhotoImage]] = {}
        self.current_frames: list[ImageTk.PhotoImage] = []
        self.current_animation = "three-vrm"
        self.viewer_process: ThreeVRMViewerProcess | None = None
        self.viewer_launcher = ThreeVRMViewerLauncher(Path(__file__).resolve().parent.parent)
        self.viewer_width = max(320, self.settings.vrm_window_width)
        self.viewer_height = max(240, self.settings.vrm_window_height)
        self.frame_padding = 10
        self.content_inset = 10
        self.control_area_height = 32
        self.resize_outset = 40
        self.window_width = self.viewer_width + self.frame_padding * 2 + self.resize_outset
        self.window_height = self.viewer_height + self.frame_padding * 2 + self.control_area_height + self.表示領域上部オフセット
        self.viewer_handles_window_controls = False

        self.root = tk.Tk()
        self.root.title(settings.gui_name)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", settings.always_on_top)
        self.root.wm_attributes("-transparentcolor", "#00ff00")
        self.root.configure(bg="#00ff00")

        self.speaker_var = tk.BooleanVar(value=True)
        self.microphone_var = tk.BooleanVar(value=False)
        self.camera_var = tk.BooleanVar(value=False)
        self.topmost_var = tk.BooleanVar(value=settings.always_on_top)
        self.container: tk.Frame | None = None
        self.bubble_window: tk.Toplevel | None = None
        self.bubble_frame: tk.Frame | None = None
        self.bubble_tail: tk.Canvas | None = None
        self.bubble_label: tk.Label | None = None
        self.gui_surface: tk.Widget | None = None
        self.drag_surface: tk.Frame | None = None
        self.drag_grip: tk.Frame | None = None
        self.drag_grip_label: tk.Label | None = None
        self.drag_border_top: tk.Frame | None = None
        self.drag_border_bottom: tk.Frame | None = None
        self.drag_border_left: tk.Frame | None = None
        self.drag_border_right: tk.Frame | None = None
        self.resize_handle_top_left: tk.Frame | None = None
        self.resize_handle_top_left_label: tk.Label | None = None
        self.resize_handle: tk.Frame | None = None
        self.resize_handle_label: tk.Label | None = None
        self.control_panel: tk.Frame | None = None
        self.icon_panel: tk.Frame | None = None
        self._icon_images: dict[str, tuple] = {}
        self.mic_icon_btn: tk.Button | None = None
        self.speaker_icon_btn: tk.Button | None = None
        self.camera_icon_btn: tk.Button | None = None
        self.menu: tk.Menu | None = None
        self.preview_frame: tk.Frame | None = None
        self.preview_label: tk.Label | None = None
        self.preview_text_label: tk.Label | None = None
        self.preview_image_ref: ImageTk.PhotoImage | None = None
        self.preview_flash_job: str | None = None
        self.viewer_sync_job: str | None = None
        self.hover_watch_job: str | None = None
        self.dragging_overlay = False
        self.drag_start_root_x = 0
        self.drag_start_root_y = 0
        self.drag_start_pointer_x = 0
        self.drag_start_pointer_y = 0
        self.chrome_visible = False
        self.resizing = False
        self.resize_start_width = self.viewer_width
        self.resize_start_height = self.viewer_height
        self.resize_start_pointer_x = 0
        self.resize_start_pointer_y = 0
        self.control_button_size = self.リサイズハンドルサイズ

        self._ウィンドウアイコンを設定()
        self._UI骨組みを構築()

    def _ウィンドウアイコンを設定(self) -> None:
        base = Path(__file__).resolve().parent.parent
        icon_path: Path | None = None
        for root in (base / "GUI制御" / "assets", base / "assets"):
            if not root.exists():
                continue
            for pattern in ("AiDiy.ico", "AiDiy.png"):
                matches = sorted(root.rglob(pattern))
                if matches:
                    icon_path = matches[0]
                    break
            if icon_path:
                break
        if not icon_path:
            return
        try:
            if icon_path.suffix.lower() == ".ico":
                self.root.iconbitmap(default=str(icon_path))
            else:
                image = tk.PhotoImage(file=str(icon_path))
                self.root.iconphoto(True, image)
                self.root._icon_image = image
        except tk.TclError:
            return

    def _UI骨組みを構築(self) -> None:
        display_left = self.frame_padding + self.content_inset
        display_top = self.frame_padding + self.content_inset + self.表示領域上部オフセット
        frame_left = display_left - self.枠線外側余白
        frame_top = display_top - self.枠線外側余白
        frame_width = self.viewer_width + self.枠線外側余白 * 2
        frame_height = self.viewer_height + self.枠線外側余白 * 2
        right_panel_left = display_left + self.viewer_width + 2

        self.container = tk.Frame(self.root, bg="#00ff00", width=self.window_width, height=self.window_height, highlightthickness=0, bd=0)
        self.container.pack()
        self.container.pack_propagate(False)

        self.bubble_window = tk.Toplevel(self.root)
        self.bubble_window.overrideredirect(True)
        self.bubble_window.configure(bg="#00ff00")
        self.bubble_window.wm_attributes("-transparentcolor", "#00ff00")
        self.bubble_window.attributes("-alpha", 0.75)
        self.bubble_window.attributes("-topmost", self.settings.always_on_top)
        self.bubble_window.withdraw()
        self.bubble_frame = tk.Frame(
            self.bubble_window,
            bg=self.吹き出し背景色,
            highlightbackground=self.吹き出し通常色,
            highlightthickness=1,
            bd=0,
            padx=self.吹き出し内側余白,
            pady=8,
        )
        self.bubble_frame.pack()

        self.bubble_tail = tk.Canvas(
            self.bubble_window,
            width=40,
            height=18,
            bg="#00ff00",
            highlightthickness=0,
            bd=0,
        )
        self._吹き出ししっぽを描画する(self.吹き出し通常色)
        self.bubble_tail.pack_forget()

        self.bubble_label = tk.Label(
            self.bubble_frame,
            text="",
            justify="center",
            bg=self.吹き出し背景色,
            fg=self.吹き出し通常色,
            font=("Yu Gothic UI", 10, "bold"),
            wraplength=self.吹き出し横幅,
        )
        self.bubble_label.pack()

        surface = tk.Frame(
            self.container,
            bg="#00ff00",
            width=self.viewer_width,
            height=self.viewer_height,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
        )
        surface.place(x=display_left, y=display_top, width=self.viewer_width, height=self.viewer_height)
        # ボーダー枠は常時配置（透過色）でマウスイベントを受け取る
        # "#00ff00" は透過色。マウスオーバー時に色を付けて表示する
        _BORDER_HIDDEN = "#00ff00"
        border_top = tk.Frame(self.container, bg=_BORDER_HIDDEN, height=self.枠線操作幅, bd=0, highlightthickness=0, cursor="fleur")
        border_top.place(x=frame_left, y=frame_top, width=frame_width, height=self.枠線操作幅)
        border_bottom = tk.Frame(self.container, bg=_BORDER_HIDDEN, height=self.枠線操作幅, bd=0, highlightthickness=0, cursor="fleur")
        border_bottom.place(
            x=frame_left,
            y=display_top + self.viewer_height - self.枠線外側余白,
            width=frame_width,
            height=self.枠線操作幅,
        )
        border_left = tk.Frame(self.container, bg=_BORDER_HIDDEN, width=self.枠線操作幅, bd=0, highlightthickness=0, cursor="fleur")
        border_left.place(x=frame_left, y=frame_top, width=self.枠線操作幅, height=frame_height)
        border_right = tk.Frame(self.container, bg=_BORDER_HIDDEN, width=self.枠線操作幅, bd=0, highlightthickness=0, cursor="fleur")
        border_right.place(
            x=display_left + self.viewer_width - self.枠線外側余白,
            y=frame_top,
            width=self.枠線操作幅,
            height=frame_height,
        )
        grip = tk.Frame(
            self.container,
            bg="#8f7cff",
            width=frame_width,
            height=self.タイトル高さ,
            bd=0,
            highlightthickness=0,
            cursor="fleur",
        )
        grip.pack_propagate(False)
        grip_label = tk.Label(
            grip,
            text=self.settings.gui_name,
            bg="#8f7cff",
            fg="#ffffff",
            font=("Yu Gothic UI", self.タイトル文字サイズ, "bold"),
            bd=0,
            padx=0,
            pady=0,
            cursor="fleur",
        )
        grip_label.place(relx=0.5, rely=0.5, anchor="center")
        self.gui_surface = surface
        self.drag_surface = surface
        self.drag_grip = grip
        self.drag_grip_label = grip_label
        self.drag_border_top = border_top
        self.drag_border_bottom = border_bottom
        self.drag_border_left = border_left
        self.drag_border_right = border_right
        resize_handle = tk.Frame(
            self.container,
            bg="#8f7cff",
            width=self.リサイズハンドルサイズ,
            height=self.リサイズハンドルサイズ,
            bd=0,
            highlightthickness=0,
            cursor="size_nw_se",
        )
        resize_handle.pack_propagate(False)
        resize_label = tk.Label(
            resize_handle,
            text="◢",
            bg="#8f7cff",
            fg="#ffffff",
            font=("Yu Gothic UI", 9, "bold"),
            bd=0,
            padx=0,
            pady=0,
            cursor="size_nw_se",
        )
        resize_label.place(relx=0.5, rely=0.5, anchor="center")
        resize_handle_top_left = tk.Frame(
            self.container,
            bg="#8f7cff",
            width=self.リサイズハンドルサイズ,
            height=self.リサイズハンドルサイズ,
            bd=0,
            highlightthickness=0,
            cursor="size_nw_se",
        )
        resize_handle_top_left.pack_propagate(False)
        resize_top_left_label = tk.Label(
            resize_handle_top_left,
            text="◤",
            bg="#8f7cff",
            fg="#ffffff",
            font=("Yu Gothic UI", 9, "bold"),
            bd=0,
            padx=0,
            pady=0,
            cursor="size_nw_se",
        )
        resize_top_left_label.place(relx=0.5, rely=0.5, anchor="center")
        self.resize_handle_top_left = resize_handle_top_left
        self.resize_handle_top_left_label = resize_top_left_label
        self.resize_handle = resize_handle
        self.resize_handle_label = resize_label

        control_panel = tk.Frame(self.container, bg="#00ff00", bd=0, highlightthickness=0)
        # 初期状態では非表示（ホバーで表示）
        for label, command in (
            ("＋", lambda: self._カメラを調整する("zoom_in")),
            ("−", lambda: self._カメラを調整する("zoom_out")),
            ("▲", lambda: self._カメラを調整する("move_up")),
            ("▼", lambda: self._カメラを調整する("move_down")),
            ("◀", lambda: self._カメラを調整する("move_left")),
            ("▶", lambda: self._カメラを調整する("move_right")),
        ):
            button_slot = tk.Frame(
                control_panel,
                bg="#00ff00",
                width=self.control_button_size,
                height=self.control_button_size,
                bd=0,
                highlightthickness=0,
            )
            button_slot.pack(side="top", pady=1)
            button_slot.pack_propagate(False)
            button = tk.Button(
                button_slot,
                text=label,
                command=command,
                bg="#8f7cff",
                fg="#ffffff",
                activebackground="#b9abff",
                activeforeground="#ffffff",
                relief="flat",
                bd=0,
                highlightthickness=0,
                font=("Yu Gothic UI", 8, "bold"),
                cursor="hand2",
                padx=0,
                pady=0,
            )
            button.place(x=0, y=0, width=self.control_button_size, height=self.control_button_size)
        self.control_panel = control_panel

        self.preview_frame = tk.Frame(
            self.container,
            bg="#f7f4ec",
            highlightbackground="#404040",
            highlightthickness=self.プレビュー通常枠太さ,
            bd=0,
            padx=4,
            pady=4,
        )
        self.preview_label = tk.Label(self.preview_frame, bg="#f7f4ec", bd=0, highlightthickness=0)
        self.preview_label.pack()
        self.preview_text_label = tk.Label(self.preview_frame, text="", bg="#f7f4ec", fg="#404040", font=("Yu Gothic UI", 8, "bold"))

        if self.viewer_handles_window_controls:
            surface.configure(cursor="")
            for widget in (border_top, border_bottom, border_left, border_right, grip, resize_handle_top_left, resize_handle, control_panel):
                widget.place_forget()
            self.gui_surface = None
            self.drag_surface = None
            self.drag_grip = None
            self.drag_grip_label = None
            self.drag_border_top = None
            self.drag_border_bottom = None
            self.drag_border_left = None
            self.drag_border_right = None
            self.resize_handle_top_left = None
            self.resize_handle_top_left_label = None
            self.resize_handle = None
            self.resize_handle_label = None
            self.control_panel = None

        self._ホバー終了(None)

    def メニューとイベントを構築(self, auth_user_id: str, callbacks: 表示イベントコールバック) -> None:
        del auth_user_id
        display_top = self.frame_padding + self.content_inset + self.表示領域上部オフセット
        right_panel_left = self.frame_padding + self.content_inset + self.viewer_width + 2
        self.menu = tk.Menu(
            self.root,
            tearoff=0,
            bg=self.メニュー背景色,
            fg=self.メニュー文字色,
            activebackground=self.メニュー面色,
            activeforeground=self.メニュー文字色,
            disabledforeground=self.メニュー補助色,
            relief="flat",
            bd=1,
            activeborderwidth=0,
            selectcolor=self.メニュー強調色,
        )
        self.menu.configure(borderwidth=1)
        self.menu.add_checkbutton(label="最前面表示", variable=self.topmost_var, command=lambda: self._メニュー後に実行(callbacks.最前面切替))
        self.menu.add_separator()
        self.menu.add_command(label="最新会話", command=lambda: self._メニュー後に実行(callbacks.最新会話を表示))
        self.menu.add_separator()
        self.menu.add_command(label="終了", command=lambda: self._メニュー後に実行(callbacks.終了))

        # マイク/スピーカー/イメージ アイコンボタン（枠右上、常時表示）
        self._アイコン画像を準備する()
        icon_panel = tk.Frame(self.container, bg="#00ff00", bd=0, highlightthickness=0)
        def _mic_toggle(v=self.microphone_var, cb=callbacks.マイク切替):
            v.set(not v.get()); cb()
            self._アイコンボタン状態を更新(self.mic_icon_btn, "mic", v.get())
        def _spk_toggle(v=self.speaker_var, cb=callbacks.スピーカー切替):
            v.set(not v.get()); cb()
            self._アイコンボタン状態を更新(self.speaker_icon_btn, "spk", v.get())
        def _cam_toggle(cb=callbacks.イメージ切替):
            next_value = not self.camera_var.get()
            self.イメージUI状態を設定(next_value)
            cb()
        self.mic_icon_btn = self._アイコンボタンを作成(icon_panel, "mic", _mic_toggle)
        self.speaker_icon_btn = self._アイコンボタンを作成(icon_panel, "spk", _spk_toggle)
        self.camera_icon_btn = self._アイコンボタンを作成(icon_panel, "cam", _cam_toggle)
        self.mic_icon_btn.pack(side="top", padx=2, pady=2)
        self.speaker_icon_btn.pack(side="top", padx=2, pady=2)
        self.camera_icon_btn.pack(side="top", padx=2, pady=2)
        self.icon_panel = icon_panel
        self._アイコンボタン状態を更新(self.mic_icon_btn, "mic", self.microphone_var.get())
        self._アイコンボタン状態を更新(self.speaker_icon_btn, "spk", self.speaker_var.get())
        self._アイコンボタン状態を更新(self.camera_icon_btn, "cam", self.camera_var.get())
        icon_panel.place(
            x=right_panel_left,
            y=display_top,
            anchor="nw",
        )

        common_widgets = [
            self.root,
            self.container,
            self.drag_surface,
            self.bubble_window,
            self.bubble_frame,
            self.bubble_label,
            self.bubble_tail,
        ]
        drag_widgets = [
            self.drag_grip,
            self.drag_grip_label,
            self.drag_border_top,
            self.drag_border_bottom,
            self.drag_border_left,
            self.drag_border_right,
        ]
        double_click_widgets = [
            self.drag_surface,
            self.drag_grip,
            self.drag_grip_label,
            self.bubble_window,
            self.bubble_frame,
            self.bubble_label,
            self.bubble_tail,
        ]
        right_click_widgets = [
            self.drag_grip,
            self.drag_grip_label,
        ]

        for widget in common_widgets:
            if widget is None:
                continue
            widget.bind("<ButtonRelease-1>", callbacks.クリック解放)
            widget.bind("<Enter>", self._ホバー開始)
            widget.bind("<Leave>", self._ホバー終了)
            widget.bind("<Motion>", self._マウス移動でホバー判定, add="+")
        for widget in double_click_widgets:
            if widget is None:
                continue
            widget.bind("<Double-Button-1>", callbacks.ダブルクリック)
        for widget in right_click_widgets:
            if widget is None:
                continue
            widget.bind("<Button-3>", lambda event, cb=callbacks.メニューを開く: self._右クリックメニューイベント(event, cb))
        for widget in drag_widgets:
            if widget is None:
                continue
            widget.bind("<ButtonPress-1>", callbacks.ドラッグ開始)
            widget.bind("<B1-Motion>", callbacks.ドラッグ移動)
            widget.bind("<ButtonRelease-1>", callbacks.クリック解放)
            widget.bind("<ButtonPress-1>", self._直接ドラッグ開始, add="+")
            widget.bind("<B1-Motion>", self._直接ドラッグ移動, add="+")
            widget.bind("<ButtonRelease-1>", self._直接ドラッグ終了, add="+")
            widget.bind("<Enter>", self._ホバー開始)
            widget.bind("<Leave>", self._ホバー終了)
            widget.bind("<Motion>", self._マウス移動でホバー判定, add="+")
        if self.resize_handle is not None:
            self.resize_handle.bind("<ButtonPress-1>", self._リサイズ開始)
            self.resize_handle.bind("<B1-Motion>", self._リサイズ移動)
            self.resize_handle.bind("<ButtonRelease-1>", self._リサイズ終了)
            self.resize_handle.bind("<Enter>", self._ホバー開始)
            self.resize_handle.bind("<Leave>", self._ホバー終了)
            self.resize_handle.bind("<Motion>", self._マウス移動でホバー判定, add="+")
        if self.resize_handle_top_left is not None:
            self.resize_handle_top_left.bind("<ButtonPress-1>", self._左上リサイズ開始)
            self.resize_handle_top_left.bind("<B1-Motion>", self._左上リサイズ移動)
            self.resize_handle_top_left.bind("<ButtonRelease-1>", self._リサイズ終了)
            self.resize_handle_top_left.bind("<Enter>", self._ホバー開始)
            self.resize_handle_top_left.bind("<Leave>", self._ホバー終了)
            self.resize_handle_top_left.bind("<Motion>", self._マウス移動でホバー判定, add="+")
        if self.resize_handle_label is not None:
            self.resize_handle_label.bind("<ButtonPress-1>", self._リサイズ開始)
            self.resize_handle_label.bind("<B1-Motion>", self._リサイズ移動)
            self.resize_handle_label.bind("<ButtonRelease-1>", self._リサイズ終了)
            self.resize_handle_label.bind("<Enter>", self._ホバー開始)
            self.resize_handle_label.bind("<Leave>", self._ホバー終了)
            self.resize_handle_label.bind("<Motion>", self._マウス移動でホバー判定, add="+")
        if self.resize_handle_top_left_label is not None:
            self.resize_handle_top_left_label.bind("<ButtonPress-1>", self._左上リサイズ開始)
            self.resize_handle_top_left_label.bind("<B1-Motion>", self._左上リサイズ移動)
            self.resize_handle_top_left_label.bind("<ButtonRelease-1>", self._リサイズ終了)
            self.resize_handle_top_left_label.bind("<Enter>", self._ホバー開始)
            self.resize_handle_top_left_label.bind("<Leave>", self._ホバー終了)
            self.resize_handle_top_left_label.bind("<Motion>", self._マウス移動でホバー判定, add="+")
        if self.control_panel is not None:
            self.control_panel.bind("<Enter>", self._ホバー開始)
            self.control_panel.bind("<Leave>", self._ホバー終了)
            self.control_panel.bind("<Motion>", self._マウス移動でホバー判定, add="+")
            for child in self.control_panel.winfo_children():
                child.bind("<ButtonRelease-1>", callbacks.クリック解放)
                child.bind("<Enter>", self._ホバー開始)
                child.bind("<Leave>", self._ホバー終了)
                child.bind("<Motion>", self._マウス移動でホバー判定, add="+")
        self.root.bind("<Motion>", self._マウス移動でホバー判定, add="+")
        self.root.bind("<Leave>", self._ルート離脱でホバー解除, add="+")

    def 初期位置へ配置(self) -> None:
        display_left = self.frame_padding + self.content_inset
        display_top = self.frame_padding + self.content_inset + self.表示領域上部オフセット
        screen_width, screen_height = self.画面サイズを取得()
        position = self.settings.start_position.lower()
        if position == "top-left":
            x = self.settings.offset_x
            y = self.settings.offset_y
        elif position == "top-right":
            x = screen_width - self.window_width - self.settings.offset_x
            y = self.settings.offset_y
        elif position == "bottom-left":
            x = self.settings.offset_x
            y = screen_height - self.window_height - self.settings.offset_y
        else:
            x = screen_width - self.window_width - self.settings.offset_x
            y = screen_height - self.window_height - self.settings.offset_y
        y -= 8

        self.位置を設定(max(0, x), max(0, y))
        vrm_path = self._vrmパスを解決する()
        config = self.viewer_launcher.設定を作る(
            vrm_path=vrm_path,
            window_x=max(0, x + display_left),
            window_y=max(0, y + display_top),
            window_width=self.viewer_width,
            window_height=self.viewer_height,
            always_on_top=bool(self.topmost_var.get()),
            title=self.settings.gui_name,
        )
        self.viewer_process = self.viewer_launcher.起動する(config)
        self._viewer位置を同期する()
        self._ホバー監視を開始する()

    def _vrmパスを解決する(self) -> Path:
        configured = Path(self.settings.vrm_path)
        if not configured.is_absolute():
            configured = Path(__file__).resolve().parent.parent / configured
        if configured.exists():
            return configured
        vrm_dir = Path(__file__).resolve().parent / "vrm"
        candidates = sorted(vrm_dir.glob("*.vrm"))
        if candidates:
            return candidates[0]
        raise FileNotFoundError("VRM ファイルが見つかりません。frontend_gui/GUI制御/vrm を確認してください。")

    def 予約する(self, delay_ms: int, callback: Callable[[], None]) -> str:
        return self.root.after(delay_ms, callback)

    def 予約解除(self, job_id: str | None) -> None:
        if not job_id:
            return
        try:
            self.root.after_cancel(job_id)
        except tk.TclError:
            return

    def イベントループ開始(self) -> None:
        self.root.mainloop()

    def 破棄する(self) -> None:
        self.予約解除(self.viewer_sync_job)
        self.予約解除(self.hover_watch_job)
        if self.viewer_process is not None:
            self.viewer_process.停止する()
            self.viewer_process = None
        try:
            self.root.destroy()
        except tk.TclError:
            return

    def 現在位置を取得(self) -> tuple[int, int]:
        return self.root.winfo_x(), self.root.winfo_y()

    def 位置を設定(self, x: int, y: int) -> None:
        display_left = self.frame_padding + self.content_inset
        display_top = self.frame_padding + self.content_inset + self.表示領域上部オフセット
        self.root.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")
        self.root.update_idletasks()
        if self.viewer_process is not None:
            self.viewer_process.状態を書き込む(
                x=x + display_left,
                y=y + display_top,
                width=self.viewer_width,
                height=self.viewer_height,
            )
        self._オーバーレイを最前面へ出す()

    def _レイアウトを更新する(self) -> None:
        display_left = self.frame_padding + self.content_inset
        display_top = self.frame_padding + self.content_inset + self.表示領域上部オフセット
        frame_left = display_left - self.枠線外側余白
        frame_top = display_top - self.枠線外側余白
        frame_width = self.viewer_width + self.枠線外側余白 * 2
        frame_height = self.viewer_height + self.枠線外側余白 * 2
        title_width = max(160, int(frame_width * self.タイトル幅比率))
        title_left = frame_left + max(0, (frame_width - title_width) // 2)
        title_top = frame_top - self.タイトル高さ - self.タイトル枠間隔
        top_left_handle_left = frame_left - self.リサイズハンドルサイズ + 1
        top_left_handle_top = frame_top - self.リサイズハンドルサイズ + 1
        right_panel_left = display_left + self.viewer_width + 2
        bottom_panel_top = display_top + self.viewer_height - 4

        if self.container is not None:
            self.container.configure(width=self.window_width, height=self.window_height)
        if self.drag_surface is not None:
            self.drag_surface.place(x=display_left, y=display_top, width=self.viewer_width, height=self.viewer_height)
        if self.drag_border_top is not None:
            self.drag_border_top.place(x=frame_left, y=frame_top, width=frame_width, height=self.枠線操作幅)
        if self.drag_border_bottom is not None:
            self.drag_border_bottom.place(
                x=frame_left,
                y=display_top + self.viewer_height - self.枠線外側余白,
                width=frame_width,
                height=self.枠線操作幅,
            )
        if self.drag_border_left is not None:
            self.drag_border_left.place(x=frame_left, y=frame_top, width=self.枠線操作幅, height=frame_height)
        if self.drag_border_right is not None:
            self.drag_border_right.place(
                x=display_left + self.viewer_width - self.枠線外側余白,
                y=frame_top,
                width=self.枠線操作幅,
                height=frame_height,
            )
        if self.drag_grip is not None:
            self.drag_grip.place(
                x=title_left,
                y=title_top,
                width=title_width,
                height=self.タイトル高さ,
            )
        if self.resize_handle is not None:
            self.resize_handle.place(
                x=right_panel_left,
                y=display_top + self.viewer_height + 2,
                width=self.リサイズハンドルサイズ,
                height=self.リサイズハンドルサイズ,
            )
        if self.resize_handle_top_left is not None:
            self.resize_handle_top_left.place(
                x=top_left_handle_left,
                y=top_left_handle_top,
                width=self.リサイズハンドルサイズ,
                height=self.リサイズハンドルサイズ,
            )
        if self.control_panel is not None:
            self.control_panel.place(
                x=0,
                y=bottom_panel_top,
                anchor="sw",
            )
        if self.icon_panel is not None:
            self.icon_panel.place(
                x=right_panel_left,
                y=display_top,
                anchor="nw",
            )
        if self.bubble_window is not None and self.bubble_window.winfo_viewable():
            self._メッセージ位置を更新する()

    def _直接ドラッグ開始(self, event: tk.Event) -> str:
        self.dragging_overlay = True
        self.drag_start_root_x, self.drag_start_root_y = self.現在位置を取得()
        self.drag_start_pointer_x = event.x_root
        self.drag_start_pointer_y = event.y_root
        return "break"

    def _直接ドラッグ移動(self, event: tk.Event) -> str:
        if not self.dragging_overlay:
            return "break"
        next_x = self.drag_start_root_x + (event.x_root - self.drag_start_pointer_x)
        next_y = self.drag_start_root_y + (event.y_root - self.drag_start_pointer_y)
        self.位置を設定(next_x, next_y)
        return "break"

    def _直接ドラッグ終了(self, _event: tk.Event) -> str:
        self.dragging_overlay = False
        return "break"

    def _リサイズ開始(self, event: tk.Event) -> str:
        self.resizing = True
        self.resize_start_width = self.viewer_width
        self.resize_start_height = self.viewer_height
        self.resize_start_window_width = self.window_width
        self.resize_start_window_height = self.window_height
        self.resize_start_root_x, self.resize_start_root_y = self.現在位置を取得()
        self.resize_start_pointer_x = event.x_root
        self.resize_start_pointer_y = event.y_root
        return "break"

    def _左上リサイズ開始(self, event: tk.Event) -> str:
        self.resizing = True
        self.resize_start_width = self.viewer_width
        self.resize_start_height = self.viewer_height
        self.resize_start_window_width = self.window_width
        self.resize_start_window_height = self.window_height
        self.resize_start_root_x, self.resize_start_root_y = self.現在位置を取得()
        self.resize_start_pointer_x = event.x_root
        self.resize_start_pointer_y = event.y_root
        return "break"

    def _リサイズ移動(self, event: tk.Event) -> str:
        if not self.resizing:
            return "break"
        next_width = max(320, self.resize_start_width + (event.x_root - self.resize_start_pointer_x))
        next_height = max(240, self.resize_start_height + (event.y_root - self.resize_start_pointer_y))
        self.viewer_width = next_width
        self.viewer_height = next_height
        self.window_width = self.viewer_width + self.frame_padding * 2 + self.resize_outset
        self.window_height = self.viewer_height + self.frame_padding * 2 + self.control_area_height + self.表示領域上部オフセット
        self._レイアウトを更新する()
        self.位置を設定(self.resize_start_root_x, self.resize_start_root_y)
        return "break"

    def _左上リサイズ移動(self, event: tk.Event) -> str:
        if not self.resizing:
            return "break"
        width_delta = event.x_root - self.resize_start_pointer_x
        height_delta = event.y_root - self.resize_start_pointer_y
        next_width = max(320, self.resize_start_width - width_delta)
        next_height = max(240, self.resize_start_height - height_delta)
        width_change = next_width - self.resize_start_width
        height_change = next_height - self.resize_start_height
        self.viewer_width = next_width
        self.viewer_height = next_height
        self.window_width = self.viewer_width + self.frame_padding * 2 + self.resize_outset
        self.window_height = self.viewer_height + self.frame_padding * 2 + self.control_area_height + self.表示領域上部オフセット
        next_x = self.resize_start_root_x - width_change
        next_y = self.resize_start_root_y - height_change
        self._レイアウトを更新する()
        self.位置を設定(next_x, next_y)
        return "break"

    def _リサイズ終了(self, _event: tk.Event) -> str:
        self.resizing = False
        return "break"

    def _カメラを調整する(self, command: str) -> None:
        if self.viewer_process is None:
            return
        state = self.viewer_process.状態を読む()
        next_command_seq = int(state.get("camera_command_seq", 0)) + 1
        self.viewer_process.状態を書き込む(
            camera_command=command,
            camera_command_seq=next_command_seq,
        )

    def _オーバーレイを前面維持する(self) -> None:
        pass

    def _オーバーレイを最前面へ出す(self) -> None:
        always_on_top = bool(self.topmost_var.get())
        self.root.attributes("-topmost", always_on_top)
        if self.viewer_process is not None:
            self.viewer_process.状態を書き込む(always_on_top=always_on_top)
        if always_on_top:
            self.root.lift()
        for widget in (
            self.drag_surface,
            self.preview_frame,
            self.drag_grip,
            self.control_panel,
            self.resize_handle_top_left,
            self.resize_handle,
            self.icon_panel,
        ):
            if widget is not None:
                try:
                    widget.lift()
                except tk.TclError:
                    pass
        if self.bubble_window is not None:
            try:
                self.bubble_window.attributes("-topmost", always_on_top)
                self.bubble_window.lift()
            except tk.TclError:
                pass

    def _viewer位置を同期する(self) -> None:
        self.viewer_sync_job = None
        if self.viewer_process is None:
            return
        display_left = self.frame_padding + self.content_inset
        display_top = self.frame_padding + self.content_inset + self.表示領域上部オフセット
        root_x, root_y = self.現在位置を取得()
        self.viewer_process.状態を書き込む(
            x=root_x + display_left,
            y=root_y + display_top,
            width=self.viewer_width,
            height=self.viewer_height,
        )
        self._オーバーレイを最前面へ出す()
        self.viewer_sync_job = self.予約する(120, self._viewer位置を同期する)

    def _ホバー監視を開始する(self) -> None:
        self.予約解除(self.hover_watch_job)
        self.hover_watch_job = self.予約する(80, self._ホバー状態を監視する)

    def _ホバー状態を監視する(self) -> None:
        self.hover_watch_job = None
        try:
            pointer_x = self.root.winfo_pointerx()
            pointer_y = self.root.winfo_pointery()
        except tk.TclError:
            return
        root_x, root_y = self.現在位置を取得()
        inside = (
            root_x <= pointer_x < (root_x + self.window_width)
            and root_y <= pointer_y < (root_y + self.window_height)
        )
        if inside:
            self._ホバー開始(None)
        else:
            self._ホバー終了(None)
        self._ホバー監視を開始する()

    def _ホバー開始(self, _event: tk.Event | None) -> None:
        if self.chrome_visible:
            return
        display_left = self.frame_padding + self.content_inset
        display_top = self.frame_padding + self.content_inset + self.表示領域上部オフセット
        frame_left = display_left - self.枠線外側余白
        frame_top = display_top - self.枠線外側余白
        frame_width = self.viewer_width + self.枠線外側余白 * 2
        title_width = max(160, int(frame_width * self.タイトル幅比率))
        title_left = frame_left + max(0, (frame_width - title_width) // 2)
        title_top = frame_top - self.タイトル高さ - self.タイトル枠間隔
        top_left_handle_left = frame_left - self.リサイズハンドルサイズ + 1
        top_left_handle_top = frame_top - self.リサイズハンドルサイズ + 1
        right_panel_left = display_left + self.viewer_width + 2
        bottom_panel_top = display_top + self.viewer_height - 4

        self.chrome_visible = True
        # 枠線
        for widget in (
            self.drag_border_top,
            self.drag_border_bottom,
            self.drag_border_left,
            self.drag_border_right,
        ):
            if widget is not None:
                widget.configure(bg="#b9abff")
        # グリップ（タイトルバー）
        if self.drag_grip is not None:
            self.drag_grip.configure(bg="#8f7cff")
            self.drag_grip.place(
                x=title_left,
                y=title_top,
                width=title_width,
                height=self.タイトル高さ,
            )
        # コントロールパネル・リサイズハンドル・アイコンパネル
        if self.control_panel is not None:
            self.control_panel.place(
                x=0,
                y=bottom_panel_top,
                anchor="sw",
            )
        if self.resize_handle_top_left is not None:
            self.resize_handle_top_left.place(
                x=top_left_handle_left,
                y=top_left_handle_top,
                width=self.リサイズハンドルサイズ,
                height=self.リサイズハンドルサイズ,
            )
        if self.resize_handle is not None:
            self.resize_handle.place(
                x=right_panel_left,
                y=display_top + self.viewer_height + 2,
                width=self.リサイズハンドルサイズ,
                height=self.リサイズハンドルサイズ,
            )
        if self.icon_panel is not None:
            self.icon_panel.place(
                x=right_panel_left,
                y=display_top,
                anchor="nw",
            )

    def _ホバー終了(self, event: tk.Event | None) -> None:
        if not self.chrome_visible and event is not None:
            return
        if event is not None:
            next_widget = self.root.winfo_containing(event.x_root, event.y_root)
            hover_widgets = {
                widget
                for widget in (
                    self.drag_surface,
                    self.drag_grip,
                    self.drag_grip_label,
                    self.drag_border_top,
                    self.drag_border_bottom,
                    self.drag_border_left,
                    self.drag_border_right,
                    self.bubble_frame,
                    self.bubble_label,
                    self.bubble_tail,
                    self.control_panel,
                    self.resize_handle_top_left,
                    self.resize_handle_top_left_label,
                    self.resize_handle,
                    self.resize_handle_label,
                    self.icon_panel,
                    self.mic_icon_btn,
                    self.speaker_icon_btn,
                    self.camera_icon_btn,
                )
                if widget is not None
            }
            # 子ウィジェット間の移動は無視（ボタン上でも消えないように）
            if next_widget is not None and (next_widget in hover_widgets or next_widget.master in hover_widgets):
                return

        self.chrome_visible = False
        # 枠線を透明に
        for widget in (
            self.drag_border_top,
            self.drag_border_bottom,
            self.drag_border_left,
            self.drag_border_right,
        ):
            if widget is not None:
                widget.configure(bg="#00ff00")

        # グリップ・コントロール・リサイズ・アイコンパネルを隠す
        if self.drag_grip is not None:
            self.drag_grip.place_forget()
        if self.control_panel is not None:
            self.control_panel.place_forget()
        if self.resize_handle_top_left is not None:
            self.resize_handle_top_left.place_forget()
        if self.resize_handle is not None:
            self.resize_handle.place_forget()
        if self.icon_panel is not None:
            self.icon_panel.place_forget()

    def _マウス移動でホバー判定(self, event: tk.Event) -> None:
        self._ホバー開始(event)

    def _ルート離脱でホバー解除(self, event: tk.Event) -> None:
        self._ホバー終了(event)


    def 表示サイズを取得(self) -> tuple[int, int]:
        return self.window_width, self.window_height

    def 必要サイズを取得(self) -> tuple[int, int]:
        return self.window_width, self.window_height

    def 画面サイズを取得(self) -> tuple[int, int]:
        return self.root.winfo_screenwidth(), self.root.winfo_screenheight()

    def 現在フレームを表示(self, frames: Sequence[ImageTk.PhotoImage], index: int) -> None:
        del frames, index

    def _吹き出ししっぽを描画する(self, line_color: str) -> None:
        if self.bubble_tail is None:
            return
        self.bubble_tail.delete("all")
        self.bubble_tail.create_oval(4, 8, 12, 16, fill=self.吹き出し背景色, outline=line_color, width=1)
        self.bubble_tail.create_oval(13, 4, 25, 16, fill=self.吹き出し背景色, outline=line_color, width=1)
        self.bubble_tail.create_oval(24, 1, 39, 17, fill=self.吹き出し背景色, outline=line_color, width=1)

    def _吹き出し配色を設定する(self, error: bool) -> None:
        line_color = self.吹き出し異常色 if error else self.吹き出し通常色
        if self.bubble_frame is not None:
            self.bubble_frame.configure(bg=self.吹き出し背景色, highlightbackground=line_color)
        if self.bubble_label is not None:
            self.bubble_label.configure(bg=self.吹き出し背景色, fg=line_color)
        self._吹き出ししっぽを描画する(line_color)

    def 吹き出しを表示(self, message: str, error: bool = False) -> None:
        if self.bubble_label is None or self.bubble_window is None:
            return
        h_scale = self.viewer_width / 320
        v_scale = self.viewer_height / 320
        bubble_total_width = max(140, int(self.吹き出し横幅 * h_scale))
        bubble_width = max(100, bubble_total_width - self.吹き出し内側余白 * 2)
        font_size = max(8, round(10 * math.sqrt(h_scale * v_scale)))
        self._吹き出し配色を設定する(error)
        self.bubble_label.configure(text=message, wraplength=bubble_width, font=("Yu Gothic UI", font_size, "bold"))
        self._メッセージ位置を更新する()
        self.bubble_window.deiconify()
        self._オーバーレイを最前面へ出す()
        self.root.update_idletasks()

    def _メッセージ位置を更新する(self) -> None:
        if self.bubble_window is None or self.bubble_frame is None:
            return
        display_left = self.frame_padding + self.content_inset
        display_top = self.frame_padding + self.content_inset + self.表示領域上部オフセット
        self.root.update_idletasks()
        bubble_width = self.bubble_frame.winfo_reqwidth()
        bubble_height = self.bubble_frame.winfo_reqheight()
        x = display_left + max(0, (self.viewer_width - bubble_width) // 2)
        desired_y = display_top + int(self.viewer_height * 0.70)
        max_y = display_top + max(0, self.viewer_height - bubble_height - 8)
        y = min(desired_y, max_y)
        root_x, root_y = self.現在位置を取得()
        self.bubble_window.geometry(f"{bubble_width}x{bubble_height}+{root_x + x}+{root_y + y}")

    def 吹き出しを隠す(self) -> None:
        if self.bubble_window is None:
            return
        self.bubble_window.withdraw()

    def コンテキストメニューを表示(self, x_root: int, y_root: int) -> None:
        if self.menu is None:
            return
        try:
            self._オーバーレイを最前面へ出す()
            self.root.update_idletasks()
            self.menu.tk_popup(x_root, y_root + self.タイトル高さ + 10)
        except tk.TclError:
            return
        finally:
            try:
                self.menu.grab_release()
            except tk.TclError:
                pass

    def コンテキストメニューを閉じる(self) -> None:
        if self.menu is None:
            return
        try:
            self.menu.unpost()
            self.menu.grab_release()
        except tk.TclError:
            return

    def _メニュー後に実行(self, callback: Callable[[], None]) -> None:
        self.コンテキストメニューを閉じる()
        self.root.after(self.メニュー後実行待機ミリ秒, callback)

    def _右クリックメニューイベント(self, event: tk.Event, callback: Callable[[tk.Event], None]) -> str:
        callback(event)
        return "break"

    _ICON_STATE_MAP: dict[str, dict] = {
        "mic": {False: ("dark",  "#ffffff", "#ff4444"), True:  ("light", "#ff4444", "#ff4444")},
        "spk": {False: ("dark",  "#ffffff", "#00bfff"), True:  ("dark",  "#00bfff", "#00bfff")},
        "cam": {False: ("dark",  "#888888", "#2e7d32"), True:  ("light", "#1f8f4c", "#6dff9f")},
    }

    def _アイコン画像を準備する(self) -> None:
        from pathlib import Path as _Path
        icons_dir = _Path(__file__).resolve().parent.parent / "_icons"
        size = 32
        for key, filename in [("mic", "microphone.png"), ("spk", "speaker.png"), ("cam", "camera.png")]:
            p = icons_dir / filename
            if not p.exists():
                self._icon_images[key] = (None, None)
                continue
            img = Image.open(p).convert("RGBA").resize((size, size), Image.LANCZOS)
            _r, _g, _b, a = img.split()
            zero = Image.new("L", (size, size), 0)
            full = Image.new("L", (size, size), 255)
            dark_img  = Image.merge("RGBA", [zero, zero, zero, a])
            light_img = Image.merge("RGBA", [full, full, full, a])
            self._icon_images[key] = (
                ImageTk.PhotoImage(dark_img),
                ImageTk.PhotoImage(light_img),
            )

    def _アイコンボタンを作成(self, parent: tk.Widget, key: str, command: Callable[[], None]) -> tk.Button:
        _, bg, hl = self._ICON_STATE_MAP[key][False]
        dark_img, _ = self._icon_images.get(key, (None, None))
        return tk.Button(
            parent,
            text="" if dark_img else key.upper(),
            image=dark_img,
            command=command,
            bg=bg,
            activebackground=bg,
            relief="flat",
            bd=0,
            highlightthickness=2,
            highlightbackground=hl,
            cursor="hand2",
            padx=2,
            pady=2,
        )

    def _アイコンボタン状態を更新(self, btn: "tk.Button | None", key: str, active: bool) -> None:
        if btn is None:
            return
        icon_type, bg, hl = self._ICON_STATE_MAP[key][active]
        dark_img, light_img = self._icon_images.get(key, (None, None))
        img = light_img if icon_type == "light" else dark_img
        kw: dict = {"bg": bg, "activebackground": bg, "highlightbackground": hl}
        if img is not None:
            kw["image"] = img
        btn.configure(**kw)

    def プレビューを表示(self, image: Image.Image | None, label_text: str = "", flash: bool = False) -> None:
        if self.preview_frame is None or self.preview_label is None or self.preview_text_label is None:
            return
        if image is None:
            self.プレビューを隠す()
            return
        display_left = self.frame_padding + self.content_inset
        display_top = self.frame_padding + self.content_inset + self.表示領域上部オフセット
        preview = image.copy()
        max_width = max(180, int(self.viewer_width * self.プレビュー最大横幅比率))
        max_height = max(96, int(self.viewer_height * self.プレビュー最大高さ比率))
        preview.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(preview)
        self.preview_image_ref = photo
        self.preview_label.configure(image=photo)
        self.preview_text_label.configure(text="")
        self.preview_frame.place(
            x=display_left + (self.viewer_width // 2),
            y=display_top + self.viewer_height - self.プレビュー下端余白,
            anchor="s",
        )
        if flash:
            self._プレビューをフラッシュする()
        self.root.update_idletasks()

    def プレビューを隠す(self) -> None:
        if self.preview_frame is None:
            return
        self.preview_frame.place_forget()

    def _プレビューをフラッシュする(self) -> None:
        if self.preview_frame is None:
            return
        self.preview_frame.configure(
            bg="#ffe8e8",
            highlightbackground="#d93025",
            highlightthickness=self.プレビューフラッシュ枠太さ,
        )
        if self.preview_label is not None:
            self.preview_label.configure(bg="#ffe8e8")
        if self.preview_text_label is not None:
            self.preview_text_label.configure(bg="#ffe8e8")
        self.予約解除(self.preview_flash_job)
        self.preview_flash_job = self.予約する(self.プレビューフラッシュ時間ミリ秒, self._プレビューの見た目を戻す)

    def _プレビューの見た目を戻す(self) -> None:
        self.preview_flash_job = None
        if self.preview_frame is not None:
            self.preview_frame.configure(
                bg="#f7f4ec",
                highlightbackground="#404040",
                highlightthickness=self.プレビュー通常枠太さ,
            )
        if self.preview_label is not None:
            self.preview_label.configure(bg="#f7f4ec")
        if self.preview_text_label is not None:
            self.preview_text_label.configure(bg="#f7f4ec")

    def マイクUI状態を設定(self, value: bool) -> None:
        self.microphone_var.set(value)
        self._アイコンボタン状態を更新(self.mic_icon_btn, "mic", value)

    def マイクUI状態を取得(self) -> bool:
        return bool(self.microphone_var.get())

    def スピーカーUI状態を設定(self, value: bool) -> None:
        self.speaker_var.set(value)
        self._アイコンボタン状態を更新(self.speaker_icon_btn, "spk", value)

    def スピーカーUI状態を取得(self) -> bool:
        return bool(self.speaker_var.get())

    def イメージUI状態を設定(self, value: bool) -> None:
        self.camera_var.set(value)
        self._アイコンボタン状態を更新(self.camera_icon_btn, "cam", value)

    def イメージUI状態を取得(self) -> bool:
        return bool(self.camera_var.get())

    def イメージメニュー表示を設定(self, value: bool) -> None:
        self.イメージUI状態を設定(value)

    def 最前面UI状態を取得(self) -> bool:
        return bool(self.topmost_var.get())

    def 最前面UI状態を設定(self, value: bool) -> None:
        self.topmost_var.set(value)
        self._オーバーレイを最前面へ出す()

    def リップシンクを更新(self, value: float) -> None:
        if self.viewer_process is None:
            return
        self.viewer_process.状態を書き込む(lip_sync=value)


def 表示バックエンドを生成(
    settings: GuiSettings,
) -> GUI表示バックエンド:
    return 三次元表示バックエンド(settings=settings)

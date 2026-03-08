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

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol, Sequence

import tkinter as tk
from PIL import Image, ImageTk

from util import AvatarSettings
from .vrm_viewer import ThreeVRMViewerLauncher, ThreeVRMViewerProcess
from .表示画像 import xneko風フレームを構築, 安定ポーズフレームを構築


@dataclass(slots=True)
class 表示イベントコールバック:
    マイク切替: Callable[[], None]
    スピーカー切替: Callable[[], None]
    カメラ切替: Callable[[], None]
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


class アバター表示バックエンド(Protocol):
    root: tk.Tk
    sprite_mode: bool
    animations: dict[str, list[ImageTk.PhotoImage]]
    current_frames: list[ImageTk.PhotoImage]

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
    def 吹き出しを表示(self, message: str) -> None: ...
    def 吹き出しを隠す(self) -> None: ...
    def コンテキストメニューを表示(self, x_root: int, y_root: int) -> None: ...
    def コンテキストメニューを閉じる(self) -> None: ...
    def プレビューを表示(self, image: Image.Image | None, label_text: str = "", flash: bool = False) -> None: ...
    def プレビューを隠す(self) -> None: ...
    def マイクUI状態を設定(self, value: bool) -> None: ...
    def マイクUI状態を取得(self) -> bool: ...
    def スピーカーUI状態を設定(self, value: bool) -> None: ...
    def スピーカーUI状態を取得(self) -> bool: ...
    def カメラUI状態を取得(self) -> bool: ...
    def カメラメニュー表示を設定(self, value: bool) -> None: ...
    def 最前面UI状態を取得(self) -> bool: ...
    def 最前面UI状態を設定(self, value: bool) -> None: ...
    def リップシンクを更新(self, value: float) -> None: ...


class 二次元表示バックエンド:
    吹き出し横幅 = 300
    メニュー後実行待機ミリ秒 = 180
    プレビューフラッシュ時間ミリ秒 = 180
    メニュー背景色 = "#111019"
    メニュー面色 = "#1a1826"
    メニュー文字色 = "#f5f3ff"
    メニュー補助色 = "#b8b2d9"
    メニュー強調色 = "#667eea"
    メニュー境界色 = "#3a3556"

    def __init__(
        self,
        settings: AvatarSettings,
        pose_paths: Sequence[Path],
        icon_path: Path | None,
        sprite_mode: bool,
        sprite_scale: int,
    ) -> None:
        self.settings = settings
        self.pose_paths = list(pose_paths)
        self.icon_path = icon_path
        self.sprite_mode = sprite_mode
        self.sprite_scale = sprite_scale

        if not self.sprite_mode and not self.pose_paths:
            raise FileNotFoundError("アバター画像が見つかりません。")

        self.root = tk.Tk()
        self.root.title(settings.avatar_name)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", settings.always_on_top)
        self.root.wm_attributes("-transparentcolor", "#00ff00")
        self.root.configure(bg="#00ff00")

        self.animations: dict[str, list[ImageTk.PhotoImage]] = {}
        self.current_animation = "stand_right"
        self.current_frames: list[ImageTk.PhotoImage] = []
        self.animation_index = 0

        self.speaker_var = tk.BooleanVar(value=True)
        self.microphone_var = tk.BooleanVar(value=False)
        self.camera_var = tk.BooleanVar(value=False)
        self.topmost_var = tk.BooleanVar(value=settings.always_on_top)
        self.container: tk.Frame | None = None
        self.bubble_shell: tk.Frame | None = None
        self.bubble_frame: tk.Frame | None = None
        self.bubble_tail: tk.Canvas | None = None
        self.bubble_label: tk.Label | None = None
        self.avatar_label: tk.Label | None = None
        self.menu: tk.Menu | None = None
        self.preview_frame: tk.Frame | None = None
        self.preview_label: tk.Label | None = None
        self.preview_text_label: tk.Label | None = None
        self.preview_image_ref: ImageTk.PhotoImage | None = None
        self.preview_flash_job: str | None = None

        self._ウィンドウアイコンを設定()
        self._画像を読み込む()
        self._UI骨組みを構築()

    def _ウィンドウアイコンを設定(self) -> None:
        if not self.icon_path:
            return
        try:
            if self.icon_path.suffix.lower() == ".ico":
                self.root.iconbitmap(default=str(self.icon_path))
            else:
                image = tk.PhotoImage(file=str(self.icon_path))
                self.root.iconphoto(True, image)
                self.root._icon_image = image
        except tk.TclError:
            return

    def _画像を読み込む(self) -> None:
        if self.sprite_mode:
            frames = xneko風フレームを構築(max(2, self.sprite_scale))
            self.animations = {
                name: [ImageTk.PhotoImage(frame) for frame in images]
                for name, images in frames.items()
            }
            self.current_frames = self.animations[self.current_animation]
            return

        pose_frames: list[ImageTk.PhotoImage] = []
        for pose_image in 安定ポーズフレームを構築(self.pose_paths, self.settings.scale):
            pose_frames.append(ImageTk.PhotoImage(pose_image))
        if not pose_frames:
            raise FileNotFoundError("利用可能なアバター画像を読み込めませんでした。")
        self.animations = {"pose": pose_frames}
        self.current_animation = "pose"
        self.current_frames = pose_frames

    def _UI骨組みを構築(self) -> None:
        self.container = tk.Frame(self.root, bg="#00ff00", highlightthickness=0, bd=0)
        self.container.pack()

        self.bubble_shell = tk.Frame(self.container, bg="#00ff00", highlightthickness=0, bd=0)
        self.bubble_frame = tk.Frame(
            self.bubble_shell,
            bg="#fffdf5",
            highlightbackground="#404040",
            highlightthickness=1,
            bd=0,
            padx=12,
            pady=10,
        )
        self.bubble_frame.pack(padx=6, pady=(8, 0))

        self.bubble_tail = tk.Canvas(
            self.bubble_shell,
            width=40,
            height=18,
            bg="#00ff00",
            highlightthickness=0,
            bd=0,
        )
        self.bubble_tail.pack(anchor="w", padx=24, pady=(0, 4))
        self.bubble_tail.create_oval(
            4,
            8,
            12,
            16,
            fill="#fffdf5",
            outline="#404040",
            width=1,
        )
        self.bubble_tail.create_oval(
            13,
            4,
            25,
            16,
            fill="#fffdf5",
            outline="#404040",
            width=1,
        )
        self.bubble_tail.create_oval(
            24,
            1,
            39,
            17,
            fill="#fffdf5",
            outline="#404040",
            width=1,
        )

        self.bubble_label = tk.Label(
            self.bubble_frame,
            text="",
            justify="left",
            bg="#fffdf5",
            fg="#202020",
            font=("Yu Gothic UI", 10, "bold"),
            wraplength=self.吹き出し横幅,
        )
        self.bubble_label.pack()

        self.avatar_label = tk.Label(
            self.container,
            image=self.current_frames[self.animation_index],
            bg="#00ff00",
            bd=0,
            highlightthickness=0,
            cursor="hand2",
        )
        self.avatar_label.pack(padx=8, pady=(0, 8))

        self.preview_frame = tk.Frame(
            self.container,
            bg="#f7f4ec",
            highlightbackground="#404040",
            highlightthickness=1,
            bd=0,
            padx=4,
            pady=4,
        )
        self.preview_label = tk.Label(
            self.preview_frame,
            bg="#f7f4ec",
            bd=0,
            highlightthickness=0,
        )
        self.preview_label.pack()
        self.preview_text_label = tk.Label(
            self.preview_frame,
            text="",
            bg="#f7f4ec",
            fg="#404040",
            font=("Yu Gothic UI", 8, "bold"),
        )
        self.preview_text_label.pack(pady=(2, 0))

    def メニューとイベントを構築(self, auth_user_id: str, callbacks: 表示イベントコールバック) -> None:
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
        self.menu.add_checkbutton(label="マイク", variable=self.microphone_var, command=lambda: self._メニュー後に実行(callbacks.マイク切替))
        self.menu.add_checkbutton(label="スピーカー", variable=self.speaker_var, command=lambda: self._メニュー後に実行(callbacks.スピーカー切替))
        self.menu.add_checkbutton(label="カメラ", variable=self.camera_var, command=lambda: self._メニュー後に実行(callbacks.カメラ切替))
        self.menu.add_checkbutton(label="最前面表示", variable=self.topmost_var, command=lambda: self._メニュー後に実行(callbacks.最前面切替))
        self.menu.add_separator()
        if self.sprite_mode:
            self.menu.add_command(label="自走切替", command=lambda: self._メニュー後に実行(callbacks.自走切替))
        self.menu.add_command(label="最新会話", command=lambda: self._メニュー後に実行(callbacks.最新会話を表示))
        self.menu.add_separator()
        self.menu.add_command(label="終了", command=lambda: self._メニュー後に実行(callbacks.終了))

        widgets = [self.root, self.container, self.avatar_label, self.bubble_frame, self.bubble_label, self.bubble_shell, self.bubble_tail]
        for widget in widgets:
            if widget is None:
                continue
            widget.bind("<ButtonPress-1>", callbacks.ドラッグ開始)
            widget.bind("<B1-Motion>", callbacks.ドラッグ移動)
            widget.bind("<ButtonRelease-1>", callbacks.クリック解放)
            widget.bind("<Button-3>", lambda event, cb=callbacks.メニューを開く: self._右クリックメニューイベント(event, cb))
            widget.bind("<Double-Button-1>", callbacks.ダブルクリック)

    def 初期位置へ配置(self) -> None:
        width, height = self.必要サイズを取得()
        screen_width, screen_height = self.画面サイズを取得()
        position = self.settings.start_position.lower()

        if position == "top-left":
            x = self.settings.offset_x
            y = self.settings.offset_y
        elif position == "top-right":
            x = screen_width - width - self.settings.offset_x
            y = self.settings.offset_y
        elif position == "bottom-left":
            x = self.settings.offset_x
            y = screen_height - height - self.settings.offset_y
        else:
            x = screen_width - width - self.settings.offset_x
            y = screen_height - height - self.settings.offset_y
        self.位置を設定(max(0, x), max(0, y))

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
        try:
            self.root.destroy()
        except tk.TclError:
            return

    def 現在位置を取得(self) -> tuple[int, int]:
        return self.root.winfo_x(), self.root.winfo_y()

    def 位置を設定(self, x: int, y: int) -> None:
        self.root.geometry(f"+{x}+{y}")

    def 表示サイズを取得(self) -> tuple[int, int]:
        self.root.update_idletasks()
        return self.root.winfo_width(), self.root.winfo_height()

    def 必要サイズを取得(self) -> tuple[int, int]:
        self.root.update_idletasks()
        return self.root.winfo_reqwidth(), self.root.winfo_reqheight()

    def 画面サイズを取得(self) -> tuple[int, int]:
        return self.root.winfo_screenwidth(), self.root.winfo_screenheight()

    def 現在フレームを表示(self, frames: Sequence[ImageTk.PhotoImage], index: int) -> None:
        if self.avatar_label is None:
            return
        self.current_frames = list(frames)
        self.animation_index = index
        self.avatar_label.configure(image=self.current_frames[self.animation_index])
        self.root.update_idletasks()

    def 吹き出しを表示(self, message: str) -> None:
        if self.bubble_label is None or self.bubble_shell is None or self.avatar_label is None:
            return
        self.bubble_label.configure(text=message)
        if not self.bubble_shell.winfo_ismapped():
            self.bubble_shell.pack(before=self.avatar_label)
        self.root.update_idletasks()

    def 吹き出しを隠す(self) -> None:
        if self.bubble_shell is None:
            return
        if self.bubble_shell.winfo_ismapped():
            self.bubble_shell.pack_forget()

    def コンテキストメニューを表示(self, x_root: int, y_root: int) -> None:
        if self.menu is None:
            return
        try:
            self._オーバーレイを最前面へ出す()
            self.root.update_idletasks()
            self.menu.tk_popup(x_root, y_root + self.タイトル高さ + 4)
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

    def プレビューを表示(self, image: Image.Image | None, label_text: str = "", flash: bool = False) -> None:
        if self.preview_frame is None or self.preview_label is None or self.preview_text_label is None:
            return
        if image is None:
            self.プレビューを隠す()
            return
        photo = ImageTk.PhotoImage(image)
        self.preview_image_ref = photo
        self.preview_label.configure(image=photo)
        self.preview_text_label.configure(text="")
        if not self.preview_frame.winfo_ismapped():
            self.preview_frame.pack(anchor="e", padx=6, pady=(0, 6))
        if flash:
            self._プレビューをフラッシュする()
        self.root.update_idletasks()

    def プレビューを隠す(self) -> None:
        if self.preview_frame is None:
            return
        if self.preview_frame.winfo_ismapped():
            self.preview_frame.pack_forget()

    def _プレビューをフラッシュする(self) -> None:
        if self.preview_frame is None:
            return
        self.preview_frame.configure(bg="#e7e2ff", highlightbackground="#667eea")
        if self.preview_label is not None:
            self.preview_label.configure(bg="#e7e2ff")
        if self.preview_text_label is not None:
            self.preview_text_label.configure(bg="#e7e2ff")
        self.予約解除(self.preview_flash_job)
        self.preview_flash_job = self.予約する(self.プレビューフラッシュ時間ミリ秒, self._プレビューの見た目を戻す)

    def _プレビューの見た目を戻す(self) -> None:
        self.preview_flash_job = None
        if self.preview_frame is not None:
            self.preview_frame.configure(bg="#f7f4ec", highlightbackground="#404040")
        if self.preview_label is not None:
            self.preview_label.configure(bg="#f7f4ec")
        if self.preview_text_label is not None:
            self.preview_text_label.configure(bg="#f7f4ec")

    def マイクUI状態を設定(self, value: bool) -> None:
        self.microphone_var.set(value)

    def マイクUI状態を取得(self) -> bool:
        return bool(self.microphone_var.get())

    def スピーカーUI状態を設定(self, value: bool) -> None:
        self.speaker_var.set(value)

    def スピーカーUI状態を取得(self) -> bool:
        return bool(self.speaker_var.get())

    def カメラUI状態を取得(self) -> bool:
        return bool(self.camera_var.get())

    def カメラメニュー表示を設定(self, value: bool) -> None:
        self.camera_var.set(value)

    def 最前面UI状態を取得(self) -> bool:
        return bool(self.topmost_var.get())

    def 最前面UI状態を設定(self, value: bool) -> None:
        self.topmost_var.set(value)
        self.root.attributes("-topmost", value)

    def リップシンクを更新(self, value: float) -> None:
        pass


class 三次元表示バックエンド:
    吹き出し横幅 = 300
    メニュー後実行待機ミリ秒 = 180
    プレビューフラッシュ時間ミリ秒 = 180
    タイトル幅 = 196
    タイトル高さ = 26
    メニュー背景色 = "#111019"
    メニュー面色 = "#1a1826"
    メニュー文字色 = "#f5f3ff"
    メニュー補助色 = "#b8b2d9"
    メニュー強調色 = "#667eea"
    メニュー境界色 = "#3a3556"

    def __init__(
        self,
        settings: AvatarSettings,
        pose_paths: Sequence[Path],
        icon_path: Path | None,
        sprite_mode: bool,
        sprite_scale: int,
    ) -> None:
        del pose_paths, sprite_mode, sprite_scale
        self.settings = settings
        self.icon_path = icon_path
        self.sprite_mode = False
        self.animations: dict[str, list[ImageTk.PhotoImage]] = {}
        self.current_frames: list[ImageTk.PhotoImage] = []
        self.current_animation = "three-vrm"
        self.viewer_process: ThreeVRMViewerProcess | None = None
        self.viewer_launcher = ThreeVRMViewerLauncher(Path(__file__).resolve().parent.parent)
        self.viewer_width = max(320, self.settings.vrm_window_width)
        self.viewer_height = max(240, self.settings.vrm_window_height)
        self.frame_padding = 10
        self.content_inset = 11
        self.control_area_height = 32
        self.resize_outset = 40
        self.window_width = self.viewer_width + self.frame_padding * 2 + self.resize_outset
        self.window_height = self.viewer_height + self.frame_padding * 2 + self.control_area_height
        self.viewer_handles_window_controls = False

        self.root = tk.Tk()
        self.root.title(settings.avatar_name)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", settings.always_on_top)
        self.root.wm_attributes("-transparentcolor", "#00ff00")
        self.root.configure(bg="#00ff00")

        self.speaker_var = tk.BooleanVar(value=True)
        self.microphone_var = tk.BooleanVar(value=False)
        self.camera_var = tk.BooleanVar(value=False)
        self.topmost_var = tk.BooleanVar(value=settings.always_on_top)
        self.container: tk.Frame | None = None
        self.bubble_shell: tk.Frame | None = None
        self.bubble_frame: tk.Frame | None = None
        self.bubble_tail: tk.Canvas | None = None
        self.bubble_label: tk.Label | None = None
        self.avatar_label: tk.Widget | None = None
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
        self.control_button_size = 24

        self._ウィンドウアイコンを設定()
        self._UI骨組みを構築()

    def _ウィンドウアイコンを設定(self) -> None:
        if not self.icon_path:
            return
        try:
            if self.icon_path.suffix.lower() == ".ico":
                self.root.iconbitmap(default=str(self.icon_path))
            else:
                image = tk.PhotoImage(file=str(self.icon_path))
                self.root.iconphoto(True, image)
                self.root._icon_image = image
        except tk.TclError:
            return

    def _UI骨組みを構築(self) -> None:
        self.container = tk.Frame(self.root, bg="#00ff00", width=self.window_width, height=self.window_height, highlightthickness=0, bd=0)
        self.container.pack()
        self.container.pack_propagate(False)

        self.bubble_shell = tk.Frame(self.container, bg="#00ff00", highlightthickness=0, bd=0)
        self.bubble_frame = tk.Frame(
            self.bubble_shell,
            bg="#000000",
            highlightbackground="#39ff14",
            highlightthickness=1,
            bd=0,
            padx=12,
            pady=8,
        )
        self.bubble_frame.pack()

        self.bubble_tail = tk.Canvas(
            self.bubble_shell,
            width=40,
            height=18,
            bg="#00ff00",
            highlightthickness=0,
            bd=0,
        )
        self.bubble_tail.create_oval(4, 8, 12, 16, fill="#000000", outline="#39ff14", width=1)
        self.bubble_tail.create_oval(13, 4, 25, 16, fill="#000000", outline="#39ff14", width=1)
        self.bubble_tail.create_oval(24, 1, 39, 17, fill="#000000", outline="#39ff14", width=1)
        self.bubble_tail.pack_forget()

        self.bubble_label = tk.Label(
            self.bubble_frame,
            text="",
            justify="center",
            bg="#000000",
            fg="#39ff14",
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
        surface.place(x=self.frame_padding + self.content_inset, y=self.frame_padding + self.content_inset, width=self.viewer_width, height=self.viewer_height)
        # ボーダー枠は常時配置（透過色）でマウスイベントを受け取る
        # "#00ff00" は透過色。マウスオーバー時に色を付けて表示する
        _BORDER_HIDDEN = "#00ff00"
        border_top = tk.Frame(self.container, bg=_BORDER_HIDDEN, height=6, bd=0, highlightthickness=0, cursor="fleur")
        border_top.place(x=self.frame_padding + self.content_inset - 3, y=self.frame_padding + self.content_inset - 3, width=self.viewer_width + 6, height=6)
        border_bottom = tk.Frame(self.container, bg=_BORDER_HIDDEN, height=6, bd=0, highlightthickness=0, cursor="fleur")
        border_bottom.place(x=self.frame_padding + self.content_inset - 3, y=self.frame_padding + self.content_inset + self.viewer_height - 3, width=self.viewer_width + 6, height=6)
        border_left = tk.Frame(self.container, bg=_BORDER_HIDDEN, width=6, bd=0, highlightthickness=0, cursor="fleur")
        border_left.place(x=self.frame_padding + self.content_inset - 3, y=self.frame_padding + self.content_inset - 3, width=6, height=self.viewer_height + 6)
        border_right = tk.Frame(self.container, bg=_BORDER_HIDDEN, width=6, bd=0, highlightthickness=0, cursor="fleur")
        border_right.place(x=self.frame_padding + self.content_inset + self.viewer_width - 3, y=self.frame_padding + self.content_inset - 3, width=6, height=self.viewer_height + 6)
        grip = tk.Frame(
            self.container,
            bg="#8f7cff",
            width=self.タイトル幅,
            height=self.タイトル高さ,
            bd=0,
            highlightthickness=0,
            cursor="fleur",
        )
        grip.pack_propagate(False)
        grip_label = tk.Label(
            grip,
            text=self.settings.avatar_name,
            bg="#8f7cff",
            fg="#ffffff",
            font=("Yu Gothic UI", 11, "bold"),
            bd=0,
            padx=0,
            pady=0,
            cursor="fleur",
        )
        grip_label.place(relx=0.5, rely=0.5, anchor="center")
        self.avatar_label = surface
        self.drag_surface = surface
        self.drag_grip = grip
        self.drag_grip_label = grip_label
        self.drag_border_top = border_top
        self.drag_border_bottom = border_bottom
        self.drag_border_left = border_left
        self.drag_border_right = border_right
        resize_handle = tk.Frame(self.container, bg="#8f7cff", width=18, height=18, bd=0, highlightthickness=0, cursor="size_nw_se")
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
        resize_handle_top_left = tk.Frame(self.container, bg="#8f7cff", width=18, height=18, bd=0, highlightthickness=0, cursor="size_nw_se")
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

        control_panel = tk.Frame(self.container, bg="#211b38", bd=0, highlightthickness=1, highlightbackground="#8f7cff")
        # 初期状態では非表示（ホバーで表示）
        for label, command in (
            ("＋", lambda: self._カメラを調整する("zoom_in")),
            ("−", lambda: self._カメラを調整する("zoom_out")),
            ("▲", lambda: self._カメラを調整する("move_up")),
            ("▼", lambda: self._カメラを調整する("move_down")),
            ("◀", lambda: self._カメラを調整する("move_left")),
            ("▶", lambda: self._カメラを調整する("move_right")),
        ):
            button = tk.Button(
                control_panel,
                text=label,
                command=command,
                width=2,
                height=1,
                bg="#8f7cff",
                fg="#ffffff",
                activebackground="#b9abff",
                activeforeground="#ffffff",
                relief="flat",
                bd=0,
                font=("Yu Gothic UI", 9, "bold"),
                cursor="hand2",
                padx=0,
                pady=0,
            )
            button.pack(side="top", padx=1, pady=1)
        self.control_panel = control_panel

        self.preview_frame = tk.Frame(
            self.container,
            bg="#f7f4ec",
            highlightbackground="#404040",
            highlightthickness=1,
            bd=0,
            padx=4,
            pady=4,
        )
        self.preview_label = tk.Label(self.preview_frame, bg="#f7f4ec", bd=0, highlightthickness=0)
        self.preview_label.pack()
        self.preview_text_label = tk.Label(self.preview_frame, text="", bg="#f7f4ec", fg="#404040", font=("Yu Gothic UI", 8, "bold"))
        self.preview_text_label.pack(pady=(2, 0))

        if self.viewer_handles_window_controls:
            surface.configure(cursor="")
            for widget in (border_top, border_bottom, border_left, border_right, grip, resize_handle_top_left, resize_handle, control_panel):
                widget.place_forget()
            self.avatar_label = None
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
        self.menu.add_checkbutton(label="マイク", variable=self.microphone_var, command=lambda: self._メニュー後に実行(callbacks.マイク切替))
        self.menu.add_checkbutton(label="スピーカー", variable=self.speaker_var, command=lambda: self._メニュー後に実行(callbacks.スピーカー切替))
        self.menu.add_checkbutton(label="カメラ", variable=self.camera_var, command=lambda: self._メニュー後に実行(callbacks.カメラ切替))
        self.menu.add_checkbutton(label="最前面表示", variable=self.topmost_var, command=lambda: self._メニュー後に実行(callbacks.最前面切替))
        self.menu.add_separator()
        self.menu.add_command(label="最新会話", command=lambda: self._メニュー後に実行(callbacks.最新会話を表示))
        self.menu.add_separator()
        self.menu.add_command(label="終了", command=lambda: self._メニュー後に実行(callbacks.終了))

        common_widgets = [
            self.root,
            self.container,
            self.drag_surface,
            self.bubble_frame,
            self.bubble_label,
            self.bubble_shell,
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
            self.bubble_frame,
            self.bubble_label,
            self.bubble_shell,
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
            window_x=max(0, x + self.frame_padding + self.content_inset),
            window_y=max(0, y + self.frame_padding + self.content_inset),
            window_width=self.viewer_width,
            window_height=self.viewer_height,
            always_on_top=False,
            title=self.settings.avatar_name,
        )
        self.viewer_process = self.viewer_launcher.起動する(config)
        self._viewer位置を同期する()
        self._ホバー監視を開始する()
        self.root.after(250, self._オーバーレイを前面維持する)

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
        raise FileNotFoundError("VRM ファイルが見つかりません。frontend_avatar/アバター制御/vrm を確認してください。")

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
        self.root.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")
        self.root.update_idletasks()
        if self.viewer_process is not None:
            self.viewer_process.状態を書き込む(
                x=x + self.frame_padding + self.content_inset,
                y=y + self.frame_padding + self.content_inset,
                width=self.viewer_width,
                height=self.viewer_height,
            )
        self._オーバーレイを最前面へ出す()

    def _レイアウトを更新する(self) -> None:
        if self.container is not None:
            self.container.configure(width=self.window_width, height=self.window_height)
        if self.drag_surface is not None:
            self.drag_surface.place(x=self.frame_padding + self.content_inset, y=self.frame_padding + self.content_inset, width=self.viewer_width, height=self.viewer_height)
        if self.drag_border_top is not None:
            self.drag_border_top.place(x=self.frame_padding + self.content_inset - 3, y=self.frame_padding + self.content_inset - 3, width=self.viewer_width + 6, height=6)
        if self.drag_border_bottom is not None:
            self.drag_border_bottom.place(x=self.frame_padding + self.content_inset - 3, y=self.frame_padding + self.content_inset + self.viewer_height - 3, width=self.viewer_width + 6, height=6)
        if self.drag_border_left is not None:
            self.drag_border_left.place(x=self.frame_padding + self.content_inset - 3, y=self.frame_padding + self.content_inset - 3, width=6, height=self.viewer_height + 6)
        if self.drag_border_right is not None:
            self.drag_border_right.place(x=self.frame_padding + self.content_inset + self.viewer_width - 3, y=self.frame_padding + self.content_inset - 3, width=6, height=self.viewer_height + 6)
        if self.drag_grip is not None:
            self.drag_grip.place(
                x=(self.window_width - self.タイトル幅) // 2,
                y=1,
                width=self.タイトル幅,
                height=self.タイトル高さ,
            )
        if self.resize_handle is not None:
            self.resize_handle.place(x=self.frame_padding + self.content_inset + self.viewer_width + 2, y=self.frame_padding + self.content_inset + self.viewer_height + 2, width=18, height=18)
        if self.resize_handle_top_left is not None:
            self.resize_handle_top_left.place(x=0, y=0, width=18, height=18)
        if self.control_panel is not None:
            self.control_panel.place(
                x=self.frame_padding + self.content_inset + self.viewer_width + 6,
                y=self.frame_padding + self.content_inset + 6,
                anchor="nw",
            )
        if self.bubble_shell is not None and self.bubble_shell.winfo_ismapped():
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
        self.window_height = self.viewer_height + self.frame_padding * 2 + self.control_area_height
        next_x = self.resize_start_root_x - (self.window_width - self.resize_start_window_width) // 2
        next_y = self.resize_start_root_y - (self.window_height - self.resize_start_window_height) // 2
        self._レイアウトを更新する()
        self.位置を設定(next_x, next_y)
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
        self.window_height = self.viewer_height + self.frame_padding * 2 + self.control_area_height
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
        try:
            self._オーバーレイを最前面へ出す()
        except tk.TclError:
            return
        self.root.after(250, self._オーバーレイを前面維持する)

    def _オーバーレイを最前面へ出す(self) -> None:
        always_on_top = bool(self.topmost_var.get())
        self.root.attributes("-topmost", False)
        self.root.lift()
        self.root.attributes("-topmost", always_on_top)
        self.root.update_idletasks()

    def _viewer位置を同期する(self) -> None:
        self.viewer_sync_job = None
        if self.viewer_process is None:
            return
        root_x, root_y = self.現在位置を取得()
        self.viewer_process.状態を書き込む(
            x=root_x + self.frame_padding + self.content_inset,
            y=root_y + self.frame_padding + self.content_inset,
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
                x=(self.window_width - self.タイトル幅) // 2,
                y=1,
                width=self.タイトル幅,
                height=self.タイトル高さ,
            )
        # コントロールパネル・リサイズハンドル
        if self.control_panel is not None:
            self.control_panel.place(
                x=self.frame_padding + self.content_inset + self.viewer_width + 6,
                y=self.frame_padding + self.content_inset + 6,
                anchor="nw",
            )
        if self.resize_handle_top_left is not None:
            self.resize_handle_top_left.place(x=0, y=0, width=18, height=18)
        if self.resize_handle is not None:
            self.resize_handle.place(x=self.frame_padding + self.content_inset + self.viewer_width + 2, y=self.frame_padding + self.content_inset + self.viewer_height + 2, width=18, height=18)

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
                    self.bubble_shell,
                    self.bubble_frame,
                    self.bubble_label,
                    self.bubble_tail,
                    self.control_panel,
                    self.resize_handle_top_left,
                    self.resize_handle_top_left_label,
                    self.resize_handle,
                    self.resize_handle_label,
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

        # グリップ・コントロール・リサイズを隠す
        if self.drag_grip is not None:
            self.drag_grip.place_forget()
        if self.control_panel is not None:
            self.control_panel.place_forget()
        if self.resize_handle_top_left is not None:
            self.resize_handle_top_left.place_forget()
        if self.resize_handle is not None:
            self.resize_handle.place_forget()

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

    def 吹き出しを表示(self, message: str) -> None:
        if self.bubble_label is None or self.bubble_shell is None:
            return
        self.bubble_label.configure(text=message)
        self._メッセージ位置を更新する()
        self.bubble_shell.lift()
        if self.drag_grip is not None:
            self.drag_grip.lift()
        if self.control_panel is not None and self.chrome_visible:
            self.control_panel.lift()
        if self.resize_handle is not None and self.chrome_visible:
            self.resize_handle.lift()
        self._オーバーレイを最前面へ出す()
        self.root.update_idletasks()

    def _メッセージ位置を更新する(self) -> None:
        if self.bubble_shell is None or self.bubble_frame is None:
            return
        self.root.update_idletasks()
        bubble_width = max(self.bubble_frame.winfo_reqwidth(), self.bubble_shell.winfo_reqwidth())
        bubble_height = max(self.bubble_frame.winfo_reqheight(), self.bubble_shell.winfo_reqheight())
        x = self.frame_padding + self.content_inset + max(0, (self.viewer_width - bubble_width) // 2)
        desired_y = self.frame_padding + self.content_inset + int(self.viewer_height * 0.70)
        max_y = self.frame_padding + self.content_inset + max(0, self.viewer_height - bubble_height - 8)
        y = min(desired_y, max_y)
        self.bubble_shell.place(x=x, y=y)

    def 吹き出しを隠す(self) -> None:
        if self.bubble_shell is None:
            return
        self.bubble_shell.place_forget()

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

    def プレビューを表示(self, image: Image.Image | None, label_text: str = "", flash: bool = False) -> None:
        if self.preview_frame is None or self.preview_label is None or self.preview_text_label is None:
            return
        if image is None:
            self.プレビューを隠す()
            return
        photo = ImageTk.PhotoImage(image)
        self.preview_image_ref = photo
        self.preview_label.configure(image=photo)
        self.preview_text_label.configure(text="")
        self.preview_frame.place(
            x=max(self.frame_padding + self.content_inset + 8, self.frame_padding + self.content_inset + self.viewer_width - image.width - 22),
            y=max(self.frame_padding + self.content_inset + 8, self.frame_padding + self.content_inset + self.viewer_height - image.height - 22),
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
        self.preview_frame.configure(bg="#e7e2ff", highlightbackground="#667eea")
        if self.preview_label is not None:
            self.preview_label.configure(bg="#e7e2ff")
        if self.preview_text_label is not None:
            self.preview_text_label.configure(bg="#e7e2ff")
        self.予約解除(self.preview_flash_job)
        self.preview_flash_job = self.予約する(self.プレビューフラッシュ時間ミリ秒, self._プレビューの見た目を戻す)

    def _プレビューの見た目を戻す(self) -> None:
        self.preview_flash_job = None
        if self.preview_frame is not None:
            self.preview_frame.configure(bg="#f7f4ec", highlightbackground="#404040")
        if self.preview_label is not None:
            self.preview_label.configure(bg="#f7f4ec")
        if self.preview_text_label is not None:
            self.preview_text_label.configure(bg="#f7f4ec")

    def マイクUI状態を設定(self, value: bool) -> None:
        self.microphone_var.set(value)

    def マイクUI状態を取得(self) -> bool:
        return bool(self.microphone_var.get())

    def スピーカーUI状態を設定(self, value: bool) -> None:
        self.speaker_var.set(value)

    def スピーカーUI状態を取得(self) -> bool:
        return bool(self.speaker_var.get())

    def カメラUI状態を取得(self) -> bool:
        return bool(self.camera_var.get())

    def カメラメニュー表示を設定(self, value: bool) -> None:
        self.camera_var.set(value)

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
    settings: AvatarSettings,
    pose_paths: Sequence[Path],
    icon_path: Path | None,
    sprite_mode: bool,
    sprite_scale: int,
) -> アバター表示バックエンド:
    if settings.display_backend.lower() == "three-vrm":
        return 三次元表示バックエンド(
            settings=settings,
            pose_paths=pose_paths,
            icon_path=icon_path,
            sprite_mode=sprite_mode,
            sprite_scale=sprite_scale,
        )
    return 二次元表示バックエンド(
        settings=settings,
        pose_paths=pose_paths,
        icon_path=icon_path,
        sprite_mode=sprite_mode,
        sprite_scale=sprite_scale,
    )

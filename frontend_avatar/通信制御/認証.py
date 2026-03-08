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
import tkinter as tk
from http import HTTPStatus
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

from util import AuthSession, AvatarSettings


def コアで認証(base_url: str, user_id: str, password: str) -> AuthSession:
    url = f"{base_url.rstrip('/')}{urllib_parse.quote('/core/auth/ログイン')}"
    body = json.dumps({"利用者ID": user_id, "パスワード": password}, ensure_ascii=False).encode("utf-8")
    request = urllib_request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib_request.urlopen(request, timeout=10) as response:
            status_code = getattr(response, "status", HTTPStatus.OK)
            raw = response.read()
    except urllib_error.HTTPError as exc:
        if exc.code == HTTPStatus.UNAUTHORIZED:
            raise ValueError("認証に失敗しました。")
        raise RuntimeError(f"認証サーバーへ接続できませんでした: {url}") from exc
    except urllib_error.URLError as exc:
        raise RuntimeError(f"認証サーバーへ接続できませんでした: {url}") from exc

    if status_code >= HTTPStatus.BAD_REQUEST:
        raise RuntimeError(f"認証サーバーがエラーを返しました: HTTP {status_code}")

    try:
        payload = json.loads(raw.decode("utf-8"))
    except ValueError as exc:
        raise RuntimeError("認証レスポンスを解析できませんでした。") from exc

    if payload.get("status") != "OK":
        message = payload.get("message") or "ログインに失敗しました。"
        raise ValueError(message)

    data = payload.get("data") or {}
    token = data.get("access_token")
    token_type = data.get("token_type", "bearer")
    if not token:
        raise RuntimeError("認証レスポンスに access_token がありません。")
    return AuthSession(
        user_id=user_id,
        access_token=token,
        token_type=token_type,
        initial_page=data.get("初期ページ", ""),
    )


class LoginDialog:
    影色 = "#07060d"
    背景色 = "#111019"
    面色 = "#1a1826"
    境界色 = "#3a3556"
    文字色 = "#f5f3ff"
    補助色 = "#b8b2d9"
    強調色 = "#667eea"
    入力背景色 = "#0d0c14"
    透過率 = 0.96

    def __init__(self, settings: AvatarSettings) -> None:
        self.settings = settings
        self.session: AuthSession | None = None

        self.root = tk.Tk()
        self.root.title("AiDiy Avatar Login")
        self.root.attributes("-alpha", self.透過率)
        self.root.resizable(False, False)
        self.root.configure(bg=self.背景色)
        self.root.protocol("WM_DELETE_WINDOW", self._キャンセル)
        try:
            self.root.attributes("-toolwindow", True)
        except tk.TclError:
            pass

        self.user_id_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.status_var = tk.StringVar(value=f"認証先: {self.settings.auth_base_url}")
        self.error_var = tk.StringVar()
        self.login_button: tk.Button | None = None
        self.user_entry: tk.Entry | None = None
        self.password_entry: tk.Entry | None = None

        self._画面を構築()
        self._画面中央へ配置()

    def _画面を構築(self) -> None:
        container = tk.Frame(
            self.root,
            bg=self.背景色,
            highlightbackground=self.境界色,
            highlightthickness=1,
            bd=0,
        )
        container.pack(fill="both", expand=True)

        body = tk.Frame(container, bg=self.背景色, padx=18, pady=12)
        body.pack(fill="both", expand=True)

        tk.Label(body, text="利用者ID", anchor="w", bg=self.背景色, fg=self.補助色, font=("Yu Gothic UI", 10, "bold")).pack(fill="x")
        user_entry = tk.Entry(
            body,
            textvariable=self.user_id_var,
            width=30,
            bg=self.入力背景色,
            fg=self.文字色,
            insertbackground=self.強調色,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=self.境界色,
            highlightcolor=self.強調色,
            font=("Yu Gothic UI", 10),
        )
        user_entry.pack(fill="x", pady=(4, 12))
        self.user_entry = user_entry

        tk.Label(body, text="パスワード", anchor="w", bg=self.背景色, fg=self.補助色, font=("Yu Gothic UI", 10, "bold")).pack(fill="x")
        password_entry = tk.Entry(
            body,
            textvariable=self.password_var,
            width=30,
            show="*",
            bg=self.入力背景色,
            fg=self.文字色,
            insertbackground=self.強調色,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=self.境界色,
            highlightcolor=self.強調色,
            font=("Yu Gothic UI", 10),
        )
        password_entry.pack(fill="x", pady=(4, 12))
        self.password_entry = password_entry

        tk.Label(
            body,
            textvariable=self.error_var,
            bg=self.背景色,
            fg="#f87171",
            justify="left",
            wraplength=280,
        ).pack(fill="x", pady=(0, 8))

        tk.Label(
            body,
            textvariable=self.status_var,
            bg=self.背景色,
            fg=self.補助色,
            justify="left",
            wraplength=280,
        ).pack(fill="x", pady=(0, 12))

        actions = tk.Frame(body, bg=self.背景色)
        actions.pack(fill="x")

        self.login_button = tk.Button(
            actions,
            text="ログイン",
            command=self._ログイン実行,
            bg=self.強調色,
            fg="#081016",
            activebackground="#5a6fd8",
            activeforeground="#081016",
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=self.強調色,
            font=("Yu Gothic UI", 10, "bold"),
            padx=10,
            pady=8,
            cursor="hand2",
        )
        self.login_button.pack(side="left", fill="x", expand=True)
        tk.Button(
            actions,
            text="終了",
            command=self._キャンセル,
            bg=self.面色,
            fg=self.文字色,
            activebackground="#202636",
            activeforeground=self.文字色,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=self.境界色,
            font=("Yu Gothic UI", 10, "bold"),
            padx=10,
            pady=8,
            cursor="hand2",
        ).pack(side="left", fill="x", expand=True, padx=(8, 0))

        user_entry.focus_set()
        user_entry.bind("<Return>", self._利用者IDでEnterキー押下)
        password_entry.bind("<Return>", self._Enterキー押下)
        self.root.bind("<Return>", self._Enterキー押下)
        self.root.bind("<Escape>", lambda _event: self._キャンセル())

    def _画面中央へ配置(self) -> None:
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"+{max(0, x)}+{max(0, y)}")

    def _利用者IDでEnterキー押下(self, _event: tk.Event) -> str:
        if self.password_entry is not None:
            self.password_entry.focus_set()
        return "break"

    def _Enterキー押下(self, _event: tk.Event) -> None:
        self._ログイン実行()

    def _処理中表示を設定(self, is_busy: bool) -> None:
        state = "disabled" if is_busy else "normal"
        if self.login_button is not None:
            self.login_button.configure(state=state)
        self.root.configure(cursor="watch" if is_busy else "")
        self.root.update_idletasks()

    def _ログイン実行(self) -> None:
        user_id = self.user_id_var.get().strip()
        password = self.password_var.get()
        if not user_id or not password:
            self.error_var.set("利用者IDとパスワードを入力してください。")
            return

        self.error_var.set("")
        self.status_var.set("認証中...")
        self._処理中表示を設定(True)
        try:
            self.session = コアで認証(self.settings.auth_base_url, user_id, password)
        except ValueError as exc:
            self.error_var.set(str(exc))
            self.status_var.set(f"認証先: {self.settings.auth_base_url}")
            self.password_var.set("")
            self.session = None
        except RuntimeError as exc:
            self.error_var.set(str(exc))
            self.status_var.set(f"認証先: {self.settings.auth_base_url}")
            self.session = None
        finally:
            self._処理中表示を設定(False)

        if self.session is not None:
            self.root.destroy()

    def _キャンセル(self) -> None:
        self.session = None
        self.root.destroy()

    def 表示(self) -> AuthSession | None:
        self.root.mainloop()
        return self.session

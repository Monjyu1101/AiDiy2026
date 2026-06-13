#!/usr/bin/env python
# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

from log_config import get_logger
logger = get_logger(__name__)

import os
import time
import json
import asyncio
import queue
import base64
import mimetypes
from typing import Optional
from pathlib import Path

# api ライブラリ
import openai

# backend_local（ローカル LLM サーバー）の既定接続先
_DEFAULT_LOCAL_HOST = "http://localhost"
_DEFAULT_LOCAL_PORT = "8096"


def _build_base_url(host: str, port: str) -> str:
    """host / port から OpenAI 互換の base_url（.../v1）を組み立てる。"""
    h = (host or _DEFAULT_LOCAL_HOST).strip().rstrip("/")
    if not h.startswith("http://") and not h.startswith("https://"):
        h = "http://" + h
    p = str(port or _DEFAULT_LOCAL_PORT).strip()
    return f"{h}:{p}/v1"


class ChatAI:
    """
    Local Chat api統合クラス（backend_local の OpenAI互換API使用・APIキー不要）

    backend_local（local_main.py / 既定 localhost:8096）が提供する
    `POST /v1/chat/completions` をバックエンドに使う。実モデルは backend_local 側で
    AiDiy_key.json の CHAT_LOCAL_MODEL に従ってロードされる。
    """

    def __init__(self, 親=None, セッションID: str = "", チャンネル: int = 0, 絶対パス: str = None,
                 AI_NAME: str = "local", AI_MODEL: str = "google/gemma-4-E2B-it",
                 api_key: str = None, system_instruction: str = None):
        """初期化"""

        # セッションID・チャンネル
        self.セッションID = セッションID
        self.チャンネル = チャンネル

        # 親参照（セッションマネージャー）
        self.parent_manager = 親
        self.親 = 親

        # backend_local 接続先（host / port）を conf から取得
        self.local_host = _DEFAULT_LOCAL_HOST
        self.local_port = _DEFAULT_LOCAL_PORT
        try:
            if 親 and hasattr(親, "conf") and 親.conf and hasattr(親.conf, "json"):
                host = 親.conf.json.get("LOCAL_HOST", "")
                if host and isinstance(host, str) and not host.startswith("<"):
                    self.local_host = host.strip()
                port = 親.conf.json.get("LOCAL_BASE", "")
                if port and not str(port).startswith("<"):
                    self.local_port = str(port).strip()
        except Exception:
            pass

        # モデル設定（実モデルは backend_local 側で決定されるが、ラベルとして保持）
        self.chat_ai = AI_NAME
        self.chat_model = AI_MODEL
        self.system_instruction = (
            system_instruction.strip()
            if isinstance(system_instruction, str) and system_instruction.strip()
            else None
        )

        # 作業ディレクトリ設定
        if 絶対パス and isinstance(絶対パス, str):
            work_dir = Path(絶対パス)
        else:
            work_dir = Path.cwd()

        self.cwd_str = str(work_dir.resolve())

        # apiクライアント
        self.client = None

        # 生成パラメータ
        self.temperature = 0.8
        self.max_wait_sec = 120

        # 履歴管理システム(ローカル保管)
        self.履歴最終番号 = 0
        self.履歴最終時刻 = time.time()
        self.履歴辞書 = {}
        self.last_output_files = []
        self.last_tool_calls = []

        # 生存状態管理
        self.is_alive = False

    async def 開始(self):
        """ChatAI開始（apiクライアント初期化）"""
        try:
            base_url = _build_base_url(self.local_host, self.local_port)
            try:
                # backend_local は認証なし。OpenAI クライアントはダミーキーを要求するため "local" を渡す。
                self.client = openai.OpenAI(
                    api_key="local",
                    base_url=base_url,
                )
                self.is_alive = True
                logger.info(f"ChatAI(Local): 初期化完了 base_url={base_url} model={self.chat_model}")
                return True
            except Exception as e:
                logger.error(f"ChatAI(Local): apiクライアント初期化エラー: {e}")
                return False

        except Exception as e:
            logger.error(f"ChatAI(Local)開始エラー: {e}")
            self.is_alive = False
            return False

    async def 終了(self):
        """ChatAI終了"""
        try:
            self.is_alive = False
            self.client = None
            return True
        except Exception as e:
            logger.error(f"ChatAI(Local)終了エラー: {e}")
            return False

    async def 実行(self, 要求テキスト: str, テキスト受信処理Ｑ=None, タイムアウト秒数: int = 120,
                   システムプロンプト: str = None, file_path: str = None,
                   completions_tools: dict = None, 自己ループ: bool = False,
                   max_turns: int = 8) -> str:
        """
        ChatAI実行（backend_local 経由でテキスト生成）

        completions_tools: OpenAI completions の追加パラメータ（例: {"tools": [...], "tool_choice": "auto"}）。
                           空 or None のときは何も付与せず、従来挙動と完全に同一。
        """
        try:
            if not self.is_alive:
                logger.warning("ChatAI(Local)実行: ChatAIが開始されていません")
                return "Local ChatAIが停止状態です。backend_local(localhost:8096)が起動しているか確認してください。"

            # 自己ループ（aidiy_chat_llms）: 自前 MCP 群をツールとして使い、
            # tool_calls をサーバー側で実行しながら応答が確定するまで回す。
            # ただしローカル LLM（E2B 等・CPU 推論）では全 MCP ツールの prefill が重く
            # 応答が返らないため、ロジックは残しつつ `if False:` で常に無効化する。
            # （高速な環境で使いたくなったら `if 自己ループ:` に戻すだけ）
            if False:  # 遅すぎるため無効化（self-loop ロジックは温存）
                try:
                    from AIコア.AI内部ツール import MCPツールブリッジ, 自己ループ実行
                except ImportError:
                    from AI内部ツール import MCPツールブリッジ, 自己ループ実行
                ブリッジ = MCPツールブリッジ()
                tools, name_map = ブリッジ.collect_tools()
                if tools:
                    msgs = []
                    sys_text = システムプロンプト or getattr(self, "system_instruction", None)
                    if sys_text:
                        msgs.append({"role": "system", "content": sys_text})
                    msgs.append({"role": "user", "content": 要求テキスト})
                    結果 = await 自己ループ実行(
                        self, msgs, ブリッジ, tools, name_map, max_turns, タイムアウト秒数
                    )
                    self.last_tool_trace = 結果["tool_trace"]
                    self.last_tool_turns = 結果["turns"]
                    self.last_tool_stopped = 結果["stopped"]
                    return 結果["content"] or "!"
                # tools 無し（8095 未起動等）→ 通常処理にフォールバック

            # ファイル添付処理（画像のみ対応、vision対応モデルの場合）
            image_data = None
            if file_path:
                try:
                    if os.path.isfile(file_path):
                        mime_type, _ = mimetypes.guess_type(file_path)
                        if mime_type and mime_type.startswith("image/"):
                            with open(file_path, "rb") as f:
                                image_bytes = f.read()
                                image_base64 = base64.b64encode(image_bytes).decode("utf-8")
                                image_data = {"mime_type": mime_type, "data": image_base64}
                            logger.info(f"ChatAI(Local): 画像ファイルを添付 {file_path}")
                except Exception as e:
                    logger.error(f"ChatAI(Local): ファイル添付エラー {e}")

            output_files = []
            self.last_output_files = output_files
            self.last_tool_calls = []

            タイムアウトフラグ = asyncio.Event()

            async def タイムアウト監視():
                try:
                    await asyncio.sleep(タイムアウト秒数)
                    タイムアウトフラグ.set()
                    logger.warning(f"ChatAI(Local)実行タイムアウト: {タイムアウト秒数}秒")
                except asyncio.CancelledError:
                    pass

            タイムアウトタスク = asyncio.create_task(タイムアウト監視())

            try:
                self._履歴追加(role="user", text=要求テキスト, image_data=image_data)
                メッセージ履歴 = self._メッセージ履歴構築(システムプロンプト=システムプロンプト)

                応答テキスト = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self._同期実行(
                        メッセージ履歴=メッセージ履歴,
                        テキスト受信処理Ｑ=テキスト受信処理Ｑ,
                        タイムアウトフラグ=タイムアウトフラグ,
                        output_files=output_files,
                        completions_tools=completions_tools,
                    ),
                )

                タイムアウトタスク.cancel()
                final_result = 応答テキスト.strip() if 応答テキスト.strip() else "!"
                self._履歴追加(role="assistant", text=final_result)

                if final_result == "!" and テキスト受信処理Ｑ:
                    try:
                        data = {"type": "stream", "content": "!", "timestamp": time.time()}
                        テキスト受信処理Ｑ.put_nowait({"text": "!", "json": json.dumps(data, ensure_ascii=False)})
                    except Exception:
                        pass

                return final_result

            except asyncio.CancelledError:
                logger.warning("ChatAI(Local)実行がキャンセルされました")
                return "処理がキャンセルされました。"
            except Exception as e:
                logger.error(f"ChatAI(Local)実行エラー: {e}")
                エラーメッセージ = f"実行エラー: {str(e)}"
                if テキスト受信処理Ｑ:
                    data = {"type": "error", "content": "!!! 処理エラー !!!", "timestamp": time.time()}
                    テキスト受信処理Ｑ.put_nowait({"text": "!!! 処理エラー !!!", "json": json.dumps(data, ensure_ascii=False)})
                return エラーメッセージ
            finally:
                タイムアウトタスク.cancel()

        except Exception as e:
            セッションID_str = self.セッションID[:10] + "..." if self.セッションID else "不明"
            logger.error(f"ChatAI(Local)実行エラー: {e} 要求=[{要求テキスト[:10]}...] セッション={セッションID_str}")
            エラーメッセージ = f"実行エラー: {str(e)}"
            if テキスト受信処理Ｑ:
                data = {"type": "error", "content": "!!! 処理エラー !!!", "timestamp": time.time()}
                テキスト受信処理Ｑ.put_nowait({"text": "!!! 処理エラー !!!", "json": json.dumps(data, ensure_ascii=False)})
            return エラーメッセージ

    def _同期実行(self, メッセージ履歴: list,
                   テキスト受信処理Ｑ: queue.Queue = None,
                   タイムアウトフラグ: asyncio.Event = None,
                   output_files: list = None,
                   completions_tools: dict = None) -> str:
        """同期API実行（スレッドプールで実行）"""
        try:
            parm_kwargs = {
                "model": self.chat_model,
                "messages": メッセージ履歴,
                "temperature": float(self.temperature),
                "timeout": self.max_wait_sec,
                "stream": False,
            }

            # completions_tools が指定された場合のみ tools などの追加パラメータをマージ
            # （空 or None のときは何もしないため従来挙動と同一）
            if completions_tools:
                parm_kwargs.update(completions_tools)

            response = self.client.chat.completions.create(**parm_kwargs)

            応答テキスト = ""
            if response and response.choices:
                message = response.choices[0].message
                # tool_calls を捕捉（completions_tools 指定時のみ発生。空なら従来通り）
                tc = getattr(message, "tool_calls", None)
                if tc:
                    self.last_tool_calls = [
                        {
                            "id": getattr(c, "id", None),
                            "type": getattr(c, "type", "function") or "function",
                            "function": {
                                "name": c.function.name,
                                "arguments": c.function.arguments,
                            },
                        }
                        for c in tc
                    ]
                message_content = message.content
                if isinstance(message_content, list):
                    for part in message_content:
                        if hasattr(part, "type") and part.type == "text":
                            応答テキスト += part.text
                else:
                    応答テキスト = str(message_content) if message_content else ""

            if テキスト受信処理Ｑ and 応答テキスト:
                try:
                    data = {"type": "stream", "content": 応答テキスト, "timestamp": time.time()}
                    テキスト受信処理Ｑ.put_nowait({"text": 応答テキスト, "json": json.dumps(data, ensure_ascii=False)})
                except Exception:
                    pass

            return 応答テキスト

        except Exception as e:
            logger.error(f"ChatAI(Local)同期実行エラー: {e}")
            return ""

    def _メッセージ履歴構築(self, システムプロンプト: str = None) -> list:
        """Local/OpenAI形式のメッセージ履歴を構築"""
        メッセージ = []
        system_prompt_text = None
        if isinstance(システムプロンプト, str) and システムプロンプト.strip():
            system_prompt_text = システムプロンプト.strip()
        elif self.system_instruction:
            system_prompt_text = self.system_instruction
        else:
            system_prompt_text = "あなたは、美しい日本語を話す、賢いAIアシスタントです。"

        メッセージ.append({
            "role": "system",
            "content": [{"type": "text", "text": system_prompt_text}],
        })

        履歴 = self._履歴取得()
        for item in 履歴:
            if item.get("image_data"):
                image_data = item["image_data"]
                メッセージ.append({
                    "role": item["role"],
                    "content": [
                        {"type": "text", "text": item["text"]},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{image_data['mime_type']};base64,{image_data['data']}"
                            },
                        },
                    ],
                })
            else:
                メッセージ.append({
                    "role": item["role"],
                    "content": [{"type": "text", "text": item["text"]}],
                })

        return メッセージ

    def _履歴追加(self, role: str, text: str, image_data: dict = None):
        """履歴にメッセージを追加"""
        self.履歴最終番号 += 1
        self.履歴最終時刻 = time.time()
        self.履歴辞書[self.履歴最終番号] = {
            "role": role,
            "text": text,
            "image_data": image_data,
            "time": self.履歴最終時刻,
        }

    def _履歴取得(self) -> list:
        """履歴を時系列順に取得"""
        return [
            {
                "role": self.履歴辞書[番号]["role"],
                "text": self.履歴辞書[番号]["text"],
                "image_data": self.履歴辞書[番号].get("image_data"),
            }
            for 番号 in sorted(self.履歴辞書.keys())
        ]

    def 履歴クリア(self):
        """履歴をクリア"""
        self.履歴辞書 = {}
        self.履歴最終番号 = 0
        self.履歴最終時刻 = time.time()

# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101
# -------------------------------------------------------------------------

"""
AIコア チャット処理プロセッサ
非同期キューでチャット要求を受け取り、AI応答を生成してWebSocketへ返す
"""

import asyncio
import importlib
import json
import os
from typing import Optional

from log_config import get_logger

logger = get_logger(__name__)

_CHAT_CONTEXT_JSON_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_config", "AiDiy_chat__context.json")
)

_CHAT_CONTEXT_TEMPLATE_LINES = [
    "あなたは、美しい日本語を話す、賢いAIアシスタントです。",
]


def _context_template_payload() -> dict:
    return {
        "version": 1,
        "description": "AIコア ChatAI 定型コンテキスト",
        "system_instruction_lines": _CHAT_CONTEXT_TEMPLATE_LINES,
    }


def _compose_instruction(lines: list[str]) -> str:
    text = "\n".join(lines)
    if not text.endswith("\n"):
        text += "\n"
    return text


def _load_or_create_chat_context() -> str:
    """ChatAI定型コンテキストを読み込む。無ければひな形JSONを作成。"""
    template_payload = _context_template_payload()
    template_instruction = _compose_instruction(template_payload["system_instruction_lines"])

    try:
        os.makedirs(os.path.dirname(_CHAT_CONTEXT_JSON_PATH), exist_ok=True)

        if not os.path.exists(_CHAT_CONTEXT_JSON_PATH):
            with open(_CHAT_CONTEXT_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(template_payload, f, indent=2, ensure_ascii=False)
            logger.info(f"[Chat] 定型コンテキストJSONを作成: {_CHAT_CONTEXT_JSON_PATH}")
            return template_instruction

        with open(_CHAT_CONTEXT_JSON_PATH, "r", encoding="utf-8-sig") as f:
            payload = json.load(f)

        lines = payload.get("system_instruction_lines") if isinstance(payload, dict) else None
        if isinstance(lines, list):
            normalized = [str(line) for line in lines]
            return _compose_instruction(normalized)

        logger.warning(f"[Chat] 定型コンテキストJSONの形式不正。ひな形を再作成します: {_CHAT_CONTEXT_JSON_PATH}")
        with open(_CHAT_CONTEXT_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(template_payload, f, indent=2, ensure_ascii=False)
        return template_instruction
    except Exception as e:
        logger.error(f"[Chat] 定型コンテキスト読込エラー: {e}")
        return template_instruction


class Chat:
    """チャット処理クラス（キュー処理）- チャンネル0専用"""

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
        self.システム指示 = _load_or_create_chat_context()
        self.AIモジュール = self._select_ai_module()
        self.AIインスタンス = None
        self.is_alive = False
        self.チャット処理Ｑ = asyncio.Queue()
        self.worker_task: Optional[asyncio.Task] = None
        self.会話履歴 = []  # チャンネル専用の会話履歴

    def _select_ai_module(self):
        """AI_NAMEに応じたチャットモジュールを選択してインポート"""
        module_name = "AIコア.AIチャット_openrt"
        if self.AI_NAME in ("gemini", "freeai"):
            module_name = "AIコア.AIチャット_gemini"
        try:
            return importlib.import_module(module_name)
        except Exception as e:
            logger.error(f"[Chat] AIモジュールのインポート失敗: {module_name} error={e}")
            return None

    async def _ensure_ai_instance(self):
        """AIモジュールのChatAIインスタンスを生成・開始"""
        if not self.AIモジュール:
            return None
        if self.AIインスタンス:
            return self.AIインスタンス
        try:
            api_key = ""
            try:
                conf_json = getattr(self.親, "conf", None)
                if conf_json and hasattr(conf_json, "json"):
                    if self.AI_NAME in ("gemini", "freeai"):
                        api_key = conf_json.json.get("gemini_key_id", "")
                        if self.AI_NAME == "freeai":
                            api_key = conf_json.json.get("freeai_key_id", "") or api_key
                    else:
                        api_key = conf_json.json.get("openrt_key_id", "")
            except Exception:
                api_key = ""
            ChatAI = getattr(self.AIモジュール, "ChatAI", None)
            if ChatAI is None:
                logger.error("[Chat] ChatAIクラスが見つかりません")
                return None
            self.AIインスタンス = ChatAI(
                親=self.親,
                セッションID=self.セッションID,
                チャンネル=self.チャンネル,
                AI_NAME=self.AI_NAME,
                AI_MODEL=self.AI_MODEL,
                絶対パス=self.絶対パス or None,
                api_key=api_key or None,
                system_instruction=self.システム指示,
            )
            開始成功 = await self.AIインスタンス.開始()
            if (開始成功 is False) or (not getattr(self.AIインスタンス, "is_alive", False)):
                logger.error(
                    f"[Chat] ChatAI開始失敗: AI={self.AI_NAME} モデル={self.AI_MODEL} "
                    f"セッション={self.セッションID}"
                )
                self.AIインスタンス = None
                return None
            return self.AIインスタンス
        except Exception as e:
            logger.error(f"[Chat] ChatAI初期化エラー: {e}")
            self.AIインスタンス = None
            return None

    async def 開始(self):
        """チャット処理ワーカーを開始"""
        self.is_alive = True
        if self.worker_task is None or self.worker_task.done():
            self.worker_task = asyncio.create_task(self._チャット処理ワーカー())
            logger.debug(f"[Chat] チャンネル{self.チャンネル} 開始")

    async def 終了(self):
        """チャット処理ワーカーを終了"""
        self.is_alive = False
        if self.worker_task and not self.worker_task.done():
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        logger.debug(f"[Chat] チャンネル{self.チャンネル} 終了")

    async def チャット要求(self, 受信データ: dict):
        """チャット要求をキューに追加（受信データ構造体をそのまま投入）"""
        if not 受信データ:
            return
        if not self.is_alive:
            logger.warning("[Chat] チャット要求: Chatプロセッサが開始されていません")
            if self.接続:
                await self.接続.send_to_channel(self.チャンネル, {
                    "セッションID": self.セッションID,
                    "メッセージ識別": "output_text",
                    "メッセージ内容": "ChatAIが停止状態です。APIキーの設定を確認、再起動してください。",
                    "ファイル名": None,
                    "サムネイル画像": None
                })
            return
        await self.チャット処理Ｑ.put(受信データ)

    async def _チャット処理ワーカー(self):
        """チャット処理ワーカー（キューから取り出して処理）"""
        while self.is_alive:
            try:
                try:
                    受信データ = await asyncio.wait_for(self.チャット処理Ｑ.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    await asyncio.sleep(0.2)
                    continue

                if not isinstance(受信データ, dict):
                    continue
                    
                メッセージ識別 = 受信データ.get("メッセージ識別", "")
                
                if メッセージ識別 == "input_text":
                    # テキスト処理: AI実行 → output_text送信（エコーバックは既に実施済み）
                    await self._処理_input_text(受信データ)
                elif メッセージ識別 == "input_file":
                    # ファイル処理: temp/outputコピー → output_file送信 → 会話履歴保存
                    await self._処理_input_file(受信データ)
                
                self.チャット処理Ｑ.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Chat] チャンネル{self.チャンネル} 処理エラー: {e}")
                await asyncio.sleep(0.2)

    def _サムネイル生成(self, ファイルパス: str) -> str | None:
        """画像ファイルからサムネイルを生成してbase64で返す"""
        try:
            import base64
            from io import BytesIO
            from PIL import Image
            image = Image.open(ファイルパス)
            image = image.convert("RGBA")
            width, height = image.size
            if width > 0 and height > 0:
                new_width = 320
                new_height = int(height * (new_width / width))
                thumbnail = image.resize((new_width, new_height), Image.LANCZOS)
                buf = BytesIO()
                thumbnail.save(buf, format="PNG")
                return base64.b64encode(buf.getvalue()).decode("ascii")
        except Exception as e:
            logger.debug(f"[Chat] サムネイル生成スキップ: {e}")
        return None

    async def _AI実行と応答送信(self, 受信データ: dict, file_path: str = None):
        """AI実行 → output_text送信 + 出力ファイルがあればoutput_fileをチャンネル-1に送信"""
        try:
            import os
            import re

            メッセージ内容 = 受信データ.get("メッセージ内容", "")

            # 処理要求ログ
            セッションID_短縮 = self.セッションID[:10] if self.セッションID else '不明'
            logger.info(
                f"処理要求: チャンネル={self.チャンネル}, ソケット={セッションID_短縮}...,\n{メッセージ内容.rstrip()}\n"
            )

            出力メッセージ内容 = ""
            出力ファイル一覧 = []
            try:
                ai_instance = await self._ensure_ai_instance()
                if ai_instance:
                    logger.info(
                        f"[Chat] AI実行開始: AI={self.AI_NAME} モデル={self.AI_MODEL} チャンネル={self.チャンネル}"
                    )
                    出力メッセージ内容 = await ai_instance.実行(
                        要求テキスト=メッセージ内容,
                        file_path=file_path,
                    )
                    logger.info(
                        f"[Chat] AI実行結果: 文字数={len(出力メッセージ内容) if 出力メッセージ内容 is not None else 'None'}"
                    )
                    # AI側が保存したファイル一覧を取得
                    出力ファイル一覧 = getattr(ai_instance, "last_output_files", []) or []
            except Exception as e:
                logger.error(f"[Chat] AI実行エラー: {e}")
                出力メッセージ内容 = "!"

            if not 出力メッセージ内容:
                出力メッセージ内容 = "!"

            # テキストから [画像ファイル: ...] 行を除去（ファイルは別途output_fileで送る）
            if 出力ファイル一覧:
                出力メッセージ内容 = re.sub(r'\n?\[画像ファイル: [^\]]+\]', '', 出力メッセージ内容).strip()
                if not 出力メッセージ内容:
                    出力メッセージ内容 = "画像を生成しました。"

            # 処理応答ログ
            logger.info(
                f"処理応答: チャンネル={self.チャンネル}, ソケット={セッションID_短縮}...,\n{出力メッセージ内容.rstrip()}\n"
            )

            # 1) output_text送信
            await self.接続.send_to_channel(self.チャンネル, {
                "セッションID": self.セッションID,
                "メッセージ識別": "output_text",
                "メッセージ内容": 出力メッセージ内容,
                "ファイル名": None,
                "サムネイル画像": None
            })

            # 2) 会話履歴保存（テキスト）
            if self.保存関数:
                self.保存関数(
                    セッションID=self.セッションID,
                    チャンネル=self.チャンネル,
                    メッセージ識別="output_text",
                    メッセージ内容=出力メッセージ内容,
                    ファイル名=None,
                    サムネイル画像=None
                )

            # 3) 出力ファイルがあればoutput_fileとしてチャンネル-1に送信
            for 出力ファイルパス in 出力ファイル一覧:
                if not os.path.exists(出力ファイルパス):
                    logger.warning(f"[Chat] 出力ファイルが見つかりません: {出力ファイルパス}")
                    continue
                ファイル名のみ = os.path.basename(出力ファイルパス)
                相対パス = f"temp/output/{ファイル名のみ}"
                # サムネイル生成
                サムネイル_base64 = self._サムネイル生成(出力ファイルパス)
                await self.接続.send_to_channel(self.チャンネル, {
                    "セッションID": self.セッションID,
                    "メッセージ識別": "output_file",
                    "メッセージ内容": f"ファイル出力: {ファイル名のみ}",
                    "ファイル名": 相対パス,
                    "サムネイル画像": サムネイル_base64
                })
                # 会話履歴保存（ファイル）
                if self.保存関数:
                    self.保存関数(
                        セッションID=self.セッションID,
                        チャンネル=self.チャンネル,
                        メッセージ識別="output_file",
                        メッセージ内容=f"ファイル出力: {ファイル名のみ}",
                        ファイル名=相対パス,
                        サムネイル画像=サムネイル_base64
                    )

        except Exception as e:
            logger.error(f"[Chat] チャンネル{self.チャンネル} AI実行応答エラー: {e}")

    async def _処理_input_text(self, 受信データ: dict):
        """input_text処理: AI実行 → output_text送信（画像自動添付対応）"""
        import os
        
        元のメッセージ内容 = 受信データ.get("メッセージ内容", "")
        添付ファイル一覧 = 受信データ.get("添付ファイル一覧", [])
        
        # 添付ファイルが無い場合、最近1分以内の画像を自動添付
        # （実際は core_router/AIコア.py で既に添付済みだが、念のため再確認）
        if not 添付ファイル一覧:
            # 親のセッション管理から最近のファイルを取得（1分 = 60秒）
            if hasattr(self.親, "最近のファイル取得"):
                最近のファイル一覧 = self.親.最近のファイル取得(self.チャンネル, 秒数=60)
                if 最近のファイル一覧:
                    # 最初の画像ファイルを添付
                    for パス in 最近のファイル一覧:
                        if os.path.exists(パス):
                            拡張子 = os.path.splitext(パス)[1].lower()
                            if 拡張子 in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"):
                                添付ファイル一覧 = [パス]
                                logger.info(f"[Chat] 最近の画像を自動添付: {パス}")
                                break
        
        file_path = None
        if 添付ファイル一覧:
            # 最初の画像ファイルをfile_pathとして渡す
            for パス in 添付ファイル一覧:
                if os.path.exists(パス):
                    拡張子 = os.path.splitext(パス)[1].lower()
                    if 拡張子 in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"):
                        file_path = パス
                        break
            # file_pathが無い場合は最初の存在するファイルを使用
            if not file_path:
                for パス in 添付ファイル一覧:
                    if os.path.exists(パス):
                        file_path = パス
                        break
            
            if file_path:
                logger.info(f"[Chat] 添付ファイル渡し: {file_path}")
        
        # AI実行と応答送信（エコーバックは core_router/AIコア.py で既に実施済み）
        受信データ["メッセージ内容"] = 元のメッセージ内容
        await self._AI実行と応答送信(受信データ, file_path=file_path)

    async def _処理_input_file(self, 受信データ: dict):
        """input_file処理: AIにファイルを渡して実行 → output_text + output_file送信"""
        import os

        入力ファイル名 = 受信データ.get("ファイル名")
        if not 入力ファイル名:
            return
        # 絶対パスに変換
        file_path = os.path.abspath(入力ファイル名) if 入力ファイル名 else None
        if file_path and not os.path.exists(file_path):
            logger.warning(f"[Chat] 入力ファイルが見つかりません: {file_path}")
            return
        await self._AI実行と応答送信(受信データ, file_path=file_path)


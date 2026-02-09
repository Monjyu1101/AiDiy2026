# -*- coding: utf-8 -*-
#
# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

"""
AIコア Live処理プロセッサ
LiveAIの初期化と開始、受信キューをフロントへ中継
旧実装（AiDiy_AIコア__server_live.py）と同じ手順で実装
"""

import importlib
import asyncio
import base64
import time
from typing import Optional
from log_config import get_logger

logger = get_logger(__name__)

# ユーザー音声検出割り込み制御定数
USER_VOICE_INTERRUPT_SECONDS = 1.0  # ユーザー音声が1.0秒以上経過でAI音声出力


class Live:
    """LiveAI 管理クラス（旧実装準拠）"""

    def __init__(
        self,
        親=None,
        セッションID: str = "",
        チャンネル: int = 0,
        絶対パス: str = "",
        AI_NAME: str = "",
        AI_MODEL: str = "",
        AI_VOICE: str = "",
        接続=None,
        保存関数=None,
    ):
        self.セッションID = セッションID
        self.チャンネル = チャンネル
        self.絶対パス = 絶対パス
        self.AI_NAME = AI_NAME
        self.AI_MODEL = AI_MODEL
        self.AI_VOICE = AI_VOICE
        self.接続 = 接続
        self.保存関数 = 保存関数
        self.親 = 親
        self.AIモジュール = self._select_ai_module()
        self.AIインスタンス = None
        self.is_alive = False
        self._initializing = False  # 初期化中フラグ（重複呼び出し防止）
        self.音声受信Ｑ: Optional[asyncio.Queue] = None
        self.テキスト受信Ｑ: Optional[asyncio.Queue] = None
        self._audio_task: Optional[asyncio.Task] = None
        self._text_task: Optional[asyncio.Task] = None

        # 音声入力/出力データは接続（セッション）のaudio_dataを使用
        # 統合音声分離ワーカーはaudio_processing.pyのものを使用
        # live.pyはLiveAIからの出力音声受信処理のみを担当

    def _select_ai_module(self):
        """AI_NAMEに応じたLiveモジュールを選択してインポート"""
        module_name = "AIコア.AIライブ_gemini"
        ai_name = (self.AI_NAME or "").lower()
        if ai_name == "openai_live":
            module_name = "AIコア.AIライブ_openai"
        try:
            return importlib.import_module(module_name)
        except Exception as e:
            logger.error(f"[Live] AIモジュールのインポート失敗: {module_name} error={e}")
            return None

    async def _ensure_ai_instance(self):
        """AIモジュールのLiveAIインスタンスを生成・開始"""
        if not self.AIモジュール:
            return None
        if self.AIインスタンス:
            return self.AIインスタンス

        logger.info(f"[Live] LiveAI初期化開始: {self.AI_NAME} (AIコアセッション: {self.セッションID})")
        try:
            api_key = ""
            organization = ""
            ai_name = (self.AI_NAME or "").lower()
            live_ai = ai_name

            try:
                conf_json = getattr(self.親, "conf", None)
                if conf_json and hasattr(conf_json, "json"):
                    if live_ai in ("gemini_live", "freeai_live"):
                        api_key = conf_json.json.get("gemini_key_id", "")
                        if live_ai == "freeai_live":
                            api_key = conf_json.json.get("freeai_key_id", "") or api_key
                        if not self.AI_MODEL:
                            key = "LIVE_FREEAI_MODEL" if live_ai == "freeai_live" else "LIVE_GEMINI_MODEL"
                            self.AI_MODEL = conf_json.json.get(key, "") or self.AI_MODEL
                        if not self.AI_VOICE:
                            key = "LIVE_FREEAI_VOICE" if live_ai == "freeai_live" else "LIVE_GEMINI_VOICE"
                            self.AI_VOICE = conf_json.json.get(key, "") or self.AI_VOICE
                    else:
                        api_key = conf_json.json.get("openai_key_id", "")
                        organization = conf_json.json.get("openai_organization", "")
                        if not self.AI_MODEL:
                            self.AI_MODEL = conf_json.json.get("LIVE_OPENAI_MODEL", "") or self.AI_MODEL
                        if not self.AI_VOICE:
                            self.AI_VOICE = conf_json.json.get("LIVE_OPENAI_VOICE", "") or self.AI_VOICE
            except Exception:
                api_key = ""
                organization = ""

            LiveAI = getattr(self.AIモジュール, "LiveAI", None)
            if LiveAI is None:
                logger.error("[Live] LiveAIクラスが見つかりません")
                return None

            if live_ai == "openai_live":
                self.AIインスタンス = LiveAI(
                    セッションID=self.セッションID,
                    parent_manager=self.親,
                    live_ai=live_ai,
                    live_model=self.AI_MODEL,
                    live_voice=self.AI_VOICE,
                    api_key=api_key or None,
                    organization=organization or None,
                )
            else:
                self.AIインスタンス = LiveAI(
                    セッションID=self.セッションID,
                    parent_manager=self.親,
                    live_ai=live_ai,
                    live_model=self.AI_MODEL,
                    live_voice=self.AI_VOICE,
                    api_key=api_key or None,
                )
            if self.音声受信Ｑ is None:
                self.音声受信Ｑ = asyncio.Queue()
            if self.テキスト受信Ｑ is None:
                self.テキスト受信Ｑ = asyncio.Queue()
            await self.AIインスタンス.開始(self.音声受信Ｑ, self.テキスト受信Ｑ)
            logger.info(f"[Live] LiveAI初期化完了: {self.AI_NAME} (AIコアセッション: {self.セッションID})")
            return self.AIインスタンス
        except Exception as e:
            logger.error(f"[Live] LiveAI初期化エラー: {e}")
            self.AIインスタンス = None
            return None

    async def 開始(self):
        """Live処理を開始（旧実装準拠）"""
        # 既に初期化中または完了している場合はスキップ
        if self._initializing or self.AIインスタンス:
            return

        self._initializing = True
        try:
            self.is_alive = True
            await self._ensure_ai_instance()
            if self._audio_task is None or self._audio_task.done():
                self._audio_task = asyncio.create_task(self._音声受信ワーカー())
            if self._text_task is None or self._text_task.done():
                self._text_task = asyncio.create_task(self._テキスト受信ワーカー())
            # 統合音声分離ワーカーはaudio_processing.pyで起動済み（重複回避）
        finally:
            self._initializing = False

    async def 終了(self):
        """Live処理を終了"""
        self.is_alive = False
        if self._audio_task and not self._audio_task.done():
            self._audio_task.cancel()
            try:
                await self._audio_task
            except asyncio.CancelledError:
                pass
        if self._text_task and not self._text_task.done():
            self._text_task.cancel()
            try:
                await self._text_task
            except asyncio.CancelledError:
                pass
        if self.AIインスタンス and hasattr(self.AIインスタンス, "終了"):
            try:
                await self.AIインスタンス.終了()
            except Exception:
                pass
        self.AIインスタンス = None

    # ===== 音声受信処理（旧実装準拠） =====
    # 音声入力処理はaudio_processing.pyで実装済み（重複回避）

    async def _音声データ受信処理(self, audio_data: dict):
        """
        LiveAIから受信した音声データの処理（割り込み制御付き、旧実装準拠）

        Args:
            audio_data: 音声データ辞書 {"bytes_data": bytes, "mime_type": str}
        """
        try:
            current_time = time.time()

            # 接続のaudio_dataを使用
            input_data = self.接続.audio_data["音声入力データ"] if self.接続 else None
            output_data = self.接続.audio_data["音声出力データ"] if self.接続 else None

            if not input_data or not output_data:
                # audio_dataが未初期化の場合は音声送信のみ
                await self._send_output_audio(audio_data)
                return

            # ユーザーが話していない時（1.0秒以上経過）のみ出力
            input_audio_lasttime = input_data.get('音声入力最終時刻')
            if (input_audio_lasttime is None or
                (input_audio_lasttime and current_time - input_audio_lasttime > USER_VOICE_INTERRUPT_SECONDS)):

                # WebSocketクライアントに送信
                await self._send_output_audio(audio_data)

            # 音声認識用バッファに蓄積
            audio_bytes = audio_data['bytes_data']
            if len(output_data['音声出力バッファ']) == 0:
                output_data['音声出力開始時刻'] = current_time  # バッファリング開始時刻

            output_data['音声出力最終時刻'] = current_time
            output_data['音声出力バッファ'].append(audio_bytes)

        except Exception as e:
            logger.error(f"音声データ受信処理エラー: {e}")

    async def _send_output_audio(self, audio_data: dict) -> bool:
        """出力音声をWebSocketクライアントに送信（旧実装準拠）"""
        try:
            if not self.接続:
                return False
            bytes_data = audio_data.get("bytes_data")
            mime_type = audio_data.get("mime_type", "audio/pcm")
            if not bytes_data:
                return False
            base64_audio = base64.b64encode(bytes_data).decode("utf-8")
            await self.接続.send_to_channel(-1, {
                "セッションID": self.セッションID,
                "メッセージ識別": "output_audio",
                "メッセージ内容": mime_type,
                "ファイル名": base64_audio,
                "サムネイル画像": None
            })
            return True
        except Exception as e:
            logger.error(f"[Live] 音声送信エラー: {e}")
            return False

    async def _send_output_text(self, text_data: dict) -> bool:
        """出力テキストをWebSocketクライアントに送信（旧実装準拠）"""
        try:
            if not self.接続:
                return False
            text = text_data.get("text") if isinstance(text_data, dict) else None
            if not text:
                return False
            # Chatと共通の処理応答ログ形式
            セッションID_短縮 = self.セッションID[:10] if self.セッションID else '不明'
            logger.info(
                f"処理応答: チャンネル={self.チャンネル}, ソケット={セッションID_短縮}...,\n{text.rstrip()}\n"
            )
            await self.接続.send_to_channel(0, {
                "セッションID": self.セッションID,
                "メッセージ識別": "output_text",
                "メッセージ内容": text,
                "ファイル名": None,
                "サムネイル画像": None
            })
            return True
        except Exception as e:
            logger.error(f"[Live] テキスト送信エラー: {e}")
            return False

    # ===== ワーカー（旧実装準拠） =====

    async def _音声受信ワーカー(self):
        """音声受信ワーカー（旧実装準拠）"""
        while self.is_alive:
            try:
                if not self.音声受信Ｑ:
                    await asyncio.sleep(0.2)
                    continue

                # 音声データを待機（タイムアウト付き）
                try:
                    item = await asyncio.wait_for(self.音声受信Ｑ.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                if not item:
                    continue
                if not self.接続:
                    continue

                # 音声データ受信処理を経由（バッファ蓄積、割り込み制御を含む）
                await self._音声データ受信処理(item)

                # バッファ件数による切り分け
                if self.音声受信Ｑ.qsize() > 0:
                    pass  # データあり：高速処理
                else:
                    await asyncio.sleep(0.10)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Live] 音声受信ワーカーエラー: {e}")
                await asyncio.sleep(0.2)

    async def _テキスト受信ワーカー(self):
        """テキスト受信ワーカー（旧実装準拠）"""
        while self.is_alive:
            try:
                if not self.テキスト受信Ｑ:
                    await asyncio.sleep(0.2)
                    continue

                # テキストデータを待機（タイムアウト付き）
                try:
                    item = await asyncio.wait_for(self.テキスト受信Ｑ.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                if not item:
                    continue
                if not self.接続:
                    continue

                # WebSocketクライアントに送信
                await self._send_output_text(item)

                # バッファ件数による切り分け
                if self.テキスト受信Ｑ.qsize() > 0:
                    await asyncio.sleep(0.25)  # データ有：CPU軽減
                else:
                    await asyncio.sleep(0.50)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Live] テキスト受信ワーカーエラー: {e}")
                await asyncio.sleep(0.2)

    # 統合音声分離ワーカーはaudio_processing.pyで実装済み（重複回避）

    # ===== テキスト送信（LiveAIへ） =====

    async def テキスト送信(self, text: str) -> bool:
        """LiveAIへテキスト送信（旧実装準拠）"""
        try:
            if self.AIインスタンス and self.AIインスタンス.is_alive:
                # Chatと共通の処理要求ログ形式
                セッションID_短縮 = self.セッションID[:10] if self.セッションID else '不明'
                logger.info(
                    f"処理要求: チャンネル={self.チャンネル}, ソケット={セッションID_短縮}...,\n{text.rstrip()}\n"
                )
                return await self.AIインスタンス.テキスト送信(text)
            return False
        except Exception as e:
            logger.error(f"[Live] テキスト送信エラー: {e}")
            return False

    async def 画像送信(self, image_data, format: str = "jpeg") -> bool:
        """LiveAIへ画像送信（旧実装準拠）"""
        try:
            if self.AIインスタンス and self.AIインスタンス.is_alive:
                image_size = len(image_data) if isinstance(image_data, bytes) else "unknown"
                logger.info(f"[Live] 画像入力: format={format} size={image_size}bytes ({self.セッションID})")
                return await self.AIインスタンス.画像送信(image_data, format)
            return False
        except Exception as e:
            logger.error(f"[Live] 画像送信エラー: {e}")
            return False


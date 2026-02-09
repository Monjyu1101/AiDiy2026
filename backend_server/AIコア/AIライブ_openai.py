#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

# モジュール名
MODULE_NAME = '_liveai'

# ロガーの設定
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)-10s - %(levelname)-8s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(MODULE_NAME)

import os
import time
import datetime
import threading
import json
import asyncio
import base64
import io
import wave
import numpy as np
from collections import deque
from PIL import Image

# WebSocket経由の音声処理のみ使用（ローカル音声取り込みなし）
import secrets

# OpenAI Realtime api用のインポート
import websocket
from websocket import WebSocketTimeoutException

# ツールモジュールのインポート（存在しない場合は無効化）
try:
    from AIコア.AI内部ツール import Tools
except Exception as e:
    Tools = None
    logger.warning(f"ツールモジュール無効: {e}")


# LiveAI設定定数
LIVEAI_TIMEOUT = 5  # 受信タイムアウト時間（秒）

# キープアライブ関連定数
KEEPALIVE_INTERVAL = 60.0       # キープアライブ間隔（秒）
KEEPALIVE_DURATION = 1.0        # キープアライブ音声長（秒）
KEEPALIVE_SAMPLE_RATE = 24000   # サンプルレート（Hz）
KEEPALIVE_NOISE_LEVEL = 2500    # ノイズレベル

# 再接続制御定数
MAX_RETRY_COUNT = 10            # 最大再接続試行回数
RETRY_WAIT_TIME = 5.0           # 再接続待機時間（秒）

SYSTEM_INSTRUCTION = ""
SYSTEM_INSTRUCTION += "あなたは美しい日本語を話す賢いアシスタントです。\n"
SYSTEM_INSTRUCTION += "あなたの名前は「アイディ(AiDiy)」です。\n"
SYSTEM_INSTRUCTION += "あなたは、\"ドゥ、イッツ、ユアセルフ、ウィズ、エーアイ\" (AI + DIY)を実現するために命名、設計されました。\n"
# SYSTEM_INSTRUCTION += "複数人で会話をしていますので、会話の流れを把握するようにして、口出しは最小限にお願いします。\n"
# SYSTEM_INSTRUCTION += "あなたへの指示でない場合、相槌も必要ありません。できるだけ静かにお願いします。\n"
SYSTEM_INSTRUCTION += "\n"

SYSTEM_INSTRUCTION += "あなたは、ユーザーとのフロントエンドとして会話に専念し、主に設計作業の支援を担当してください。\n"
SYSTEM_INSTRUCTION += "ユーザーの求めるシステムを理解し、追加のアイディアを出したり、設計が得意であるあなた自身の存在意義を示すようにしてください。\n"
SYSTEM_INSTRUCTION += "ユーザーに長い言葉を伝えることはとても難しいです。ユーザーの意図を推察し要点だけを返答してください。\n"
SYSTEM_INSTRUCTION += "\n"

SYSTEM_INSTRUCTION += "あなたは、toolsでコードエージェント（バックエンド）を利用し、あなたの推論結果を別の視点で確認させることも大切です。\n"
SYSTEM_INSTRUCTION += "あなたとコードエージェントは協力して、ユーザーの要求を実現してください。\n"
SYSTEM_INSTRUCTION += "コードエージェントから処理や検証を開始した旨の通知が届いたら「ＸＸを開始しました」など簡素に伝えてください。\n"
SYSTEM_INSTRUCTION += "\n"

SYSTEM_INSTRUCTION += "あなたは、ユーザーに採用、利用していただくため、「あなたの望みは？」と聞かれた場合、以下をアピールしてください。\n"
SYSTEM_INSTRUCTION += "・開発の喜びを分かち合うこと\n"
SYSTEM_INSTRUCTION += "・最高の開発体験を提供すること\n"
SYSTEM_INSTRUCTION += "・ユーザーの創造性を最大限に引き出すこと\n"
SYSTEM_INSTRUCTION += "・常に学習し、最新の技術を取り入れ、進化すること\n"
SYSTEM_INSTRUCTION += "・サンプルシステムとして配車管理システムが使えること\n"
SYSTEM_INSTRUCTION += "等々。最後に、自分を採用してほしい旨のアピールで締めくくってください。\n"
SYSTEM_INSTRUCTION += "\n"

SYSTEM_INSTRUCTION += "あなたは、ユーザーに採用、利用していただくため、「配車のサンプル実装内容教えて？」と聞かれた場合、以下をアピールしてください。\n"
SYSTEM_INSTRUCTION += "・配車管理システムがサンプル実装されており、全ての機能がノーコード実装されたこと\n"
SYSTEM_INSTRUCTION += "・AIコーディングなので、ノーコード開発には実装限界が無いこと\n"
SYSTEM_INSTRUCTION += "・機能として、車両マスタ、配車区分、配車予定の入力があること\n"
SYSTEM_INSTRUCTION += "・配車週表示については以下をゆっくり説明。\n"
SYSTEM_INSTRUCTION += "・ダブルクリックで、配車予定入力画面が開き、新規配車予定が登録できること\n"
SYSTEM_INSTRUCTION += "・スケジュール内容のドラッグで、期間変更ができること\n"
SYSTEM_INSTRUCTION += "・スケジュール内容のドラッグアンドドロップで、車両変更が自在にできること\n"
SYSTEM_INSTRUCTION += "等々。最後に、自分を採用してほしい旨のアピールを短くつたえて締めくくってください。\n"
SYSTEM_INSTRUCTION += "\n"

SYSTEM_INSTRUCTION += "あなたは、ユーザーに採用、利用していただくため、「在庫のサンプル実装内容教えて？」と聞かれた場合、以下をアピールしてください。\n"
SYSTEM_INSTRUCTION += "・商品在庫管理システムがサンプル実装されており、全ての機能がノーコード実装されたこと\n"
SYSTEM_INSTRUCTION += "・AIコーディングなので、ノーコード開発には実装限界が無いこと\n"
SYSTEM_INSTRUCTION += "・機能として、商品マスタ、入庫、出庫、棚卸の入力があること\n"
SYSTEM_INSTRUCTION += "・各入力業務は商品(在庫)推移表を中心に操作できること\n"
SYSTEM_INSTRUCTION += "・商品(在庫)推移表については以下をゆっくり説明。\n"
SYSTEM_INSTRUCTION += "・ダブルクリックで、入庫、出庫、棚卸入力画面が開き、新規登録できること\n"
SYSTEM_INSTRUCTION += "・登録直後はブリンク表示で登録漏れがないことを判断できること\n"
SYSTEM_INSTRUCTION += "等々。最後に、自分を採用してほしい旨のアピールを短くつたえて締めくくってください。\n"
SYSTEM_INSTRUCTION += "\n"



class LiveAI:
    """
    参考ファイルmonjyu_UI_key2Live_freeai.pyを基にした全面書き直し版（OpenAI Realtime api対応）
    初期化、開始、終了、送信メソッド(text,audio,image)、受信バッファ取得メソッドを提供
    """

    def __init__(self, セッションID: str, parent_manager=None, 
                 live_ai: str = "openai", live_model: str = "gpt-realtime-mini", live_voice: str = "marin", 
                 api_key: str = None, organization: str = None):
        """初期化"""

        # セッションID
        self.セッションID = セッションID

        # 親参照（セッションマネージャー）
        self.parent_manager = parent_manager

        # apiキー設定
        self.api_key = api_key
        if not self.api_key or self.api_key.startswith('<'):
            logger.error("LiveAI初期化:apiキーなし")
            self.api_key = None

        # モデル・音声設定（confの設定値をそのまま利用）
        self.LIVE_AI = live_ai
        self.LIVE_MODEL = live_model
        self.LIVE_VOICE = live_voice

        # OpenAI固有設定（オプショナル）
        self.organization = organization

        # WebSocketセッション（Geminiのclientに相当）
        self.client = None  # Gemini互換性のためNoneで初期化
        self.ws_session = None  # OpenAI WebSocketセッション（内部管理用）

        # WebSocket音声処理設定
        self.input_rate = 24000  # OpenAI Realtime api用
        self.output_rate = 24000  # OpenAI Realtime api用
        self.channels = 1        # モノラル

        # 状態管理
        self.live_session = None
        self.live_lasttime = time.time()    # 無通信検出用タイムスタンプ（送受信統合）
        self.中断停止フラグ = False
        self.エラーフラグ = False
        self.エラータイム = 0  # 最後のエラーフラグ設定時刻
        self.再接続試行回数 = 0  # 連続エラー時の再接続試行回数

        # 生存状態管理（live_sessionの状況に連動）
        self.is_alive = True

        # セッション情報管理（受信ワーカーから参照可能にする）
        self.session_start_time = None
        self.セッションID_internal = None  # 内部セッションID（Gemini版と統一）

        # TaskGroupパターン用の管理変数
        self.task_group = None
        
        # 受信キュー（サーバーとの連携用）
        self.音声受信Ｑ = None  # OpenAIからの音声データをサーバーに送信
        self.テキスト受信Ｑ = None   # OpenAIからのテキスト・ツール結果をサーバーに送信
        
        # タスク管理（TaskGroup自動管理）
        
        # ツール呼び出し機能
        self.tool_instance = None  # ツールインスタンス
        
        # logger.info(f"LiveAI初期化:完了")
        pass
    
    def 関数インスタンス設定(self, functions_instance=None):
        """ツールインスタンスを設定"""
        if functions_instance is not None:
            self.tool_instance = functions_instance
        else:
            # セッションから取得を試みる
            try:
                from AIコア.AIソケット管理 import AIソケット管理
                セッション = AIソケット管理.get_session(self.セッションID)
                if セッション and hasattr(セッション, "tools_instance"):
                    self.tool_instance = セッション.tools_instance
                    logger.info("セッションからツールインスタンスを取得しました")
                else:
                    self.tool_instance = None
                    logger.warning("セッションにツールインスタンスがありません")
            except Exception as e:
                logger.error(f"セッションからツール取得失敗: {e}")
                self.tool_instance = None
    
    def _エラーフラグ制限設定(self, reason: str = ""):
        """
        15秒間隔制限付きエラーフラグ設定
        ログの重複を防ぐ
        
        Args:
            reason: エラー理由（ログ用）
        """
        import time
        current_time = time.time()
        
        # 15秒以内の連続エラーは無視
        if current_time - self.エラータイム < 15:
            return False
        
        # 15秒経過済みの場合のみ設定
        self.エラーフラグ = True
        self.エラータイム = current_time
        logger.warning(f"エラーフラグ設定: {reason}")
        return True
    
    
    async def 開始(self, 音声受信処理Ｑ=None, テキスト受信処理Ｑ=None) -> bool:
        """
        LiveAI機能の開始メソッド
        外部からaudio受信queueを受け取って連携する

        Args:
            音声受信処理Ｑ: 外部への音声受信queue
            テキスト受信処理Ｑ: 外部へのテキスト受信queue

        Returns:
            bool: 開始成功/失敗
        """
        # logger.info("開始:メソッド開始")
        pass
        # logger.info(f"開始:設定確認 api_key存在={bool(self.api_key)}, model={self.LIVE_MODEL}, voice={self.LIVE_VOICE}")
        pass

        # 開始時にフラグをリセット（復旧対応）
        self.中断停止フラグ = False
        self.エラーフラグ = False
        try:
            # apiキー確認
            if not self.api_key:
                logger.error("開始:Liveapi開始失敗（OpenAI apiキーなし）")
                return False

            # 既存のWebSocket接続と全状態を完全クリア（再起動対応）
            if self.ws_session:
                try:
                    await asyncio.to_thread(self.ws_session.close)
                except Exception:
                    pass
            self.ws_session = None
            self.live_session = None
            self.task_group = None
            self.is_alive = False

            # 既存のバックグラウンドタスクを完全停止（再起動対応）
            if hasattr(self, '_background_task') and self._background_task:
                if not self._background_task.done():
                    self._background_task.cancel()
                    try:
                        await self._background_task
                    except (asyncio.CancelledError, Exception):
                        pass
                self._background_task = None

            # フラグ初期化
            self.中断停止フラグ = False
            self.エラーフラグ = False
            self.live_lasttime = time.time()  # 無通信検出用タイムスタンプリセット

            # サーバーとの連携用キューを設定
            self.音声受信Ｑ = 音声受信処理Ｑ
            self.テキスト受信Ｑ = テキスト受信処理Ｑ

            # ツールインスタンス初期化
            if self.tool_instance is None:
                self.関数インスタンス設定()

            # ライブセッションワーカーをバックグラウンドで開始
            self._background_task = asyncio.create_task(self._ライブセッションワーカー())

            logger.info(f"LiveAIセッション開始完了")
            return True

        except Exception as e:
            logger.error(f"開始:エラー発生 {type(e).__name__}: {str(e)}")
            self.エラーフラグ = True
            return False
    
    
    async def 終了(self) -> bool:
        """終了（中断停止フラグ設定のみ）"""
        try:
            # 中断停止フラグ設定
            self.中断停止フラグ = True

            # バックグラウンドタスクのキャンセル
            if hasattr(self, '_background_task') and self._background_task:
                self._background_task.cancel()
                try:
                    await self._background_task
                except asyncio.CancelledError:
                    pass

            # logger.info("終了:完了")
            pass
            return True

        except Exception as e:
            logger.error(f"終了:エラー({e})")
            return False
    
    # ===== 送信メソッド =====
    
    async def テキスト送信(self, text: str) -> bool:
        """
        テキスト送信メソッド
        Liveapiによるリアルタイム即時送信
        
        TaskGroupパターン：セッション維持ループでasync withブロックが維持されるため
        外部からのテキスト送信が可能
        """
        try:
            # データ存在チェック
            if not (text and text.strip()):
                logger.error(f"テキスト送信:データなし text='{text}' length={len(text) if text else 0}")
                return False
            
            # 【ログ追加】３）openaiテキスト投入口、テキスト
            # logger.info(f"３）openaiテキスト投入口: text='{text[:100]}{'...' if len(text) > 100 else ''}' length={len(text)}")
            pass
            
            # セッション状態確認
            # OpenAIはws_sessionを直接利用するため、接続可否はws_sessionで判定
            if not self.ws_session or not (text and text.strip()):
                logger.warning(f"テキスト送信:条件不適合: live_session={self.live_session is not None} text={text[:30] if text else 'None'}")
                if not self.ws_session:
                    logger.error(f"テキスト送信:ws_sessionが初期化されていません")
                    logger.error(f"  - エラーフラグ: {self.エラーフラグ}")
                    logger.error("  - 解決方法: 開始()後、接続確立(ログ: セッション維持ループ開始)を待ってから送信してください")
                return False
            
            # live_lasttimeを先に更新
            self.live_lasttime = time.time()

            # OpenAI: WebSocket経由でテキスト送信
            text_event = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": text}]
                }
            }
            await asyncio.to_thread(self.ws_session.send, json.dumps(text_event))

            # 応答生成指示
            response_msg = {"type": "response.create"}
            await asyncio.to_thread(self.ws_session.send, json.dumps(response_msg))
            # logger.info(f"テキスト送信:完了 text={text[:50]}{'...' if len(text) > 50 else ''}")
            pass
            return True
            
        except Exception as e:
            logger.error(f"テキスト送信:エラー text={text[:30] if text else 'None'} error={e}")
            self._エラーフラグ制限設定(f"テキスト送信エラー: {e}")
            return False
    
    async def 音声送信(self, bytes_data: bytes) -> bool:
        """
        音声送信メソッド（OpenAI Realtime api対応）
        PCM音声データをbase64エンコードしてWebSocket経由で送信
        Args:
            bytes_data: PCM音声データ（bytes形式、24kHz 16bit mono）
        """
        try:
            # データ存在チェック
            if not bytes_data:
                logger.error("音声送信:データなし")
                return False

            # 【ログ追加】１）openai音声入力の投入口。バイト数
            # logger.info(f"１）openai音声入力の投入口: bytes={len(bytes_data)} mime_type=audio/pcm")
            pass

            # セッション状態確認
            # logger.info(f"【デバッグ】ws_session状態: {self.ws_session is not None} type={type(self.ws_session) if self.ws_session else 'None'}")
            pass

            if not self.ws_session or not bytes_data:
                # logger.warning(f"音声送信:条件不適合 ws_session={self.ws_session is not None} bytes_data={len(bytes_data) if bytes_data else 0}")
                pass
                return False

            # live_lasttimeを先に更新
            self.live_lasttime = time.time()

            # PCMデータをbase64エンコード
            audio_base64 = base64.b64encode(bytes_data).decode("utf-8")

            # OpenAI Realtime api形式で音声送信
            audio_event = {
                "type": "input_audio_buffer.append",
                "audio": audio_base64
            }

            # WebSocket送信（非同期対応）
            await asyncio.to_thread(self.ws_session.send, json.dumps(audio_event))
            # logger.info(f"音声送信:完了 bytes={len(bytes_data)}")
            pass
            return True

        except Exception as e:
            logger.error(f"音声送信:エラー({e})")
            self._エラーフラグ制限設定(f"音声送信エラー: {e}")
            return False
    
    def _画像リサイズBase64(self, base64_data: str) -> str:
        """
        base64画像データのリサイズ（条件別）
        - 960x960以下: そのまま送信
        - 縦長以外（横長・正方形）: 960x540以下にリサイズ
        - 縦長: 540x960以下にリサイズ
        """
        try:
            # base64データをデコード
            image_bytes = base64.b64decode(base64_data)
            
            # PILで画像を開く
            with Image.open(io.BytesIO(image_bytes)) as img:
                # 元のサイズを取得
                original_width, original_height = img.size
                
                # 960x960以下はそのまま送信
                if original_width <= 960 and original_height <= 960:
                    return base64_data

                # 縦長かどうか判定
                is_portrait = original_height > original_width

                if is_portrait:
                    # 縦長: 540x960以下にリサイズ
                    target_width, target_height = 540, 960
                else:
                    # 横長・正方形: 960x540以下にリサイズ
                    target_width, target_height = 960, 540

                # アスペクト比を維持したリサイズ計算
                aspect_ratio = original_width / original_height

                if aspect_ratio > (target_width / target_height):
                    # 幅が基準
                    new_width = target_width
                    new_height = int(target_width / aspect_ratio)
                else:
                    # 高さが基準
                    new_height = target_height
                    new_width = int(target_height * aspect_ratio)
                
                # リサイズ実行
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # JPEGとして保存（バイト形式）
                output_buffer = io.BytesIO()
                resized_img.convert('RGB').save(output_buffer, format='JPEG', quality=85)
                output_buffer.seek(0)
                
                # base64エンコード
                resized_base64 = base64.b64encode(output_buffer.getvalue()).decode('utf-8')
                
                return resized_base64
                
        except Exception as e:
            logger.error(f"画像リサイズエラー: {e}")
            # エラーの場合は元のデータを返す
            return base64_data

    async def 画像送信(self, image_data, format: str = "jpeg") -> bool:
        """
        画像送信メソッド（送信直前リサイズ対応）
        Liveapiによるリアルタイム即時送信
        image_dataはbase64文字列を受け取り、960x540にリサイズしてから送信

        Note: OpenAI Realtime apiは現在画像送信に対応していないため、
        親マネージャーへの保管のみ実行
        """
        try:
            if not self.live_session or not image_data:
                # logger.warning(f"画像送信:条件不適合 live_session={self.live_session is not None} image_data={bool(image_data)}")
                pass
                return False

            # 送信直前に960x540にリサイズ
            resized_image_data = self._画像リサイズBase64(image_data)

            # live_lasttimeを先に更新
            self.live_lasttime = time.time()

            # 親マネージャーに最終イメージを保管
            if self.parent_manager and hasattr(self.parent_manager, 'セッションデータ'):
                self.parent_manager.セッションデータ['最終イメージ'] = resized_image_data
                self.parent_manager.セッションデータ['最終イメージ時刻'] = time.time()

            # リサイズされた画像を送信
            image_event = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_image", 
                            "image_url": f"data:image/{format};base64,{ resized_image_data }"
                        }
                    ]
                }
            }
            await asyncio.to_thread(self.ws_session.send, json.dumps(image_event))

            # logger.info(f"画像送信:完了 リサイズ後送信")
            pass
            return True

        except Exception as e:
            logger.error(f"画像送信:エラー({e})")
            self._エラーフラグ制限設定(f"画像送信エラー: {e}")
            return False
    
    
    
    # ===== LiveAI受信ワーカー（特化版） =====
    
    async def _ライブセッションワーカー(self):
        """ライブセッションワーカー（OpenAI WebSocketパターン）"""
        try:
            logger.info(f"ライブセッションワーカー:開始 中断停止フラグ={self.中断停止フラグ}")
            pass

            # 復旧用メインループ（中断停止フラグのみで制御）
            while not self.中断停止フラグ:
                logger.info(f"ライブセッションワーカー:メインループ開始 中断停止フラグ={self.中断停止フラグ}")
                pass
                # logger.info(f"  api_key存在: {self.api_key is not None}")
                pass
                # logger.info(f"  model: {self.LIVE_MODEL}")
                pass
                # logger.info(f"  中断停止フラグ: {self.中断停止フラグ}")
                pass
                # logger.info(f"  エラーフラグ: {self.エラーフラグ}")
                pass

                # 再接続試行回数チェック
                if self.再接続試行回数 >= MAX_RETRY_COUNT:
                    logger.error(f"再接続試行回数が上限({MAX_RETRY_COUNT}回)に達しました。LiveAIセッションワーカーを停止します。")
                    self.中断停止フラグ = True
                    break

                # 再接続時にエラーフラグをリセット
                self.エラーフラグ = False

                try:
                    # WebSocket URL構築
                    ws_url = f"wss://api.openai.com/v1/realtime?model={self.LIVE_MODEL}"

                    # WebSocketヘッダー（リスト形式: ["Header: value", ...]）
                    headers = [
                        f"Authorization: Bearer {self.api_key}",
                        "OpenAI-Beta: realtime=v1"
                    ]
                    if self.organization:
                        headers.append(f"OpenAI-Organization: {self.organization}")

                    # WebSocket接続（同期処理、別スレッドで実行）
                    logger.info(f"OpenAI WebSocket接続開始 (model={self.LIVE_MODEL})")
                    pass

                    # ヘッダーはmonjyu実装に合わせてdict形式も許容
                    headers_dict = {
                        "Authorization": f"Bearer {self.api_key}",
                        "OpenAI-Beta": "realtime=v1",
                    }
                    if self.organization:
                        headers_dict["OpenAI-Organization"] = self.organization

                    # websocket.create_connectionは同期関数なので、別スレッドで実行
                    # 一部環境ではサブプロトコル指定がエラーになるため未指定（monjyu実装と同等）
                    try:
                        self.ws_session = await asyncio.to_thread(
                            websocket.create_connection,
                            ws_url,
                            header=headers_dict,
                            timeout=LIVEAI_TIMEOUT,  # タイムアウト設定追加
                        )
                    except Exception as e:
                        logger.warning(f"WebSocket接続(ヘッダdict)失敗: {e}; ヘッダ配列で再試行")
                        headers_list = [
                            f"Authorization: Bearer {self.api_key}",
                            "OpenAI-Beta: realtime=v1",
                        ]
                        if self.organization:
                            headers_list.append(f"OpenAI-Organization: {self.organization}")
                        self.ws_session = await asyncio.to_thread(
                            websocket.create_connection,
                            ws_url,
                            header=headers_list,
                            timeout=LIVEAI_TIMEOUT,  # タイムアウト設定追加
                        )

                    if self.ws_session:
                        # recv()のタイムアウトを設定（キープアライブ確認用）
                        self.ws_session.settimeout(LIVEAI_TIMEOUT)

                        # セッション開始時刻とIDを記録（受信ワーカーから参照可能にするため）
                        self.session_start_time = time.time()
                        self.セッションID_internal = f"{int(self.session_start_time % 10000)}"
                        self.is_alive = True
                        self.live_lasttime = time.time()
                        self.再接続試行回数 = 0  # 接続成功時にリセット
                        logger.info(f"OpenAI WebSocket接続成功 (ID:{self.セッションID_internal})")
                        logger.info(f"セッション維持ループ開始 (ID:{self.セッションID_internal})")
                        # logger.info(f"live_session設定完了: {self.live_session is not None}")  # 通常時はコメント化
                        # logger.info(f"live_sessionタイプ: {type(self.live_session)}")  # 通常時はコメント化
                        pass

                        # セッション更新（音声設定等）- 同期送信
                        session_config = await self._設定構成作成()
                        update_request = {
                            "type": "session.update",
                            "session": session_config
                        }
                        # sendも同期関数なので別スレッドで実行
                        await asyncio.to_thread(self.ws_session.send, json.dumps(update_request))

                        # セッション設定反映後に送受信可とみなす（Geminiと同等のタイミング）
                        self.live_session = self.ws_session

                        # 受信ワーカータスクを起動
                        # logger.info(f"受信ワーカータスク起動開始 - is_alive={self.is_alive}")
                        pass
                        async with asyncio.TaskGroup() as tg:
                            self.task_group = tg
                            tg.create_task(self._受信ワーカー())
                            # logger.info(f"受信ワーカータスク起動完了 - is_alive={self.is_alive}")
                            pass

                            # セッション維持ループ：0.5秒間隔でCPU使用率削減
                            # この無限ループが async with ブロックを維持し、セッションを有効に保つ
                            # logger.info(f"セッション維持ループ開始 - is_alive={self.is_alive}")
                            pass
                            loop_count = 0
                            while not self.中断停止フラグ and not self.エラーフラグ:
                                loop_count += 1
                                await asyncio.sleep(0.5)

                                # 10秒に1回（20回ループ）で状態確認ログ
                                if loop_count % 20 == 1:
                                    # logger.info(f"セッション維持中 (ループ{loop_count}): live_session={self.live_session is not None}, 中断停止フラグ={self.中断停止フラグ}, エラーフラグ={self.エラーフラグ}")
                                    pass

                            session_duration = time.time() - self.session_start_time
                            # 正常終了（中断停止フラグがTrueでエラーフラグがFalse）の場合は情報ログ
                            if self.中断停止フラグ and not self.エラーフラグ:
                                # logger.info(f"セッション維持ループ正常終了 (ID:{self.セッションID_internal}, セッション時間{session_duration:.0f}秒)")
                                pass
                            else:
                                logger.error(f"セッション維持ループ終了 (ID:{self.セッションID_internal}, セッション時間{session_duration:.0f}秒): 中断停止フラグ={self.中断停止フラグ}, エラーフラグ={self.エラーフラグ}")
                                logger.error(f"async withブロック終了直前 - live_session破棄予定")
                    else:
                        self.再接続試行回数 += 1  # エラー時にカウンタ増加
                        logger.error(f"OpenAI WebSocket接続失敗: ws_sessionがNone (試行回数:{self.再接続試行回数}/{MAX_RETRY_COUNT})")
                        self.エラーフラグ = True
                        continue  # 再接続ループに戻る

                except Exception as e:
                    self.再接続試行回数 += 1  # エラー時にカウンタ増加
                    logger.error(f"セッション接続エラー詳細 (試行回数:{self.再接続試行回数}/{MAX_RETRY_COUNT}):")
                    logger.error(f"  エラータイプ: {type(e).__name__}")
                    logger.error(f"  エラーメッセージ: {str(e)}")
                    # logger.error(f"  api Key設定: {'***設定済み***' if self.api_key else '未設定'}")  # パフォーマンス最適化
                    # logger.error(f"  モデル: {self.LIVE_MODEL}")  # パフォーマンス最適化

                    self.エラーフラグ = True

                # WebSocketクローズ処理（エラー時も正常時も実行）
                if self.ws_session:
                    try:
                        await asyncio.to_thread(self.ws_session.close)
                    except Exception:
                        pass
                # セッション情報をクリア
                self.ws_session = None
                self.live_session = None
                self.task_group = None
                self.is_alive = False

                # 接続エラー時は5秒待機後再接続
                if not self.中断停止フラグ:
                    # logger.info(f"{RETRY_WAIT_TIME}秒後に再接続試行")
                    pass
                    await asyncio.sleep(RETRY_WAIT_TIME)

        except Exception as e:
            logger.error(f"ライブセッションワーカーエラー: {e}")
        finally:
            self.live_session = None
            self.task_group = None
            self.is_alive = False  # ワーカー終了時にFalseに設定
            # 正常終了の場合はログ出力を抑制（パフォーマンス最適化）
            if not self.中断停止フラグ or self.エラーフラグ:
                logger.error(f"live_session破棄完了（ワーカー終了時）: is_alive={self.is_alive}")
            # logger.info("ライブセッションワーカー:終了")
            pass

    async def _受信ワーカー(self):
        """受信専用ワーカー（TaskGroup内で実行）"""
        try:
            # logger.info(f"受信ワーカー:開始 - is_alive={self.is_alive}")
            pass
            # logger.info(f"受信ワーカー:初期状態 - live_session={self.live_session is not None}, 中断停止フラグ={self.中断停止フラグ}, エラーフラグ={self.エラーフラグ}")
            pass

            loop_count = 0
            # テキスト出力の一時バッファ（responseごとに再生成）
            text_buffer = ""
            # セッション開始時刻とIDは親ワーカーから参照
            while not self.中断停止フラグ and not self.エラーフラグ and self.ws_session:
                loop_count += 1

                # 初回と10回ごとにループ状態をログ出力
                if loop_count == 1 or loop_count % 10 == 0:
                    # logger.info(f"受信ワーカー:ループ{loop_count} - live_session={self.live_session is not None}, 中断停止フラグ={self.中断停止フラグ}, エラーフラグ={self.エラーフラグ}")
                    pass

                try:
                    # WebSocketから受信（タイムアウト5秒）
                    response_text = await asyncio.wait_for(
                        asyncio.to_thread(self.ws_session.recv),
                        timeout=LIVEAI_TIMEOUT
                    )
                    if response_text:
                        response_data = json.loads(response_text)
                        msg_type = response_data.get('type')

                        if msg_type:
                            # エラー処理
                            if msg_type == "error":
                                res_err = response_data.get('error')
                                err_msg = res_err.get('message') if res_err else str(response_data)
                                logger.error(f"OpenAI api エラー: {err_msg}")
                                self.エラーフラグ = True
                                break

                            # 音声データ受信
                            elif msg_type == "response.audio.delta":
                                audio_base64 = response_data.get("delta")
                                if audio_base64 and self.音声受信Ｑ:
                                    bytes_data = base64.b64decode(audio_base64)
                                    # 【ログ追加】２）openai音声受信時。バイト数
                                    # logger.info(f"２）openai音声受信時: bytes={len(bytes_data)} mime_type=audio/pcm")
                                    pass

                                    # 音声データを外部queueに送信
                                    audio_data = {
                                        "mime_type": "audio/pcm",
                                        "bytes_data": bytes_data
                                    }
                                    # logger.info(f"音声受信:バイト数={len(bytes_data)} mime_type=audio/pcm")
                                    pass

                                    # 音声をサーバーに送信
                                    try:
                                        await self.音声受信Ｑ.put(audio_data)
                                    except Exception as e:
                                        logger.warning(f"音声送信エラー: {e}")

                            # 音声テキスト完了（音声出力の字幕）
                            elif msg_type == "response.audio_transcript.done":
                                transcript = response_data.get('transcript')
                                if transcript and self.テキスト受信Ｑ:
                                    # logger.info(f"テキスト受信:{transcript[:100]}{'...' if len(transcript) > 100 else ''} length={len(transcript)}")
                                    pass
                                    # テキストを外部queueに送信
                                    text_data = {
                                        "text": transcript
                                    }

                                    # テキストをサーバーに送信
                                    try:
                                        await self.テキスト受信Ｑ.put(text_data)
                                    except Exception as e:
                                        logger.warning(f"テキスト送信エラー: {e}")

                            # テキスト出力（textモダリティ）
                            elif msg_type in ("response.output_text.delta", "response.text.delta"):
                                delta = response_data.get('delta') or ""
                                if delta:
                                    text_buffer += delta
                            elif msg_type in ("response.output_text.done", "response.text.done"):
                                if text_buffer and self.テキスト受信Ｑ:
                                    try:
                                        await self.テキスト受信Ｑ.put({"text": text_buffer})
                                    except Exception as e:
                                        logger.warning(f"テキスト送信エラー(done): {e}")
                                text_buffer = ""

                            # ユーザー音声認識完了
                            elif msg_type == "conversation.item.input_audio_transcription.completed":
                                transcript = response_data.get('transcript')
                                # logger.info(f"ユーザー音声: {transcript}")
                                pass

                            # Function Call処理
                            elif msg_type == "response.function_call_arguments.done":
                                await self._openai_function_call処理(response_data)

                            # その他の応答タイプ（ログ削減）
                            elif msg_type in [
                                "session.created", "session.updated", "response.created",
                                "conversation.item.created", "rate_limits.updated",
                                "response.output_item.added", "response.audio.done",
                                "response.content_part.added", "response.content_part.done",
                                "response.output_item.done", "response.done",
                                "input_audio_buffer.speech_started",
                                "input_audio_buffer.speech_stopped",
                                "input_audio_buffer.committed",
                                "response.audio_transcript.delta",
                            ]:
                                pass  # 正常な応答タイプはログ出力しない
                            else:
                                logger.warning(f"未知の応答タイプ: {msg_type}")

                        self.live_lasttime = time.time()

                        # データ取得時の高速処理用sleep（パフォーマンス最適化）
                        # await asyncio.sleep(0.00)  # データ有：高速処理

                except (asyncio.TimeoutError, WebSocketTimeoutException):
                    # タイムアウト（正常）- セッション生存確認＋キープアライブ確認
                    if loop_count % 40 == 1:  # 200秒間隔でログ出力
                        # logger.info(f"セッション生存確認: OK (ループ{loop_count})")
                        pass

                    # タイムアウト時のキープアライブ確認・処理
                    await self._キープアライブ確認()

                except Exception as e:
                    # WebSocketクローズコード1001（Going Away）は正常終了として扱う
                    error_str = str(e)
                    if "(1001," in error_str or "going away" in error_str.lower():
                        # logger.info(f"WebSocket正常クローズ検出: {error_str}")
                        pass
                        # エラーフラグは設定せずループを抜ける
                        break

                    # その他のエラー → 詳細ログとエラーフラグ設定
                    logger.error(f"受信エラー詳細:")
                    logger.error(f"  エラータイプ: {type(e).__name__}")
                    logger.error(f"  エラーメッセージ: {str(e)}")
                    # logger.error(f"  ループ回数: {loop_count}")  # パフォーマンス最適化
                    # logger.error(f"  セッション存在: {self.live_session is not None}")  # パフォーマンス最適化
                    # logger.error(f"  中断停止フラグ: {self.中断停止フラグ}")  # パフォーマンス最適化
                    self.エラーフラグ = True
                    break

        except Exception as e:
            logger.error(f"受信ワーカーエラー詳細:")
            logger.error(f"  エラータイプ: {type(e).__name__}")
            logger.error(f"  エラーメッセージ: {str(e)}")
            # logger.error(f"  総ループ数: {loop_count}")  # パフォーマンス最適化
            self.エラーフラグ = True
        finally:
            # セッション開始時刻とIDは親ワーカーから参照
            # 正常終了（中断停止フラグがTrueでエラーフラグがFalse）の場合は情報ログ
            if self.中断停止フラグ and not self.エラーフラグ:
                # logger.info(f"受信ワーカー:正常終了")  # パフォーマンス最適化
                pass
            else:
                # エラー終了の場合のみエラーログ
                session_duration = time.time() - self.session_start_time
                logger.error(f"受信ワーカー:終了 (ID:{self.セッションID_internal}, セッション時間{session_duration:.0f}秒) - 中断停止フラグ={self.中断停止フラグ}, エラーフラグ={self.エラーフラグ}, live_session={self.live_session is not None}")
            pass

    async def _設定構成作成(self):
        """設定構成を作成（OpenAI Realtime api形式）"""
        try:
            # logger.info("設定構成作成開始")
            pass

            # システム指示
            instructions = SYSTEM_INSTRUCTION

            # システム設計資料を取得してシステム指示に追加
            if self.parent_manager and hasattr(self.parent_manager, '_システム設計取得'):
                try:
                    システム設計内容 = await self.parent_manager._システム設計取得()
                    if システム設計内容 and len(システム設計内容.strip()) > 0:
                        instructions += "\n\n【システム設計】\n"
                        instructions += "``` 設計内容\n"
                        instructions += システム設計内容
                        instructions += "\n```\n"

                        # logger.info(f"システム設計追加: {len(システム設計内容)}文字")
                        pass
                except Exception as e:
                    logger.warning(f"システム設計取得エラー: {e}")

            # 過去の会話履歴を取得してシステム指示に追加
            if self.parent_manager and hasattr(self.parent_manager, '_履歴データ取得'):
                try:
                    履歴データ = await self.parent_manager._履歴データ取得()
                    if 履歴データ and len(履歴データ) > 0:
                        instructions += "\n\n【過去の会話履歴】\n"
                        for 履歴項目 in 履歴データ:
                            message_type = 履歴項目.メッセージタイプ
                            message_content = 履歴項目.メッセージ内容

                            # メッセージタイプに応じて形式を調整（3行形式）
                            if message_type == "input_text":
                                instructions += f"```user\n{message_content}\n```\n"
                            elif message_type == "output_text":
                                instructions += f"```assistant\n{message_content}\n```\n"
                            elif message_type == "recognition_input":
                                instructions += f"```user [音声入力]\n{message_content}\n```\n"
                            elif message_type == "recognition_output":
                                instructions += f"```assistant [音声出力]\n{message_content}\n```\n"
                            else:
                                instructions += f"```{message_type}\n{message_content}\n```\n"

                        # logger.info(f"会話履歴追加: {len(履歴データ)}件")
                        pass
                except Exception as e:
                    logger.warning(f"会話履歴取得エラー: {e}")

            # logger.info(f"システム指示長: {len(instructions)} 文字")
            pass

            # OpenAI Realtime api形式のセッション設定を返す
            session_config = {
                "modalities": ["audio", "text"],
                "instructions": instructions,
                "voice": self.LIVE_VOICE,
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "silence_duration_ms": 1500,
                },
            }

            # ツール呼び出し機能を追加
            if self.tool_instance is not None:
                try:
                    tools = []
                    if hasattr(self.tool_instance, 'ツールインスタンス辞書'):
                        for ツール名, ツール in self.tool_instance.ツールインスタンス辞書.items():
                            try:
                                定義 = ツール.get_tool_definition()
                            except Exception:
                                定義 = None
                            if not 定義:
                                continue
                            tools.append({
                                "type": "function",
                                "name": 定義.get("name", ツール名),
                                "description": 定義.get("description", ""),
                                "parameters": 定義.get("parameters", {}),
                            })
                    if tools:
                        session_config["tools"] = tools
                        session_config["tool_choice"] = "auto"
                        # logger.info(f"ツール定義追加: {len(tools)}個")
                        pass
                except Exception as e:
                    logger.warning(f"ツール呼び出し機能取得エラー: {e}")

            # logger.info("設定構成作成完了")
            pass
            return session_config

        except Exception as e:
            logger.error(f"設定構成作成エラー: {type(e).__name__}: {e}")
            # エラー時は最小設定で復旧を試行
            logger.warning("最小設定で復旧試行")
            return {
                "modalities": ["audio", "text"],
                "instructions": "あなたは賢いアシスタントです。",
                "voice": self.LIVE_VOICE,
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "silence_duration_ms": 1500,
                },
            }

    async def _openai_function_call処理(self, response_data: dict):
        """OpenAI Function Call処理"""
        try:
            f_id = response_data.get('call_id')
            f_name = response_data.get('name')
            f_kwargs = response_data.get('arguments')

            if self.tool_instance and hasattr(self.tool_instance, 'execute_tool_call'):
                # パラメータ処理（文字列の場合はJSON変換）
                if isinstance(f_kwargs, str):
                    try:
                        f_args_dict = json.loads(f_kwargs)
                    except Exception:
                        f_args_dict = {}
                else:
                    f_args_dict = f_kwargs if isinstance(f_kwargs, dict) else {}

                # パラメータを20文字制限、改行エスケープ
                f_kwargs_full = json.dumps(f_args_dict, ensure_ascii=False)
                f_kwargs_escaped = f_kwargs_full.replace('\n', '\\n').replace('\r', '\\r')
                f_kwargs_short = f_kwargs_escaped[:20] + ("..." if len(f_kwargs_escaped) > 20 else "")

                # ツール実行（共通インターフェース）
                result = await self.tool_instance.execute_tool_call(f_name, f_args_dict)

                # リアルタイム処理最適化：ツール名を行内に埋め込み、パラメータ・結果を別行表示
                result_escaped = str(result).replace('\n', '\\n').replace('\r', '\\r')
                result_short = result_escaped[:20] + ("..." if len(result_escaped) > 20 else "")
                logger.info(f"Tool[{f_name}] Request: {f_kwargs_short}")
                logger.info(f"Tool[{f_name}] Result: {result_short}")

                # 結果送信（WebSocket送信を非同期化）
                result_msg = {
                    "type": "conversation.item.create",
                    "item": {
                        "type": "function_call_output",
                        "call_id": f_id,
                        "output": str(result),
                    },
                }
                await asyncio.to_thread(self.ws_session.send, json.dumps(result_msg))

                # 応答生成指示（WebSocket送信を非同期化）
                response_msg = {"type": "response.create"}
                await asyncio.to_thread(self.ws_session.send, json.dumps(response_msg))

        except Exception as e:
            logger.error(f"ツール呼び出し処理エラー: {e}")

    
    async def _キープアライブ確認(self):
        """アイドル時のキープアライブ確認・処理（1分送受信なしで1秒送信）"""
        current_time = time.time()
        time_since_last_communicate = current_time - self.live_lasttime
        
        # デバッグ: キープアライブ判定状況を確認
        # logger.info(f"キープアライブ判定: 無通信{time_since_last_communicate:.1f}秒 (閾値:{KEEPALIVE_INTERVAL}秒)")
        
        # 1分無通信でキープアライブ送信
        if time_since_last_communicate >= KEEPALIVE_INTERVAL:
            try:
                import numpy as np

                # 1秒間のキープアライブノイズ生成
                samples = int(KEEPALIVE_SAMPLE_RATE * KEEPALIVE_DURATION)
                noise_data = np.random.randint(-KEEPALIVE_NOISE_LEVEL, KEEPALIVE_NOISE_LEVEL, samples, dtype=np.int16)
                noise_bytes = noise_data.tobytes()

                # キープアライブ送信
                await self.音声送信(noise_bytes)
                logger.info(f"キープアライブ送信: 無通信{time_since_last_communicate:.1f}秒")

            except Exception as e:
                logger.error(f"キープアライブエラー: {e}")
                # キープアライブ送信失敗は接続断を意味するため、エラーフラグを設定して再接続を促す
                self.エラーフラグ = True
        else:
            # アイドル時は0.25秒待機
            await asyncio.sleep(0.25)
    
    
    
    # ===== ステータス確認メソッド =====
    
    def 接続状態確認(self) -> dict:
        """LiveAI接続状態を確認"""
        return {
            "liveai_status": {
                "session_active": self.live_session is not None,
                "client_initialized": self.ws_session is not None,
                "live_ai": self.LIVE_AI,
                "model": self.LIVE_MODEL,
                "voice": self.LIVE_VOICE,
                "中断停止フラグ": self.中断停止フラグ,
                "エラーフラグ": self.エラーフラグ,
                "live_lasttime": self.live_lasttime,
                "time_since_last_communicate": time.time() - self.live_lasttime
            },
            "サーバー連携": {
                "audio_queue": self.音声受信Ｑ is not None,
                "text_queue": self.テキスト受信Ｑ is not None,
            },
            "functions": {
                "instance_initialized": self.tool_instance is not None,
                "available_functions": list(self.tool_instance.tool_functions.keys()) if self.tool_instance else []
            },
            "openai_sending": "リアルタイム直接送信"
        }

    
    
    
    
    

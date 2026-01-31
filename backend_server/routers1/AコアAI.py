# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

"""
AコアAI APIエンドポイント
WebSocketベースのセッション管理とストリーミング処理
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from pydantic import BaseModel
from typing import Dict, Optional
import uuid
import json
import asyncio
import os
import sys
import base64
from datetime import datetime
import time
import database
import crud1 as crud
import models1 as models

# WebSocket接続管理をインポート
# backend_serverディレクトリをパスに追加
現在ディレクトリ = os.path.dirname(os.path.abspath(__file__))
バックエンドディレクトリ = os.path.dirname(現在ディレクトリ)
if バックエンドディレクトリ not in sys.path:
    sys.path.insert(0, バックエンドディレクトリ)

from log_config import get_logger

# ロガー取得
logger = get_logger(__name__)

try:
    from ws_manager import ws_manager, SessionConnection
    from AコアAI.streaming import StreamingProcessor
    from AコアAI.recognition import Recognition
    from AコアAI.audio_processing import 音声入力データ処理, 統合音声分離ワーカー
    from AコアAI.backup import バックアップ実行
    from AコアAI.chat import Chat
    from AコアAI.code import CodeAgent
    from AコアAI.live import Live
    logger.info("WebSocketマネージャーをインポートしました")
except Exception as e:
    logger.exception("WebSocketマネージャーのインポートエラー: %s", e)
    raise

router = APIRouter()

# 後方互換性のため、REST API用のセッションデータも保持
セッション情報: Dict[str, dict] = {}


def 保存_会話履歴(
    ソケットID: str,
    チャンネル: int,
    メッセージ識別: str,
    メッセージ内容: Optional[str] = None,
    ファイル名: Optional[str] = None,
    サムネイル画像: Optional[str] = None
):
    """会話履歴を保存（AコアAI用）"""
    db = database.SessionLocal()
    try:
        シーケンス = crud.get_next_sequence(db, ソケットID)
        crud.create_会話履歴(
            db,
            ソケットID=ソケットID,
            シーケンス=シーケンス,
            チャンネル=チャンネル,
            メッセージ識別=メッセージ識別,
            メッセージ内容=メッセージ内容,
            ファイル名=ファイル名,
            サムネイル画像=サムネイル画像,
            認証情報={"利用者ID": "AコアAI", "利用者名": "AコアAI"}
        )
    finally:
        db.close()


def 取得_会話履歴一覧(
    ソケットID: str,
    チャンネル: int = 0
):
    """会話履歴一覧を取得（シーケンス昇順）"""
    db = database.SessionLocal()
    try:
        items = (
            db.query(models.A会話履歴)
            .filter(models.A会話履歴.ソケットID == ソケットID)
            .filter(models.A会話履歴.チャンネル == チャンネル)
            .order_by(models.A会話履歴.シーケンス.asc())
            .all()
        )
        return items
    finally:
        db.close()

def 取得_コードベース選択肢(アプリ設定=None) -> dict:
    """コードベースパス選択肢を取得"""
    options = {}
    try:
        path_conf = getattr(アプリ設定, 'path', None) if アプリ設定 else None
        external_root_dic = getattr(path_conf, 'external_root_dic', None)
        if isinstance(external_root_dic, dict) and external_root_dic:
            # _AIDIY.md を含むプロジェクト一覧を相対パスに変換
            for 表示名, 絶対パス in external_root_dic.items():
                try:
                    相対パス = os.path.relpath(絶対パス, バックエンドディレクトリ)
                    相対パス = 相対パス.replace('\\', '/')
                    if not 相対パス.endswith('/'):
                        相対パス += '/'
                    options[相対パス] = 表示名
                except Exception:
                    continue
        # external_root_path とその親も探索（_AIDIY.md を含むフォルダ）
        external_root_path = getattr(path_conf, 'external_root_path', None) if path_conf else None
        探索ルート = []
        if external_root_path:
            探索ルート.append(external_root_path)
            親 = os.path.abspath(os.path.join(external_root_path, '..'))
            if 親 and 親 not in 探索ルート:
                探索ルート.append(親)

        def 追加探索(root_dir: str) -> None:
            root_dir = root_dir.replace('\\', '/').rstrip('/')
            if not root_dir or not os.path.isdir(root_dir):
                return
            # ルート自身
            root_marker = os.path.join(root_dir, '_AIDIY.md')
            if os.path.isfile(root_marker):
                表示名 = os.path.basename(root_dir) or 'project_root'
                try:
                    相対パス = os.path.relpath(root_dir, バックエンドディレクトリ).replace('\\', '/')
                    if not 相対パス.endswith('/'):
                        相対パス += '/'
                    options.setdefault(相対パス, 表示名)
                except Exception:
                    pass
            # ルート直下と1階層下
            try:
                for entry in os.scandir(root_dir):
                    if not entry.is_dir():
                        continue
                    candidates = [entry.path]
                    try:
                        for sub_entry in os.scandir(entry.path):
                            if sub_entry.is_dir():
                                candidates.append(sub_entry.path)
                    except (PermissionError, OSError):
                        pass
                    for path in candidates:
                        marker = os.path.join(path, '_AIDIY.md')
                        if os.path.isfile(marker):
                            表示名 = os.path.basename(path)
                            try:
                                相対パス = os.path.relpath(path, バックエンドディレクトリ).replace('\\', '/')
                                if not 相対パス.endswith('/'):
                                    相対パス += '/'
                                options.setdefault(相対パス, 表示名)
                            except Exception:
                                continue
            except (PermissionError, OSError):
                return

        for root in 探索ルート:
            追加探索(root)
    except Exception:
        options = {}

    if not options:
        # フォールバック: 従来の固定候補
        候補 = []
        候補.append(("../", "プロジェクトルート"))
        候補.append(("../backend_server", "backend_server"))
        候補.append(("../frontend_server", "frontend_server"))
        候補.append(("../docs", "docs"))

        for 相対パス, 表示名 in 候補:
            実パス = os.path.normpath(os.path.join(バックエンドディレクトリ, 相対パス))
            if os.path.isdir(実パス):
                options[相対パス] = 表示名

    if not options:
        options["../"] = "プロジェクトルート"

    return options




async def 送信_会話履歴(
    接続: SessionConnection,
    ソケットID: str,
    チャンネル: int = 0
):
    """会話履歴をソケット送出（シーケンス昇順）"""
    履歴一覧 = 取得_会話履歴一覧(ソケットID, チャンネル=チャンネル)
    for item in 履歴一覧:
        payload = {
            "ソケットID": item.ソケットID,
            "チャンネル": item.チャンネル,
            "メッセージ識別": item.メッセージ識別,
            "メッセージ内容": item.メッセージ内容,
            "ファイル名": item.ファイル名,
            "サムネイル画像": item.サムネイル画像
        }
        await 接続.send_json(payload)
    logger.info(f"会話履歴送信: チャンネル={チャンネル}, 件数={len(履歴一覧)}")

class 初期化リクエスト(BaseModel):
    ソケットID: str = ""
    セッションID: str = ""


class 初期化レスポンス(BaseModel):
    status: str
    message: str
    data: dict


@router.post("/core/AコアAI/初期化", response_model=初期化レスポンス)
async def 初期化(http_request: Request, request: 初期化リクエスト):
    """
    AコアAI画面の初期化
    ソケットIDがなければ新規生成、あれば既存データを返す
    """
    try:
        ソケットID = request.ソケットID or request.セッションID

        # ソケットIDがない場合は新規生成
        if not ソケットID:
            ソケットID = ws_manager.generate_socket_id()
            バックアップ実行(getattr(http_request.app, "conf", None), backend_dir=バックエンドディレクトリ)

        # セッションを確実に作成（存在しなければ新規）
        ws_manager.ensure_session(ソケットID, app_conf=getattr(http_request.app, "conf", None))

        return 初期化レスポンス(
            status="OK",
            message="初期化成功",
            data={
                "ソケットID": ソケットID
            }
        )

    except Exception as e:
        return 初期化レスポンス(
            status="NG",
            message=f"初期化エラー: {str(e)}",
            data={}
        )



@router.post("/core/AコアAI/セッション一覧")
async def セッション一覧():
    """
    デバッグ用：現在のセッション一覧を取得（REST + WebSocket両方）
    """
    return {
        "status": "OK",
        "message": "セッション一覧",
        "data": {
            "REST_セッション数": len(セッション情報),
            "REST_セッションID一覧": list(セッション情報.keys()),
            "WebSocket_セッション数": ws_manager.get_session_count(),
            "WebSocket_セッション一覧": ws_manager.get_session_list()
        }
    }


class モデル情報取得リクエスト(BaseModel):
    ソケットID: str


class モデル設定リクエスト(BaseModel):
    ソケットID: str
    モデル設定: dict
    再起動要求: Optional[dict] = None

@router.post("/core/AコアAI/モデル情報/取得")
async def モデル情報取得(http_request: Request, request: モデル情報取得リクエスト):
    """
    ソケットのAIモデル情報と設定を取得
    """
    try:
        ソケットID = request.ソケットID

        if not ソケットID:
            return {
                "status": "NG",
                "message": "ソケットIDが指定されていません",
                "data": {}
            }

        # WebSocketマネージャーから接続を取得
        接続 = ws_manager.get_session(ソケットID)

        if not 接続:
            return {
                "status": "NG",
                "message": f"ソケットID {ソケットID} が見つかりません",
                "data": {}
            }

        # http_request.app.confから利用可能なモデル一覧を取得
        利用可能モデル = {}
        if hasattr(http_request.app, 'conf') and http_request.app.conf and http_request.app.conf.models:
            モデル一覧 = http_request.app.conf.models
            利用可能モデル = {
                "chat_models": モデル一覧.get_chat_models(),
                "live_models": モデル一覧.get_live_models(),
                "live_voices": モデル一覧.get_live_voices(),
                "code_models": モデル一覧.get_code_models(),
            }

        # ソケットのモデル設定を取得
        現在設定 = 接続.モデル設定

        return {
            "status": "OK",
            "message": "モデル情報取得成功",
            "data": {
                "available_models": 利用可能モデル,
                "モデル設定": 現在設定,
                "external_root_dic": 取得_コードベース選択肢(http_request.app.conf if hasattr(http_request.app, 'conf') else None)
            }
        }

    except Exception as e:
        logger.exception("モデル情報取得エラー")
        return {
            "status": "NG",
            "message": f"モデル情報取得エラー: {str(e)}",
            "data": {}
        }


@router.post("/core/AコアAI/モデル情報/設定")
async def モデル情報設定(http_request: Request, request: モデル設定リクエスト):
    """
    ソケットのAIモデル設定を更新（セッション内のみ、ファイル保存しない）
    """
    try:
        ソケットID = request.ソケットID
        設定 = request.モデル設定
        再起動要求 = request.再起動要求 or {}

        if not ソケットID:
            return {
                "status": "NG",
                "message": "ソケットIDが指定されていません"
            }

        # WebSocketマネージャーから接続を取得
        接続 = ws_manager.get_session(ソケットID)

        if not 接続:
            return {
                "status": "NG",
                "message": f"ソケットID {ソケットID} が見つかりません"
            }

        # 設定可能なキーのホワイトリスト（セキュリティのため）
        許可キー = {
            # ChatAI設定
            "CHAT_AI", "CHAT_GEMINI_MODEL", "CHAT_FREEAI_MODEL", "CHAT_OPENRT_MODEL",
            # LiveAI設定
            "LIVE_AI", "LIVE_GEMINI_MODEL", "LIVE_GEMINI_VOICE",
            "LIVE_FREEAI_MODEL", "LIVE_FREEAI_VOICE",
            "LIVE_OPENAI_MODEL", "LIVE_OPENAI_VOICE",
            # CodeAI設定
            "CODE_AI1", "CODE_AI2", "CODE_AI3", "CODE_AI4",
            "CODE_AI1_MODEL", "CODE_AI2_MODEL", "CODE_AI3_MODEL", "CODE_AI4_MODEL",
            "CODE_CLAUDE_SDK_MODEL", "CODE_CLAUDE_CLI_MODEL",
            "CODE_COPILOT_CLI_MODEL", "CODE_GEMINI_CLI_MODEL", "CODE_CODEX_CLI_MODEL",
            "CODE_BASE_PATH",
            "CODE_MAX_TURNS", "CODE_PLAN", "CODE_VERIFY",
        }

        # ホワイトリストにあるキーのみをフィルタリング
        許可設定 = {k: v for k, v in 設定.items() if k in 許可キー}

        if not 許可設定:
            return {
                "status": "NG",
                "message": "有効な設定項目がありません"
            }

        # ソケットのモデル設定を更新（ファイル保存はしない）
        接続.update_model_settings(許可設定, manager=ws_manager)

        # 既存プロセッサに反映（即時反映）
        try:
            if hasattr(接続, "chat_processor") and 接続.chat_processor:
                chat_ai = 接続.モデル設定.get("CHAT_AI", "")
                chat_model = ""
                if chat_ai == "openrt":
                    chat_model = 接続.モデル設定.get("CHAT_OPENRT_MODEL", "")
                elif chat_ai in ("gemini", "freeai"):
                    key = "CHAT_FREEAI_MODEL" if chat_ai == "freeai" else "CHAT_GEMINI_MODEL"
                    chat_model = 接続.モデル設定.get(key, "")
                接続.chat_processor.AI_NAME = chat_ai
                接続.chat_processor.AI_MODEL = chat_model
                if hasattr(接続.chat_processor, "_select_ai_module"):
                    接続.chat_processor.AIモジュール = 接続.chat_processor._select_ai_module()
                接続.chat_processor.AIインスタンス = None

            if hasattr(接続, "code_agent_processors") and 接続.code_agent_processors:
                for idx, agent in enumerate(接続.code_agent_processors, start=1):
                    ai_key = f"CODE_AI{idx}"
                    model_key = f"CODE_AI{idx}_MODEL"
                    agent.AI_NAME = 接続.モデル設定.get(ai_key, "")
                    agent.AI_MODEL = 接続.モデル設定.get(model_key, "")
                    if hasattr(agent, "_select_ai_module"):
                        agent.AIモジュール = agent._select_ai_module()
                    agent.AIインスタンス = None

            if hasattr(接続, "live_processor") and 接続.live_processor:
                live_ai = 接続.モデル設定.get("LIVE_AI", "")
                live_model = ""
                live_voice = ""
                if live_ai in ("gemini_live", "freeai_live"):
                    model_key = "LIVE_FREEAI_MODEL" if live_ai == "freeai_live" else "LIVE_GEMINI_MODEL"
                    voice_key = "LIVE_FREEAI_VOICE" if live_ai == "freeai_live" else "LIVE_GEMINI_VOICE"
                    live_model = 接続.モデル設定.get(model_key, "")
                    live_voice = 接続.モデル設定.get(voice_key, "")
                elif live_ai == "openai_live":
                    live_model = 接続.モデル設定.get("LIVE_OPENAI_MODEL", "")
                    live_voice = 接続.モデル設定.get("LIVE_OPENAI_VOICE", "")
                接続.live_processor.AI_NAME = live_ai
                接続.live_processor.AI_MODEL = live_model
                接続.live_processor.AI_VOICE = live_voice
                if hasattr(接続.live_processor, "_select_ai_module"):
                    接続.live_processor.AIモジュール = 接続.live_processor._select_ai_module()
                接続.live_processor.AIインスタンス = None
                try:
                    await 接続.live_processor.開始()
                except Exception:
                    logger.exception("LiveAI再開始に失敗しました")
        except Exception:
            logger.exception("モデル設定の反映に失敗しました")

        # 再起動要求があればフラグファイルを作成
        try:
            reboot1 = bool(再起動要求.get("reboot1"))
            reboot2 = bool(再起動要求.get("reboot2"))
            if reboot1:
                with open(os.path.join(バックエンドディレクトリ, "temp", "reboot1.txt"), "w", encoding="utf-8") as f:
                    f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            if reboot2:
                with open(os.path.join(バックエンドディレクトリ, "temp", "reboot2.txt"), "w", encoding="utf-8") as f:
                    f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            if reboot1 or reboot2:
                logger.info(f"再起動要求受信: reboot1={reboot1} reboot2={reboot2}")
        except Exception:
            logger.exception("再起動要求の処理に失敗しました")

        return {
            "status": "OK",
            "message": f"{len(許可設定)}件の設定を更新しました（セッション内のみ）"
        }

    except Exception as e:
        logger.exception("モデル設定エラー")
        return {
            "status": "NG",
            "message": f"モデル設定エラー: {str(e)}"
        }

@router.websocket("/ws/AコアAI")
async def websocket_endpoint(WebSocket接続: WebSocket):
    """
    AコアAI WebSocketエンドポイント
    セッション確立、状態同期、ストリーミング処理を行う
    """
    ソケットID = None
    ソケット番号 = -1

    try:
        await WebSocket接続.accept()
        logger.info("WebSocket /ws/AコアAI 接続受付")

        # 初回メッセージでセッションID・ソケット番号を受信
        try:
            初期データ = await WebSocket接続.receive_json()
            クライアントソケットID = 初期データ.get("ソケットID") or 初期データ.get("セッションID")
            ソケット番号 = 初期データ.get("ソケット番号")
            if ソケット番号 is None:
                ソケット番号 = 初期データ.get("チャンネル")
            if ソケット番号 is None:
                ソケット番号 = -1
            logger.debug(f"接続要求受信 (ソケットID: {クライアントソケットID}, ソケット番号: {ソケット番号})")
        except Exception as e:
            logger.error(f"初回メッセージ受信エラー: {e}")
            クライアントソケットID = None
            ソケット番号 = -1

        # WebSocket接続を登録（accept済み）
        ソケットID = await ws_manager.connect(
            WebSocket接続,
            socket_id=クライアントソケットID,
            socket_no=int(ソケット番号),
            app_conf=getattr(WebSocket接続.app, "conf", None),
            accept_in_connect=False
        )

        セッション = ws_manager.get_session(ソケットID)
        if not セッション:
            raise RuntimeError("セッションの作成に失敗しました")

        # 初回のみプロセッサを起動
        if セッション.streaming_processor is None and int(ソケット番号) == -1:
            セッション.streaming_processor = StreamingProcessor(ソケットID, セッション)
            await セッション.streaming_processor.start()

        if セッション.recognition_processor is None:
            セッション.recognition_processor = Recognition(ソケットID, セッション, 保存_会話履歴)
            await セッション.recognition_processor.開始()

        if not hasattr(セッション, "chat_processor"):
            実行パス = セッション.モデル設定.get("CODE_BASE_PATH", "")
            チャット保存基準パス = バックエンドディレクトリ
            chat_ai = セッション.モデル設定.get("CHAT_AI", "")
            chat_model = ""
            if chat_ai == "openrt":
                chat_model = セッション.モデル設定.get("CHAT_OPENRT_MODEL", "")
            elif chat_ai in ("gemini", "freeai"):
                key = "CHAT_FREEAI_MODEL" if chat_ai == "freeai" else "CHAT_GEMINI_MODEL"
                chat_model = セッション.モデル設定.get(key, "")
            セッション.chat_processor = Chat(
                親=WebSocket接続.app,
                ソケットID=ソケットID,
                チャンネル=0,
                絶対パス=チャット保存基準パス,
                AI_NAME=chat_ai,
                AI_MODEL=chat_model,
                接続=セッション,
                保存関数=保存_会話履歴,
            )
            await セッション.chat_processor.開始()

        if not hasattr(セッション, "code_agent_processors"):
            セッション.code_agent_processors = []
            実行パス = セッション.モデル設定.get("CODE_BASE_PATH", "")
            for i in range(1, 5):
                ai_key = f"CODE_AI{i}"
                model_key = f"CODE_AI{i}_MODEL"
                agent = CodeAgent(
                    親=WebSocket接続.app,
                    ソケットID=ソケットID,
                    チャンネル=i,
                    絶対パス=実行パス,
                    AI_NAME=セッション.モデル設定.get(ai_key, ""),
                    AI_MODEL=セッション.モデル設定.get(model_key, ""),
                    接続=セッション,
                    保存関数=保存_会話履歴,
                )
                await agent.開始()
                セッション.code_agent_processors.append(agent)

        if not hasattr(セッション, "live_processor"):
            live_ai = セッション.モデル設定.get("LIVE_AI", "")
            live_model = ""
            live_voice = ""
            if live_ai in ("gemini_live", "freeai_live"):
                model_key = "LIVE_FREEAI_MODEL" if live_ai == "freeai_live" else "LIVE_GEMINI_MODEL"
                voice_key = "LIVE_FREEAI_VOICE" if live_ai == "freeai_live" else "LIVE_GEMINI_VOICE"
                live_model = セッション.モデル設定.get(model_key, "")
                live_voice = セッション.モデル設定.get(voice_key, "")
            elif live_ai == "openai_live":
                live_model = セッション.モデル設定.get("LIVE_OPENAI_MODEL", "")
                live_voice = セッション.モデル設定.get("LIVE_OPENAI_VOICE", "")
            セッション.live_processor = Live(
                親=WebSocket接続.app,
                ソケットID=ソケットID,
                チャンネル=0,
                絶対パス=実行パス,
                AI_NAME=live_ai,
                AI_MODEL=live_model,
                AI_VOICE=live_voice,
                接続=セッション,
                保存関数=保存_会話履歴,
            )
            await セッション.live_processor.開始()

        if セッション.audio_split_task is None or セッション.audio_split_task.done():
            セッション.audio_split_task = asyncio.create_task(統合音声分離ワーカー(セッション))

        # 出力ソケット接続時にwelcome_infoと履歴を送信
        if int(ソケット番号) in [0, 1, 2, 3, 4]:
            ウェルカムメッセージ = {
                0: "ようこそ AiDiy へ",
                1: "コードエージェント1 です。",
                2: "コードエージェント2 です。",
                3: "コードエージェント3 です。",
                4: "コードエージェント4 です。"
            }
            if int(ソケット番号) in ウェルカムメッセージ:
                await セッション.send_to_channel(int(ソケット番号), {
                    "ソケットID": ソケットID,
                    "チャンネル": int(ソケット番号),
                    "メッセージ識別": "welcome_info",
                    "メッセージ内容": ウェルカムメッセージ[int(ソケット番号)],
                    "ファイル名": None,
                    "サムネイル画像": None
                })
                logger.info(f"welcome_info送信: チャンネル={ソケット番号}")

            await asyncio.sleep(0.1)
            try:
                await 送信_会話履歴(セッション, ソケットID, チャンネル=int(ソケット番号))
            except Exception as e:
                logger.exception(f"会話履歴送信エラー: {e}")

        # メインループ：メッセージを受信し処理（入力ソケットのみ）
        while True:
            try:
                受信データ = await WebSocket接続.receive_json()
                メッセージ識別 = 受信データ.get("メッセージ識別")

                if int(ソケット番号) != -1:
                    continue

                if メッセージ識別 == "operations":
                    内容 = 受信データ.get("メッセージ内容", {})
                    画面 = 内容.get("画面", {})
                    ボタン = 内容.get("ボタン", {})
                    セッション.update_state(画面, ボタン, manager=ws_manager)

                elif メッセージ識別 == "input_text":
                    メッセージ内容 = 受信データ.get("メッセージ内容") or 受信データ.get("text", "")
                    ファイル名 = 受信データ.get("ファイル名") or ""
                    入力チャンネル = 受信データ.get("チャンネル", -1)
                    出力先チャンネル = 受信データ.get("出力先チャンネル", 0)
                    logger.debug(f"テキスト受信 (入力={入力チャンネル}, 出力先={出力先チャンネル}, {ソケットID}): {メッセージ内容}")

                    if セッション.is_channel_processing(出力先チャンネル):
                        await セッション.send_to_channel(出力先チャンネル, {
                            "ソケットID": ソケットID,
                            "チャンネル": 出力先チャンネル,
                            "メッセージ識別": "output_text",
                            "メッセージ内容": f"⏳ チャンネル{出力先チャンネル}は処理中です。キューに追加しました...",
                            "ファイル名": None,
                            "サムネイル画像": None
                        })
                        logger.info(f"チャンネル{出力先チャンネル}処理中のため、キューに追加: {ソケットID}")
                        continue

                    セッション.set_channel_processing(出力先チャンネル, True)

                    await セッション.send_to_channel(出力先チャンネル, {
                        "ソケットID": ソケットID,
                        "チャンネル": 出力先チャンネル,
                        "メッセージ識別": "input_text",
                        "メッセージ内容": メッセージ内容,
                        "ファイル名": None,
                        "サムネイル画像": None
                    })

                    保存_会話履歴(
                        ソケットID=ソケットID,
                        チャンネル=出力先チャンネル,
                        メッセージ識別="input_text",
                        メッセージ内容=メッセージ内容,
                        ファイル名=None,
                        サムネイル画像=None
                    )

                    受信データ["チャンネル"] = 出力先チャンネル

                    try:
                        if 出力先チャンネル == 0:
                            ファイル名_判定 = ファイル名.lower() if isinstance(ファイル名, str) else ""
                            logger.info(
                                f"input_text分岐判定: socket={ソケットID} channel=0 "
                                f"file='{ファイル名}' live={'live' in ファイル名_判定}"
                            )
                            if "live" in ファイル名_判定:
                                if hasattr(セッション, "live_processor") and セッション.live_processor:
                                    logger.info(f"LiveAI起動要求: socket={ソケットID}")
                                    await セッション.live_processor.開始()
                                    logger.info(f"LiveAIテキスト送信開始: socket={ソケットID}")
                                    await セッション.live_processor.テキスト送信(メッセージ内容)
                                    logger.info(f"LiveAIテキスト送信完了: socket={ソケットID}")
                                else:
                                    logger.warning(f"LiveAI未初期化のためChatへフォールバック ({ソケットID})")
                                    if hasattr(セッション, "chat_processor"):
                                        await セッション.chat_processor.チャット要求(受信データ)
                            elif hasattr(セッション, "chat_processor"):
                                await セッション.chat_processor.チャット要求(受信データ)
                        elif 1 <= 出力先チャンネル <= 4 and hasattr(セッション, 'code_agent_processors'):
                            await セッション.code_agent_processors[出力先チャンネル - 1].コード要求(受信データ)
                    finally:
                        セッション.set_channel_processing(出力先チャンネル, False)

                elif メッセージ識別 == "input_file":
                    メッセージ内容 = 受信データ.get("メッセージ内容") or ""
                    入力チャンネル = 受信データ.get("チャンネル", -1)
                    出力先チャンネル = 受信データ.get("出力先チャンネル", 0)
                    ファイル名 = 受信データ.get("ファイル名")
                    保存ファイル名 = None
                    サムネイル_base64 = None

                    Base64ペイロード = メッセージ内容
                    if Base64ペイロード and "base64," in Base64ペイロード:
                        Base64ペイロード = Base64ペイロード.split("base64,", 1)[1]

                    if Base64ペイロード:
                        try:
                            デコードデータ = base64.b64decode(Base64ペイロード)
                            保存ディレクトリ = os.path.join(バックエンドディレクトリ, "temp", "input")
                            os.makedirs(保存ディレクトリ, exist_ok=True)
                            タイムスタンプ = datetime.now().strftime("%Y%m%d.%H%M%S")
                            安全ファイル名 = os.path.basename(ファイル名) if ファイル名 else "file.bin"
                            保存ファイル名 = f"{タイムスタンプ}.{安全ファイル名}"
                            保存パス = os.path.join(保存ディレクトリ, 保存ファイル名)
                            with open(保存パス, "wb") as f:
                                f.write(デコードデータ)

                            try:
                                from PIL import Image
                                from io import BytesIO
                                image = Image.open(BytesIO(デコードデータ))
                                image = image.convert("RGBA")
                                width, height = image.size
                                if width > 0 and height > 0:
                                    new_width = 320
                                    new_height = int(height * (new_width / width))
                                    thumbnail = image.resize((new_width, new_height), Image.LANCZOS)
                                    buf = BytesIO()
                                    thumbnail.save(buf, format="PNG")
                                    サムネイル_base64 = base64.b64encode(buf.getvalue()).decode("ascii")
                            except Exception as e:
                                logger.info(f"画像ではありません: {e}")
                        except Exception as e:
                            logger.exception(f"ファイル保存エラー: {e}")

                    await セッション.send_to_channel(出力先チャンネル, {
                        "ソケットID": ソケットID,
                        "チャンネル": 出力先チャンネル,
                        "メッセージ識別": "input_file",
                        "メッセージ内容": f"ファイル受信: {ファイル名}" if ファイル名 else "ファイル受信",
                        "ファイル名": f"temp/input/{保存ファイル名}" if 保存ファイル名 else None,
                        "サムネイル画像": サムネイル_base64
                    })

                    保存_会話履歴(
                        ソケットID=ソケットID,
                        チャンネル=出力先チャンネル,
                        メッセージ識別="input_file",
                        メッセージ内容=f"ファイル受信: {ファイル名}" if ファイル名 else "ファイル受信",
                        ファイル名=f"temp/input/{保存ファイル名}" if 保存ファイル名 else None,
                        サムネイル画像=サムネイル_base64
                    )

                    if セッション:
                        セッション.set_channel_processing(出力先チャンネル, True)
                        try:
                            更新済み受信データ = {
                                "ソケットID": ソケットID,
                                "チャンネル": 出力先チャンネル,
                                "メッセージ識別": "input_file",
                                "メッセージ内容": f"ファイル受信: {ファイル名}" if ファイル名 else "ファイル受信",
                                "ファイル名": f"temp/input/{保存ファイル名}" if 保存ファイル名 else None,
                                "サムネイル画像": サムネイル_base64
                            }
                            if 出力先チャンネル == 0 and hasattr(セッション, 'chat_processor'):
                                await セッション.chat_processor.チャット要求(更新済み受信データ)
                            elif 1 <= 出力先チャンネル <= 4 and hasattr(セッション, 'code_agent_processors'):
                                await セッション.code_agent_processors[出力先チャンネル - 1].コード要求(更新済み受信データ)
                        finally:
                            セッション.set_channel_processing(出力先チャンネル, False)

                elif メッセージ識別 == "input_audio":
                    try:
                        base64_audio = 受信データ.get("ファイル名") or ""
                        mime_type = 受信データ.get("メッセージ内容", "audio/pcm")
                        if not base64_audio:
                            continue
                        try:
                            audio_bytes = base64.b64decode(base64_audio)
                        except Exception:
                            audio_bytes = b""
                        if not audio_bytes:
                            continue
                        if セッション:
                            # LiveAI初期化確認（未初期化の場合は再試行）
                            if getattr(セッション, "live_processor", None) and not getattr(セッション.live_processor, "AIインスタンス", None):
                                try:
                                    await セッション.live_processor.開始()
                                except Exception:
                                    logger.exception("LiveAI初期化再試行エラー")
                            # AIインスタンス未初期化でも音声入力データ処理は実行
                            # （audio_processing.pyでAIインスタンスがない場合は送信スキップされる）
                            await 音声入力データ処理(セッション, audio_bytes)
                    except Exception as e:
                        logger.warning(f"音声入力処理エラー: {e}")

                elif メッセージ識別 == "cancel_audio":
                    try:
                        if セッション:
                            セッション.output_audio_paused = True
                            logger.info("音声出力停止")
                    except Exception as e:
                        logger.warning(f"cancel_audio処理エラー: {e}")

                elif メッセージ識別 == "input_image":
                    try:
                        base64_image = 受信データ.get("ファイル名") or ""
                        mime_type = 受信データ.get("メッセージ内容", "image/png")
                        if not base64_image:
                            continue
                        Base64ペイロード = base64_image
                        if "base64," in base64_image:
                            Base64ペイロード = base64_image.split("base64,", 1)[1]
                        try:
                            image_bytes = base64.b64decode(Base64ペイロード)
                        except Exception:
                            image_bytes = b""
                        if not image_bytes:
                            continue
                        try:
                            保存ディレクトリ = os.path.join(バックエンドディレクトリ, "temp", "input")
                            os.makedirs(保存ディレクトリ, exist_ok=True)
                            タイムスタンプ = datetime.now().strftime("%Y%m%d.%H%M%S")
                            保存ファイル名 = f"{タイムスタンプ}.image.png"
                            保存パス = os.path.join(保存ディレクトリ, 保存ファイル名)
                            with open(保存パス, "wb") as f:
                                f.write(image_bytes)
                            logger.info(f"画像保存完了 ({ソケットID}): {保存パス}")
                        except Exception as e:
                            logger.exception(f"画像保存エラー: {e}")
                            continue
                        # LiveAIへ画像送信（大きい画像はLive側でリサイズ）
                        try:
                            if セッション and getattr(セッション, "live_processor", None):
                                await セッション.live_processor.開始()
                                画像形式 = "png"
                                if isinstance(mime_type, str) and "/" in mime_type:
                                    画像形式 = mime_type.split("/", 1)[1].strip() or "png"
                                await セッション.live_processor.画像送信(Base64ペイロード, format=画像形式)
                        except Exception as e:
                            logger.warning(f"LiveAI画像送信エラー: {e}")
                    except Exception as e:
                        logger.warning(f"画像入力処理エラー: {e}")

                else:
                    logger.error(f"不明なメッセージ識別 ({ソケットID}): {メッセージ識別} data={json.dumps(受信データ, ensure_ascii=False)}")

            except WebSocketDisconnect:
                logger.info(f"クライアント切断: {ソケットID} socket={ソケット番号}")
                break
            except Exception as e:
                logger.error(f"メッセージ処理エラー ({ソケットID}): {e}")
                await WebSocket接続.send_json({
                    "メッセージ識別": "error",
                    "ソケットID": ソケットID,
                    "メッセージ内容": str(e)
                })

    except WebSocketDisconnect:
        logger.info(f"接続切断 (初期): {ソケットID}")
    except Exception as e:
        logger.error(f"エラー ({ソケットID}): {e}")
    finally:
        if ソケットID is not None:
            logger.info(f"WebSocket /ws/AコアAI 切断: {ソケットID} socket={ソケット番号}")
            await ws_manager.disconnect(ソケットID, socket_no=ソケット番号)
            logger.debug(f"クリーンアップ完了: {ソケットID}")

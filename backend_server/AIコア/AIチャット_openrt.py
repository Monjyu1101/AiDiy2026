#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

# モジュール名
MODULE_NAME = '_openrt'

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
import queue
import base64
import mimetypes
from typing import Optional, Dict, Any
from pathlib import Path

# api ライブラリ
import openai


class ChatAI:
    """
    OpenRouter Chat api統合クラス（履歴管理 + テキストチャット実装）
    """

    def __init__(self, 親=None, セッションID: str = "", チャンネル: int = 0, 絶対パス: str = None,
                 AI_NAME: str = "openrt", AI_MODEL: str = "google/gemini-2.5-flash",
                 api_key: str = None):
        """初期化"""

        # セッションID・チャンネル
        self.セッションID = セッションID
        self.チャンネル = チャンネル

        # 親参照（セッションマネージャー）
        self.parent_manager = 親
        self.親 = 親

        # apiキー設定
        self.api_key = api_key
        if api_key and api_key[:1] != '<':
            # logger.info("ChatAI: OpenRouter apiキー設定完了")
            pass
        else:
            logger.warning("ChatAI: apiキーが未設定です")

        # モデル設定
        self.chat_ai = AI_NAME
        self.chat_model = AI_MODEL

        # 作業ディレクトリ設定
        if 絶対パス and isinstance(絶対パス, str):
            work_dir = Path(絶対パス)
        else:
            work_dir = Path.cwd()

        self.cwd_str = str(work_dir.resolve())
        # logger.info(f"作業ディレクトリ設定: {self.cwd_str}")
        pass

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

        # 生存状態管理
        self.is_alive = False

        # logger.info(f"初期化:完了 (OpenRouter Chat api設定済み, 履歴管理有効)")
        pass

    async def 開始(self):
        """ChatAI開始（apiクライアント初期化）"""
        try:
            # パラメータで渡されたapiキー・モデル名を優先使用（親からの再取得は不要）
            # 初期化時にすでに設定済み

            # apiクライアント初期化
            if not self.api_key or self.api_key[:1] == '<':
                logger.error("ChatAI: apiキーが設定されていません")
                return False

            try:
                self.client = openai.OpenAI(
                    api_key=self.api_key,
                    base_url="https://openrouter.ai/api/v1",
                )
                self.is_alive = True
                pass
                return True
            except Exception as e:
                logger.error(f"ChatAI: apiクライアント初期化エラー: {e}")
                return False

        except Exception as e:
            logger.error(f"ChatAI開始エラー: {e}")
            return False

    async def 終了(self):
        """ChatAI終了"""
        try:
            self.is_alive = False
            self.client = None
            # logger.info("ChatAI終了")
            pass
            return True
        except Exception as e:
            logger.error(f"ChatAI終了エラー: {e}")
            return False

    async def 実行(self, 要求テキスト: str, テキスト受信処理Ｑ=None, タイムアウト秒数: int = 120,
                   システムプロンプト: str = None, file_path: str = None) -> str:
        """
        ChatAI実行（OpenRouter経由でテキスト生成）

        Args:
            要求テキスト: ユーザーの要求テキスト
            テキスト受信処理Ｑ: ストリーミング用キュー
            タイムアウト秒数: タイムアウト時間
            システムプロンプト: システムプロンプト
            file_path: 添付ファイルの絶対パス（オプション）

        Returns:
            生成されたテキスト
        """
        try:
            if not self.is_alive:
                logger.warning("ChatAI実行:ChatAIが開始されていません")
                return "ChatAIが停止状態です。APIキーの設定を確認、再起動してください。"

            # ファイル添付処理
            image_data = None
            if file_path:
                try:
                    # ファイルの存在確認
                    if not os.path.isfile(file_path):
                        logger.warning(f"ChatAI: ファイルが存在しません {file_path}")
                    else:
                        # MIMEタイプ取得
                        mime_type, _ = mimetypes.guess_type(file_path)

                        # 画像ファイルのみ対応
                        if mime_type and mime_type.startswith('image/'):
                            # base64エンコード
                            with open(file_path, 'rb') as f:
                                image_bytes = f.read()
                                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                                image_data = {
                                    "mime_type": mime_type,
                                    "data": image_base64
                                }
                            logger.info(f"ChatAI: 画像ファイルを添付 {file_path} ({mime_type})")
                        else:
                            # 画像以外のファイル（未対応）
                            logger.warning(f"ChatAI: 画像以外のファイル形式は未対応 {file_path} ({mime_type})")

                except Exception as e:
                    logger.error(f"ChatAI: ファイル添付エラー {e}")

            # 出力ファイルリスト（OpenRouterは画像生成非対応のため常に空）
            output_files = []
            self.last_output_files = output_files

            # タイムアウト監視タスク作成
            タイムアウトフラグ = asyncio.Event()

            async def タイムアウト監視():
                try:
                    await asyncio.sleep(タイムアウト秒数)
                    タイムアウトフラグ.set()
                    logger.warning(f"ChatAI実行タイムアウト: {タイムアウト秒数}秒")
                except asyncio.CancelledError:
                    pass

            タイムアウトタスク = asyncio.create_task(タイムアウト監視())

            try:
                # 履歴追加（画像データも含める）
                self._履歴追加(role="user", text=要求テキスト, image_data=image_data)

                # 履歴構築
                メッセージ履歴 = self._メッセージ履歴構築(
                    システムプロンプト=システムプロンプト
                )

                # 非同期でapi実行
                応答テキスト = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self._同期実行(
                        メッセージ履歴=メッセージ履歴,
                        テキスト受信処理Ｑ=テキスト受信処理Ｑ,
                        タイムアウトフラグ=タイムアウトフラグ,
                        output_files=output_files
                    )
                )

                # タイムアウトタスクキャンセル
                タイムアウトタスク.cancel()

                # 応答がない場合のデフォルト値
                final_result = 応答テキスト.strip() if 応答テキスト.strip() else "!"

                # 履歴追加
                self._履歴追加(role="assistant", text=final_result)

                if final_result == "!" and テキスト受信処理Ｑ:
                    try:
                        data = {"type": "stream", "content": "!", "timestamp": time.time()}
                        テキスト受信処理Ｑ.put_nowait({"text": "!", "json": json.dumps(data, ensure_ascii=False)})
                    except Exception:
                        pass

                # 出力ファイルログ
                if output_files:
                    logger.info(f"出力ファイル: {len(output_files)}件")
                    for output_file in output_files:
                        logger.info(f"  - {output_file}")

                return final_result

            except asyncio.CancelledError:
                logger.warning("ChatAI実行がキャンセルされました")
                応答テキスト = "処理がキャンセルされました。"
                return 応答テキスト
            except Exception as e:
                logger.error(f"ChatAI実行エラー: {e}")
                エラーメッセージ = f"実行エラー: {str(e)}"

                if テキスト受信処理Ｑ:
                    data = {"type": "error", "content": "!!! 処理エラー !!!", "timestamp": time.time()}
                    テキスト受信処理Ｑ.put_nowait({"text": "!!! 処理エラー !!!", "json": json.dumps(data, ensure_ascii=False)})

                return エラーメッセージ
            finally:
                タイムアウトタスク.cancel()

        except Exception as e:
            # ツールエラーログ（必須）
            セッションID_str = self.セッションID[:10] + '...' if self.セッションID else '不明'
            logger.error(f"ChatAI実行エラー: {e} 要求=[{要求テキスト[:10]}...] セッション={セッションID_str}")
            エラーメッセージ = f"実行エラー: {str(e)}"

            if テキスト受信処理Ｑ:
                data = {"type": "error", "content": "!!! 処理エラー !!!", "timestamp": time.time()}
                テキスト受信処理Ｑ.put_nowait({"text": "!!! 処理エラー !!!", "json": json.dumps(data, ensure_ascii=False)})

            return エラーメッセージ

    def _同期実行(self, メッセージ履歴: list,
                   テキスト受信処理Ｑ: queue.Queue = None,
                   タイムアウトフラグ: asyncio.Event = None,
                   output_files: list = None) -> str:
        """
        同期api実行（スレッドプールで実行、画像生成対応）
        """
        try:
            # パラメータ構築
            parm_kwargs = {
                "model": self.chat_model,
                "messages": メッセージ履歴,
                "temperature": float(self.temperature),
                "timeout": self.max_wait_sec,
                "stream": False,  # ストリーミング無効
            }

            # 画像生成モデルの場合はmodalitiesを指定（OpenRouterサンプル準拠）
            if "image" in str(self.chat_model):
                parm_kwargs["extra_body"] = {"modalities": ["image", "text"]}

            # api実行
            response = self.client.chat.completions.create(**parm_kwargs)

            # デバッグログ簡略化（ファイル送受信に関係するもののみ）
            if response and response.choices:
                message = response.choices[0].message

            def _保存画像データ(image_url: str):
                """data URL画像を保存してパスを返す"""
                if not image_url or not image_url.startswith('data:image/'):
                    return None
                try:
                    from pathlib import Path

                    header, data = image_url.split(',', 1)
                    mime_type = header.split(':')[1].split(';')[0]

                    ext = 'png'
                    if 'jpeg' in mime_type or 'jpg' in mime_type:
                        ext = 'jpg'
                    elif 'gif' in mime_type:
                        ext = 'gif'
                    elif 'webp' in mime_type:
                        ext = 'webp'

                    image_bytes = base64.b64decode(data)

                    base_path = Path(self.cwd_str)
                    output_dir = base_path / "temp" / "output"
                    output_dir.mkdir(parents=True, exist_ok=True)

                    nowTime = datetime.datetime.now()
                    file_name = nowTime.strftime('%Y%m%d.%H%M%S') + f'.image.{ext}'
                    output_path = output_dir / file_name

                    with open(output_path, 'wb') as f:
                        f.write(image_bytes)

                    if output_files is not None:
                        output_files.append(str(output_path))

                    logger.info(f"ChatAI: 出力ファイルを保存 {output_path} ({mime_type})")
                    return output_path
                except Exception as e:
                    logger.error(f"ChatAI: 画像保存エラー {e}")
                    return None

            # レスポンス処理
            応答テキスト = ""
            画像保存済み = False  # 最初の1つだけ保存するフラグ
            if response and response.choices:
                message = response.choices[0].message
                message_content = message.content

                # contentがリスト形式の場合（画像生成モデルの可能性）
                if isinstance(message_content, list):
                    for content_part in message_content:
                        if hasattr(content_part, 'type'):
                            # テキスト部分
                            if content_part.type == 'text':
                                応答テキスト += content_part.text
                            # 画像部分（base64またはURL）- 最初の1つだけ保存
                            elif content_part.type == 'image_url' and hasattr(content_part, 'image_url') and not 画像保存済み:
                                try:
                                    image_url = content_part.image_url.url
                                    # base64データの場合
                                    if image_url.startswith('data:image/'):
                                        # data:image/png;base64,... の形式
                                        header, data = image_url.split(',', 1)
                                        mime_type = header.split(':')[1].split(';')[0]

                                        # 拡張子判定
                                        ext = 'png'
                                        if 'jpeg' in mime_type or 'jpg' in mime_type:
                                            ext = 'jpg'
                                        elif 'gif' in mime_type:
                                            ext = 'gif'
                                        elif 'webp' in mime_type:
                                            ext = 'webp'

                                        # base64デコード
                                        image_bytes = base64.b64decode(data)

                                        # 出力ディレクトリ作成
                                        from pathlib import Path
                                        base_path = Path(self.cwd_str)
                                        output_dir = base_path / "temp" / "output"
                                        output_dir.mkdir(parents=True, exist_ok=True)

                                        # ファイル名生成
                                        nowTime = datetime.datetime.now()
                                        file_name = nowTime.strftime('%Y%m%d.%H%M%S') + f'.image.{ext}'
                                        output_path = output_dir / file_name

                                        # ファイルに書き込み
                                        with open(output_path, 'wb') as f:
                                            f.write(image_bytes)

                                        if output_files is not None:
                                            output_files.append(str(output_path))

                                        画像保存済み = True  # 1つ保存したのでフラグを立てる
                                        logger.info(f"ChatAI: 出力ファイルを保存 {output_path} ({mime_type})")

                                        # テキストにファイルパス情報を追加
                                        if 応答テキスト != '':
                                            応答テキスト += '\n'
                                        表示パス = None
                                        try:
                                            base_path = Path(self.cwd_str).resolve()
                                            表示パス = str(Path(output_path).resolve().relative_to(base_path))
                                        except Exception:
                                            表示パス = str(output_path)
                                        応答テキスト += f"[画像ファイル: {表示パス}]"

                                except Exception as e:
                                    logger.error(f"ChatAI: 画像保存エラー {e}")
                elif hasattr(message, "images") and message.images and not 画像保存済み:
                    # OpenRouter imageレスポンス（response.choices[0].message.images）- 最初の1つだけ保存
                    for img in message.images:
                        if 画像保存済み:
                            break
                        try:
                            image_url = None
                            if isinstance(img, dict):
                                image_url = img.get("image_url", {}).get("url")
                            elif hasattr(img, "image_url"):
                                image_url = getattr(img.image_url, "url", None)

                            output_path = _保存画像データ(image_url)
                            if output_path:
                                画像保存済み = True  # 1つ保存したのでフラグを立てる
                                if 応答テキスト != '':
                                    応答テキスト += '\n'
                                表示パス = None
                                try:
                                    base_path = Path(self.cwd_str).resolve()
                                    表示パス = str(Path(output_path).resolve().relative_to(base_path))
                                except Exception:
                                    表示パス = str(output_path)
                                応答テキスト += f"[画像ファイル: {表示パス}]"
                        except Exception as e:
                            logger.error(f"ChatAI: 画像保存エラー {e}")
                else:
                    # 通常のテキストレスポンス
                    応答テキスト = str(message_content) if message_content else ""

            # 画像だけでテキストが空のときの補足
            if 応答テキスト == "" and output_files:
                表示一覧 = []
                for p in output_files:
                    表示パス = None
                    try:
                        base_path = Path(self.cwd_str).resolve()
                        表示パス = str(Path(p).resolve().relative_to(base_path))
                    except Exception:
                        表示パス = str(p)
                    表示一覧.append(f"[画像ファイル: {表示パス}]")
                応答テキスト = "\n".join(表示一覧)

            # テキスト受信処理Ｑへ出力（オプション）
            if テキスト受信処理Ｑ and 応答テキスト:
                try:
                    data = {"type": "stream", "content": 応答テキスト, "timestamp": time.time()}
                    テキスト受信処理Ｑ.put_nowait({"text": 応答テキスト, "json": json.dumps(data, ensure_ascii=False)})
                except:
                    pass

            return 応答テキスト

        except Exception as e:
            logger.error(f"同期実行エラー: {e}")
            return ""

    def _メッセージ履歴構築(self, システムプロンプト: str = None) -> list:
        """
        OpenRouter apiメッセージ形式に変換（vision対応）
        """
        メッセージ = []

        # システムプロンプト追加
        if システムプロンプト:
            メッセージ.append({
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": システムプロンプト
                    }
                ]
            })
        else:
            メッセージ.append({
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "あなたは美しい日本語を話す賢いアシスタントです。"
                    }
                ]
            })

        # 履歴追加
        履歴 = self._履歴取得()
        for item in 履歴:
            # 画像データがある場合はvision形式で送信
            if item.get("image_data"):
                image_data = item["image_data"]
                メッセージ.append({
                    "role": item["role"],
                    "content": [
                        {
                            "type": "text",
                            "text": item["text"]
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{image_data['mime_type']};base64,{image_data['data']}"
                            }
                        }
                    ]
                })
            else:
                # テキストのみ（常にtextパートで送信）
                メッセージ.append({
                    "role": item["role"],
                    "content": [
                        {
                            "type": "text",
                            "text": item["text"]
                        }
                    ]
                })

        return メッセージ

    def _履歴追加(self, role: str, text: str, image_data: dict = None):
        """履歴にメッセージを追加（画像対応）"""
        self.履歴最終番号 += 1
        self.履歴最終時刻 = time.time()
        self.履歴辞書[self.履歴最終番号] = {
            "role": role,
            "text": text,
            "image_data": image_data,  # 画像データを保存
            "time": self.履歴最終時刻
        }

    def _履歴取得(self) -> list:
        """履歴を時系列順に取得（画像対応）"""
        履歴 = []
        for 番号 in sorted(self.履歴辞書.keys()):
            item = self.履歴辞書[番号]
            履歴.append({
                "role": item["role"],
                "text": item["text"],
                "image_data": item.get("image_data")  # 画像データも含める
            })
        return 履歴

    def 履歴クリア(self):
        """履歴をクリア"""
        self.履歴辞書 = {}
        self.履歴最終番号 = 0
        self.履歴最終時刻 = time.time()


if __name__ == "__main__":

    print("画像生成テスト実行 (OpenRouter + 画像生成モデル)")

    # 参考: OPENROUTER_API_KEY の一時値
    # openrt_key_id = "< your openrouter api key >"

    async def _main(api_key: str, AI_MODEL: str):
        AI_NAME = "openrt"
        chatai = ChatAI(親=None, セッションID="image_test", AI_NAME=AI_NAME, AI_MODEL=AI_MODEL, api_key=api_key)

        try:
            print(f"モデル: {AI_MODEL}")
            await chatai.開始()

            temp_output_dir = Path(chatai.cwd_str) / "temp" / "output"
            existing_images = set(temp_output_dir.glob("*.image.*")) if temp_output_dir.exists() else set()

            # 1回目: 挨拶
            prompt1 = "おはよう"
            print(f"プロンプト1: {prompt1}")
            result1 = await chatai.実行(prompt1)
            print(f"\n実行結果1: {result1}")

            # 2回目: 猫の画像生成依頼
            prompt2 = "かわいい猫の画像を作って"
            print(f"\nプロンプト2: {prompt2}")
            result2 = await chatai.実行(prompt2)
            print(f"\n実行結果2: {result2}")

            # 生成画像の最新ファイルを取得（実際に新規保存されたもののみ採用）
            latest_image = None
            if temp_output_dir.exists():
                new_images = sorted(
                    [p for p in temp_output_dir.glob("*.image.*") if p not in existing_images],
                    key=lambda p: p.stat().st_mtime,
                    reverse=True
                )
                if new_images:
                    latest_image = new_images[0]

            # 3回目: 添付画像の説明（直前に生成した画像を使用）
            prompt3 = "この画像を説明してください"
            print(f"\nプロンプト3: {prompt3}")
            if latest_image and latest_image.exists():
                print(f"添付画像: {latest_image}")
                result3 = await chatai.実行(prompt3, file_path=str(latest_image))
                print(f"\n実行結果3: {result3}")
            else:
                print("生成画像が見つかりませんでした（temp/output/*.image.* を確認してください）")

        except Exception as e:
            print(f"画像生成テストエラー: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await chatai.終了()

    def _load_config():
        try:
            base_dir = Path(__file__).resolve().parents[1]
            config_path = base_dir / "_config" / "AiDiy_key.json"
            if not config_path.exists():
                print(f"configが見つかりません: {config_path}")
                return {}
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"config読込エラー: {e}")
            return {}

    conf = _load_config()
    AI_MODEL = conf.get("CHAT_OPENRT_MODEL", "google/gemini-3-pro-image-preview")
    api_key = conf.get("openrt_key_id")

    if not api_key or str(api_key).startswith("<"):
        print("APIキーが設定されていません。_config/AiDiy_key.json を確認してください。")
    else:
        asyncio.run(_main(api_key=api_key, AI_MODEL=AI_MODEL))

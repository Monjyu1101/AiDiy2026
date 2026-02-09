#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

# モジュール名
MODULE_NAME = '_claude'

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
from collections import deque
from pathlib import Path
from typing import Optional, Dict, Any
from PIL import Image
import io

# Claude Agent SDK
import anyio
from claude_agent_sdk import query, ClaudeAgentOptions


class CodeAI:
    """
    Claude Agent SDK統合クラス（履歴管理 + SDK resume混合実装）
    """
    
    def __init__(self, 親=None, セッションID: str = "", チャンネル: int = 0, 絶対パス: str = None,
                 AI_NAME: str = "claude", AI_MODEL: str = "sonnet", max_turns: int = 999,
                 code_plan: str = "auto", code_verify: str = "auto"):
        """初期化"""

        # セッションID・チャンネル
        self.セッションID = セッションID
        self.チャンネル = チャンネル

        # 親参照（セッションマネージャー）
        self.parent_manager = 親
        self.親 = 親

        # プロバイダー設定
        self.code_ai = AI_NAME
        self.code_model = AI_MODEL
        self.max_turns = max_turns
        self.code_plan = code_plan
        self.code_verify = code_verify
        
        # apiキー設定（Claude Agent SDK用）
        # Claude Agent SDKはキーなしで動作可能
        # 環境変数への保存は行わない（セキュリティ上の理由）
        pass
        
        # 作業ディレクトリ設定
        work_dir_input = 絶対パス if isinstance(絶対パス, str) else None
        if work_dir_input and isinstance(work_dir_input, str):
            work_dir = Path(work_dir_input)
        else:
            work_dir = Path.cwd()

        cwd_str = work_dir.resolve().as_posix()  # "/" 区切りに統一
        self.base_abs_path = cwd_str
        # logger.info(f"作業ディレクトリ設定: {cwd_str}")
        pass
        
        # システムプロンプトを構築（システム情報を含む）
        system_prompt = self._システムプロンプト構築()
        
        # 基本オプション
        self.base_options = {
            "max_turns": max_turns,
            "system_prompt": system_prompt,
            "cwd": cwd_str,
            # 通常時は制限なし（全ツール利用可能）
            # "allowed_tools": 指定なし = 全ツール利用可能
            # "permission_mode": 指定なし = デフォルト（制限なし）
        }
        
        # 履歴管理システム(ローカル保管)
        self.履歴最終番号 = 0
        self.履歴最終時刻 = time.time()
        self.履歴辞書 = {}
        
        # SDK session管理（WebSocketのセッションIDとは分離）
        self.AIセッションID = None
        
        # 生存状態管理
        self.is_alive = True
        
        # バージョン管理（変化検出用）
        self.last_version = None
        
        # logger.info(f"初期化:完了 (Claude Agent SDK設定済み, 履歴管理有効)")
        pass
    
    def _システムプロンプト構築(self) -> str:
        """
        システムプロンプトを構築（【システム情報】セクション付き）
        
        Args:
            base_prompt: 基本のシステムプロンプト
            cwd_str: 作業ディレクトリ
            
        Returns:
            システム情報を含む完全なシステムプロンプト
        """
        try:
            base_prompt = "あなたは日本語対応のコードエージェントです。"
            base_prompt += "このプロジェクトの概要は`_AIDIY.md`を確認してください。"
            base_prompt += "概要以外にも`*.md`の記載内容は必要に応じて確認してください。"
            if os.name == 'nt':
                base_prompt += "Windows環境で動作していることを考慮して、適切なコマンドを使用してください。"
            base_prompt += "概要が不明な場合は、プログラムコードの説明、分析、実装支援を行います。"
            base_prompt += "機能追加、修正操作時は、同類のソースを参考にしてください。"

            # _AIDIY.mdファイルのパスを構築（絶対パス）※区切りは"/"に統一
            base_path = getattr(self, "base_abs_path", None)
            if not base_path and self.parent_manager and hasattr(self.parent_manager, "CODE_ABS_PATH"):
                base_path = getattr(self.parent_manager, "CODE_ABS_PATH", None)
            if not base_path and self.parent_manager and hasattr(self.parent_manager, "utils"):
                base_path = getattr(self.parent_manager.utils, "CODE_ABS_PATH", None)
            if not base_path and hasattr(self, "base_options"):
                base_path = self.base_options.get("cwd")
            if not base_path:
                base_path = Path(__file__).resolve().parent.as_posix()

            aidiy_md_path = (Path(base_path) / "_AIDIY.md").as_posix()
            
            # ファイルの存在確認
            if not os.path.exists(aidiy_md_path):
                logger.warning(f"システムプロンプト構築: _AIDIY.mdファイルが存在しません: `{aidiy_md_path}`")
                return base_prompt
            
            # システムプロンプトを構築（基本プロンプトのみ）
            system_prompt = base_prompt
            system_prompt += f"初回メッセージ開始前に`{aidiy_md_path}`を確認してください。"
            
            # logger.info(f"システムプロンプト構築完了: _AIDIY.mdパス={aidiy_md_path}")
            pass
            return system_prompt
            
        except Exception as e:
            logger.error(f"システムプロンプト構築エラー: {e}")
            return base_prompt
    
    async def 開始(self):
        """CodeAI開始（セッション作成）"""
        try:
            # パラメータで渡されたapiキーを優先使用（親からの再取得は不要）

            # SDK resumeセッション初期化（最初の実行時に作成）
            self.AIセッションID = None
            self.is_alive = True
            # logger.info("CodeAI: セッション開始完了")
            pass
            return True
        except Exception as e:
            logger.error(f"CodeAI開始:エラー {e}")
            self.is_alive = False
            return False
    
    async def 終了(self):
        """CodeAI終了"""
        try:
            self.is_alive = False
            # SDK session終了処理は不要（実行ベースのため）
            # logger.info(f"CodeAI: 終了完了 セッションID={self.セッションID[:8]}")
            pass
        except Exception as e:
            logger.error(f"CodeAI終了:エラー {e}")
            self.is_alive = False
    
    def _履歴追加(self, text: str, type: str):
        """履歴に項目を追加"""
        self.履歴最終番号 += 1
        self.履歴最終時刻 = time.time()
        key = str(self.履歴最終番号)
        
        self.履歴辞書[key] = {
            "seq": str(self.履歴最終番号),
            "time": self.履歴最終時刻,
            "type": type,
            "text": text
        }
        
        # logger.debug(f"履歴追加: {key} ({type}) - {text[:50]}...")
        pass
    
    def _履歴取得(self) -> str:
        """過去の会話履歴を取得してフォーマット"""
        if not self.履歴辞書:
            return ""
        
        履歴テキスト = "【過去の会話履歴】\n"
        
        # 番号順にソートして履歴を構築
        sorted_keys = sorted(self.履歴辞書.keys(), key=lambda x: int(x))
        
        for key in sorted_keys:
            item = self.履歴辞書[key]
            if item["type"] == "system":
                履歴テキスト += f"```system\n{item['text']}\n```\n"
            elif item["type"] == "user":
                履歴テキスト += f"```user\n{item['text']}\n```\n"
            elif item["type"] == "agent":
                履歴テキスト += f"```agent\n{item['text']}\n```\n"
        
        return 履歴テキスト
    
        
    
    async def 実行(self, 要求テキスト: str, テキスト受信処理Ｑ=None, タイムアウト秒数: int = 600, resume: bool = True, 読取専用: bool = False, 絶対パス: str = None, file_path: str = None, 変更ファイル一覧: list = None, 再プラン要求: bool = False) -> str:
        """
        Claude Agent SDK実行（セッション.chatメソッド使用）

        Args:
            要求テキスト: ユーザーの要求テキスト
            テキスト受信処理Ｑ: ストリーミング用キュー
            タイムアウト秒数: タイムアウト時間
            resume: セッション継続フラグ
            読取専用: 読取専用モード
            絶対パス: 実行ディレクトリの絶対パス
            file_path: 添付ファイルの絶対パス（オプション）
            変更ファイル一覧: 変更されたファイルのリスト（検証用、オプション）
            再プラン要求: 修正内容の再プラン要求フラグ（オプション）
        """
        try:
            # 添付ファイルを後段で埋め込むためのブロックを準備（ログには含めない）
            attachment_block = ""
            if file_path:
                try:
                    abs_path = Path(file_path).resolve()
                    path_str = abs_path.as_posix()
                    attachment_block = f"\n\n添付ファイル: `{path_str}`"
                    logger.info(f"ClaudeSDK: 添付ファイルをコンテキストに追加: {path_str}")
                except Exception as e:
                    logger.error(f"ClaudeSDK: ファイルパス処理エラー: {e}")

            # 再プラン要求ブロックを準備
            replan_block = ""
            if 再プラン要求:
                try:
                    replan_block = """

修正が正しいことを検証するために、
修正概要、修正手順を再プランしてください。
"""
                    logger.info("ClaudeSDK: 再プラン要求をプロンプトに追加")
                except Exception as e:
                    logger.error(f"ClaudeSDK: 再プラン要求処理エラー: {e}")

            # 生存状態チェック
            if not self.is_alive:
                logger.warning("ClaudeSDK実行:ClaudeSDKが開始されていません")
                return "ClaudeSDKが停止状態です。開始してください。"

            # 履歴管理（セッション内で自動管理されるが、独自履歴も維持）
            if len(self.履歴辞書) == 0:
                self._履歴追加(self.base_options["system_prompt"], "system")

            # 最終プロンプトを作成
            # 変更ファイル一覧がある場合は検証モード（元の依頼は実施済みとして検証のみ）
            if 変更ファイル一覧 and len(変更ファイル一覧) > 0:
                try:
                    ファイル一覧文字列 = '\n'.join([f"- {ファイル名}" for ファイル名 in 変更ファイル一覧])
                    最終要求テキスト = f"""前回の依頼「{要求テキスト}」は実施済みです。

以下のファイルが変更されました：
{ファイル一覧文字列}

これらのファイルの変更内容を検証し、問題があれば追加修正を行ってください。
問題がなければ「検証完了」と報告してください。"""
                    logger.info(f"ClaudeSDK: 検証モード - 変更ファイル {len(変更ファイル一覧)}件")
                except Exception as e:
                    logger.error(f"ClaudeSDK: 変更ファイル一覧処理エラー: {e}")
                    最終要求テキスト = 要求テキスト + attachment_block + replan_block
            else:
                # 通常モード（順序：元の要求 → 添付ファイル → 再プラン要求）
                最終要求テキスト = 要求テキスト + attachment_block + replan_block

            # 送信コンテキスト側で「今回の依頼」を必ず明示（オリジナルの要求文は改変しない）
            依頼本文 = (最終要求テキスト or "").strip()
            if 依頼本文.startswith("【今回の依頼】"):
                送信用要求テキスト = 依頼本文
            else:
                送信用要求テキスト = f"【今回の依頼】\n{依頼本文}\n"

            self._履歴追加(最終要求テキスト, "user")

            # 実行開始通知
            if テキスト受信処理Ｑ is not None:
                try:
                    data = {"type": "start", "content": "<<< 処理開始 >>>", "timestamp": time.time()}
                    テキスト受信処理Ｑ.put_nowait({"text": data["content"], "json": json.dumps(data, ensure_ascii=False)})
                except Exception:
                    pass

            # parent_manager経由でoutput_stream送信（処理開始）
            if self.parent_manager and hasattr(self.parent_manager, '接続'):
                try:
                    await self.parent_manager.接続.send_to_channel(self.チャンネル, {
                        "セッションID": self.セッションID,
                        "チャンネル": self.チャンネル,
                        "メッセージ識別": "output_stream",
                        "メッセージ内容": "<<< 処理開始 >>>",
                        "ファイル名": None,
                        "サムネイル画像": None
                    })
                    logger.info(f"テキストストリーム送信開始: チャンネル={self.チャンネル}, <<< 処理開始 >>>")
                except Exception as e:
                    logger.error(f"[CodeClaud] output_stream送信エラー(開始): {e}")
            else:
                logger.warning(f"[CodeClaud] parent_manager未設定またはparent_manager.接続なし")
            
            result_text = ""
            last_stream_time = time.time()
            
            # セッション.chat実行（タイムアウト監視付き）
            try:
                async def _chat_execution():
                    nonlocal result_text, last_stream_time

                    # 作業ディレクトリを決定（パラメータ優先、なければデフォルト）
                    cwd_posix = 絶対パス if 絶対パス else self.base_options["cwd"]

                    # オプション設定（初回はresume=False、2回目以降のみセッションID使用）
                    # 読取専用パラメータに応じてallowed_toolsを設定
                    allowed_tools_list = ["Read", "Write", "Bash"] if not 読取専用 else ["Read"]
                    logger.info(f"ClaudeSDK許可ツール: {allowed_tools_list}, 読取専用={読取専用}, AIセッションID={self.AIセッションID}")

                    # Claude Agent SDK用のパス設定（Windows環境ではパス区切り文字を変換）
                    if os.name == 'nt':
                        cwd = cwd_posix.replace('/', '\\')
                    else:
                        cwd = cwd_posix

                    logger.info(f"ClaudeSDK実行パス: {cwd}")
                    if not self.AIセッションID:
                        # 初回：新規セッション作成
                        options = ClaudeAgentOptions(
                            max_turns=self.base_options["max_turns"],
                            system_prompt=self.base_options["system_prompt"],
                            cwd=Path(cwd),
                            allowed_tools=allowed_tools_list,
                            permission_mode="acceptEdits",
                            continue_conversation=False
                        )
                    else:
                        # 継続会話：読取専用パラメータに応じてallowed_toolsを設定
                        options = ClaudeAgentOptions(
                            max_turns=self.base_options["max_turns"],
                            system_prompt=self.base_options["system_prompt"],
                            cwd=Path(cwd),
                            allowed_tools=allowed_tools_list,  # 毎回正しく設定
                            permission_mode="acceptEdits",
                            continue_conversation=True,
                            resume=self.AIセッションID
                        )
                     
                    # テスト用：初回のみ system_prompt、毎回「今回の依頼」（送信用）を標準出力に表示（平文）
                    try:
                        print("\n" + "=" * 80)
                        if not self.AIセッションID:
                            print("送信コンテキスト（Claude Agent SDK / 初回）")
                        else:
                            print("送信コンテキスト（Claude Agent SDK）")
                        print(f"AI={self.code_ai} model={self.code_model} resume={resume} 読取専用={読取専用}")
                        print(f"allowed_tools={allowed_tools_list} cwd={cwd}")
                        if not self.AIセッションID:
                            print("-" * 80)
                            print("【system_prompt】")
                            print(self.base_options.get("system_prompt", ""))
                        print("-" * 80)
                        print(送信用要求テキスト)
                        print("=" * 80 + "\n")
                    except Exception:
                        pass

                    # queryメソッドで実行（ストリーミング対応）
                    async for message in query(prompt=送信用要求テキスト, options=options):
                        last_stream_time = time.time()
                        
                        # AIセッションIDを取得・保存（SDK仕様のsession_id属性）
                        if not self.AIセッションID:
                            sdk_id = getattr(message, "session_id", None)
                            if sdk_id:
                                self.AIセッションID = sdk_id
                                # logger.info(f"AIセッションID取得: {self.AIセッションID}")
                                pass
                        
                        # ストリーミングコンテンツを抽出
                        content = self.メッセージ内容抽出(message)
                        if content and テキスト受信処理Ｑ:
                            data = {"type": "stream", "content": content, "timestamp": time.time()}
                            テキスト受信処理Ｑ.put_nowait({"text": content, "json": json.dumps(data, ensure_ascii=False)})

                        # parent_manager経由でoutput_stream送信（ストリーム）
                        if content and self.parent_manager and hasattr(self.parent_manager, '接続'):
                            try:
                                await self.parent_manager.接続.send_to_channel(self.チャンネル, {
                                    "セッションID": self.セッションID,
                                    "チャンネル": self.チャンネル,
                                    "メッセージ識別": "output_stream",
                                    "メッセージ内容": content,
                                    "ファイル名": None,
                                    "サムネイル画像": None
                                })
                            except Exception as e:
                                logger.error(f"[CodeClaud] output_stream送信エラー(stream): {e}")
                        
                        # 最終結果を取得
                        if hasattr(message, 'result') and message.result:
                            result_text = str(message.result)
                
                # タイムアウト監視
                async def _timeout_monitor():
                    while True:
                        await asyncio.sleep(1)
                        if time.time() - last_stream_time > タイムアウト秒数:
                            raise asyncio.TimeoutError(f"タイムアウト({タイムアウト秒数}秒)")
                
                # 実行とタイムアウト監視を並行実行
                monitor_task = asyncio.create_task(_timeout_monitor())
                execution_task = asyncio.create_task(_chat_execution())
                
                done, pending = await asyncio.wait([execution_task, monitor_task], return_when=asyncio.FIRST_COMPLETED)
                
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                
                for task in done:
                    if task == monitor_task:
                        raise asyncio.TimeoutError(f"タイムアウト({タイムアウト秒数}秒)")
                
            except asyncio.TimeoutError:
                logger.warning(f"ClaudeSDK タイムアウト ({タイムアウト秒数}秒)")
                result_text = f"処理タイムアウト({タイムアウト秒数}秒)が発生しました。"
                
                if テキスト受信処理Ｑ:
                    data = {"type": "timeout", "content": "!!! 処理タイムアウト !!!", "timestamp": time.time()}
                    テキスト受信処理Ｑ.put_nowait({"text": "!!! 処理タイムアウト !!!", "json": json.dumps(data, ensure_ascii=False)})
                        
            except Exception as sdk_error:
                logger.error(f"ClaudeSDK エラー: {sdk_error}")
                result_text = f"ClaudeSDK実行エラー: {str(sdk_error)}"
                
                if テキスト受信処理Ｑ:
                    data = {"type": "error", "content": "!!! 処理エラー !!!", "timestamp": time.time()}
                    テキスト受信処理Ｑ.put_nowait({"text": "!!! 処理エラー !!!", "json": json.dumps(data, ensure_ascii=False)})
            
            # 履歴に結果を追加
            final_result = result_text.strip() if result_text.strip() else "!"
            self._履歴追加(final_result, "agent")
            if final_result == "!" and テキスト受信処理Ｑ:
                try:
                    data = {"type": "stream", "content": "!", "timestamp": time.time()}
                    テキスト受信処理Ｑ.put_nowait({"text": "!", "json": json.dumps(data, ensure_ascii=False)})
                except Exception:
                    pass
            
            # 完了通知
            if テキスト受信処理Ｑ:
                data = {"type": "complete", "content": "<<< 処理終了 >>>", "timestamp": time.time()}
                テキスト受信処理Ｑ.put_nowait({"text": "<<< 処理終了 >>>", "json": json.dumps(data, ensure_ascii=False)})

            # parent_manager経由でoutput_stream送信（処理終了）
            if self.parent_manager and hasattr(self.parent_manager, '接続'):
                try:
                    await self.parent_manager.接続.send_to_channel(self.チャンネル, {
                        "セッションID": self.セッションID,
                        "チャンネル": self.チャンネル,
                        "メッセージ識別": "output_stream",
                        "メッセージ内容": "<<< 処理終了 >>>",
                        "ファイル名": None,
                        "サムネイル画像": None
                    })
                    logger.info(f"テキストストリーム送信終了: チャンネル={self.チャンネル}, <<< 処理終了 >>>")
                except Exception as e:
                    logger.error(f"[CodeClaud] output_stream送信エラー(終了): {e}")

            return final_result
            
        except Exception as e:
            # ツールエラーログ（必須）
            セッションID_str = (self.セッションID[:10] + '...') if self.セッションID else '新規'
            logger.error(f"ClaudeSDK実行エラー: {e} 要求=[{要求テキスト[:10]}...] セッション={セッションID_str}")
            エラーメッセージ = f"実行エラー: {str(e)}"
            
            if テキスト受信処理Ｑ:
                data = {"type": "error", "content": "!!! 処理エラー !!!", "timestamp": time.time()}
                テキスト受信処理Ｑ.put_nowait({"text": "!!! 処理エラー !!!", "json": json.dumps(data, ensure_ascii=False)})
            
            return エラーメッセージ
    
    def メッセージ内容抽出(self, message) -> Optional[str]:
        """メッセージから内容を抽出"""
        try:
            if hasattr(message, 'result') and message.result:
                # 結果はストリームしない（関数戻り値のみ）
                return None
            
            if hasattr(message, 'content') and message.content:
                if hasattr(message.content, '__iter__') and len(message.content) > 0:
                    first_content = message.content[0]
                    if hasattr(first_content, 'text'):
                        return first_content.text
                    elif 'ToolUseBlock' in str(type(first_content).__name__):
                        tool_name = getattr(first_content, 'name', '不明')
                        return f"[{tool_name}実行中...]"
                return str(message.content)
            
            if hasattr(message, 'text') and message.text:
                return message.text
                
            return None
            
        except Exception:
            return None


# ===== 使用例とテストコード =====

async def session_test(AI_NAME="claude", AI_MODEL="sonnet"):
    """
    セッション管理テスト（Claude Agent SDK版）
    - セッション開始
    - 1回目: 近藤の自己紹介
    - 2回目: 名前を覚えているか確認
    - 3回目: Pythonコードの質問
    - 4回目: 続けて質問
    - 履歴表示
    """
    print("=" * 50)
    print("ClaudeSDK セッション管理テスト")
    print("=" * 50)

    # ClaudeSDKインスタンス作成
    codeai = CodeAI(親=None, セッションID="test_session", AI_NAME=AI_NAME, AI_MODEL=AI_MODEL, max_turns=10)

    try:
        # セッション開始
        print("\n[セッション開始]")
        start_result = await codeai.開始()
        print(f"セッション開始結果: {start_result}")

        # 1回目実行
        print("\n[1回目] 自己紹介")
        result1 = await codeai.実行(
            要求テキスト="私の名前は近藤です。覚えておいてください。",
            タイムアウト秒数=30,
            resume=False
        )
        print(f"結果: {result1[:100]}...")
        print(f"履歴件数: {len(codeai.履歴辞書)}件")

        # 2回目実行
        print("\n[2回目] 名前確認")
        result2 = await codeai.実行(
            要求テキスト="私の名前を教えてください",
            タイムアウト秒数=30,
            resume=True
        )
        print(f"結果: {result2[:100]}...")
        print(f"履歴件数: {len(codeai.履歴辞書)}件")

        # 3回目実行
        print("\n[3回目] Pythonコード質問")
        result3 = await codeai.実行(
            要求テキスト="if文の使い方を教えて",
            タイムアウト秒数=30,
            resume=True
        )
        print(f"結果: {result3[:100]}...")
        print(f"履歴件数: {len(codeai.履歴辞書)}件")

        # 4回目実行
        print("\n[4回目] 続けて質問")
        result4 = await codeai.実行(
            要求テキスト="for文との違いは何ですか？",
            タイムアウト秒数=30,
            resume=True
        )
        print(f"結果: {result4[:100]}...")
        print(f"履歴件数: {len(codeai.履歴辞書)}件")

        # 履歴表示
        print("\n[履歴表示]")
        formatted_history = codeai._履歴取得()
        print(formatted_history)

    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # セッション終了
        await codeai.終了()

    print("=" * 50)
    print("テスト完了")
    print("=" * 50)


async def simple_test(AI_NAME="claude", AI_MODEL="sonnet"):
    """キューなしのシンプルテスト"""
    print("\n" + "=" * 30)
    print("シンプルテスト開始")
    print("=" * 30)

    # ClaudeSDKインスタンス作成
    codeai = CodeAI(親=None, セッションID="simple_test", AI_NAME=AI_NAME, AI_MODEL=AI_MODEL, max_turns=10)

    try:
        # セッション開始
        await codeai.開始()

        # キューなしでの実行
        result = await codeai.実行("こんにちは、CodeAIです。現在の時刻を教えてください。")
        print(f"シンプル実行結果: {result}")

        # 追加プロンプト：AI に作業をやらせる
        result2 = await codeai.実行("temp/hello.txt というファイルを作成して、Hello World と書いて。")
        print(f"作業実行結果: {result2}")

    except Exception as e:
        print(f"シンプルテストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await codeai.終了()

    print("=" * 30)
    print("シンプルテスト完了")
    print("=" * 30)


if __name__ == "__main__":

    # プロバイダーとモデルの設定
    AI_NAME, AI_MODEL = "claude_sdk", "sonnet"

    #print("履歴テスト")
    #asyncio.run(session_test(AI_NAME=AI_NAME, AI_MODEL=AI_MODEL))

    print("\nシンプルテスト")
    asyncio.run(simple_test(AI_NAME=AI_NAME, AI_MODEL=AI_MODEL))

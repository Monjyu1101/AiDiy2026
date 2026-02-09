#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

# モジュール名
MODULE_NAME = 'ai_tools'

# ロガーの設定
import logging
logger = logging.getLogger(MODULE_NAME)

import json
import asyncio
from typing import Dict, Any, List
from abc import ABC, abstractmethod


# ============================================================
# 1. 共通インターフェース・基底クラス
# ============================================================

class ToolInterface(ABC):
    """Tool Call機能の共通インターフェース"""
    
    @abstractmethod
    def get_tool_definition(self) -> Dict[str, Any]:
        """ツール定義を取得"""
        pass
    
    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> str:
        """ツールを実行"""
        pass
    
    @property
    @abstractmethod
    def tool_name(self) -> str:
        """ツール名を取得"""
        pass


# ============================================================
# 2. 具体的ツール実装クラス群
# ============================================================

class EchoTestTool(ToolInterface):
    """エコーテスト機能クラス（内部テスト用オウム返し）"""
    
    @property
    def tool_name(self) -> str:
        return "echoTest"
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """エコーテスト機能の定義"""
        return {
            "name": "echoTest",
            "description": "内部テスト用のオウム返し機能です。送信されたメッセージをそのまま返します。",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "オウム返しするメッセージ"
                    }
                },
                "required": ["message"]
            }
        }
    
    async def execute(self, parameters: Dict[str, Any]) -> str:
        """エコーテスト実行"""
        try:
            メッセージ = parameters.get("message", "")
            結果 = f"エコーテスト: {メッセージ}"
            return 結果
        except Exception as e:
            logger.error(f"echoTest エラー: {e}")
            return f"エコーテストでエラーが発生しました: {str(e)}"


# ============================================================
# 3. 新ツール追加エリア（拡張専用セクション）
# ============================================================

class CodeAgentRequestTool(ToolInterface):
    """コードエージェント処理依頼機能クラス"""
    
    def __init__(self, セッション=None):
        self.セッション = セッション
    
    @property
    def tool_name(self) -> str:
        return "codeAgentRequest"
    
    def get_tool_definition(self) -> Dict[str, Any]:
        return {
            "name": "codeAgentRequest",
            "description": """
コードエージェントへ処理を依頼できます。
エージェント1: 通称設計君。計画、設計が得意、汎用的なこともこなします。
エージェント2: 通称バックエンド君。バックエンドに精通しており実装も得意。
エージェント3: 通称フロント、フロントエンド君。フロントエンドに精通しており実装も得意。
エージェント4: 通称検査、検証君。検査、検証が得意。
""",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "integer",
                        "description": "依頼先のコードエージェント番号（1-4の範囲）。迷ったら1を指定。"
                    },
                    "request": {
                        "type": "string",
                        "description": "コードエージェントへの依頼内容"
                    }
                },
                "required": ["channel", "request"]
            }
        }
    
    async def execute(self, parameters: Dict[str, Any]) -> str:
        try:
            チャンネル = parameters.get("channel", 1)
            要求内容 = parameters.get("request", "")
            
            if チャンネル not in [1, 2, 3, 4]:
                return f"エラー: チャンネル番号は1-4の範囲で指定してください（指定値: {チャンネル}）"
            
            if not 要求内容:
                return "エラー: 処理依頼内容が空です"
            
            if not self.セッション or not hasattr(self.セッション, "code_agent_processors"):
                return "エラー: コードエージェントプロセッサが未初期化です"
            
            code_agents = self.セッション.code_agent_processors
            if not code_agents or len(code_agents) < チャンネル:
                return f"エラー: エージェント{チャンネル}が未初期化です"
            
            エージェント = code_agents[チャンネル - 1]
            
            # 1) フロントエンドへ送信（表示用）
            要求データ = {
                "セッションID": self.セッション.セッションID,
                "メッセージ識別": "input_request",
                "メッセージ内容": 要求内容,
                "チャンネル": チャンネル,
                "ファイル名": None,
                "サムネイル画像": None
            }
            await self.セッション.send_to_channel(チャンネル, 要求データ)
            
            # 2) 会話履歴保存
            if hasattr(エージェント, "保存関数") and エージェント.保存関数:
                エージェント.保存関数(
                    セッションID=self.セッション.セッションID,
                    チャンネル=チャンネル,
                    メッセージ識別="input_request",
                    メッセージ内容=要求内容,
                    ファイル名=None,
                    サムネイル画像=None
                )
            
            # 3) 処理キューへ投入
            await エージェント.コード要求(要求データ)
            
            logger.info(f"コードエージェント{チャンネル}へ処理依頼を送信しました")
            
            return "要求を受け付けました。しばらくお待ちください。\n継続する指示がある場合は、コードエージェントの応答を待って指示ください。"
            
        except Exception as e:
            logger.error(f"codeAgentRequest エラー: {e}")
            return f"コードエージェント処理依頼でエラーが発生しました: {str(e)}"


# ============================================================
# 4. メイン管理クラス
# ============================================================

class Tools:
    """AIコア用Tool Call機能統合管理クラス"""
    
    def __init__(self, セッション=None):
        self.セッション = セッション
        self.エコーテストツール = EchoTestTool()
        self.コードエージェント依頼ツール = CodeAgentRequestTool(セッション=セッション)
        
        self.ツール関数辞書 = {}
        self.ツールインスタンス辞書 = {}
        self.ツール関数初期化()
    
    # ----------------------------------------
    # 外部インターフェース（LiveAIから呼び出し）
    # ----------------------------------------
    
    async def execute_tool_call(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Tool Callの実行（新しいキューシステム対応）"""
        try:
            if tool_name not in self.ツール関数辞書:
                エラーメッセージ = f"未知のツールです: {tool_name}"
                logger.error(f"{エラーメッセージ}")
                logger.error(f"利用可能なツール: {list(self.ツール関数辞書.keys())}")
                return エラーメッセージ
            
            # echoTest, codeAgentRequest を即座実行
            ツール関数 = self.ツール関数辞書[tool_name]
            結果 = await ツール関数(parameters)
            return 結果
            
        except Exception as e:
            logger.error(f"Tool Call実行エラー ({tool_name}): {e}")
            return f"Tool実行エラー: {str(e)}"
    
    # ----------------------------------------
    # ツール登録・管理
    # ----------------------------------------
    
    def ツール関数初期化(self):
        """Tool Call機能で使用可能なツール群を初期化"""
        self.ツール関数辞書["echoTest"] = self.エコーテストツール.execute
        self.ツールインスタンス辞書["echoTest"] = self.エコーテストツール
        
        self.ツール関数辞書["codeAgentRequest"] = self.コードエージェント依頼ツール.execute
        self.ツールインスタンス辞書["codeAgentRequest"] = self.コードエージェント依頼ツール
    
    def _register_new_tool(self):
        """新しいツール登録用メソッド（拡張用）"""
        # 新しいツールを追加する際はここに実装
        # 例:
        # self.新ツール = NewTool()
        # self.ツール関数辞書["newTool"] = self.新ツール.execute
        # self.ツールインスタンス辞書["newTool"] = self.新ツール
        pass
    
    # ----------------------------------------
    # 互換性・外部インターフェース
    # ----------------------------------------
    
    @property
    def tool_functions(self):
        """互換性のためのプロパティ"""
        return self.ツール関数辞書
    
    def get_tool_calling_tools(self) -> List[Dict[str, Any]]:
        """Gemini apiで使用するTool Calling用のツール定義を取得"""
        ツール宣言リスト = []
        
        # 各機能の定義を収集
        for ツールインスタンス in self.ツールインスタンス辞書.values():
            ツール宣言リスト.append(ツールインスタンス.get_tool_definition())
        
        return [{"function_declarations": ツール宣言リスト}]

    def exec(self, json_str: str) -> str:
        """Tool Call実行（要求された形式）"""
        try:
            呼出データ = json.loads(json_str)
            ツール名 = 呼出データ.get("function_name", "")
            パラメータ = 呼出データ.get("parameters", {})
            
            if ツール名 == "echoTest":
                メッセージ = パラメータ.get("message", "")
                return json.dumps({'result': f"エコーテスト: {メッセージ}"}, ensure_ascii=False)
            return json.dumps({'error': f"未知のツール: {ツール名}"}, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({'error': f"実行エラー: {str(e)}"}, ensure_ascii=False)


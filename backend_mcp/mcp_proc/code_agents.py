# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""
Code Agents モジュール

AIコード.py (CodeAgent) を MCP ツールとして公開するラッパー。
起動時に key.json の各 CODE_AIx_NAME に対して CLI --version を確認し、
利用可能な AI 名を MCP ツールの description で通知する。

ツール公開先:
    SSE: http://localhost:8095/aidiy_code_agents/sse
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional


class CodeAgentsError(Exception):
    """CodeAgents 実行エラー"""
    pass


class _NullConnection:
    """MCP経由実行時の接続ダミー。WebSocket送信を全て無視する。"""
    モデル設定: dict = {}

    async def send_to_channel(self, *args: Any, **kwargs: Any) -> None:
        pass


class CodeAgents:
    """AIコード.py の CodeAgent を MCP 経由で起動するラッパークラス"""

    KEY_JSON_REL = os.path.join("backend_server", "_config", "AiDiy_key.json")

    def __init__(self, project_root: Optional[str] = None):
        if project_root:
            self.root = os.path.abspath(project_root)
        else:
            # backend_mcp/mcp_proc/ から 2 つ上がプロジェクトルート
            here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.root = os.path.dirname(here)

        # 起動時バージョン確認結果（mcp_main.py から _check_ai_versions() で設定）
        self.version_info: dict[str, dict] = {}

    # ------------------------------------------------------------------ #
    # sys.path 設定
    # ------------------------------------------------------------------ #

    def _setup_sys_path(self) -> None:
        """backend_server を sys.path に追加（AIコード.py のインポートに必要）"""
        backend_server = os.path.join(self.root, "backend_server")
        if os.path.isdir(backend_server) and backend_server not in sys.path:
            sys.path.append(backend_server)

    # ------------------------------------------------------------------ #
    # 設定ファイル読み込み
    # ------------------------------------------------------------------ #

    def _load_key_json(self) -> dict:
        """AiDiy_key.json を読み込んで dict を返す。失敗時は空 dict。"""
        key_path = os.path.join(self.root, self.KEY_JSON_REL)
        try:
            with open(key_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _resolve_project_path(self, project_path: Optional[str] = None) -> str:
        """
        実行ディレクトリの絶対パスを解決する。

        1. project_path が指定されていれば絶対パスに正規化して返す。
        2. なければ AiDiy_key.json の CODE_BASE_PATH を使う。
           CODE_BASE_PATH は相対パス（例: "../"）の場合、backend_server/_config/ 基準で解釈。
        3. それも取得できなければプロジェクトルートを返す。
        """
        if project_path:
            return str(Path(project_path).resolve())

        key = self._load_key_json()
        code_base = key.get("CODE_BASE_PATH", "").strip()
        if code_base:
            config_dir = os.path.join(self.root, "backend_server", "_config")
            resolved = Path(config_dir) / code_base
            return str(resolved.resolve())

        return self.root

    def _resolve_ai_params(self, ai_name: str, ai_model: str) -> tuple[str, str]:
        """ai_name / ai_model の "auto" を key.json 値で解決する"""
        key = self._load_key_json()
        if ai_name == "auto":
            available = [k for k, v in self.version_info.items() if v.get("ok")]
            # copilot_cli が利用可能なら優先、なければ key.json の並び順で最初に利用可能な AI
            if "copilot_cli" in available:
                ai_name = "copilot_cli"
            elif available:
                ai_name = available[0]
            else:
                ai_name = key.get("CODE_AI1_NAME", "claude_cli")
        if ai_model == "auto":
            model_key = f"CODE_{ai_name.upper()}_MODEL"
            ai_model = key.get(model_key, "auto")
        return ai_name, ai_model

    # ------------------------------------------------------------------ #
    # 起動時バージョン確認
    # ------------------------------------------------------------------ #

    def _check_ai_versions(self) -> dict[str, dict]:
        """
        key.json の CODE_AI1_NAME ... CODE_AI9_NAME に対して CLI --version を
        同期実行し、各 AI の利用可否を返す。

        claude_sdk は anthropic パッケージと claude_key_id の存在で確認。
        CLI ベースは subprocess.run で --version を実行。
        また、必要な API キーが未設定の場合は利用不可とする。
        """
        self._setup_sys_path()

        key = self._load_key_json()

        # CODE_AI1_NAME ... CODE_AI9_NAME から候補を収集
        candidates: list[str] = []
        for i in range(1, 10):
            name = key.get(f"CODE_AI{i}_NAME", "").strip()
            if name and name not in candidates:
                candidates.append(name)
        if not candidates:
            candidates = ["claude_cli"]

        results: dict[str, dict] = {}

        for ai_name in candidates:
            info: dict = {"ok": False, "version": "", "cmd": ""}

            # 各 AI が必要とするキーのチェック
            # copilot_cli は gh auth で認証するため API キー不要
            key_ok = True
            if ai_name == "antigravity_cli":
                claude_key = key.get("claude_key_id", "").strip()
                if not claude_key or claude_key.startswith("<"):
                    info = {"ok": False, "version": "claude_key_id 未設定", "cmd": ""}
                    key_ok = False
            elif ai_name == "codex_cli":
                openai_key = key.get("openai_key_id", "").strip()
                if not openai_key or openai_key.startswith("<"):
                    info = {"ok": False, "version": "openai_key_id 未設定", "cmd": ""}
                    key_ok = False

            if not key_ok:
                results[ai_name] = info
                continue

            try:
                if ai_name == "claude_sdk":
                    # SDK ベース: anthropic インポート + APIキー確認
                    try:
                        import anthropic  # noqa: F401, PLC0415
                        api_key = key.get("claude_key_id", "").strip()
                        if api_key and not api_key.startswith("<"):
                            info = {"ok": True, "version": "anthropic SDK", "cmd": "anthropic"}
                        else:
                            info = {"ok": False, "version": "claude_key_id 未設定", "cmd": "anthropic"}
                    except ImportError:
                        info = {"ok": False, "version": "anthropic 未インストール", "cmd": "anthropic"}

                else:
                    from AIコア.AIコード_cli import CodeAI  # noqa: PLC0415
                    dummy = CodeAI(AI_NAME=ai_name, AI_MODEL="auto")
                    cmd_path = dummy._コマンドパス取得()
                    info["cmd"] = cmd_path

                    if ai_name == "aidiy_hermes":
                        base = dummy._hermes直接実行コマンド()
                        if None is base:
                            base = [cmd_path]
                        cmd = base + ["--version"]
                        timeout = 30
                    else:
                        direct = dummy._npmシム直接実行に解決(cmd_path)
                        cmd = (direct if direct else [cmd_path]) + ["--version"]
                        timeout = 10

                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        timeout=timeout,
                    )
                    stdout = (result.stdout or b"").decode("utf-8", errors="replace").strip()
                    stderr = (result.stderr or b"").decode("utf-8", errors="replace").strip()
                    lines = (stdout or stderr).splitlines()
                    first_line = lines[0].strip() if lines else ""
                    ok = bool(first_line) and not first_line.startswith("Error:")
                    info = {"ok": ok, "version": first_line, "cmd": cmd_path}

            except FileNotFoundError:
                info["version"] = "コマンドが見つかりません"
            except subprocess.TimeoutExpired:
                info["version"] = "timeout"
            except Exception as e:
                info["version"] = str(e)[:80]

            results[ai_name] = info

        return results

    # ------------------------------------------------------------------ #
    # 情報取得
    # ------------------------------------------------------------------ #

    def get_config(self, project_path: Optional[str] = None) -> dict:
        """設定情報（解決済みパス・key.json の CODE_* 設定）を返す。"""
        key = self._load_key_json()
        resolved_path = self._resolve_project_path(project_path)
        code_keys = {k: v for k, v in key.items() if k.startswith("CODE_")}
        return {
            "project_root": self.root,
            "resolved_project_path": resolved_path,
            "project_path_exists": os.path.isdir(resolved_path),
            "key_json": os.path.join(self.root, self.KEY_JSON_REL),
            "code_config": code_keys,
            "version_info": self.version_info,
        }

    def get_description(self) -> str:
        """利用可能な AI 一覧を含む code_agents_run の description を生成する。"""
        available = [(k, self.version_info[k]) for k in self.version_info if self.version_info[k].get("ok")]
        unavailable = [k for k in self.version_info if not self.version_info[k].get("ok")]

        lines = ["AIコード.py の CodeAgent を実行する。"]

        if available:
            ver_parts = []
            for ai_name, v in available:
                ver = v.get("version", "")
                ver_parts.append(f"{ai_name}({ver})" if ver else ai_name)
            lines.append(f"\n利用可能な ai_name: {', '.join(ver_parts)}")

        if unavailable:
            lines.append(f"利用不可の ai_name: {', '.join(unavailable)}")

        lines.append("""
Args:
    prompt: エージェントへの依頼テキスト
    project_path: 作業ディレクトリの絶対パス（省略時は AiDiy_key.json の CODE_BASE_PATH）
    ai_name: 使用 AI（上記の利用可能な ai_name から指定。"auto" は copilot_cli 優先で自動選択）
    ai_model: モデル名（"auto" で key.json の設定を使用）
    max_turns: 最大ターン数（default: 999）
    code_plan: プラン設定（auto / on / off）
    code_verify: 検証設定（auto / on / off）
    code_permissions: 権限設定（auto / full / none）
    system_instruction: システム指示（省略時はデフォルト文）
    resume: セッション継続フラグ
    timeout_sec: タイムアウト秒数""")

        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # エージェント実行
    # ------------------------------------------------------------------ #

    async def run_async(
        self,
        prompt: str,
        project_path: Optional[str] = None,
        ai_name: str = "auto",
        ai_model: str = "auto",
        max_turns: int = 999,
        code_plan: str = "auto",
        code_verify: str = "auto",
        code_permissions: str = "auto",
        system_instruction: Optional[str] = None,
        resume: bool = True,
        timeout_sec: int = 1200,
    ) -> dict:
        """
        AIコード.py の CodeAgent を使ってコードエージェントを実行する。

        Args:
            prompt: エージェントへの依頼テキスト
            project_path: 作業ディレクトリの絶対パス。
                          省略時は AiDiy_key.json の CODE_BASE_PATH を使用。
            ai_name: 使用 AI（例: claude_cli / copilot_cli / aidiy_hermes）。
                     "auto" は利用可能な最初の AI にフォールバック。
            ai_model: モデル名。"auto" は key.json の対応モデルにフォールバック。
            max_turns: 最大ターン数（default: 999）
            code_plan: プラン設定（auto / on / off）
            code_verify: 検証設定（auto / on / off）
            code_permissions: 権限設定（auto / full / none）
            system_instruction: システム指示（省略時はデフォルト文）
            resume: セッション継続フラグ
            timeout_sec: タイムアウト秒数

        Returns:
            {"status": "OK"/"NG", "result": "...", "project_path": "...", ...}
        """
        self._setup_sys_path()

        resolved_path = self._resolve_project_path(project_path)
        ai_name, ai_model = self._resolve_ai_params(ai_name, ai_model)

        # 利用不可の AI が指定された場合は早期リターン
        if ai_name in self.version_info and not self.version_info[ai_name].get("ok"):
            reason = self.version_info[ai_name].get("version", "利用不可")
            return {
                "status": "NG",
                "result": f"ai_name='{ai_name}' は利用できません: {reason}",
                "project_path": resolved_path,
                "ai_name": ai_name,
                "ai_model": ai_model,
                "prompt_length": len(prompt),
            }

        try:
            from AIコア.AIコード import CodeAgent  # noqa: PLC0415
        except Exception as e:
            raise CodeAgentsError(f"AIコード.py のインポートに失敗しました: {e}") from e

        agent = CodeAgent(
            セッションID="mcp_session",
            チャンネル="mcp",
            絶対パス=resolved_path,
            AI_NAME=ai_name,
            AI_MODEL=ai_model,
            接続=_NullConnection(),
            保存関数=None,
        )

        ai_instance = await agent._ensure_ai_instance()
        if not ai_instance:
            return {
                "status": "NG",
                "result": f"AIインスタンスの初期化に失敗しました (ai_name={ai_name})",
                "project_path": resolved_path,
                "ai_name": ai_name,
                "ai_model": ai_model,
                "prompt_length": len(prompt),
            }

        try:
            result_text = await ai_instance.実行(
                要求テキスト=prompt,
                絶対パス=resolved_path,
                タイムアウト秒数=timeout_sec,
                resume=resume,
            )
        finally:
            await ai_instance.終了()

        return {
            "status": "OK",
            "result": result_text or "（応答なし）",
            "project_path": resolved_path,
            "ai_name": ai_name,
            "ai_model": ai_model,
            "prompt_length": len(prompt),
        }

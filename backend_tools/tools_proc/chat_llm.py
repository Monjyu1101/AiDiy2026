# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""
Chat LLM モジュール

AIチャット.py 系の ChatAI を MCP ツールとして公開するラッパー。
aidiy_code_agents が AIコード を駆動するのに対し、本モジュールは AIチャット を駆動する。
起動時に key.json の CHAT_* 設定と各種 API キーから利用可能な ai_name を確認し、
MCP ツールの description で通知する。

ツール公開先:
    SSE: http://localhost:8095/aidiy_chat_llms/sse

加えて OpenAI / Ollama 互換の標準チャットインターフェース
(/aidiy_chat_completions) からも本ラッパーを利用する。
"""

import importlib
import inspect
import json
import os
import sys
from pathlib import Path
from typing import Any, Optional


class ChatLLMError(Exception):
    """ChatLLM 実行エラー"""
    pass


# ai_name -> (モジュール, モデル設定キー, APIキー設定キー)
_AI_TABLE = {
    "openrt_chat": ("AIコア.AIチャット_openrt", "CHAT_OPENRT_MODEL", "openrt_key_id"),
    "gemini_chat": ("AIコア.AIチャット_gemini", "CHAT_GEMINI_MODEL", "gemini_key_id"),
    "freeai_chat": ("AIコア.AIチャット_gemini", "CHAT_FREEAI_MODEL", "freeai_key_id"),
    "ollama_chat": ("AIコア.AIチャット_ollama", "CHAT_OLLAMA_MODEL", "ollama_key_id"),
}

# ai_name 候補（key.json の並びに依らず固定の優先順）
_AI_CANDIDATES = ["openrt_chat", "gemini_chat", "freeai_chat", "ollama_chat"]


class _ConfShim:
    """ChatAI が参照する 親.conf.json を模した薄いラッパー"""

    def __init__(self, data: dict):
        self.json = data or {}


class _ParentShim:
    """ChatAI コンストラクタに渡す 親 オブジェクトの最小実装"""

    def __init__(self, data: dict):
        self.conf = _ConfShim(data)

    def 最近のファイル取得(self, *args: Any, **kwargs: Any) -> list:
        return []


class ChatLLM:
    """AIチャット.py 系の ChatAI を MCP / HTTP 経由で起動するラッパークラス"""

    KEY_JSON_REL = os.path.join("backend_server", "_config", "AiDiy_key.json")

    def __init__(self, project_root: Optional[str] = None):
        if project_root:
            self.root = os.path.abspath(project_root)
        else:
            # backend_tools/tools_proc/ から 2 つ上がプロジェクトルート
            here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.root = os.path.dirname(here)

        # 起動時 API キー確認結果（tools_main.py から _check_ai_versions() で設定）
        self.version_info: dict[str, dict] = {}

        # resume 用セッションキャッシュ（session_id -> ChatAI インスタンス）
        self._sessions: dict[str, Any] = {}

    # ------------------------------------------------------------------ #
    # sys.path 設定
    # ------------------------------------------------------------------ #

    def _setup_sys_path(self) -> None:
        """backend_server を sys.path に追加（AIチャット.py のインポートに必要）"""
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
            with open(key_path, encoding="utf-8-sig") as f:
                return json.load(f)
        except Exception:
            return {}

    def _resolve_project_path(self, project_path: Optional[str] = None) -> str:
        """
        作業ディレクトリ（出力ファイル保存先）の絶対パスを解決する。

        1. project_path が指定されていれば絶対パスに正規化して返す。
        2. なければ AiDiy_key.json の CODE_BASE_PATH を使う
           （backend_server/_config/ 基準の相対パスとして解釈）。
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

    def _model_for(self, ai_name: str, key: dict) -> str:
        """ai_name に対応する既定モデル名を key.json から取得する"""
        entry = _AI_TABLE.get(ai_name)
        if not entry:
            return ""
        _, model_key, _ = entry
        return str(key.get(model_key, "") or "").strip()

    def _api_key_for(self, ai_name: str, key: dict) -> str:
        """ai_name に対応する API キーを取得する（freeai は gemini にフォールバック）"""
        if ai_name == "freeai_chat":
            return (key.get("freeai_key_id", "") or key.get("gemini_key_id", "")).strip()
        if ai_name == "ollama_chat":
            return (key.get("ollama_key_id", "") or "ollama").strip()
        entry = _AI_TABLE.get(ai_name)
        if not entry:
            return ""
        _, _, key_id = entry
        return str(key.get(key_id, "") or "").strip()

    def _resolve_ai_params(self, ai_name: str, ai_model: str) -> tuple[str, str]:
        """ai_name / ai_model の "auto" を key.json 値で解決する"""
        key = self._load_key_json()
        if ai_name == "auto" or not ai_name:
            # 利用可能 AI を優先、なければ key.json の CHAT_AI_NAME
            available = [k for k, v in self.version_info.items() if v.get("ok")]
            default_name = (key.get("CHAT_AI_NAME", "") or "").strip()
            if default_name in available:
                ai_name = default_name
            elif available:
                ai_name = available[0]
            else:
                ai_name = default_name or "freeai_chat"
        if ai_model == "auto" or not ai_model:
            ai_model = self._model_for(ai_name, key) or "auto"
        return ai_name, ai_model

    def _select_chat_class(self, ai_name: str):
        """ai_name に応じた ChatAI クラスをインポートして返す"""
        entry = _AI_TABLE.get(ai_name)
        module_name = entry[0] if entry else "AIコア.AIチャット_openrt"
        module = importlib.import_module(module_name)
        ChatAI = getattr(module, "ChatAI", None)
        if ChatAI is None:
            raise ChatLLMError(f"{module_name} に ChatAI クラスが見つかりません")
        return ChatAI

    @staticmethod
    def _inject_history(ai_instance: Any, role: str, text: str) -> None:
        """ChatAI 実装ごとに異なる _履歴追加 のシグネチャ差異を吸収して履歴を注入する"""
        fn = getattr(ai_instance, "_履歴追加", None)
        if fn is None or not text:
            return
        try:
            params = inspect.signature(fn).parameters
            if "role" in params:          # ollama / openrt 形式
                fn(role=role, text=text)
            elif "type" in params:        # gemini 形式
                fn(text=text, type=role)
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # 起動時 API キー確認
    # ------------------------------------------------------------------ #

    def _check_ai_versions(self) -> dict[str, dict]:
        """
        各 ai_name の利用可否を API キーの有無で判定して返す。
        ollama_chat はローカル接続前提のため常に利用可（実接続は実行時に判定）。
        """
        self._setup_sys_path()
        key = self._load_key_json()

        results: dict[str, dict] = {}
        for ai_name in _AI_CANDIDATES:
            model = self._model_for(ai_name, key)

            if ai_name == "ollama_chat":
                cloud_key = (key.get("ollama_key_id", "") or "").strip()
                cloud = bool(cloud_key) and not cloud_key.startswith("<")
                results[ai_name] = {
                    "ok": True,
                    "version": "ollama cloud" if cloud else "ollama local",
                    "model": model,
                }
                continue

            api_key = self._api_key_for(ai_name, key)
            ok = bool(api_key) and not api_key.startswith("<")
            entry = _AI_TABLE.get(ai_name)
            key_label = entry[2] if entry else "key"
            results[ai_name] = {
                "ok": ok,
                "version": f"{key_label} {'設定済' if ok else '未設定'}",
                "model": model,
            }

        return results

    # ------------------------------------------------------------------ #
    # 情報取得
    # ------------------------------------------------------------------ #

    def get_config(self, project_path: Optional[str] = None) -> dict:
        """設定情報（解決済みパス・key.json の CHAT_* 設定）を返す。"""
        key = self._load_key_json()
        resolved_path = self._resolve_project_path(project_path)
        chat_keys = {k: v for k, v in key.items() if k.startswith("CHAT_")}
        return {
            "project_root": self.root,
            "resolved_project_path": resolved_path,
            "project_path_exists": os.path.isdir(resolved_path),
            "key_json": os.path.join(self.root, self.KEY_JSON_REL),
            "chat_config": chat_keys,
            "version_info": self.version_info,
        }

    def available_models(self) -> list[dict]:
        """OpenAI 互換 /models 用に利用可能な ai_name 一覧を返す。"""
        models = []
        for ai_name, v in self.version_info.items():
            if v.get("ok"):
                models.append({
                    "id": ai_name,
                    "object": "model",
                    "owned_by": "aidiy",
                    "model": v.get("model", ""),
                })
        return models

    def get_description(self) -> str:
        """利用可能な ai_name 一覧を含む chat_llms_run の description を生成する。"""
        available = [(k, self.version_info[k]) for k in self.version_info if self.version_info[k].get("ok")]
        unavailable = [k for k in self.version_info if not self.version_info[k].get("ok")]

        lines = ["AIチャット.py 系の ChatAI を実行してテキスト応答を生成する。"]

        if available:
            parts = []
            for ai_name, v in available:
                model = v.get("model", "")
                parts.append(f"{ai_name}({model})" if model else ai_name)
            lines.append(f"\n利用可能な ai_name: {', '.join(parts)}")

        if unavailable:
            lines.append(f"利用不可の ai_name: {', '.join(unavailable)}")

        lines.append("""
Args:
    prompt: AI への入力テキスト
    project_path: 出力ファイル保存先の絶対パス（省略時は AiDiy_key.json の CODE_BASE_PATH）
    ai_name: 使用 AI（上記の利用可能な ai_name から指定。"auto" は CHAT_AI_NAME を優先）
    ai_model: モデル名（"auto" で key.json の設定を使用）
    system_instruction: システム指示（省略時はデフォルト文）
    session_id: 会話履歴のキー（resume=True 時に同一セッションの履歴を継続）
    resume: True で session_id の会話履歴を継続、False で毎回新規
    temperature: 生成温度（省略時はモジュール既定値）
    timeout_sec: タイムアウト秒数""")

        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # ChatAI インスタンス生成
    # ------------------------------------------------------------------ #

    async def _build_instance(
        self,
        ai_name: str,
        ai_model: str,
        system_instruction: Optional[str],
        resolved_path: str,
        temperature: Optional[float],
    ):
        """ChatAI インスタンスを生成・開始して返す。失敗時は None。"""
        key = self._load_key_json()
        api_key = self._api_key_for(ai_name, key)
        parent = _ParentShim(key)

        ChatAI = self._select_chat_class(ai_name)
        instance = ChatAI(
            親=parent,
            セッションID="mcp_session",
            チャンネル="0",
            絶対パス=resolved_path,
            AI_NAME=ai_name,
            AI_MODEL=ai_model,
            api_key=api_key or None,
            system_instruction=system_instruction,
        )
        if temperature is not None and hasattr(instance, "temperature"):
            try:
                instance.temperature = float(temperature)
            except (TypeError, ValueError):
                pass

        開始成功 = await instance.開始()
        if (開始成功 is False) or (not getattr(instance, "is_alive", False)):
            return None
        return instance

    # ------------------------------------------------------------------ #
    # 実行（aidiy_chat_llms: code_agents 互換インターフェース）
    # ------------------------------------------------------------------ #

    async def run_async(
        self,
        prompt: str,
        project_path: Optional[str] = None,
        ai_name: str = "auto",
        ai_model: str = "auto",
        system_instruction: Optional[str] = None,
        session_id: str = "mcp_default",
        resume: bool = True,
        temperature: Optional[float] = None,
        timeout_sec: int = 120,
        file_path: Optional[str] = None,
    ) -> dict:
        """
        AIチャット.py 系の ChatAI を使ってテキスト応答を生成する。

        Returns:
            {"status": "OK"/"NG", "result": "...", "ai_name": ..., "ai_model": ..., ...}
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
                "prompt_length": len(prompt or ""),
            }

        cache_key = f"{session_id}::{ai_name}::{ai_model}"
        instance = self._sessions.get(cache_key) if resume else None

        try:
            if instance is None:
                instance = await self._build_instance(
                    ai_name, ai_model, system_instruction, resolved_path, temperature
                )
                if instance is None:
                    return {
                        "status": "NG",
                        "result": f"AIインスタンスの初期化に失敗しました (ai_name={ai_name})",
                        "project_path": resolved_path,
                        "ai_name": ai_name,
                        "ai_model": ai_model,
                        "prompt_length": len(prompt or ""),
                    }
                if resume:
                    self._sessions[cache_key] = instance
            elif temperature is not None and hasattr(instance, "temperature"):
                try:
                    instance.temperature = float(temperature)
                except (TypeError, ValueError):
                    pass

            result_text = await instance.実行(
                要求テキスト=prompt,
                タイムアウト秒数=timeout_sec,
                システムプロンプト=system_instruction,
                file_path=file_path,
            )
            output_files = list(getattr(instance, "last_output_files", []) or [])
        finally:
            if not resume and instance is not None:
                try:
                    await instance.終了()
                except Exception:
                    pass

        return {
            "status": "OK",
            "result": result_text or "（応答なし）",
            "project_path": resolved_path,
            "ai_name": ai_name,
            "ai_model": ai_model,
            "output_files": output_files,
            "prompt_length": len(prompt or ""),
        }

    # ------------------------------------------------------------------ #
    # 実行（aidiy_chat_completions: OpenAI / Ollama 互換）
    # ------------------------------------------------------------------ #

    @staticmethod
    def _extract_parts(content: Any) -> tuple[str, list[str]]:
        """OpenAI messages の content（文字列 or パーツ配列）から
        テキストと画像 URL（data: / http(s) / ローカルパス）を抽出する。

        Returns:
            (テキスト, [画像URL, ...])
        """
        if content is None:
            return "", []
        if isinstance(content, str):
            return content, []
        if not isinstance(content, list):
            return str(content), []

        texts: list[str] = []
        images: list[str] = []
        for part in content:
            if isinstance(part, dict):
                ptype = part.get("type")
                if ptype in (None, "text") and "text" in part:
                    texts.append(str(part.get("text", "")))
                elif ptype == "image_url":
                    iu = part.get("image_url")
                    url = iu.get("url") if isinstance(iu, dict) else iu
                    if url:
                        images.append(str(url))
            else:
                texts.append(str(part))
        return "\n".join(t for t in texts if t), images

    def _materialize_image(self, url: str, dest_dir: str) -> Optional[str]:
        """画像 URL を一時ファイル化して絶対パスを返す。失敗時は None。

        - data: URL は base64 デコードして保存
        - http(s) URL はダウンロードして保存
        - 既存ローカルパスはそのまま返す
        """
        import base64  # noqa: PLC0415
        import os as _os  # noqa: PLC0415
        import tempfile  # noqa: PLC0415
        import urllib.request  # noqa: PLC0415

        _ext_by_mime = {
            "image/png": ".png", "image/jpeg": ".jpg", "image/jpg": ".jpg",
            "image/gif": ".gif", "image/webp": ".webp", "image/bmp": ".bmp",
        }
        try:
            if url.startswith("data:"):
                header, b64 = url.split(",", 1)
                mime = header[5:].split(";")[0].strip()
                ext = _ext_by_mime.get(mime, ".png")
                raw = base64.b64decode(b64)
            elif url.startswith(("http://", "https://")):
                with urllib.request.urlopen(url, timeout=30) as resp:  # noqa: S310
                    raw = resp.read()
                ext = _os.path.splitext(url.split("?")[0])[1] or ".png"
            elif _os.path.isfile(url):
                return str(Path(url).resolve())
            else:
                return None

            _os.makedirs(dest_dir, exist_ok=True)
            fd, path = tempfile.mkstemp(suffix=ext, prefix="chat_img_", dir=dest_dir)
            with _os.fdopen(fd, "wb") as f:
                f.write(raw)
            return path
        except Exception:
            return None

    def _parse_model_field(self, model: str, ai_name: str, ai_model: str) -> tuple[str, str]:
        """
        completions の model フィールドを ai_name / ai_model に解決する。

        - "ai_name/ai_model" 形式 → 分割
        - 候補 ai_name そのもの → ai_name として扱う
        - それ以外 → ai_model として扱う（ai_name は呼び出し側指定 or auto）
        """
        if not model:
            return ai_name, ai_model
        model = model.strip()
        if "/" in model:
            head, tail = model.split("/", 1)
            if head in _AI_TABLE:
                return head, (tail or "auto")
        if model in _AI_TABLE:
            return model, ai_model
        # 具体モデル名が来た場合は ai_model として採用
        return ai_name, model

    async def complete_async(
        self,
        messages: list,
        model: Optional[str] = None,
        ai_name: str = "auto",
        ai_model: str = "auto",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout_sec: int = 120,
        project_path: Optional[str] = None,
        tools: Optional[list] = None,
        tool_choice: Any = None,
    ) -> dict:
        """
        OpenAI / Ollama 互換の messages 配列を受けて 1 回の生成を行う。

        tools / tool_choice が指定された場合は OpenAI function calling として
        ChatAI へ completions_tools 経由で委譲し、tool_calls を回収して返す。

        Returns:
            {"status": "OK"/"NG", "content": "...", "ai_name": ..., "ai_model": ...,
             "output_files": [...], "tool_calls": [...] | None,
             "prompt_tokens": .., "completion_tokens": ..}
        """
        self._setup_sys_path()

        resolved_path = self._resolve_project_path(project_path)

        if model:
            ai_name, ai_model = self._parse_model_field(model, ai_name, ai_model)
        ai_name, ai_model = self._resolve_ai_params(ai_name, ai_model)

        if ai_name in self.version_info and not self.version_info[ai_name].get("ok"):
            reason = self.version_info[ai_name].get("version", "利用不可")
            return {
                "status": "NG",
                "content": f"ai_name='{ai_name}' は利用できません: {reason}",
                "ai_name": ai_name,
                "ai_model": ai_model,
            }

        # messages を system / 履歴 / 最後の user に分解（画像 URL も保持）
        system_parts: list[str] = []
        turns: list[tuple[str, str, list[str]]] = []  # (role, text, image_urls)
        for m in messages or []:
            if not isinstance(m, dict):
                continue
            role = m.get("role", "user")
            text, images = self._extract_parts(m.get("content"))
            if role == "system":
                if text:
                    system_parts.append(text)
            else:
                turns.append((role, text, images))

        system_instruction = "\n".join(system_parts) if system_parts else None

        # 最後のメッセージを要求テキスト・添付画像とし、それ以前を会話履歴にする。
        # （tool calling の 2 巡目では末尾が role="tool" の結果になるため、
        #   「最後の user」ではなく「最後のメッセージ」を要求として扱う）
        要求テキスト = ""
        last_images: list[str] = []
        history: list[tuple[str, str]] = []
        if turns:
            要求テキスト = turns[-1][1]
            last_images = turns[-1][2]
            history = [(r, t) for r, t, _ in turns[:-1]]

        prompt_chars = sum(len(t) for _, t, _ in turns) + sum(len(s) for s in system_parts)

        # tools / tool_choice を completions_tools(dict) に集約（空なら None=従来挙動）
        completions_tools: Optional[dict] = None
        if tools:
            completions_tools = {"tools": tools}
            if tool_choice is not None:
                completions_tools["tool_choice"] = tool_choice
            # tool calling 時は assistant.tool_calls / tool 結果のリンクを保つため、
            # 元の messages を忠実に API へ渡す（ChatAI のテキスト履歴再構成を上書き）。
            faithful: list[dict] = []
            for m in messages or []:
                if not isinstance(m, dict):
                    continue
                entry: dict = {"role": m.get("role", "user"), "content": m.get("content")}
                if m.get("tool_calls"):
                    entry["tool_calls"] = m["tool_calls"]
                if m.get("tool_call_id"):
                    entry["tool_call_id"] = m["tool_call_id"]
                if m.get("name"):
                    entry["name"] = m["name"]
                faithful.append(entry)
            if system_instruction and not any(e.get("role") == "system" for e in faithful):
                faithful.insert(0, {"role": "system", "content": system_instruction})
            completions_tools["messages"] = faithful

        instance = await self._build_instance(
            ai_name, ai_model, system_instruction, resolved_path, temperature
        )
        if instance is None:
            return {
                "status": "NG",
                "content": f"AIインスタンスの初期化に失敗しました (ai_name={ai_name})",
                "ai_name": ai_name,
                "ai_model": ai_model,
            }

        # 最後の user メッセージの先頭画像を一時ファイル化して file_path として渡す
        # （ChatAI 側は単一画像の file_path 添付に対応）
        file_path: Optional[str] = None
        temp_image_paths: list[str] = []
        if last_images:
            dest_dir = os.path.join(resolved_path, "temp", "input")
            for url in last_images:
                materialized = self._materialize_image(url, dest_dir)
                if materialized:
                    file_path = materialized
                    # 新規生成した一時ファイル（chat_img_*）だけ後始末対象にする
                    # （既存ローカルパスのパススルーは削除しない）
                    if os.path.basename(materialized).startswith("chat_img_"):
                        temp_image_paths.append(materialized)
                    break

        try:
            # 過去ターンを履歴注入（最後の user を除く）
            for role, text in history:
                norm_role = "assistant" if role in ("assistant", "model") else "user"
                self._inject_history(instance, norm_role, text)

            result_text = await instance.実行(
                要求テキスト=要求テキスト,
                タイムアウト秒数=timeout_sec,
                システムプロンプト=system_instruction,
                file_path=file_path,
                completions_tools=completions_tools,
            )
            output_files = list(getattr(instance, "last_output_files", []) or [])
            tool_calls = list(getattr(instance, "last_tool_calls", []) or [])
        finally:
            try:
                await instance.終了()
            except Exception:
                pass
            # 生成した一時画像を後始末
            for p in temp_image_paths:
                try:
                    if os.path.isfile(p):
                        os.remove(p)
                except Exception:
                    pass

        content = result_text or ""
        # tool_calls のみでテキストが無い場合、ChatAI は "!" を返すため空に正規化する
        if tool_calls and content.strip() in ("", "!"):
            content = ""
        return {
            "status": "OK",
            "content": content,
            "ai_name": ai_name,
            "ai_model": ai_model,
            "output_files": output_files,
            "tool_calls": tool_calls or None,
            "prompt_tokens": prompt_chars,
            "completion_tokens": len(content),
        }

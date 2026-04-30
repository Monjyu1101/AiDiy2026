"""Hermes Harness の全ツールのための中央レジストリ。

各ツールファイルはモジュールレベルで ``registry.register()`` を呼び出し、
スキーマ・ハンドラ・ツールセット所属・利用可否チェックを宣言します。
``model_tools.py`` は独自の並列データ構造を持たず、このレジストリに問い合わせます。

インポートの循環依存を回避するためのチェーン:
    tools/registry.py  (model_tools や各ツールファイルからのインポートなし)
           ^
    tools/*.py  (モジュールレベルで tools.registry からインポート)
           ^
    model_tools.py  (tools.registry + 全ツールモジュールをインポート)
"""

import ast
import importlib
import json
import logging
import threading
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


def _is_registry_register_call(node: ast.AST) -> bool:
    """``registry.register(...)`` 呼び出し式の場合に True を返す。"""
    if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
        return False
    func = node.value.func
    return (
        isinstance(func, ast.Attribute)
        and func.attr == "register"
        and isinstance(func.value, ast.Name)
        and func.value.id == "registry"
    )


def _module_registers_tools(module_path: Path) -> bool:
    """モジュールのトップレベルで ``registry.register(...)`` 呼び出しがある場合に True を返す。

    モジュール本文の文のみを検査するため、関数内で偶然 ``registry.register()``
    を呼び出すヘルパーモジュールが誤って検出されることはありません。
    """
    try:
        source = module_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(module_path))
    except (OSError, SyntaxError):
        return False

    return any(_is_registry_register_call(stmt) for stmt in tree.body)


def discover_builtin_tools(tools_dir: Optional[Path] = None) -> List[str]:
    """組み込みの自己登録ツールモジュールをインポートし、モジュール名のリストを返す。"""
    tools_path = Path(tools_dir) if tools_dir is not None else Path(__file__).resolve().parent
    # importlib 用の完全パッケージプレフィックスを決定する
    # __package__ は例えば "aidiy_hermes.tools" や "src.aidiy_hermes.tools"
    pkg = __package__ or "tools"
    module_names = [
        f"{pkg}.{path.stem}"
        for path in sorted(tools_path.glob("*.py"))
        if path.name not in {"__init__.py", "registry.py", "mcp_tool.py"}
        and _module_registers_tools(path)
    ]

    imported: List[str] = []
    for mod_name in module_names:
        try:
            importlib.import_module(mod_name)
            imported.append(mod_name)
        except Exception as e:
            logger.warning("ツールモジュール %s のインポートに失敗しました: %s", mod_name, e)
    return imported


class ToolEntry:
    """登録された単一ツールのメタデータ。"""

    __slots__ = (
        "name", "toolset", "schema", "handler", "check_fn",
        "requires_env", "is_async", "description", "emoji",
        "max_result_size_chars",
    )

    def __init__(self, name, toolset, schema, handler, check_fn,
                 requires_env, is_async, description, emoji,
                 max_result_size_chars=None):
        self.name = name
        self.toolset = toolset
        self.schema = schema
        self.handler = handler
        self.check_fn = check_fn
        self.requires_env = requires_env
        self.is_async = is_async
        self.description = description
        self.emoji = emoji
        self.max_result_size_chars = max_result_size_chars


class ToolRegistry:
    """ツールファイルからスキーマ＋ハンドラを収集するシングルトンレジストリ。"""

    def __init__(self):
        self._tools: Dict[str, ToolEntry] = {}
        self._toolset_checks: Dict[str, Callable] = {}
        self._toolset_aliases: Dict[str, str] = {}
        # MCP 動的リフレッシュは他スレッドがツールメタデータを読んでいる間に
        # レジストリを変更する可能性があるため、変更を直列化し、読み取りは
        # 安定したスナップショットに対して行う。
        self._lock = threading.RLock()

    def _snapshot_state(self) -> tuple[List[ToolEntry], Dict[str, Callable]]:
        """レジストリエントリとツールセットチェックの一貫性のあるスナップショットを返す。"""
        with self._lock:
            return list(self._tools.values()), dict(self._toolset_checks)

    def _snapshot_entries(self) -> List[ToolEntry]:
        """登録済みツールエントリの安定したスナップショットを返す。"""
        return self._snapshot_state()[0]

    def _snapshot_toolset_checks(self) -> Dict[str, Callable]:
        """ツールセット利用可否チェックの安定したスナップショットを返す。"""
        return self._snapshot_state()[1]

    def _evaluate_toolset_check(self, toolset: str, check: Callable | None) -> bool:
        """ツールセットチェックを実行し、チェックがない場合や失敗した場合は適切に扱う。"""
        if not check:
            return True
        try:
            return bool(check())
        except Exception:
            logger.debug("ツールセット %s のチェックで例外が発生したため、利用不可として扱います", toolset)
            return False

    def get_entry(self, name: str) -> Optional[ToolEntry]:
        """名前で登録済みツールエントリを返す。存在しない場合は None。"""
        with self._lock:
            return self._tools.get(name)

    def get_registered_toolset_names(self) -> List[str]:
        """レジストリに存在するユニークなツールセット名のソート済みリストを返す。"""
        return sorted({entry.toolset for entry in self._snapshot_entries()})

    def get_tool_names_for_toolset(self, toolset: str) -> List[str]:
        """指定されたツールセットに登録されているツール名のソート済みリストを返す。"""
        return sorted(
            entry.name for entry in self._snapshot_entries()
            if entry.toolset == toolset
        )

    def register_toolset_alias(self, alias: str, toolset: str) -> None:
        """正規ツールセット名に対する明示的なエイリアスを登録する。"""
        with self._lock:
            existing = self._toolset_aliases.get(alias)
            if existing and existing != toolset:
                logger.warning(
                    "ツールセットエイリアスの衝突: '%s' (%s) が %s によって上書きされました",
                    alias, existing, toolset,
                )
            self._toolset_aliases[alias] = toolset

    def get_registered_toolset_aliases(self) -> Dict[str, str]:
        """``{alias: 正規ツールセット名}`` マッピングのスナップショットを返す。"""
        with self._lock:
            return dict(self._toolset_aliases)

    def get_toolset_alias_target(self, alias: str) -> Optional[str]:
        """エイリアスの正規ツールセット名を返す。存在しない場合は None。"""
        with self._lock:
            return self._toolset_aliases.get(alias)

    # ------------------------------------------------------------------
    # 登録
    # ------------------------------------------------------------------

    def register(
        self,
        name: str,
        toolset: str,
        schema: dict,
        handler: Callable,
        check_fn: Callable = None,
        requires_env: list = None,
        is_async: bool = False,
        description: str = "",
        emoji: str = "",
        max_result_size_chars: int | float | None = None,
    ):
        """ツールを登録する。各ツールファイルのモジュールインポート時に呼び出される。"""
        with self._lock:
            existing = self._tools.get(name)
            if existing and existing.toolset != toolset:
                # MCP間の上書きは許可（正当なケース: サーバーリフレッシュ、
                # またはツール名が重複した2つのMCPサーバー）
                both_mcp = (
                    existing.toolset.startswith("mcp-")
                    and toolset.startswith("mcp-")
                )
                if both_mcp:
                    logger.debug(
                        "ツール '%s': MCPツールセット '%s' が MCPツールセット '%s' を上書き",
                        name, toolset, existing.toolset,
                    )
                else:
                    # シャドウイングを拒否 — プラグイン/MCPが組み込みツールを
                    # 上書きしたり、その逆を防ぐ
                    logger.error(
                        "ツール登録が拒否されました: '%s' (ツールセット '%s') は"
                        "既存ツール (ツールセット '%s') をシャドウします。"
                        "意図的である場合は先に既存ツールを登録解除してください。",
                        name, toolset, existing.toolset,
                    )
                    return
            self._tools[name] = ToolEntry(
                name=name,
                toolset=toolset,
                schema=schema,
                handler=handler,
                check_fn=check_fn,
                requires_env=requires_env or [],
                is_async=is_async,
                description=description or schema.get("description", ""),
                emoji=emoji,
                max_result_size_chars=max_result_size_chars,
            )
            if check_fn and toolset not in self._toolset_checks:
                self._toolset_checks[toolset] = check_fn

    def deregister(self, name: str) -> None:
        """レジストリからツールを削除する。

        同じツールセットに他のツールが残っていない場合、ツールセットチェックも
        クリーンアップする。MCP 動的ツールディスカバリがサーバーから
        ``notifications/tools/list_changed`` を受信した際の
        全削除＆再構築（nuke-and-repave）に使用される。
        """
        with self._lock:
            entry = self._tools.pop(name, None)
            if entry is None:
                return
            # このツールセットの最後のツールであれば、ツールセットチェックと
            # エイリアスを削除する
            toolset_still_exists = any(
                e.toolset == entry.toolset for e in self._tools.values()
            )
            if not toolset_still_exists:
                self._toolset_checks.pop(entry.toolset, None)
                self._toolset_aliases = {
                    alias: target
                    for alias, target in self._toolset_aliases.items()
                    if target != entry.toolset
                }
        logger.debug("ツール登録解除: %s", name)

    # ------------------------------------------------------------------
    # スキーマ取得
    # ------------------------------------------------------------------

    def get_definitions(self, tool_names: Set[str], quiet: bool = False) -> List[dict]:
        """要求されたツール名に対する OpenAI 形式のツールスキーマを返す。

        ``check_fn()`` が True を返す（または check_fn が設定されていない）
        ツールのみが含まれる。
        """
        result = []
        check_results: Dict[Callable, bool] = {}
        entries_by_name = {entry.name: entry for entry in self._snapshot_entries()}
        for name in sorted(tool_names):
            entry = entries_by_name.get(name)
            if not entry:
                continue
            if entry.check_fn:
                if entry.check_fn not in check_results:
                    try:
                        check_results[entry.check_fn] = bool(entry.check_fn())
                    except Exception:
                        check_results[entry.check_fn] = False
                        if not quiet:
                            logger.debug("ツール %s のチェックで例外が発生したためスキップ", name)
                if not check_results[entry.check_fn]:
                    if not quiet:
                        logger.debug("ツール %s は利用不可（チェック失敗）", name)
                    continue
            # スキーマに常に "name" フィールドがあることを保証 — フォールバックとして entry.name を使用
            schema_with_name = {**entry.schema, "name": entry.name}
            result.append({"type": "function", "function": schema_with_name})
        return result

    # ------------------------------------------------------------------
    # ディスパッチ
    # ------------------------------------------------------------------

    def dispatch(self, name: str, args: dict, **kwargs) -> str:
        """ツールハンドラを名前で実行する。

        * 非同期ハンドラは ``_run_async()`` を介して自動的にブリッジされる。
        * すべての例外は捕捉され、一貫したエラー形式で ``{"error": "..."}`` として返される。
        """
        entry = self.get_entry(name)
        if not entry:
            return json.dumps({"error": f"不明なツール: {name}"})
        try:
            if entry.is_async:
                from base.model_tools import _run_async
                return _run_async(entry.handler(args, **kwargs))
            return entry.handler(args, **kwargs)
        except Exception as e:
            logger.exception("ツール %s のディスパッチエラー: %s", name, e)
            return json.dumps({"error": f"ツール実行に失敗しました: {type(e).__name__}: {e}"})

    # ------------------------------------------------------------------
    # クエリヘルパー（model_tools.py の重複データ構造を置き換え）
    # ------------------------------------------------------------------

    def get_max_result_size(self, name: str, default: int | float | None = None) -> int | float:
        """ツールごとの最大結果サイズ、または *default*（またはグローバルデフォルト）を返す。"""
        entry = self.get_entry(name)
        if entry and entry.max_result_size_chars is not None:
            return entry.max_result_size_chars
        if default is not None:
            return default
        return 100000

    def get_all_tool_names(self) -> List[str]:
        """登録済みの全ツール名のソート済みリストを返す。"""
        return sorted(entry.name for entry in self._snapshot_entries())

    def get_schema(self, name: str) -> Optional[dict]:
        """ツールの生のスキーマ辞書を check_fn フィルタリングを経ずに返す。

        トークン推定や内省において、利用可否は関係なくスキーマの内容だけが
        必要な場合に有用。
        """
        entry = self.get_entry(name)
        return entry.schema if entry else None

    def get_toolset_for_tool(self, name: str) -> Optional[str]:
        """ツールが所属するツールセットを返す。存在しない場合は None。"""
        entry = self.get_entry(name)
        return entry.toolset if entry else None

    def get_emoji(self, name: str, default: str = "⚡") -> str:
        """ツールの絵文字を返す。未設定の場合は *default* を返す。"""
        entry = self.get_entry(name)
        return (entry.emoji if entry and entry.emoji else default)

    def get_tool_to_toolset_map(self) -> Dict[str, str]:
        """登録済み全ツールの ``{ツール名: ツールセット名}`` マップを返す。"""
        return {entry.name: entry.toolset for entry in self._snapshot_entries()}

    def is_toolset_available(self, toolset: str) -> bool:
        """ツールセットの要件が満たされているか確認する。

        チェック関数が予期しない例外（ネットワークエラー、インポート欠落、
        設定ミスなど）を発生させた場合も、False を返す（クラッシュしない）。
        """
        with self._lock:
            check = self._toolset_checks.get(toolset)
        return self._evaluate_toolset_check(toolset, check)

    def check_toolset_requirements(self) -> Dict[str, bool]:
        """全ツールセットの ``{ツールセット名: 利用可否}`` 辞書を返す。"""
        entries, toolset_checks = self._snapshot_state()
        toolsets = sorted({entry.toolset for entry in entries})
        return {
            toolset: self._evaluate_toolset_check(toolset, toolset_checks.get(toolset))
            for toolset in toolsets
        }

    def get_available_toolsets(self) -> Dict[str, dict]:
        """UI表示用のツールセットメタデータを返す。"""
        toolsets: Dict[str, dict] = {}
        entries, toolset_checks = self._snapshot_state()
        for entry in entries:
            ts = entry.toolset
            if ts not in toolsets:
                toolsets[ts] = {
                    "available": self._evaluate_toolset_check(
                        ts, toolset_checks.get(ts)
                    ),
                    "tools": [],
                    "description": "",
                    "requirements": [],
                }
            toolsets[ts]["tools"].append(entry.name)
            if entry.requires_env:
                for env in entry.requires_env:
                    if env not in toolsets[ts]["requirements"]:
                        toolsets[ts]["requirements"].append(env)
        return toolsets

    def get_toolset_requirements(self) -> Dict[str, dict]:
        """後方互換のための TOOLSET_REQUIREMENTS 互換辞書を構築する。"""
        result: Dict[str, dict] = {}
        entries, toolset_checks = self._snapshot_state()
        for entry in entries:
            ts = entry.toolset
            if ts not in result:
                result[ts] = {
                    "name": ts,
                    "env_vars": [],
                    "check_fn": toolset_checks.get(ts),
                    "setup_url": None,
                    "tools": [],
                }
            if entry.name not in result[ts]["tools"]:
                result[ts]["tools"].append(entry.name)
            for env in entry.requires_env:
                if env not in result[ts]["env_vars"]:
                    result[ts]["env_vars"].append(env)
        return result

    def check_tool_availability(self, quiet: bool = False):
        """従来の関数と同様に (available_toolsets, unavailable_info) を返す。"""
        available = []
        unavailable = []
        seen = set()
        entries, toolset_checks = self._snapshot_state()
        for entry in entries:
            ts = entry.toolset
            if ts in seen:
                continue
            seen.add(ts)
            if self._evaluate_toolset_check(ts, toolset_checks.get(ts)):
                available.append(ts)
            else:
                unavailable.append({
                    "name": ts,
                    "env_vars": entry.requires_env,
                    "tools": [e.name for e in entries if e.toolset == ts],
                })
        return available, unavailable


# モジュールレベルのシングルトン
registry = ToolRegistry()


# ---------------------------------------------------------------------------
# ツール応答シリアライゼーション用ヘルパー
# ---------------------------------------------------------------------------
# 全てのツールハンドラは JSON 文字列を返さなければなりません。
# これらのヘルパーは、ツールファイル全体で何百回も出現する
# ``json.dumps({"error": msg}, ensure_ascii=False)`` というボイラープレートを排除します。
#
# 使用例:
#   from tools.registry import registry, tool_error, tool_result
#
#   return tool_error("something went wrong")
#   return tool_error("not found", code=404)
#   return tool_result(success=True, data=payload)
#   return tool_result(items)            # 辞書を直接渡す


def tool_error(message, **extra) -> str:
    """ツールハンドラ用の JSON エラー文字列を返す。

    >>> tool_error("file not found")
    '{"error": "file not found"}'
    >>> tool_error("bad input", success=False)
    '{"error": "bad input", "success": false}'
    """
    result = {"error": str(message)}
    if extra:
        result.update(extra)
    return json.dumps(result, ensure_ascii=False)


def tool_result(data=None, **kwargs) -> str:
    """ツールハンドラ用の JSON 結果文字列を返す。

    位置引数の辞書 *または* キーワード引数（両方不可）を受け付けます:

    >>> tool_result(success=True, count=42)
    '{"success": true, "count": 42}'
    >>> tool_result({"key": "value"})
    '{"key": "value"}'
    """
    if data is not None:
        return json.dumps(data, ensure_ascii=False)
    return json.dumps(kwargs, ensure_ascii=False)

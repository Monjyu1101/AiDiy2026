"""モデルツールモジュール

ツールレジストリ上の薄いオーケストレーション層。tools/ 内の各ツールファイルは
tools.registry.register() を介して自身のスキーマ・ハンドラ・メタデータを自己登録します。
このモジュールはディスカバリ（全ツールモジュールのインポート）をトリガーし、
run_agent.py や cli.py が使用するパブリック API を提供します。

パブリック API（元の 2400 行版からシグネチャ維持）:
    get_tool_definitions(enabled_toolsets, disabled_toolsets, quiet_mode) -> list
    handle_function_call(function_name, function_args, task_id, user_task) -> str
    TOOL_TO_TOOLSET_MAP: dict          (batch_runner.py 向け)
    TOOLSET_REQUIREMENTS: dict         (cli.py, doctor.py 向け)
    get_all_tool_names() -> list
    get_toolset_for_tool(name) -> str
    get_available_toolsets() -> dict
    check_toolset_requirements() -> dict
    check_tool_availability(quiet) -> tuple
"""

import json
import asyncio
import logging
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from tools.registry import registry, discover_builtin_tools
from base.toolsets import resolve_toolset, validate_toolset

logger = logging.getLogger(__name__)


# =============================================================================
# Async ブリッジ（registry.dispatch も使用する唯一の正統ソース）
# =============================================================================

_tool_loop = None          # メイン（CLI）スレッド用の永続ループ
_tool_loop_lock = threading.Lock()
_worker_thread_local = threading.local()  # ワーカースレッドごとの永続ループ


def _get_tool_loop():
    """非同期ツールハンドラ実行用の長命イベントループを返す。

    毎回作成して*閉じる* asyncio.run() の代わりに永続ループを使うことで、
    キャッシュされた httpx/AsyncOpenAI クライアントがガベージコレクション時に
    終了したループ上でトランスポートをクローズしようとして発生する
    "Event loop is closed" エラーを防ぐ。
    """
    global _tool_loop
    with _tool_loop_lock:
        if _tool_loop is None or _tool_loop.is_closed():
            _tool_loop = asyncio.new_event_loop()
        return _tool_loop


def _get_worker_loop():
    """現在のワーカースレッド用の永続イベントループを返す。

    各ワーカースレッド（例: delegate_task の ThreadPoolExecutor スレッド）は
    スレッドローカルストレージに自身の長命ループを持ちます。これにより、
    呼び出しごとに asyncio.run() を使用していた際に発生した "Event loop is closed"
    エラーを防ぎます。
    """
    loop = getattr(_worker_thread_local, 'loop', None)
    if loop is None or loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        _worker_thread_local.loop = loop
    return loop


def _run_async(coro):
    """同期コンテキストから非同期コルーチンを実行する。

    既に実行中のイベントループがある場合（ゲートウェイや Atropos の内部など）、
    競合を避けるため使い捨てスレッドを起動する。

    通常の CLI パス（実行中のループなし）では、キャッシュされた非同期クライアント
    （httpx / AsyncOpenAI）が生きたループにバインドされたままになり、
    GC 時に "Event loop is closed" を発生させないよう、永続イベントループを使用する。

    ワーカースレッドから呼び出された場合（並列ツール実行）、メインスレッドの共有ループ
    との競合と asyncio.run() の作成＆破棄ライフサイクルによるエラーの両方を回避するため、
    スレッドごとの永続ループを使用する。

    これはツールハンドラにおける同期→非同期ブリッジの唯一の正統ソースである。
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # 非同期コンテキスト内（ゲートウェイ、RL 環境）— 新しいスレッドで実行
        import concurrent.futures
        pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = pool.submit(asyncio.run, coro)
        try:
            return future.result(timeout=300)
        except concurrent.futures.TimeoutError:
            future.cancel()
            raise
        finally:
            pool.shutdown(wait=False, cancel_futures=True)

    # ワーカースレッド上の場合（例: delegate_task での並列ツール実行）、
    # スレッドごとの永続ループを使用
    if threading.current_thread() is not threading.main_thread():
        worker_loop = _get_worker_loop()
        return worker_loop.run_until_complete(coro)

    tool_loop = _get_tool_loop()
    return tool_loop.run_until_complete(coro)


# =============================================================================
# ツールディスカバリ（各モジュールのインポートで registry.register 呼び出しが発生）
# =============================================================================

# file_tools を明示的にインポートして registry.register() 呼び出しをトリガー
from tools import file_tools  # noqa: F401

# 他の組み込みツールモジュールを自動ディスカバリ
discover_builtin_tools()


# =============================================================================
# 後方互換定数（ディスカバリ後に一度だけ構築）
# =============================================================================

TOOL_TO_TOOLSET_MAP: Dict[str, str] = registry.get_tool_to_toolset_map()

TOOLSET_REQUIREMENTS: Dict[str, dict] = registry.get_toolset_requirements()

# 最後の get_tool_definitions() 呼び出しで解決されたツール名。
# execute_code がこのセッションで利用可能なツールを知るために使用。
_last_resolved_tool_names: List[str] = []


# =============================================================================
# レガシーツールセット名マッピング（旧 _tools サフィックス名 → ツール名リスト）
# =============================================================================

_LEGACY_TOOLSET_MAP = {
    "web_tools": ["web_search", "web_extract"],
    "terminal_tools": ["terminal"],
    "vision_tools": ["vision_analyze"],
    "moa_tools": ["mixture_of_agents"],
    "image_tools": ["image_generate"],
    "video_tools": ["create_video_from_images"],
    "skills_tools": ["skills_list", "skill_view", "skill_manage"],
    "browser_tools": [
        "browser_navigate", "browser_snapshot", "browser_click",
        "browser_type", "browser_scroll", "browser_back",
        "browser_press", "browser_get_images",
        "browser_vision", "browser_console",
    ],
    "cronjob_tools": ["cronjob"],
    "rl_tools": [
        "rl_list_environments", "rl_select_environment",
        "rl_get_current_config", "rl_edit_config",
        "rl_start_training", "rl_check_status",
        "rl_stop_training", "rl_get_results",
        "rl_list_runs", "rl_test_inference",
    ],
    "file_tools": ["read_file", "write_file", "patch", "search_files"],
    "tts_tools": ["text_to_speech"],
}


# =============================================================================
# get_tool_definitions（メインスキーマプロバイダ）
# =============================================================================


def get_tool_definitions(
    enabled_toolsets: List[str] = None,
    disabled_toolsets: List[str] = None,
    quiet_mode: bool = False,
) -> List[Dict[str, Any]]:
    """ツールセットベースのフィルタリングでモデル API 呼び出し用のツール定義を取得する。

    全てのツールはアクセス可能になるためにツールセットに属している必要がある。

    Args:
        enabled_toolsets: これらのツールセットからのツールのみを含める。
        disabled_toolsets: これらのツールセットのツールを除外（enabled_toolsets が None の場合）。
        quiet_mode: ステータス表示を抑制。

    Returns:
        フィルタリング済みの OpenAI 形式ツール定義リスト。
    """
    # 呼び出し元が要求するツール名を決定
    tools_to_include: set = set()

    if enabled_toolsets is not None:
        for toolset_name in enabled_toolsets:
            if validate_toolset(toolset_name):
                resolved = resolve_toolset(toolset_name)
                tools_to_include.update(resolved)
                if not quiet_mode:
                    print(f"✅ 有効化されたツールセット '{toolset_name}': {', '.join(resolved) if resolved else 'ツールなし'}")
            elif toolset_name in _LEGACY_TOOLSET_MAP:
                legacy_tools = _LEGACY_TOOLSET_MAP[toolset_name]
                tools_to_include.update(legacy_tools)
                if not quiet_mode:
                    print(f"✅ 有効化されたレガシーツールセット '{toolset_name}': {', '.join(legacy_tools)}")
            else:
                if not quiet_mode:
                    print(f"⚠️  不明なツールセット: {toolset_name}")

    elif disabled_toolsets:
        from base.toolsets import get_all_toolsets
        for ts_name in get_all_toolsets():
            tools_to_include.update(resolve_toolset(ts_name))

        for toolset_name in disabled_toolsets:
            if validate_toolset(toolset_name):
                resolved = resolve_toolset(toolset_name)
                tools_to_include.difference_update(resolved)
                if not quiet_mode:
                    print(f"🚫 無効化されたツールセット '{toolset_name}': {', '.join(resolved) if resolved else 'ツールなし'}")
            elif toolset_name in _LEGACY_TOOLSET_MAP:
                legacy_tools = _LEGACY_TOOLSET_MAP[toolset_name]
                tools_to_include.difference_update(legacy_tools)
                if not quiet_mode:
                    print(f"🚫 無効化されたレガシーツールセット '{toolset_name}': {', '.join(legacy_tools)}")
            else:
                if not quiet_mode:
                    print(f"⚠️  不明なツールセット: {toolset_name}")
    else:
        from base.toolsets import get_all_toolsets
        for ts_name in get_all_toolsets():
            tools_to_include.update(resolve_toolset(ts_name))

    # レジストリにスキーマを問い合わせ（check_fn が通るツールのみ返る）
    filtered_tools = registry.get_definitions(tools_to_include, quiet=quiet_mode)

    # 実際に check_fn フィルタリングを通ったツール名のセット
    available_tool_names = {t["function"]["name"] for t in filtered_tools}

    if not quiet_mode:
        if filtered_tools:
            tool_names = [t["function"]["name"] for t in filtered_tools]
            print(f"🛠️  最終ツール選択 ({len(filtered_tools)} ツール): {', '.join(tool_names)}")
        else:
            print("🛠️  ツール未選択（全てフィルタリングアウトまたは利用不可）")

    global _last_resolved_tool_names
    _last_resolved_tool_names = [t["function"]["name"] for t in filtered_tools]

    return filtered_tools


# =============================================================================
# handle_function_call（メインディスパッチャ）
# =============================================================================

# 旧 run_agent.py では memory/session_search/delegate_task をエージェントループ側で
# インターセプトしていた。現在は必要な状態を dispatch のキーワード引数に渡し、
# registry 登録済みハンドラへ一本化する。
_AGENT_LOOP_TOOLS: set[str] = set()
_READ_SEARCH_TOOLS = {"read_file", "search_files"}


# =========================================================================
# ツール引数の型強制
# =========================================================================


def coerce_tool_args(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """ツール呼び出しの引数を JSON Schema の型に合わせて強制する。

    LLM は数値を文字列（``"42"`` の代わりに ``42``）やブール値を文字列
    （``"true"`` の代わりに ``true``）として返すことが頻繁にある。
    各引数の値をツールの登録済み JSON Schema と比較し、値が文字列で
    スキーマが異なる型を期待する場合に安全な型強制を試みる。
    強制に失敗した場合は元の値を保持する。

    ``"type": "integer"``, ``"type": "number"``, ``"type": "boolean"``,
    およびユニオン型（``"type": ["integer", "string"]``）を処理する。
    """
    if not args or not isinstance(args, dict):
        return args

    schema = registry.get_schema(tool_name)
    if not schema:
        return args

    properties = (schema.get("parameters") or {}).get("properties")
    if not properties:
        return args

    for key, value in args.items():
        if not isinstance(value, str):
            continue
        prop_schema = properties.get(key)
        if not prop_schema:
            continue
        expected = prop_schema.get("type")
        if not expected and not _schema_allows_null(prop_schema):
            continue
        coerced = _coerce_value(value, expected, schema=prop_schema)
        if coerced is not value:
            args[key] = coerced

    return args


def _coerce_value(value: str, expected_type, schema: dict | None = None):
    """文字列 *value* を *expected_type* に強制する。

    強制が適用できない場合や失敗した場合は元の文字列を返す。
    """
    if _schema_allows_null(schema) and value.strip().lower() == "null":
        return None

    if isinstance(expected_type, list):
        # ユニオン型 — 各型を順に試し、最初に成功したものを返す
        for t in expected_type:
            result = _coerce_value(value, t, schema=schema)
            if result is not value:
                return result
        return value

    if expected_type in ("integer", "number"):
        return _coerce_number(value, integer_only=(expected_type == "integer"))
    if expected_type == "boolean":
        return _coerce_boolean(value)
    if expected_type == "array":
        return _coerce_json(value, list)
    if expected_type == "object":
        return _coerce_json(value, dict)
    if expected_type == "null" and value.strip().lower() == "null":
        return None
    return value


def _schema_allows_null(schema: dict | None) -> bool:
    """JSON Schema フラグメントが明示的に null を許可する場合に True を返す。"""
    if not isinstance(schema, dict):
        return False

    schema_type = schema.get("type")
    if schema_type == "null":
        return True
    if isinstance(schema_type, list) and "null" in schema_type:
        return True
    if schema.get("nullable") is True:
        return True

    for union_key in ("anyOf", "oneOf"):
        variants = schema.get(union_key)
        if not isinstance(variants, list):
            continue
        for variant in variants:
            if isinstance(variant, dict) and variant.get("type") == "null":
                return True

    return False


def _coerce_json(value: str, expected_python_type: type):
    """スキーマが配列やオブジェクトを期待する場合に *value* を JSON としてパースする。

    LLM が複雑な oneOf/discriminated-union スキーマの出力として配列/オブジェクトを
    ネイティブ構造ではなく JSON 文字列として出力した場合に対処する。
    パース失敗時や期待する Python 型と異なる場合は元の文字列を返す。
    """
    try:
        parsed = json.loads(value)
    except (ValueError, TypeError):
        return value
    if isinstance(parsed, expected_python_type):
        logger.debug(
            "coerce_tool_args: 文字列を %s に json.loads で強制",
            expected_python_type.__name__,
        )
        return parsed
    return value


def _coerce_number(value: str, integer_only: bool = False):
    """*value* を数値としてパースする。失敗時は元の文字列を返す。"""
    try:
        f = float(value)
    except (ValueError, OverflowError):
        return value
    # inf/nan は JSON シリアライズ不可なので元の文字列を保持
    if f != f or f == float("inf") or f == float("-inf"):
        return value
    # 整数に見える場合（小数部なし）は int を返す
    if f == int(f):
        return int(f)
    if integer_only:
        # スキーマは整数を期待しているが値に小数がある — 文字列のまま保持
        return value
    return f


def _coerce_boolean(value: str):
    """*value* をブール値としてパースする。失敗時は元の文字列を返す。"""
    low = value.strip().lower()
    if low == "true":
        return True
    if low == "false":
        return False
    return value


def _build_agent_dispatch_context(
    function_name: str,
    parent_agent: Any = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """旧版ツールが必要とするエージェント状態を registry.dispatch 用に整える。"""
    if parent_agent is None:
        context: Dict[str, Any] = {"current_session_id": session_id}
        if function_name == "session_search":
            try:
                from base.hermes_state import SessionDB

                context["db"] = SessionDB()
            except Exception as exc:
                logger.debug("SessionDB initialization skipped: %s", exc, exc_info=True)
        return context

    context: Dict[str, Any] = {
        "parent_agent": parent_agent,
        "store": getattr(parent_agent, "_memory_store", None),
        "db": getattr(parent_agent, "_session_db", None),
        "current_session_id": session_id or getattr(parent_agent, "session_id", None),
    }

    if function_name == "session_search" and context["db"] is None:
        try:
            from base.hermes_state import SessionDB

            context["db"] = SessionDB()
            setattr(parent_agent, "_session_db", context["db"])
        except Exception as exc:
            logger.debug("SessionDB initialization skipped: %s", exc, exc_info=True)

    return context


def handle_function_call(
    function_name: str,
    function_args: Dict[str, Any],
    task_id: Optional[str] = None,
    tool_call_id: Optional[str] = None,
    session_id: Optional[str] = None,
    user_task: Optional[str] = None,
    enabled_tools: Optional[List[str]] = None,
    parent_agent: Any = None,
    skip_pre_tool_call_hook: bool = False,
) -> str:
    """ツール呼び出しをツールレジストリにルーティングするメインディスパッチャ。

    Args:
        function_name: 呼び出す関数の名前。
        function_args: 関数の引数。
        task_id: ターミナル/ブラウザセッション分離用の一意識別子。
        user_task: ユーザーの元のタスク（browser_snapshot コンテキスト用）。
        enabled_tools: このセッションで有効なツール名。
                       execute_code はこのリストを使用してどのサンドボックスツールを
                       生成するか決定する。後方互換のためプロセスグローバルの
                       ``_last_resolved_tool_names`` にフォールバック。

    Returns:
        関数の結果を JSON 文字列として返す。
    """
    # 文字列引数をスキーマ宣言された型に強制（例: "42"→42）
    function_args = coerce_tool_args(function_name, function_args)

    try:
        if function_name in _AGENT_LOOP_TOOLS:
            return json.dumps({"error": f"{function_name} はエージェントループで処理される必要があります"})

        # ツールディスパッチレイテンシを計測
        _dispatch_start = time.monotonic()
        agent_context = _build_agent_dispatch_context(function_name, parent_agent, session_id)
        if function_name == "execute_code":
            # 呼び出し元が指定したリストを優先。サブエージェントがプロセスグローバルを
            # 上書きできないようにする。
            sandbox_enabled = enabled_tools if enabled_tools is not None else _last_resolved_tool_names
            result = registry.dispatch(
                function_name, function_args,
                task_id=task_id,
                enabled_tools=sandbox_enabled,
                **agent_context,
            )
        else:
            result = registry.dispatch(
                function_name, function_args,
                task_id=task_id,
                user_task=user_task,
                **agent_context,
            )

        return result

    except Exception as e:
        error_msg = f"{function_name} の実行エラー: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


# =============================================================================
# 後方互換ラッパー関数
# =============================================================================


def get_all_tool_names() -> List[str]:
    """登録済みの全ツール名を返す。"""
    return registry.get_all_tool_names()


def get_toolset_for_tool(tool_name: str) -> Optional[str]:
    """ツールが属するツールセットを返す。"""
    return registry.get_toolset_for_tool(tool_name)


def get_available_toolsets() -> Dict[str, dict]:
    """UI 表示用のツールセット利用可否情報を返す。"""
    return registry.get_available_toolsets()


def check_toolset_requirements() -> Dict[str, bool]:
    """登録済み全ツールセットの {ツールセット: 利用可否} 辞書を返す。"""
    return registry.check_toolset_requirements()


def check_tool_availability(quiet: bool = False) -> Tuple[List[str], List[dict]]:
    """(利用可能なツールセット, 利用不可の情報) を返す。"""
    return registry.check_tool_availability(quiet=quiet)

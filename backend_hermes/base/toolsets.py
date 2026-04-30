"""
ツールセットモジュール

ツールのエイリアス/ツールセットを定義・管理するための柔軟なシステムを提供します。
ツールセットを使うと、特定のシナリオ向けにツールをグループ化でき、
個別のツールや他のツールセットから構成することができます。

機能:
- 特定のツールを含むカスタムツールセットの定義
- 他のツールセットからのツールセット構成
- 一般的なユースケース向けの組み込みツールセット
- 新しいツールセットの容易な拡張
- 動的なツールセット解決のサポート

使用例:
    from base.toolsets import get_toolset, resolve_toolset, get_all_toolsets

    # 特定のツールセットの定義を取得
    tools = get_toolset("research")

    # ツールセットを解決して全ツール名を取得（構成されたツールセットも含む）
    all_tools = resolve_toolset("full_stack")
"""
from typing import Any, Dict, List, Optional, Set


# CLIおよび全メッセージングプラットフォームのツールセットで共有されるコアツールリスト。
# ここを編集すれば全プラットフォームに同時に反映されます。
_HERMES_CORE_TOOLS = [
    # Web
    "web_search", "web_extract",
    # ターミナル + プロセス管理
    "terminal", "process",
    # ファイル操作
    "read_file", "write_file", "patch", "search_files",
    # ビジョン + 画像生成
    "vision_analyze", "image_generate", "create_video_from_images",
    # スキル
    "skills_list", "skill_view", "skill_manage",
    # ブラウザ自動化
    "browser_navigate", "browser_snapshot", "browser_click",
    "browser_type", "browser_scroll", "browser_back",
    "browser_press", "browser_get_images",
    "browser_vision", "browser_console", "browser_cdp", "browser_dialog",
    # テキスト読み上げ
    "text_to_speech",
    # 計画 & メモリ
    "todo", "memory",
    # セッション履歴検索
    "session_search",
    # 確認質問
    "clarify",
    # コード実行 + 委譲
    "execute_code", "delegate_task",
    # Cronジョブ管理
    "cronjob",
]

# ツールセット定義
# 個別のツールまたは他のツールセットへの参照を含められます
TOOLSETS = {
    # 基本ツールセット - 個別のツールカテゴリ
    "web": {
        "description": "Webリサーチとコンテンツ抽出ツール",
        "tools": ["web_search", "web_extract"],
        "includes": [],
    },
    "search": {
        "description": "Web検索のみ（コンテンツ抽出/スクレイピングなし）",
        "tools": ["web_search"],
        "includes": [],
    },
    "vision": {
        "description": "画像分析とビジョンツール",
        "tools": ["vision_analyze"],
        "includes": [],
    },
    "image_gen": {
        "description": "クリエイティブ生成ツール（画像）",
        "tools": ["image_generate"],
        "includes": [],
    },
    "video": {
        "description": "画像列から動画を作成するツール",
        "tools": ["create_video_from_images"],
        "includes": [],
    },
    "terminal": {
        "description": "ターミナル/コマンド実行とプロセス管理ツール",
        "tools": ["terminal", "process"],
        "includes": [],
    },
    "skills": {
        "description": "スキルドキュメントへのアクセス、作成、編集、管理",
        "tools": ["skills_list", "skill_view", "skill_manage"],
        "includes": [],
    },
    "browser": {
        "description": "Web操作用ブラウザ自動化（ナビゲート、クリック、入力、スクロール、iframe、長押しクリック）+ URL検索用Web検索",
        "tools": [
            "browser_navigate", "browser_snapshot", "browser_click",
            "browser_type", "browser_scroll", "browser_back",
            "browser_press", "browser_get_images",
            "browser_vision", "browser_console", "browser_cdp", "browser_dialog",
            "web_search",
        ],
        "includes": [],
    },
    "file": {
        "description": "ファイル操作ツール: 読み取り、書き込み、パッチ（ファジーマッチング）、検索（コンテンツ+ファイル）",
        "tools": ["read_file", "write_file", "patch", "search_files"],
        "includes": [],
    },
    "tts": {
        "description": "テキスト読み上げ: Edge TTS（無料）、ElevenLabs、OpenAI、xAIでテキストを音声に変換",
        "tools": ["text_to_speech"],
        "includes": [],
    },
    "todo": {
        "description": "マルチステップ作業のタスク計画と追跡",
        "tools": ["todo"],
        "includes": [],
    },
    "memory": {
        "description": "セッションを越えた永続メモリ（個人メモ + ユーザープロファイル）",
        "tools": ["memory"],
        "includes": [],
    },
    "session_search": {
        "description": "過去の会話の検索と要約による呼び出し",
        "tools": ["session_search"],
        "includes": [],
    },
    "clarify": {
        "description": "ユーザーに確認質問を投げかける（多肢選択式または自由記述式）",
        "tools": ["clarify"],
        "includes": [],
    },
    "code_execution": {
        "description": "ツールをプログラムから呼び出すPythonスクリプトの実行（LLMのラウンドトリップを削減）",
        "tools": ["execute_code"],
        "includes": [],
    },
    "delegation": {
        "description": "複雑なサブタスク用に分離されたコンテキストを持つサブエージェントを起動",
        "tools": ["delegate_task"],
        "includes": [],
    },
    "cronjob": {
        "description": "Cronジョブ管理ツール - 作成、一覧表示、更新、一時停止、再開、削除、トリガー",
        "tools": ["cronjob"],
        "includes": [],
    },
    # シナリオ固有のツールセット
    "debugging": {
        "description": "デバッグとトラブルシューティングのツールキット",
        "tools": ["terminal", "process"],
        "includes": ["web", "file"],
    },
    "safe": {
        "description": "ターミナルアクセスなしのセーフツールキット",
        "tools": [],
        "includes": ["web", "vision", "image_gen"],
    },
}

# ハーネスコアツールセット
_HERMES_HARNESS_TOOLS = list(_HERMES_CORE_TOOLS)

TOOLSETS["aidiy-hermes"] = {
    "description": "AiDiy CLIデフォルトツールセット - 全コアツール",
    "tools": _HERMES_HARNESS_TOOLS,
    "includes": [],
}


def get_toolset(name: str) -> Optional[Dict[str, Any]]:
    """名前でツールセット定義を取得する。

    Args:
        name: ツールセット名

    Returns:
        Dict: description、tools、includesを含むツールセット定義
        None: ツールセットが見つからない場合
    """
    toolset = TOOLSETS.get(name)
    if toolset:
        return toolset

    # プラグイン/レジストリからのツールセットを試す
    try:
        from tools.registry import registry
    except Exception:
        return None

    registry_toolset = name
    description = f"プラグインツールセット: {name}"
    alias_target = registry.get_toolset_alias_target(name)

    if name not in _get_plugin_toolset_names():
        registry_toolset = alias_target
        if not registry_toolset:
            return None
        description = f"MCPサーバー '{name}' のツール"
    else:
        reverse_aliases = {
            canonical: alias
            for alias, canonical in _get_registry_toolset_aliases().items()
            if alias not in TOOLSETS
        }
        alias = reverse_aliases.get(name)
        if alias:
            description = f"MCPサーバー '{alias}' のツール"

    return {
        "description": description,
        "tools": registry.get_tool_names_for_toolset(registry_toolset),
        "includes": [],
    }


def resolve_toolset(name: str, visited: Set[str] = None) -> List[str]:
    """ツールセットを再帰的に解決して全ツール名を取得する。

    ツールセットの構成を処理し、含まれているツールセットを再帰的に解決して
    すべてのツールを結合します。

    Args:
        name: 解決するツールセット名
        visited: 訪問済みツールセットのセット（循環検出用）

    Returns:
        List[str]: ツールセット内の全ツール名のリスト
    """
    if visited is None:
        visited = set()

    # 全ツールセットの全ツールを表す特別なエイリアス
    # これにより、コード変更なしで将来のツールセットが自動的に含まれます。
    if name in {"all", "*"}:
        all_tools: Set[str] = set()
        for toolset_name in get_toolset_names():
            # ブランチ間の汚染を避けるため、各ブランチごとに新しいvisitedセットを使用
            resolved = resolve_toolset(toolset_name, visited.copy())
            all_tools.update(resolved)
        return sorted(all_tools)

    # 循環/既解決のチェック（ダイヤモンド依存関係）
    # サイレントに [] を返す — ダイヤモンドの場合（バグではなく、別パスで既に収集済み）
    # または真の循環（スキップしても安全）
    if name in visited:
        return []

    visited.add(name)

    toolset = get_toolset(name)
    if not toolset:
        return []

    tools = set(toolset.get("tools", []))

    # 含まれているツールセットを再帰的に解決し、visitedセットを共有して
    # ダイヤモンド依存関係が一度だけ解決されるようにする
    for included_name in toolset.get("includes", []):
        included_tools = resolve_toolset(included_name, visited)
        tools.update(included_tools)

    return sorted(tools)


def resolve_multiple_toolsets(toolset_names: List[str]) -> List[str]:
    """複数のツールセットを解決してツールを結合する。

    Args:
        toolset_names: 解決するツールセット名のリスト

    Returns:
        List[str]: 全ツール名の結合リスト（重複除去済み）
    """
    all_tools: Set[str] = set()
    for name in toolset_names:
        tools = resolve_toolset(name)
        all_tools.update(tools)
    return sorted(all_tools)


def get_toolset_names() -> List[str]:
    """利用可能な全ツールセットの名前を取得する（エイリアスは除外）。

    プラグイン登録済みのツールセット名も含みます。

    Returns:
        List[str]: ツールセット名のリスト
    """
    names = set(TOOLSETS.keys())
    aliases = _get_registry_toolset_aliases()
    for ts_name in _get_plugin_toolset_names():
        for alias, canonical in aliases.items():
            if canonical == ts_name and alias not in TOOLSETS:
                names.add(alias)
                break
        else:
            names.add(ts_name)
    return sorted(names)


def get_all_toolsets() -> Dict[str, Dict[str, Any]]:
    """定義付きで利用可能な全ツールセットを取得する。

    静的に定義されたツールセットとプラグイン登録済みのものを含みます。

    Returns:
        Dict: 全ツールセットの定義
    """
    result = dict(TOOLSETS)
    aliases = _get_registry_toolset_aliases()
    for ts_name in _get_plugin_toolset_names():
        display_name = ts_name
        for alias, canonical in aliases.items():
            if canonical == ts_name and alias not in TOOLSETS:
                display_name = alias
                break
        if display_name in result:
            continue
        toolset = get_toolset(display_name)
        if toolset:
            result[display_name] = toolset
    return result


def validate_toolset(name: str) -> bool:
    """ツールセット名が有効かどうかを確認する。

    Args:
        name: 検証するツールセット名

    Returns:
        bool: 有効な場合はTrue、それ以外はFalse
    """
    if name in {"all", "*"}:
        return True
    if name in TOOLSETS:
        return True
    if name in _get_plugin_toolset_names():
        return True
    return name in _get_registry_toolset_aliases()


def create_custom_toolset(
    name: str,
    description: str,
    tools: List[str] = None,
    includes: List[str] = None,
) -> None:
    """実行時にカスタムツールセットを作成する。

    Args:
        name: 新しいツールセットの名前
        description: ツールセットの説明
        tools: 含める直接ツール
        includes: 含める他のツールセット
    """
    TOOLSETS[name] = {
        "description": description,
        "tools": tools or [],
        "includes": includes or [],
    }


def get_toolset_info(name: str) -> Optional[Dict[str, Any]]:
    """解決済みツールを含むツールセットの詳細情報を取得する。

    Args:
        name: ツールセット名

    Returns:
        Dict: 詳細なツールセット情報
    """
    toolset = get_toolset(name)
    if not toolset:
        return None

    resolved_tools = resolve_toolset(name)

    return {
        "name": name,
        "description": toolset["description"],
        "direct_tools": toolset["tools"],
        "includes": toolset["includes"],
        "resolved_tools": resolved_tools,
        "tool_count": len(resolved_tools),
        "is_composite": bool(toolset["includes"]),
    }


# ─── 内部ヘルパー ───


def _get_plugin_toolset_names() -> Set[str]:
    """プラグインが登録したツールセット名を返す（ツールレジストリから）。"""
    try:
        from tools.registry import registry
        return {
            ts_name
            for ts_name in registry.get_registered_toolset_names()
            if ts_name not in TOOLSETS
        }
    except Exception:
        return set()


def _get_registry_toolset_aliases() -> Dict[str, str]:
    """ライブレジストリに登録されている明示的なツールセットエイリアスを返す。"""
    try:
        from tools.registry import registry
        return registry.get_registered_toolset_aliases()
    except Exception:
        return {}

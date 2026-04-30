"""ファイルツールモジュール - LLMエージェントのファイル操作ツール。"""
import json
import logging
import os
import re
from fnmatch import fnmatch
from pathlib import Path
from typing import Optional

from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)

# 読み取りサイズの上限（文字数）。100K文字 ≒ 25–35Kトークン。
# これを超える読み取りは拒否し、offset/limit で該当セクションのみ読むよう促す。
_MAX_READ_CHARS = 100_000

# デバイスパスのブロックリスト — 読み込むとプロセスがハングする（無限出力または入力待ちブロック）
_BLOCKED_DEVICE_PATHS = frozenset({
    # 無限出力 — EOFに到達しない
    "/dev/zero", "/dev/random", "/dev/urandom", "/dev/full",
    # 入力待ちでブロックする
    "/dev/stdin", "/dev/tty", "/dev/console",
    # 読み取りが無意味
    "/dev/stdout", "/dev/stderr",
    # fdエイリアス
    "/dev/fd/0", "/dev/fd/1", "/dev/fd/2",
})


def _resolve_path(file_path: str) -> Optional[Path]:
    """ファイルパスを解決する。失敗した場合はNoneを返す。"""
    try:
        path = Path(file_path).expanduser().resolve()
    except (OSError, ValueError):
        return None
    return path


def _validate_path(path: Path) -> Optional[str]:
    """パスが安全に読み取り可能かを検証する。エラーメッセージまたはNoneを返す。"""
    str_path = str(path)
    # デバイスパスのブロックチェック（シンボリックリンク解決前のリテラルパス）
    if str_path in _BLOCKED_DEVICE_PATHS:
        return f"ブロックされたデバイスパス: {str_path}"
    # /proc/self/fd/0-2 および /proc/<pid>/fd/0-2 はstdioのエイリアス
    if str_path.startswith("/proc/") and str_path.endswith(("/fd/0", "/fd/1", "/fd/2")):
        return f"ブロックされたデバイスパス: {str_path}"
    return None


def _search_files(
    pattern: str, search_path: str = ".",
    file_glob: Optional[str] = None, limit: int = 50,
    offset: int = 0, output_mode: str = "content",
    context: int = 0,
) -> dict:
    """正規表現パターンを使用してファイルを検索する。純Pythonフォールバック実装。

    戻り値:
        {"matches": [...], "total_count": int, "truncated": bool}
    """
    results = []
    sp = Path(search_path).expanduser().resolve()
    if not sp.is_dir():
        return {"matches": [], "total_count": 0, "truncated": False}

    pattern_compiled = re.compile(pattern, re.IGNORECASE) if pattern else None

    for root, dirs, files in os.walk(sp):
        # 隠しディレクトリと node_modules をスキップ
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules"]
        for filename in files:
            if file_glob:
                if not fnmatch(filename, file_glob):
                    continue
            filepath = Path(root) / filename
            try:
                if pattern_compiled:
                    if output_mode == "files_only":
                        # ファイル名マッチ — 内容を読まずにパスのみ記録
                        results.append({"path": str(filepath)})
                    else:
                        # 内容検索 — 1行ずつ読み取り
                        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                            lines = f.readlines()
                        file_matches = []
                        for lineno, line in enumerate(lines, 1):
                            if pattern_compiled.search(line):
                                file_matches.append({
                                    "line": lineno,
                                    "content": line.rstrip("\n\r"),
                                })
                        if file_matches:
                            if context > 0 and output_mode == "content":
                                # コンテキスト行を追加
                                enriched = []
                                for m in file_matches:
                                    ctx_start = max(0, m["line"] - 1 - context)
                                    ctx_end = min(len(lines), m["line"] - 1 + context + 1)
                                    ctx_lines = []
                                    for ci in range(ctx_start, ctx_end):
                                        prefix = ">" if ci == m["line"] - 1 else " "
                                        ctx_lines.append(f"{prefix}{ci + 1}|{lines[ci].rstrip(chr(10) + chr(13))}")
                                    enriched.append({
                                        "path": str(filepath),
                                        "line": m["line"],
                                        "content": m["content"],
                                        "context": ctx_lines,
                                    })
                                results.extend(enriched)
                            else:
                                m_with_path = [{"path": str(filepath), **m} for m in file_matches]
                                results.extend(m_with_path)
                else:
                    # パターンなし — 全ファイルを列挙
                    results.append({"path": str(filepath)})
            except (OSError, UnicodeDecodeError):
                continue

    total = len(results)
    if output_mode == "count":
        # ファイルごとのマッチ数を集計
        from collections import Counter
        file_counts = Counter(m["path"] for m in results if "path" in m)
        count_results = [{"path": p, "count": c} for p, c in file_counts.items()]
        paginated = count_results[offset:offset + limit] if offset else count_results[:limit]
        truncated = len(count_results) > offset + limit
        return {"matches": paginated, "total_count": len(count_results), "truncated": truncated}

    paginated = results[offset:offset + limit] if offset else results[:limit]
    truncated = len(results) > offset + limit
    return {"matches": paginated, "total_count": total, "truncated": truncated}


def read_file_handler(args: dict, **kwargs) -> str:
    """ファイルを行番号付きで読み取る。出力形式: 'LINE_NUM|CONTENT'。

    引数:
        path: ファイルパス（必須）
        offset: 読み取り開始行（1始まり、デフォルト: 1）
        limit: 最大読み取り行数（デフォルト: 500、最大: 2000）
    """
    path_str = args.get("path", "")
    offset = args.get("offset", 1)
    limit = args.get("limit", 500)

    # 最大行数を制限
    limit = min(limit, 2000)

    path = _resolve_path(path_str)
    if not path:
        return tool_error(f"パスを解決できません: {path_str}")
    err = _validate_path(path)
    if err:
        return tool_error(err)
    if not path.exists():
        return tool_error(f"ファイルが見つかりません: {path}")
    if not path.is_file():
        return tool_error(f"ファイルではありません: {path}")

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except (OSError, UnicodeDecodeError) as e:
        return tool_error(f"読み取りエラー: {e}")

    total = len(lines)
    start = max(0, (offset or 1) - 1)
    end = min(total, start + (limit or 500))

    content = "".join(lines[start:end])
    if len(content) > _MAX_READ_CHARS:
        content = content[:_MAX_READ_CHARS] + "\n... [切り詰められました]"

    # 行番号付きで整形（"LINE_NUM|CONTENT" 形式）
    line_display = "\n".join(
        f"{i + start + 1}|{lines[start + i].rstrip(chr(10) + chr(13))}"
        for i in range(end - start)
    )

    result = {
        "content": line_display,
        "total_lines": total,
        "file_size": path.stat().st_size,
        "truncated": len(content) >= _MAX_READ_CHARS,
    }

    # 大容量ファイルヒント
    file_size = path.stat().st_size
    if file_size > 512_000 and limit > 200 and result.get("truncated"):
        result["_hint"] = (
            f"このファイルは大容量です（{file_size:,} バイト）。"
            "offset と limit を使用して必要なセクションのみを読み込むことで、"
            "コンテキスト使用量を効率的に保てます。"
        )

    return tool_result(result)


def write_file_handler(args: dict, **kwargs) -> str:
    """ファイルにコンテンツを書き込む（完全に上書き）。親ディレクトリは自動生成。"""
    path_str = args.get("path", "")
    content = args.get("content", "")

    path = _resolve_path(path_str)
    if not path:
        return tool_error(f"パスを解決できません: {path_str}")
    err = _validate_path(path)
    if err:
        return tool_error(err)

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    except OSError as e:
        return tool_error(f"書き込みエラー: {e}")

    return tool_result({
        "success": True,
        "bytes_written": len(content.encode("utf-8")),
        "dirs_created": True,
    })


def _parse_v4a_patch(patch_content: str) -> list:
    """V4A形式のパッチを解析し、(action, path, hunks) のリストを返す。

    各hunkは (context_before, removed_lines, added_lines) のタプル。
    """
    operations = []
    current_action = None
    current_path = None
    current_hunks = []
    current_context = []
    current_removed = []
    current_added = []
    in_hunk = False

    for line in patch_content.splitlines():
        # ファイルヘッダの検出
        update_match = re.match(r'^\*\*\*\s+(Update|Add|Delete)\s+File:\s*(.+)$', line)
        if update_match:
            # 前の操作を保存
            if current_path and current_action:
                if current_removed or current_added:
                    current_hunks.append((current_context, current_removed, current_added))
                operations.append((current_action, current_path, current_hunks))
            current_action = update_match.group(1).lower()  # update, add, delete
            current_path = update_match.group(2).strip()
            current_hunks = []
            current_context = []
            current_removed = []
            current_added = []
            in_hunk = False
            continue

        # ハンクヘッダの検出
        if re.match(r'^@@\s+.*@@', line):
            if in_hunk and (current_removed or current_added):
                current_hunks.append((current_context, current_removed, current_added))
            current_context = []
            current_removed = []
            current_added = []
            in_hunk = True
            continue

        if in_hunk:
            if line.startswith("-"):
                current_removed.append(line[1:])
            elif line.startswith("+"):
                current_added.append(line[1:])
            else:
                # context line
                ctx = line[1:] if line.startswith(" ") else line
                if current_removed or current_added:
                    current_hunks.append((current_context, current_removed, current_added))
                    current_context = []
                    current_removed = []
                    current_added = []
                current_context.append(ctx)
        else:
            current_context.append(line)

    # 最後の操作を保存
    if current_path and current_action:
        if current_removed or current_added:
            current_hunks.append((current_context, current_removed, current_added))
        operations.append((current_action, current_path, current_hunks))

    return operations


def _apply_v4a_patch(action: str, path: Path, hunks: list) -> list:
    """単一ファイルにV4Aパッチを適用する。(成功したファイル, エラー) のペアを返す。"""
    if action == "delete":
        if path.exists():
            path.unlink()
            return [(str(path), f"ファイルを削除しました: {path}"), None]
        return [None, f"ファイルが見つかりません: {path}"]

    if action == "add":
        path.parent.mkdir(parents=True, exist_ok=True)
        content = ""
        for _, removed, added in hunks:
            if removed and not added:
                continue
            for a in added:
                content += a + "\n"
        path.write_text(content, encoding="utf-8")
        return [(str(path), f"ファイルを作成しました: {path}"), None]

    # update
    if not path.exists():
        return [None, f"更新対象ファイルが見つかりません: {path}"]

    content = path.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)

    for ctx_before, removed, added in hunks:
        # コンテキスト行を使ってマッチ位置を特定
        target_text = "".join(r + "\n" for r in removed) if removed else ""
        if ctx_before:
            target_text = "".join(c + "\n" for c in ctx_before) + target_text

        replacement = "".join(a + "\n" for a in added) if added else ""
        if ctx_before and not removed:
            replacement = "".join(c + "\n" for c in ctx_before) + replacement

        # 単純置換（末尾改行を考慮）
        full_content = content
        if target_text and target_text in full_content:
            full_content = full_content.replace(target_text, replacement, 1)
        elif removed:
            # removed linesのみでマッチを試みる
            remove_text = "".join(r + "\n" for r in removed)
            if remove_text in full_content:
                full_content = full_content.replace(remove_text, replacement, 1)
        content = full_content

    path.write_text(content, encoding="utf-8")
    return [(str(path), f"ファイルを更新しました: {path}"), None]


def patch_handler(args: dict, **kwargs) -> str:
    """ファイル内のテキストをファジーマッチングで検索・置換する。

    replaceモード（デフォルト）: ユニークな文字列を検索して置換。
    patchモード: V4Aマルチファイルパッチを適用。

    引数:
        mode: "replace"（デフォルト）または "patch"
        path: 編集対象ファイルパス（replaceモードで必須）
        old_string: 検索テキスト（replaceモードで必須）
        new_string: 置換テキスト（replaceモードで必須）
        replace_all: 全出現箇所を置換（デフォルト: false）
        patch: V4A形式パッチ内容（patchモードで必須）
    """
    mode = args.get("mode", "replace")
    path_str = args.get("path", "")
    old_string = args.get("old_string", "")
    new_string = args.get("new_string", "")
    replace_all = args.get("replace_all", False)
    patch_content = args.get("patch", "")

    if mode == "patch":
        if not patch_content:
            return tool_error("patchモードでは patch 内容が必須です")
        operations = _parse_v4a_patch(patch_content)
        if not operations:
            return tool_error("有効なV4Aパッチ操作が見つかりません")

        results = []
        errors = []
        for action, p, hunks in operations:
            resolved = _resolve_path(p)
            if resolved is None:
                errors.append(f"パスを解決できません: {p}")
                continue
            result, err = _apply_v4a_patch(action, resolved, hunks)
            if result:
                results.append(result)
            if err:
                errors.append(err)

        response = {
            "success": len(errors) == 0,
            "results": results,
            "count": len(results),
        }
        if errors:
            response["errors"] = errors
        return tool_result(response)

    # replaceモード
    if not path_str:
        return tool_error("path は必須です")
    if not old_string:
        return tool_error("old_string は必須です")

    path = _resolve_path(path_str)
    if not path:
        return tool_error(f"パスを解決できません: {path_str}")
    if not path.exists():
        return tool_error(f"ファイルが見つかりません: {path}")

    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return tool_error(f"読み取りエラー: {e}")

    if replace_all:
        new_content = content.replace(old_string, new_string)
        count = content.count(old_string)
    else:
        if old_string not in content:
            # 改行の正規化を試みる
            normalized_content = content.replace("\r\n", "\n")
            normalized_old = old_string.replace("\r\n", "\n")
            if normalized_old in normalized_content:
                new_content = normalized_content.replace(normalized_old, new_string, 1)
                count = 1
            else:
                return tool_error(f"old_string が見つかりません:\n```\n{old_string[:200]}\n```")
        else:
            new_content = content.replace(old_string, new_string, 1)
            count = 1

    try:
        original_mode = path.stat().st_mode
        path.write_text(new_content, encoding="utf-8")
        os.chmod(path, original_mode)  # Windows ではこの操作は無視される（OSError は catch される）
    except OSError as e:
        return tool_error(f"書き込みエラー: {e}")

    return tool_result({
        "success": True,
        "count": count,
    })


def search_files_handler(args: dict, **kwargs) -> str:
    """ファイル名（glob）またはファイル内容（正規表現）で検索する。

    引数:
        pattern: 検索パターン（必須）
        target: "content"（ファイル内容検索）または "files"（ファイル名検索）
        path: 検索パス（デフォルト: "."）
        file_glob: ファイルフィルター（例: "*.py"）
        limit: 最大結果数（デフォルト: 50）
        offset: 結果のページネーションオフセット（デフォルト: 0）
        output_mode: "content"（行番号付き）、"files_only"（パスのみ）、"count"（ファイルごとの集計）
        context: 各マッチの前後のコンテキスト行数（デフォルト: 0）
    """
    pattern = args.get("pattern", "")
    target = args.get("target", "content")
    search_path = args.get("path", ".")
    file_glob = args.get("file_glob")
    limit = args.get("limit", 50)
    offset = args.get("offset", 0)
    output_mode = args.get("output_mode", "content")
    context = args.get("context", 0)

    if target == "files":
        # ファイル名検索（glob）
        sp = Path(search_path).expanduser().resolve()
        results = []
        for root, dirs, files in os.walk(sp):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules"]
            for filename in files:
                if fnmatch(filename, pattern):
                    results.append({"path": str(Path(root) / filename)})
                    if len(results) >= offset + limit:
                        break
            if len(results) >= offset + limit:
                break
        total = len(results)
        paginated = results[offset:offset + limit] if offset else results[:limit]
        return tool_result({
            "matches": paginated,
            "total_count": total,
            "truncated": len(results) > offset + limit,
        })
    else:
        # ファイル内容検索（正規表現）
        result_data = _search_files(
            pattern, search_path, file_glob,
            limit=limit, offset=offset,
            output_mode=output_mode, context=context,
        )
        return tool_result(result_data)


# ─── ツール登録 ───

registry.register(
    name="read_file",
    toolset="file",
    schema={
        "description": "ファイルを行番号付きで読み取ります。offset/limit によるページネーションをサポートします。",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "読み取るファイルのパス（絶対パス、相対パス、~/path）"},
                "offset": {
                    "type": "integer",
                    "description": "読み取り開始行（1始まり、デフォルト: 1）",
                    "default": 1,
                    "minimum": 1,
                },
                "limit": {
                    "type": "integer",
                    "description": "最大読み取り行数（デフォルト: 500、最大: 2000）",
                    "default": 500,
                    "maximum": 2000,
                },
            },
            "required": ["path"],
        },
    },
    handler=read_file_handler,
    description="ファイル読み取りツール",
    emoji="📄",
)

registry.register(
    name="write_file",
    toolset="file",
    schema={
        "description": "ファイルにコンテンツを書き込みます（完全に上書き）。親ディレクトリは自動生成されます。",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "書き込むファイルのパス"},
                "content": {"type": "string", "description": "書き込むコンテンツ"},
            },
            "required": ["path", "content"],
        },
    },
    handler=write_file_handler,
    description="ファイル書き込みツール",
    emoji="📝",
)

registry.register(
    name="patch",
    toolset="file",
    schema={
        "description": "ファイル内のテキストをファジーマッチングで検索・置換します。マイナーな空白・インデントの差異を吸収します。\n\nreplaceモード（デフォルト）: ユニークな文字列を検索して置換します。\npatchモード: V4Aマルチファイルパッチを一括適用します。",
        "parameters": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["replace", "patch"],
                    "description": "編集モード: 'replace' は検索置換、'patch' はV4Aマルチファイルパッチ",
                    "default": "replace",
                },
                "path": {
                    "type": "string",
                    "description": "編集対象ファイルパス（replaceモードでは必須）",
                },
                "old_string": {
                    "type": "string",
                    "description": "検索するテキスト（replaceモードでは必須）。replace_all=true でない限りファイル内でユニークである必要があります。一意性を確保するために十分な周辺コンテキストを含めてください。",
                },
                "new_string": {
                    "type": "string",
                    "description": "置換テキスト（replaceモードでは必須）。空文字列で該当テキストを削除できます。",
                },
                "replace_all": {
                    "type": "boolean",
                    "description": "全出現箇所を置換するかどうか（デフォルト: false）",
                    "default": False,
                },
                "patch": {
                    "type": "string",
                    "description": "V4A形式パッチ内容（patchモードでは必須）。形式:\n*** Begin Patch\n*** Update File: path/to/file\n@@ context hint @@\n context line\n-removed line\n+added line\n*** End Patch",
                },
            },
            "required": ["mode"],
        },
    },
    handler=patch_handler,
    description="ファイルテキスト置換ツール",
    emoji="🔧",
)

registry.register(
    name="search_files",
    toolset="file",
    schema={
        "description": "ファイル名（glob）またはファイル内容（正規表現）で検索します。\n\n内容検索（target='content'）: ファイル内を正規表現検索。output_mode で結果形式を選択: 'content'（行番号付き）、'files_only'（パスのみ）、'count'（ファイルごとのマッチ数）。\n\nファイル名検索（target='files'）: globパターンでファイルを検索（例: '*.py', '*config*'）。",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "内容検索の場合は正規表現パターン、ファイル名検索の場合はglobパターン",
                },
                "target": {
                    "type": "string",
                    "enum": ["content", "files"],
                    "description": "'content': ファイル内容を検索、'files': ファイル名で検索",
                    "default": "content",
                },
                "path": {
                    "type": "string",
                    "description": "検索対象のディレクトリまたはファイル（デフォルト: カレントディレクトリ）",
                    "default": ".",
                },
                "file_glob": {
                    "type": "string",
                    "description": "ファイルフィルター（例: '*.py'）。内容検索時に特定の拡張子のみを対象とする場合に指定",
                },
                "limit": {
                    "type": "integer",
                    "description": "最大結果数（デフォルト: 50）",
                    "default": 50,
                },
                "offset": {
                    "type": "integer",
                    "description": "結果のページネーションオフセット（デフォルト: 0）",
                    "default": 0,
                },
                "output_mode": {
                    "type": "string",
                    "enum": ["content", "files_only", "count"],
                    "description": "出力形式: 'content' は行番号付きマッチ行、'files_only' はファイルパスのみ、'count' はファイルごとのマッチ数",
                    "default": "content",
                },
                "context": {
                    "type": "integer",
                    "description": "各マッチの前後のコンテキスト行数（grepモードのみ、デフォルト: 0）",
                    "default": 0,
                },
            },
            "required": ["pattern"],
        },
    },
    handler=search_files_handler,
    description="ファイル検索ツール",
    emoji="🔍",
)

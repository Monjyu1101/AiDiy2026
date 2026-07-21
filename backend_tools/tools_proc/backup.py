# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""
バックアップ処理モジュール

`aidiy_backup` MCP が使う差分バックアップ実行とバックアップ照合を提供する。
バックアップ作成は backend_server のネイティブ実装を動的ロードして流用し、
バックアップ参照は MCP 側でバックアップフォルダを横断照合する。
"""

import difflib
import importlib.util
import os
import re
from datetime import datetime
from typing import Optional


class BackupSaveError(Exception):
    """バックアップ実行エラー"""
    pass


class BackupCheckError(Exception):
    """バックアップ照合エラー"""
    pass


_AIDIY_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load_native_module():
    """AiDiy 自身の backend_server/AIコア/AIバックアップ.py を動的にロードする。

    バックアップ対象（project_root）は小説執筆フォルダ等プログラムと無関係な場合もあるため、
    ネイティブ実装は常に AiDiy 自身のものを使う（対象フォルダ側に同名モジュールは不要）。
    """
    native_path = os.path.join(
        _AIDIY_ROOT, "backend_server", "AIコア", "AIバックアップ.py"
    )
    if not os.path.isfile(native_path):
        raise BackupSaveError(
            f"ネイティブバックアップモジュールが見つかりません: {native_path}"
        )
    spec = importlib.util.spec_from_file_location(
        "aidiy_ai_backup_native", native_path
    )
    if spec is None or spec.loader is None:
        raise BackupSaveError(f"ネイティブモジュール読み込み失敗: {native_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BackupSave:
    """AiDiy ネイティブのバックアップ機能を MCP から実行するラッパー"""

    def __init__(self, project_root: Optional[str] = None):
        if project_root:
            self.root = os.path.abspath(project_root)
        else:
            here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.root = os.path.dirname(here)
        self.backend_dir = os.path.join(self.root, "backend_server")
        self._native = None

    def _get_native(self):
        if self._native is None:
            self._native = _load_native_module()
        return self._native

    def run(self) -> dict:
        """ネイティブ `バックアップ実行` を呼び出して差分バックアップを作成する。"""
        native = self._get_native()
        try:
            result = native.バックアップ実行(
                アプリ設定=None,
                backend_dir=self.backend_dir,
                セッション設定=None,
                ログ出力=False,
            )
        except Exception as e:
            raise BackupSaveError(f"バックアップ実行中に例外: {e}") from e

        if result is None:
            return {
                "ok": False,
                "最終時刻": "",
                "全件数": 0,
                "バックアップ件数": 0,
                "全件フラグ": False,
                "バックアップ先": "",
                "差分なし": False,
            }

        最終時刻, all_files, changed_files, 全件フラグ, target_dir = result
        changed = changed_files or []
        return {
            "ok": True,
            "最終時刻": 最終時刻,
            "全件数": len(all_files or []),
            "バックアップ件数": len(changed),
            "全件フラグ": bool(全件フラグ),
            "バックアップ先": (target_dir or "").replace("\\", "/"),
            "差分なし": (len(changed) == 0) and (not 全件フラグ),
        }

    def diff_scan(self) -> dict:
        """バックアップは実行せず、現時点の差分対象ファイル一覧のみ返す。"""
        native = self._get_native()
        try:
            result = native.差分ファイル取得(
                アプリ設定=None,
                backend_dir=self.backend_dir,
            )
        except Exception as e:
            raise BackupSaveError(f"差分スキャン中に例外: {e}") from e

        if result is None:
            return {
                "最終バックアップ日時": "",
                "差分ファイル": [],
                "count": 0,
            }
        最終日時, files = result
        files = files or []
        return {
            "最終バックアップ日時": 最終日時,
            "差分ファイル": files,
            "count": len(files),
        }


class BackupCheck:
    """AiDiy バックアップフォルダの横断照合を提供"""

    BACKUP_DIR_NAME = "backup"
    MAX_CONTENT_BYTES = 512 * 1024

    _DATE_RE = re.compile(r"^\d{8}$")
    _TIME_RE = re.compile(r"^(\d{6})")

    def __init__(self, project_root: Optional[str] = None):
        if project_root:
            self.root = os.path.abspath(project_root)
        else:
            here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.root = os.path.dirname(here)
        self.backup_root = os.path.join(self.root, self.BACKUP_DIR_NAME)

    def _normalize_rel(self, path: str) -> str:
        """入力パスをプロジェクトルート相対・POSIX 区切りに正規化"""
        p = (path or "").strip().replace("\\", "/")
        if not p:
            raise BackupCheckError("path が空です")
        if os.path.isabs(p):
            try:
                p = os.path.relpath(p, self.root).replace("\\", "/")
            except ValueError as e:
                raise BackupCheckError(f"プロジェクト外のパスです: {path}") from e
        if ".." in p.split("/"):
            raise BackupCheckError(f"不正なパス（上位参照）: {path}")
        return p

    def _timestamp(self, date_dir: str, time_dir: str) -> Optional[str]:
        """YYYYMMDD と HHMMSS[.xxx] から 'YYYYMMDD_HHMMSS' を作る"""
        if not self._DATE_RE.match(date_dir):
            return None
        m = self._TIME_RE.match(time_dir)
        if not m:
            return None
        return f"{date_dir}_{m.group(1)}"

    def _iter_backup_folders_desc(self) -> list[tuple[str, str, str, str]]:
        """バックアップ下のフォルダを降順で返す"""
        if not os.path.isdir(self.backup_root):
            return []
        entries: list[tuple[str, str, str, str]] = []
        for date_dir in os.listdir(self.backup_root):
            date_path = os.path.join(self.backup_root, date_dir)
            if not os.path.isdir(date_path) or not self._DATE_RE.match(date_dir):
                continue
            for time_dir in os.listdir(date_path):
                time_path = os.path.join(date_path, time_dir)
                if not os.path.isdir(time_path):
                    continue
                ts = self._timestamp(date_dir, time_dir)
                if ts is None:
                    continue
                entries.append((ts, date_dir, time_dir, time_path))
        entries.sort(key=lambda x: x[0], reverse=True)
        return entries

    def _read_file(self, abs_path: str) -> tuple[str, int, bool]:
        """ファイルを UTF-8 で読む。上限超過時は truncated を立てる。"""
        size = os.path.getsize(abs_path)
        with open(abs_path, "rb") as f:
            raw = f.read(self.MAX_CONTENT_BYTES + 1)
        truncated = len(raw) > self.MAX_CONTENT_BYTES
        if truncated:
            raw = raw[: self.MAX_CONTENT_BYTES]
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("utf-8", errors="replace")
        return text, size, truncated

    def backup_root_path(self) -> dict:
        """バックアップルートの絶対パスと存在フラグを返す"""
        return {
            "project_root": self.root.replace("\\", "/"),
            "backup_root": self.backup_root.replace("\\", "/"),
            "exists": os.path.isdir(self.backup_root),
        }

    def get_before_after(
        self,
        path: str,
        base_ts: Optional[str] = None,
    ) -> dict:
        """
        現行（after）と、直前のバックアップ版（before）を同時に返す。
        base_ts 指定時はその日時以前のバックアップから before を探す。
        """
        rel = self._normalize_rel(path)
        abs_live = os.path.join(self.root, rel.replace("/", os.sep))

        after: Optional[dict] = None
        if os.path.isfile(abs_live):
            content, size, truncated = self._read_file(abs_live)
            mtime = datetime.fromtimestamp(os.path.getmtime(abs_live))
            after = {
                "content": content,
                "size_bytes": size,
                "truncated": truncated,
                "mtime": mtime.strftime("%Y-%m-%d %H:%M:%S"),
                "source": "live",
                "path": rel,
            }

        before: Optional[dict] = None
        for ts, date_dir, time_dir, folder in self._iter_backup_folders_desc():
            if base_ts and ts >= base_ts:
                continue
            candidate = os.path.join(folder, rel.replace("/", os.sep))
            if os.path.isfile(candidate):
                content, size, truncated = self._read_file(candidate)
                before = {
                    "content": content,
                    "size_bytes": size,
                    "truncated": truncated,
                    "timestamp": ts,
                    "backup_folder": f"{date_dir}/{time_dir}",
                    "source": "backup",
                    "path": rel,
                }
                break

        return {"path": rel, "before": before, "after": after}

    def list_versions(self, path: str) -> dict:
        """指定ファイルがバックアップに出現する全日時を新しい順で返す"""
        rel = self._normalize_rel(path)
        versions: list[dict] = []
        for ts, date_dir, time_dir, folder in self._iter_backup_folders_desc():
            candidate = os.path.join(folder, rel.replace("/", os.sep))
            if os.path.isfile(candidate):
                try:
                    size = os.path.getsize(candidate)
                except OSError:
                    size = 0
                versions.append({
                    "timestamp": ts,
                    "backup_folder": f"{date_dir}/{time_dir}",
                    "size_bytes": size,
                })
        return {"path": rel, "versions": versions, "count": len(versions)}

    def find_changed(
        self,
        from_ts: str,
        to_ts: Optional[str] = None,
    ) -> dict:
        """指定期間のバックアップに含まれる相対パス一覧を返す。"""
        if not from_ts:
            raise BackupCheckError("from_ts は必須です（例: '20260418_000000'）")
        changed: dict[str, list[str]] = {}
        for ts, _, _, folder in self._iter_backup_folders_desc():
            if ts < from_ts:
                continue
            if to_ts and ts > to_ts:
                continue
            for root, _, files in os.walk(folder):
                for fn in files:
                    abs_p = os.path.join(root, fn)
                    rel = os.path.relpath(abs_p, folder).replace("\\", "/")
                    changed.setdefault(rel, []).append(ts)
        items = [
            {"path": p, "timestamps": sorted(set(ts_list), reverse=True)}
            for p, ts_list in changed.items()
        ]
        items.sort(key=lambda x: x["path"])
        return {
            "from_ts": from_ts,
            "to_ts": to_ts,
            "items": items,
            "count": len(items),
        }

    def diff_stats(self, path: str, base_ts: Optional[str] = None) -> dict:
        """指定ファイルの before/after の追加・削除行数を返す軽量サマリ。"""
        pair = self.get_before_after(path, base_ts=base_ts)
        before = pair.get("before")
        after = pair.get("after")
        before_lines = before["content"].splitlines() if before else []
        after_lines = after["content"].splitlines() if after else []
        added = 0
        removed = 0
        for op in difflib.ndiff(before_lines, after_lines):
            if op.startswith("+ "):
                added += 1
            elif op.startswith("- "):
                removed += 1
        return {
            "path": pair["path"],
            "before_timestamp": before["timestamp"] if before else None,
            "after_source": after["source"] if after else None,
            "added_lines": added,
            "removed_lines": removed,
            "before_lines_total": len(before_lines),
            "after_lines_total": len(after_lines),
        }

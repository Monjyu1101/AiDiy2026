# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""
バックアップ照合モジュール

AiDiy のバックアップフォルダ（差分バックアップ）から、
指定ソースの「変更前」版を抽出し、現行ソース（変更後）と併せて返す。
CLI/AIエージェントの差分検証を支援する。

バックアップ構造:
    <project_root>/backup/YYYYMMDD/HHMMSS[.all|.コメント]/<相対パス>
    - HHMMSS.all : 初回全件スナップショット
    - HHMMSS     : 差分（最終バックアップ+1秒以降の変更ファイル）

差分バックアップのため、「変更前」抽出は日時フォルダを降順で走査し、
最初にヒットしたファイル（= 最も新しい過去バージョン）を採用する。
"""

import difflib
import os
import re
from datetime import datetime
from typing import Optional


class BackupCheckError(Exception):
    """バックアップ照合エラー"""
    pass


class BackupCheck:
    """AiDiy バックアップフォルダの横断照合を提供"""

    BACKUP_DIR_NAME = "backup"
    MAX_CONTENT_BYTES = 512 * 1024  # 1 ファイルあたり最大 512KB 返却

    _DATE_RE = re.compile(r"^\d{8}$")
    _TIME_RE = re.compile(r"^(\d{6})")

    def __init__(self, project_root: Optional[str] = None):
        if project_root:
            self.root = os.path.abspath(project_root)
        else:
            here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.root = os.path.dirname(here)
        self.backup_root = os.path.join(self.root, self.BACKUP_DIR_NAME)

    # ------------------------------------------------------------------ #
    # 内部ヘルパ
    # ------------------------------------------------------------------ #

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
        """YYYYMMDD と HHMMSS[.xxx] から 'YYYYMMDD_HHMMSS' を作る（並べ替え可能な文字列）"""
        if not self._DATE_RE.match(date_dir):
            return None
        m = self._TIME_RE.match(time_dir)
        if not m:
            return None
        return f"{date_dir}_{m.group(1)}"

    def _iter_backup_folders_desc(self) -> list[tuple[str, str, str, str]]:
        """
        バックアップ下のフォルダ (timestamp, date_dir, time_dir, abs_folder) を降順で返す
        """
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
        """
        ファイルを UTF-8 で読む。上限超過時は末尾を切り捨て truncated を立てる。
        戻り値: (content, size_bytes, truncated)
        """
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

    # ------------------------------------------------------------------ #
    # 公開メソッド
    # ------------------------------------------------------------------ #

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
        base_ts ('YYYYMMDD_HHMMSS') を与えた場合、その日時以前のバックアップから before を探す。
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
        """
        指定期間（from_ts ≦ ts ≦ to_ts）のバックアップに含まれる相対パス一覧を返す。
        差分バックアップゆえ、ここに挙がるパスはその期間に変更されたファイル。
        """
        if not from_ts:
            raise BackupCheckError("from_ts は必須です（例: '20260418_000000'）")
        changed: dict[str, list[str]] = {}
        for ts, date_dir, time_dir, folder in self._iter_backup_folders_desc():
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
        """
        指定ファイルの before/after の追加・削除行数を返す軽量サマリ。
        base_ts 指定時はその日時以前を before とする。
        """
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

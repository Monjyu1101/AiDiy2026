# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

import os
import shutil
from datetime import datetime, timedelta
from typing import Optional, Tuple, List

from log_config import get_logger

logger = get_logger(__name__)

_バックアップ除外フォルダ = (
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    "_data",
    "temp",
    "log",
    "logs",
    "backup",
    "node_modules",
    "dist",
    "build",
    ".output",
    ".nuxt",
    ".next",
    ".vite",
    ".turbo",
    ".cache",
    ".npm",
    ".pnpm-store",
    ".yarn",
)

_バックアップ除外ファイル = (
    ".DS_Store",
    "Thumbs.db",
)

_バックアップ除外拡張子 = (
    ".pyc",
    ".pyo",
    ".pyd",
    ".log",
    ".tmp",
    ".swp",
)


def _コードベース絶対パス取得(アプリ設定=None, backend_dir: Optional[str] = None) -> str:
    raw_path = "../"
    if アプリ設定 and hasattr(アプリ設定, "json"):
        raw_path = アプリ設定.json.get("CODE_BASE_PATH", "../")
    normalized = raw_path.replace("\\", "/").strip()
    base_dir = backend_dir or os.path.dirname(os.path.abspath(__file__))
    if os.path.isabs(normalized):
        return os.path.abspath(normalized)
    return os.path.abspath(os.path.join(base_dir, normalized))


def _最新更新と全ファイル一覧(ベースパス: str) -> Tuple[float, List[str]]:
    max_mtime = 0.0
    files: List[str] = []
    workspace_root = os.path.abspath(ベースパス)
    for root, dirs, file_names in os.walk(workspace_root):
        dirs[:] = [d for d in dirs if not any(marker in d for marker in _バックアップ除外フォルダ) and not d.startswith(".")]
        for file_name in file_names:
            file_path = os.path.join(root, file_name)

            # "nul" または "null" ファイルを強制削除
            if file_name.lower() in ("nul", "null"):
                try:
                    os.remove(file_path)
                    logger.warning(f"不正なファイル名を削除: {file_path}")
                except Exception as e:
                    logger.error(f"ファイル削除失敗: {file_path}, エラー: {e}")
                continue

            if any(marker in file_path for marker in _バックアップ除外フォルダ):
                continue
            if file_name in _バックアップ除外ファイル or file_name.endswith(_バックアップ除外拡張子):
                continue
            try:
                mtime = os.path.getmtime(file_path)
            except OSError:
                continue
            rel_path = os.path.relpath(file_path, workspace_root).replace("\\", "/")
            files.append(rel_path)
            if mtime > max_mtime:
                max_mtime = mtime
    return max_mtime, files


def バックアップ実行(アプリ設定=None, backend_dir: Optional[str] = None) -> Optional[Tuple[str, List[str], List[str], bool]]:
    """
    自動バックアップ実行（全件/差分を自動判定）
    - 最大日付フォルダ無し または *.allフォルダ無し → 全件バックアップ
    - それ以外 → 最終バックアップ時刻+1秒からの差分バックアップ

    戻り値: (最大日時文字列, 全ファイル一覧, バックアップファイル一覧, 全件フラグ) または None
    """
    try:
        base_path = _コードベース絶対パス取得(アプリ設定, backend_dir=backend_dir)
        if not os.path.isdir(base_path):
            return None

        # 全ファイルの最大更新日時とファイル一覧を取得
        max_mtime, all_files = _最新更新と全ファイル一覧(base_path)
        if not max_mtime or not all_files:
            return None

        timestamp = datetime.fromtimestamp(max_mtime)
        date_dir = timestamp.strftime("%Y%m%d")
        time_dir = timestamp.strftime("%H%M%S")
        last_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        backup_root = os.path.join(base_path, "backup")
        date_folder = os.path.join(backup_root, date_dir)

        # 最大日付フォルダの存在確認
        if not os.path.isdir(date_folder):
            # 日付フォルダ無し → 全件バックアップ
            result = _全件バックアップ作成(base_path, all_files, backup_root, date_dir, time_dir, last_time)
            return (last_time, all_files, all_files, True) if result else None

        # *.allフォルダの存在確認
        all_folder_exists = any(
            item.endswith(".all") and os.path.isdir(os.path.join(date_folder, item))
            for item in os.listdir(date_folder)
        )
        if not all_folder_exists:
            # *.allフォルダ無し → 全件バックアップ
            result = _全件バックアップ作成(base_path, all_files, backup_root, date_dir, time_dir, last_time)
            return (last_time, all_files, all_files, True) if result else None

        # 差分バックアップ: 同日内の最終バックアップ時刻を取得
        最終時刻 = _最終バックアップ時刻取得(date_folder)
        if not 最終時刻:
            # 時刻取得失敗 → 全件バックアップ
            result = _全件バックアップ作成(base_path, all_files, backup_root, date_dir, time_dir, last_time)
            return (last_time, all_files, all_files, True) if result else None

        # 最終時刻+1秒以降の更新ファイルのみ抽出
        threshold_ts = 最終時刻 + 1.0
        changed_files = []
        workspace_root = os.path.abspath(base_path)
        for rel_path in all_files:
            src_path = os.path.join(base_path, rel_path.replace("/", os.sep))
            if not os.path.exists(src_path):
                continue
            try:
                mtime = os.path.getmtime(src_path)
            except OSError:
                continue
            if mtime >= threshold_ts:
                changed_files.append(rel_path)

        if not changed_files:
            # 差分なし
            return (last_time, all_files, [], False)

        # 差分バックアップ作成
        target_dir = os.path.join(backup_root, date_dir, time_dir)
        if os.path.isdir(target_dir):
            return (last_time, all_files, [], False)

        os.makedirs(target_dir, exist_ok=True)
        copied = 0
        for rel_path in changed_files:
            src_path = os.path.join(base_path, rel_path.replace("/", os.sep))
            if not os.path.exists(src_path):
                continue
            dest_path = os.path.join(target_dir, rel_path.replace("/", os.sep))
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy2(src_path, dest_path)
            copied += 1

        if copied == 0:
            return (last_time, all_files, [], False)

        logger.info(f"AIコア差分バックアップ作成: {date_dir}/{time_dir} ({copied}件)")
        return (last_time, all_files, changed_files, False)

    except Exception as e:
        logger.warning(f"AIコアバックアップ失敗: {e}")
        return None


def _全件バックアップ作成(
    base_path: str,
    all_files: List[str],
    backup_root: str,
    date_dir: str,
    time_dir: str,
    last_time: str
) -> Optional[str]:
    """全件バックアップ作成"""
    target_dir = os.path.join(backup_root, date_dir, f"{time_dir}.all")
    if os.path.isdir(target_dir):
        return last_time

    os.makedirs(target_dir, exist_ok=True)
    copied = 0
    for rel_path in all_files:
        src_path = os.path.join(base_path, rel_path.replace("/", os.sep))
        if not os.path.exists(src_path):
            continue
        dest_path = os.path.join(target_dir, rel_path.replace("/", os.sep))
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy2(src_path, dest_path)
        copied += 1

    if copied == 0:
        return None

    logger.info(f"AIコア全件バックアップ作成: {date_dir}/{time_dir}.all ({copied}件)")
    return last_time


def _最終バックアップ時刻取得(date_folder: str) -> Optional[float]:
    """
    date_folder内の全フォルダ（*.all含む）の最大時刻をタイムスタンプで返す
    """
    max_ts = 0.0
    try:
        for item in os.listdir(date_folder):
            item_path = os.path.join(date_folder, item)
            if not os.path.isdir(item_path):
                continue
            # フォルダ名から時刻を抽出（"HHMMSS" または "HHMMSS.all"）
            time_str = item.replace(".all", "")
            if len(time_str) != 6 or not time_str.isdigit():
                continue
            # HHMMSS をタイムスタンプに変換
            hour = int(time_str[0:2])
            minute = int(time_str[2:4])
            second = int(time_str[4:6])
            # date_folderの日付を取得
            date_str = os.path.basename(date_folder)
            if len(date_str) != 8 or not date_str.isdigit():
                continue
            year = int(date_str[0:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            dt = datetime(year, month, day, hour, minute, second)
            ts = dt.timestamp()
            if ts > max_ts:
                max_ts = ts
        return max_ts if max_ts > 0 else None
    except Exception as e:
        logger.error(f"最終バックアップ時刻取得エラー: {e}")
        return None


def _バックアップ全体の最終日時取得(backup_root: str) -> Optional[Tuple[float, str]]:
    """
    バックアップフォルダ全体から最も新しいバックアップ日時を取得
    戻り値: (タイムスタンプ, "YYYY-MM-DD HH:MM:SS") または None
    """
    max_ts = 0.0
    try:
        if not os.path.isdir(backup_root):
            return None

        for date_dir in os.listdir(backup_root):
            date_folder = os.path.join(backup_root, date_dir)
            if not os.path.isdir(date_folder):
                continue
            if len(date_dir) != 8 or not date_dir.isdigit():
                continue

            # この日付フォルダ内の最終時刻を取得
            folder_max_ts = _最終バックアップ時刻取得(date_folder)
            if folder_max_ts and folder_max_ts > max_ts:
                max_ts = folder_max_ts

        if max_ts == 0.0:
            return None

        timestamp = datetime.fromtimestamp(max_ts)
        last_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return (max_ts, last_time)

    except Exception as e:
        logger.error(f"バックアップ全体の最終日時取得エラー: {e}")
        return None


def 差分ファイル取得(アプリ設定=None, backend_dir: Optional[str] = None) -> Optional[Tuple[str, List[str]]]:
    """
    バックアップフォルダから最終日時を取得し、その+1秒以降に更新されたファイル一覧を返す

    戻り値: (最終バックアップ日時, 差分ファイル一覧) または None
    """
    try:
        base_path = _コードベース絶対パス取得(アプリ設定, backend_dir=backend_dir)
        if not os.path.isdir(base_path):
            return None

        backup_root = os.path.join(base_path, "backup")

        # バックアップフォルダ全体から最終日時を取得
        result = _バックアップ全体の最終日時取得(backup_root)
        if not result:
            return None

        最終タイムスタンプ, 最終日時文字列 = result
        threshold_ts = 最終タイムスタンプ + 1.0

        # 全ファイルをスキャンして差分を抽出
        差分ファイル一覧: List[str] = []
        workspace_root = os.path.abspath(base_path)

        for root, dirs, file_names in os.walk(workspace_root):
            dirs[:] = [d for d in dirs if not any(marker in d for marker in _バックアップ除外フォルダ) and not d.startswith(".")]
            for file_name in file_names:
                file_path = os.path.join(root, file_name)

                # "nul" または "null" ファイルを強制削除
                if file_name.lower() in ("nul", "null"):
                    try:
                        os.remove(file_path)
                        logger.warning(f"不正なファイル名を削除: {file_path}")
                    except Exception as e:
                        logger.error(f"ファイル削除失敗: {file_path}, エラー: {e}")
                    continue

                if any(marker in file_path for marker in _バックアップ除外フォルダ):
                    continue
                if file_name in _バックアップ除外ファイル or file_name.endswith(_バックアップ除外拡張子):
                    continue

                try:
                    mtime = os.path.getmtime(file_path)
                except OSError:
                    continue

                if mtime >= threshold_ts:
                    rel_path = os.path.relpath(file_path, workspace_root).replace("\\", "/")
                    差分ファイル一覧.append(rel_path)

        return (最終日時文字列, 差分ファイル一覧)

    except Exception as e:
        logger.warning(f"差分ファイル取得失敗: {e}")
        return None




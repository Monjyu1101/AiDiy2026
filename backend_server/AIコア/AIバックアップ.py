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
    "package-lock.json",
    "package.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "bun.lockb",
    "npm-shrinkwrap.json",
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


def バックアップ実行(アプリ設定=None, backend_dir: Optional[str] = None) -> Optional[Tuple[str, List[str], List[str], bool, str]]:
    """
    シンプル差分バックアップ実行
    - 初回（*.allフォルダなし）→ 全件バックアップ
    - 2回目以降 → 最終バックアップ時刻+1秒以降の差分のみ
    
    戻り値: (最終更新時刻, 全ファイル一覧, バックアップファイル一覧, 全件フラグ, バックアップフォルダ絶対パス) または None（差分なしまたはエラー）
    """
    try:
        base_path = _コードベース絶対パス取得(アプリ設定, backend_dir=backend_dir)
        if not os.path.isdir(base_path):
            return None

        backup_root = os.path.join(base_path, "backup")
        
        # 最終バックアップ時刻を取得
        最終バックアップ結果 = _バックアップ全体の最終日時取得(backup_root)
        
        # 全ファイル一覧と最大更新時刻を取得
        max_mtime, all_files = _最新更新と全ファイル一覧(base_path)
        if not max_mtime or not all_files:
            return None
        
        # バックアップフォルダ名を作成
        timestamp = datetime.fromtimestamp(max_mtime)
        date_dir = timestamp.strftime("%Y%m%d")
        time_dir = timestamp.strftime("%H%M%S")
        最終時刻 = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        # 初回（全件バックアップ）
        if not 最終バックアップ結果:
            logger.info(f"初回全件バックアップ作成: {len(all_files)}件")
            target_dir = os.path.abspath(os.path.join(backup_root, date_dir, f"{time_dir}.all"))
            if _ファイルコピー実行(base_path, all_files, target_dir):
                return (最終時刻, all_files, all_files, True, target_dir)
            return None
        
        # 差分バックアップ: 最終バックアップ時刻+1秒以降
        最終タイムスタンプ, _ = 最終バックアップ結果
        threshold_ts = 最終タイムスタンプ + 1.0
        
        # 差分ファイル抽出
        changed_files = []
        for rel_path in all_files:
            src_path = os.path.join(base_path, rel_path.replace("/", os.sep))
            if not os.path.exists(src_path):
                continue
            try:
                mtime = os.path.getmtime(src_path)
                if mtime >= threshold_ts:
                    changed_files.append(rel_path)
            except OSError:
                continue
        
        if not changed_files:
            logger.debug(f"差分なし: 最終={datetime.fromtimestamp(最終タイムスタンプ).strftime('%Y-%m-%d %H:%M:%S')}")
            return None
        
        # 差分バックアップ作成
        target_dir = os.path.abspath(os.path.join(backup_root, date_dir, time_dir))
        if os.path.isdir(target_dir):
            logger.info(f"バックアップ既存: {target_dir}")
            return None
        
        logger.info(f"差分バックアップ作成: {len(changed_files)}件")
        if _ファイルコピー実行(base_path, changed_files, target_dir):
            return (最終時刻, all_files, changed_files, False, target_dir)
        return None

    except Exception as e:
        logger.error(f"バックアップ実行エラー: {e}")
        return None


def _ファイルコピー実行(base_path: str, file_list: List[str], target_dir: str) -> bool:
    """ファイルリストをtarget_dirにコピー"""
    try:
        os.makedirs(target_dir, exist_ok=True)
        for rel_path in file_list:
            src_path = os.path.join(base_path, rel_path.replace("/", os.sep))
            if not os.path.exists(src_path):
                continue
            dest_path = os.path.join(target_dir, rel_path.replace("/", os.sep))
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy2(src_path, dest_path)
        return True
    except Exception as e:
        logger.error(f"ファイルコピーエラー: {e}")
        return False





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
            # フォルダ名から時刻を抽出（"HHMMSS", "HHMMSS.all", "HHMMSS.コメント" 等）
            time_str = item.split(".")[0]
            # 数字6桁で始まる時刻フォルダのみ処理
            if len(time_str) != 6 or not time_str.isdigit():
                continue
            # HHMMSS をタイムスタンプに変換
            hour = int(time_str[0:2])
            minute = int(time_str[2:4])
            second = int(time_str[4:6])
            # date_folderの日付を取得（最初の8桁のみ使用）
            date_str = os.path.basename(date_folder)
            if len(date_str) < 8 or not date_str[:8].isdigit():
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
            # 数字8桁で始まる日付フォルダのみ処理
            if len(date_dir) < 8:
                continue
            if not date_dir[:8].isdigit():
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




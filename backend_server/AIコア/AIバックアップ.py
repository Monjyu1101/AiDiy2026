# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101
# -------------------------------------------------------------------------

import os
import shutil
import ctypes
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Optional, Tuple, List

from log_config import get_logger

logger = get_logger("バックアップ")

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

# Windows予約デバイス名（削除不可能）
_WINDOWS予約デバイス名 = (
    "con", "prn", "aux", "nul",
    "com1", "com2", "com3", "com4", "com5", "com6", "com7", "com8", "com9",
    "lpt1", "lpt2", "lpt3", "lpt4", "lpt5", "lpt6", "lpt7", "lpt8", "lpt9",
)

# ファイルコピーは軽量な並列数で実行（呼び出し元APIは同期で待機）
_バックアップコピー並列数 = 4


def _コードベース絶対パス取得(アプリ設定=None, backend_dir: Optional[str] = None, セッション設定: Optional[dict] = None) -> str:
    """
    CODE_BASE_PATHの絶対パスを取得
    優先順位: 1. セッション設定, 2. アプリ設定, 3. デフォルト("../")
    """
    raw_path = "../"
    
    # 1. セッション設定から取得（最優先）
    if セッション設定 and "CODE_BASE_PATH" in セッション設定:
        raw_path = セッション設定["CODE_BASE_PATH"]
    # 2. アプリ設定から取得
    elif アプリ設定 and hasattr(アプリ設定, "json"):
        raw_path = アプリ設定.json.get("CODE_BASE_PATH", "../")
    
    normalized = raw_path.replace("\\", "/").strip()
    base_dir = backend_dir or os.path.dirname(os.path.abspath(__file__))
    if os.path.isabs(normalized):
        return os.path.abspath(normalized)
    return os.path.abspath(os.path.join(base_dir, normalized))


def コードベース絶対パス取得(アプリ設定=None, backend_dir: Optional[str] = None, セッション設定: Optional[dict] = None) -> str:
    """CODE_BASE_PATH の絶対パスを返す公開ヘルパー"""
    return _コードベース絶対パス取得(アプリ設定=アプリ設定, backend_dir=backend_dir, セッション設定=セッション設定)


def バックアップ実行_共通ログ(
    呼出しロガー=None,
    アプリ設定=None,
    backend_dir: Optional[str] = None,
    セッション設定: Optional[dict] = None,
) -> Optional[Tuple[str, List[str], List[str], bool, str]]:
    """
    呼び出し元ロガーに開始/終了を必ず出す共通ラッパー
    - 開始は呼び出し直後に出力
    - 終了は結果の有無に関わらず出力（差分なしは件数0）
    """
    base_path = _コードベース絶対パス取得(
        アプリ設定=アプリ設定,
        backend_dir=backend_dir,
        セッション設定=セッション設定,
    )
    log = 呼出しロガー or logger
    log.info(f"バックアップ開始({base_path})")
    result = バックアップ実行(
        アプリ設定=アプリ設定,
        backend_dir=backend_dir,
        セッション設定=セッション設定,
        ログ出力=False,
    )
    count = len(result[2]) if result else 0
    log.info(f"バックアップ終了(件数={count})")
    return result


def _最新更新と全ファイル一覧(ベースパス: str) -> Tuple[float, List[str]]:
    max_mtime = 0.0
    files: List[str] = []
    workspace_root = os.path.abspath(ベースパス)
    for root, dirs, file_names in os.walk(workspace_root):
        dirs[:] = [d for d in dirs if not any(marker in d for marker in _バックアップ除外フォルダ) and not d.startswith(".")]
        for file_name in file_names:
            file_path = os.path.join(root, file_name)

            # Windows予約デバイス名 + null チェック（削除不可能/問題ファイルのため警告のみ）
            base_name = os.path.splitext(file_name)[0].lower()
            if base_name in _WINDOWS予約デバイス名 or base_name == "null":
                if os.name == "nt" and base_name in ("nul", "null"):
                    _nul_nullファイル削除試行(file_path)
                logger.warning(f"問題のあるファイル名を検出（バックアップ対象外）: {file_path}")
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


def _nul_nullファイル削除試行(file_path: str) -> bool:
    """Windows環境で nul/null ファイル削除を試行（失敗しても継続）"""
    if os.name != "nt":
        return False

    try:
        abs_path = os.path.abspath(file_path)
        if abs_path.startswith("\\\\"):
            unc_path = "\\\\?\\UNC\\" + abs_path[2:]
        else:
            unc_path = "\\\\?\\" + abs_path

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        delete_file_w = kernel32.DeleteFileW
        delete_file_w.argtypes = [ctypes.c_wchar_p]
        delete_file_w.restype = ctypes.c_int

        result = delete_file_w(unc_path)
        if result:
            logger.info(f"問題ファイルを削除しました: {file_path}")
            return True

        error_code = ctypes.get_last_error()
        error_message = ctypes.FormatError(error_code).strip()
        logger.error(
            f"問題ファイルの削除に失敗しました: {file_path}, "
            f"error_code={error_code}, error={error_message}"
        )
        return False
    except Exception as e:
        logger.error(f"問題ファイルの削除中に例外が発生しました: {file_path}, error={e}")
        return False


def バックアップ実行(
    アプリ設定=None,
    backend_dir: Optional[str] = None,
    セッション設定: Optional[dict] = None,
    ログ出力: bool = True,
) -> Optional[Tuple[str, List[str], List[str], bool, str]]:
    """
    シンプル差分バックアップ実行
    - 初回（*.allフォルダなし）→ 全件バックアップ
    - 2回目以降 → 最終バックアップ時刻+1秒以降の差分のみ
    
    セッション設定: セッション固有のCODE_BASE_PATHを含む辞書（オプション）
    戻り値: (最終更新時刻, 全ファイル一覧, バックアップファイル一覧, 全件フラグ, バックアップフォルダ絶対パス) または None（差分なしまたはエラー）
    """
    try:
        base_path = _コードベース絶対パス取得(アプリ設定, backend_dir=backend_dir, セッション設定=セッション設定)
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
            target_dir = os.path.abspath(os.path.join(backup_root, date_dir, f"{time_dir}.all"))
            if ログ出力:
                logger.info(f"バックアップ開始({base_path})")
            if _ファイルコピー実行(base_path, all_files, target_dir):
                if ログ出力:
                    logger.info(f"バックアップ終了(件数={len(all_files)})")
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
            return None
        
        # 差分バックアップ作成
        target_dir = os.path.abspath(os.path.join(backup_root, date_dir, time_dir))
        if os.path.isdir(target_dir):
            return None
        
        if ログ出力:
            logger.info(f"バックアップ開始({base_path})")
        if _ファイルコピー実行(base_path, changed_files, target_dir):
            if ログ出力:
                logger.info(f"バックアップ終了(件数={len(changed_files)})")
            return (最終時刻, all_files, changed_files, False, target_dir)
        return None

    except Exception as e:
        logger.error(f"バックアップ実行エラー: {e}")
        return None


def _ファイルコピー実行(base_path: str, file_list: List[str], target_dir: str) -> bool:
    """ファイルリストをtarget_dirにコピー"""
    try:
        os.makedirs(target_dir, exist_ok=True)
        targets: List[Tuple[str, str]] = []
        for rel_path in file_list:
            src_path = os.path.join(base_path, rel_path.replace("/", os.sep))
            if not os.path.exists(src_path):
                continue
            dest_path = os.path.join(target_dir, rel_path.replace("/", os.sep))
            targets.append((src_path, dest_path))

        if not targets:
            return True

        max_workers = min(_バックアップコピー並列数, len(targets))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_単一ファイルコピー, src_path, dest_path) for src_path, dest_path in targets]
            for future in as_completed(futures):
                if not future.result():
                    return False
        return True
    except Exception as e:
        logger.error(f"ファイルコピーエラー: {e}")
        return False


def _単一ファイルコピー(src_path: str, dest_path: str) -> bool:
    try:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy2(src_path, dest_path)
        return True
    except Exception as e:
        logger.error(f"ファイルコピー失敗: {src_path} -> {dest_path}, エラー: {e}")
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

                # Windows予約デバイス名 + null チェック（削除不可能/問題ファイルのため警告のみ）
                base_name = os.path.splitext(file_name)[0].lower()
                if base_name in _WINDOWS予約デバイス名 or base_name == "null":
                    if os.name == "nt" and base_name in ("nul", "null"):
                        _nul_nullファイル削除試行(file_path)
                    logger.warning(f"問題のあるファイル名を検出（バックアップ対象外）: {file_path}")
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

# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/2026
# -------------------------------------------------------------------------

"""
バックアップ実行モジュール

AiDiy ネイティブの `backend_server/AIコア/AIバックアップ.py` の
`バックアップ実行` / `差分ファイル取得` をそのまま流用する。

設計方針:
- ロジックを二重管理しない。常にネイティブ実装を `importlib.util` で動的ロードする。
- ファイル名に日本語を含むため、パス指定ロードが最も堅い。
- backend_mcp 側にも `log_config.py` があり、ネイティブ実装内の
  `from log_config import get_logger` はこちら側のものが解決される。
"""

import importlib.util
import os
from typing import Optional


class BackupSaveError(Exception):
    """バックアップ実行エラー"""
    pass


def _load_native_module(project_root: str):
    """backend_server/AIコア/AIバックアップ.py を動的にロードする"""
    native_path = os.path.join(
        project_root, "backend_server", "AIコア", "AIバックアップ.py"
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
            self._native = _load_native_module(self.root)
        return self._native

    # ------------------------------------------------------------------ #
    # 公開
    # ------------------------------------------------------------------ #

    def run(self) -> dict:
        """
        ネイティブ `バックアップ実行` を呼び出して差分バックアップを作成する。

        戻り値:
            ok              : 実行成功フラグ
            最終時刻         : 最新ファイルの更新日時（"YYYY-MM-DD HH:MM:SS"）
            全件数           : スキャンした全ファイル数
            バックアップ件数  : 今回コピーしたファイル数（差分ゼロなら 0）
            全件フラグ       : 初回全件バックアップなら True
            バックアップ先    : 作成された日時フォルダの絶対パス（差分ゼロ時は ""）
            差分なし         : 前回バックアップ以降に更新なし
        """
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
        """
        バックアップは実行せず、現時点の差分対象ファイル一覧のみ返す。
        ネイティブの `差分ファイル取得` を利用。
        """
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

# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""
ffmpeg / ffprobe / ffplay 制御モジュール

各サブコマンドの引数文字列（args_str）を受け取り、サブプロセスとして実行する。
高水準のラッパーは設けず、引数構築は呼び出し側（AI）に委ねる。
"""

from __future__ import annotations

import asyncio
import json
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any, Optional

from log_config import get_logger

logger = get_logger(__name__)


class FfmpegControlError(Exception):
    """ffmpeg / ffprobe / ffplay 制御エラー"""


class FfmpegControl:
    """ffmpeg / ffprobe / ffplay の薄いランナー"""

    DEFAULT_FFMPEG_PATH = "ffmpeg"
    DEFAULT_FFPROBE_PATH = "ffprobe"
    DEFAULT_FFPLAY_PATH = "ffplay"
    DEFAULT_TIMEOUT_SEC = 600.0
    DEFAULT_PLAY_TIMEOUT_SEC = 600.0
    DEFAULT_OUTPUT_BYTES = 1024 * 1024  # stdout/stderr の文字列化上限

    # 接続設定ファイル（backend_mcp 起点）
    _FFMPEG_CONFIG_REL = "../backend_server/_config/aidiy_ffmpeg_control.json"

    def __init__(
        self,
        ffmpeg_path: Optional[str] = None,
        ffprobe_path: Optional[str] = None,
        ffplay_path: Optional[str] = None,
        timeout_sec: Optional[float] = None,
    ) -> None:
        config = self._load_or_create_config()

        self.ffmpeg_path = (
            ffmpeg_path
            if ffmpeg_path is not None
            else str(config.get("ffmpeg_path", self.DEFAULT_FFMPEG_PATH))
        )
        self.ffprobe_path = (
            ffprobe_path
            if ffprobe_path is not None
            else str(config.get("ffprobe_path", self.DEFAULT_FFPROBE_PATH))
        )
        self.ffplay_path = (
            ffplay_path
            if ffplay_path is not None
            else str(config.get("ffplay_path", self.DEFAULT_FFPLAY_PATH))
        )
        self.default_timeout_sec = float(
            timeout_sec
            if timeout_sec is not None
            else config.get("default_timeout_sec", self.DEFAULT_TIMEOUT_SEC)
        )
        self.default_play_timeout_sec = float(
            config.get("default_play_timeout_sec", self.DEFAULT_PLAY_TIMEOUT_SEC)
        )

        # 起動時に各実行ファイルの -version を確認する
        self.version_info: dict[str, Any] = self._probe_versions()

    # ------------------------------------------------------------------ #
    # 設定ファイル
    # ------------------------------------------------------------------ #

    def _config_path(self) -> Path:
        return Path(__file__).resolve().parent.parent / self._FFMPEG_CONFIG_REL

    def _default_config(self) -> dict[str, Any]:
        return {
            "version": 1,
            "description": (
                "aidiy_ffmpeg_control の実行ファイルパス・既定タイムアウト設定。"
                " PATH 上にあれば実行ファイル名のみ、別パスならフルパスを指定する。"
            ),
            "ffmpeg_path": self.DEFAULT_FFMPEG_PATH,
            "ffprobe_path": self.DEFAULT_FFPROBE_PATH,
            "ffplay_path": self.DEFAULT_FFPLAY_PATH,
            "default_timeout_sec": self.DEFAULT_TIMEOUT_SEC,
            "default_play_timeout_sec": self.DEFAULT_PLAY_TIMEOUT_SEC,
        }

    def _write_default_config(self, config_path: Path) -> None:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(self._default_config(), f, ensure_ascii=False, indent=2)
            f.write("\n")

    def _load_or_create_config(self) -> dict[str, Any]:
        """設定ファイルがあれば読む。無ければデフォルトを書き出す。"""
        config_path = self._config_path()
        if not config_path.exists():
            try:
                self._write_default_config(config_path)
            except OSError:
                return self._default_config()
            return self._default_config()

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return self._default_config()

        if not isinstance(data, dict):
            return self._default_config()
        return data

    # ------------------------------------------------------------------ #
    # 実行ヘルパー
    # ------------------------------------------------------------------ #

    def _resolve_executable(self, exe_path: str, label: str) -> str:
        """実行ファイルが見つからなければ FfmpegControlError を投げる。"""
        # 区切り文字を含むならフルパス指定。そうでなければ which で解決。
        candidate = Path(exe_path)
        if any(sep in exe_path for sep in ("/", "\\")) or candidate.is_absolute():
            if candidate.is_file():
                return str(candidate)
            raise FfmpegControlError(
                f"{label} が見つかりません: {exe_path}"
            )
        resolved = shutil.which(exe_path)
        if resolved:
            return resolved
        raise FfmpegControlError(
            f"{label} が PATH 上に見つかりません: {exe_path}"
        )

    @staticmethod
    def _split_args(args_str: str) -> list[str]:
        """args_str を shlex で argv リストに変換する（POSIX 風、Windows パスも安全）。"""
        if not isinstance(args_str, str):
            raise FfmpegControlError("args_str は文字列で指定してください")
        try:
            # posix=False で Windows パスのバックスラッシュをエスケープ扱いしない
            return shlex.split(args_str, posix=False)
        except ValueError as e:
            raise FfmpegControlError(f"args_str の解析に失敗しました: {e}") from e

    @staticmethod
    def _decode_bytes(data: bytes, limit: int) -> str:
        if not data:
            return ""
        if len(data) > limit:
            data = data[:limit]
            suffix = b"\n... [truncated]"
            data = data + suffix
        return data.decode("utf-8", errors="replace")

    async def _exec(
        self,
        exe_path: str,
        label: str,
        args_str: str,
        timeout_sec: Optional[float],
        capture_output: bool,
    ) -> dict[str, Any]:
        """汎用サブプロセス実行。capture_output=False の場合は stdout/stderr を捕捉しない。"""
        resolved = self._resolve_executable(exe_path, label)
        argv = [resolved] + self._split_args(args_str)
        effective_timeout = (
            float(timeout_sec) if timeout_sec is not None else self.default_timeout_sec
        )

        try:
            if capture_output:
                proc = await asyncio.create_subprocess_exec(
                    *argv,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
            else:
                proc = await asyncio.create_subprocess_exec(*argv)
        except FileNotFoundError as e:
            raise FfmpegControlError(f"{label} を起動できません: {e}") from e
        except OSError as e:
            raise FfmpegControlError(f"{label} の起動に失敗しました: {e}") from e

        try:
            stdout_b, stderr_b = await asyncio.wait_for(
                proc.communicate(), timeout=effective_timeout
            )
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            raise FfmpegControlError(
                f"{label} がタイムアウトしました（{effective_timeout:g} 秒）"
            )

        return {
            "command": argv,
            "returncode": proc.returncode,
            "stdout": self._decode_bytes(stdout_b or b"", self.DEFAULT_OUTPUT_BYTES),
            "stderr": self._decode_bytes(stderr_b or b"", self.DEFAULT_OUTPUT_BYTES),
            "timeout_sec": effective_timeout,
        }

    # ------------------------------------------------------------------ #
    # 公開操作
    # ------------------------------------------------------------------ #

    async def run_ffmpeg(
        self,
        args_str: str,
        timeout_sec: Optional[float] = None,
    ) -> dict[str, Any]:
        return await self._exec(
            self.ffmpeg_path, "ffmpeg", args_str, timeout_sec, capture_output=True
        )

    async def run_ffprobe(
        self,
        args_str: str,
        timeout_sec: Optional[float] = None,
    ) -> dict[str, Any]:
        return await self._exec(
            self.ffprobe_path, "ffprobe", args_str, timeout_sec, capture_output=True
        )

    async def run_ffplay(
        self,
        args_str: str,
        timeout_sec: Optional[float] = None,
    ) -> dict[str, Any]:
        effective_timeout = (
            float(timeout_sec)
            if timeout_sec is not None
            else self.default_play_timeout_sec
        )
        # ffplay はウィンドウを開く対話アプリ。タイムアウトで kill されるため、
        # 呼び出し側で `-autoexit -t <秒>` を付けて自然終了させるのが望ましい。
        return await self._exec(
            self.ffplay_path,
            "ffplay",
            args_str,
            effective_timeout,
            capture_output=True,
        )

    def _probe_versions(self) -> dict[str, Any]:
        """各実行ファイルに -version を投げて使用可能か確認し、結果をログに残す。"""
        results: dict[str, Any] = {}
        for label, exe_attr in (
            ("ffmpeg", "ffmpeg_path"),
            ("ffprobe", "ffprobe_path"),
            ("ffplay", "ffplay_path"),
        ):
            exe_path = getattr(self, exe_attr)
            try:
                resolved = self._resolve_executable(exe_path, label)
            except FfmpegControlError as e:
                results[label] = {"ok": False, "configured": exe_path, "error": str(e)}
                logger.warning(f"{label} を解決できません: {e}")
                continue

            try:
                proc = subprocess.run(
                    [resolved, "-version"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=10,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                results[label] = {
                    "ok": False,
                    "configured": exe_path,
                    "resolved": resolved,
                    "error": "-version 実行がタイムアウトしました",
                }
                logger.warning(f"{label} -version タイムアウト: {resolved}")
                continue
            except OSError as e:
                results[label] = {
                    "ok": False,
                    "configured": exe_path,
                    "resolved": resolved,
                    "error": str(e),
                }
                logger.warning(f"{label} -version 起動失敗: {e}")
                continue

            stdout_text = (proc.stdout or b"").decode("utf-8", errors="replace")
            first_line = stdout_text.splitlines()[0] if stdout_text else ""
            ok = proc.returncode == 0 and bool(first_line)
            entry: dict[str, Any] = {
                "ok": ok,
                "configured": exe_path,
                "resolved": resolved,
                "returncode": proc.returncode,
                "version": first_line,
            }
            results[label] = entry
            if ok:
                logger.info(f"{label} OK: {first_line}")
            else:
                logger.warning(
                    f"{label} -version 失敗 (rc={proc.returncode}): {resolved}"
                )
        return results

    def get_versions(self) -> dict[str, Any]:
        """設定値と起動時の -version 確認結果を返す。"""
        return {
            "ffmpeg_path": self.ffmpeg_path,
            "ffprobe_path": self.ffprobe_path,
            "ffplay_path": self.ffplay_path,
            "default_timeout_sec": self.default_timeout_sec,
            "default_play_timeout_sec": self.default_play_timeout_sec,
            "checks": self.version_info,
        }

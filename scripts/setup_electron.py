# -*- coding: utf-8 -*-

# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1". See LICENSE for full terms.

"""Avatar / VS Code 共通の Electron 事前セットアップと ZIP キャッシュ。"""

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path


CACHE_DIR = Path(__file__).resolve().parents[1] / "_cache" / "electron"
DOWNLOAD_TIMEOUT = 30


def electron_executable_name() -> str:
    if sys.platform == "win32":
        return "electron.exe"
    if sys.platform == "darwin":
        return "Electron.app/Contents/MacOS/Electron"
    return "electron"


def get_electron_version(frontend_dir: Path) -> str:
    package = frontend_dir / "node_modules" / "electron" / "package.json"
    version = json.loads(package.read_text(encoding="utf-8"))["version"]
    if not isinstance(version, str) or not version:
        raise ValueError("Electron の導入済みバージョンがありません。")
    return version


def _dist_ready(dist: Path, version: str) -> bool:
    try:
        return (
            (dist / electron_executable_name()).is_file()
            and (dist / "version").read_text(encoding="utf-8").strip().removeprefix("v") == version
        )
    except OSError:
        return False


def electron_binary_ready(frontend_dir: Path) -> bool:
    electron_dir = frontend_dir / "node_modules" / "electron"
    try:
        return (
            (electron_dir / "path.txt").read_text(encoding="utf-8") == electron_executable_name()
            and _dist_ready(electron_dir / "dist", get_electron_version(frontend_dir))
        )
    except (OSError, KeyError, ValueError):
        return False


def _archive_ready(archive: Path, version: str) -> bool:
    try:
        with zipfile.ZipFile(archive) as zipped:
            return (
                electron_executable_name() in zipped.namelist()
                and zipped.read("version").decode("utf-8").strip().removeprefix("v") == version
            )
    except (OSError, KeyError, ValueError, zipfile.BadZipFile):
        return False


def _download_archive(archive: Path, version: str, label: str, info) -> None:
    url = f"https://github.com/electron/electron/releases/download/v{version}/{archive.name}"
    info(f"{label}: Electron をダウンロードします: {archive.name}")
    # 未完了の ZIP は共有キャッシュとして公開せず、正常完了後だけ保存する。
    with tempfile.TemporaryDirectory(prefix="download-", dir=archive.parent) as temporary:
        partial = Path(temporary) / archive.name
        started = last_report = time.monotonic()
        with urllib.request.urlopen(url, timeout=DOWNLOAD_TIMEOUT) as response, partial.open("wb") as output:
            total = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            while block := response.read(1024 * 1024):
                output.write(block)
                downloaded += len(block)
                now = time.monotonic()
                if now - last_report >= 2:
                    size = f"{downloaded / 1024 / 1024:.1f} MB"
                    if total:
                        size += f" / {total / 1024 / 1024:.1f} MB ({downloaded * 100 // total}%)"
                    speed = downloaded / 1024 / 1024 / max(now - started, 0.001)
                    info(f"  ダウンロード中: {size}, {speed:.1f} MB/秒")
                    last_report = now
        if total and downloaded != total:
            raise OSError("Electron ZIP のダウンロードが完了していません。")
        if not _archive_ready(partial, version):
            raise ValueError("Electron ZIP の実行ファイル・バージョンを確認できません。")
        partial.replace(archive)
    info(f"{label}: ダウンロード完了。ZIP を共有キャッシュに保存しました。")


def _place_dist(source: Path, frontend_dir: Path, *, move: bool = False) -> None:
    electron_dir = frontend_dir / "node_modules" / "electron"
    dist = electron_dir / "dist"
    if dist.exists():
        shutil.rmtree(dist)
    if move:
        shutil.move(str(source), str(dist))
    else:
        shutil.copytree(source, dist, symlinks=True)
    if sys.platform != "win32":
        (dist / electron_executable_name()).chmod(0o755)
    (electron_dir / "path.txt").write_bytes(electron_executable_name().encode("utf-8"))


def prepare_electron_binary(frontend_dir: Path, label: str, *, info=print, error=print) -> bool:
    """配置済み → 他方の dist → 共有 ZIP → GitHub の順で準備する。"""
    try:
        version = get_electron_version(frontend_dir)
        if electron_binary_ready(frontend_dir):
            info(f"{label}: Electron v{version} の配置を確認しました。")
            return True

        # npm 更新後も dist が一致する場合は path.txt の修復だけでよい。
        electron_dir = frontend_dir / "node_modules" / "electron"
        if _dist_ready(electron_dir / "dist", version):
            (electron_dir / "path.txt").write_bytes(electron_executable_name().encode("utf-8"))
            return True

        for name in ("frontend_avatar", "frontend_vscode"):
            peer = frontend_dir.parent / name
            if peer.resolve() == frontend_dir.resolve():
                continue
            source = peer / "node_modules" / "electron" / "dist"
            if _dist_ready(source, version):
                info(f"{label}: {name} の Electron v{version} を再利用します。")
                _place_dist(source, frontend_dir)
                return electron_binary_ready(frontend_dir)

        machine = platform.machine().lower()
        if machine in ("arm64", "aarch64"):
            arch = "arm64"
        elif machine in ("x86", "i386", "i686"):
            arch = "ia32"
        else:
            arch = "x64"
        plat = "win32" if sys.platform == "win32" else "darwin" if sys.platform == "darwin" else "linux"
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        archive = CACHE_DIR / f"electron-v{version}-{plat}-{arch}.zip"
        if _archive_ready(archive, version):
            info(f"{label}: 保存済み ZIP を再利用します: {archive.name}")
        else:
            archive.unlink(missing_ok=True)
            _download_archive(archive, version, label, info)

        with tempfile.TemporaryDirectory(prefix="extract-", dir=CACHE_DIR) as temporary:
            extracted = Path(temporary) / "dist"
            extracted.mkdir()
            # macOS のシンボリックリンク、Linux の実行権限を保持する。
            if sys.platform != "win32" and shutil.which("unzip"):
                subprocess.run(["unzip", "-q", "-o", str(archive), "-d", str(extracted)], check=True)
            else:
                with zipfile.ZipFile(archive) as zipped:
                    zipped.extractall(extracted)
            if not _dist_ready(extracted, version):
                raise ValueError("展開した Electron の実行ファイル・バージョンを確認できません。")
            _place_dist(extracted, frontend_dir, move=True)
        info(f"{label}: Electron v{version} の配置が完了しました。")
        return electron_binary_ready(frontend_dir)
    except (OSError, KeyError, ValueError, subprocess.SubprocessError, zipfile.BadZipFile) as exc:
        error(f"{label}: Electron の準備に失敗しました: {exc}")
        return False


def setup_dependencies(frontend_dir: Path, npm: str, label: str, run_command, *, info=print, warning=print, error=print) -> bool:
    """npm での重複取得を避け、依存導入後に Electron を一度だけ準備する。"""
    env = {**os.environ, "ELECTRON_SKIP_BINARY_DOWNLOAD": "1"}
    recovery_needed = False
    for action in ("install", "update"):
        if not run_command([npm, action], cwd=frontend_dir, env=env):
            warning(f"{label}: npm {action} を --ignore-scripts で再試行します。")
            recovery_needed = True
            if not run_command([npm, action, "--ignore-scripts"], cwd=frontend_dir, env=env):
                return False
    if not prepare_electron_binary(frontend_dir, label, info=info, error=error):
        return False
    if recovery_needed:
        if not run_command([npm, "rebuild"], cwd=frontend_dir, env=env):
            return False
        if not electron_binary_ready(frontend_dir):
            error(f"{label}: Electron バイナリを確認できません。")
            return False
    return True

#!/usr/bin/env python3
"""Windows-native file operation implementation for Hermes."""

import os
import re
import difflib
import fnmatch
import shutil
import subprocess
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path
from tools.binary_extensions import BINARY_EXTENSIONS

from agent.file_safety import (
    build_write_denied_paths,
    build_write_denied_prefixes,
    get_safe_write_root as _shared_get_safe_write_root,
    is_write_denied as _shared_is_write_denied,
)


# ---------------------------------------------------------------------------
# Write-path deny list — blocks writes to sensitive system/credential files
# ---------------------------------------------------------------------------

_HOME = str(Path.home())

WRITE_DENIED_PATHS = build_write_denied_paths(_HOME)

WRITE_DENIED_PREFIXES = build_write_denied_prefixes(_HOME)


def _get_safe_write_root() -> Optional[str]:
    """Return the resolved HERMES_WRITE_SAFE_ROOT path, or None if unset.

    When set, all write_file/patch operations are constrained to this
    directory tree.  Writes outside it are denied even if the target is
    not on the static deny list.  Opt-in hardening for gateway/messaging
    deployments that should only touch a workspace checkout.
    """
    return _shared_get_safe_write_root()


def _is_write_denied(path: str) -> bool:
    """Return True if path is on the write deny list."""
    return _shared_is_write_denied(path)


# =============================================================================
# Result Data Classes
# =============================================================================

@dataclass
class ReadResult:
    """Result from reading a file."""
    content: str = ""
    total_lines: int = 0
    file_size: int = 0
    truncated: bool = False
    hint: Optional[str] = None
    is_binary: bool = False
    is_image: bool = False
    base64_content: Optional[str] = None
    mime_type: Optional[str] = None
    dimensions: Optional[str] = None  # For images: "WIDTHxHEIGHT"
    error: Optional[str] = None
    similar_files: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None and v != []}


@dataclass
class WriteResult:
    """Result from writing a file."""
    bytes_written: int = 0
    dirs_created: bool = False
    error: Optional[str] = None
    warning: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class PatchResult:
    """Result from patching a file."""
    success: bool = False
    diff: str = ""
    files_modified: List[str] = field(default_factory=list)
    files_created: List[str] = field(default_factory=list)
    files_deleted: List[str] = field(default_factory=list)
    lint: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        result = {"success": self.success}
        if self.diff:
            result["diff"] = self.diff
        if self.files_modified:
            result["files_modified"] = self.files_modified
        if self.files_created:
            result["files_created"] = self.files_created
        if self.files_deleted:
            result["files_deleted"] = self.files_deleted
        if self.lint:
            result["lint"] = self.lint
        if self.error:
            result["error"] = self.error
        return result


@dataclass
class SearchMatch:
    """A single search match."""
    path: str
    line_number: int
    content: str
    mtime: float = 0.0  # Modification time for sorting


@dataclass
class SearchResult:
    """Result from searching."""
    matches: List[SearchMatch] = field(default_factory=list)
    files: List[str] = field(default_factory=list)
    counts: Dict[str, int] = field(default_factory=dict)
    total_count: int = 0
    truncated: bool = False
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        result = {"total_count": self.total_count}
        if self.matches:
            result["matches"] = [
                {"path": m.path, "line": m.line_number, "content": m.content}
                for m in self.matches
            ]
        if self.files:
            result["files"] = self.files
        if self.counts:
            result["counts"] = self.counts
        if self.truncated:
            result["truncated"] = True
        if self.error:
            result["error"] = self.error
        return result


@dataclass
class LintResult:
    """Result from linting a file."""
    success: bool = True
    skipped: bool = False
    output: str = ""
    message: str = ""
    
    def to_dict(self) -> dict:
        if self.skipped:
            return {"status": "skipped", "message": self.message}
        return {
            "status": "ok" if self.success else "error",
            "output": self.output
        }


@dataclass
class ExecuteResult:
    """Result from executing a shell command."""
    stdout: str = ""
    exit_code: int = 0


# =============================================================================
# Abstract Interface
# =============================================================================

class FileOperations(ABC):
    """Abstract interface for file operations across terminal backends."""
    
    @abstractmethod
    def read_file(self, path: str, offset: int = 1, limit: int = 500) -> ReadResult:
        """Read a file with pagination support."""
        ...

    @abstractmethod
    def read_file_raw(self, path: str) -> ReadResult:
        """Read the complete file content as a plain string.

        No pagination, no line-number prefixes, no per-line truncation.
        Returns ReadResult with .content = full file text, .error set on
        failure. Always reads to EOF regardless of file size.
        """
        ...

    @abstractmethod
    def write_file(self, path: str, content: str) -> WriteResult:
        """Write content to a file, creating directories as needed."""
        ...

    @abstractmethod
    def patch_replace(self, path: str, old_string: str, new_string: str,
                      replace_all: bool = False) -> PatchResult:
        """Replace text in a file using fuzzy matching."""
        ...

    @abstractmethod
    def patch_v4a(self, patch_content: str) -> PatchResult:
        """Apply a V4A format patch."""
        ...

    @abstractmethod
    def delete_file(self, path: str) -> WriteResult:
        """Delete a file. Returns WriteResult with .error set on failure."""
        ...

    @abstractmethod
    def move_file(self, src: str, dst: str) -> WriteResult:
        """Move/rename a file from src to dst. Returns WriteResult with .error set on failure."""
        ...

    @abstractmethod
    def search(self, pattern: str, path: str = ".", target: str = "content",
               file_glob: Optional[str] = None, limit: int = 50, offset: int = 0,
               output_mode: str = "content", context: int = 0) -> SearchResult:
        """Search for content or files."""
        ...


# =============================================================================
# Shell-based Implementation
# =============================================================================

# Image extensions (subset of binary that we can return as base64)
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.ico'}

# Linters by file extension
LINTERS = {
    '.py': 'python -m py_compile {file} 2>&1',
    '.js': 'node --check {file} 2>&1',
    '.ts': 'npx tsc --noEmit {file} 2>&1',
    '.go': 'go vet {file} 2>&1',
    '.rs': 'rustfmt --check {file} 2>&1',
}

# Max limits for read operations
MAX_LINES = 2000
MAX_LINE_LENGTH = 2000
MAX_FILE_SIZE = 50 * 1024  # 50KB
DEFAULT_READ_OFFSET = 1
DEFAULT_READ_LIMIT = 500
DEFAULT_SEARCH_OFFSET = 0
DEFAULT_SEARCH_LIMIT = 50


def _coerce_int(value: Any, default: int) -> int:
    """Best-effort integer coercion for tool pagination inputs."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_read_pagination(offset: Any = DEFAULT_READ_OFFSET,
                              limit: Any = DEFAULT_READ_LIMIT) -> tuple[int, int]:
    """Return safe read_file pagination bounds.

    Tool schemas declare minimum/maximum values, but not every caller or
    provider enforces schemas before dispatch. Clamp here so invalid values
    cannot leak into sed ranges like ``0,-1p``.

    The upper bound on ``limit`` comes from ``tool_output.max_lines`` in
    config.yaml (defaults to the module-level ``MAX_LINES`` constant).
    """
    from tools.tool_output_limits import get_max_lines
    max_lines = get_max_lines()
    normalized_offset = max(1, _coerce_int(offset, DEFAULT_READ_OFFSET))
    normalized_limit = _coerce_int(limit, DEFAULT_READ_LIMIT)
    normalized_limit = max(1, min(normalized_limit, max_lines))
    return normalized_offset, normalized_limit


def normalize_search_pagination(offset: Any = DEFAULT_SEARCH_OFFSET,
                                limit: Any = DEFAULT_SEARCH_LIMIT) -> tuple[int, int]:
    """Return safe search pagination bounds for shell head/tail pipelines."""
    normalized_offset = max(0, _coerce_int(offset, DEFAULT_SEARCH_OFFSET))
    normalized_limit = max(1, _coerce_int(limit, DEFAULT_SEARCH_LIMIT))
    return normalized_offset, normalized_limit

class WindowsFileOperations(FileOperations):
    """Windows-native file operations for the local terminal backend."""

    def __init__(self, terminal_env, cwd: str = None):
        self.env = terminal_env
        self.cwd = cwd or getattr(terminal_env, 'cwd', None) or \
                   getattr(getattr(terminal_env, 'config', None), 'cwd', None) or os.getcwd()
        self._command_cache: Dict[str, bool] = {}

    def _is_likely_binary(self, path: str, content_sample: str = None) -> bool:
        ext = os.path.splitext(path)[1].lower()
        if ext in BINARY_EXTENSIONS:
            return True
        if content_sample:
            non_printable = sum(
                1 for c in content_sample[:1000]
                if ord(c) < 32 and c not in '\n\r\t'
            )
            return non_printable / min(len(content_sample), 1000) > 0.30
        return False

    def _is_image(self, path: str) -> bool:
        ext = os.path.splitext(path)[1].lower()
        return ext in IMAGE_EXTENSIONS

    def _add_line_numbers(self, content: str, start_line: int = 1) -> str:
        from tools.tool_output_limits import get_max_line_length
        max_line_length = get_max_line_length()
        lines = content.split('\n')
        numbered = []
        for i, line in enumerate(lines, start=start_line):
            if len(line) > max_line_length:
                line = line[:max_line_length] + "... [truncated]"
            numbered.append(f"{i:6d}|{line}")
        return '\n'.join(numbered)

    def _unified_diff(self, old_content: str, new_content: str, filename: str) -> str:
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
        )
        return ''.join(diff)

    def _live_cwd(self) -> str:
        cwd = getattr(self.env, "cwd", None) or self.cwd or os.getcwd()
        return self._from_msys_path(str(cwd)).replace("\\", "/")

    @staticmethod
    def _from_msys_path(path: str) -> str:
        normalized = str(path).replace("\\", "/")
        if (
            len(normalized) >= 3
            and normalized[0] == "/"
            and normalized[1].isalpha()
            and normalized[2] == "/"
        ):
            return f"{normalized[1].upper()}:{normalized[2:]}"
        return normalized

    def _expand_path(self, path: str) -> str:
        if not path:
            return path
        return os.path.expanduser(self._from_msys_path(path))

    def _resolve_windows_path(self, path: str) -> Path:
        expanded = Path(self._expand_path(path))
        if not expanded.is_absolute():
            expanded = Path(self._live_cwd()) / expanded
        return expanded.resolve(strict=False)

    def _has_command(self, cmd: str) -> bool:
        if cmd not in self._command_cache:
            self._command_cache[cmd] = shutil.which(cmd) is not None
        return self._command_cache[cmd]

    @staticmethod
    def _text_lines_for_count(content: str) -> list[str]:
        if not content:
            return []
        lines = content.split("\n")
        if content.endswith("\n"):
            lines = lines[:-1]
        return lines

    @staticmethod
    def _atomic_write_text(path: Path, content: str) -> None:
        tmp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        try:
            with tmp_path.open("w", encoding="utf-8", errors="replace", newline="") as f:
                f.write(content)
            last_exc = None
            for attempt in range(3):
                try:
                    os.replace(tmp_path, path)
                    return
                except PermissionError as exc:
                    last_exc = exc
                    if attempt < 2:
                        time.sleep(0.1)
            if last_exc:
                raise last_exc
        finally:
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
            except OSError:
                pass

    def _read_text(self, path: Path) -> str:
        with path.open("r", encoding="utf-8", errors="replace", newline=None) as f:
            return f.read().replace("\r\n", "\n").replace("\r", "\n")

    def _is_binary_path(self, path: Path) -> bool:
        if self._is_likely_binary(str(path)):
            return True
        try:
            sample = path.read_bytes()[:1000]
        except OSError:
            return False
        if b"\x00" in sample:
            return True
        if not sample:
            return False
        textish = sum(
            1 for b in sample
            if b in (9, 10, 13) or 32 <= b <= 126 or b >= 128
        )
        return (len(sample) - textish) / len(sample) > 0.30

    def read_file(self, path: str, offset: int = 1, limit: int = 500) -> ReadResult:
        path = self._expand_path(path)
        offset, limit = normalize_read_pagination(offset, limit)
        resolved = self._resolve_windows_path(path)

        if not resolved.is_file():
            return self._suggest_similar_files(path)

        file_size = resolved.stat().st_size
        if self._is_image(str(resolved)):
            return ReadResult(
                is_image=True,
                is_binary=True,
                file_size=file_size,
                hint=(
                    "Image file detected. Automatically redirected to vision_analyze tool. "
                    "Use vision_analyze with this file path to inspect the image contents."
                ),
            )
        if self._is_binary_path(resolved):
            return ReadResult(
                is_binary=True,
                file_size=file_size,
                error="Binary file - cannot display as text. Use appropriate tools to handle this file type."
            )

        try:
            content = self._read_text(resolved)
        except OSError as exc:
            return ReadResult(error=f"Failed to read file: {exc}")

        lines = self._text_lines_for_count(content)
        total_lines = len(lines)
        end_line = offset + limit - 1
        selected = lines[offset - 1:end_line]
        read_content = "\n".join(selected)
        truncated = total_lines > end_line
        hint = None
        if truncated:
            hint = f"Use offset={end_line + 1} to continue reading (showing {offset}-{end_line} of {total_lines} lines)"

        return ReadResult(
            content=self._add_line_numbers(read_content, offset),
            total_lines=total_lines,
            file_size=file_size,
            truncated=truncated,
            hint=hint,
        )

    def _suggest_similar_files(self, path: str) -> ReadResult:
        resolved = self._resolve_windows_path(path)
        dir_path = resolved.parent
        filename = resolved.name
        basename_no_ext = resolved.stem
        ext = resolved.suffix.lower()
        lower_name = filename.lower()

        scored: list[tuple[int, str]] = []
        try:
            entries = list(dir_path.iterdir())[:50]
        except OSError:
            entries = []
        for entry in entries:
            name = entry.name
            lname = name.lower()
            score = 0
            if lname == lower_name:
                score = 100
            elif entry.stem.lower() == basename_no_ext.lower():
                score = 90
            elif lname.startswith(lower_name) or lower_name.startswith(lname):
                score = 70
            elif lower_name in lname:
                score = 60
            elif lname in lower_name and len(lname) > 2:
                score = 40
            elif ext and entry.suffix.lower() == ext:
                common = set(lower_name) & set(lname)
                if len(common) >= max(len(lower_name), len(lname)) * 0.4:
                    score = 30
            if score > 0:
                scored.append((score, str(entry)))

        scored.sort(key=lambda x: -x[0])
        return ReadResult(
            error=f"File not found: {path}",
            similar_files=[fp for _, fp in scored[:5]],
        )

    def read_file_raw(self, path: str) -> ReadResult:
        path = self._expand_path(path)
        resolved = self._resolve_windows_path(path)
        if not resolved.is_file():
            return self._suggest_similar_files(path)
        file_size = resolved.stat().st_size
        if self._is_image(str(resolved)):
            return ReadResult(is_image=True, is_binary=True, file_size=file_size)
        if self._is_binary_path(resolved):
            return ReadResult(
                is_binary=True,
                file_size=file_size,
                error="Binary file — cannot display as text.",
            )
        try:
            return ReadResult(content=self._read_text(resolved), file_size=file_size)
        except OSError as exc:
            return ReadResult(error=f"Failed to read file: {exc}")

    def delete_file(self, path: str) -> WriteResult:
        path = self._expand_path(path)
        if _is_write_denied(path):
            return WriteResult(error=f"Delete denied: {path} is a protected path")
        resolved = self._resolve_windows_path(path)
        try:
            if resolved.exists():
                resolved.unlink()
            return WriteResult()
        except OSError as exc:
            return WriteResult(error=f"Failed to delete {path}: {exc}")

    def move_file(self, src: str, dst: str) -> WriteResult:
        src = self._expand_path(src)
        dst = self._expand_path(dst)
        for p in (src, dst):
            if _is_write_denied(p):
                return WriteResult(error=f"Move denied: {p} is a protected path")
        src_path = self._resolve_windows_path(src)
        dst_path = self._resolve_windows_path(dst)
        try:
            shutil.move(str(src_path), str(dst_path))
            return WriteResult()
        except OSError as exc:
            return WriteResult(error=f"Failed to move {src} -> {dst}: {exc}")

    def write_file(self, path: str, content: str) -> WriteResult:
        path = self._expand_path(path)
        if _is_write_denied(path):
            return WriteResult(error=f"Write denied: '{path}' is a protected system/credential file.")

        resolved = self._resolve_windows_path(path)
        dirs_created = False
        try:
            if not resolved.parent.exists():
                resolved.parent.mkdir(parents=True, exist_ok=True)
                dirs_created = True
            self._atomic_write_text(resolved, content)
            return WriteResult(
                bytes_written=resolved.stat().st_size,
                dirs_created=dirs_created,
            )
        except OSError as exc:
            return WriteResult(error=f"Failed to write file: {exc}")

    def patch_replace(self, path: str, old_string: str, new_string: str,
                      replace_all: bool = False) -> PatchResult:
        path = self._expand_path(path)
        if _is_write_denied(path):
            return PatchResult(error=f"Write denied: '{path}' is a protected system/credential file.")

        resolved = self._resolve_windows_path(path)
        try:
            content = self._read_text(resolved)
        except OSError:
            return PatchResult(error=f"Failed to read file: {path}")

        from tools.fuzzy_match import fuzzy_find_and_replace

        new_content, match_count, _strategy, error = fuzzy_find_and_replace(
            content, old_string, new_string, replace_all
        )

        if error or match_count == 0:
            err_msg = error or f"Could not find match for old_string in {path}"
            try:
                from tools.fuzzy_match import format_no_match_hint
                err_msg += format_no_match_hint(err_msg, match_count, old_string, content)
            except Exception:
                pass
            return PatchResult(error=err_msg)

        write_result = self.write_file(path, new_content)
        if write_result.error:
            return PatchResult(error=f"Failed to write changes: {write_result.error}")

        try:
            verify_content = self._read_text(resolved)
        except OSError:
            return PatchResult(error=f"Post-write verification failed: could not re-read {path}")
        if verify_content != new_content:
            return PatchResult(error=(
                f"Post-write verification failed for {path}: on-disk content "
                f"differs from intended write "
                f"(wrote {len(new_content)} chars, read back {len(verify_content)}). "
                "The patch did not persist. Re-read the file and try again."
            ))

        lint_result = self._check_lint(str(resolved))
        return PatchResult(
            success=True,
            diff=self._unified_diff(content, new_content, path),
            files_modified=[path],
            lint=lint_result.to_dict() if lint_result else None,
        )

    def patch_v4a(self, patch_content: str) -> PatchResult:
        from tools.patch_parser import parse_v4a_patch, apply_v4a_operations

        operations, parse_error = parse_v4a_patch(patch_content)
        if parse_error:
            return PatchResult(error=f"Failed to parse patch: {parse_error}")
        return apply_v4a_operations(operations, self)

    def _check_lint(self, path: str) -> LintResult:
        ext = os.path.splitext(path)[1].lower()
        if ext not in LINTERS:
            return LintResult(skipped=True, message=f"No linter for {ext} files")

        linter_cmd = LINTERS[ext]
        base_cmd = linter_cmd.split()[0]
        if not self._has_command(base_cmd):
            return LintResult(skipped=True, message=f"{base_cmd} not available")

        if ext == ".py":
            args = ["python", "-m", "py_compile", path]
        elif ext == ".js":
            args = ["node", "--check", path]
        elif ext == ".ts":
            args = ["npx", "tsc", "--noEmit", path]
        elif ext == ".go":
            args = ["go", "vet", path]
        elif ext == ".rs":
            args = ["rustfmt", "--check", path]
        else:
            return LintResult(skipped=True, message=f"No Windows-native linter for {ext} files")

        result = subprocess.run(
            args,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=30,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return LintResult(
            success=result.returncode == 0,
            output=result.stdout.strip() if result.stdout.strip() else "",
        )

    def search(self, pattern: str, path: str = ".", target: str = "content",
               file_glob: Optional[str] = None, limit: int = 50, offset: int = 0,
               output_mode: str = "content", context: int = 0) -> SearchResult:
        offset, limit = normalize_search_pagination(offset, limit)
        path = self._expand_path(path)
        resolved = self._resolve_windows_path(path)
        if not resolved.exists():
            return SearchResult(error=f"Path not found: {path}", total_count=0)
        if target == "files":
            return self._search_files(pattern, str(resolved), limit, offset)
        return self._search_content(pattern, str(resolved), file_glob, limit, offset,
                                    output_mode, context)

    @staticmethod
    def _visible_file_paths(root: Path, glob_pattern: str | None = None) -> list[Path]:
        paths: list[Path] = []
        if root.is_file():
            return [root]
        for candidate in root.rglob(glob_pattern or "*"):
            try:
                rel_parts = candidate.relative_to(root).parts
            except ValueError:
                rel_parts = candidate.parts
            if any(part.startswith(".") for part in rel_parts):
                continue
            if candidate.is_file():
                paths.append(candidate)
        return paths

    def _search_files(self, pattern: str, path: str, limit: int, offset: int) -> SearchResult:
        root = Path(path)
        search_pattern = pattern.split("/")[-1] if "/" in pattern else pattern
        if not search_pattern:
            search_pattern = "*"

        try:
            all_files = self._visible_file_paths(root, search_pattern)
            all_files.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
        except OSError as exc:
            return SearchResult(error=f"File search failed: {exc}", total_count=0)

        page = [str(p) for p in all_files[offset:offset + limit]]
        return SearchResult(
            files=page,
            total_count=len(all_files),
            truncated=len(all_files) > offset + limit,
        )

    def _search_content(self, pattern: str, path: str, file_glob: Optional[str],
                        limit: int, offset: int, output_mode: str, context: int) -> SearchResult:
        if self._has_command("rg"):
            return self._search_with_rg_native(pattern, path, file_glob, limit, offset,
                                               output_mode, context)
        return self._search_content_python(pattern, path, file_glob, limit, offset,
                                           output_mode, context)

    def _search_with_rg_native(self, pattern: str, path: str, file_glob: Optional[str],
                               limit: int, offset: int, output_mode: str,
                               context: int) -> SearchResult:
        args = ["rg", "--line-number", "--no-heading", "--with-filename"]
        if context > 0:
            args.extend(["-C", str(context)])
        if file_glob:
            args.extend(["--glob", file_glob])
        if output_mode == "files_only":
            args.append("-l")
        elif output_mode == "count":
            args.append("-c")
        args.extend([pattern, path])

        fetch_limit = limit + offset + (200 if context > 0 else 0)
        try:
            proc = subprocess.Popen(
                args,
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            rows = []
            reader_done = threading.Event()
            assert proc.stdout is not None

            def _read_rows() -> None:
                try:
                    while len(rows) < fetch_limit:
                        line = proc.stdout.readline()
                        if not line:
                            break
                        line = line.rstrip("\r\n")
                        if line and line != "--":
                            rows.append(line)
                finally:
                    reader_done.set()

            threading.Thread(target=_read_rows, daemon=True).start()
            deadline = time.monotonic() + 60
            while proc.poll() is None and not reader_done.is_set():
                if len(rows) >= fetch_limit:
                    proc.terminate()
                    break
                if time.monotonic() > deadline:
                    proc.kill()
                    return SearchResult(error="Search timed out after 60s", total_count=0)
                time.sleep(0.05)
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=2)
            else:
                proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            return SearchResult(error="Search timed out after 60s", total_count=0)
        except OSError as exc:
            return SearchResult(error=f"Search failed: {exc}", total_count=0)

        if proc.returncode == 2 and not rows:
            return SearchResult(error="Search failed", total_count=0)

        if output_mode == "files_only":
            page = rows[offset:offset + limit]
            return SearchResult(files=page, total_count=len(rows), truncated=len(rows) >= fetch_limit)
        if output_mode == "count":
            counts = {}
            for line in rows:
                if ":" in line:
                    file_path, value = line.rsplit(":", 1)
                    try:
                        counts[file_path] = int(value)
                    except ValueError:
                        pass
            return SearchResult(
                counts=counts,
                total_count=sum(counts.values()),
                truncated=len(rows) >= fetch_limit,
            )

        match_re = re.compile(r'^([A-Za-z]:)?(.*?):(\d+):(.*)$')
        ctx_re = re.compile(r'^([A-Za-z]:)?(.*?)-(\d+)-(.*)$')
        matches: list[SearchMatch] = []
        for line in rows:
            m = match_re.match(line)
            if not m and context > 0:
                m = ctx_re.match(line)
            if not m:
                continue
            matches.append(SearchMatch(
                path=(m.group(1) or "") + m.group(2),
                line_number=int(m.group(3)),
                content=m.group(4)[:500],
            ))

        page = matches[offset:offset + limit]
        return SearchResult(
            matches=page,
            total_count=len(matches),
            truncated=len(matches) >= fetch_limit,
        )

    def _search_content_python(self, pattern: str, path: str, file_glob: Optional[str],
                               limit: int, offset: int, output_mode: str,
                               context: int) -> SearchResult:
        try:
            regex = re.compile(pattern)
        except re.error as exc:
            return SearchResult(error=f"Invalid regex: {exc}", total_count=0)

        root = Path(path)
        try:
            candidates = self._visible_file_paths(root, file_glob or "*")
        except OSError as exc:
            return SearchResult(error=f"Search failed: {exc}", total_count=0)

        matches: list[SearchMatch] = []
        counts: dict[str, int] = {}
        files_only: list[str] = []
        fetch_limit = limit + offset + (200 if context > 0 else 0)
        for file_path in candidates:
            if file_glob and not fnmatch.fnmatch(file_path.name, file_glob):
                continue
            if self._is_binary_path(file_path):
                continue
            try:
                lines = self._read_text(file_path).splitlines()
            except OSError:
                continue
            file_count = 0
            for idx, line in enumerate(lines, start=1):
                if regex.search(line):
                    file_count += 1
                    matches.append(SearchMatch(str(file_path), idx, line[:500]))
            if file_count:
                counts[str(file_path)] = file_count
                files_only.append(str(file_path))
                if output_mode == "files_only" and len(files_only) >= fetch_limit:
                    break
                if output_mode == "count" and len(counts) >= fetch_limit:
                    break
            if output_mode == "content" and len(matches) >= fetch_limit:
                break

        if output_mode == "files_only":
            page = files_only[offset:offset + limit]
            return SearchResult(files=page, total_count=len(files_only), truncated=len(files_only) >= fetch_limit)
        if output_mode == "count":
            return SearchResult(
                counts=counts,
                total_count=sum(counts.values()),
                truncated=len(counts) >= fetch_limit,
            )
        page = matches[offset:offset + limit]
        return SearchResult(
            matches=page,
            total_count=len(matches),
            truncated=len(matches) >= fetch_limit,
        )


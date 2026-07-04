"""Local execution environment — spawn-per-call with session snapshot."""

import os
import platform
import re
import shutil
import signal
import subprocess
import tempfile
import time

from tools.environments.base import BaseEnvironment, _pipe_stdin

_IS_WINDOWS = platform.system() == "Windows"


# Hermes-internal env vars that should NOT leak into terminal subprocesses.
_HERMES_PROVIDER_ENV_FORCE_PREFIX = "_HERMES_FORCE_"


def _build_provider_env_blocklist() -> frozenset:
    """Derive the blocklist from provider, tool, and gateway config."""
    blocked: set[str] = set()

    try:
        from hermes_cli.auth import PROVIDER_REGISTRY
        for pconfig in PROVIDER_REGISTRY.values():
            blocked.update(pconfig.api_key_env_vars)
            if pconfig.base_url_env_var:
                blocked.add(pconfig.base_url_env_var)
    except ImportError:
        pass

    try:
        from hermes_cli.config import OPTIONAL_ENV_VARS
        for name, metadata in OPTIONAL_ENV_VARS.items():
            category = metadata.get("category")
            if category in {"tool", "messaging"}:
                blocked.add(name)
            elif category == "setting" and metadata.get("password"):
                blocked.add(name)
    except ImportError:
        pass

    blocked.update({
        "OPENAI_BASE_URL",
        "OPENAI_API_KEY",
        "OPENAI_API_BASE",
        "OPENAI_ORG_ID",
        "OPENAI_ORGANIZATION",
        "OPENROUTER_API_KEY",
        "ANTHROPIC_BASE_URL",
        "ANTHROPIC_TOKEN",
        "CLAUDE_CODE_OAUTH_TOKEN",
        "LLM_MODEL",
        "GOOGLE_API_KEY",
        "DEEPSEEK_API_KEY",
        "MISTRAL_API_KEY",
        "GROQ_API_KEY",
        "TOGETHER_API_KEY",
        "PERPLEXITY_API_KEY",
        "COHERE_API_KEY",
        "FIREWORKS_API_KEY",
        "XAI_API_KEY",
        "HELICONE_API_KEY",
        "PARALLEL_API_KEY",
        "FIRECRAWL_API_KEY",
        "FIRECRAWL_API_URL",
        "TELEGRAM_HOME_CHANNEL",
        "TELEGRAM_HOME_CHANNEL_NAME",
        "DISCORD_HOME_CHANNEL",
        "DISCORD_HOME_CHANNEL_NAME",
        "DISCORD_REQUIRE_MENTION",
        "DISCORD_FREE_RESPONSE_CHANNELS",
        "DISCORD_AUTO_THREAD",
        "SLACK_HOME_CHANNEL",
        "SLACK_HOME_CHANNEL_NAME",
        "SLACK_ALLOWED_USERS",
        "WHATSAPP_ENABLED",
        "WHATSAPP_MODE",
        "WHATSAPP_ALLOWED_USERS",
        "SIGNAL_HTTP_URL",
        "SIGNAL_ACCOUNT",
        "SIGNAL_ALLOWED_USERS",
        "SIGNAL_GROUP_ALLOWED_USERS",
        "SIGNAL_HOME_CHANNEL",
        "SIGNAL_HOME_CHANNEL_NAME",
        "SIGNAL_IGNORE_STORIES",
        "HASS_TOKEN",
        "HASS_URL",
        "EMAIL_ADDRESS",
        "EMAIL_PASSWORD",
        "EMAIL_IMAP_HOST",
        "EMAIL_SMTP_HOST",
        "EMAIL_HOME_ADDRESS",
        "EMAIL_HOME_ADDRESS_NAME",
        "GATEWAY_ALLOWED_USERS",
        "GH_TOKEN",
        "GITHUB_APP_ID",
        "GITHUB_APP_PRIVATE_KEY_PATH",
        "GITHUB_APP_INSTALLATION_ID",
        "MODAL_TOKEN_ID",
        "MODAL_TOKEN_SECRET",
        "DAYTONA_API_KEY",
        "VERCEL_OIDC_TOKEN",
        "VERCEL_TOKEN",
        "VERCEL_PROJECT_ID",
        "VERCEL_TEAM_ID",
    })
    return frozenset(blocked)


_HERMES_PROVIDER_ENV_BLOCKLIST = _build_provider_env_blocklist()


def _sanitize_subprocess_env(base_env: dict | None, extra_env: dict | None = None) -> dict:
    """Filter Hermes-managed secrets from a subprocess environment."""
    try:
        from tools.env_passthrough import is_env_passthrough as _is_passthrough
    except Exception:
        _is_passthrough = lambda _: False  # noqa: E731

    sanitized: dict[str, str] = {}

    for key, value in (base_env or {}).items():
        if key.startswith(_HERMES_PROVIDER_ENV_FORCE_PREFIX):
            continue
        if key not in _HERMES_PROVIDER_ENV_BLOCKLIST or _is_passthrough(key):
            sanitized[key] = value

    for key, value in (extra_env or {}).items():
        if key.startswith(_HERMES_PROVIDER_ENV_FORCE_PREFIX):
            real_key = key[len(_HERMES_PROVIDER_ENV_FORCE_PREFIX):]
            sanitized[real_key] = value
        elif key not in _HERMES_PROVIDER_ENV_BLOCKLIST or _is_passthrough(key):
            sanitized[key] = value

    # Per-profile HOME isolation for background processes (same as _make_run_env).
    from hermes_constants import get_subprocess_home
    _profile_home = get_subprocess_home()
    if _profile_home:
        sanitized["HOME"] = _profile_home

    return sanitized


def _find_bash() -> str:
    """Find bash on POSIX, or the selected local shell path on Windows."""
    if not _IS_WINDOWS:
        return (
            shutil.which("bash")
            or ("/usr/bin/bash" if os.path.isfile("/usr/bin/bash") else None)
            or ("/bin/bash" if os.path.isfile("/bin/bash") else None)
            or os.environ.get("SHELL")
            or "/bin/sh"
        )

    kind, path = _find_windows_shell()
    return path


def _find_windows_shell() -> tuple[str, str]:
    """Find the best local shell on Windows.

    Prefer bash when available for compatibility with the existing POSIX
    wrapper, but fall back to PowerShell so Git for Windows is not required.
    """
    if not _IS_WINDOWS:
        return ("bash", _find_bash())

    custom = os.environ.get("HERMES_GIT_BASH_PATH")
    if custom and os.path.isfile(custom):
        return ("bash", custom)

    # Prefer Git for Windows bash over System32\bash.exe (WSL). WSL's bash
    # cannot execute POSIX commands against Windows host paths (D:/... is
    # invisible without /mnt/d/...) and its cold-start latency trips the
    # tool's 30s I/O timeout, producing silent [error] returns for read /
    # find / cd. Git Bash handles Windows paths via MSYS translation and
    # spawns instantly.
    for candidate in (
        os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Git", "bin", "bash.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), "Git", "bin", "bash.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Git", "bin", "bash.exe"),
    ):
        if candidate and os.path.isfile(candidate):
            return ("bash", candidate)

    found = shutil.which("bash")
    if found and "\\system32\\" not in found.lower():
        return ("bash", found)

    for name in ("pwsh", "powershell"):
        found = shutil.which(name)
        if found:
            return ("powershell", found)

    for candidate in (
        os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "WindowsPowerShell", "v1.0", "powershell.exe"),
    ):
        if candidate and os.path.isfile(candidate):
            return ("powershell", candidate)

    raise RuntimeError(
        "No usable shell found. Hermes Agent requires either Git Bash, PowerShell 7 (pwsh), "
        "or Windows PowerShell on Windows."
    )


# Backward compat — process_registry.py imports this name
_find_shell = _find_bash


if os.name == 'nt':
    def _to_msys_path(path: str) -> str:
        """Convert 'D:\\foo\\bar' or 'D:/foo/bar' to '/d/foo/bar' for Git Bash."""
        if not path:
            return path
        normalized = path.replace("\\", "/")
        if len(normalized) >= 2 and normalized[1] == ":":
            return f"/{normalized[0].lower()}{normalized[2:]}"
        return normalized


    def _from_msys_path(path: str) -> str:
        """Convert '/d/foo/bar' from Git Bash back to 'D:/foo/bar'."""
        if not path:
            return path
        normalized = path.replace("\\", "/")
        if (
            len(normalized) >= 3
            and normalized[0] == "/"
            and normalized[1].isalpha()
            and normalized[2] == "/"
        ):
            return f"{normalized[1].upper()}:{normalized[2:]}"
        return normalized


    def _ps_quote(value: str) -> str:
        return "'" + str(value).replace("'", "''") + "'"


    def _strip_shell_quotes(value: str) -> str:
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            return value[1:-1]
        return value


    def _normalize_win_literal_path(value: str) -> str:
        value = _strip_shell_quotes(value)
        value = _from_msys_path(value)
        return value.replace("\\", "/")


    def _translate_posixish_to_powershell(command: str) -> str:
        """Translate the small POSIX-ish command subset Hermes commonly emits.

        Unknown commands are still executed as PowerShell scriptblocks, which
        keeps native commands like git/npm/python working without Git Bash.
        """
        parts = [part.strip() for part in command.split("&&")]
        script_parts = ["$__hermes_ec = 0"]
        for idx, part in enumerate(parts):
            if not part:
                continue
            translated = _translate_single_posixish_part(part)
            if idx == 0:
                script_parts.append(translated)
            else:
                script_parts.append(f"if ($__hermes_ec -eq 0) {{\n{translated}\n}}")
        return "\n".join(script_parts)


    def _translate_single_posixish_part(command: str) -> str:
        command = command.strip()
        if command == "pwd":
            return "(Get-Location).ProviderPath\n$__hermes_ec = 0"

        m = re.fullmatch(
            r"ls(?:\s+-(?P<flags>[A-Za-z]+))?"
            r"(?:\s+(?P<path>[^|]+?))?"
            r"(?:\s*\|\s*head\s+-(?P<head>\d+))?",
            command,
        )
        if m:
            flags = m.group("flags") or ""
            raw_path = _normalize_win_literal_path(m.group("path") or ".")
            force = " -Force" if "a" in flags.lower() else ""
            head = m.group("head")
            head_pipe = f" | Select-Object -First {int(head)}" if head else ""
            return (
                f"Get-ChildItem{force} -LiteralPath {_ps_quote(raw_path)}{head_pipe} | Format-Table -AutoSize\n"
                "$__hermes_ec = if ($?) { 0 } else { 1 }"
            )

        m = re.fullmatch(r"test\s+-(?P<kind>[efd])\s+(?P<path>.+)", command)
        if not m:
            m = re.fullmatch(r"\[\s+-(?P<kind>[efd])\s+(?P<path>.+?)\s+\]", command)
        if m:
            kind = m.group("kind")
            raw_path = _normalize_win_literal_path(m.group("path"))
            test_path = f"Test-Path -LiteralPath {_ps_quote(raw_path)}"
            if kind == "f":
                test_path = f"({test_path} -PathType Leaf)"
            elif kind == "d":
                test_path = f"({test_path} -PathType Container)"
            return f"if ({test_path}) {{ $__hermes_ec = 0 }} else {{ $__hermes_ec = 1 }}"

        m = re.fullmatch(r"echo(?:\s+(?P<text>.*))?", command)
        if m:
            return f"Write-Output {_ps_quote(_strip_shell_quotes(m.group('text') or ''))}\n$__hermes_ec = 0"

        m = re.fullmatch(r"cd\s+(?P<path>.+)", command)
        if m:
            raw_path = _normalize_win_literal_path(m.group("path"))
            return (
                f"Set-Location -LiteralPath {_ps_quote(raw_path)}\n"
                "$__hermes_ec = if ($?) { 0 } else { 1 }"
            )

        return (
            f"& ([scriptblock]::Create({_ps_quote(command)}))\n"
            "$__hermes_ec = if ($LASTEXITCODE -ne $null) { $LASTEXITCODE } elseif ($?) { 0 } else { 1 }"
        )


# Standard PATH entries for environments with minimal PATH.
_SANE_PATH = (
    "/opt/homebrew/bin:/opt/homebrew/sbin:"
    "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
)


def _make_run_env(env: dict) -> dict:
    """Build a run environment with a sane PATH and provider-var stripping."""
    try:
        from tools.env_passthrough import is_env_passthrough as _is_passthrough
    except Exception:
        _is_passthrough = lambda _: False  # noqa: E731

    merged = dict(os.environ | env)
    run_env = {}
    for k, v in merged.items():
        if k.startswith(_HERMES_PROVIDER_ENV_FORCE_PREFIX):
            real_key = k[len(_HERMES_PROVIDER_ENV_FORCE_PREFIX):]
            run_env[real_key] = v
        elif k not in _HERMES_PROVIDER_ENV_BLOCKLIST or _is_passthrough(k):
            run_env[k] = v
    existing_path = run_env.get("PATH", "")
    if "/usr/bin" not in existing_path.split(":"):
        run_env["PATH"] = f"{existing_path}:{_SANE_PATH}" if existing_path else _SANE_PATH

    # Per-profile HOME isolation: redirect system tool configs (git, ssh, gh,
    # npm …) into {HERMES_HOME}/home/ when that directory exists.  Only the
    # subprocess sees the override — the Python process keeps the real HOME.
    from hermes_constants import get_subprocess_home
    _profile_home = get_subprocess_home()
    if _profile_home:
        run_env["HOME"] = _profile_home

    return run_env


def _read_terminal_shell_init_config() -> tuple[list[str], bool]:
    """Return (shell_init_files, auto_source_bashrc) from config.yaml.

    Best-effort — returns sensible defaults on any failure so terminal
    execution never breaks because the config file is unreadable.
    """
    try:
        from hermes_cli.config import load_config

        cfg = load_config() or {}
        terminal_cfg = cfg.get("terminal") or {}
        files = terminal_cfg.get("shell_init_files") or []
        if not isinstance(files, list):
            files = []
        auto_bashrc = bool(terminal_cfg.get("auto_source_bashrc", True))
        return [str(f) for f in files if f], auto_bashrc
    except Exception:
        return [], True


def _resolve_shell_init_files() -> list[str]:
    """Resolve the list of files to source before the login-shell snapshot.

    Expands ``~`` and ``${VAR}`` references and drops anything that doesn't
    exist on disk, so a missing ``~/.bashrc`` never breaks the snapshot.
    The ``auto_source_bashrc`` path runs only when the user hasn't supplied
    an explicit list — once they have, Hermes trusts them.
    """
    explicit, auto_bashrc = _read_terminal_shell_init_config()

    candidates: list[str] = []
    if explicit:
        candidates.extend(explicit)
    elif auto_bashrc and not _IS_WINDOWS:
        # Build a login-shell-ish source list so tools like n / nvm / asdf /
        # pyenv that self-install into the user's shell rc land on PATH in
        # the captured snapshot.
        #
        # ~/.profile and ~/.bash_profile run first because they have no
        # interactivity guard — installers like ``n`` and ``nvm`` append
        # their PATH export there on most distros, and a non-interactive
        # ``. ~/.profile`` picks that up.
        #
        # ~/.bashrc runs last. On Debian/Ubuntu the default bashrc starts
        # with ``case $- in *i*) ;; *) return;; esac`` and exits early
        # when sourced non-interactively, which is why sourcing bashrc
        # alone misses nvm/n PATH additions placed below that guard. We
        # still include it so users who put PATH logic in bashrc (and
        # stripped the guard, or never had one) keep working.
        candidates.extend(["~/.profile", "~/.bash_profile", "~/.bashrc"])

    resolved: list[str] = []
    for raw in candidates:
        try:
            path = os.path.expandvars(os.path.expanduser(raw))
        except Exception:
            continue
        if path and os.path.isfile(path):
            resolved.append(path)
    return resolved


def _prepend_shell_init(cmd_string: str, files: list[str]) -> str:
    """Prepend ``source <file>`` lines (guarded + silent) to a bash script.

    Each file is wrapped so a failing rc file doesn't abort the whole
    bootstrap: ``set +e`` keeps going on errors, ``2>/dev/null`` hides
    noisy prompts, and ``|| true`` neutralises the exit status.
    """
    if not files:
        return cmd_string

    prelude_parts = ["set +e"]
    for path in files:
        # shlex.quote isn't available here without an import; the files list
        # comes from os.path.expanduser output so it's a concrete absolute
        # path.  Escape single quotes defensively anyway.
        safe = path.replace("'", "'\\''")
        prelude_parts.append(f"[ -r '{safe}' ] && . '{safe}' 2>/dev/null || true")
    prelude = "\n".join(prelude_parts) + "\n"
    return prelude + cmd_string


class LocalEnvironment(BaseEnvironment):
    """Run commands directly on the host machine.

    Spawn-per-call: every execute() spawns a fresh bash process.
    Session snapshot preserves env vars across calls.
    CWD persists via file-based read after each command.
    """

    _winnt_native_local = True

    def __init__(self, cwd: str = "", timeout: int = 60, env: dict = None):
        self._winnt_shell: tuple[str, str] | None = None
        if cwd:
            cwd = os.path.expanduser(cwd)
        super().__init__(cwd=cwd or os.getcwd(), timeout=timeout, env=env)
        self.init_session()

    def _get_windows_shell(self) -> tuple[str, str]:
        if self._winnt_shell is None:
            self._winnt_shell = _find_windows_shell()
        return self._winnt_shell

    def get_temp_dir(self) -> str:
        """Return a shell-safe writable temp dir for local execution.

        Termux does not provide /tmp by default, but exposes a POSIX TMPDIR.
        Prefer POSIX-style env vars when available, keep using /tmp on regular
        Unix systems, and only fall back to tempfile.gettempdir() when it also
        resolves to a POSIX path.

        Check the environment configured for this backend first so callers can
        override the temp root explicitly (for example via terminal.env or a
        custom TMPDIR), then fall back to the host process environment.
        """
        for env_var in ("TMPDIR", "TMP", "TEMP"):
            candidate = self.env.get(env_var) or os.environ.get(env_var)
            if candidate and candidate.startswith("/"):
                return candidate.rstrip("/") or "/"

        if os.path.isdir("/tmp") and os.access("/tmp", os.W_OK | os.X_OK):
            return "/tmp"

        candidate = tempfile.gettempdir()
        if candidate.startswith("/"):
            return candidate.rstrip("/") or "/"

        # Windows: return the system temp dir with forward slashes so both
        # Git Bash and PowerShell can use it in generated wrapper scripts.
        if _IS_WINDOWS:
            return candidate.replace("\\", "/").rstrip("/") or "/tmp"

        return "/tmp"

    def _wrap_command(self, command: str, cwd: str) -> str:
        if os.name != 'nt':
            return super()._wrap_command(command, cwd)

        shell_kind, _shell_path = self._get_windows_shell()
        if shell_kind == "bash":
            return super()._wrap_command(command, cwd)

        escaped_cwd = _normalize_win_literal_path(cwd)
        cwd_file = _normalize_win_literal_path(self._cwd_file)
        marker = self._cwd_marker
        translated_command = _translate_posixish_to_powershell(command)
        return "\n".join([
            "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8",
            "$OutputEncoding = [System.Text.Encoding]::UTF8",
            "$ErrorActionPreference = 'Continue'",
            "$__hermes_ec = 0",
            f"Set-Location -LiteralPath {_ps_quote(escaped_cwd)}",
            "if (-not $?) { exit 126 }",
            translated_command,
            "$__hermes_final_ec = $__hermes_ec",
            "$__hermes_cwd = (Get-Location).ProviderPath",
            f"Set-Content -LiteralPath {_ps_quote(cwd_file)} -Value $__hermes_cwd -Encoding UTF8",
            f"Write-Output \"`n{marker}$($__hermes_cwd){marker}\"",
            "exit $__hermes_final_ec",
        ])

    def _run_bash(self, cmd_string: str, *, login: bool = False,
                  timeout: int = 120,
                  stdin_data: str | None = None) -> subprocess.Popen:
        if os.name != 'nt':
            bash = _find_bash()
            # For login-shell invocations (used by init_session to build the
            # environment snapshot), prepend sources for the user's bashrc /
            # custom init files so tools registered outside bash_profile
            # (nvm, asdf, pyenv, …) end up on PATH in the captured snapshot.
            # Non-login invocations are already sourcing the snapshot and
            # don't need this.
            if login:
                init_files = _resolve_shell_init_files()
                if init_files:
                    cmd_string = _prepend_shell_init(cmd_string, init_files)
            args = [bash, "-l", "-c", cmd_string] if login else [bash, "-c", cmd_string]
            run_env = _make_run_env(self.env)

            proc = subprocess.Popen(
                args,
                text=True,
                env=run_env,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE if stdin_data is not None else subprocess.DEVNULL,
                preexec_fn=None if _IS_WINDOWS else os.setsid,
                cwd=self.cwd,
            )
            try:
                proc._hermes_pgid = os.getpgid(proc.pid)
            except ProcessLookupError:
                pass
        else:
            shell_kind, shell_path = self._get_windows_shell()
            if shell_kind == "bash":
                args = [shell_path, "-c", cmd_string]
            else:
                args = [
                    shell_path,
                    "-NoLogo",
                    "-NoProfile",
                    "-NonInteractive",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    cmd_string,
                ]
            run_env = _make_run_env(self.env)
            cwd = _from_msys_path(self.cwd).replace("\\", "/")
            if not os.path.isdir(cwd):
                cwd = os.getcwd()
            proc = subprocess.Popen(
                args,
                text=True,
                env=run_env,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE if stdin_data is not None else subprocess.DEVNULL,
                cwd=cwd,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )

        if stdin_data is not None:
            _pipe_stdin(proc, stdin_data)

        return proc

    def _kill_process(self, proc):
        """Kill the entire process group (all children)."""

        def _group_alive(pgid: int) -> bool:
            try:
                # POSIX-only: _IS_WINDOWS is handled before this helper is used.
                os.killpg(pgid, 0)
                return True
            except ProcessLookupError:
                return False
            except PermissionError:
                # The group exists, even if this process cannot signal it.
                return True

        def _wait_for_group_exit(pgid: int, timeout: float) -> bool:
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                # Reap the wrapper promptly. A dead but unreaped group leader
                # still makes killpg(pgid, 0) report the group as alive.
                try:
                    proc.poll()
                except Exception:
                    pass
                if not _group_alive(pgid):
                    return True
                time.sleep(0.05)
            try:
                proc.poll()
            except Exception:
                pass
            return not _group_alive(pgid)

        try:
            if _IS_WINDOWS:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    try:
                        proc.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        pass
                if getattr(proc, "returncode", None) is None:
                    try:
                        proc.returncode = -9
                    except Exception:
                        pass
            else:
                try:
                    pgid = os.getpgid(proc.pid)
                except ProcessLookupError:
                    pgid = getattr(proc, "_hermes_pgid", None)
                    if pgid is None:
                        raise

                try:
                    os.killpg(pgid, signal.SIGTERM)
                except ProcessLookupError:
                    return

                # Wait on the process group, not just the shell wrapper. Under
                # load the wrapper can exit before grandchildren do; returning
                # at that point leaves orphaned process-group members behind.
                if _wait_for_group_exit(pgid, 1.0):
                    return

                try:
                    # POSIX-only: _IS_WINDOWS is handled by the outer branch.
                    os.killpg(pgid, signal.SIGKILL)
                except ProcessLookupError:
                    return
                _wait_for_group_exit(pgid, 2.0)
                try:
                    proc.wait(timeout=0.2)
                except (subprocess.TimeoutExpired, OSError):
                    pass
        except (ProcessLookupError, PermissionError, OSError):
            try:
                proc.kill()
            except Exception:
                pass

    def _update_cwd(self, result: dict):
        """Read CWD from temp file (local-only, no round-trip needed)."""
        try:
            with open(self._cwd_file, encoding="utf-8-sig", errors="replace") as f:
                cwd_path = f.read().strip()
            if cwd_path:
                if os.name == 'nt':
                    cwd_path = _from_msys_path(cwd_path).replace("\\", "/")
                self.cwd = cwd_path
        except (OSError, FileNotFoundError):
            pass

        # Still strip the marker from output so it's not visible
        self._extract_cwd_from_output(result)
        if os.name == 'nt' and self.cwd:
            self.cwd = _from_msys_path(self.cwd).replace("\\", "/")

    def cleanup(self):
        """Clean up temp files."""
        for f in (self._snapshot_path, self._cwd_file):
            try:
                os.unlink(f)
            except OSError:
                pass

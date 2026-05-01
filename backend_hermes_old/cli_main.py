"""Hermes Harness CLI — オリジナル Hermes Agent の CLI アーキテクチャに準拠。

HermesCLI クラス:
  - __init__ : 設定読み込み、引数解決
  - run() : TUI 起動 + process_loop
  - chat() : バックグラウンドスレッドでエージェント実行
  - process_command() : スラッシュコマンド処理
  - ステータスバー、スピナー、割り込みキュー対応

新旧対比:
  - agent/           → core/           (エージェントコア)
  - agent/display.py → core/display.py (表示ユーティリティ)
  - hermes_cli/commands.py → hermes_cli/commands.py (そのまま — スラッシュ補完)
  - プロバイダ: Anthropic/OpenRouter/... → Ollama 専用 (OpenAI 互換 API 経由)
  - config.yaml → 環境変数 + 引数 (後で config.yaml サポート追加予定)

依存グラフ:
    base/hermes_constants.py → base/utils.py → tools/registry.py
    → base/model_tools.py → core/run_agent.py → cli_main.py
                                         ↓
                                    tools/*.py（各ツール実装）
"""
__version__ = "0.5.1"

import json
import logging
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from prompt_toolkit import Application
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.filters import Condition
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, HSplit, Window, FormattedTextControl, ConditionalContainer
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.layout.processors import Processor, Transformation
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.styles import Style as PTStyle
from prompt_toolkit.utils import get_cwidth
from prompt_toolkit.widgets import TextArea
try:
    from prompt_toolkit.cursor_shapes import CursorShape
    _STEADY_CURSOR = CursorShape.BLOCK
except (ImportError, AttributeError):
    _STEADY_CURSOR = None

from core.run_agent import AIAgent
from base.hermes_constants import get_hermes_home
from base.hermes_logging import setup_logging
from base.model_tools import get_all_tool_names, get_toolset_for_tool
from hermes_cli.commands import SlashCommandCompleter, SlashCommandAutoSuggest, resolve_command

logger = logging.getLogger(__name__)


def _configure_pipe_encoding() -> None:
    """AiDiy などのパイプ受信時はUTF-8で罫線文字を渡す。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            if hasattr(stream, "reconfigure") and not stream.isatty():
                stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


_configure_pipe_encoding()

# ─── AiDiy 設定 ───────────────────────────────────────────────────

_AIDIY_KEY_JSON = Path(__file__).resolve().parent.parent / "backend_server" / "_config" / "AiDiy_key.json"
_DEFAULT_OLLAMA_HOST = "http://localhost:11434"
_OLLAMA_CLOUD_BASE_URL = "https://ollama.com/v1"
_OLLAMA_CLOUD_SUFFIXES = (":cloud", ":clude")
_CLOUD_MODEL_MAX_AGE_DAYS = 240
_OPENAI_BASE_URL = "https://api.openai.com/v1"
_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
_GEMINI_OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
_CLAUDE_BASE_URL = "https://api.anthropic.com"

# シェル (subprocess) プロバイダー定義
_SHELL_CLI_PROVIDERS: Dict[str, Dict] = {
    "claude_cli":  {"name": "Claude Code CLI",      "default_model": "auto"},
    "codex_cli":   {"name": "Codex CLI (OpenAI)",   "default_model": "auto"},
    "gemini_cli":  {"name": "Gemini CLI",            "default_model": "auto"},
    "copilot_cli": {"name": "GitHub Copilot CLI",   "default_model": "auto"},
}


def _is_cloud_key(api_key: str) -> bool:
    """Ollama Cloud 用 API キーが設定されているか判定する。"""
    return isinstance(api_key, str) and bool(api_key.strip()) and not api_key.strip().startswith("<")


def _is_valid_key(api_key: str) -> bool:
    """AiDiy_key.json のプレースホルダーでない API キーか判定する。"""
    return isinstance(api_key, str) and bool(api_key.strip()) and not api_key.strip().startswith("<")


def _strip_cloud_suffix(model: str) -> str:
    """Ollama Cloud 直叩き時にローカル転送用サフィックスを外す。"""
    if not isinstance(model, str):
        return model
    name = model.strip()
    lower = name.lower()
    for suffix in _OLLAMA_CLOUD_SUFFIXES:
        if lower.endswith(suffix):
            return name[: -len(suffix)]
    return name


def _model_from_display_label(label: str) -> str:
    """`YYYY/MM/DD - model` 形式の表示ラベルからモデル ID だけを取り出す。"""
    text = (label or "").strip()
    if len(text) >= 13 and text[4:5] == "/" and text[7:8] == "/" and text[10:13] == " - ":
        return text[13:].strip()
    return text


def _load_aidiy_config() -> dict:
    """backend_server/_config/AiDiy_key.json を読み込む。見つからなければ空 dict。"""
    try:
        if _AIDIY_KEY_JSON.exists():
            with open(_AIDIY_KEY_JSON, "r", encoding="utf-8-sig") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _parse_date_to_timestamp(value: Any) -> int:
    """created / created_at を新しい順ソート用 timestamp に寄せる。"""
    if not value:
        return 0
    try:
        return int(float(value))
    except Exception:
        pass
    try:
        text = str(value).strip().replace("Z", "+00:00")
        return int(datetime.fromisoformat(text).timestamp())
    except Exception:
        return 0


def _strip_leaked_bracketed_paste_wrappers(text: str) -> str:
    """旧版互換: 端末から漏れた bracketed paste 制御列を取り除く。"""
    if not isinstance(text, str):
        return text
    return text.replace("\x1b[200~", "").replace("\x1b[201~", "")


def _strip_leaked_terminal_responses(text: str) -> str:
    """旧版互換: 貼り付けや focus 復帰時に混ざる端末応答を軽く除去する。"""
    if not isinstance(text, str):
        return text
    # CSI sequence のうち、入力欄に混ざると command 判定を壊しやすいものだけ除く。
    import re
    return re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text)


def _looks_like_slash_command(text: str) -> bool:
    """旧版互換: 入力が slash command として扱えるか判定する。"""
    if not isinstance(text, str):
        return False
    cleaned = _strip_leaked_terminal_responses(
        _strip_leaked_bracketed_paste_wrappers(text)
    ).strip()
    return bool(cleaned.startswith("/") and len(cleaned) >= 1)


def _fits_output_encoding(text: str) -> bool:
    """現在の stdout encoding で安全に出力できるか判定する。"""
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        (text or "").encode(encoding)
        return True
    except Exception:
        return False


# ─── スタイル定数 ─────────────────────────────────────────────────

_DIM = "\033[2m"
_ACCENT = "\033[34m"
_RST = "\033[0m"
_RED = "\033[31m"
_GREEN = "\033[32m"
_BOLD = "\033[1m"
_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")

_AIDIY_HERMES_LOGO = rf"""{_ACCENT}{'=' * 40}{_RST}
        _    _ ____  _
       / \  (_)  _ \(_) _   _
      / _ \ | | | | | || | | |     AiDiy
     / ___ \| | |_| | || |_| |    Hermes
    /_/   \_\_|____/|_| \__, |
                         |___/
{_ACCENT}{'=' * 40}{_RST}"""


def _cprint(text: str = "") -> None:
    """シンプルな出力（TUI 内外問わず安全）。"""
    try:
        if not _supports_ansi_color():
            text = _strip_ansi(text)
        print(text, flush=True)
    except Exception:
        pass


def _eprint(text: str = "") -> None:
    """stderr へ進捗履歴を出す。ANSI は混ぜない。"""
    try:
        line = _strip_ansi(text or "")
        if _should_skip_progress_stderr(line):
            return
        sys.stderr.write(line + "\n")
        sys.stderr.flush()
    except Exception:
        pass


def _stdout_is_tty() -> bool:
    try:
        return bool(sys.stdout.isatty())
    except Exception:
        return False


def _strip_ansi(text: str) -> str:
    """ANSIエスケープを、未対応の表示面へ出す前に除去する。"""
    return _ANSI_RE.sub("", text or "")


def _should_skip_progress_stderr(text: str) -> bool:
    """進捗stderrから不要なロゴ/バージョン行を除外する。"""
    s = (text or "").strip()
    if not s:
        return True

    lower = s.lower()
    if lower.startswith("aidiy_hermes v"):
        return True

    logo_prefixes = (
        "========================================",
        "_    _ ____  _",
        "/ \\  (_)  _ \\(_)",
        "/ _ \\ | | | | | |",
        "/ ___ \\| | |_| | |",
        "/_/   \\_\\_|____/|_|",
        "|___/",
    )
    return any(s.startswith(p) for p in logo_prefixes)


def _supports_ansi_color() -> bool:
    """ANSIカラーを安全に出せる端末か判定する。"""
    if os.environ.get("NO_COLOR") is not None:
        return False
    if os.environ.get("HERMES_NO_COLOR") is not None:
        return False
    if os.environ.get("AIDIY_NO_COLOR") is not None:
        return False
    if os.environ.get("FORCE_COLOR") or os.environ.get("CLICOLOR_FORCE"):
        return True
    if not _stdout_is_tty():
        return False

    term = (os.environ.get("TERM") or "").lower()
    if term == "dumb":
        return False

    if os.name == "nt":
        # Windows 10+ は SetConsoleMode で VT処理を有効化できる
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            mode = ctypes.c_ulong()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                new_mode = mode.value | 0x0004  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
                if kernel32.SetConsoleMode(handle, new_mode):
                    return True
        except Exception:
            pass
        # VT有効化できなかった場合は既知ターミナル変数で判定
        return bool(
            os.environ.get("WT_SESSION") or
            os.environ.get("ANSICON") or
            os.environ.get("ConEmuANSI", "").upper() == "ON" or
            os.environ.get("TERM_PROGRAM") or
            any(t in term for t in ("xterm", "ansi", "vt100", "screen"))
        )

    return bool(term) and term != "dumb"


def _color_for_tty(text: str, color: str) -> str:
    """通常ターミナルだけANSI色を付け、AiDiyパイプ表示では文字化けを避ける。"""
    if not text:
        return text
    if not _supports_ansi_color():
        return _strip_ansi(text)
    return f"{color}{text}{_RST}"


class HermesCLI:
    """Hermes Agent 対話型 CLI。

    オリジナルの HermesCLI (cli.py の HermesCLI クラス) と同じ設計:
    - バックグラウンドスレッドでエージェント実行
    - 割り込みキューによる実行中入力
    - process_loop による非同期入力処理
    - スピナー + ステータスバー
    - スラッシュ補完 (SlashCommandCompleter)
    """

    # ── __init__ ───────────────────────────────────────────────────

    def __init__(
        self,
        model: str = None,
        toolsets: List[str] = None,
        api_key: str = None,
        base_url: str = None,
        max_turns: int = None,
        verbose: bool = False,
        compact: bool = False,
        provider: str = "ollama",
        api_mode: str = "chat_completions",
    ):
        self.verbose = verbose
        self.compact = compact
        self._aidiy_config = _load_aidiy_config()

        # モデル設定
        self.model = model or os.environ.get("OLLAMA_MODEL", "deepseek-v4-flash:cloud")

        # API 設定
        self.provider = (provider or "ollama").strip().lower()
        self.api_mode = (api_mode or "chat_completions").strip().lower()
        self.base_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        self.api_key = api_key or "ollama"

        # シェル (subprocess) プロバイダー用セッション状態
        self.shell_session_started: bool = False
        self.shell_codex_session_id: Optional[str] = None
        self.max_turns = max_turns or 99

        # ツールセット
        self.enabled_toolsets = toolsets or ["aidiy-hermes"]

        # エージェント（遅延初期化）
        self.agent: Optional[AIAgent] = None

        # 会話履歴
        self.conversation_history: List[Dict] = []
        self._last_user_message: Optional[str] = None
        self._last_assistant_response: Optional[str] = None
        self._turn_log: List[Dict[str, str]] = []

        # セッション情報
        self._session_start = datetime.now()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 履歴ファイル (旧版に合わせる)
        self._history_file = get_hermes_home() / ".hermes_history"

        # ── 非同期実行状態 ──
        self._agent_running = False
        self._spinner_text = ""
        self._tool_start_time = 0.0
        self._current_step = 0
        self._current_step_max = self.max_turns
        self._spinner_idx = 0
        self._last_invalidate = 0.0
        self._last_ctrl_c_time = 0.0
        self._status_bar_visible = True
        self._command_running = False
        self._command_status = ""

        # キュー (旧版と同じ)
        self._pending_input = queue.Queue()     # アイドル時の入力
        self._interrupt_queue = queue.Queue()   # エージェント実行中の割り込み
        self._should_exit = False
        self._model_picker_state: Optional[Dict[str, Any]] = None

        # prompt_toolkit Application 参照
        self._app: Optional[Application] = None

        # TUI スタイルベース (旧版互換)
        self._tui_style_base = {
            "input-area": "#FFF8DC",
            "placeholder": "#555555 italic",
            "prompt": "#FFF8DC",
            "prompt-working": "#888888 italic",
            "hint": "#00BFFF italic",
            "status-bar": "bg:#1a1a2e #C0C0C0",
            "status-bar-strong": "bg:#1a1a2e #FFD700 bold",
            "status-bar-dim": "bg:#1a1a2e #8B8682",
            "status-bar-good": "bg:#1a1a2e #8FBC8F bold",
            "status-bar-warn": "bg:#1a1a2e #FFD700 bold",
            "status-bar-bad": "bg:#1a1a2e #FF8C00 bold",
            "status-bar-critical": "bg:#1a1a2e #FF6B6B bold",
            "input-rule": "#FFFFFF",
            "image-badge": "#87CEEB bold",
            "completion-menu": "bg:#1a1a2e #FFF8DC",
            "completion-menu.completion": "bg:#1a1a2e #FFF8DC",
            "completion-menu.completion.current": "bg:#333355 #FFD700",
            "completion-menu.meta.completion": "bg:#1a1a2e #888888",
            "completion-menu.meta.completion.current": "bg:#333355 #FFBF00",
            "clarify-border": "#CD7F32",
            "clarify-title": "#FFD700 bold",
            "clarify-question": "#FFF8DC bold",
            "clarify-choice": "#AAAAAA",
            "clarify-selected": "#FFD700 bold",
            "clarify-active-other": "#FFD700 italic",
            "clarify-countdown": "#CD7F32",
            "sudo-prompt": "#FF6B6B bold",
            "sudo-border": "#CD7F32",
            "sudo-title": "#FF6B6B bold",
            "sudo-text": "#FFF8DC",
            "approval-border": "#CD7F32",
            "approval-title": "#FF8C00 bold",
            "approval-desc": "#FFF8DC bold",
            "approval-cmd": "#AAAAAA italic",
            "approval-choice": "#AAAAAA",
            "approval-selected": "#FFD700 bold",
            "voice-prompt": "#87CEEB",
            "voice-recording": "#FF4444 bold",
            "voice-processing": "#FFA500 italic",
            "voice-status": "bg:#1a1a2e #87CEEB",
            "voice-status-recording": "bg:#1a1a2e #FF4444 bold",
        }

    # ── エージェント初期化 ──────────────────────────────────────────

    _SUPPORTED_COMMANDS = {
        "clear",
        "commands",
        "config",
        "copy",
        "exit",
        "help",
        "history",
        "model",
        "new",
        "profile",
        "quit",
        "redraw",
        "retry",
        "save",
        "status",
        "tools",
        "toolsets",
        "undo",
    }

    def _command_available(self, slash_command: str) -> bool:
        base_word = (slash_command or "").strip().split()[0].lower().lstrip("/")
        if base_word == "q":
            return True
        cmd_def = resolve_command(base_word)
        canonical = cmd_def.name if cmd_def else base_word
        return canonical in self._SUPPORTED_COMMANDS

    def _on_agent_thinking(self, text: str) -> None:
        """エージェントの現在ステップを TUI spinner 行へ反映する。"""
        if text:
            self._update_spinner_text(text)
            _eprint(text)
        else:
            self._stop_spinner()

    def _on_agent_step(self, step: int, _previous_tools: Optional[List[str]] = None) -> None:
        """旧版互換のステップ進捗表示。"""
        self._current_step = max(0, int(step or 0))
        self._current_step_max = self.max_turns
        line = f"Step {self._current_step}/{self._current_step_max}: モデル呼び出し中"
        self._update_spinner_text(line)
        _eprint(f"[step] {self._current_step}")

    def _on_tool_progress(
        self,
        event_type: str,
        function_name: str = None,
        preview: str = None,
        function_args: dict = None,
        **kwargs,
    ) -> None:
        """ツール実行中のステップ表示を更新する。"""
        step = int(kwargs.get("step") or self._current_step or 0)
        max_steps = int(kwargs.get("max_steps") or self._current_step_max or self.max_turns)
        self._current_step = step
        self._current_step_max = max_steps
        name = function_name or "tool"
        if event_type == "tool.started":
            detail = f"{name}"
            if preview:
                detail += f" {preview}"
            self._update_spinner_text(f"Step {step}/{max_steps}: ツール実行中 {detail}")
            _eprint(f"[tool] {name} ... {preview or ''}".rstrip())
            return
        if event_type == "tool.completed":
            self._spinner_text = f"Step {step}/{max_steps}: ツール完了 {name}"
            self._tool_start_time = 0.0
            duration = kwargs.get("duration")
            if isinstance(duration, (int, float)):
                suffix = f" ({duration:.1f}s)"
            else:
                suffix = ""
            _eprint(f"done Step {step}/{max_steps}: {name}{suffix}")
            self._invalidate(min_interval=0)

    def _init_agent(self) -> bool:
        if self.agent is not None:
            return True
        try:
            self.agent = AIAgent(
                base_url=self.base_url,
                api_key=self.api_key,
                model=self.model,
                max_iterations=self.max_turns,
                enabled_toolsets=self.enabled_toolsets,
                provider=self.provider,
                api_mode=self.api_mode,
                session_id=self.session_id,
                platform="cli",
                thinking_callback=self._on_agent_thinking,
                step_callback=self._on_agent_step,
                tool_progress_callback=self._on_tool_progress,
            )
            return True
        except Exception as e:
            _cprint(f"  {_RED}ERROR: エージェント初期化エラー: {e}{_RST}")
            return False

    def _reset_agent(self) -> None:
        """次回ターンで現在設定を反映した AIAgent を作り直す。"""
        self.agent = None

    def _new_session(self) -> None:
        """会話履歴と実行状態を捨て、新しいセッション ID を採番する。"""
        self.conversation_history.clear()
        self._last_user_message = None
        self._last_assistant_response = None
        self._turn_log.clear()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._session_start = datetime.now()
        self._spinner_text = ""
        self._tool_start_time = 0.0
        self.shell_session_started = False
        self.shell_codex_session_id = None
        self._reset_agent()

    # ── ステータスバー (旧版互換) ────────────────────────────────────

    def _status_bar_context_style(self, percent_used: Optional[int]) -> str:
        """旧版互換: context 使用率に応じた status bar style を返す。"""
        if percent_used is None:
            return "class:status-bar-dim"
        if percent_used >= 95:
            return "class:status-bar-critical"
        if percent_used > 80:
            return "class:status-bar-bad"
        if percent_used >= 50:
            return "class:status-bar-warn"
        return "class:status-bar-good"

    def _build_context_bar(self, percent_used: Optional[int], width: int = 10) -> str:
        """旧版互換: context 使用率バーを返す。"""
        safe_percent = max(0, min(100, percent_used or 0))
        filled = round((safe_percent / 100) * width)
        return f"[{('#' * filled) + ('-' * max(0, width - filled))}]"

    def _status_bar_snapshot(self) -> Dict[str, Any]:
        model = self.model or "unknown"
        short = model.split("/")[-1] if "/" in model else model
        if len(short) > 24:
            short = f"{short[:21]}..."
        secs = max(0.0, (datetime.now() - self._session_start).total_seconds())
        m = int(secs // 60)
        s = int(secs % 60)
        dur = f"{m}m {s}s" if m else f"{s}s"
        provider = self.provider or "provider"
        return {
            "model": short,
            "model_short": short,
            "model_name": model,
            "provider": provider,
            "duration": dur,
            "context_tokens": 0,
            "context_length": None,
            "context_percent": None,
            "prompt_elapsed": "",
        }

    def _get_status_bar_snapshot(self) -> Dict[str, Any]:
        """旧版メソッド名互換。"""
        return self._status_bar_snapshot()

    @staticmethod
    def _status_bar_display_width(text: str) -> int:
        try:
            return get_cwidth(text or "")
        except Exception:
            return len(text or "")

    @staticmethod
    def _trim_status_bar_text(text: str, mw: int) -> str:
        if mw <= 0:
            return ""
        if HermesCLI._status_bar_display_width(text) <= mw:
            return text
        el = "..."
        ew = HermesCLI._status_bar_display_width(el)
        if mw <= ew:
            return el[:mw]
        out, w = [], 0
        for ch in text:
            cw = get_cwidth(ch)
            if w + cw + ew > mw:
                break
            out.append(ch)
            w += cw
        return "".join(out).rstrip() + el

    def _get_tui_prompt_symbols(self) -> tuple[str, str]:
        """旧版互換: 通常プロンプトと状態表示用 suffix を返す。"""
        try:
            from hermes_cli.skin_engine import get_active_prompt_symbol
            symbol = get_active_prompt_symbol("❯ ")
        except Exception:
            symbol = "❯ "

        symbol = (symbol or "❯ ").rstrip() + " "
        if not _fits_output_encoding(symbol):
            symbol = ">>> "
        stripped = symbol.rstrip()
        if not stripped:
            return ">>> ", ">>> "

        parts = stripped.split()
        candidate = parts[-1] if parts else ""
        arrow_chars = ("❯", ">", "$", "#", "›", "»", "→")
        if any(ch in candidate for ch in arrow_chars):
            return symbol, candidate.rstrip() + " "
        return symbol, symbol

    def _get_tui_prompt_fragments(self):
        """プロンプト断片を返す (旧版互換)。"""
        symbol, state_suffix = self._get_tui_prompt_symbols()
        compact = self._use_minimal_tui_chrome(width=self._get_tui_terminal_width())

        def _state_fragment(style: str, icon: str):
            if compact:
                return [(style, icon + " ")]
            return [(style, f"{icon} {state_suffix}")]

        if self._command_running:
            return _state_fragment("class:prompt-working", self._command_spinner_frame())
        if self._agent_running:
            return _state_fragment("class:prompt-working", "H")
        return [("class:prompt", symbol)]

    def _get_tui_prompt_text(self) -> str:
        """プロンプト表示テキストを返す (旧版互換)。"""
        return "".join(text for _, text in self._get_tui_prompt_fragments())

    def _command_spinner_frame(self) -> str:
        """旧版互換: slash command 実行中の軽量スピナー。"""
        frames = self._spinner_frames()
        frame_idx = int(time.monotonic() * 10) % len(frames)
        return frames[frame_idx]

    def _get_terminal_width(self) -> int:
        try:
            if self._app:
                return self._app.output.get_size().columns
        except Exception:
            pass
        try:
            return shutil.get_terminal_size().columns
        except Exception:
            return 80

    def _invalidate(self, min_interval: float = 0) -> None:
        now = time.monotonic()
        if self._app and (now - self._last_invalidate) >= min_interval:
            self._last_invalidate = now
            try:
                self._app.invalidate()
            except Exception:
                pass

    def _force_full_redraw(self) -> None:
        """旧版同様、prompt_toolkit の描画キャッシュごと画面を再描画する。"""
        app = getattr(self, "_app", None)
        if not app:
            return
        try:
            renderer = app.renderer
            out = renderer.output
            out.reset_attributes()
            out.erase_screen()
            out.cursor_goto(0, 0)
            out.flush()
            renderer.reset(leave_alternate_screen=False)
        except Exception:
            pass
        self._invalidate(min_interval=0)

    def _get_tui_terminal_width(self) -> int:
        return self._get_terminal_width()

    def _use_minimal_tui_chrome(self, width: Optional[int] = None) -> bool:
        if width is None:
            width = self._get_tui_terminal_width()
        return width < 64

    def _tui_input_rule_height(self, position: str, width: Optional[int] = None) -> int:
        if position not in {"top", "bottom"}:
            raise ValueError(f"Unknown input rule position: {position}")
        if position == "top":
            return 1
        return 0 if self._use_minimal_tui_chrome(width=width) else 1

    def _agent_spacer_height(self, width: Optional[int] = None) -> int:
        if not self._agent_running:
            return 0
        return 0 if self._use_minimal_tui_chrome(width=width) else 1

    def _spinner_widget_height(self, width: Optional[int] = None) -> int:
        spinner_line = self._render_spinner_text()
        if not spinner_line or self._use_minimal_tui_chrome(width=width):
            return 0
        width = width or self._get_tui_terminal_width()
        if width and width > 10:
            import math
            return max(1, math.ceil(self._status_bar_display_width(spinner_line) / width))
        return 1

    def _get_status_bar_fragments(self):
        try:
            s = self._status_bar_snapshot()
            w = self._get_terminal_width()
            if w < 52:
                frags = [
                    ("class:status-bar", " H "),
                    ("class:status-bar-dim", s["provider"]),
                    ("class:status-bar-dim", "/"),
                    ("class:status-bar-strong", s["model"]),
                    ("class:status-bar-dim", " · "),
                    ("class:status-bar-dim", s["duration"]),
                    ("class:status-bar", " "),
                ]
            else:
                frags = [
                    ("class:status-bar", " H "),
                    ("class:status-bar-dim", s["provider"]),
                    ("class:status-bar-dim", "/"),
                    ("class:status-bar-strong", s["model"]),
                    ("class:status-bar-dim", " │ "),
                    ("class:status-bar-dim", s["duration"]),
                    ("class:status-bar", " "),
                ]
            tw = sum(self._status_bar_display_width(t) for _, t in frags)
            if tw > w:
                return [("class:status-bar", self._trim_status_bar_text("".join(t for _, t in frags), w))]
            return frags
        except Exception:
            return [("class:status-bar", " Hermes Harness ")]

    def _build_tui_style_dict(self) -> dict[str, str]:
        """旧版同様、基本色にアクティブスキンの色上書きを重ねる。"""
        style_dict = dict(getattr(self, "_tui_style_base", {}) or {})
        try:
            from hermes_cli.skin_engine import get_prompt_toolkit_style_overrides
            style_dict.update(get_prompt_toolkit_style_overrides())
        except Exception:
            pass
        style_dict["input-rule"] = "#FFFFFF"
        style_dict["hint"] = "#00BFFF italic"
        return style_dict

    def _apply_tui_skin_style(self) -> bool:
        """実行中 TUI のスキン色を再適用する旧版互換フック。"""
        if not getattr(self, "_app", None) or not getattr(self, "_tui_style_base", None):
            return False
        self._app.style = PTStyle.from_dict(self._build_tui_style_dict())
        self._invalidate(min_interval=0.0)
        return True

    def _get_extra_tui_widgets(self) -> list:
        return []

    def _register_extra_tui_keybindings(self, kb, *, input_area) -> None:
        """派生 CLI 用の拡張ポイント。AiDiy 版では何もしない。"""

    def _build_tui_layout_children(
        self,
        *,
        model_picker_widget=None,
        spinner_widget=None,
        spacer,
        status_bar,
        input_rule_top,
        input_area,
        input_rule_bot,
        completions_menu,
    ) -> list:
        """旧版と同じ順序で、下部固定 TUI 部品だけを並べる。"""
        return [
            item for item in [
                Window(height=0),
                model_picker_widget,
                spinner_widget,
                spacer,
                *self._get_extra_tui_widgets(),
                status_bar,
                input_rule_top,
                input_area,
                input_rule_bot,
                completions_menu,
            ] if item is not None
        ]

    @staticmethod
    def _compute_model_picker_viewport(
        selected: int,
        scroll_offset: int,
        n: int,
        term_rows: int,
        reserved_below: int = 6,
        panel_chrome: int = 6,
        min_visible: int = 3,
    ) -> tuple[int, int]:
        max_visible = max(min_visible, term_rows - reserved_below - panel_chrome)
        if n <= max_visible:
            return 0, n
        visible = max_visible
        if selected < scroll_offset:
            scroll_offset = selected
        elif selected >= scroll_offset + visible:
            scroll_offset = selected - visible + 1
        scroll_offset = max(0, min(scroll_offset, n - visible))
        return scroll_offset, visible

    # ── スピナー (旧版互換) ──────────────────────────────────────────
    _BRAILLE_SPINNER_FRAMES = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")
    _ASCII_SPINNER_FRAMES = ("|", "/", "-", "\\")

    def _spinner_frames(self) -> tuple[str, ...]:
        """旧版の点滅を優先しつつ、Windows 端末の文字化けを避ける。"""
        if all(_fits_output_encoding(frame) for frame in self._BRAILLE_SPINNER_FRAMES):
            return self._BRAILLE_SPINNER_FRAMES
        return self._ASCII_SPINNER_FRAMES

    def _start_spinner(self, text: str) -> None:
        self._spinner_text = text
        self._spinner_idx = 0
        self._tool_start_time = 0.0
        self._invalidate(min_interval=0)

    def _update_spinner_text(self, text: str) -> None:
        self._spinner_text = text
        self._tool_start_time = time.monotonic()
        self._invalidate(min_interval=0)

    def _stop_spinner(self) -> None:
        self._spinner_text = ""
        self._tool_start_time = 0.0

    def _render_spinner_text(self) -> str:
        txt = getattr(self, "_spinner_text", "")
        if not txt:
            return ""
        t0 = getattr(self, "_tool_start_time", 0) or 0
        if t0 > 0:
            elapsed = time.monotonic() - t0
            if elapsed >= 60:
                minutes, seconds = int(elapsed // 60), int(elapsed % 60)
                elapsed_str = f"{minutes}m {seconds}s"
            else:
                elapsed_str = f"{elapsed:.1f}s"
            return f"  {txt}  ({elapsed_str})"
        return f"  {txt}"

    def _terminal_rule(self, *, label: str = "", width: Optional[int] = None) -> str:
        """AiDiy表示へ流しても崩れない、ANSIなしの横罫線を返す。"""
        w = max(20, min(80, (width or self._get_terminal_width()) - 2))
        rule_char = "─" if _fits_output_encoding("─") else "-"
        clean_label = (label or "").strip()
        if clean_label:
            text = f"{rule_char * 2} {clean_label} "
            line = text + (rule_char * max(w - len(text), 0))
        else:
            line = rule_char * w
        return line

    def _print_user_message(self, message: str) -> None:
        """入力後にスクロールバックへ残るユーザー入力を表示する。"""
        print(self._terminal_rule(label="User"))
        for line in (message or "").split("\n"):
            print(f"  {line}")
        print(self._terminal_rule())

    def _print_cpu_output(self, response: str) -> None:
        """AiDiy応答を緑色で線に挟んで表示する。"""
        print()
        print(self._terminal_rule(label="AiDiy"))
        for line in (response or "").split("\n"):
            print(f"  {line}")
        print(self._terminal_rule())
        print()

    # ── シェル (subprocess) プロバイダー ────────────────────────────

    def _is_shell_provider(self) -> bool:
        return self.provider in _SHELL_CLI_PROVIDERS

    def _shell_cmd_path(self) -> str:
        """現在の shell プロバイダーの CLI コマンドパスを返す。"""
        provider = self.provider
        custom = os.environ.get(f"{provider.upper()}_CLI_PATH")
        if custom:
            return custom
        if os.name == "nt":
            userprofile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
            npm_bin = os.path.join(userprofile, "AppData", "Roaming", "npm")
            _win = {
                "claude_cli": "claude.cmd",
                "codex_cli": "codex.cmd",
                "gemini_cli": "gemini.cmd",
                "copilot_cli": "copilot.cmd",
            }
            return os.path.join(npm_bin, _win.get(provider, f"{provider}.cmd"))
        _unix = {
            "claude_cli": "claude",
            "codex_cli": "codex",
            "gemini_cli": "gemini",
            "copilot_cli": "copilot",
        }
        return _unix.get(provider, provider)

    def _shell_build_command(self, prompt: str, first_turn: bool) -> List[str]:
        """シェルプロバイダー別にコマンド配列を構築する。"""
        provider = self.provider
        model = self.model or "auto"
        use_model = model.lower() not in ("auto", "", "none")
        cmd = self._shell_cmd_path()

        if provider == "claude_cli":
            args = [cmd, "--allow-dangerously-skip-permissions",
                    "--permission-mode", "bypassPermissions"]
            if use_model:
                args += ["--model", model]
            args += (["-p", prompt] if first_turn else ["--continue", "-p", prompt])
            return args

        if provider == "codex_cli":
            args = [cmd, "exec", "--skip-git-repo-check",
                    "--dangerously-bypass-approvals-and-sandbox"]
            if use_model:
                args += ["--model", model]
            if not first_turn and self.shell_codex_session_id:
                args += ["resume", self.shell_codex_session_id]
            args.append(prompt)
            return args

        if provider == "gemini_cli":
            args = [cmd, "--yolo"]
            if use_model:
                args += ["--model", model]
            args += ["--prompt", prompt]
            return args

        if provider == "copilot_cli":
            args = [cmd, "--allow-all-tools"]
            if use_model:
                args += ["--model", model]
            args += (["-p", prompt] if first_turn else ["--continue", "-p", prompt])
            return args

        return [cmd, prompt]

    def _chat_shell(self, message: str) -> None:
        """シェル (subprocess) プロバイダーでメッセージを処理する。"""
        first_turn = not self.shell_session_started
        req = message.strip()
        _eprint(
            f"[start] provider={self.provider} model={self.model} tools={len(self.enabled_toolsets or []) if self.enabled_toolsets else 'all'}"
        )

        # プロンプト構築: 初回はシステムプロンプトなし (CLI が自身で管理)
        if first_turn:
            prompt_raw = f"【今回の依頼】\n{req}\n"
        else:
            hist_parts: List[str] = []
            for turn in self._turn_log[-3:]:
                hist_parts.append(f"```user\n{turn['user']}\n```")
                hist_parts.append(f"```agent\n{turn['assistant']}\n```")
            hist_str = "\n".join(hist_parts)
            prompt_raw = (
                f"【過去の会話】\n{hist_str}\n\n【今回の依頼】\n{req}\n"
                if hist_str else f"【今回の依頼】\n{req}\n"
            )

        # CLI へは 1 行で渡す
        prompt_cli = prompt_raw.replace("\n", " ").replace("\r", " ").strip()
        command = self._shell_build_command(prompt_cli, first_turn)
        cwd = str(Path.cwd())

        self._start_spinner(f"shell/{self.provider}: 実行中...")
        self._last_user_message = message

        result_lines: List[str] = []
        stderr_lines: List[str] = []
        completed = threading.Event()

        def run_shell() -> None:
            try:
                env = os.environ.copy()
                env.update({"NO_COLOR": "1", "FORCE_COLOR": "0",
                             "CLICOLOR": "0", "TERM": "dumb"})
                proc = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=cwd,
                    env=env,
                )

                def _read_stdout() -> None:
                    print()
                    print(self._terminal_rule(label=f"AiDiy [{self.provider}]"))
                    for raw in proc.stdout:
                        line = _strip_ansi(raw.decode("utf-8", errors="replace").rstrip())
                        if line:
                            result_lines.append(line)
                            try:
                                print(f"  {line}")
                            except Exception:
                                pass
                    print(self._terminal_rule())
                    print()

                def _read_stderr() -> None:
                    for raw in proc.stderr:
                        line = _strip_ansi(raw.decode("utf-8", errors="replace").rstrip())
                        if line:
                            stderr_lines.append(line)

                t_out = threading.Thread(target=_read_stdout, daemon=True)
                t_err = threading.Thread(target=_read_stderr, daemon=True)
                t_out.start()
                t_err.start()
                proc.wait()
                t_out.join(timeout=5)
                t_err.join(timeout=5)
            except FileNotFoundError:
                msg = f"ERROR: コマンドが見つかりません: {command[0]}"
                result_lines.append(msg)
                _cprint(f"  {_RED}{msg}{_RST}")
            except Exception as exc:
                msg = f"ERROR: {exc}"
                result_lines.append(msg)
                _cprint(f"  {_RED}{msg}{_RST}")
            finally:
                completed.set()

        shell_thread = threading.Thread(target=run_shell, daemon=True,
                                        name=f"shell-{self.session_id}")
        shell_thread.start()

        while not completed.wait(timeout=0.1):
            try:
                interrupt_msg = self._interrupt_queue.get_nowait()
                if interrupt_msg:
                    _cprint("\n[interrupt] shell プロセスを中断します...")
                    break
            except queue.Empty:
                self._invalidate(min_interval=0.12)

        shell_thread.join(timeout=10)
        self._stop_spinner()

        self.shell_session_started = True

        if self.provider == "codex_cli" and stderr_lines:
            m = re.search(r"session id:\s*([a-f0-9\-]+)",
                          "\n".join(stderr_lines), re.IGNORECASE)
            if m:
                self.shell_codex_session_id = m.group(1)

        response = "\n".join(result_lines).strip()
        if response:
            self._last_assistant_response = response
            self._turn_log.append({
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "user": message,
                "assistant": response,
            })
            self._turn_log = self._turn_log[-80:]
            _eprint(f"[done] provider={self.provider} interrupted=False error=False")
        else:
            _cprint(f"  {_RED}WARNING: shell 応答が空です{_RST}")
            _eprint(f"[done] provider={self.provider} interrupted=False error=True")

    # ── エージェント実行 (旧版 chat() 互換) ─────────────────────────

    def chat(self, message: str, images: List[Path] = None) -> None:
        """ユーザーメッセージを処理し、エージェントをバックグラウンドで実行する。

        旧版と同様:
        - エージェントは別スレッドで実行される
        - メインスレッドは interrupt_queue を監視し割り込みを処理
        """
        if self._is_shell_provider():
            self._chat_shell(message)
            return

        if not self._init_agent():
            _cprint(f"  {_RED}ERROR: エージェントを初期化できません{_RST}")
            return

        self._last_user_message = message
        self._start_spinner(f"Step 0/{self.max_turns}: 準備中")
        _eprint(
            f"[start] provider={self.provider} model={self.model} tools={len(self.enabled_toolsets or []) if self.enabled_toolsets else 'all'}"
        )

        agent_thread = None
        result = None

        def run_agent():
            nonlocal result
            try:
                result = self.agent.run_conversation(
                    user_message=message,
                    conversation_history=self.conversation_history,
                )
            except Exception as exc:
                logging.error("run_conversation raised: %s", exc, exc_info=True)
                result = {
                    "final_response": f"Error: {exc}",
                    "messages": [],
                    "api_calls": 0,
                    "failed": True,
                    "error": str(exc),
                }

        # エージェントをバックグラウンドスレッドで起動
        agent_thread = threading.Thread(target=run_agent, daemon=True,
                                        name=f"agent-{self.session_id}")
        agent_thread.start()

        # interrupt_queue を監視しながらエージェント完了を待つ
        interrupt_msg = None
        while agent_thread.is_alive():
            try:
                interrupt_msg = self._interrupt_queue.get(timeout=0.1)
                if interrupt_msg:
                    _cprint("\n[interrupt] 中断リクエストを送信...")
                    self.agent.interrupt(str(interrupt_msg))
                    break
            except queue.Empty:
                self._invalidate(min_interval=0.12)
                pass

        # 割り込み後、エージェントの終了を待つ（最大5秒）
        if interrupt_msg is not None:
            for _ in range(25):  # 25 * 0.2s = 5s
                agent_thread.join(timeout=0.2)
                if not agent_thread.is_alive():
                    break
            if agent_thread.is_alive():
                logging.warning("Agent thread did not stop within 5s after interrupt")

        agent_thread.join(timeout=5)
        self._stop_spinner()

        # 結果を表示
        if result:
            resp = result.get("final_response", "")
            api_calls = int(result.get("api_calls") or 0)
            interrupted = bool(result.get("interrupted", False))
            has_error = bool(result.get("error"))
            _eprint(f"[done] api_calls={api_calls} interrupted={interrupted} error={has_error}")
            if resp:
                self._last_assistant_response = resp
                self._turn_log.append({
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "user": message,
                    "assistant": resp,
                })
                self._turn_log = self._turn_log[-80:]
                self._print_cpu_output(resp)

            if result.get("messages"):
                self.conversation_history.extend(result["messages"][-4:])
                self.conversation_history = self.conversation_history[-40:]
        else:
            _cprint(f"  {_RED}ERROR: 応答がありません{_RST}")
            _eprint("[done] api_calls=0 interrupted=False error=True")

    # ── スラッシュコマンド ──────────────────────────────────────────

    def process_command(self, text: str) -> bool:
        """スラッシュコマンドを処理する。

        Returns:
            False で終了 (exit/quit)、True で続行。
        """
        cmd_original = text.strip()
        base_word = cmd_original.split()[0].lower().lstrip("/")
        if base_word == "q":
            return False
        cmd_def = resolve_command(base_word)
        canonical = cmd_def.name if cmd_def else base_word

        if canonical in ("exit", "quit"):
            return False
        elif canonical == "help":
            self._show_help()
        elif canonical in ("new", "clear"):
            self._new_session()
            _cprint("  Fresh session started.")
            if canonical == "clear" and self._app:
                try:
                    out = self._app.output
                    out.erase_screen()
                    out.cursor_goto(0, 0)
                    out.flush()
                except Exception:
                    pass
                self.show_banner()
        elif canonical == "redraw":
            self._force_redraw()
            _cprint("  UI redrawn.")
        elif canonical in ("commands",):
            self._show_help(show_all=True)
        elif canonical == "history":
            self._show_history()
        elif canonical == "retry":
            if self._last_user_message:
                self._pending_input.put(self._last_user_message)
                _cprint("  Last user message queued again.")
            else:
                _cprint("  No message to retry.")
        elif canonical == "undo":
            self._undo_last()
        elif canonical == "save":
            self._save_conversation()
        elif canonical == "copy":
            self._copy_last_response()
        elif canonical in ("config", "profile"):
            self._show_config()
        elif canonical == "tools":
            names = get_all_tool_names()
            _cprint(f"  登録ツール ({len(names)}個):")
            for n in sorted(names):
                ts = get_toolset_for_tool(n) or "-"
                _cprint(f"    - {n} ({ts})")
        elif canonical == "toolsets":
            self._show_toolsets()
        elif canonical == "model":
            self._handle_model_command(cmd_original)
        elif canonical == "status":
            running = "実行中" if self._agent_running else "待機中"
            _cprint(f"  状態: {running}")
            _cprint(f"  セッション経過: {(datetime.now() - self._session_start).total_seconds():.0f}s")
            _cprint(f"  Turn log: {len(self._turn_log)} turns")
            _cprint(f"  Model: {self.model}")
        else:
            if cmd_def:
                _cprint(f"  /{canonical} はこの AiDiy Hermes 軽量版では未対応です。")
            else:
                _cprint(f"  不明なコマンド: /{base_word}")
        return True

    def _show_help(self, show_all: bool = False) -> None:
        _cprint("")
        commands = [
            ("/new", "Start a fresh session"),
            ("/model", "Open provider -> model picker"),
            ("/model <name>", "Switch model for the current provider"),
            ("/model <name> --provider <provider>", "Switch provider and model"),
            ("/history", "Show recent conversation turns"),
            ("/retry", "Queue the last user message again"),
            ("/undo", "Remove the last local conversation turn"),
            ("/save", "Save the current local conversation"),
            ("/copy", "Copy the last assistant response to clipboard"),
            ("/clear", "Clear screen and start a fresh session"),
            ("/redraw", "Force a screen redraw"),
            ("/tools", "Show enabled tools"),
            ("/toolsets", "Show enabled toolsets"),
            ("/config", "Show current runtime configuration"),
            ("/status", "Show session status"),
            ("/help", "Show this help"),
            ("/exit /quit /q", "Exit"),
        ]
        for name, desc in commands:
            _cprint(f"  {name:<16} {desc}")
        if show_all:
            _cprint("")
            _cprint("  Cloud/gateway-only original Hermes commands are intentionally pruned here.")
        _cprint("")

    def _show_history(self) -> None:
        if not self._turn_log:
            _cprint("  Conversation history is empty.")
            return
        _cprint("")
        for i, turn in enumerate(self._turn_log[-10:], start=max(1, len(self._turn_log) - 9)):
            user = turn.get("user", "").replace("\n", " ")
            assistant = turn.get("assistant", "").replace("\n", " ")
            if len(user) > 100:
                user = user[:97] + "..."
            if len(assistant) > 140:
                assistant = assistant[:137] + "..."
            _cprint(f"  [{i}] user: {user}")
            _cprint(f"      hermes: {assistant}")
        _cprint("")

    def _undo_last(self) -> None:
        if not self._turn_log:
            _cprint("  No local turn to undo.")
            return
        removed = self._turn_log.pop()
        if self.conversation_history:
            del self.conversation_history[-min(4, len(self.conversation_history)):]
        self._last_user_message = self._turn_log[-1]["user"] if self._turn_log else None
        self._last_assistant_response = self._turn_log[-1]["assistant"] if self._turn_log else None
        preview = removed.get("user", "").replace("\n", " ")
        if len(preview) > 80:
            preview = preview[:77] + "..."
        _cprint(f"  Removed last turn: {preview}")

    def _save_conversation(self) -> None:
        out_dir = get_hermes_home() / "sessions"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{self.session_id}.json"
        payload = {
            "session_id": self.session_id,
            "model": self.model,
            "base_url": self.base_url,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "turns": self._turn_log,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        _cprint(f"  Saved conversation: {path}")

    def _copy_last_response(self) -> None:
        if not self._last_assistant_response:
            _cprint("  No assistant response to copy.")
            return
        try:
            subprocess.run(
                ["clip.exe"],
                input=self._last_assistant_response,
                text=True,
                check=True,
                encoding="utf-8",
            )
            _cprint("  Last assistant response copied.")
        except Exception as exc:
            _cprint(f"  Clipboard copy failed: {exc}")

    def _show_config(self) -> None:
        _cprint("")
        _cprint(f"  Session ID: {self.session_id}")
        _cprint(f"  Hermes home: {get_hermes_home()}")
        _cprint(f"  Provider: {self.provider}")
        _cprint(f"  Model: {self.model}")
        _cprint(f"  Base URL: {self.base_url}")
        _cprint(f"  API mode: {self.api_mode}")
        _cprint(f"  Toolsets: {', '.join(self.enabled_toolsets or []) or '(none)'}")
        _cprint(f"  History file: {self._history_file}")
        _cprint("")

    def _show_toolsets(self) -> None:
        _cprint("  Enabled toolsets:")
        for item in self.enabled_toolsets or []:
            _cprint(f"    - {item}")

    def _force_redraw(self) -> None:
        self._force_full_redraw()
        if not self._app:
            print("\033[2J\033[H", end="", flush=True)

    def _handle_model_command(self, command: str) -> None:
        """旧 Hermes 準拠: 引数なしは provider -> model picker、引数ありは直接切替。"""
        parts = command.split(maxsplit=1)
        raw_args = parts[1].strip() if len(parts) > 1 else ""
        model_input, explicit_provider = self._parse_model_args(raw_args)

        if not model_input and not explicit_provider:
            if self._app:
                self._open_model_picker()
            else:
                self._show_model_picker_fallback()
            return

        if explicit_provider and not model_input:
            provider_entry = self._get_provider_entry(explicit_provider, include_models=True)
            if not provider_entry:
                _cprint(f"  Provider is not available: {explicit_provider}")
                return
            models = provider_entry.get("models") or []
            if not models:
                _cprint(f"  No models listed for provider: {explicit_provider}")
                return
            self._apply_provider_model(provider_entry, models[0][1])
            return

        model_name = _model_from_display_label(model_input)
        provider_name = explicit_provider
        if ":" in model_name and not provider_name:
            prefix, rest = model_name.split(":", 1)
            if prefix.lower() in self._provider_slugs():
                provider_name = prefix.lower()
                model_name = rest.strip()
        provider_entry = self._get_provider_entry(provider_name or self.provider, include_models=False)
        if not provider_entry:
            _cprint(f"  Provider is not available: {provider_name or self.provider}")
            return
        self._apply_provider_model(provider_entry, model_name)

    @staticmethod
    def _parse_model_args(raw_args: str) -> Tuple[str, Optional[str]]:
        tokens = raw_args.split()
        provider = None
        model_parts: List[str] = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token == "--provider" and i + 1 < len(tokens):
                provider = tokens[i + 1].strip().lower()
                i += 2
                continue
            if token.startswith("--provider="):
                provider = token.split("=", 1)[1].strip().lower()
                i += 1
                continue
            if token == "--global":
                i += 1
                continue
            model_parts.append(token)
            i += 1
        return " ".join(model_parts).strip(), provider

    @staticmethod
    def _provider_slugs() -> set:
        return {
            "ollama", "openai", "openrt", "openrouter", "gemini", "freeai", "claude", "anthropic",
            "claude_cli", "codex_cli", "gemini_cli", "copilot_cli",
        }

    def _provider_default_model(self, provider: str) -> str:
        cfg = self._aidiy_config
        provider = (provider or "").lower()
        if provider == "openai":
            return cfg.get("CHAT_OPENAI_MODEL") or "gpt-5.2"
        if provider in ("openrt", "openrouter"):
            return cfg.get("CHAT_OPENRT_MODEL") or "google/gemini-3.1-flash-image-preview"
        if provider == "gemini":
            return cfg.get("CHAT_GEMINI_MODEL") or "gemini-3.1-flash-image-preview"
        if provider == "freeai":
            return cfg.get("CHAT_FREEAI_MODEL") or cfg.get("CHAT_GEMINI_MODEL") or "gemini-3.1-flash-image-preview"
        if provider in ("claude", "anthropic"):
            return cfg.get("CHAT_CLAUDE_MODEL") or "claude-sonnet-4-6"
        return cfg.get("CHAT_OLLAMA_MODEL") or "deepseek-v4-flash:cloud"

    def _get_provider_entry(self, provider: str, include_models: bool = False) -> Optional[Dict[str, Any]]:
        provider = (provider or "ollama").strip().lower()
        if provider == "openrouter":
            provider = "openrt"
        if provider == "anthropic":
            provider = "claude"
        cfg = self._aidiy_config

        if provider == "ollama":
            api_key = cfg.get("ollama_key_id", "")
            host = cfg.get("ollama_host", _DEFAULT_OLLAMA_HOST) or _DEFAULT_OLLAMA_HOST
            cloud = _is_valid_key(api_key)
            entry = {
                "slug": "ollama",
                "name": "Ollama Cloud" if cloud else "Ollama Local",
                "base_url": _OLLAMA_CLOUD_BASE_URL if cloud else f"{host.rstrip('/')}/v1",
                "api_key": api_key.strip() if cloud else "ollama",
                "api_mode": "chat_completions",
                "default_model": _strip_cloud_suffix(self._provider_default_model("ollama")) if cloud else self._provider_default_model("ollama"),
            }
        elif provider == "openai":
            api_key = cfg.get("openai_key_id", "")
            if not _is_valid_key(api_key):
                return None
            entry = {
                "slug": "openai",
                "name": "OpenAI",
                "base_url": _OPENAI_BASE_URL,
                "api_key": api_key.strip(),
                "api_mode": "chat_completions",
                "default_model": self._provider_default_model("openai"),
            }
        elif provider == "openrt":
            api_key = cfg.get("openrt_key_id", "")
            if not _is_valid_key(api_key):
                return None
            entry = {
                "slug": "openrt",
                "name": "OpenRouter",
                "base_url": _OPENROUTER_BASE_URL,
                "api_key": api_key.strip(),
                "api_mode": "chat_completions",
                "default_model": self._provider_default_model("openrt"),
            }
        elif provider in ("gemini", "freeai"):
            key_name = "freeai_key_id" if provider == "freeai" else "gemini_key_id"
            api_key = cfg.get(key_name, "")
            if not _is_valid_key(api_key):
                return None
            entry = {
                "slug": provider,
                "name": "FreeAI Gemini" if provider == "freeai" else "Google Gemini",
                "base_url": _GEMINI_OPENAI_BASE_URL,
                "api_key": api_key.strip(),
                "api_mode": "chat_completions",
                "default_model": self._provider_default_model(provider),
            }
        elif provider == "claude":
            api_key = cfg.get("claude_key_id", "")
            if not _is_valid_key(api_key):
                return None
            entry = {
                "slug": "claude",
                "name": "Claude",
                "base_url": _CLAUDE_BASE_URL,
                "api_key": api_key.strip(),
                "api_mode": "anthropic_messages",
                "default_model": self._provider_default_model("claude"),
            }
        elif provider in _SHELL_CLI_PROVIDERS:
            info = _SHELL_CLI_PROVIDERS[provider]
            entry = {
                "slug": provider,
                "name": info["name"],
                "base_url": "",
                "api_key": "",
                "api_mode": "shell",
                "default_model": info["default_model"],
            }
        else:
            return None

        if include_models:
            if entry["api_mode"] == "shell":
                entry["models"] = [("auto", "auto")]
            else:
                entry["models"] = self._fetch_provider_model_labels(entry, limit=50)
                if not entry["models"]:
                    default_model = entry["default_model"]
                    entry["models"] = [(f"yyyy/mm/dd - {default_model}", default_model)]
        return entry

    def _list_provider_entries(self, include_models: bool = False) -> List[Dict[str, Any]]:
        providers: List[Dict[str, Any]] = []
        for slug in ("ollama", "openai", "openrt", "gemini", "freeai", "claude",
                     "claude_cli", "codex_cli", "gemini_cli", "copilot_cli"):
            entry = self._get_provider_entry(slug, include_models=include_models)
            if entry:
                entry["is_current"] = entry["slug"] == self.provider
                providers.append(entry)
        return providers

    def _apply_provider_model(self, provider_entry: Dict[str, Any], model_name: str) -> None:
        model_name = _model_from_display_label(model_name)
        if provider_entry["slug"] == "ollama" and provider_entry["base_url"].rstrip("/") == _OLLAMA_CLOUD_BASE_URL:
            model_name = _strip_cloud_suffix(model_name)
        old_provider = self.provider
        old_model = self.model
        self.provider = provider_entry["slug"]
        self.api_mode = provider_entry["api_mode"]
        self.base_url = provider_entry["base_url"]
        self.api_key = provider_entry["api_key"]
        self.model = model_name or provider_entry["default_model"]
        self.shell_session_started = False
        self.shell_codex_session_id = None
        self._reset_agent()
        _cprint(f"  Model switched: {old_provider}/{old_model} -> {self.provider}/{self.model}")
        _cprint(f"    Provider: {provider_entry['name']}")

    def _show_model_picker_fallback(self) -> None:
        _cprint(f"  Current: {self.provider} / {self.model}")
        _cprint("  Providers:")
        for entry in self._list_provider_entries(include_models=False):
            marker = "*" if entry["slug"] == self.provider else " "
            _cprint(f"   {marker} {entry['slug']:<8} {entry['name']}")
        _cprint("  Usage:")
        _cprint("    /model --provider openai")
        _cprint("    /model gpt-5.2 --provider openai")
        _cprint("    /model openrt:anthropic/claude-sonnet-4.5")

    def _open_model_picker(self) -> None:
        providers = self._list_provider_entries(include_models=True)
        if not providers:
            _cprint("  No available providers in AiDiy_key.json.")
            return
        selected = next((i for i, p in enumerate(providers) if p.get("is_current")), 0)
        self._model_picker_state = {
            "stage": "provider",
            "providers": providers,
            "selected": selected,
            "current_provider": self.provider,
            "current_model": self.model,
        }
        self._invalidate(min_interval=0.0)

    def _close_model_picker(self) -> None:
        self._model_picker_state = None
        self._invalidate(min_interval=0.0)

    def _handle_model_picker_selection(self) -> None:
        state = self._model_picker_state
        if not state:
            return
        selected = state.get("selected", 0)
        if state.get("stage") == "provider":
            providers = state.get("providers") or []
            if selected >= len(providers):
                self._close_model_picker()
                return
            provider_data = providers[selected]
            state["stage"] = "model"
            state["provider_data"] = provider_data
            state["model_list"] = provider_data.get("models") or []
            state["selected"] = 0
            self._invalidate(min_interval=0.0)
            return

        provider_data = state.get("provider_data") or {}
        model_list = state.get("model_list") or []
        back_idx = len(model_list)
        cancel_idx = len(model_list) + 1
        if selected == back_idx:
            state["stage"] = "provider"
            providers = state.get("providers") or []
            state["selected"] = next((i for i, p in enumerate(providers) if p.get("slug") == provider_data.get("slug")), 0)
            self._invalidate(min_interval=0.0)
            return
        if selected >= cancel_idx:
            self._close_model_picker()
            return
        if selected < len(model_list):
            _label, model_id = model_list[selected]
            self._close_model_picker()
            self._apply_provider_model(provider_data, model_id)
            return
        self._close_model_picker()

    def _fetch_available_models(self, limit: int = 12) -> List[str]:
        return [model_id for _label, model_id in self._fetch_available_model_labels(limit=limit)]

    def _fetch_available_model_labels(self, limit: int = 12) -> List[Tuple[str, str]]:
        entry = {
            "slug": self.provider,
            "name": self.provider,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "api_mode": self.api_mode,
        }
        return self._fetch_provider_model_labels(entry, limit=limit)

    def _fetch_provider_model_labels(self, provider_entry: Dict[str, Any], limit: int = 12) -> List[Tuple[str, str]]:
        """OpenAI互換 /models からモデルIDを取得する。失敗時は空配列。"""
        try:
            if provider_entry.get("api_mode") == "anthropic_messages":
                return self._fetch_claude_model_labels(provider_entry, limit=limit)

            base_url = provider_entry["base_url"].rstrip("/")
            url = f"{base_url}/models"
            headers = {"Authorization": f"Bearer {provider_entry['api_key']}"}
            if provider_entry.get("slug") == "openrt":
                headers["HTTP-Referer"] = "https://github.com/monjyu1101/AiDiy2026"
                headers["X-Title"] = "AiDiy Hermes"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as res:
                payload = json.loads(res.read().decode("utf-8"))
            items = [item for item in payload.get("data", []) if isinstance(item, dict)]
            rows: List[Tuple[int, str, str]] = []
            cutoff = datetime.now() - timedelta(days=_CLOUD_MODEL_MAX_AGE_DAYS)
            provider = provider_entry.get("slug", "")
            cloud = base_url == _OLLAMA_CLOUD_BASE_URL
            for item in items:
                model_id = str(item.get("id", "")).strip()
                if not model_id:
                    continue
                if provider == "ollama":
                    model_id = _strip_cloud_suffix(model_id)
                if provider in ("gemini", "freeai") and model_id.startswith("models/"):
                    model_id = model_id.replace("models/", "", 1)
                created_ts = _parse_date_to_timestamp(item.get("created") or item.get("created_at"))
                if created_ts > 0:
                    created_dt = datetime.fromtimestamp(created_ts)
                    if provider in ("ollama", "openai", "openrt", "gemini", "freeai") and created_dt < cutoff:
                        continue
                    label = f"{created_dt.strftime('%Y/%m/%d')} - {model_id.lstrip('~')}"
                else:
                    label = f"yyyy/mm/dd - {model_id.lstrip('~')}"
                rows.append((created_ts, label, model_id))
            rows.sort(key=lambda row: row[0], reverse=True)
            return [(label, model_id) for _created, label, model_id in rows[:limit]]
        except Exception:
            return []

    def _fetch_claude_model_labels(self, provider_entry: Dict[str, Any], limit: int = 12) -> List[Tuple[str, str]]:
        try:
            req = urllib.request.Request(
                provider_entry["base_url"].rstrip("/") + "/v1/models",
                headers={
                    "x-api-key": provider_entry["api_key"],
                    "anthropic-version": "2023-06-01",
                },
            )
            with urllib.request.urlopen(req, timeout=10) as res:
                payload = json.loads(res.read().decode("utf-8"))
            rows: List[Tuple[int, str, str]] = []
            cutoff = datetime.now() - timedelta(days=_CLOUD_MODEL_MAX_AGE_DAYS)
            for item in payload.get("data", []) or []:
                if not isinstance(item, dict):
                    continue
                model_id = str(item.get("id", "")).strip()
                if not model_id:
                    continue
                created_ts = _parse_date_to_timestamp(item.get("created_at") or item.get("created"))
                if created_ts > 0:
                    created_dt = datetime.fromtimestamp(created_ts)
                    if created_dt < cutoff:
                        continue
                    label = f"{created_dt.strftime('%Y/%m/%d')} - {model_id.lstrip('~')}"
                else:
                    label = f"yyyy/mm/dd - {model_id.lstrip('~')}"
                rows.append((created_ts, label, model_id))
            rows.sort(key=lambda row: row[0], reverse=True)
            return [(label, model_id) for _created, label, model_id in rows[:limit]]
        except Exception:
            return []

    # ── バナー ──────────────────────────────────────────────────────

    def show_banner(self) -> None:
        print(_color_for_tty(_AIDIY_HERMES_LOGO, ""))
        print(_color_for_tty(f"v{__version__}", _DIM))
        print()

    # ── TUI 構築 (旧版 _build_tui 互換) ─────────────────────────────

    def _build_tui(self) -> Application:
        """prompt_toolkit Application を構築する。

        旧版 Hermes と同じく、通常出力はターミナルのスクロールバックへ流し、
        TUI 側は画面下部の入力・ステータス・スピナーだけを固定する。
        """
        cli_ref = self

        # ── 入力エリア (旧版互換: completer + auto_suggest + history + multiline) ──
        _completer = SlashCommandCompleter(
            skill_commands_provider=dict,
            command_filter=cli_ref._command_available,
        )
        inp = TextArea(
            height=Dimension(min=1, max=8, preferred=1),
            prompt=cli_ref._get_tui_prompt_fragments,
            style="class:input-area",
            multiline=True,
            wrap_lines=True,
            read_only=Condition(lambda: bool(cli_ref._command_running)),
            history=FileHistory(str(self._history_file)),
            completer=_completer,
            complete_while_typing=True,
            auto_suggest=SlashCommandAutoSuggest(
                history_suggest=AutoSuggestFromHistory(),
                completer=_completer,
            ),
        )
        inp.buffer.tempfile_suffix = ".md"

        def _input_height():
            try:
                doc = inp.buffer.document
                prompt_width = max(2, get_cwidth(cli_ref._get_tui_prompt_text()))
                available_width = max(20, cli_ref._get_terminal_width() - prompt_width)
                visual_lines = 0
                for line in doc.lines:
                    line_width = get_cwidth(line)
                    visual_lines += max(1, -(-max(line_width, 1) // available_width))
                return min(max(visual_lines, 1), 8)
            except Exception:
                return 1

        inp.window.height = _input_height

        class _PlaceholderProcessor(Processor):
            """空入力時に旧版同様の薄いプレースホルダーを描画する。"""

            def __init__(self, get_text):
                self._get_text = get_text

            def apply_transformation(self, ti):
                if not ti.document.text and ti.lineno == 0:
                    text = self._get_text()
                    if text:
                        return Transformation(fragments=ti.fragments + [("class:placeholder", text)])
                return Transformation(fragments=ti.fragments)

        def _get_placeholder():
            if cli_ref._command_running:
                return cli_ref._command_status or "command in progress..."
            if cli_ref._agent_running:
                return "msg=interrupt · slash commands queue for next turn · Ctrl+C cancel"
            return ""

        inp.control.input_processors.append(_PlaceholderProcessor(_get_placeholder))

        # ── スピナー行 (旧版互換) ──
        def _spinner_display():
            txt = cli_ref._render_spinner_text()
            if not txt:
                return []
            return [("class:hint", txt)]

        spin = Window(
            content=FormattedTextControl(_spinner_display),
            height=lambda: cli_ref._spinner_widget_height(),
            wrap_lines=True,
        )

        spacer = Window(
            content=FormattedTextControl(lambda: []),
            height=lambda: cli_ref._agent_spacer_height(),
        )

        # --- /model picker: provider -> model の二段選択 ---
        def _model_picker_display():
            state = cli_ref._model_picker_state
            if not state:
                return []
            stage = state.get("stage", "provider")
            selected = state.get("selected", 0)
            lines = []
            if stage == "provider":
                providers = state.get("providers") or []
                choices = []
                for p in providers:
                    count = len(p.get("models") or [])
                    current = "  <- current" if p.get("is_current") else ""
                    choices.append(f"{p['slug']:<8} {p['name']} ({count} models){current}")
                choices.append("Cancel")
                title = "Model Picker - Select Provider"
                hint = f"Current: {state.get('current_provider')} / {state.get('current_model')}"
            else:
                provider_data = state.get("provider_data") or {}
                model_list = state.get("model_list") or []
                choices = [label for label, _model_id in model_list] + ["<- Back", "Cancel"]
                title = f"Model Picker - {provider_data.get('name', provider_data.get('slug', 'Provider'))}"
                hint = f"Select a model ({len(model_list)} available)"

            lines.append(("class:clarify-border", "╭─ "))
            lines.append(("class:clarify-title", title))
            lines.append(("class:clarify-border", " " + ("─" * max(0, 66 - len(title))) + "╮\n"))
            lines.append(("class:clarify-border", "│ "))
            lines.append(("class:clarify-choice", hint.ljust(66)))
            lines.append(("class:clarify-border", " │\n"))
            total = len(choices)
            offset = state.get("_scroll_offset", 0)
            try:
                term_rows = cli_ref._app.output.get_size().rows if cli_ref._app else shutil.get_terminal_size((100, 24)).lines
            except Exception:
                term_rows = shutil.get_terminal_size((100, 24)).lines
            offset, visible = HermesCLI._compute_model_picker_viewport(selected, offset, total, term_rows)
            state["_scroll_offset"] = offset
            for idx in range(offset, min(total, offset + visible)):
                prefix = "> " if idx == selected else "  "
                style = "class:clarify-selected" if idx == selected else "class:clarify-choice"
                text = (prefix + choices[idx])[:66]
                lines.append(("class:clarify-border", "│ "))
                lines.append((style, text.ljust(66)))
                lines.append(("class:clarify-border", " │\n"))
            lines.append(("class:clarify-border", "╰" + ("─" * 68) + "╯\n"))
            return lines

        model_picker_widget = ConditionalContainer(
            Window(content=FormattedTextControl(_model_picker_display), wrap_lines=True),
            filter=Condition(lambda: cli_ref._model_picker_state is not None),
        )

        input_rule_top = Window(
            char="─",
            height=lambda: cli_ref._tui_input_rule_height("top"),
            style="class:input-rule",
        )
        input_rule_bot = Window(
            char="─",
            height=lambda: cli_ref._tui_input_rule_height("bottom"),
            style="class:input-rule",
        )
        status_bar = ConditionalContainer(
            Window(
                content=FormattedTextControl(lambda: cli_ref._get_status_bar_fragments()),
                height=1,
                wrap_lines=False,
            ),
            filter=Condition(lambda: cli_ref._status_bar_visible),
        )

        # ── キーバインド (旧版とほぼ同じ) ──
        kb = KeyBindings()

        @kb.add("/")
        def _slash(event):
            buf = event.app.current_buffer
            buf.insert_text("/")
            if buf.document.text_before_cursor.strip() == "/":
                buf.start_completion(select_first=False)

        @kb.add("tab", eager=True)
        def _tab(event):
            """Tab: accept selected completion/suggestion, or open completion menu."""
            buf = event.current_buffer
            if buf.complete_state:
                completion = buf.complete_state.current_completion
                if completion is None:
                    buf.go_to_completion(0)
                    completion = buf.complete_state and buf.complete_state.current_completion
                if completion is not None:
                    buf.apply_completion(completion)
                return
            if buf.suggestion and buf.suggestion.text:
                buf.insert_text(buf.suggestion.text)
                return
            buf.start_completion(select_first=False)

        @kb.add("escape", "enter")
        def _alt_enter(event):
            """Alt+Enter inserts a newline for multi-line input."""
            event.current_buffer.insert_text("\n")

        @kb.add("c-j")
        def _ctrl_enter(event):
            """Ctrl+Enter inserts a newline on terminals that send c-j."""
            event.current_buffer.insert_text("\n")

        @kb.add("up")
        def _history_up(event):
            """Up arrow: history on first line, cursor movement inside multiline input."""
            if cli_ref._model_picker_state:
                state = cli_ref._model_picker_state
                state["selected"] = max(0, state.get("selected", 0) - 1)
                event.app.invalidate()
                return
            event.current_buffer.auto_up(count=event.arg)

        @kb.add("down")
        def _history_down(event):
            """Down arrow: history on last line, cursor movement inside multiline input."""
            if cli_ref._model_picker_state:
                state = cli_ref._model_picker_state
                if state.get("stage") == "provider":
                    max_idx = len(state.get("providers") or [])
                else:
                    max_idx = len(state.get("model_list") or []) + 1
                state["selected"] = min(max_idx, state.get("selected", 0) + 1)
                event.app.invalidate()
                return
            event.current_buffer.auto_down(count=event.arg)

        @kb.add("escape", eager=True)
        def _esc(event):
            if cli_ref._model_picker_state:
                cli_ref._close_model_picker()
                event.app.current_buffer.reset()
                return

        @kb.add("c-c")
        def _cc(event):
            now = time.time()
            if cli_ref._model_picker_state:
                cli_ref._close_model_picker()
                event.app.current_buffer.reset()
                event.app.invalidate()
                return
            if cli_ref._agent_running:
                if now - cli_ref._last_ctrl_c_time < 2.0:
                    print("\nForce exiting...")
                    cli_ref._should_exit = True
                    event.app.exit()
                    return
                cli_ref._last_ctrl_c_time = now
                print("\nInterrupting agent... (press Ctrl+C again to force exit)")
                if cli_ref.agent:
                    cli_ref.agent.interrupt("Ctrl+C")
                else:
                    cli_ref._interrupt_queue.put("[Ctrl+C interrupt]")
                return
            if event.app.current_buffer.text:
                event.app.current_buffer.reset()
                event.app.invalidate()
                return
            cli_ref._should_exit = True
            event.app.exit()

        @kb.add("c-d")
        def _cd(event):
            buf = event.app.current_buffer
            if buf.text:
                buf.delete()
            else:
                cli_ref._should_exit = True
                event.app.exit()

        @kb.add("c-l")
        def _cl(event):
            cli_ref._force_full_redraw()

        @kb.add("c-z")
        def _cz(event):
            if sys.platform == "win32":
                _cprint("\nSuspend (Ctrl+Z) is not supported on Windows.")
                event.app.invalidate()
                return
            import signal as _sig
            from prompt_toolkit.application import run_in_terminal

            def _suspend():
                os.kill(0, _sig.SIGTSTP)

            run_in_terminal(_suspend)

        @kb.add("enter")
        def _enter(event):
            if cli_ref._model_picker_state:
                cli_ref._handle_model_picker_selection()
                event.app.current_buffer.reset()
                return

            text = _strip_leaked_terminal_responses(
                _strip_leaked_bracketed_paste_wrappers(inp.text)
            ).strip()
            if not text:
                return

            # スラッシュコマンド
            if _looks_like_slash_command(text):
                if cli_ref._agent_running:
                    cli_ref._pending_input.put(text)
                    _cprint(f"  Queued command for the next turn: {text}")
                    event.app.current_buffer.reset(append_to_history=True)
                    return
                if not cli_ref.process_command(text):
                    cli_ref._should_exit = True
                    event.app.exit()
                event.app.current_buffer.reset(append_to_history=True)
                return

            # 通常メッセージ
            if cli_ref._agent_running:
                cli_ref._interrupt_queue.put(text)
            else:
                cli_ref._pending_input.put(text)
            event.app.current_buffer.reset(append_to_history=True)

        self._register_extra_tui_keybindings(kb, input_area=inp)

        # ── スタイル ──
        style = PTStyle.from_dict(self._build_tui_style_dict())

        # ── レイアウト ──
        completions_menu = CompletionsMenu(max_height=12, scroll_offset=1)
        layout = Layout(
            HSplit(
                self._build_tui_layout_children(
                    model_picker_widget=model_picker_widget,
                    spinner_widget=spin,
                    spacer=spacer,
                    status_bar=status_bar,
                    input_rule_top=input_rule_top,
                    input_area=inp,
                    input_rule_bot=input_rule_bot,
                    completions_menu=completions_menu,
                )
            )
        )

        app = Application(
            layout=layout,
            key_bindings=kb,
            style=style,
            full_screen=False,
            mouse_support=False,
            **({"cursor": _STEADY_CURSOR} if _STEADY_CURSOR is not None else {}),
        )
        self._app = app

        original_on_resize = app._on_resize

        def _resize_clear_ghosts():
            try:
                renderer = app.renderer
                out = renderer.output
                out.reset_attributes()
                out.erase_screen()
                out.cursor_goto(0, 0)
                out.flush()
                renderer.reset(leave_alternate_screen=False)
            except Exception:
                pass
            original_on_resize()

        app._on_resize = _resize_clear_ghosts
        return app

    # ── メインループ (旧版 run() 互換) ──────────────────────────────

    def run(self) -> None:
        """対話モードのメインループを開始する (旧版互換)。"""
        try:
            term_lines = shutil.get_terminal_size().lines
            if term_lines > 2:
                print("\n" * (term_lines - 1), end="", flush=True)
        except Exception:
            pass

        self.show_banner()
        _cprint("対話モード")
        _cprint("　／help でコマンド一覧  Ctrl+C または /exit で終了します。")
        _cprint("  Tab でスラッシュ補完、エージェント実行中に Enter で割り込みできます。")
        _cprint("")

        app = self._build_tui()

        # コマンドスピナーと経過秒を旧版と同じ 0.1 秒間隔で更新する。
        def spinner_loop():
            while not self._should_exit:
                if not self._app:
                    time.sleep(0.1)
                    continue
                if self._command_running or self._spinner_text:
                    self._invalidate(min_interval=0.1)
                    time.sleep(0.1)
                else:
                    time.sleep(0.2)

        spinner_thread = threading.Thread(target=spinner_loop, daemon=True,
                                          name="spinner-loop")
        spinner_thread.start()

        # process_loop (旧版と同構造: バックグラウンドスレッド)
        def process_loop():
            while not self._should_exit:
                try:
                    user_input = self._pending_input.get(timeout=0.1)
                except queue.Empty:
                    if self._agent_running:
                        self._invalidate(min_interval=0.15)
                    continue

                if not user_input:
                    continue
                if isinstance(user_input, str):
                    user_input = _strip_leaked_terminal_responses(
                        _strip_leaked_bracketed_paste_wrappers(user_input)
                    )

                # スラッシュコマンド判定
                if _looks_like_slash_command(user_input):
                    _cprint(f"\n[command] {user_input}")
                    if not self.process_command(user_input):
                        self._should_exit = True
                        if app.is_running:
                            app.exit()
                    continue

                # 通常チャット
                self._print_user_message(user_input)
                self._agent_running = True
                app.invalidate()

                try:
                    self.chat(user_input)
                finally:
                    self._agent_running = False
                    self._spinner_text = ""
                    app.invalidate()

        loop_thread = threading.Thread(target=process_loop, daemon=True,
                                       name="process-loop")
        loop_thread.start()

        with patch_stdout():
            app.run()


# ─── ヘルパー ──────────────────────────────────────────────────────

def _ts(s: str) -> List[str]:
    if not s or s == "all":
        return ["all"]
    return [x.strip() for x in s.split(",") if x.strip()]


def _env() -> None:
    """プロジェクト直下の .env を読む（存在すれば）。"""
    p = Path(__file__).resolve().parent / ".env"
    if p.exists():
        with open(p) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k, v = k.strip(), v.strip().strip("\"'")
                if k not in os.environ:
                    os.environ[k] = v


# ─── 引数解析 ─────────────────────────────────────────────────────

def _parser(default_model: str = "deepseek-v4-flash:cloud"):
    import argparse
    p = argparse.ArgumentParser(
        prog="aidiy_hermes",
        description="Hermes Harness - Ollama AI Agent CLI",
    )
    p.add_argument("--version", "-V", action="store_true")
    p.add_argument("-z", "--oneshot", metavar="PROMPT", default=None)
    p.add_argument("-m", "--model", default=os.environ.get("OLLAMA_MODEL", default_model))
    p.add_argument("--provider", default=os.environ.get("HERMES_PROVIDER", "ollama"))
    p.add_argument("-t", "--toolsets", default="aidiy-hermes")
    p.add_argument("--list-tools", action="store_true")
    p.add_argument("-Q", "--quiet", action="store_true")
    p.add_argument("--no-tools", action="store_true")
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument("--yolo", action="store_true", default=False,
                   help="Bypass all dangerous command approval prompts (use at your own risk)")
    p.add_argument("query", nargs="*")
    return p


# ─── メイン ────────────────────────────────────────────────────────

def main(argv: Optional[List[str]] = None) -> int:
    _env()

    # AiDiy_key.json から接続設定を取得
    cfg = _load_aidiy_config()
    default_model = cfg.get("CHAT_OLLAMA_MODEL", "deepseek-v4-flash:cloud")

    args = _parser(default_model).parse_args(argv)

    if args.yolo:
        os.environ["HERMES_YOLO_MODE"] = "1"

    if args.version:
        print(f"aidiy_hermes v{__version__}")
        return 0

    setup_logging(log_level="DEBUG" if args.verbose else "WARNING")
    quiet = args.quiet or bool(args.oneshot)

    if args.list_tools:
        names = get_all_tool_names()
        print(f"登録ツール ({len(names)}個):")
        for n in sorted(names):
            ts = get_toolset_for_tool(n) or "-"
            print(f"  - {n} ({ts})")
        return 0

    enabled = None if args.no_tools else _ts(args.toolsets)

    provider_seed = HermesCLI(
        model=default_model,
        toolsets=enabled,
        verbose=args.verbose,
    )
    provider_entry = provider_seed._get_provider_entry(args.provider, include_models=False)
    if not provider_entry:
        provider_entry = provider_seed._get_provider_entry("ollama", include_models=False)
    if not provider_entry:
        print(f"{_RED}ERROR: provider is not available: {args.provider}{_RST}", file=sys.stderr)
        return 1

    model = args.model
    if args.provider != "ollama" and model == default_model:
        model = provider_entry["default_model"]
    if provider_entry["slug"] == "ollama" and provider_entry["base_url"].rstrip("/") == _OLLAMA_CLOUD_BASE_URL:
        model = _strip_cloud_suffix(model)

    cli = HermesCLI(
        model=model,
        toolsets=enabled,
        api_key=provider_entry["api_key"],
        base_url=provider_entry["base_url"],
        provider=provider_entry["slug"],
        api_mode=provider_entry["api_mode"],
        verbose=args.verbose,
    )

    query = args.oneshot or (" ".join(args.query) if args.query else None)

    if query:
        if not quiet:
            cli.show_banner()
            print(f"\nクエリ: {query}")
            print(f"{_ACCENT}{'-' * 40}{_RST}")
        def _progress_thinking(text: str) -> None:
            pass  # [step]/[tool]で経過表示済みのため不要

        def _progress_step(step: int, previous_tools: Optional[List[str]] = None) -> None:
            prev = ",".join(previous_tools or [])
            if prev:
                _eprint(f"[step] {step} (prev:{prev})")
            else:
                _eprint(f"[step] {step}")

        def _progress_tool(event_type: str, function_name: str, *args, **kwargs) -> None:
            preview_args = ""
            if args:
                try:
                    preview_args = str(args[0] or "")
                except Exception:
                    preview_args = ""
            if preview_args and len(preview_args) > 120:
                preview_args = preview_args[:117] + "..."
            if event_type == "tool.started":
                if preview_args:
                    _eprint(f"[tool] {function_name} ... {preview_args}")
                else:
                    _eprint(f"[tool] {function_name} ...")
            elif event_type == "tool.completed":
                duration = kwargs.get("duration")
                if duration is not None:
                    _eprint(f"[tool] {function_name} 完了 ({duration:.1f}s)")
                else:
                    _eprint(f"[tool] {function_name} 完了")

        try:
            _eprint(
                f"[start] provider={provider_entry['slug']} model={model} tools={len(enabled or []) if enabled else 'all'}"
            )
            agent = AIAgent(
                base_url=provider_entry["base_url"],
                api_key=provider_entry["api_key"],
                model=model,
                max_iterations=99,
                enabled_toolsets=enabled,
                provider=provider_entry["slug"],
                api_mode=provider_entry["api_mode"],
                thinking_callback=_progress_thinking,
                tool_progress_callback=_progress_tool,
                step_callback=_progress_step,
            )
            result = agent.run_conversation(query)
            resp = result.get("final_response", "")
            api_calls = result.get("api_calls", 0)
            interrupted = bool(result.get("interrupted", False))
            has_error = bool(result.get("error"))
            _eprint(f"[done] api_calls={api_calls} interrupted={interrupted} error={has_error}")
            if resp:
                print(f"\n{resp}")
        except Exception as e:
            print(f"\n{_RED}ERROR: {e}{_RST}", file=sys.stderr)
            return 1
        return 0

    cli.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())

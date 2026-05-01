"""Hermes Harness — AI Agent コア

OpenAI SDK 経由で Ollama（OpenAI 互換 API）と通信するエージェント。
"""
import json
import logging
import threading
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, List, Optional

from openai import OpenAI

from base.model_tools import get_tool_definitions, handle_function_call
from core.prompt_builder import DEFAULT_AGENT_IDENTITY

logger = logging.getLogger(__name__)


class AIAgent:
    """AI エージェント — Ollama（OpenAI 互換 API）と通信する中核クラス。"""

    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        api_key: str = "",
        model: str = "llama3.2",
        max_iterations: int = 99,
        enabled_toolsets: Optional[List[str]] = None,
        system_prompt: Optional[str] = None,
        quiet_mode: bool = False,
        provider: str = "ollama",
        api_mode: str = "chat_completions",
        **extra: Any,
    ):
        if not system_prompt and extra.get("ephemeral_system_prompt"):
            system_prompt = str(extra.get("ephemeral_system_prompt"))
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.provider = (provider or "ollama").strip().lower()
        self.api_mode = (api_mode or "chat_completions").strip().lower()
        self.max_iterations = max_iterations
        self.enabled_toolsets = enabled_toolsets or ["aidiy-hermes"]
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.quiet_mode = quiet_mode

        # 割り込み機構（スレッドセーフ）
        self._interrupt_requested = False
        self._interrupt_lock = threading.Lock()

        # コールバック
        self.thinking_callback: Optional[Callable[[str], None]] = extra.get("thinking_callback")
        self.tool_progress_callback = extra.get("tool_progress_callback")
        self.step_callback = extra.get("step_callback")
        self.clarify_callback = extra.get("clarify_callback")

        # 旧版由来ツールが参照する軽量互換属性。
        self.platform = extra.get("platform") or "cli"
        self.max_tokens = extra.get("max_tokens")
        self.reasoning_config = extra.get("reasoning_config")
        self.prefill_messages = extra.get("prefill_messages")
        self.session_id = extra.get("session_id") or extra.get("parent_session_id")
        self.providers_allowed = extra.get("providers_allowed", [])
        self.providers_ignored = extra.get("providers_ignored", [])
        self.providers_order = extra.get("providers_order", [])
        self.provider_sort = extra.get("provider_sort")
        self._session_db = extra.get("session_db")
        self._memory_store = extra.get("memory_store")
        if self._memory_store is None and not extra.get("skip_memory"):
            try:
                from tools.memory_tool import MemoryStore

                self._memory_store = MemoryStore()
                self._memory_store.load_from_disk()
            except Exception as exc:
                logger.debug("MemoryStore initialization skipped: %s", exc, exc_info=True)
                self._memory_store = None
        self._current_task_id = extra.get("task_id")
        self._api_call_count = 0
        self._current_tool = None
        self._last_activity_desc = "initialized"

        # OpenAI 互換クライアント。Claude だけは Anthropic Messages 形式で直接呼ぶ。
        self.client = None
        if self.api_mode != "anthropic_messages":
            self.client = OpenAI(
                base_url=self._openai_compatible_base_url(self.base_url),
                api_key=self.api_key or "ollama",
            )

        # ツール定義を取得
        self.tool_definitions = get_tool_definitions(
            enabled_toolsets=self.enabled_toolsets,
            quiet_mode=True,
        )
        self.valid_tool_names = [
            item.get("function", {}).get("name")
            for item in self.tool_definitions
            if item.get("function", {}).get("name")
        ]
        logger.info(
            "AIAgent initialized: provider=%s model=%s tools=%d",
            self.provider, self.model, len(self.tool_definitions),
        )

    @staticmethod
    def _openai_compatible_base_url(base_url: str) -> str:
        """OpenAI SDK に渡す base_url をプロバイダ別に正規化する。"""
        base = (base_url or "").rstrip("/")
        if not base:
            return "http://localhost:11434/v1"
        if base.endswith("/v1") or base.endswith("/openai") or "/openai/" in base:
            return base
        return base + "/v1"

    def _default_system_prompt(self) -> str:
        """デフォルトのシステムプロンプトを返す。"""
        model_short = self.model.split(":")[0] if ":" in self.model else self.model
        return (
            "あなたは Hermes Harness です — ファイル操作・ターミナル実行・Web 検索などのツールを持つ AI エージェント。\n"
            f"モデル: {model_short}\n"
            "利用可能なツールを適宜使って、ユーザーの要求に応えてください。\n"
            "日本語で応答してください。"
        )

    def interrupt(self, reason: str = "") -> None:
        """割り込みをリクエストする（スレッドセーフ）。

        Args:
            reason: 割り込みの理由（ログ用）。
        """
        with self._interrupt_lock:
            self._interrupt_requested = True
        logger.debug("Interrupt requested: %s", reason)

    def clear_interrupt(self) -> None:
        """割り込み状態をクリアする。

        旧版 run_agent.py の clear_interrupt() に準拠。
        次の会話ターンの開始前に必ず呼び出すこと。
        """
        with self._interrupt_lock:
            self._interrupt_requested = False

    @property
    def is_interrupted(self) -> bool:
        """割り込みがリクエストされているかどうか。"""
        with self._interrupt_lock:
            return self._interrupt_requested

    def chat(self, message: str) -> str:
        """単一メッセージを送信し、最終応答を返す。"""
        result = self.run_conversation(message)
        return result.get("final_response", "")

    def get_activity_summary(self) -> Dict[str, Any]:
        """旧版 delegate_task 互換の軽量アクティビティスナップショット。"""
        return {
            "current_tool": self._current_tool,
            "api_call_count": self._api_call_count,
            "max_iterations": self.max_iterations,
            "last_activity_desc": self._last_activity_desc,
        }

    def _notify_thinking(self, text: str) -> None:
        """TUI/CLI へ現在の処理内容を通知する。通知失敗は会話を止めない。"""
        if not self.thinking_callback:
            return
        try:
            self.thinking_callback(text)
        except Exception as exc:
            logger.debug("thinking_callback failed: %s", exc, exc_info=True)

    def _notify_step(self, step: int, previous_tools: Optional[List[str]] = None) -> None:
        """旧版互換のステップ通知。"""
        if not self.step_callback:
            return
        try:
            self.step_callback(step, previous_tools or [])
        except Exception as exc:
            logger.debug("step_callback failed: %s", exc, exc_info=True)

    def _notify_tool_progress(
        self,
        event_type: str,
        function_name: str,
        function_args: Optional[Dict[str, Any]] = None,
        **extra: Any,
    ) -> None:
        if not self.tool_progress_callback:
            return
        try:
            self.tool_progress_callback(
                event_type,
                function_name,
                self._preview_tool_args(function_args or {}),
                function_args or {},
                step=self._api_call_count,
                max_steps=self.max_iterations,
                **extra,
            )
        except Exception as exc:
            logger.debug("tool_progress_callback failed: %s", exc, exc_info=True)

    @staticmethod
    def _preview_tool_args(function_args: Dict[str, Any], max_len: int = 80) -> str:
        if not function_args:
            return ""
        try:
            text = json.dumps(function_args, ensure_ascii=False)
        except Exception:
            text = str(function_args)
        text = " ".join(text.split())
        if len(text) > max_len:
            return text[: max_len - 3] + "..."
        return text

    def run_conversation(
        self,
        user_message: str,
        system_message: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None,
        **extra: Any,
    ) -> Dict:
        """会話を実行する。ツール呼び出しを含む完全なループ。

        割り込みフラグが立った場合、即座に中断する。
        """
        # 割り込み状態をリセット（旧版 run_agent.py の run_conversation 先頭で実施）
        self.clear_interrupt()
        if extra.get("task_id"):
            self._current_task_id = extra.get("task_id")

        if self.api_mode == "anthropic_messages":
            return self._run_anthropic_conversation(
                user_message=user_message,
                system_message=system_message,
                conversation_history=conversation_history,
            )

        messages: List[Dict] = []

        # システムプロンプト
        messages.append({
            "role": "system",
            "content": system_message or self.system_prompt,
        })

        # 過去の会話履歴（あれば）
        if conversation_history:
            messages.extend(conversation_history)

        # ユーザーメッセージ
        messages.append({"role": "user", "content": user_message})

        api_call_count = 0
        previous_tools: List[str] = []

        while api_call_count < self.max_iterations:
            # 割り込みチェック
            if self.is_interrupted:
                logger.debug("Conversation interrupted after %d API calls", api_call_count)
                self._notify_thinking("")
                return {
                    "final_response": "⏸️ 中断されました。",
                    "messages": messages,
                    "api_calls": api_call_count,
                    "interrupted": True,
                }

            api_call_count += 1
            self._api_call_count = api_call_count
            self._last_activity_desc = "calling model"
            self._notify_step(api_call_count, previous_tools)
            self._notify_thinking(f"Step {api_call_count}/{self.max_iterations}: モデル呼び出し中")
            previous_tools = []

            try:
                kwargs: Dict[str, Any] = {
                    "model": self.model,
                    "messages": messages,
                }

                # ツール定義がある場合のみ追加
                if self.tool_definitions:
                    kwargs["tools"] = self.tool_definitions

                response = self.client.chat.completions.create(**kwargs)
                choice = response.choices[0]
                msg = choice.message

                # アシスタントの応答をメッセージリストに追加
                assistant_msg = {"role": "assistant", "content": msg.content or ""}
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    assistant_msg["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in msg.tool_calls
                    ]
                messages.append(assistant_msg)

                # ツール呼び出しがある場合
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        function_name = tool_call.function.name
                        try:
                            function_args = json.loads(tool_call.function.arguments)
                        except json.JSONDecodeError:
                            function_args = {}

                        logger.debug("Tool call: %s(%s)", function_name, function_args)
                        self._current_tool = function_name
                        self._last_activity_desc = f"running {function_name}"
                        previous_tools.append(function_name)
                        self._notify_tool_progress("tool.started", function_name, function_args)
                        tool_start = time.monotonic()
                        result = handle_function_call(
                            function_name,
                            function_args,
                            task_id=self._current_task_id,
                            session_id=self.session_id,
                            parent_agent=self,
                            enabled_tools=self.valid_tool_names,
                        )
                        tool_duration = time.monotonic() - tool_start
                        self._current_tool = None
                        self._last_activity_desc = "tool completed"
                        self._notify_tool_progress(
                            "tool.completed",
                            function_name,
                            function_args,
                            duration=tool_duration,
                        )

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result,
                        })

                    # ツール結果の後、ループを続けてモデルに結果を渡す
                    continue

                # ツール呼び出しがない → 最終応答
                self._notify_thinking("")
                return {
                    "final_response": msg.content or "",
                    "messages": messages,
                    "api_calls": api_call_count,
                }

            except Exception as e:
                logger.error("API call failed: %s", e)
                if self.is_interrupted:
                    self._notify_thinking("")
                    return {
                        "final_response": "⏸️ 中断されました。",
                        "messages": messages,
                        "api_calls": api_call_count,
                        "interrupted": True,
                    }
                self._notify_thinking("")
                return {
                    "final_response": f"エラーが発生しました: {e}",
                    "messages": messages,
                    "api_calls": api_call_count,
                    "error": str(e),
                }

        # 最大反復回数に達した
        self._notify_thinking("")
        return {
            "final_response": "最大反復回数に達しました。応答を生成できませんでした。",
            "messages": messages,
            "api_calls": api_call_count,
        }

    def _run_anthropic_conversation(
        self,
        user_message: str,
        system_message: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None,
    ) -> Dict:
        """Anthropic Messages API で会話を実行する。"""
        messages: List[Dict] = []
        messages.append({
            "role": "system",
            "content": system_message or self.system_prompt,
        })
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})

        api_call_count = 0
        previous_tools: List[str] = []
        while api_call_count < self.max_iterations:
            if self.is_interrupted:
                self._notify_thinking("")
                return {
                    "final_response": "中断されました。",
                    "messages": messages,
                    "api_calls": api_call_count,
                    "interrupted": True,
                }

            api_call_count += 1
            self._api_call_count = api_call_count
            self._last_activity_desc = "calling model"
            self._notify_step(api_call_count, previous_tools)
            self._notify_thinking(f"Step {api_call_count}/{self.max_iterations}: モデル呼び出し中")
            previous_tools = []
            try:
                payload = {
                    "model": self.model,
                    "max_tokens": 4096,
                    "system": system_message or self.system_prompt,
                    "messages": self._anthropic_messages_from_openai(messages),
                }
                tools = self._anthropic_tools_from_openai(self.tool_definitions)
                if tools:
                    payload["tools"] = tools

                data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(
                    self.base_url.rstrip("/") + "/v1/messages",
                    data=data,
                    method="POST",
                    headers={
                        "content-type": "application/json",
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                    },
                )
                with urllib.request.urlopen(req, timeout=120) as res:
                    response = json.loads(res.read().decode("utf-8"))

                text_parts: List[str] = []
                tool_calls: List[Dict[str, Any]] = []
                for block in response.get("content", []) or []:
                    block_type = block.get("type")
                    if block_type == "text":
                        text_parts.append(block.get("text", ""))
                    elif block_type == "tool_use":
                        tool_calls.append({
                            "id": block.get("id", ""),
                            "type": "function",
                            "function": {
                                "name": block.get("name", ""),
                                "arguments": json.dumps(block.get("input") or {}, ensure_ascii=False),
                            },
                        })

                assistant_msg: Dict[str, Any] = {
                    "role": "assistant",
                    "content": "\n".join(part for part in text_parts if part).strip(),
                }
                if tool_calls:
                    assistant_msg["tool_calls"] = tool_calls
                messages.append(assistant_msg)

                if tool_calls:
                    for tool_call in tool_calls:
                        function_name = tool_call["function"]["name"]
                        try:
                            function_args = json.loads(tool_call["function"]["arguments"])
                        except json.JSONDecodeError:
                            function_args = {}
                        self._current_tool = function_name
                        self._last_activity_desc = f"running {function_name}"
                        previous_tools.append(function_name)
                        self._notify_tool_progress("tool.started", function_name, function_args)
                        tool_start = time.monotonic()
                        result = handle_function_call(
                            function_name,
                            function_args,
                            task_id=self._current_task_id,
                            session_id=self.session_id,
                            parent_agent=self,
                            enabled_tools=self.valid_tool_names,
                        )
                        tool_duration = time.monotonic() - tool_start
                        self._current_tool = None
                        self._last_activity_desc = "tool completed"
                        self._notify_tool_progress(
                            "tool.completed",
                            function_name,
                            function_args,
                            duration=tool_duration,
                        )
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": result,
                        })
                    continue

                self._notify_thinking("")
                return {
                    "final_response": assistant_msg["content"],
                    "messages": messages,
                    "api_calls": api_call_count,
                }

            except urllib.error.HTTPError as e:
                body = ""
                try:
                    body = e.read().decode("utf-8", errors="replace")
                except Exception:
                    pass
                logger.error("Anthropic API call failed: HTTP %s %s", e.code, body)
                self._notify_thinking("")
                return {
                    "final_response": f"エラーが発生しました: Anthropic HTTP {e.code} {body}",
                    "messages": messages,
                    "api_calls": api_call_count,
                    "error": body or str(e),
                }
            except Exception as e:
                logger.error("Anthropic API call failed: %s", e)
                self._notify_thinking("")
                return {
                    "final_response": f"エラーが発生しました: {e}",
                    "messages": messages,
                    "api_calls": api_call_count,
                    "error": str(e),
                }

        self._notify_thinking("")
        return {
            "final_response": "最大反復回数に達しました。応答を生成できませんでした。",
            "messages": messages,
            "api_calls": api_call_count,
        }

    @staticmethod
    def _anthropic_tools_from_openai(tool_definitions: List[Dict]) -> List[Dict]:
        tools: List[Dict] = []
        for tool in tool_definitions or []:
            fn = tool.get("function", {}) if isinstance(tool, dict) else {}
            name = fn.get("name")
            if not name:
                continue
            tools.append({
                "name": name,
                "description": fn.get("description", ""),
                "input_schema": fn.get("parameters") or {"type": "object", "properties": {}},
            })
        return tools

    @staticmethod
    def _anthropic_messages_from_openai(messages: List[Dict]) -> List[Dict]:
        result: List[Dict] = []
        for msg in messages:
            role = msg.get("role")
            if role == "system":
                continue
            if role == "tool":
                result.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.get("tool_call_id", ""),
                        "content": str(msg.get("content", "")),
                    }],
                })
                continue
            if role == "assistant":
                blocks: List[Dict] = []
                content = msg.get("content")
                if content:
                    blocks.append({"type": "text", "text": str(content)})
                for tc in msg.get("tool_calls") or []:
                    fn = tc.get("function", {})
                    try:
                        tool_input = json.loads(fn.get("arguments") or "{}")
                    except json.JSONDecodeError:
                        tool_input = {}
                    blocks.append({
                        "type": "tool_use",
                        "id": tc.get("id", ""),
                        "name": fn.get("name", ""),
                        "input": tool_input,
                    })
                result.append({"role": "assistant", "content": blocks or ""})
                continue
            if role == "user":
                result.append({"role": "user", "content": msg.get("content", "")})
        return result

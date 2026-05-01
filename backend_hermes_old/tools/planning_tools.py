"""AiDiy Hermes planning and clarification tools."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from tools.registry import registry, tool_error, tool_result


_STATE_DIR = Path(__file__).resolve().parents[1] / "temp" / "state"
_TODO_FILE = _STATE_DIR / "todo.json"


def _load_todos() -> List[Dict[str, Any]]:
    try:
        payload = json.loads(_TODO_FILE.read_text(encoding="utf-8"))
        return payload if isinstance(payload, list) else []
    except Exception:
        return []


def _save_todos(items: List[Dict[str, Any]]) -> None:
    _STATE_DIR.mkdir(parents=True, exist_ok=True)
    _TODO_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def _handle_todo(args: Dict[str, Any], **_kw) -> str:
    action = str(args.get("action") or "list").strip().lower()
    todos = _load_todos()

    if action == "list":
        return tool_result(success=True, items=todos)

    if action == "clear":
        _save_todos([])
        return tool_result(success=True, items=[])

    if action == "add":
        title = str(args.get("title") or "").strip()
        if not title:
            return tool_error("title is required for add")
        next_id = max([int(item.get("id", 0)) for item in todos] or [0]) + 1
        item = {
            "id": next_id,
            "title": title,
            "status": str(args.get("status") or "pending"),
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        todos.append(item)
        _save_todos(todos)
        return tool_result(success=True, item=item, items=todos)

    if action in {"update", "done", "delete"}:
        try:
            target_id = int(args.get("id"))
        except Exception:
            return tool_error("id is required")
        found = next((item for item in todos if int(item.get("id", 0)) == target_id), None)
        if not found:
            return tool_error(f"todo id not found: {target_id}")
        if action == "delete":
            todos = [item for item in todos if int(item.get("id", 0)) != target_id]
        else:
            found["status"] = "done" if action == "done" else str(args.get("status") or found.get("status") or "pending")
            if args.get("title"):
                found["title"] = str(args.get("title"))
            found["updated_at"] = datetime.now().isoformat(timespec="seconds")
        _save_todos(todos)
        return tool_result(success=True, items=todos)

    return tool_error("action must be one of: list, add, update, done, delete, clear")


def _handle_clarify(args: Dict[str, Any], **_kw) -> str:
    question = str(args.get("question") or "").strip()
    if not question:
        return tool_error("question is required")
    choices = args.get("choices") or []
    if choices and not isinstance(choices, list):
        return tool_error("choices must be an array")
    return tool_result(
        success=True,
        needs_user_input=True,
        question=question,
        choices=[str(choice) for choice in choices],
        instruction="Ask the user this question verbatim and wait for their next reply before continuing.",
    )


TODO_SCHEMA = {
    "description": "Maintain a simple persistent todo list for the current AiDiy Hermes workspace.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["list", "add", "update", "done", "delete", "clear"], "default": "list"},
            "id": {"type": "integer", "description": "Todo id for update/done/delete."},
            "title": {"type": "string", "description": "Todo title for add/update."},
            "status": {"type": "string", "description": "Status such as pending, in_progress, done."},
        },
    },
}


CLARIFY_SCHEMA = {
    "description": "Request clarification from the user. The tool returns a question for the assistant to ask.",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "Question to ask the user."},
            "choices": {"type": "array", "items": {"type": "string"}, "description": "Optional answer choices."},
        },
        "required": ["question"],
    },
}


registry.register(
    name="todo",
    toolset="todo",
    schema=TODO_SCHEMA,
    handler=_handle_todo,
    description="作業TODOを管理する",
)

registry.register(
    name="clarify",
    toolset="clarify",
    schema=CLARIFY_SCHEMA,
    handler=_handle_clarify,
    description="ユーザーへの確認質問を生成する",
)

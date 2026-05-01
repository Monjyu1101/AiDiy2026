"""Anthropic プロンプトキャッシュ（簡略化版）。

マルチターン会話の会話プレフィックスをキャッシュすることで、
入力トークンコストを削減する。
"""
from typing import Any, Dict, List


def _apply_cache_marker(msg: dict, native_anthropic: bool = False) -> dict:
    """単一メッセージに cache_control を付与する。"""
    message = dict(msg)
    role = message.get("role", "")

    if role == "tool" and not native_anthropic:
        return message

    message["cache_control"] = {"type": "ephemeral"}
    return message


def build_system_message(content: str) -> dict:
    """キャッシュ有効化されたシステムメッセージを構築する。"""
    return {
        "role": "system",
        "content": content,
        "cache_control": {"type": "ephemeral"},
    }


def apply_caching_to_conversation(messages: List[Dict]) -> List[Dict]:
    """会話メッセージにキャッシュ制御マーカーを付与する。

    戦略:
    1. システムメッセージ（最初のもの）にマーカーを付与する
    2. 最後の3件の非システムメッセージにマーカーを付与する
    """
    if not messages:
        return messages

    result = list(messages)

    for i, msg in enumerate(result):
        if msg.get("role") == "system":
            result[i] = _apply_cache_marker(msg, True)
            break

    non_system = [(j, msg) for j, msg in enumerate(result) if msg.get("role") != "system"]
    for idx, (j, msg) in enumerate(non_system[-3:]):
        result[j] = _apply_cache_marker(msg, True)

    return result

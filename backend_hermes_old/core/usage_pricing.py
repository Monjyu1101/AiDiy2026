"""利用状況の追跡とコスト計算。"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict

_ZERO = Decimal("0")
_ONE_MILLION = Decimal("1000000")


@dataclass(frozen=True)
class CanonicalUsage:
    """正規化された利用状況データ。"""
    input_tokens: int = 0
    output_tokens: int = 0
    input_cost: Decimal = _ZERO
    output_cost: Decimal = _ZERO
    total_cost: Decimal = _ZERO
    currency: str = "USD"
    cost_status: str = "unknown"  # actual, estimated, included, unknown


@dataclass
class SessionUsage:
    """セッションレベルの利用状況追跡。"""
    session_id: str = ""
    usage_history: list = field(default_factory=list)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: Decimal = _ZERO
    api_call_count: int = 0
    tool_call_count: int = 0


_PRICING_TABLE: Dict[str, Dict[str, float]] = {
    # === OpenAI ===
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4.1": {"input": 2.00, "output": 8.00},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
    # === Anthropic ===
    "claude-sonnet-4": {"input": 3.00, "output": 15.00},
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    # === DeepSeek ===
    "deepseek-chat": {"input": 0.27, "output": 1.10},
    "deepseek-reasoner": {"input": 0.55, "output": 2.19},
    # === Ollama（ローカル実行・無料）===
    "llama3.2": {"input": 0.0, "output": 0.0},
    "llama3.1": {"input": 0.0, "output": 0.0},
    "qwen2.5": {"input": 0.0, "output": 0.0},
    "mistral": {"input": 0.0, "output": 0.0},
    "gemma2": {"input": 0.0, "output": 0.0},
    "phi4": {"input": 0.0, "output": 0.0},
    # 未知のモデルも0扱いにするフォールバック
    "*": {"input": 0.0, "output": 0.0},
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> Decimal:
    """モデル名とトークン数からコストを見積もる。"""
    pricing = _PRICING_TABLE.get(model)
    if not pricing:
        return _ZERO

    input_cost = (Decimal(str(pricing["input"])) * Decimal(input_tokens)) / _ONE_MILLION
    output_cost = (Decimal(str(pricing["output"])) * Decimal(output_tokens)) / _ONE_MILLION
    return input_cost + output_cost


def record_usage(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cached_input_tokens: int = 0,
) -> CanonicalUsage:
    """API呼び出し1回分の利用状況を記録する。"""
    cost = estimate_cost(model, input_tokens + cached_input_tokens, output_tokens)
    return CanonicalUsage(
        input_tokens=input_tokens + cached_input_tokens,
        output_tokens=output_tokens,
        total_cost=cost,
        cost_status="estimated" if cost > _ZERO else "unknown",
    )

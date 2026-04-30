"""モデルメタデータの解決。"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ModelMetadata:
    """モデルのメタデータ。"""
    name: str
    provider: str = ""
    context_length: int = 128000
    max_output: int = 4096
    supports_reasoning: bool = False


_KNOWN_MODELS = {
    # OpenAI
    "gpt-4o": ModelMetadata("gpt-4o", "openai", 128000, 16384),
    "gpt-4o-mini": ModelMetadata("gpt-4o-mini", "openai", 128000, 16384),
    "gpt-4.1": ModelMetadata("gpt-4.1", "openai", 1048576, 32768),
    "gpt-4.1-mini": ModelMetadata("gpt-4.1-mini", "openai", 1048576, 32768),
    "gpt-4.1-nano": ModelMetadata("gpt-4.1-nano", "openai", 1048576, 32768),
    # Anthropic
    "claude-sonnet-4": ModelMetadata("claude-sonnet-4", "anthropic", 200000, 8192, True),
    "claude-sonnet-4-20250514": ModelMetadata("claude-sonnet-4-20250514", "anthropic", 200000, 8192, True),
    # DeepSeek
    "deepseek-chat": ModelMetadata("deepseek-chat", "deepseek", 65536, 8192),
    "deepseek-reasoner": ModelMetadata("deepseek-reasoner", "deepseek", 65536, 8192, True),
    # Ollama（ローカルLLM）
    "llama3.2": ModelMetadata("llama3.2", "ollama", 128000, 4096),
    "llama3.1": ModelMetadata("llama3.1", "ollama", 128000, 8192),
    "qwen2.5": ModelMetadata("qwen2.5", "ollama", 32768, 8192),
    "mistral": ModelMetadata("mistral", "ollama", 32768, 4096),
    "gemma2": ModelMetadata("gemma2", "ollama", 8192, 4096),
    "phi4": ModelMetadata("phi4", "ollama", 16384, 4096),
}


def get_model_metadata(model_name: str) -> ModelMetadata:
    """モデル名からメタデータを取得する。

    既知のモデルの場合は登録済みのメタデータを返し、
    不明なモデルの場合はデフォルト値（ollama, 128Kコンテキスト）で返す。
    """
    return _KNOWN_MODELS.get(model_name, ModelMetadata(model_name, provider="ollama"))


def resolve_provider(model_name: str, base_url: str = "") -> str:
    """モデル名とベースURLからプロバイダを解決する。

    Args:
        model_name: モデル名
        base_url: APIのベースURL（オプション）

    Returns:
        プロバイダ名（'openai', 'anthropic', 'deepseek', 'gemini',
        'openrouter', 'ollama' のいずれか）
    """
    name_lower = model_name.lower()
    url_lower = base_url.lower()

    # OpenAI
    if "openai" in name_lower or "gpt" in name_lower:
        return "openai"
    # Anthropic
    if "claude" in name_lower or "anthropic" in name_lower:
        return "anthropic"
    # DeepSeek
    if "deepseek" in name_lower:
        return "deepseek"
    # Gemini
    if "gemini" in name_lower:
        return "gemini"
    # OpenRouter（ベースURLで判定）
    if "openrouter" in url_lower:
        return "openrouter"
    # Ollama — ベースURLで判定（localhost:11434 / 127.0.0.1:11434）
    if "localhost:11434" in url_lower or "127.0.0.1:11434" in url_lower:
        return "ollama"
    # Ollama — モデル名で判定（よく使われるローカルLLMの接頭辞）
    for prefix in ("llama", "qwen", "mistral", "gemma", "phi", "mixtral"):
        if name_lower.startswith(prefix):
            return "ollama"
    # デフォルト
    return "ollama"

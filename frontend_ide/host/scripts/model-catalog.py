# -*- coding: utf-8 -*-
#
# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""Hermes の既存 picker から公開用の名前・ID だけを取得する。"""
import contextlib
import json
from pathlib import Path
import re
import sys


_CLI_MODEL_BATS = {
    "claude-code": "_claude-code.bat",
    "antigravity-cli": "_antigravity_cli.bat",
    "codex-cli": "_codex_cli.bat",
    "copilot-cli": "_copilot_cli.bat",
    "grok-cli": "_grok_cli.bat",
}
_CLI_MODEL_CONFIGS = {
    "claude-code": "AiDiy_code_claude_cli.json",
    "antigravity-cli": "AiDiy_code_antigravity_cli.json",
    "codex-cli": "AiDiy_code_codex_cli.json",
    "copilot-cli": "AiDiy_code_copilot_cli.json",
    "grok-cli": "AiDiy_code_grok_cli.json",
}
_MODEL_ID = re.compile(r"[A-Za-z0-9._:/-]+")
_BAT_MODEL_LINE = re.compile(r'^if "%MODEL_NUMBER%"=="\d+" set "MODEL=([A-Za-z0-9._:-]+)"$')


def _cli_models(project_root: Path, provider: str) -> list[dict[str, str]]:
    """外部 CLI の設定 JSON を優先し、候補がなければ bat から補う。"""
    config_name = _CLI_MODEL_CONFIGS.get(provider)
    if config_name:
        try:
            payload = json.loads((project_root / "_config" / config_name).read_text(encoding="utf-8-sig"))
            configured = payload.get("models", {})
            if isinstance(configured, dict):
                models = [
                    {"label": label, "id": model}
                    for model, label in configured.items()
                    if isinstance(model, str) and _MODEL_ID.fullmatch(model)
                    and isinstance(label, str) and label.strip()
                ]
                if any(item["id"] != "auto" for item in models):
                    return [
                        next((item for item in models if item["id"] == "auto"), {"label": "auto", "id": "auto"}),
                        *(item for item in models if item["id"] != "auto"),
                    ]
        except (OSError, ValueError, AttributeError):
            pass
    filename = _CLI_MODEL_BATS.get(provider)
    if not filename:
        return [{"label": "auto", "id": "auto"}]
    try:
        lines = (project_root / "scripts" / "cli_bat" / filename).read_text(encoding="utf-8-sig").splitlines()
    except OSError:
        return [{"label": "auto", "id": "auto"}]
    models = list(dict.fromkeys(
        match.group(1)
        for line in lines
        if (match := _BAT_MODEL_LINE.fullmatch(line.strip()))
    ))
    return [{"label": "auto", "id": "auto"}, *({"label": model, "id": model} for model in models)]


def catalog(cli_path: str, provider: str = "") -> dict:
    cli_root = Path(cli_path).resolve().parent
    sys.path.insert(0, str(cli_root))
    with contextlib.redirect_stdout(sys.stderr):
        import cli_main as cli

        # 会話/TUI/MCP を起動せず、既存 picker の一覧取得メソッドだけを使う。
        class Picker:
            _aidiy_provider_default_model = cli.HermesCLI._aidiy_provider_default_model
            _get_aidiy_provider_entry = cli.HermesCLI._get_aidiy_provider_entry
            _fetch_aidiy_provider_model_labels = cli.HermesCLI._fetch_aidiy_provider_model_labels
            _fetch_aidiy_openrouter_model_meta = cli.HermesCLI._fetch_aidiy_openrouter_model_meta
            _fetch_aidiy_codex_model_labels = cli.HermesCLI._fetch_aidiy_codex_model_labels
            _fetch_aidiy_claude_model_labels = cli.HermesCLI._fetch_aidiy_claude_model_labels

        picker = Picker()
        try:
            picker._aidiy_config = json.loads(cli._AIDIY_KEY_JSON.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            picker._aidiy_config = {}
        # プロバイダ一覧表示ではネットワーク問い合わせを行わない。
        picker._aidiy_config.setdefault("CHAT_OPENAI_OAUTH_MODEL", cli._OPENAI_OAUTH_FALLBACK_MODEL)
        if provider:
            entry = picker._get_aidiy_provider_entry(provider, include_models=True)
            if not entry:
                return {"models": []}
            if entry.get("is_cli"):
                return {"models": _cli_models(cli_root.parent, provider)}
            return {"models": [{"label": str(label), "id": str(model)} for label, model in entry.get("models", [])]}
        slugs = [
            "openai_oauth", "xai-oauth", "ollama", "openai", "openrt",
            "gemini", "freeai", "anthropic", "local_chat",
        ]
        slugs.extend(item["slug"] for item in cli._AIDIY_CLI_PROVIDERS)
        providers = []
        for slug in slugs:
            entry = picker._get_aidiy_provider_entry(slug, include_models=False)
            if entry:
                providers.append({"id": entry["slug"], "label": entry["name"]})
        return {"providers": providers}


if __name__ == "__main__":
    try:
        print(json.dumps(catalog(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else ""), ensure_ascii=False))
    except Exception:
        # 設定や認証情報を含み得る内部例外を Webview へ渡さない。
        print("モデル候補を取得できません。Hermes のバージョンと設定を確認してください。", file=sys.stderr)
        sys.exit(1)

"""Hermes の既存 picker から公開用の名前・ID だけを取得する。"""
import contextlib
import json
from pathlib import Path
import sys


def catalog(cli_path: str, provider: str = "") -> dict:
    sys.path.insert(0, str(Path(cli_path).resolve().parent))
    with contextlib.redirect_stdout(sys.stderr):
        import cli_main as cli

        # 会話/TUI/MCP を起動せず、既存 picker の一覧取得メソッドだけを使う。
        class Picker:
            _aidiy_provider_default_model = cli.HermesCLI._aidiy_provider_default_model
            _get_aidiy_provider_entry = cli.HermesCLI._get_aidiy_provider_entry
            _fetch_aidiy_provider_model_labels = cli.HermesCLI._fetch_aidiy_provider_model_labels
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
            return {"models": [{"label": str(label), "id": str(model)} for label, model in entry.get("models", [])]}
        slugs = ["openai_oauth", "ollama", "openai", "openrt", "gemini", "freeai", "anthropic", "local_chat"]
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

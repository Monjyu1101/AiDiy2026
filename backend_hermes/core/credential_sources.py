"""Hermes が読み取るすべての認証情報ソースに対する統一された削除契約。

Hermes は認証情報プールを多くの場所からシードする:

    env:<VAR>     — os.environ / ~/.hermes/.env
    claude_code   — ~/.claude/.credentials.json
    hermes_pkce   — ~/.hermes/.anthropic_oauth.json
    device_code   — auth.json providers.<provider> (nous, openai-codex 等)
    qwen-cli      — ~/.qwen/oauth_creds.json
    gh_cli        — gh auth token
    config:<name> — custom_providers 設定エントリ
    model_config  — model.provider == "custom" のときの model.api_key
    manual        — ユーザーが `hermes auth add` を実行

各ソースには ``agent.credential_pool._seed_from_*`` に独自のリーダーがある
（既存の形状を維持 — 再構成はしない）。ここで統一するのは **削除** のみ:

    ``hermes auth remove <provider> <N>`` はプールエントリを永続的に消去しなければならない。

このモジュール以前は、各ソースが ``auth_remove_command`` に ad-hoc な削除ブランチを持ち、
いくつかのソースにはブランチがなかった。そのため ``auth remove`` は次の
``load_pool()`` 呼び出しで qwen-cli、nous device_code（部分的）、
hermes_pkce、copilot gh_cli、custom-config ソースについて暗黙に元に戻っていた。

今や全ソースが ``RemovalStep`` を登録し、同一形状で3つのことを行う:

    1. ソースが読み取る外部読み取り可能な状態をクリーンアップする
       (.env 行、auth.json ブロック、OAuth ファイル等)
    2. 対応する ``_seed_from_*`` ブランチが再ロード時に upsert をスキップするよう
       auth.json の ``(provider, source_id)`` を抑制する
    3. クリーンアップ内容とユーザーが確認すべき診断ヒントを
       ``RemovalResult`` で返す（シェルエクスポートされた環境変数、
       意図的に削除しない外部認証情報ファイル等）

新しい認証情報ソースの追加:
    - ``_seed_from_*`` にリーダーブランチを接続（既存パターン）
    - そのリーダーを ``is_source_suppressed(provider, source_id)`` でガード
    - ここに ``RemovalStep`` を登録

``auth_remove_command`` のソースごとの if/elif チェーンは不要になった。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Callable, List, Optional


@dataclass
class RemovalResult:
    """認証情報ソース削除の結果。

    Attributes:
        cleaned: 実際に変更された外部状態を説明する短い文字列リスト
            （例: ``"Cleared XAI_API_KEY from .env"``,
            ``"Cleared openai-codex OAuth tokens from auth store"``）。
            ユーザーへのプレーンテキスト行として表示される。
        hints: ユーザーが自分でクリーンアップする必要があるか、
            意図的にそのまま残している状態に関する診断行
            （シェルエクスポートされた環境変数、削除しない Claude Code
            認証情報ファイル等）。常に非破壊的。
        suppress: クリーンアップ後に ``suppress_credential_source`` を呼び出して
            将来の ``load_pool`` 呼び出しがこのソースをスキップするようにするかどうか。
            デフォルト True — ほぼ全てのソースで粘着性を維持するために必要。
            唯一の正当な False は ``manual`` エントリ（外部からシードされない）。
    """

    cleaned: List[str] = field(default_factory=list)
    hints: List[str] = field(default_factory=list)
    suppress: bool = True


@dataclass
class RemovalStep:
    """特定の認証情報ソースをクリーンに削除する方法。

    Attributes:
        provider: プロバイダープールキー（``"xai"``、``"anthropic"``、``"nous"`` 等）。
            特殊値 ``"*"`` は「任意のプロバイダーに一致」を意味する。
            ``manual`` のようなプロバイダー非特異的なソースに使用。
        source_id: ``PooledCredential.source`` に現れるソース識別子。
            リテラル（``"claude_code"``）または ``match_fn`` でマッチする
            プレフィックスパターンのいずれか。
        match_fn: リテラルの ``source_id`` マッチングを上書きするオプション述語。
            削除されたエントリのソース文字列を受け取る。``env:*``（任意の
            env シードキー）、``config:*``（任意のカスタムプール）、
            ``manual:*``（任意の手動ソースバリアント）に使用。
        remove_fn: ``(provider, removed_entry) -> RemovalResult``。実際の
            クリーンアップを行い、ユーザーへの結果を返す。
        description: ドキュメント / テスト用の一行人間可読説明。
    """

    provider: str
    source_id: str
    remove_fn: Callable[..., RemovalResult]
    match_fn: Optional[Callable[[str], bool]] = None
    description: str = ""

    def matches(self, provider: str, source: str) -> bool:
        if self.provider != "*" and self.provider != provider:
            return False
        if self.match_fn is not None:
            return self.match_fn(source)
        return source == self.source_id


_REGISTRY: List[RemovalStep] = []


def register(step: RemovalStep) -> RemovalStep:
    _REGISTRY.append(step)
    return step


def find_removal_step(provider: str, source: str) -> Optional[RemovalStep]:
    """最初に一致する RemovalStep を返す。未登録の場合は None を返す。

    未登録のソースは ``auth_remove_command`` のデフォルト削除パスにフォールスルーする:
    プールエントリはすでに消去済み（ディスパッチ前に行われる）、外部クリーンアップなし、
    抑制なし。これは ``manual`` エントリの正しい動作 — プールにのみ保存されており、
    外部にクリーンアップするものがない。
    """
    for step in _REGISTRY:
        if step.matches(provider, source):
            return step
    return None


# ---------------------------------------------------------------------------
# ソースごとの RemovalStep 実装 — 1ソース1エントリ。
# ---------------------------------------------------------------------------
# 各 remove_fn は意図的に小さく単一目的にしている。新しい認証情報ソースを
# 追加するにはここに1エントリ追加するだけ — auth_remove_command の変更は不要。


def _remove_env_source(provider: str, removed) -> RemovalResult:
    """env:<VAR> — 最も一般的なケース。

    3つのユーザー状況を処理する:
      1. 変数が ~/.hermes/.env にのみ存在する → クリアする
      2. 変数がユーザーのシェルにのみ存在する（シェルプロファイル、systemd
         EnvironmentFile、launchd plist）→ どこでアンセットするかをヒント
      3. 両方に存在する → .env からクリアし、シェルについてヒント
    """
    from hermes_cli.config import get_env_path, remove_env_value

    result = RemovalResult()
    env_var = removed.source[len("env:"):]
    if not env_var:
        return result

    # Detect shell vs .env BEFORE remove_env_value pops os.environ.
    env_in_process = bool(os.getenv(env_var))
    env_in_dotenv = False
    try:
        env_path = get_env_path()
        if env_path.exists():
            env_in_dotenv = any(
                line.strip().startswith(f"{env_var}=")
                for line in env_path.read_text(errors="replace").splitlines()
            )
    except OSError:
        pass
    shell_exported = env_in_process and not env_in_dotenv

    cleared = remove_env_value(env_var)
    if cleared:
        result.cleaned.append(f"Cleared {env_var} from .env")

    if shell_exported:
        result.hints.extend([
            f"Note: {env_var} is still set in your shell environment "
            f"(not in ~/.hermes/.env).",
            "  Unset it there (shell profile, systemd EnvironmentFile, "
            "launchd plist, etc.) or it will keep being visible to Hermes.",
            f"  The pool entry is now suppressed — Hermes will ignore "
            f"{env_var} until you run `hermes auth add {provider}`.",
        ])
    else:
        result.hints.append(
            f"Suppressed env:{env_var} — it will not be re-seeded even "
            f"if the variable is re-exported later."
        )
    return result


def _remove_claude_code(provider: str, removed) -> RemovalResult:
    """~/.claude/.credentials.json は Claude Code 自体が所有する。

    削除しない — ユーザーの Claude Code インストールはまだ機能する必要がある。
    Hermes が読み取らないよう抑制するだけ。
    """
    return RemovalResult(hints=[
        "Suppressed claude_code credential — it will not be re-seeded.",
        "Note: Claude Code credentials still live in ~/.claude/.credentials.json",
        "Run `hermes auth add anthropic` to re-enable if needed.",
    ])


def _remove_hermes_pkce(provider: str, removed) -> RemovalResult:
    """~/.hermes/.anthropic_oauth.json は Hermes が所有 — 完全に削除する。"""
    from base.hermes_constants import get_hermes_home

    result = RemovalResult()
    oauth_file = get_hermes_home() / ".anthropic_oauth.json"
    if oauth_file.exists():
        try:
            oauth_file.unlink()
            result.cleaned.append("Cleared Hermes Anthropic OAuth credentials")
        except OSError as exc:
            result.hints.append(f"Could not delete {oauth_file}: {exc}")
    return result


def _clear_auth_store_provider(provider: str) -> bool:
    """auth_store.providers[provider] を削除する。削除した場合は True を返す。"""
    from hermes_cli.auth import (
        _auth_store_lock,
        _load_auth_store,
        _save_auth_store,
    )

    with _auth_store_lock():
        auth_store = _load_auth_store()
        providers_dict = auth_store.get("providers")
        if isinstance(providers_dict, dict) and provider in providers_dict:
            del providers_dict[provider]
            _save_auth_store(auth_store)
            return True
    return False


def _remove_nous_device_code(provider: str, removed) -> RemovalResult:
    """Nous OAuth は auth.json providers.nous に存在 — クリアして抑制する。

    クリアに加えて抑制するのは、次の `hermes login` 実行が決定前に
    providers.nous を再書き込みするのを防ぐほかに手段がないから。
    抑制により再有効化に `hermes auth add nous` を経由させ、
    ドキュメントに記載された再追加パスで抑制をアトミックにクリアする。
    """
    result = RemovalResult()
    if _clear_auth_store_provider(provider):
        result.cleaned.append(f"Cleared {provider} OAuth tokens from auth store")
    return result


def _remove_codex_device_code(provider: str, removed) -> RemovalResult:
    """Codex トークンは2か所に存在: Hermes の auth ストアと ~/.codex/auth.json。

    refresh_codex_oauth_pure() は毎回両方に書き込むため、Hermes の auth ストアのみを
    クリアするだけでは不十分 — _seed_from_singletons() が次の load_pool() 呼び出しで
    ~/.codex/auth.json から再インポートし、削除が即座に元に戻る。
    Codex CLI のファイルを削除せず抑制することで、Codex CLI 自体は引き続き動作する。

    ``_seed_from_singletons`` での正規のソース名は ``"device_code"``（プレフィックスなし）。
    エントリはプールに ``"device_code"``（シード済み）または ``"manual:device_code"``
    （``hermes auth add openai-codex`` で追加）として現れるが、いずれも再シードゲートは
    ``"device_code"`` 抑制キーにある。ここで正規キーを抑制し、中央ディスパッチャーも
    ``removed.source`` を抑制する — 多重防衛、べき等。
    """
    from hermes_cli.auth import suppress_credential_source

    result = RemovalResult()
    if _clear_auth_store_provider(provider):
        result.cleaned.append(f"Cleared {provider} OAuth tokens from auth store")
    # Suppress the canonical re-seed source, not just whatever source the
    # removed entry had.  Otherwise `manual:device_code` removals wouldn't
    # block the `device_code` re-seed path.
    suppress_credential_source(provider, "device_code")
    result.hints.extend([
        "Suppressed openai-codex device_code source — it will not be re-seeded.",
        "Note: Codex CLI credentials still live in ~/.codex/auth.json",
        "Run `hermes auth add openai-codex` to re-enable if needed.",
    ])
    return result


def _remove_qwen_cli(provider: str, removed) -> RemovalResult:
    """~/.qwen/oauth_creds.json は Qwen CLI が所有する。

    claude_code と同じパターン — 削除せず抑制する。
    ユーザーの Qwen CLI インストールはそのファイルを引き続き読み取る。
    """
    return RemovalResult(hints=[
        "Suppressed qwen-cli credential — it will not be re-seeded.",
        "Note: Qwen CLI credentials still live in ~/.qwen/oauth_creds.json",
        "Run `hermes auth add qwen-oauth` to re-enable if needed.",
    ])


def _remove_copilot_gh(provider: str, removed) -> RemovalResult:
    """Copilot トークンは `gh auth token` または COPILOT_GITHUB_TOKEN / GH_TOKEN / GITHUB_TOKEN から取得。

    Copilot は特殊: 同一トークンが複数のソースエントリとしてシードされる
    （``_seed_from_singletons`` の gh_cli と ``_seed_from_env`` の env:<VAR>）。
    一つのエントリを他を抑制せずに削除すると重複が復活する。
    ユーザーがどのエントリをクリックしても削除が安定するよう、
    既知の copilot ソースをすべて抑制する。

    ユーザーの gh CLI やシェル状態には触れない — Hermes がトークンを拾わないよう抑制するだけ。
    """
    # Suppress ALL copilot source variants up-front so no path resurrects
    # the pool entry.  The central dispatcher in auth_remove_command will
    # ALSO suppress removed.source, but it's idempotent so double-calling
    # is harmless.
    from hermes_cli.auth import suppress_credential_source
    suppress_credential_source(provider, "gh_cli")
    for env_var in ("COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
        suppress_credential_source(provider, f"env:{env_var}")

    return RemovalResult(hints=[
        "Suppressed all copilot token sources (gh_cli + env vars) — they will not be re-seeded.",
        "Note: Your gh CLI / shell environment is unchanged.",
        "Run `hermes auth add copilot` to re-enable if needed.",
    ])


def _remove_custom_config(provider: str, removed) -> RemovalResult:
    """カスタムプロバイダープールは custom_providers 設定または model.api_key からシードされる。
    両方とも config.yaml にある — ここから変更するのは抑制より侵襲的。
    抑制する; ディスクからキーを完全に削除したい場合はユーザーが config.yaml を直接編集する。
    """
    source_label = removed.source
    return RemovalResult(hints=[
        f"Suppressed {source_label} — it will not be re-seeded.",
        "Note: The underlying value in config.yaml is unchanged.  Edit it "
        "directly if you want to remove the credential from disk.",
    ])


def _register_all_sources() -> None:
    """モジュールインポート時に一度だけ呼び出される。

    順序が重要 — ``find_removal_step`` は最初の一致を返す。
    copilot の ``env:GH_TOKEN`` がシェルに触れない copilot 削除を経由し、
    .env をクリアしようとする汎用環境変数削除を経由しないよう、
    プロバイダー固有のステップを汎用 ``env:*`` ステップの前に置く。
    """
    register(RemovalStep(
        provider="copilot", source_id="gh_cli",
        match_fn=lambda src: src == "gh_cli" or src.startswith("env:"),
        remove_fn=_remove_copilot_gh,
        description="gh auth token / COPILOT_GITHUB_TOKEN / GH_TOKEN",
    ))
    register(RemovalStep(
        provider="*", source_id="env:",
        match_fn=lambda src: src.startswith("env:"),
        remove_fn=_remove_env_source,
        description="Any env-seeded credential (XAI_API_KEY, DEEPSEEK_API_KEY, etc.)",
    ))
    register(RemovalStep(
        provider="anthropic", source_id="claude_code",
        remove_fn=_remove_claude_code,
        description="~/.claude/.credentials.json",
    ))
    register(RemovalStep(
        provider="anthropic", source_id="hermes_pkce",
        remove_fn=_remove_hermes_pkce,
        description="~/.hermes/.anthropic_oauth.json",
    ))
    register(RemovalStep(
        provider="nous", source_id="device_code",
        remove_fn=_remove_nous_device_code,
        description="auth.json providers.nous",
    ))
    register(RemovalStep(
        provider="openai-codex", source_id="device_code",
        match_fn=lambda src: src == "device_code" or src.endswith(":device_code"),
        remove_fn=_remove_codex_device_code,
        description="auth.json providers.openai-codex + ~/.codex/auth.json",
    ))
    register(RemovalStep(
        provider="qwen-oauth", source_id="qwen-cli",
        remove_fn=_remove_qwen_cli,
        description="~/.qwen/oauth_creds.json",
    ))
    register(RemovalStep(
        provider="*", source_id="config:",
        match_fn=lambda src: src.startswith("config:") or src == "model_config",
        remove_fn=_remove_custom_config,
        description="Custom provider config.yaml api_key field",
    ))


_register_all_sources()

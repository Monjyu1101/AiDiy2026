"""AiDiy Hermes では無効化している gateway コマンド。

旧 Hermes Agent の gateway は Slack / Discord / Telegram / Webhook などの
入出力チャンネルを常駐プロセスとして扱うため、AiDiy Hermes の CLI 専用方針
とは責務が合わない。このモジュールは旧 import 互換を保つための安全なスタブ。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GatewayRuntimeSnapshot:
    """旧版 API 互換の gateway 状態スナップショット。"""

    manager: str = "disabled"
    service_installed: bool = False
    service_running: bool = False
    gateway_pids: tuple[int, ...] = ()
    service_scope: str | None = None

    @property
    def running(self) -> bool:
        """gateway が動作中かどうか。AiDiy 版では常に False。"""

        return False

    @property
    def has_process_service_mismatch(self) -> bool:
        """サービス管理状態とプロセス状態が不一致かどうか。AiDiy 版では常に False。"""

        return False


def get_gateway_runtime_snapshot(system: bool = False) -> GatewayRuntimeSnapshot:
    """旧版の状態取得 API。AiDiy 版では常に無効状態を返す。"""

    scope = "system" if system else None
    return GatewayRuntimeSnapshot(service_scope=scope)


def run_gateway(verbose: int = 0, quiet: bool = False, replace: bool = False) -> int:
    """gateway 常駐実行は AiDiy Hermes では提供しない。"""

    if not quiet:
        print("gateway は AiDiy Hermes では無効です。CLI / AIコア連携を使用してください。")
    return 2


def gateway_setup() -> int:
    """gateway セットアップは AiDiy Hermes では提供しない。"""

    print("gateway セットアップは AiDiy Hermes では無効です。")
    return 2


def gateway_command(args) -> int:
    """`hermes gateway ...` 互換エントリポイント。常に無効化メッセージを返す。"""

    action = getattr(args, "gateway_command", None) or getattr(args, "gateway_action", None) or ""
    if action in {"status", "snapshot"}:
        snapshot = get_gateway_runtime_snapshot()
        print(f"gateway: disabled (running={snapshot.running})")
        return 0
    print("gateway コマンドは AiDiy Hermes では無効です。")
    return 2


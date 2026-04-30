"""Browserbase クラウドブラウザプロバイダ — 削除済み。"""

from typing import Dict
from tools.browser_providers.base import CloudBrowserProvider


class BrowserbaseProvider(CloudBrowserProvider):
    def provider_name(self) -> str:
        return "browserbase"

    def is_configured(self) -> bool:
        return False

    def create_session(self, task_id: str) -> Dict[str, object]:
        raise RuntimeError("Browserbase is not available.")

    def close_session(self, session_id: str) -> None:
        pass

    def get_debugger_url(self, session_id: str) -> str:
        return ""

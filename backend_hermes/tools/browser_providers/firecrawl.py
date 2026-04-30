"""Firecrawl クラウドブラウザプロバイダ — 削除済み。"""

from typing import Dict
from tools.browser_providers.base import CloudBrowserProvider


class FirecrawlProvider(CloudBrowserProvider):
    def provider_name(self) -> str:
        return "firecrawl"

    def is_configured(self) -> bool:
        return False

    def create_session(self, task_id: str) -> Dict[str, object]:
        raise RuntimeError("Firecrawl is not available.")

    def close_session(self, session_id: str) -> None:
        pass

    def get_debugger_url(self, session_id: str) -> str:
        return ""

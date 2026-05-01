"""クラウドブラウザプロバイダ抽象の公開口。

呼び出し側が次の形式で ABC を import できるようにする::

    from tools.browser_providers import CloudBrowserProvider
"""

from tools.browser_providers.base import CloudBrowserProvider

__all__ = ["CloudBrowserProvider"]

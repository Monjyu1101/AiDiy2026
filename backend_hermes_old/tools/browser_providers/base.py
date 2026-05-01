"""クラウドブラウザプロバイダの抽象基底クラス。"""

from abc import ABC, abstractmethod
from typing import Dict


class CloudBrowserProvider(ABC):
    """クラウドブラウザバックエンド共通インターフェース。

    実装は同階層モジュールに置き、``browser_tool._PROVIDER_REGISTRY`` に登録する。
    ユーザーは ``hermes setup`` / ``hermes tools`` でプロバイダを選択し、
    選択値は ``config["browser"]["cloud_provider"]`` に保存される。
    """

    @abstractmethod
    def provider_name(self) -> str:
        """ログや診断表示に出す短い表示名。"""

    @abstractmethod
    def is_configured(self) -> bool:
        """必要な環境変数・認証情報が揃っている場合に True を返す。

        ツール登録時（``check_browser_requirements``）に利用可否判定として呼ばれる。
        ネットワークアクセスを行わず、軽量に終わる必要がある。
        """

    @abstractmethod
    def create_session(self, task_id: str) -> Dict[str, object]:
        """クラウドブラウザセッションを作成し、メタデータを返す。

        少なくとも次の dict を返すこと::

            {
                "session_name": str,   # agent-browser --session 用の一意名
                "bb_session_id": str,  # close/cleanup 用プロバイダセッションID
                "cdp_url": str,        # CDP websocket URL
                "features": dict,      # 有効化された機能フラグ
            }

        ``bb_session_id`` は browser_tool.py 側との後方互換のための旧キー名。
        実際にはどのプロバイダでも、そのプロバイダのセッションIDを保持する。
        """

    @abstractmethod
    def close_session(self, session_id: str) -> bool:
        """プロバイダのセッションIDでクラウドセッションを解放・終了する。

        成功時 True、失敗時 False。例外は外へ投げない。
        """

    @abstractmethod
    def emergency_cleanup(self, session_id: str) -> None:
        """プロセス終了時のベストエフォートなセッション後始末。

        atexit / signal handler から呼ばれる。認証情報不足やネットワークエラーを
        許容し、ログだけ残して処理を続ける。
        """

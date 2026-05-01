"""プラグイン可能なコンテキストエンジンの抽象基底クラス。

コンテキストエンジンは、モデルのトークン上限に近づいたときに会話コンテキストを
どのように管理するかを制御する。組み込みの ContextCompressor がデフォルト実装である。
サードパーティエンジン（例: LCM）は、プラグインシステム経由または
``plugins/context_engine/<name>/`` ディレクトリに配置することで置き換えられる。

選択は設定駆動: config.yaml の ``context.engine``。
デフォルトは ``"compressor"``（組み込み）。有効なエンジンは 1 つのみ。

エンジンの責務:
  - コンパクションをいつ実行するかを決定する
  - コンパクションを実行する（要約・DAG 構築など）
  - エージェントが呼び出せるツールをオプションで公開する（例: lcm_grep）
  - API レスポンスからトークン使用量を追跡する

ライフサイクル:
  1. エンジンをインスタンス化して登録する（プラグインの register() またはデフォルト）
  2. 会話開始時に on_session_start() が呼ばれる
  3. 各 API レスポンス後に usage データとともに update_from_response() が呼ばれる
  4. 各ターン後に should_compress() がチェックされる
  5. should_compress() が True を返したら compress() が呼ばれる
  6. 実際のセッション境界（CLI 終了・/reset・ゲートウェイセッション有効期限）で
     on_session_end() が呼ばれる — ターンごとではない
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class ContextEngine(ABC):
    """すべてのコンテキストエンジンが実装しなければならない基底クラス。"""

    # -- アイデンティティ --------------------------------------------------

    @property
    @abstractmethod
    def name(self) -> str:
        """短い識別子（例: 'compressor', 'lcm'）。"""

    # -- トークン状態（run_agent.py が表示/ログ用に読み取る） --------------
    #
    # エンジンはこれらを維持しなければならない。run_agent.py が直接読み取る。

    last_prompt_tokens: int = 0
    last_completion_tokens: int = 0
    last_total_tokens: int = 0
    threshold_tokens: int = 0
    context_length: int = 0
    compression_count: int = 0

    # -- コンパクションパラメーター（run_agent.py がプリフライト用に読み取る） --
    #
    # プリフライト圧縮チェックを制御する。サブクラスは __init__ またはプロパティで
    # オーバーライドできる。ほとんどのエンジンに対してデフォルト値は妥当である。

    threshold_percent: float = 0.75
    protect_first_n: int = 3
    protect_last_n: int = 6

    # -- コアインターフェース -----------------------------------------------

    @abstractmethod
    def update_from_response(self, usage: Dict[str, Any]) -> None:
        """API レスポンスからトークン使用量の追跡値を更新する。

        すべての LLM 呼び出し後に、レスポンスの usage 辞書とともに呼び出される。
        """

    @abstractmethod
    def should_compress(self, prompt_tokens: int = None) -> bool:
        """このターンでコンパクションを実行すべき場合に True を返す。"""

    @abstractmethod
    def compress(
        self,
        messages: List[Dict[str, Any]],
        current_tokens: int = None,
        focus_topic: str = None,
    ) -> List[Dict[str, Any]]:
        """メッセージリストをコンパクトして新しいメッセージリストを返す。

        これがメインのエントリーポイントである。エンジンは完全なメッセージリストを
        受け取り、コンテキスト予算内に収まる（おそらく短い）リストを返す。
        実装は要約・DAG 構築・その他を自由に行えるが、返されるリストは有効な
        OpenAI 形式のメッセージシーケンスでなければならない。

        Args:
            focus_topic: 手動 ``/compress <focus>`` からのオプションのトピック文字列。
                ガイド付き圧縮をサポートするエンジンはこのトピックに関連する情報の
                保持を優先すること。サポートしないエンジンはこの引数を無視してよい。
        """

    # -- オプション: プリフライトチェック -----------------------------------

    def should_compress_preflight(self, messages: List[Dict[str, Any]]) -> bool:
        """API 呼び出し前の簡易チェック（実際のトークン数未取得）。

        デフォルトは False を返す（プリフライトをスキップ）。エンジンが
        安価な見積もりを行える場合はオーバーライドする。
        """
        return False

    # -- オプション: 手動 /compress プリフライト ---------------------------

    def has_content_to_compress(self, messages: List[Dict[str, Any]]) -> bool:
        """クイックチェック: ``messages`` にコンパクト可能なものがあるか?

        ゲートウェイの ``/compress`` コマンドでプリフライトガードとして使用される。
        False を返すことで、LLM 呼び出しをせずに "nothing to compress yet" を
        ゲートウェイが報告できるようにする。

        デフォルトは True を返す（常に試行）。自分のヘッド/テール境界を安価に
        検査できるエンジンは、トランスクリプトが完全に保護されている場合に
        False を返すようオーバーライドすること。
        """
        return True

    # -- オプション: セッションライフサイクル ------------------------------

    def on_session_start(self, session_id: str, **kwargs) -> None:
        """新しい会話セッション開始時に呼ばれる。

        セッションの永続化された状態（DAG・ストア）を読み込むために使用する。
        kwargs には hermes_home・platform・model などが含まれる場合がある。
        """

    def on_session_end(self, session_id: str, messages: List[Dict[str, Any]]) -> None:
        """実際のセッション境界（CLI 終了・/reset・ゲートウェイ有効期限）で呼ばれる。

        状態のフラッシュ・DB 接続のクローズなどに使用する。
        ターンごとではなく、セッションが本当に終了したときのみ呼ばれる。
        """

    def on_session_reset(self) -> None:
        """/new または /reset 時に呼ばれる。セッションごとの状態をリセットする。

        デフォルトは compression_count とトークン追跡をリセットする。
        """
        self.last_prompt_tokens = 0
        self.last_completion_tokens = 0
        self.last_total_tokens = 0
        self.compression_count = 0

    # -- オプション: ツール -----------------------------------------------

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """このエンジンがエージェントに提供するツールスキーマを返す。

        デフォルトは空リストを返す（ツールなし）。LCM は lcm_grep・
        lcm_describe・lcm_expand のスキーマをここで返す。
        """
        return []

    def handle_tool_call(self, name: str, args: Dict[str, Any], **kwargs) -> str:
        """エージェントからのツール呼び出しを処理する。

        get_tool_schemas() が返すツール名に対してのみ呼ばれる。
        JSON 文字列を返さなければならない。

        kwargs に含まれる可能性があるもの:
          messages: 現在のインメモリメッセージリスト（ライブ取り込み用）
        """
        import json
        return json.dumps({"error": f"Unknown context engine tool: {name}"})

    # -- オプション: ステータス / 表示 -----------------------------------

    def get_status(self) -> Dict[str, Any]:
        """表示/ログ用のステータス辞書を返す。

        デフォルトは run_agent.py が期待する標準フィールドを返す。
        """
        return {
            "last_prompt_tokens": self.last_prompt_tokens,
            "threshold_tokens": self.threshold_tokens,
            "context_length": self.context_length,
            "usage_percent": (
                min(100, self.last_prompt_tokens / self.context_length * 100)
                if self.context_length else 0
            ),
            "compression_count": self.compression_count,
        }

    # -- オプション: モデル切り替えサポート -------------------------------

    def update_model(
        self,
        model: str,
        context_length: int,
        base_url: str = "",
        api_key: str = "",
        provider: str = "",
    ) -> None:
        """ユーザーがモデルを切り替えたときまたはフォールバック有効化時に呼ばれる。

        デフォルトは context_length を更新し、threshold_percent から
        threshold_tokens を再計算する。エンジンがそれ以上必要な場合はオーバーライドする
        （例: DAG 予算の再計算・要約モデルの切り替え）。
        """
        self.context_length = context_length
        self.threshold_tokens = int(context_length * self.threshold_percent)

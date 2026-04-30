"""
画像生成プロバイダー ABC
========================

画像生成のプラガブルバックエンドインターフェースを定義する。プロバイダーは
``PluginContext.register_image_gen_provider()`` でインスタンスを登録し、
アクティブなもの（``config.yaml`` の ``image_gen.provider`` で選択）が
全ての ``image_generate`` ツール呼び出しを処理する。

プロバイダーは ``<repo>/plugins/image_gen/<name>/``（組み込み、
``kind: backend`` として自動読み込み）または
``~/.hermes/plugins/image_gen/<name>/``（ユーザー、``plugins.enabled`` でオプトイン）に配置。

レスポンス形式
--------------
全プロバイダーは :func:`success_response` / :func:`error_response` が生成する
dict を返す。ツールラッパーがそれを JSON シリアライズする。キー:

    success        bool
    image          str | None       URL または絶対ファイルパス
    model          str              プロバイダー固有のモデル識別子
    prompt         str              エコーされたプロンプト
    aspect_ratio   str              "landscape" | "square" | "portrait"
    provider       str              プロバイダー名（診断用）
    error          str              success=False のときのみ
    error_type     str              success=False のときのみ
"""

from __future__ import annotations

import abc
import base64
import datetime
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


VALID_ASPECT_RATIOS: Tuple[str, ...] = ("landscape", "square", "portrait")
DEFAULT_ASPECT_RATIO = "landscape"


# ---------------------------------------------------------------------------
# ABC
# ---------------------------------------------------------------------------


class ImageGenProvider(abc.ABC):
    """画像生成バックエンドの抽象基底クラス。

    サブクラスは :meth:`generate` を実装する必要がある。その他は適切なデフォルトを持つ
    — プロバイダーが必要とするものだけをオーバーライドする。
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """``image_gen.provider`` 設定で使用する安定した短い識別子。

        小文字、スペースなし。例: ``fal``、``openai``、``replicate``。
        """

    @property
    def display_name(self) -> str:
        """``hermes tools`` に表示される人間可読ラベル。デフォルトは ``name.title()``。"""
        return self.name.title()

    def is_available(self) -> bool:
        """このプロバイダーが呼び出しを処理できる場合に True を返す。

        通常は必要な API キーの存在確認を行う。デフォルト: True
        （外部依存のないプロバイダーは常に利用可能）。
        """
        return True

    def list_models(self) -> List[Dict[str, Any]]:
        """``hermes tools`` のモデルピッカー用カタログエントリを返す。

        各エントリ::

            {
                "id": "gpt-image-1.5",               # 必須
                "display": "GPT Image 1.5",          # 省略可; デフォルトは id
                "speed": "~10s",                     # 省略可
                "strengths": "...",                  # 省略可
                "price": "$...",                     # 省略可
            }

        デフォルト: 空リスト（プロバイダーにユーザー選択可能なモデルがない）。
        """
        return []

    def get_setup_schema(self) -> Dict[str, Any]:
        """``hermes tools`` ピッカー用のプロバイダーメタデータを返す。

        ``tools_config.py`` が画像生成プロバイダーリストにこのプロバイダーを
        行として挿入するために使用。形式::

            {
                "name": "OpenAI",                     # ピッカーラベル
                "badge": "paid",                      # 省略可の短いタグ
                "tag": "One-line description...",     # 省略可のサブタイトル
                "env_vars": [                         # 入力を促すキー
                    {"key": "OPENAI_API_KEY",
                     "prompt": "OpenAI API key",
                     "url": "https://platform.openai.com/api-keys"},
                ],
            }

        デフォルト: ``display_name`` から派生した最小エントリ。API キープロンプトや
        カスタムバッジを公開するにはオーバーライドする。
        """
        return {
            "name": self.display_name,
            "badge": "",
            "tag": "",
            "env_vars": [],
        }

    def default_model(self) -> Optional[str]:
        """デフォルトのモデル id を返す。適用されない場合は None を返す。"""
        models = self.list_models()
        if models:
            return models[0].get("id")
        return None

    @abc.abstractmethod
    def generate(
        self,
        prompt: str,
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """画像を生成する。

        実装は :func:`success_response` または :func:`error_response` の dict を
        返す必要がある。``kwargs`` には将来のスキーマバージョンが公開する
        前方互換パラメータが含まれる場合がある — 実装は未知のキーを無視すること。
        """


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def resolve_aspect_ratio(value: Optional[str]) -> str:
    """aspect_ratio 値を有効な集合に丸める。デフォルトは landscape。

    無効な値は拒否せずに強制変換するため、エージェントのミスに対して
    ツールサーフェスが寛容になる。
    """
    if not isinstance(value, str):
        return DEFAULT_ASPECT_RATIO
    v = value.strip().lower()
    if v in VALID_ASPECT_RATIOS:
        return v
    return DEFAULT_ASPECT_RATIO


def _images_cache_dir() -> Path:
    """``$HERMES_HOME/cache/images/`` を返す。必要に応じて親ディレクトリを作成する。"""
    from base.hermes_constants import get_hermes_home

    path = get_hermes_home() / "cache" / "images"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_b64_image(
    b64_data: str,
    *,
    prefix: str = "image",
    extension: str = "png",
) -> Path:
    """Base64 画像データをデコードして ``$HERMES_HOME/cache/images/`` に書き込む。

    保存されたファイルへの絶対 :class:`Path` を返す。

    ファイル名形式: ``<prefix>_<YYYYMMDD_HHMMSS>_<short-uuid>.<ext>``。
    """
    raw = base64.b64decode(b64_data)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    short = uuid.uuid4().hex[:8]
    path = _images_cache_dir() / f"{prefix}_{ts}_{short}.{extension}"
    path.write_bytes(raw)
    return path


def success_response(
    *,
    image: str,
    model: str,
    prompt: str,
    aspect_ratio: str,
    provider: str,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """統一された成功レスポンス dict を構築する。

    ``image`` は HTTP URL または絶対ファイルシステムパス（OpenAI のような
    b64 プロバイダー用）のいずれか。追加のバックエンド固有フィールドを
    渡す必要がある呼び出し元は ``extra`` を指定できる。
    """
    payload: Dict[str, Any] = {
        "success": True,
        "image": image,
        "model": model,
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "provider": provider,
    }
    if extra:
        for k, v in extra.items():
            payload.setdefault(k, v)
    return payload


def error_response(
    *,
    error: str,
    error_type: str = "provider_error",
    provider: str = "",
    model: str = "",
    prompt: str = "",
    aspect_ratio: str = DEFAULT_ASPECT_RATIO,
) -> Dict[str, Any]:
    """統一されたエラーレスポンス dict を構築する。"""
    return {
        "success": False,
        "image": None,
        "error": error,
        "error_type": error_type,
        "model": model,
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "provider": provider,
    }

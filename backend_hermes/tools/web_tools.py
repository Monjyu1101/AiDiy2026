"""
Web 関連ツール — Ollama 簡易検索と HTML 抽出。

``web_search``: Ollama のモデルにクエリを投げ、その知識を使って回答する簡易検索。
``web_extract``: 指定された URL から HTML を取得し、テキスト部分だけ抽出する。
両ツールとも ``registry.register()`` により自己登録する。
"""

import json
import logging
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.error import URLError

from openai import OpenAI

from tools.registry import registry, tool_result, tool_error

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# web_search — Ollama 簡易検索
# ---------------------------------------------------------------------------

# OpenAI 互換クライアント（Ollama 用）
_ollama_client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="",
)
_OLLAMA_MODEL = "deepseek-v4-flash:cloud"


def web_search_handler(args: dict, **kwargs) -> str:
    """web_search ツールのハンドラ関数。

    Ollama のモデルにクエリを送信し、モデルの知識に基づいた回答を返す。
    実際の Web 検索は行わない簡易版。

    Args:
        args: {
            "query": str,  # 検索クエリ（必須）
        }

    Returns:
        JSON 文字列（tool_result または tool_error 形式）。
    """
    query = args.get("query")
    if not query or not isinstance(query, str):
        return tool_error("query は必須の文字列パラメータです")

    try:
        response = _ollama_client.chat.completions.create(
            model=_OLLAMA_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "あなたは役立つアシスタントです。質問に対して簡潔かつ正確に答えてください。",
                },
                {
                    "role": "user",
                    "content": f"検索クエリ: {query} について教えて",
                },
            ],
            max_tokens=1024,
            temperature=0.3,
        )
        answer = response.choices[0].message.content.strip()
        return tool_result({"query": query, "result": answer})
    except Exception as e:
        logger.exception("web_search 呼び出しエラー: %s", e)
        return tool_error(f"Ollama 呼び出しに失敗しました: {type(e).__name__}: {e}")


# OpenAI 形式の関数スキーマ
_web_search_schema = {
    "description": "Ollama のモデルにクエリを投げ、その知識に基づいた回答を得る簡易検索（実際の Web 検索は行いません）。",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "検索したいクエリ文字列。",
            },
        },
        "required": ["query"],
    },
}

# ---------------------------------------------------------------------------
# web_extract — HTML 抽出
# ---------------------------------------------------------------------------


class _TextExtractor(HTMLParser):
    """HTML からテキストのみを抽出する HTMLParser サブクラス。"""

    def __init__(self):
        super().__init__()
        self._text_parts: list[str] = []
        self._skip = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # script タグと style タグの中身はスキップ
        if tag in ("script", "style"):
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style"):
            self._skip = False
        # ブロック要素の後に改行を入れる
        if tag in ("p", "br", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr"):
            self._text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip:
            text = data.strip()
            if text:
                self._text_parts.append(text + " ")

    def get_text(self) -> str:
        return "".join(self._text_parts).strip()


def web_extract_handler(args: dict, **kwargs) -> str:
    """web_extract ツールのハンドラ関数。

    指定された URL から HTML を取得し、テキスト部分だけを抽出して
    最初の 3000 文字を返す。

    Args:
        args: {
            "url": str,  # 取得対象の URL（必須）
        }

    Returns:
        JSON 文字列（tool_result または tool_error 形式）。
    """
    url = args.get("url")
    if not url or not isinstance(url, str):
        return tool_error("url は必須の文字列パラメータです")

    try:
        req = Request(url, headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        })
        with urlopen(req, timeout=10) as response:
            html_bytes = response.read()
            # Content-Type からエンコーディングを推定、なければ utf-8
            charset = response.headers.get_content_charset()
            if charset:
                html_text = html_bytes.decode(charset, errors="replace")
            else:
                # バイト列からエンコーディングを推測（UTF-8 → latin-1 の順）
                try:
                    html_text = html_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    html_text = html_bytes.decode("latin-1")

        extractor = _TextExtractor()
        extractor.feed(html_text)
        content = extractor.get_text()

        # 最初の 3000 文字だけ返す
        truncated = content[:3000]
        return tool_result({
            "url": url,
            "content": truncated,
            "length": len(truncated),
        })
    except URLError as e:
        return tool_error(f"URL の取得に失敗しました: {e.reason}")
    except Exception as e:
        logger.exception("web_extract 呼び出しエラー: %s", e)
        return tool_error(f"HTML 抽出に失敗しました: {type(e).__name__}: {e}")


# OpenAI 形式の関数スキーマ
_web_extract_schema = {
    "description": "指定された URL から HTML を取得し、テキスト部分だけを抽出して最初の 3000 文字を返します。",
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "取得・抽出対象の完全な URL（https:// を含む）。",
            },
        },
        "required": ["url"],
    },
}

# ---------------------------------------------------------------------------
# モジュールインポート時にレジストリに自己登録
# ---------------------------------------------------------------------------

registry.register(
    name="web_search",
    toolset="web",
    schema=_web_search_schema,
    handler=web_search_handler,
    description="Ollama のモデルにクエリを投げて回答を得る簡易検索",
    emoji="🔍",
)

registry.register(
    name="web_extract",
    toolset="web",
    schema=_web_extract_schema,
    handler=web_extract_handler,
    description="URL から HTML を取得しテキストを抽出する",
    emoji="🌐",
)

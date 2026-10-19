# -*- coding: utf-8 -*-
"""Chat の添付: 画像は Provider へ渡し、テキストは本文をメッセージに含める。"""

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend_server"))

from AIコア.AIチャット import Chat


class ChatTextAttachment(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        base = Path(self.dir.name)
        self.text = base / "日本語 フォルダ" / "確認.txt"
        self.text.parent.mkdir()
        self.text.write_text("日本語と空白を含むパスの確認用です。", encoding="utf-8")
        self.sjis = base / "旧形式.txt"
        self.sjis.write_bytes("シフトJISの本文".encode("cp932"))
        self.image = base / "小さな画像.png"
        self.image.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
        self.binary = base / "資料.bin"
        self.binary.write_bytes(b"\x00\x01\x02binary")

    async def run_input(self, files):
        chat = SimpleNamespace(親=None, チャンネル="0", _添付テキスト読込=Chat._添付テキスト読込, _AI実行と応答送信=AsyncMock())
        data = {"メッセージ内容": "添付の内容を答えて", "添付ファイル一覧": [str(f) for f in files]}
        await Chat._処理_input_text(chat, data)
        return chat._AI実行と応答送信.call_args

    async def test_text_body_is_added_and_not_passed_as_file(self):
        call = await self.run_input([self.text])
        message = call.args[0]["メッセージ内容"]
        self.assertIn("[添付ファイル: 確認.txt]", message)
        self.assertIn("日本語と空白を含むパスの確認用です。", message)
        self.assertIsNone(call.kwargs["file_path"])

    async def test_image_is_passed_and_text_is_added_together(self):
        call = await self.run_input([self.text, self.image])
        self.assertEqual(call.kwargs["file_path"], str(self.image))
        self.assertIn("日本語と空白を含むパスの確認用です。", call.args[0]["メッセージ内容"])

    async def test_cp932_and_unreadable_files_are_explained(self):
        call = await self.run_input([self.sjis, self.binary])
        message = call.args[0]["メッセージ内容"]
        self.assertIn("シフトJISの本文", message)
        self.assertIn("[添付ファイル: 資料.bin（この形式はChatでは読み取れません）]", message)
        self.assertIsNone(call.kwargs["file_path"])

    def test_long_text_is_truncated_without_breaking_utf8(self):
        long_file = Path(self.dir.name) / "長文.txt"
        long_file.write_text("あ" * 10, encoding="utf-8")
        body = Chat._添付テキスト読込(str(long_file), 上限バイト=7)
        self.assertEqual(body, "ああ\n…（以下省略）")


if __name__ == "__main__":
    unittest.main()

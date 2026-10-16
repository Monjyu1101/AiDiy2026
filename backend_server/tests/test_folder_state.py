# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

import importlib
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
from fastapi import FastAPI, HTTPException, Header
from fastapi.testclient import TestClient
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
state = importlib.import_module("core_router.フォルダ状態")


class FolderStateTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        state.キャッシュ.clear()

    def test_content_membership_and_recursive_count(self):
        (self.root / "sub").mkdir()
        (self.root / "latest.txt").write_text("latest")
        os.utime(self.root / "latest.txt", (2000000000, 2000000000))
        file = self.root / "sub/a.txt"
        file.write_text("old")
        first = state.状態走査(self.root)
        file.write_text("new content")
        second = state.状態走査(self.root)
        self.assertEqual(first["ファイル数"], 2)
        self.assertEqual(len(first["ファイル一覧"]), first["ファイル数"])
        self.assertEqual(first["最終更新日時"], max(f["更新日時"] for f in first["ファイル一覧"]))
        self.assertEqual({f["パス"] for f in first["ファイル一覧"]}, {"latest.txt", "sub/a.txt"})
        self.assertEqual(set(first["ファイル一覧"][0]), {"パス", "名前", "サイズ", "更新日時"})
        self.assertEqual(first["最終更新日時"], second["最終更新日時"])
        self.assertNotEqual(first["変更識別子"], second["変更識別子"])
        file.rename(file.with_name("b.txt"))
        third = state.状態走査(self.root)
        self.assertNotEqual(second["変更識別子"], third["変更識別子"])
        self.assertEqual(state.状態走査(self.root, "sub")["ファイル数"], 1)
        file.with_name("b.txt").unlink()
        self.assertEqual(state.状態走査(self.root, "sub")["ファイル数"], 0)

    def test_boundaries_exclusions_limits_and_cache(self):
        (self.root / "node_modules").mkdir()
        (self.root / "node_modules/no.txt").write_text("no")
        (self.root / "a.txt").write_text("yes")
        (self.root / "package.json").write_text("{}")
        self.assertEqual(state.状態走査(self.root)["ファイル数"], 1)
        self.assertEqual(state.状態走査(self.root, フィルター="")["ファイル数"], 2)
        for path in ["..", "../a", "/", "C:/", "node_modules", "a.txt", "x\\y"]:
            with self.assertRaises((ValueError, OSError), msg=path): state.状態走査(self.root, path)
        self.assertTrue(state.状態走査(self.root, フィルター="", max_files=1)["不完全"])
        a=state.フォルダ状態取得(self.root)
        with patch.object(state, "状態走査", side_effect=AssertionError("cache missed")):
            self.assertIs(state.フォルダ状態取得(self.root), a)
        state.ロック.acquire()
        try:
            with self.assertRaises(BlockingIOError): state.フォルダ状態取得(self.root)
        finally: state.ロック.release()

    def test_hidden_changes_do_not_change_filtered_snapshot(self):
        (self.root / "visible.txt").write_text("visible")
        (self.root / "package.json").write_text("{}")
        before=state.状態走査(self.root)
        unfiltered=state.状態走査(self.root, フィルター="")
        for operation in (lambda:(self.root / "package.json").write_text("new hidden"),
                          lambda:(self.root / "hidden.log").write_text("log"),
                          lambda:(self.root / "hidden.log").unlink()):
            operation()
            after=state.状態走査(self.root)
            for key in ("ファイル数", "最終更新日時", "変更識別子", "ファイル一覧"):
                self.assertEqual(before[key],after[key])
        self.assertNotEqual(unfiltered["変更識別子"],state.状態走査(self.root, フィルター="")["変更識別子"])

    def test_authenticated_api_uses_configured_root(self):
        class Response(BaseModel):
            status: str
            message: str
            data: dict = {}
        def authenticated(authorization: str = Header(default="")):
            if authorization != "Bearer synthetic": raise HTTPException(401)
            return object()
        modules={"core_schema":types.SimpleNamespace(ResponseBase=Response),
                 "deps":types.SimpleNamespace(get_現在利用者=authenticated),
                 "core_models":types.SimpleNamespace(C利用者=object)}
        with patch.dict(sys.modules, modules):
            sys.modules.pop("core_router.files", None)
            files=importlib.import_module("core_router.files")
        self.addCleanup(lambda:sys.modules.pop("core_router.files",None))
        app=FastAPI();app.conf=types.SimpleNamespace(json=types.SimpleNamespace(CODE_BASE_PATH=str(self.root)))
        app.include_router(files.router)
        (self.root / "test.txt").write_text("synthetic")
        with TestClient(app) as client:
            url="/core/files/フォルダ状態"
            self.assertEqual(client.post(url,json={}).status_code,401)
            headers={"Authorization":"Bearer synthetic"}
            response=client.post(url,json={},headers=headers)
            self.assertEqual(response.status_code,200,response.text)
            self.assertEqual(response.json()["data"]["ファイル数"],1)
            self.assertEqual(client.post(url,json={"フォルダ":".."},headers=headers).status_code,404)
            self.assertEqual(client.post(url,json={"フィルター":"bad"},headers=headers).status_code,422)

if __name__ == "__main__": unittest.main()

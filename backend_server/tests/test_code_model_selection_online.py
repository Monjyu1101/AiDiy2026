# -*- coding: utf-8 -*-
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https:#github.com/monjyu1101/AiDiy2026
"""ONLINEのCode方式切替を実ルーター・実セッションで検証する（AI/CLI実行なし）。"""
import ast
import asyncio
import importlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
from typing import Optional
import unittest
from unittest.mock import Mock, patch

from fastapi import FastAPI, Request
import httpx

import test_code_voice_resources as harness


BACKEND = Path(__file__).resolve().parents[1]
SOURCE_PROVIDERS = (
    "claude_sdk", "claude_cli", "copilot_cli", "codex_cli",
    "antigravity_cli", "grok_cli", "opencode_cli",
)
HERMES_MODELS = ("", "auto", "same", "openai_oauth/test-model")


class OnlineCodeModelSelectionTest(unittest.IsolatedAsyncioTestCase):
    # 共通の実WebSocket/SessionConnectionハーネスだけを再利用する。
    # TestCase自体は継承せず、無関係な音声テストを重複実行しない。
    open_endpoint = harness.VoiceResourceTest.open_endpoint
    asyncTearDown = harness.VoiceResourceTest.asyncTearDown

    @classmethod
    def setUpClass(cls):
        harness.VoiceResourceTest.setUpClass.__func__(cls)

    def setUp(self):
        harness.VoiceResourceTest.setUp(self)
        temporary = tempfile.TemporaryDirectory(prefix="aidiy-online-model-")
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        config = root / "_config"
        config.mkdir()
        output = root / "_AIDIY" / "aidiy_diag"
        output.mkdir(parents=True)
        catalog = {provider: {"models": {"test-model": "test"}} for provider in SOURCE_PROVIDERS}
        catalog["aidiy_hermes"] = {"models": {"openai_oauth/test-model": "Hermes test"}}
        for group, value in (("code", catalog), ("chat", {}), ("live", {}), ("live_voices", {}), ("decisions", {})):
            filename = "live_voices_info.json" if group == "live_voices" else f"{group}_models_info.json"
            (output / filename).write_text(json.dumps(value), encoding="utf-8")

        # モデル候補のJSON解析・auto/same追加・初期値正規化も本物を使う。
        spec = importlib.util.spec_from_file_location("online_test_conf_models", BACKEND / "conf" / "conf_model.py")
        module = importlib.util.module_from_spec(spec)
        log = types.ModuleType("log_config")
        log.get_logger = lambda name: self.logger
        with patch.dict(sys.modules, {"log_config": log}):
            spec.loader.exec_module(module)
        config_patch = patch.object(module.conf_models, "_config_dir_path", return_value=str(config))
        config_patch.start()
        self.addCleanup(config_patch.stop)
        self.conf.models = module.conf_models()
        self.conf.json["CODE_AIDIY_HERMES_MODEL"] = ""
        self.original_config = dict(self.conf.json)

        # AIモジュールは偽物に置換するが、CodeAgentの方式選択メソッドは実装を実行。
        source = ast.parse((BACKEND / "AIコア" / "AIコード.py").read_text(encoding="utf-8"))
        agent_class = next(node for node in source.body if isinstance(node, ast.ClassDef) and node.name == "CodeAgent")
        selector = next(node for node in agent_class.body if isinstance(node, ast.FunctionDef) and node.name == "_select_ai_module")
        namespace = {"Optional": Optional, "ModuleType": types.ModuleType, "importlib": importlib, "logger": self.logger}
        exec(compile(ast.Module(body=[selector], type_ignores=[]), "AIコード.py", "exec"), namespace)
        self.cli_module = types.ModuleType("AIコア.AIコード_cli")
        self.sdk_module = types.ModuleType("AIコア.AIコード_claude")
        decisions = types.ModuleType("AIコア.AI判断")
        decisions.Decision = types.SimpleNamespace(model_options=lambda options: options or {})
        modules = patch.dict(sys.modules, {
            "AIコア.AIコード_cli": self.cli_module,
            "AIコア.AIコード_claude": self.sdk_module,
            "AIコア.AI判断": decisions,
        })
        modules.start()
        self.addCleanup(modules.stop)

        def code_provider(**kwargs):
            agent = harness.provider(**kwargs)
            agent._select_ai_module = Mock(wraps=types.MethodType(namespace["_select_ai_module"], agent))
            agent.AIモジュール = agent._select_ai_module()
            return agent

        self.code.side_effect = code_provider
        self.router.update({
            "Request": Request,
            "初期モデル設定生成": self.session_module.初期モデル設定生成,
            "_backend_local稼働中": Mock(return_value=False),
            "取得_コードベース選択肢": Mock(return_value={}),
        })
        harness.load_router_functions({
            "モデル情報設定", "モデル情報取得", "モデル情報取得リクエスト", "_local_chat候補除外",
        }, self.router)
        self.app = FastAPI()
        self.app.conf = self.conf
        for suffix, name in (("設定", "モデル情報設定"), ("取得", "モデル情報取得")):
            self.app.post(f"/core/AIコア/モデル情報/{suffix}")(self.router[name])

        # ASGIはメモリ内で実行。外部通信・実CLIが混ざれば必ずテストを失敗させる。
        self.external_guards = []
        for target in ("urllib.request.urlopen", "subprocess.Popen", "asyncio.create_subprocess_exec", "asyncio.create_subprocess_shell"):
            guard = patch(target, side_effect=AssertionError("AI・CLI・外部通信は禁止"))
            self.external_guards.append(guard.start())
            self.addCleanup(guard.stop)

    async def request(self, suffix, body):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="http://test") as client:
            response = await client.post(f"/core/AIコア/モデル情報/{suffix}", json=body)
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertEqual(result["status"], "OK", result)
        self.logger.exception.assert_not_called()
        return result

    async def choose(self, session, provider, model):
        return await self.request("設定", {
            "セッションID": session.セッションID,
            "モデル設定": {"CODE_AI1_NAME": provider, "CODE_AI1_MODEL": model},
        })

    async def assert_selected(self, session, model):
        result = await self.request("取得", {"セッションID": session.セッションID})
        data = result["data"]
        self.assertIn("aidiy_hermes", data["available_models"]["code_models"])
        self.assertEqual(list(data["available_models"]["code_models"]["aidiy_hermes"]), ["auto", "same", "openai_oauth/test-model"])
        for settings in (session.モデル設定, self.manager.session_states[session.セッションID]["モデル設定"], data["モデル設定"]):
            self.assertEqual(settings["CODE_AI1_NAME"], "aidiy_hermes")
            self.assertEqual(settings["CODE_AI1_MODEL"], model)
        agent = session.code_agent_processors[0]
        self.assertEqual(agent.AI_NAME, "aidiy_hermes")
        self.assertEqual(agent.AI_MODEL, model)
        self.assertIs(agent.AIモジュール, self.cli_module)
        self.assertIsNone(agent.AIインスタンス)
        self.assertEqual(self.conf.json, self.original_config, "適用で共通設定を書き換えない")
        for guard in self.external_guards:
            guard.assert_not_called()

    async def test_switch_from_every_provider_to_hermes_and_read_back(self):
        _, session, _ = await self.open_endpoint(voice=False)
        others = {key: value for key, value in session.モデル設定.items() if not key.startswith("CODE_AI1_")}
        for source in SOURCE_PROVIDERS:
            for model in HERMES_MODELS:
                with self.subTest(source=source, hermes_model=model):
                    await self.choose(session, source, "test-model")
                    await self.choose(session, "aidiy_hermes", model)
                    await self.assert_selected(session, model)
                    self.assertEqual({key: value for key, value in session.モデル設定.items() if not key.startswith("CODE_AI1_")}, others)

    async def test_empty_default_survives_websocket_reconnect_and_core_sync(self):
        socket, session, task = await self.open_endpoint(voice=False)
        await self.choose(session, "aidiy_hermes", "")
        await socket.close()
        await asyncio.wait_for(task, 2)
        _, restored, _ = await self.open_endpoint(session_id=session.セッションID)
        await self.assert_selected(restored, "")
        core_socket, same_session, _ = await self.open_endpoint(socket_no="core", session_id=session.セッションID, voice=False)
        self.assertIs(same_session, restored)
        init = next(message for message in core_socket.messages if message.get("メッセージ識別") == "init")
        self.assertEqual(init["メッセージ内容"]["モデル設定"]["CODE_AI1_NAME"], "aidiy_hermes")
        self.assertEqual(init["メッセージ内容"]["モデル設定"]["CODE_AI1_MODEL"], "")


if __name__ == "__main__":
    unittest.main()

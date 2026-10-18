import importlib.util
import os
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import AsyncMock, Mock, patch

from test_code_cli_output_routing import _load_code_ai_module

ROOT = Path(__file__).resolve().parents[2]
ROUTES = {
    "copilot_cli": "copilot-cli", "claude_cli": "claude-code",
    "codex_cli": "codex-cli", "antigravity_cli": "antigravity-cli",
    "opencode_cli": "opencode", "grok_cli": "grok-cli",
}


class HermesCliModelRoutesTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.cli = _load_code_ai_module()

    def command(self, model, provider="aidiy_hermes"):
        code = self.cli.CodeAI(AI_NAME=provider, AI_MODEL=model, system_instruction="fixture")
        with patch.dict(os.environ, {provider.upper()+"_CLI_PATH": "fixture-cli"}):
            return code._コマンド構築("おはよう", 初回=True, repo_path=ROOT.as_posix())

    def test_catalog_cli_routes_select_hermes_provider(self):
        for name, slug in ROUTES.items():
            for model in ("auto", "same", "fixture-model"):
                with self.subTest(name=name, model=model):
                    command = self.command(name+"/"+model)
                    model_args = [] if model in {"auto", "same"} else ["--model", model]
                    self.assertEqual(command, ["fixture-cli", "-Q", "--provider", slug] + model_args + ["--oneshot-stdin"])

    def test_api_models_auto_same_and_local_chat_keep_existing_arguments(self):
        for model in ("openai_oauth/fixture-model", "freeai/fixture-model", "xai-oauth/fixture-model", "some/model"):
            self.assertEqual(self.command(model), ["fixture-cli", "-Q", "--model", model, "--oneshot-stdin"])
        self.assertEqual(self.command("auto"), ["fixture-cli", "-Q", "--oneshot-stdin"])
        self.assertEqual(self.command("same"), ["fixture-cli", "-Q", "--provider", "same", "--model", "same", "--oneshot-stdin"])
        command = self.command("local_chat")
        self.assertEqual(command[command.index("--provider")+1], "lmstudio")
        self.assertIn("--oneshot-stdin", command)

    def test_direct_copilot_preserves_explicit_model_and_json_output(self):
        command = self.command("fixture-model", "copilot_cli")
        self.assertEqual(command[command.index("--model")+1], "fixture-model")
        self.assertEqual(command[command.index("--output-format")+1], "json")
        self.assertEqual(command[command.index("-p")+1], "おはよう")

    async def test_ordinary_mcp_request_reaches_provider_with_prompt_on_stdin(self):
        spec = importlib.util.spec_from_file_location("route_test_agents", ROOT/"backend_tools/tools_proc/code_agents.py")
        service_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(service_module)
        service = service_module.CodeAgents(project_root=str(ROOT))
        code = self.cli.CodeAI(AI_NAME="aidiy_hermes", AI_MODEL="copilot_cli/auto", system_instruction="fixture")
        code._subprocess実行 = AsyncMock(return_value="おはようございます")
        code.終了 = AsyncMock()
        agent = Mock()
        agent._ensure_ai_instance = AsyncMock(return_value=code)
        module = ModuleType("AIコア.AIコード")
        module.CodeAgent = Mock(return_value=agent)
        with patch.dict(sys.modules, {"AIコア.AIコード": module}), patch.object(service, "_setup_sys_path"), patch.object(service, "_load_key_json", return_value={}), patch.dict(os.environ, {"AIDIY_HERMES_CLI_PATH": "fixture-cli"}):
            result = await service.run_async(prompt="おはよう", ai_name="aidiy_hermes", ai_model="copilot_cli/auto", resume=False)
        self.assertEqual(result["status"], "OK")
        self.assertEqual(module.CodeAgent.call_args.kwargs["AI_MODEL"], "copilot_cli/auto")
        call = code._subprocess実行.call_args.kwargs
        self.assertEqual(call["command"], ["fixture-cli", "-Q", "--provider", "copilot-cli", "--oneshot-stdin"])
        self.assertIn("おはよう", call["stdin_text"])
        self.assertNotIn("おはよう", call["command"])
        code.終了.assert_awaited_once()

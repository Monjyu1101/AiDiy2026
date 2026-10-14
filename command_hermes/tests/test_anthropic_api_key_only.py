"""Anthropic の API キー固定を偽認証・ネットワークなしで検証する。

依存 SDK のない確認環境でも、本体 AST から実際の関数と初期化分岐を
取り出して実行する。実認証ストア・セッション・ネットワークは使わない。
"""
from __future__ import annotations

import ast
from contextlib import nullcontext
from copy import deepcopy
import logging
import json
import tempfile
import time
from pathlib import Path
import types
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
KEY = "sk-ant-api03-configured-test-key"
OAUTH = "sk-ant-oat01-ambient-test-token"


def source_tree(relative):
    return ast.parse((ROOT / relative).read_text(encoding="utf-8"))


def functions(relative, names, namespace=None):
    tree = source_tree(relative)
    found = {node.name: node for node in ast.walk(tree)
             if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names}
    assert set(found) == set(names), (relative, set(names) - set(found))
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), *found.values()], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = namespace if namespace is not None else {}
    exec(compile(module, str(ROOT / relative), "exec"), namespace)
    return namespace


def run_branch(relative, condition, namespace):
    nodes = [node for node in ast.walk(source_tree(relative))
             if isinstance(node, ast.If) and ast.unparse(node.test) == condition
             and any(isinstance(child, ast.Name) and child.id == "resolve_anthropic_api_key" for child in ast.walk(node))]
    assert len(nodes) == 1, (condition, len(nodes))
    # Execute the real production branch, without heavyweight unrelated init.
    module = ast.Module(body=nodes[0].body, type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), str(ROOT / relative), "exec"), namespace)


class FakePool:
    def __init__(self, provider, entries):
        self.provider = provider
        self._entries = entries

    def entries(self):
        return list(self._entries)

    def has_credentials(self):
        return bool(self._entries)

    def select(self):
        return self._entries[0] if self._entries else None


class FakeCredential:
    @staticmethod
    def from_dict(provider, payload):
        return types.SimpleNamespace(provider=provider, runtime_api_key=payload["access_token"], **payload)


class AnthropicApiKeyOnlyTest(unittest.TestCase):
    def setUp(self):
        self.env = {"ANTHROPIC_TOKEN": OAUTH, "CLAUDE_CODE_OAUTH_TOKEN": OAUTH}
        self.secret_reader = Mock(side_effect=lambda name, default="": self.env.get(name, default))
        self.credentials = types.ModuleType("agent.anthropic_credentials")
        namespace = self.credentials.__dict__
        namespace.update(_getenv=self.secret_reader, ANTHROPIC_API_KEY_REQUIRED="Anthropic API key required; configure claude_key_id or ANTHROPIC_API_KEY")
        functions("core/anthropic_credentials.py", ["_is_oauth_token", "resolve_anthropic_api_key", "resolve_anthropic_token"], namespace)
        # Any attempt to acquire/refresh existing Claude credentials is a failure.
        for name in ("read_claude_code_credentials", "read_hermes_oauth_credentials", "_refresh_oauth_token", "_resolve_anthropic_pool_token"):
            setattr(self.credentials, name, Mock(side_effect=AssertionError("OAuth source consulted")))
        self.adapter = types.ModuleType("agent.anthropic_adapter")
        self.adapter.resolve_anthropic_token = self.credentials.resolve_anthropic_token
        self.adapter._is_oauth_token = self.credentials._is_oauth_token
        self.adapter.build_anthropic_client = Mock(side_effect=lambda key, base=None, **kw: types.SimpleNamespace(api_key=key, base_url=base, close=Mock()))
        self.adapter.create_anthropic_message = Mock(return_value="response")
        self.config = types.ModuleType("hermes_cli.config")
        self.config.load_config = lambda: {}
        self.config.load_config_readonly = lambda: {}
        self.config.is_provider_enabled = lambda _: True
        self.models = types.ModuleType("hermes_cli.models")
        self.models.opencode_provider_family = lambda _: None
        self.models.opencode_zen_free_runtime = lambda *_: None
        self.providers = types.ModuleType("hermes_cli.providers")
        self.providers.get_provider = lambda _: None
        self.enterContext(patch.dict("sys.modules", {
            "agent": types.ModuleType("agent"), "agent.anthropic_credentials": self.credentials,
            "agent.anthropic_adapter": self.adapter, "hermes_cli": types.ModuleType("hermes_cli"),
            "hermes_cli.config": self.config, "hermes_cli.models": self.models,
            "hermes_cli.providers": self.providers,
        }))

    def runtime(self, entries=()):
        namespace = {
            "AuthError": RuntimeError, "_getenv": self.secret_reader,
            "_anthropic_base_url_override_ok": lambda _: True,
            "resolve_requested_provider": lambda requested: requested or "anthropic",
            "resolve_provider": lambda requested, **kw: requested,
            "_resolve_named_custom_runtime": lambda **kw: None,
            "_get_model_config": lambda: {},
            "base_url_host_matches": lambda base, host: host in base,
            "load_pool": Mock(return_value=FakePool("anthropic", list(entries))),
            "_is_external_process_provider": lambda _: False,
            "logger": logging.getLogger(__name__),
        }
        functions("hermes_cli/runtime_provider.py", ["_resolve_explicit_runtime", "resolve_runtime_provider"], namespace)
        return namespace

    def initialized(self, key=KEY, provider="anthropic"):
        agent = types.SimpleNamespace(api_mode="anthropic_messages", provider=provider, model="claude-test", quiet_mode=True)
        run_branch("core/agent_init.py", "agent.api_mode == 'anthropic_messages'", {
            "agent": agent, "api_key": key, "base_url": "https://api.anthropic.com",
            "_provider_timeout": None,
        })
        return agent

    def test_explicit_api_key_wins_without_reading_any_ambient_source(self):
        self.env["ANTHROPIC_API_KEY"] = "sk-ant-api03-environment-test-key"
        self.assertEqual(KEY, self.credentials.resolve_anthropic_api_key(KEY, required=True))
        self.secret_reader.assert_not_called()

    def test_compatibility_resolver_uses_only_api_key_environment(self):
        self.env["ANTHROPIC_API_KEY"] = KEY
        self.assertEqual(KEY, self.credentials.resolve_anthropic_token())
        self.assertEqual([("ANTHROPIC_API_KEY",)], [call.args for call in self.secret_reader.call_args_list])

    def test_ambient_oauth_does_not_satisfy_missing_api_key(self):
        self.assertIsNone(self.credentials.resolve_anthropic_token())
        with self.assertRaisesRegex(ValueError, "API key"):
            self.credentials.resolve_anthropic_api_key(required=True)

    def test_oauth_values_are_rejected_even_when_explicitly_named_api_key(self):
        for token in (OAUTH, "cc-test-token", "eyJfake.jwt.token"):
            with self.subTest(token=token), self.assertRaisesRegex(ValueError, "does not support Anthropic OAuth"):
                self.credentials.resolve_anthropic_api_key(token, required=True)
        self.env["ANTHROPIC_API_KEY"] = OAUTH
        with self.assertRaises(ValueError):
            self.credentials.resolve_anthropic_api_key()

    def test_explicit_runtime_retains_key_and_never_loads_pool(self):
        runtime = self.runtime()
        result = runtime["resolve_runtime_provider"](requested="anthropic", explicit_api_key=KEY)
        self.assertEqual(KEY, result["api_key"])
        self.assertEqual("anthropic_messages", result["api_mode"])
        runtime["load_pool"].assert_not_called()

    def test_direct_runtime_env_key_wins_over_old_pool(self):
        self.env["ANTHROPIC_API_KEY"] = KEY
        runtime = self.runtime([types.SimpleNamespace(access_token=OAUTH)])
        result = runtime["resolve_runtime_provider"](requested="anthropic")
        self.assertEqual(KEY, result["api_key"])
        runtime["load_pool"].assert_not_called()

    def test_environment_api_key_retains_its_endpoint(self):
        self.env.update(ANTHROPIC_API_KEY=KEY, ANTHROPIC_BASE_URL="https://env-proxy.example/anthropic")
        runtime = self.runtime()["resolve_runtime_provider"]
        result = runtime(requested="anthropic")
        self.assertEqual("https://env-proxy.example/anthropic", result["base_url"])
        result = runtime(requested="anthropic", explicit_api_key=KEY)
        self.assertEqual("https://api.anthropic.com", result["base_url"])
        namespace = {"_ANTHROPIC_DEFAULT_BASE_URL": "https://api.anthropic.com",
                     "_pool_runtime_base_url": lambda value, default: default,
                     "_scoped_key_env": lambda name: self.env.get(name, ""),
                     "_get_aux_model_for_provider": lambda _: "claude-test", "_aux_probe_active": lambda: False,
                     "AnthropicAuxiliaryClient": lambda client, *args, **kw: client,
                     "logger": logging.getLogger(__name__)}
        create = functions("core/auxiliary_client.py", ["_try_anthropic"], namespace)["_try_anthropic"]
        client, _ = create()
        self.assertEqual("https://env-proxy.example/anthropic", client.base_url)
        client, _ = create(explicit_api_key=KEY)
        self.assertEqual("https://api.anthropic.com", client.base_url)

    def test_direct_runtime_without_key_fails_clearly(self):
        for explicit_base in (None, "https://api.anthropic.com"):
            with self.subTest(base=explicit_base), self.assertRaisesRegex(RuntimeError, "API key"):
                self.runtime()["resolve_runtime_provider"](requested="anthropic", explicit_base_url=explicit_base)

    def test_aidiy_configured_key_reaches_runtime_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "fake_AiDiy_key.json"
            config_path.write_text(json.dumps({"claude_key_id": KEY}), encoding="utf-8")
            namespace = {"_AIDIY_KEY_JSON": config_path, "json": json,
                         "_CLAUDE_BASE_URL": "https://api.anthropic.com"}
            functions("cli_main.py", ["_is_valid_key", "_load_aidiy_hermes_provider_defaults"], namespace)
            defaults = namespace["_load_aidiy_hermes_provider_defaults"]("anthropic")
        result = self.runtime()["resolve_runtime_provider"](
            requested=defaults["provider"], explicit_api_key=defaults["api_key"],
            explicit_base_url=defaults["base_url"], target_model=defaults["model"])
        self.assertEqual(KEY, result["api_key"])
        self.assertEqual(KEY, self.initialized(result["api_key"]).api_key)

    def test_model_catalog_rejects_explicit_oauth_before_network(self):
        namespace = {"_urlopen_model_catalog_request": Mock(side_effect=AssertionError("network attempted"))}
        fetch = functions("hermes_cli/models.py", ["_fetch_anthropic_models"], namespace)["_fetch_anthropic_models"]
        self.assertIsNone(fetch(api_key=OAUTH))
        namespace["_urlopen_model_catalog_request"].assert_not_called()

    def test_explicit_protocol_mode_cannot_hide_native_host_auth_policy(self):
        condition = "agent.api_mode == 'anthropic_messages' and agent._base_url_hostname == 'api.anthropic.com'"
        nodes = [node for node in ast.walk(source_tree("core/agent_init.py"))
                 if isinstance(node, ast.If) and ast.unparse(node.test) == condition]
        self.assertEqual(1, len(nodes))
        for provider in ("", "custom"):
            agent = types.SimpleNamespace(provider=provider, api_mode="anthropic_messages", _base_url_hostname="api.anthropic.com", quiet_mode=True)
            module = ast.Module(body=nodes, type_ignores=[])
            exec(compile(ast.fix_missing_locations(module), "native-provider-normalization", "exec"), {"agent": agent})
            self.assertEqual("anthropic", agent.provider)
            with self.assertRaises(ValueError):
                run_branch("core/agent_init.py", "agent.api_mode == 'anthropic_messages'", {
                    "agent": agent, "api_key": OAUTH, "base_url": "https://api.anthropic.com", "_provider_timeout": None})
        self.adapter.build_anthropic_client.assert_not_called()

    def test_initialization_retains_configured_api_key(self):
        agent = self.initialized()
        self.assertEqual(KEY, agent.api_key)
        self.assertEqual(KEY, agent._anthropic_api_key)
        self.assertFalse(agent._is_anthropic_oauth)
        self.assertEqual(KEY, self.adapter.build_anthropic_client.call_args.args[0])

    def test_initialization_without_key_or_with_oauth_fails_before_client(self):
        for key in (None, OAUTH):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.initialized(key)
        self.adapter.build_anthropic_client.assert_not_called()

    def test_protocol_compatible_provider_keeps_its_own_key(self):
        agent = self.initialized("minimax-test-key", "minimax")
        self.assertEqual("minimax-test-key", agent.api_key)
        self.secret_reader.assert_not_called()

    def test_request_refresh_and_401_recovery_never_replace_api_key(self):
        namespace = {"get_provider_request_timeout": lambda *_: None, "logger": logging.getLogger(__name__)}
        functions("base/run_agent.py", ["_try_refresh_anthropic_client_credentials", "_request_anthropic_client_key", "_create_request_anthropic_client", "_anthropic_messages_create"], namespace)
        agent_type = type("OfflineAgent", (), {name: value for name, value in namespace.items() if name.startswith("_") and callable(value)})
        agent = agent_type()
        agent.provider, agent.model, agent.api_mode = "anthropic", "claude-test", "anthropic_messages"
        agent.api_key = agent._anthropic_api_key = KEY
        agent._anthropic_base_url = "https://api.anthropic.com"
        agent._anthropic_client = types.SimpleNamespace(api_key=KEY)
        agent._is_anthropic_oauth = False
        agent._credential_pool = Mock()
        agent._capture_anthropic_response_headers = Mock()
        agent._openai_client_lock = nullcontext
        cache = {"client": None, "in_use": False, "key": None, "poisoned": False}
        agent._request_anthropic_client_cache_ref = lambda: cache
        agent._is_openai_client_closed = lambda _: False
        client = agent._create_request_anthropic_client(reason="test")
        self.assertEqual(KEY, client.api_key)
        self.assertEqual("response", agent._anthropic_messages_create({}, client=client))
        # Production recovery functions on the 401 path must not consult the pool.
        recovery = functions("core/agent_runtime_helpers.py", ["recover_with_credential_pool"])["recover_with_credential_pool"]
        for status in (401, 429, 402):
            self.assertEqual((False, False), recovery(agent, status_code=status, has_retried_429=False))
            self.assertFalse(agent._try_refresh_anthropic_client_credentials())
        self.assertEqual("response", agent._anthropic_messages_create({}))
        self.assertEqual(KEY, agent._anthropic_api_key)
        self.assertEqual(KEY, agent.api_key)
        self.assertFalse(agent._is_anthropic_oauth)
        self.assertEqual([], agent._credential_pool.mock_calls)

    def test_pool_filters_oauth_without_reading_claude_or_modifying_saved_rows(self):
        raw = [
            {"id": "oauth", "auth_type": "oauth", "source": "claude_code", "access_token": OAUTH, "refresh_token": "fake-refresh"},
            {"id": "mislabeled", "auth_type": "api_key", "source": "manual", "access_token": OAUTH},
            {"id": "stale-env", "auth_type": "api_key", "source": "env:ANTHROPIC_API_KEY", "access_token": KEY},
            {"id": "key", "auth_type": "api_key", "source": "manual", "access_token": KEY},
        ]
        snapshot = deepcopy(raw)
        namespace = {"read_credential_pool": Mock(return_value=raw), "AUTH_TYPE_API_KEY": "api_key", "SOURCE_MANUAL": "manual", "CredentialPool": FakePool, "PooledCredential": FakeCredential,
                     "_profile_owns_pool_provider": lambda _: False}
        load = functions("core/credential_pool.py", ["load_pool"], namespace)["load_pool"]
        pool = load("anthropic")
        self.assertEqual([KEY], [entry.access_token for entry in pool.entries()])
        self.assertEqual(snapshot, raw)
        self.assertEqual({"oauth", "mislabeled", "stale-env", "key"}, pool._borrowed_root_ids)
        self.credentials.read_claude_code_credentials.assert_not_called()
        self.credentials.read_hermes_oauth_credentials.assert_not_called()

    def test_auxiliary_request_and_error_recovery_keep_the_explicit_key(self):
        namespace = {
            "load_pool": Mock(side_effect=AssertionError("pool should not be consulted")),
            "_ANTHROPIC_DEFAULT_BASE_URL": "https://api.anthropic.com",
            "_pool_runtime_base_url": lambda entry, default: default,
            "_get_aux_model_for_provider": lambda _: "claude-test", "_aux_probe_active": lambda: False,
            "AnthropicAuxiliaryClient": lambda client, model, key, base, **kw: client,
            "_normalize_aux_provider": lambda provider: provider,
            "logger": logging.getLogger(__name__),
        }
        functions("core/auxiliary_client.py", ["_try_anthropic", "_refresh_provider_credentials", "_recover_provider_pool"], namespace)
        client, model = namespace["_try_anthropic"](KEY)
        self.assertEqual(KEY, client.api_key)
        self.assertEqual("claude-test", model)
        client, _ = namespace["_try_anthropic"](KEY, "https://configured-proxy.example/anthropic")
        self.assertEqual("https://configured-proxy.example/anthropic", client.base_url)
        self.assertEqual(KEY, client.api_key)
        self.assertFalse(namespace["_refresh_provider_credentials"]("anthropic"))
        error = RuntimeError("synthetic 401")
        error.status_code = 401
        self.assertFalse(namespace["_recover_provider_pool"]("anthropic", error, failed_api_key=KEY))
        namespace["load_pool"].assert_not_called()

    def test_pool_swap_and_child_delegation_cannot_replace_native_key(self):
        agent = types.SimpleNamespace(provider="anthropic", api_key=KEY, _anthropic_api_key=KEY, _credential_pool=Mock())
        swap = functions("base/run_agent.py", ["_swap_credential"])["_swap_credential"]
        swap(agent, types.SimpleNamespace(access_token=OAUTH))
        self.assertEqual(KEY, agent.api_key)
        self.assertEqual(KEY, agent._anthropic_api_key)
        child_pool = functions("tools/delegate_tool.py", ["_resolve_child_credential_pool"])["_resolve_child_credential_pool"]
        for provider in (None, "anthropic"):
            self.assertIsNone(child_pool(provider, agent))

    def test_restore_after_fallback_keeps_snapshot_key_without_pool_lookup(self):
        pool_module = types.ModuleType("agent.credential_pool")
        pool_module.load_pool = Mock(side_effect=AssertionError("pool lookup during restore"))
        helpers = types.ModuleType("agent.chat_completion_helpers")
        helpers._reset_stale_streak = Mock()
        helpers.rewrite_prompt_model_identity = Mock()
        self.enterContext(patch.dict("sys.modules", {"agent.credential_pool": pool_module, "agent.chat_completion_helpers": helpers}))
        rt = dict(model="claude-test", provider="anthropic", base_url="https://api.anthropic.com",
                  api_mode="anthropic_messages", api_key=KEY, client_kwargs={}, use_prompt_caching=True,
                  anthropic_api_key=KEY, anthropic_base_url="https://api.anthropic.com", is_anthropic_oauth=False,
                  compressor_model="claude-test", compressor_context_length=1000, compressor_base_url="https://api.anthropic.com",
                  compressor_api_key=KEY, compressor_provider="anthropic")
        agent = types.SimpleNamespace(_fallback_activated=True, _primary_runtime=rt,
                                      _credential_pool=Mock(provider="openai-codex"), provider="openai-codex",
                                      model="fake-fallback", context_compressor=Mock(), _swap_credential=Mock())
        namespace = {"time": time, "logger": logging.getLogger(__name__),
                     "get_provider_request_timeout": lambda *_: None,
                     "resolve_runtime_pool_key": lambda provider, base: provider,
                     "credential_pool_matches_provider": lambda *a, **kw: False}
        restore = functions("core/agent_runtime_helpers.py", ["restore_primary_runtime"], namespace)["restore_primary_runtime"]
        self.assertTrue(restore(agent))
        self.assertEqual(KEY, agent.api_key)
        self.assertEqual(KEY, agent._anthropic_api_key)
        self.assertIsNone(agent._credential_pool)
        agent._swap_credential.assert_not_called()
        pool_module.load_pool.assert_not_called()

    def test_auxiliary_url_only_override_cannot_redirect_a_stored_key(self):
        entry = types.SimpleNamespace(access_token=KEY, base_url="https://key-owner.example/anthropic")
        namespace = {"load_pool": lambda _: FakePool("anthropic", [entry]),
                     "_ANTHROPIC_DEFAULT_BASE_URL": "https://api.anthropic.com",
                     "_pool_runtime_api_key": lambda value: value.access_token,
                     "_pool_runtime_base_url": lambda value, default: value.base_url if value else default,
                     "_get_aux_model_for_provider": lambda _: "claude-test", "_aux_probe_active": lambda: False,
                     "AnthropicAuxiliaryClient": lambda client, *args, **kw: client,
                     "logger": logging.getLogger(__name__)}
        create = functions("core/auxiliary_client.py", ["_try_anthropic"], namespace)["_try_anthropic"]
        client, _ = create(explicit_base_url="https://unrelated.example/anthropic")
        self.assertEqual("https://key-owner.example/anthropic", client.base_url)
        self.assertEqual(KEY, client.api_key)

    def test_model_switch_does_not_borrow_other_providers_key(self):
        namespace = {"agent": types.SimpleNamespace(api_key="previous-provider-key"),
                     "api_key": None, "new_provider": "anthropic", "old_norm": "openai", "new_norm": "anthropic",
                     "base_url": "https://api.anthropic.com"}
        with self.assertRaisesRegex(ValueError, "API key"):
            run_branch("core/agent_runtime_helpers.py", "api_mode == 'anthropic_messages'", namespace)
        self.adapter.build_anthropic_client.assert_not_called()


if __name__ == "__main__":
    unittest.main()

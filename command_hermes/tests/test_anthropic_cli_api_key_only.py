"""Native Anthropic CLI setup is API-key-only (standard-library, offline tests).

Extract the actual function ASTs so the CLI's optional runtime packages are not
required. Imports, auth stores, prompts, and writers are fakes; no real credential
files, external processes, or network requests are used.
"""

import ast
import contextlib
import io
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
API_KEY = "sk-ant-api03-offline-test-only"
OAUTH_TOKENS = ("sk-ant-oat01-offline-only", "cc-offline-only", "eyJoffline-only")


def tree(filename):
    return ast.parse((ROOT / filename).read_text(encoding="utf-8"))


def function(filename, name, **globals_):
    node = next(n for n in tree(filename).body if isinstance(n, ast.FunctionDef) and n.name == name)
    module = ast.Module(body=[
        ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0),
        node,
    ], type_ignores=[])
    namespace = dict(globals_)
    exec(compile(ast.fix_missing_locations(module), str(ROOT / filename), "exec"), namespace)
    return namespace[name]


def dict_entry(filename, name, key, **globals_):
    node = next(n for n in tree(filename).body
                if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.target.id == name)
    value = next(v for k, v in zip(node.value.keys, node.value.values) if ast.literal_eval(k) == key)
    return eval(compile(ast.Expression(value), filename, "eval"), globals_)


def module(name, **attrs):
    result = types.ModuleType(name)
    result.__dict__.update(attrs)
    return result


def is_oauth_token():
    return function("core/anthropic_credentials.py", "_is_oauth_token")


class FakePath:
    """In-memory stand-in for setup readiness paths, never touches disk."""

    def __init__(self, content=None):
        self.content = content

    def exists(self):
        return self.content is not None

    def read_text(self, **kwargs):
        return self.content

    def __truediv__(self, other):
        return FakePath()


class AnthropicCliApiKeyOnlyTest(unittest.TestCase):
    def setUp(self):
        self.modules = {
            "agent": module("agent"),
            "agent.anthropic_credentials": module(
                "agent.anthropic_credentials", _is_oauth_token=is_oauth_token()),
            "hermes_cli": module("hermes_cli"),
        }
        self.patch_modules = patch.dict(sys.modules, self.modules)
        self.patch_modules.start()
        self.addCleanup(self.patch_modules.stop)
        self.stdout = io.StringIO()
        self.redirect = contextlib.redirect_stdout(self.stdout)
        self.redirect.__enter__()
        self.addCleanup(self.redirect.__exit__, None, None, None)

    def install(self, name, **attrs):
        value = module(name, **attrs)
        # The surrounding patch restores these additions at teardown too.
        sys.modules[name] = value
        return value

    def test_registry_and_overlay_only_discover_api_key(self):
        registry = dict_entry("hermes_cli/auth.py", "PROVIDER_REGISTRY", "anthropic",
                              ProviderConfig=types.SimpleNamespace)
        overlay = dict_entry("hermes_cli/providers.py", "HERMES_OVERLAYS", "anthropic",
                             HermesOverlay=types.SimpleNamespace)
        self.assertEqual(("ANTHROPIC_API_KEY",), registry.api_key_env_vars)
        self.assertEqual("api_key", registry.auth_type)
        self.assertEqual(("ANTHROPIC_API_KEY",), overlay.extra_env_vars)

    def test_catalog_cannot_restore_oauth_environment_sources(self):
        overlay = types.SimpleNamespace(transport="anthropic_messages", is_aggregator=False,
                                        auth_type="api_key", extra_env_vars=("ANTHROPIC_API_KEY",),
                                        base_url_env_var="", base_url_override="")
        self.install("agent.models_dev", get_provider_info=lambda *a, **k: types.SimpleNamespace(
            env=["ANTHROPIC_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN"], name="Anthropic",
            api="https://api.anthropic.com", doc=""))
        get_provider = function("hermes_cli/providers.py", "get_provider",
                                normalize_provider=lambda n: n, HERMES_OVERLAYS={"anthropic": overlay},
                                ProviderDef=types.SimpleNamespace)
        self.assertEqual(("ANTHROPIC_API_KEY",), get_provider("anthropic", allow_network=False).api_key_env_vars)

    def test_key_reader_uses_only_explicit_api_key_slot(self):
        read = Mock(side_effect=lambda name: {"ANTHROPIC_API_KEY": "  " + API_KEY + "  ",
                                             "ANTHROPIC_TOKEN": OAUTH_TOKENS[0]}.get(name))
        self.install("hermes_cli.config", get_env_value_prefer_dotenv=read)
        get_key = function("hermes_cli/auth.py", "get_anthropic_key")
        self.assertEqual(API_KEY, get_key())
        read.assert_called_once_with("ANTHROPIC_API_KEY")
        for value in (None, "", *OAUTH_TOKENS):
            read.side_effect = None
            read.return_value = value
            self.assertEqual("", get_key())

    def test_auth_secret_resolution_does_not_accept_oauth_in_api_slot(self):
        self.install("hermes_cli.config", get_env_value_prefer_dotenv=lambda key: OAUTH_TOKENS[0])
        self.install("agent.credential_pool", load_pool=lambda p: None)
        resolve = function("hermes_cli/auth.py", "_resolve_api_key_provider_secret",
                           has_usable_secret=bool, _secret_matches_declared_prefix=lambda *a: True)
        cfg = types.SimpleNamespace(api_key_env_vars=("ANTHROPIC_API_KEY",))
        self.assertEqual(("", ""), resolve("anthropic", cfg))

    def command(self, **overrides):
        pool = types.SimpleNamespace(entries=Mock(return_value=[]), add_entry=Mock())
        oauth_set = next(n.value for n in tree("hermes_cli/auth_commands.py").body
                         if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and
                             t.id == "_OAUTH_CAPABLE_PROVIDERS" for t in n.targets))
        namespace = dict(
            _normalize_provider=lambda value: value.strip().lower(),
            _configured_provider_entry=Mock(return_value=None), _is_known_provider=lambda *a: True,
            _migrate_legacy_custom_pool_key=Mock(), AUTH_TYPE_API_KEY="api_key", AUTH_TYPE_OAUTH="oauth",
            CUSTOM_POOL_PREFIX="custom:", _OAUTH_CAPABLE_PROVIDERS=ast.literal_eval(oauth_set),
            load_pool=Mock(return_value=pool), masked_secret_prompt=Mock(return_value=API_KEY),
            _api_key_default_label=lambda n: "API key", _provider_base_url=lambda p: "https://api.anthropic.com",
            PooledCredential=types.SimpleNamespace, SOURCE_MANUAL="manual",
            sys=types.SimpleNamespace(stdin=types.SimpleNamespace(isatty=lambda: False)),
            uuid=types.SimpleNamespace(uuid4=lambda: types.SimpleNamespace(hex="fakeid1234")),
        )
        namespace.update(overrides)
        self.install("hermes_cli.auth", _load_auth_store=lambda: {}, unsuppress_credential_source=Mock())
        command = function("hermes_cli/auth_commands.py", "auth_add_command", **namespace)
        return command, pool, namespace

    def test_explicit_oauth_add_fails_before_any_store_or_prompt(self):
        forbidden = Mock(side_effect=AssertionError("Unexpected credential operation"))
        command, _, _ = self.command(load_pool=forbidden, _configured_provider_entry=forbidden,
                                     masked_secret_prompt=forbidden)
        with self.assertRaisesRegex(SystemExit, "OAuth is not supported"):
            command(types.SimpleNamespace(provider="anthropic", auth_type="oauth"))
        forbidden.assert_not_called()

    def test_api_key_add_defaults_to_api_key_and_keeps_other_oauth_providers(self):
        command, pool, namespace = self.command()
        command(types.SimpleNamespace(provider="anthropic", api_key=API_KEY))
        entry = pool.add_entry.call_args.args[0]
        self.assertEqual("api_key", entry.auth_type)
        self.assertEqual(API_KEY, entry.access_token)
        self.assertNotIn("anthropic", namespace["_OAUTH_CAPABLE_PROVIDERS"])
        self.assertTrue({"openai-codex", "xai-oauth", "nous"} <= namespace["_OAUTH_CAPABLE_PROVIDERS"])

    def test_oauth_disguised_as_api_key_is_rejected_before_pool_read(self):
        forbidden = Mock(side_effect=AssertionError("Unexpected store access"))
        command, _, _ = self.command(load_pool=forbidden, _configured_provider_entry=forbidden)
        for token in OAUTH_TOKENS:
            with self.subTest(token=token), self.assertRaisesRegex(SystemExit, "OAuth/setup tokens"):
                command(types.SimpleNamespace(provider="anthropic", api_key=token, auth_type="api-key"))
        forbidden.assert_not_called()

    def test_compatibility_oauth_setup_cannot_prompt_launch_or_save(self):
        writer = Mock(side_effect=AssertionError("Unexpected write"))
        flow = function("hermes_cli/main.py", "_run_anthropic_oauth_flow")
        self.assertFalse(flow(writer))
        writer.assert_not_called()
        self.assertIn("API key", self.stdout.getvalue())

    def test_config_oauth_helpers_cannot_clear_existing_key(self):
        writer = Mock()
        save_oauth = function("hermes_cli/config.py", "save_anthropic_oauth_token")
        link_claude = function("hermes_cli/config.py", "use_anthropic_claude_code_credentials")
        with self.assertRaisesRegex(ValueError, "not supported"):
            save_oauth(OAUTH_TOKENS[0], save_fn=writer)
        with self.assertRaisesRegex(ValueError, "not supported"):
            link_claude(save_fn=writer)
        writer.assert_not_called()

    def test_config_key_save_preserves_unrelated_existing_sessions(self):
        writer = Mock()
        save_key = function("hermes_cli/config.py", "save_anthropic_api_key")
        save_key(API_KEY, save_fn=writer)
        writer.assert_called_once_with("ANTHROPIC_API_KEY", API_KEY)
        for token in ("", *OAUTH_TOKENS):
            with self.assertRaisesRegex(ValueError, "API key is required"):
                save_key(token, save_fn=writer)
        self.assertEqual(1, writer.call_count)

    def wizard(self, entered_key=API_KEY, existing_key=""):
        writes, config_saves, choice_saves = Mock(), Mock(), Mock()
        selected = Mock(return_value="claude-offline-test")
        self.install("hermes_cli.auth", _prompt_model_selection=selected,
                     _save_model_choice=choice_saves, deactivate_provider=Mock(),
                     get_anthropic_key=lambda: existing_key)
        self.install("hermes_cli.config", save_env_value=Mock(), load_config=lambda: {},
                     save_config=config_saves, save_anthropic_api_key=writes)
        self.install("hermes_cli.models", _PROVIDER_MODELS={"anthropic": ["claude-offline-test"]})
        self.install("hermes_cli.secret_prompt", masked_secret_prompt=lambda prompt: entered_key)
        self.install("hermes_cli.env_loader", format_secret_source_suffix=lambda name: "")
        run = function("hermes_cli/model_setup_flows.py", "_model_flow_anthropic",
                       os=types.SimpleNamespace(getenv=lambda *a: ""),
                       _prompt_auth_credentials_choice=lambda label: "use",
                       clear_model_endpoint_credentials=lambda config: None)
        run({})
        return writes, config_saves, choice_saves, selected

    def test_wizard_accepts_api_key_then_model(self):
        writes, configs, choices, selected = self.wizard()
        self.assertEqual(API_KEY, writes.call_args.args[0])
        self.assertEqual("anthropic", configs.call_args.args[0]["model"]["provider"])
        choices.assert_called_once_with("claude-offline-test")

    def test_wizard_rejects_pasted_oauth_without_saving_or_selecting(self):
        for token in OAUTH_TOKENS:
            with self.subTest(token=token):
                for action in self.wizard(entered_key=token):
                    action.assert_not_called()

    def test_wizard_keeps_existing_api_key(self):
        writes, configs, choices, selected = self.wizard(entered_key="", existing_key=API_KEY)
        writes.assert_not_called()
        choices.assert_called_once_with("claude-offline-test")

    def readiness(self, *, env=None, dotenv=None, config=None, strict=False):
        self.install("hermes_cli.config", get_env_path=lambda: FakePath(dotenv),
                     get_hermes_home=lambda: FakePath(), load_config=lambda: config or {})
        registry = {"anthropic": types.SimpleNamespace(auth_type="api_key", api_key_env_vars=("ANTHROPIC_API_KEY",))}
        self.install("hermes_cli.auth", get_auth_status=lambda provider: {"logged_in": False},
                     PROVIDER_REGISTRY=registry)
        self.install("agent.secret_scope", current_secret_scope=lambda: env or {})
        ready = function("hermes_cli/main.py", "_has_any_provider_configured",
                         os=types.SimpleNamespace(getenv=(env or {}).get))
        return ready(strict_profile_scope=strict)

    def test_readiness_ignores_legacy_oauth_vars_and_oauth_only_model(self):
        self.assertFalse(self.readiness(env={"ANTHROPIC_TOKEN": OAUTH_TOKENS[0],
                                             "CLAUDE_CODE_OAUTH_TOKEN": OAUTH_TOKENS[0]}))
        for token in OAUTH_TOKENS:
            self.assertFalse(self.readiness(env={"ANTHROPIC_API_KEY": token}))
            self.assertFalse(self.readiness(dotenv="ANTHROPIC_API_KEY=" + token))
            self.assertFalse(self.readiness(config={"model": {"provider": "anthropic", "api_key": token}}))
        self.assertFalse(self.readiness(config={"model": {"provider": "anthropic", "default": "claude-test"}}))

    def test_readiness_accepts_api_keys_and_keeps_other_provider_behavior(self):
        self.assertTrue(self.readiness(env={"ANTHROPIC_API_KEY": API_KEY}))
        self.assertTrue(self.readiness(dotenv="ANTHROPIC_API_KEY=" + API_KEY))
        self.assertTrue(self.readiness(config={"model": {"provider": "anthropic", "api_key": API_KEY}}))
        self.assertTrue(self.readiness(env={"OPENAI_API_KEY": "fake-openai-key"}))
        self.assertTrue(self.readiness(config={"model": {"provider": "xai-oauth"}}))
        self.assertTrue(self.readiness(env={"ANTHROPIC_API_KEY": API_KEY}, strict=True))
        self.assertFalse(self.readiness(env={"ANTHROPIC_API_KEY": OAUTH_TOKENS[0]}, strict=True))

    def test_inventory_does_not_read_or_import_claude_oauth(self):
        check = function("hermes_cli/inventory.py", "_anthropic_oauth_credentials_present")
        self.assertFalse(check())
        node = next(n for n in tree("hermes_cli/inventory.py").body
                    if isinstance(n, ast.FunctionDef) and n.name == "_anthropic_oauth_credentials_present")
        self.assertFalse(any(isinstance(n, (ast.Import, ast.ImportFrom, ast.Call)) for n in ast.walk(node)))

    def test_picker_gate_is_api_key_status_only(self):
        status = Mock(return_value={"logged_in": False})
        self.install("hermes_cli.auth", get_auth_status=status)
        check = function("hermes_cli/model_switch.py", "_has_anthropic_api_key_for_listing")
        self.assertFalse(check())
        status.assert_called_once_with("anthropic")
        status.return_value = {"logged_in": True}
        self.assertTrue(check())

    def test_picker_prefetch_rejects_oauth_only_store_and_keeps_other_providers(self):
        registry = {
            "anthropic": types.SimpleNamespace(auth_type="api_key", api_key_env_vars=("ANTHROPIC_API_KEY",)),
            "openai-codex": types.SimpleNamespace(auth_type="oauth_external", api_key_env_vars=()),
            "xai-oauth": types.SimpleNamespace(auth_type="oauth_external", api_key_env_vars=()),
        }
        overlays = {key: types.SimpleNamespace(auth_type=value.auth_type, extra_env_vars=())
                    for key, value in registry.items()}
        self.install("agent.models_dev", PROVIDER_TO_MODELS_DEV={"anthropic": "anthropic"})
        self.install("hermes_cli.auth", PROVIDER_REGISTRY=registry, is_runtime_provider_routable=lambda p: True,
                     _load_auth_store=lambda: {"providers": {key: {"oauth": "fake"} for key in registry}})
        self.install("hermes_cli.providers", HERMES_OVERLAYS=overlays, ALIASES={})
        self.install("hermes_cli.models", _AGGREGATOR_PROVIDERS=set(),
                     CANONICAL_PROVIDERS=[types.SimpleNamespace(slug="anthropic")])
        self.install("providers", get_provider_profile=lambda name: None)
        collect = function("hermes_cli/model_switch.py", "_collect_authed_provider_slugs",
                           _has_anthropic_api_key_for_listing=lambda: False,
                           _scoped_key_env=lambda name: OAUTH_TOKENS[0],
                           _credential_pool_is_usable=lambda *a, **k: False)
        with patch.dict("os.environ", {}, clear=True):
            slugs = collect({"anthropic": {"env": ["ANTHROPIC_API_KEY"]}}, {}, [])
        self.assertEqual({"openai-codex", "xai-oauth"}, set(slugs))

    def test_direct_setup_and_picker_do_not_reference_oauth_readers_or_login(self):
        forbidden = {"read_claude_code_credentials", "read_hermes_oauth_credentials",
                     "run_oauth_setup_token", "run_hermes_oauth_login_pure"}
        for filename in ("model_setup_flows.py", "model_switch.py", "main.py", "auth_commands.py"):
            names = {n.id for n in ast.walk(tree("hermes_cli/" + filename)) if isinstance(n, ast.Name)}
            imported = {n.name for n in ast.walk(tree("hermes_cli/" + filename)) if isinstance(n, ast.alias)}
            self.assertFalse(forbidden & (names | imported), filename)
        for name in ("_collect_authed_provider_slugs", "list_authenticated_providers"):
            fn = next(n for n in tree("hermes_cli/model_switch.py").body if isinstance(n, ast.FunctionDef) and n.name == name)
            gates = [n for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                     and n.func.id == "_has_anthropic_api_key_for_listing"]
            self.assertEqual(3, len(gates), name)


if __name__ == "__main__":
    unittest.main()

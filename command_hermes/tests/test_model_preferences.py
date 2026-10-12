# -*- coding: utf-8 -*-
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026

"""same/same の復元と初期画面を、実際の設定ファイル・描画処理で検証する。"""
from contextlib import redirect_stdout
from datetime import datetime
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import command_hermes.cli_main as cli
from hermes_cli import aidiy_model_preferences as preferences
from hermes_cli.banner import build_welcome_banner
from rich.console import Console


class ModelPreferencesTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.enterContext(patch.object(preferences, 'get_hermes_home', return_value=self.home))
        self.keys = self.home / 'AiDiy_key.json'
        self.keys.write_text(json.dumps({'openai_key_id': 'test-key', 'freeai_key_id': 'test-key'}), encoding='utf-8')
        self.enterContext(patch.object(cli, '_AIDIY_KEY_JSON', self.keys))

    def invoke(self, args):
        with patch.object(cli, 'main') as main:
            self.assertEqual(cli.cli_entry(args), 0)
        return main.call_args.kwargs

    def test_explicit_launch_then_same_same_restores_provider_model_and_current_key(self):
        self.invoke(['--provider', 'openai', '--model', 'gpt-6.1-sol'])
        self.keys.write_text(json.dumps({'openai_key_id': 'updated-key'}), encoding='utf-8')
        for flags in (['--provider', 'same', '--model', 'same'], ['--model', 'same/same']):
            with self.subTest(flags=flags):
                restored = self.invoke(flags)
                self.assertEqual(restored['provider'], 'custom')
                self.assertEqual(restored['model'], 'gpt-6.1-sol')
                self.assertEqual(restored['base_url'], cli._OPENAI_BASE_URL)
                self.assertEqual(restored['api_key'], 'updated-key')
        saved = json.loads((self.home / 'aidiy_model.json').read_text(encoding='utf-8'))
        self.assertEqual(saved, {'provider': 'openai', 'model': 'gpt-6.1-sol'})

    def test_picker_choice_is_restored_on_next_launch(self):
        instance = cli.HermesCLI.__new__(cli.HermesCLI)
        instance._aidiy_config = {'freeai_key_id': 'test-key'}
        instance._aidiy_provider_slug = None
        instance._aidiy_remember_model_selection = True
        instance.provider = instance.requested_provider = 'auto'
        instance.base_url = instance.api_key = ''
        instance.model = ''
        entry = instance._get_aidiy_provider_entry('freeai')
        with patch.object(cli, '_cprint'):
            instance._apply_aidiy_provider_model(entry, 'gemini-3.8-flash')
        restored = self.invoke(['--provider', 'same', '--model', 'same'])
        self.assertEqual(restored['provider'], 'custom')
        self.assertEqual(restored['model'], 'gemini-3.8-flash')
        self.assertEqual(restored['base_url'], cli._GEMINI_OPENAI_BASE_URL)

    def test_explicit_auto_auto_does_not_restore_or_overwrite_previous(self):
        preferences.save_model_choice('codex-cli', 'gpt-6-astra')
        for flags in (['--provider', 'auto', '--model', 'auto'], ['--model', 'auto/auto']):
            with self.subTest(flags=flags):
                result = self.invoke(flags)
                self.assertIsNone(result['model'])
                self.assertIsNone(result['provider'])
        self.assertEqual(preferences.load_model_choice()['model'], 'gpt-6-astra')

    def test_omitted_interactive_arguments_restore_previous_but_quiet_keeps_native_auto(self):
        preferences.save_model_choice('copilot-cli', 'gpt-6-astra')
        for flags in ([], ['--compact']):
            with self.subTest(flags=flags):
                result = self.invoke(flags)
                self.assertEqual(result['provider'], 'copilot-cli')
                self.assertEqual(result['model'], 'gpt-6-astra')
        result = self.invoke(['-Q', '-z', '質問'])
        self.assertIsNone(result['provider'])
        self.assertIsNone(result['model'])

    def test_explicit_session_or_endpoint_does_not_restore_unrelated_cli(self):
        preferences.save_model_choice('copilot-cli', 'auto')
        for flags in (['--resume', 'saved-session'], ['--base-url', 'http://127.0.0.1:8096/v1'], ['--api-key', 'explicit-key']):
            with self.subTest(flags=flags):
                result = self.invoke(flags)
                self.assertIsNone(result['provider'])
                self.assertIsNone(result['model'])

    def test_copilot_auto_picker_then_bare_launch_restores_and_displays_cli(self):
        def instance():
            value = cli.HermesCLI.__new__(cli.HermesCLI)
            value._aidiy_config = {}
            value._aidiy_provider_slug = None
            value._aidiy_remember_model_selection = True
            value.provider = value.requested_provider = 'auto'
            value.base_url = value.api_key = value.model = ''
            value.agent = None
            value.enabled_toolsets = []
            value._provider_source = None
            value.session_id = 'test-startup'
            value.compact = False
            return value

        previous = instance()
        with patch.object(cli, '_cprint'):
            previous._apply_aidiy_provider_model(previous._get_aidiy_provider_entry('copilot-cli'), 'auto')
        restored = self.invoke([])
        self.assertEqual(restored['provider'], 'copilot-cli')
        self.assertIsNone(restored['model'])
        current = instance()
        with patch.object(cli, '_cprint'):
            self.assertTrue(cli._configure_aidiy_cli_provider(current, restored['provider'], requested_model=restored['model']))
        self.assertEqual(current.model, 'auto')
        for width in (60, 80, 120):
            with self.subTest(width=width), redirect_stdout(io.StringIO()):
                output = io.StringIO()
                current.console = Console(file=output, width=width, color_system=None)
                current._console_print = current.console.print
                snapshot = {'tools': [], 'toolset_map': {}, 'availability': {}, 'skills_by_category': {}}
                with patch.dict(cli.os.environ, {'HERMES_DEFER_AGENT_STARTUP': '1'}), patch.object(cli.shutil, 'get_terminal_size', return_value=os.terminal_size((width, 30))), patch('hermes_cli.banner.load_banner_snapshot', return_value=snapshot), patch.object(cli.threading, 'Thread'):
                    current.show_banner()
                rendered = output.getvalue()
                self.assertIn('copilot-cli (auto)', rendered)
                self.assertNotIn('自動選択', rendered)
                self.assertNotIn('unknown', rendered.lower())

    def test_external_cli_keeps_same_and_explicit_model_semantics(self):
        for model in ('same', 'auto', 'gpt-6-astra'):
            with self.subTest(model=model):
                preferences.save_model_choice('codex-cli', model)
                result = self.invoke(['--model', 'same/same'])
                self.assertEqual(result['provider'], 'codex-cli')
                self.assertEqual(result['model'], 'gpt-6-astra' if model == 'gpt-6-astra' else None)

    def test_quiet_code_execution_does_not_replace_manual_selection(self):
        preferences.save_model_choice('codex-cli', 'gpt-6-astra')
        self.invoke(['-Q', '-z', '質問', '--provider', 'freeai', '--model', 'gemini-3.8-flash'])
        self.assertEqual(preferences.load_model_choice(), {'provider': 'codex-cli', 'model': 'gpt-6-astra'})

    def test_code_ai_same_command_restores_previous_hermes_choice(self):
        from backend_server.tests.test_code_cli_output_routing import _load_code_ai_module
        code = _load_code_ai_module().CodeAI(AI_NAME='aidiy_hermes', AI_MODEL='same')
        preferences.save_model_choice('codex-cli', 'gpt-6-astra')
        with patch.dict(cli.os.environ, {'AIDIY_HERMES_CLI_PATH': 'aidiy_hermes'}):
            command = code._コマンド構築('検索依頼')
        with patch.object(cli.sys, 'stdin', io.StringIO('検索依頼')):
            restored = self.invoke(command[1:])
        self.assertEqual(restored['provider'], 'codex-cli')
        self.assertEqual(restored['model'], 'gpt-6-astra')
        self.assertEqual(restored['query'], '検索依頼')
        self.assertTrue(restored['quiet'])

    def test_missing_broken_or_ignored_preferences_fall_back_to_native_config(self):
        for content in (None, '{broken', '[]', '{"provider":"same","model":"same"}'):
            with self.subTest(content=content):
                if content is not None:
                    (self.home / 'aidiy_model.json').write_text(content, encoding='utf-8')
                result = self.invoke(['--model', 'same/same'])
                self.assertIsNone(result['provider'])
                self.assertIsNone(result['model'])
        preferences.save_model_choice('codex-cli', 'gpt-6-astra')
        result = self.invoke(['--model', 'same/same', '--ignore-user-config'])
        self.assertIsNone(result['model'])

    def test_failed_save_preserves_previous_complete_file(self):
        preferences.save_model_choice('codex-cli', 'gpt-6-astra')
        with patch.object(preferences.os, 'replace', side_effect=OSError('blocked')):
            self.assertFalse(preferences.save_model_choice('freeai', 'gemini-3.8-flash'))
        self.assertEqual(preferences.load_model_choice()['provider'], 'codex-cli')
        self.assertEqual(list(self.home.glob('*.tmp')), [])

    def test_unconfigured_status_bar_and_compact_banner_have_no_unknown(self):
        instance = cli.HermesCLI.__new__(cli.HermesCLI)
        instance.model, instance.provider, instance.api_key = '', 'auto', None
        instance.enabled_toolsets, instance._provider_source = [], None
        instance.session_start = datetime.now()
        instance._get_status_bar_session_title = Mock(return_value='')
        instance._console_print = Mock()
        with patch.dict(cli.os.environ, {'HERMES_DEFER_AGENT_STARTUP': '1'}):
            instance._show_status()
        self.assertIn('自動選択', instance._console_print.call_args.args[0])
        snapshot = instance._get_status_bar_snapshot()
        self.assertEqual(snapshot['model_short'], '自動選択')
        self.assertEqual(instance.model, '')
        instance._aidiy_provider_slug = 'codex-cli'
        for model in ('auto', 'same'):
            instance.model = model
            self.assertEqual(instance._get_status_bar_snapshot()['model_short'], 'Codex CLI')

    def test_initial_full_banner_renders_auto_and_restored_model_at_terminal_widths(self):
        for width in (80, 120):
            for model in ('', 'gpt-6.1-sol'):
                with self.subTest(width=width, model=model), redirect_stdout(io.StringIO()):
                    output = io.StringIO()
                    console = Console(file=output, width=width, color_system=None)
                    build_welcome_banner(console, preferences.model_display_name(model), cwd='C:/Users/tester/AiDiy2026',
                                         tools=[], enabled_toolsets=[], get_toolset_for_tool=lambda name: 'other',
                                         availability={}, skills_by_category={})
                    rendered = output.getvalue()
                    self.assertIn(model or '自動選択', rendered)
                    self.assertNotIn('unknown', rendered.lower())
                    self.assertNotIn('no model configured', rendered)


if __name__ == '__main__':
    unittest.main()

"""DiagのCode一覧からHermesの選択・CLI引数までを外部通信なしで確認する。"""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import command_hermes.cli_main as cli


class CodeModelCatalogTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.file = root / '_AIDIY/aidiy_diag/code_models_info.json'
        self.file.parent.mkdir(parents=True)
        patcher = patch.object(cli, '_AIDIY_CONFIG_DIR', root / '_config')
        patcher.start()
        self.addCleanup(patcher.stop)
        self.instance = cli.HermesCLI.__new__(cli.HermesCLI)
        self.instance._aidiy_config = {}

    def write(self, payload):
        self.file.write_text(json.dumps(payload), encoding='utf-8-sig')

    def test_all_cli_choices_follow_catalog_with_same_first_and_refresh(self):
        for provider, key in cli._AIDIY_CODE_CATALOG_KEYS.items():
            if provider == 'openai_oauth':
                continue
            with self.subTest(provider=provider):
                self.write({key: {'models': {'auto':'auto', 'same':'same', 'openai/custom':'日付 - openai/custom', 'other':'Other'}}})
                entry = self.instance._get_aidiy_provider_entry(provider, include_models=True)
                self.assertEqual(entry['models'], [('same (変更なし)', 'same'), ('日付 - openai/custom', 'openai/custom'), ('Other', 'other')])
                self.assertEqual(entry['default_model'], 'same')
                self.assertEqual(entry['total_models'], 3)
                self.write({key: {'models': {'new':'New'}}})
                self.assertEqual(self.instance._get_aidiy_provider_entry(provider)['models'][-1], ('New', 'new'))

    def test_missing_or_invalid_catalog_keeps_only_same_for_cli(self):
        for content in (None, '{bad', '[]', '{}', '{"codex_cli":{"models":[]}}'):
            if content is not None:
                self.file.write_text(content, encoding='utf-8')
            entry = self.instance._get_aidiy_provider_entry('codex-cli', True)
            self.assertEqual(entry['models'], [('same (変更なし)', 'same')])

    def test_oauth_uses_hermes_section_and_strips_only_route_prefix(self):
        self.write({'aidiy_hermes': {'models': {'copilot_cli/same':'CLI', 'openai_oauth/gpt-future-sol':'Future', 'openai_oauth/gpt-future-luna':'Light'}}})
        with patch.object(cli.HermesCLI, '_fetch_aidiy_codex_model_labels', side_effect=AssertionError('network')):
            entry = self.instance._get_aidiy_provider_entry('openai_oauth', True)
        self.assertEqual(entry['models'], [('Future', 'gpt-future-sol'), ('Light', 'gpt-future-luna')])
        self.assertEqual(entry['default_model'], 'gpt-future-sol')

    def test_cli_picker_opens_model_stage_instead_of_applying_auto(self):
        self.write({'codex_cli': {'models': {'gpt-future-sol':'Future'}}})
        entry = self.instance._get_aidiy_provider_entry('codex-cli', True)
        self.instance._model_picker_state = {'source':'aidiy','stage':'provider','selected':0,'providers':[entry]}
        self.instance._invalidate = Mock()
        self.instance._close_model_picker = Mock()
        self.instance._apply_aidiy_provider_model = Mock()
        self.instance._handle_model_picker_selection()
        self.assertEqual(self.instance._model_picker_state['stage'], 'model')
        self.assertEqual(self.instance._model_picker_state['model_list'], entry['models'])
        self.instance._apply_aidiy_provider_model.assert_not_called()
        self.instance._handle_model_picker_selection()
        self.instance._apply_aidiy_provider_model.assert_called_once_with(entry, 'same')

    def test_same_and_legacy_auto_omit_model_for_every_cli(self):
        with patch.object(cli, '_aidiy_cli_command_path', return_value='fixture'), patch.object(cli, '_aidiy_cli_code_permissions', return_value='none'):
            for provider in cli._AIDIY_CLI_PROVIDERS:
                for initial in (True, False):
                    for model in ('same', 'auto', None):
                        command = cli._aidiy_cli_build_command(provider['slug'], '質問', initial, '/repo', model)
                        self.assertNotIn('--model', command)
                    command = cli._aidiy_cli_build_command(provider['slug'], '質問', initial, '/repo', 'openai/custom')
                    self.assertEqual(command[command.index('--model')+1], 'openai/custom')

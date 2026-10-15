import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
def load(name):
    spec=importlib.util.spec_from_file_location('diag_'+name,ROOT/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
setup=load('_setup');cleanup=load('_cleanup')
class LauncherTests(unittest.TestCase):
    def test_launch_has_node_prerequisite_no_python_runtime(self):
        shell=setup.launcher_content('/space dir/diag_main.mjs',False)
        self.assertIn('command -v node',shell);self.assertIn("'/space dir/diag_main.mjs'",shell);self.assertIn('"$@"',shell);self.assertNotIn('python',shell)
        windows=setup.launcher_content('C:\\space dir\\diag_main.mjs',True)
        self.assertIn('where node.exe',windows);self.assertIn('%*',windows);self.assertIn('%ERRORLEVEL%',windows)
    def test_special_checkout_paths(self):
        windows=setup.launcher_content('C:\\repo%TEST%\\diag_main.mjs',True)
        self.assertIn('repo%%TEST%%',windows);self.assertIn('setlocal DisableDelayedExpansion',windows)
        shell=setup.launcher_content("/tmp/it's repo/diag_main.mjs",False)
        self.assertIn('aidiy_diag-owner:',shell)
    def test_cleanup_ownership(self):
        with tempfile.TemporaryDirectory() as directory,patch.object(Path,'home',return_value=Path(directory)),patch.object(cleanup,'__file__',str(Path(directory)/'_cleanup.py')):
            folder=Path(directory)/'.local/bin';folder.mkdir(parents=True)
            launcher=folder/'aidiy_diag';launcher.write_text('another checkout')
            self.assertTrue(cleanup.cleanup());self.assertTrue(launcher.exists())
            launcher.write_text(setup.launcher_content(Path(directory)/'diag_main.mjs',False))
            self.assertTrue(cleanup.cleanup());self.assertFalse(launcher.exists())

class RootIntegrationTests(unittest.TestCase):
    def root_module(self,name):
        spec=importlib.util.spec_from_file_location('root_diag_test_'+name,ROOT.parent/(name+'.py'))
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
    def test_setup_auto_includes_diag_first(self):
        module=self.root_module('_setup');calls=[]
        original=module.ask_yes_no
        def ask(prompt,default='n'):
            calls.append((prompt,default));return original(prompt,default)
        with patch.object(module,'ask_start_mode',return_value=(True,True)),patch.object(module,'ask_yes_no',side_effect=ask),patch('builtins.print'):
            choices=module.collect_setup_choices()
        self.assertTrue(choices['diag']);self.assertIn('Diag',calls[0][0]);self.assertEqual(calls[0][1],'y')
    def test_cleanup_auto_includes_diag_first(self):
        module=self.root_module('_cleanup');calls=[];original=module.ask_yes_no
        def ask(prompt,default='n'):
            calls.append((prompt,default));return original(prompt,default)
        with tempfile.TemporaryDirectory() as directory,patch.object(module,'ask_start_mode',return_value=(True,True)),patch.object(module,'ask_yes_no',side_effect=ask),patch('builtins.print'):
            choices=module.collect_cleanup_choices(Path(directory))
        self.assertTrue(choices['diag']);self.assertIn('Diag',calls[0][0]);self.assertEqual(calls[0][1],'y')
    def test_manual_decline_diag(self):
        for name,method in [('_setup','collect_setup_choices'),('_cleanup','collect_cleanup_choices')]:
            module=self.root_module(name)
            with patch.object(module,'ask_start_mode',return_value=(True,False)),patch.object(module,'ask_yes_no',return_value=False),patch('builtins.print'):
                choices=getattr(module,method)(ROOT.parent) if name=='_cleanup' else getattr(module,method)()
            self.assertFalse(choices['diag'])
    def test_start_choice_precedes_term_and_defaults_off(self):
        module=self.root_module('_start');calls=[]
        def choice(prompt,default_yes=False):
            calls.append((prompt,default_yes));return 'Diag' in prompt
        with patch.object(module,'prompt_choice',side_effect=choice),patch('builtins.print'):
            values=module.collect_startup_choices()
        self.assertEqual(len(values),12);self.assertTrue(values[6]);self.assertIn('Diag',calls[6][0]);self.assertIn('Term',calls[7][0]);self.assertFalse(calls[6][1])
    def test_diag_only_start_no_core_dependency_or_auto_restart(self):
        module=self.root_module('_start');started=[]
        with patch.object(module,'stop_all_tasks'),patch.object(module,'wait_for_services_quiet'),patch.object(module,'start_service',side_effect=lambda name,*args:started.append(name) or True),patch('builtins.print'):
            flags=module.start_initial_services(False,False,False,False,False,False,{}, {},None,diag_enabled=True)
        self.assertEqual(started,['フロントエンド(diag)']);self.assertFalse(flags['フロントエンド(diag)'])

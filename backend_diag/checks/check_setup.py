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
    def test_setup_common_then_diag_in_manual_and_auto_modes(self):
        for auto in (False,True):
            with self.subTest(auto=auto):
                module=self.root_module('_setup');calls=[]
                original=module.ask_yes_no
                def ask(prompt,default='n'):
                    calls.append((prompt,default));return original(prompt,default)
                with patch.object(module,'ask_start_mode',return_value=(True,auto)),patch.object(module,'ask_yes_no',side_effect=ask),patch.object(module,'_read_single_key',side_effect=lambda valid,default_key:default_key),patch('builtins.print'):
                    choices=module.collect_setup_choices()
                self.assertEqual([prompt for prompt,_ in calls[:3]],[
                    '共通セットアップを実行しますか？',
                    '共通: グローバル環境 Python ツールをアップグレードしますか？',
                    '共通: グローバル環境の AI CLI ツール(npm + Antigravity + Grok Build)をインストール/アップデートしますか？',
                ])
                self.assertEqual([default for _,default in calls[:3]],['y','y','n'])
                self.assertFalse(any('Diag' in prompt for prompt,_ in calls))
                self.assertTrue(choices['common']);self.assertTrue(choices['diag'])
                self.assertTrue(choices['common_python_upgrade']);self.assertFalse(choices['common_npm_install'])
                self.assertEqual(module.AUTO_MODE,auto)
    def test_setup_target_numbers_common_zero_diag_one(self):
        module=self.root_module('_setup')
        with patch.object(module,'collect_setup_choices',return_value=None),patch.object(module,'print_info') as info,patch('builtins.print'):
            with self.assertRaises(SystemExit):module.main()
        targets=[call.args[0].strip() for call in info.call_args_list if call.args[0].strip()[:1].isdigit()]
        self.assertEqual(targets,[
            '0. 共通','1. バックエンド(Diag)','2. バックエンド(local)',
            '3. バックエンド(tools)','4. バックエンド(core,apps)',
            '5. バックエンド(task,team)','6. フロントエンド(Web)',
            '7. フロントエンド(Avatar)','8. コマンド(hermes)',
            '9. IDE群(Term / Code / Live / IDE)','10. フロントエンド(Discord、任意)',
        ])
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
            self.assertEqual(choices['diag'], name == '_setup')
    def test_start_has_no_diag_choice(self):
        module=self.root_module('_start');calls=[]
        def choice(prompt,default_yes=False):
            calls.append((prompt,default_yes));return 'Diag' in prompt
        with patch.object(module,'prompt_choice',side_effect=choice),patch('builtins.print'):
            values=module.collect_startup_choices()
        self.assertEqual(len(values),12)
        self.assertFalse(values[6])
        self.assertFalse(any('Diag' in prompt for prompt,_ in calls))
        self.assertIn('Term',calls[6][0])

    def test_headless_always_runs_before_start_choices(self):
        from types import SimpleNamespace
        module=self.root_module('_start');events=[]
        diag=SimpleNamespace(run_headless=lambda:events.append('headless'))
        with patch.object(module,'_init_modules'),patch.object(module,'DIAG',diag,create=True),patch.object(module,'collect_startup_choices',side_effect=lambda:events.append('choices') or (_ for _ in ()).throw(KeyboardInterrupt)),patch('builtins.print'):
            with self.assertRaises(KeyboardInterrupt):module.main()
        self.assertEqual(events,['headless','choices'])

    def test_headless_failure_stops_startup(self):
        from types import SimpleNamespace
        module=self.root_module('_start')
        diag=SimpleNamespace(run_headless=lambda:(_ for _ in ()).throw(RuntimeError('failed')))
        with patch.object(module,'_init_modules'),patch.object(module,'DIAG',diag,create=True),patch.object(module,'collect_startup_choices') as choices,patch('builtins.print'):
            with self.assertRaises(SystemExit) as result:module.main()
            self.assertEqual(result.exception.code,1)
            choices.assert_not_called()

    def test_headless_command_and_nonzero_exit(self):
        from types import SimpleNamespace
        module=load('_start')
        with patch.object(module.shutil,'which',return_value='node'),patch.object(module.subprocess,'run',return_value=SimpleNamespace(returncode=0)) as run:
            module.run_headless()
            self.assertEqual(run.call_args.args[0],['node',str(ROOT/'diag_main.mjs'),'--headless'])
            self.assertEqual(run.call_args.kwargs['cwd'],ROOT)
            run.return_value.returncode=1
            with self.assertRaises(RuntimeError):module.run_headless()
    def test_diag_only_start_no_core_dependency_or_auto_restart(self):
        module=self.root_module('_start');started=[]
        with patch.object(module,'stop_all_tasks'),patch.object(module,'wait_for_services_quiet'),patch.object(module,'start_service',side_effect=lambda name,*args:started.append(name) or True),patch('builtins.print'):
            flags=module.start_initial_services(False,False,False,False,False,False,{}, {},None,diag_enabled=True)
        self.assertEqual(started,['バックエンド(Diag)']);self.assertFalse(flags['バックエンド(Diag)'])

class SetupOrderingTests(unittest.TestCase):
    root_module = RootIntegrationTests.root_module
    def test_diag_installed_before_prerequisite_failure_without_node(self):
        module=self.root_module('_setup');events=[]
        choices={'diag':True,'continue_on_error':True}
        def prerequisites():
            events.append('prerequisites')
            self.assertFalse(module.AUTO_MODE)
            raise RuntimeError('prerequisite failure')
        def loader(folder):
            self.assertEqual(folder,'backend_diag')
            return setup
        with tempfile.TemporaryDirectory() as directory,patch.object(Path,'home',return_value=Path(directory)),patch.dict('os.environ',{'PATH':''}),patch.object(module,'AUTO_MODE',True),patch.object(module,'collect_setup_choices',return_value=choices),patch.object(module,'_load_folder_module',side_effect=loader),patch.object(module,'ensure_prerequisites',side_effect=prerequisites),patch('builtins.print'):
            with self.assertRaisesRegex(RuntimeError,'prerequisite failure'):
                module.main()
            launcher=Path(directory)/'.local/bin'/('aidiy_diag.cmd' if setup.sys.platform=='win32' else 'aidiy_diag')
            self.assertTrue(launcher.exists())
            self.assertTrue(module.AUTO_MODE)
        self.assertEqual(events,['prerequisites'])
    def test_cancel_does_not_check_or_install_prerequisites(self):
        module=self.root_module('_setup')
        with patch.object(module,'collect_setup_choices',return_value=None),patch.object(module,'ensure_prerequisites') as prerequisites,patch('builtins.print'):
            with self.assertRaises(SystemExit):module.main()
            prerequisites.assert_not_called()
    def test_cleanup_backup_then_diag_after_safe_service_stop(self):
        module=self.root_module('_cleanup');events=[]
        def folder(name,choices):
            events.append(name)
            raise RuntimeError('stop test before unrelated cleanup')
        with patch.object(module,'stop_all_services',side_effect=lambda *_:events.append('stop')),patch.object(module,'_run_folder_cleanup',side_effect=folder),patch.object(module,'cleanup_backup',side_effect=lambda *_:events.append('backup')),patch('builtins.print'):
            with self.assertRaisesRegex(RuntimeError,'stop test'):
                module.execute_cleanup(ROOT.parent,{'diag':True,'npm_uninstall':False})
        self.assertEqual(events,['stop','backup','backend_diag'])
    def test_cleanup_stop_failure_prevents_deletion(self):
        module=self.root_module('_cleanup')
        with patch.object(module,'stop_all_services',side_effect=RuntimeError('unsafe')),patch.object(module,'_run_folder_cleanup') as folder,patch('builtins.print'):
            with self.assertRaisesRegex(RuntimeError,'unsafe'):
                module.execute_cleanup(ROOT.parent,{'diag':True})
            folder.assert_not_called()
    def test_manual_default_accepts_diag(self):
        for name,method in [('_setup','collect_setup_choices'),('_cleanup','collect_cleanup_choices')]:
            module=self.root_module(name)
            with patch.object(module,'ask_start_mode',return_value=(True,False)),patch.object(module,'_read_single_key',side_effect=lambda valid,default_key:default_key),patch('builtins.print'):
                choices=getattr(module,method)(ROOT.parent) if name=='_cleanup' else getattr(module,method)()
            self.assertTrue(choices['diag'])


class ElectronSetupTests(unittest.TestCase):
    def test_browser_environment_skips_electron_installs(self):
        with patch.dict('os.environ',{'CODESPACES':'true'}),patch.object(setup.shutil,'which') as which,patch('builtins.print'):
            self.assertTrue(setup.setup_desktop());which.assert_not_called()
    def test_desktop_uses_shared_helper(self):
        from types import SimpleNamespace
        calls=[]
        helper=SimpleNamespace(setup_dependencies=lambda *args: calls.append(args) or True)
        spec=SimpleNamespace(loader=SimpleNamespace(exec_module=lambda module:None))
        with patch.dict('os.environ',{'CODESPACES':'false','DISPLAY':':fixture'}),patch.object(setup.shutil,'which',return_value='/mock/npm'),patch.object(setup.importlib.util,'spec_from_file_location',return_value=spec) as load,patch.object(setup.importlib.util,'module_from_spec',return_value=helper),patch('builtins.print'):
            self.assertTrue(setup.setup_desktop())
        self.assertEqual(load.call_args.args[1],ROOT.parent/'scripts'/'_setup_electron.py')
        self.assertEqual(calls[0][0],ROOT)
    def test_missing_node_keeps_launcher_but_desktop_setup_fails(self):
        with tempfile.TemporaryDirectory() as directory,patch.object(Path,'home',return_value=Path(directory)),patch.dict('os.environ',{'CODESPACES':'false','DISPLAY':':fixture'}),patch.object(setup.shutil,'which',return_value=None),patch('builtins.print'):
            self.assertFalse(setup.setup())
            self.assertTrue((Path(directory)/'.local/bin'/('aidiy_diag.cmd' if setup.sys.platform=='win32' else 'aidiy_diag')).exists())
    def test_shared_dist_reused_both_directions_without_download(self):
        import json
        spec=importlib.util.spec_from_file_location('diag_test_shared_electron',ROOT.parent/'scripts'/'_setup_electron.py')
        shared=importlib.util.module_from_spec(spec);spec.loader.exec_module(shared)
        for source_name,target_name in [('backend_diag','frontend_avatar'),('frontend_avatar','backend_diag')]:
            with tempfile.TemporaryDirectory() as directory:
                base=Path(directory);source=base/source_name/'node_modules/electron/dist';source.mkdir(parents=True)
                exe=source/shared.electron_executable_name();exe.parent.mkdir(parents=True,exist_ok=True);exe.write_text('fixture')
                (source/'version').write_text('44.7.0')
                target=base/target_name;(target/'node_modules/electron').mkdir(parents=True)
                (target/'node_modules/electron/package.json').write_text(json.dumps({'version':'44.7.0'}))
                with patch.object(shared,'_download_archive') as download,patch('builtins.print'):
                    self.assertTrue(shared.prepare_electron_binary(target,'fixture',allow_download=False,info=lambda *_:None))
                    download.assert_not_called()
                self.assertTrue(shared.electron_binary_ready(target))

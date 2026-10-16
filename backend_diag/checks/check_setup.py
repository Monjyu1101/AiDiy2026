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

    def test_start_choices_do_not_run_headless(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        module=self.root_module('_start');diag=SimpleNamespace(run_headless=Mock())
        with patch.object(module,'_init_modules'),patch.object(module,'DIAG',diag),patch.object(module,'collect_startup_choices',side_effect=KeyboardInterrupt),patch('builtins.print'):
            with self.assertRaises(KeyboardInterrupt):module.main()
        diag.run_headless.assert_not_called()

    def test_tools_diagnosis_order_selection_and_cleanup_skip(self):
        from types import SimpleNamespace
        for enabled,blocked in [(False,False),(True,False),(True,True)]:
            with self.subTest(enabled=enabled,blocked=blocked):
                module=self.root_module('_start');events=[]
                diag=SimpleNamespace(run_headless=lambda:events.append('diag'))
                def service(name):
                    events.append(name);return object()
                with patch.object(module,'DIAG',diag),patch.object(module,'TOOLS',SimpleNamespace(start=lambda:service('tools'))),patch.object(module,'LOCAL',SimpleNamespace(start=lambda:service('local'))),patch.object(module,'SERVER',SimpleNamespace(start_core=lambda:service('core'),start_apps=lambda:service('apps'))),patch.object(module,'stop_all_tasks'),patch.object(module,'cleanup_stop_requested_services',return_value={'バックエンド(tools)'} if blocked else set()),patch.object(module,'attach_output_thread'),patch.object(module,'wait_for_services_quiet'),patch('builtins.print'):
                    module.start_initial_services(True,enabled,True,False,False,False,{}, {},None)
                self.assertEqual(events,['local','diag','tools','core','apps'] if enabled and not blocked else ['local','core','apps'])

    def test_tools_restart_runs_diagnosis_once_per_launch(self):
        from types import SimpleNamespace
        module=self.root_module('_start');events=[]
        with patch.object(module,'DIAG',SimpleNamespace(run_headless=lambda:events.append('diag'))),patch.object(module,'TOOLS',SimpleNamespace(start=lambda:events.append('tools') or object())),patch.object(module,'cleanup_stop_requested_services',return_value=set()),patch.object(module,'attach_output_thread'),patch('builtins.print'):
            for _ in range(2):self.assertTrue(module.start_service('バックエンド(tools)',{}, {},None))
        self.assertEqual(events,['diag','tools','diag','tools'])

    def test_headless_failure_stops_startup_and_cleans_started_processes(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        for error in (RuntimeError('failed'),OSError('failed')):
            with self.subTest(error=type(error)):
                module=self.root_module('_start');tools=SimpleNamespace(start=Mock());local_process=object()
                with patch.object(module,'_init_modules'),patch.object(module,'DIAG',SimpleNamespace(run_headless=Mock(side_effect=error))),patch.object(module,'TOOLS',tools),patch.object(module,'LOCAL',SimpleNamespace(start=lambda:local_process)),patch.object(module,'collect_startup_choices',return_value=(True,True)+(False,)*10),patch.object(module,'validate_initial_environment',return_value=(True,None)),patch.object(module,'stop_all_tasks'),patch.object(module,'cleanup_stop_requested_services',return_value=set()),patch.object(module,'attach_output_thread'),patch.object(module,'wait_for_services_quiet'),patch.object(module,'stop_processes') as stop,patch.object(module,'monitor_and_restart') as monitor,patch('builtins.print'):
                    with self.assertRaises(SystemExit) as result:module.main()
                self.assertEqual(result.exception.code,1);tools.start.assert_not_called();monitor.assert_not_called()
                stop.assert_called_once_with({'バックエンド(local)':local_process})

    def test_main_runs_diagnosis_once_only_when_tools_selected(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        for enabled in (False,True):
            module=self.root_module('_start');diag=SimpleNamespace(run_headless=Mock())
            with patch.object(module,'_init_modules'),patch.object(module,'DIAG',diag),patch.object(module,'TOOLS',SimpleNamespace(start=Mock(return_value=object()),PORT_TOOLS=8095)),patch.object(module,'collect_startup_choices',return_value=(False,enabled)+(False,)*10),patch.object(module,'validate_initial_environment',return_value=(True,None)),patch.object(module,'stop_all_tasks'),patch.object(module,'cleanup_stop_requested_services',return_value=set()),patch.object(module,'attach_output_thread'),patch.object(module,'wait_for_services_quiet'),patch.object(module,'stop_processes'),patch.object(module,'monitor_and_restart'),patch.object(module.time,'sleep'),patch('builtins.print'):
                module.main()
            self.assertEqual(diag.run_headless.call_count,int(enabled))

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
    def test_prerequisite_failure_prevents_setup_and_restores_auto_mode(self):
        module=self.root_module('_setup');events=[]
        choices={'diag':True,'continue_on_error':True}
        def prerequisites():
            events.append('prerequisites')
            self.assertFalse(module.AUTO_MODE)
            raise RuntimeError('prerequisite failure')
        with tempfile.TemporaryDirectory() as directory,patch.object(Path,'home',return_value=Path(directory)),patch.dict('os.environ',{'PATH':''}),patch.object(module,'AUTO_MODE',True),patch.object(module,'collect_setup_choices',return_value=choices),patch.object(module,'_load_folder_module') as loader,patch.object(module,'setup_common_global_tools') as common,patch.object(module,'ensure_prerequisites',side_effect=prerequisites),patch('builtins.print'):
            with self.assertRaisesRegex(RuntimeError,'prerequisite failure'):
                module.main()
            launcher=Path(directory)/'.local/bin'/('aidiy_diag.cmd' if setup.sys.platform=='win32' else 'aidiy_diag')
            self.assertFalse(launcher.exists())
            loader.assert_not_called();common.assert_not_called()
            self.assertTrue(module.AUTO_MODE)
        self.assertEqual(events,['prerequisites'])
    def run_setup_order(self, *, common=True, diag=True, local=True, auto=False, failure=None, keep_going=False):
        from contextlib import ExitStack
        from types import SimpleNamespace
        module=self.root_module('_setup');events=[];exit_code=0
        choices=dict.fromkeys(['common','diag','local','mcp','backend','taskteam','web','avatar','hermes','ide','discord'],False)
        choices.update(common=common,diag=diag,local=local,continue_on_error=keep_going)
        def record(name):
            events.append(name)
            self.assertEqual(module.AUTO_MODE,auto)
            return failure != name
        def prerequisites():
            events.append('prerequisites');self.assertFalse(module.AUTO_MODE)
        def launcher(selected, *, desktop):
            self.assertIs(selected,choices);self.assertFalse(desktop)
            return record('diag-launcher')
        modules={
            'backend_diag':SimpleNamespace(setup=launcher,setup_desktop=lambda:record('diag-desktop')),
            'backend_local':SimpleNamespace(setup=lambda selected:record('local'),launch_model_download=lambda selected:record('download')),
        }
        with ExitStack() as stack:
            for name,value in [('AUTO_MODE',auto),('GLOBAL_CLI_INSTALL_PROCESSES',['pending'])]:stack.enter_context(patch.object(module,name,value))
            stack.enter_context(patch.object(module,'collect_setup_choices',return_value=choices))
            stack.enter_context(patch.object(module,'ensure_prerequisites',side_effect=prerequisites))
            stack.enter_context(patch.object(module,'setup_common_global_tools',side_effect=lambda selected:[] if record('common') else ['common-error']))
            stack.enter_context(patch.object(module,'wait_global_cli_tools_install',side_effect=lambda:[] if record('common-wait') else ['fixture-package']))
            stack.enter_context(patch.object(module,'_load_folder_module',side_effect=lambda folder:modules[folder]))
            stack.enter_context(patch.object(module,'remove_folder_import_caches',side_effect=lambda:record('clear')))
            stack.enter_context(patch.object(module,'run_diag_headless',side_effect=lambda:record('headless')))
            summary=stack.enter_context(patch.object(module,'print_setup_summary'))
            stack.enter_context(patch.object(module.time,'sleep'));stack.enter_context(patch('builtins.print'))
            try:module.main()
            except SystemExit as result:exit_code=result.code
            self.assertEqual(module.AUTO_MODE,auto)
        summary.assert_called_once()
        return events,summary.call_args.args[0],exit_code

    def test_common_diag_local_order_in_manual_and_auto_modes(self):
        for auto in (False,True):
            with self.subTest(auto=auto):
                events,errors,code=self.run_setup_order(auto=auto)
                self.assertEqual(events,['prerequisites','common','common-wait','diag-launcher','diag-desktop','local','download','clear','headless'])
                self.assertEqual(errors,[]);self.assertEqual(code,0)

    def test_setup_selection_skips_only_unselected_stages(self):
        for common in (False,True):
            for diag in (False,True):
                for local in (False,True):
                    with self.subTest(common=common,diag=diag,local=local):
                        events,errors,code=self.run_setup_order(common=common,diag=diag,local=local)
                        expected=['prerequisites']+(['common','common-wait'] if common else [])+(['diag-launcher','diag-desktop'] if diag else [])+(['local','download'] if local else [])+['clear']+(['headless'] if diag else [])
                        self.assertEqual(events,expected);self.assertEqual(errors,[]);self.assertEqual(code,0)

    def test_diag_and_local_failures_preserve_continue_or_abort_policy(self):
        labels={'diag-launcher':'バックエンド(Diag)','diag-desktop':'バックエンド(Diag): Electron','local':'バックエンド(local)'}
        normal=['prerequisites','common','common-wait','diag-launcher','diag-desktop','local','download','clear','headless']
        for failure,label in labels.items():
            for keep_going in (False,True):
                with self.subTest(failure=failure,keep_going=keep_going):
                    events,errors,code=self.run_setup_order(failure=failure,keep_going=keep_going)
                    self.assertEqual(events,normal if keep_going else normal[:normal.index(failure)+1])
                    self.assertEqual(errors,[label]);self.assertEqual(code,0 if keep_going else 1)

    def test_common_errors_keep_existing_summary_and_continuation_behavior(self):
        for failure,label in [('common','common-error'),('common-wait','共通: AI CLI ツール導入 (fixture-package)')]:
            events,errors,code=self.run_setup_order(failure=failure)
            self.assertLess(events.index('common-wait'),events.index('diag-launcher'))
            self.assertEqual(events[-2:],['clear','headless']);self.assertEqual(errors,[label]);self.assertEqual(code,0)
    def test_cancel_does_not_check_or_install_prerequisites(self):
        module=self.root_module('_setup')
        with patch.object(module,'collect_setup_choices',return_value=None),patch.object(module,'ensure_prerequisites') as prerequisites,patch('builtins.print'):
            with self.assertRaises(SystemExit):module.main()
            prerequisites.assert_not_called()
    def test_cache_clear_before_single_diag_and_error_policy(self):
        for success,keep_going in [(True,False),(False,True),(False,False)]:
            with self.subTest(success=success,keep_going=keep_going):
                module=self.root_module('_setup');events=[]
                choices=dict.fromkeys(['common','local','mcp','backend','taskteam','web','avatar','hermes','ide','discord','diag'],False)
                choices.update(diag=True,continue_on_error=keep_going)
                from types import SimpleNamespace
                fake=SimpleNamespace(setup=lambda *a,**kw:True,setup_desktop=lambda:True)
                def diagnose():events.append('diag');return success
                with patch.object(module,'collect_setup_choices',return_value=choices),patch.object(module,'_load_folder_module',return_value=fake),patch.object(module,'ensure_prerequisites'),patch.object(module,'remove_folder_import_caches',side_effect=lambda:events.append('clear')),patch.object(module,'run_diag_headless',side_effect=diagnose),patch.object(module,'print_header',side_effect=lambda text:events.append(text)),patch.object(module,'print_setup_summary') as summary,patch.object(module.time,'sleep'),patch('builtins.print'):
                    if not success and not keep_going:
                        with self.assertRaises(SystemExit) as result:module.main()
                        self.assertEqual(result.exception.code,1)
                    else:module.main()
                start=events.index('キャッシュクリア');self.assertEqual(events[start:start+3],['キャッシュクリア','clear','diag'])
                self.assertEqual(events.count('diag'),1)
                summary.assert_called_once_with([] if success else ['バックエンド(Diag): aidiy_diag --headless'])

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

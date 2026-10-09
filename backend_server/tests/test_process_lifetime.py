# -*- coding: utf-8 -*-
"""実プロセスの子・孫を作り、終了理由ごとの回収と他セッションの独立性を確認する。"""

import asyncio
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import psutil

from test_aidiy_hermes_stdin import _load_code_ai_module


ROOT = Path(__file__).resolve().parents[2]
SUPERVISOR = ROOT / "backend_tools" / "tools_proc" / "process_lifetime.py"
FIXTURE = '''
import os,sys,subprocess,time
from pathlib import Path
directory=Path(sys.argv[1])
mode=sys.argv[2]
if mode == 'owner':
    process=subprocess.Popen([sys.executable,sys.argv[3],'--parent-pid',str(os.getpid()),'--',sys.executable,__file__,str(directory),'root'])
    (directory/'wrapper.pid').write_text(str(process.pid))
elif mode == 'guard':
    sys.path.insert(0,sys.argv[3])
    from tools_proc.process_lifetime import guard_parent
    guard=guard_parent()
    assert guard.thread.daemon
    subprocess.Popen([sys.executable,__file__,str(directory),'child'])
elif mode in ('root','normal'):
    subprocess.Popen([sys.executable,__file__,str(directory),'child'],start_new_session=os.name != 'nt')
elif mode == 'child':
    subprocess.Popen([sys.executable,__file__,str(directory),'leaf'],start_new_session=os.name != 'nt')
(directory/(mode+'.pid')).write_text(str(os.getpid()))
if mode in ('normal','root','guard'):
    while not (directory/'leaf.pid').exists(): time.sleep(0.01)
    print('READY',flush=True)
if mode != 'normal': time.sleep(60)
'''


class ProcessLifetimeTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.fixture = self.directory / "fixture.py"
        self.fixture.write_text(FIXTURE, encoding="utf-8")
        self.owned = []
        self.processes = []

    def tearDown(self):
        # テスト失敗時も、このテストが起動した PID だけを回収する。
        for process in reversed(self.owned):
            if process.is_running():
                try:
                    process.kill()
                except psutil.Error:
                    pass
        psutil.wait_procs(self.owned, timeout=2)
        for process in self.processes:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)
            if process.stdout:
                process.stdout.close()
            if process.stderr:
                process.stderr.close()
        self.temp.cleanup()

    def _command(self, mode="root"):
        return [sys.executable, str(self.fixture), str(self.directory), mode]

    def _spawn(self, command):
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.processes.append(process)
        self.owned.append(psutil.Process(process.pid))
        return process

    async def _ready(self, names=("child", "leaf")):
        deadline = time.monotonic() + 10
        while not all((self.directory / (name + ".pid")).exists() for name in names):
            self.assertLess(time.monotonic(), deadline, "子孫プロセスの起動待ちがタイムアウトしました")
            await asyncio.sleep(0.02)
        for name in names:
            pid = int((self.directory / (name + ".pid")).read_text())
            try:
                self.owned.append(psutil.Process(pid))
            except psutil.NoSuchProcess:
                pass

    async def _assert_children_gone(self):
        deadline = time.monotonic() + 8
        pids = [int((self.directory / (name + ".pid")).read_text()) for name in ("child", "leaf")]
        while True:
            alive = []
            for pid in pids:
                try:
                    p = psutil.Process(pid)
                    if p.status() != psutil.STATUS_ZOMBIE:
                        alive.append(pid)
                except psutil.NoSuchProcess:
                    pass
            if not alive:
                return
            self.assertLess(time.monotonic(), deadline, f"子孫が残っています: {alive}")
            await asyncio.sleep(0.05)

    async def test_normal_exit_cleans_detached_grandchildren(self):
        process = self._spawn([sys.executable, str(SUPERVISOR), "--parent-pid", str(os.getpid()), "--", *self._command("normal")])
        await self._ready()
        output, error = await asyncio.to_thread(process.communicate, timeout=10)
        self.assertEqual(0, process.returncode, error.decode())
        self.assertEqual(b"READY\n", output.replace(b"\r\n", b"\n"))
        await self._assert_children_gone()

    async def test_parent_force_kill_cleans_tree(self):
        owner = self._spawn([*self._command("owner"), str(SUPERVISOR)])
        await self._ready(("wrapper", "root", "child", "leaf"))
        owner.kill()
        await asyncio.to_thread(owner.communicate, timeout=10)
        await self._assert_children_gone()
        wrapper = int((self.directory / "wrapper.pid").read_text())
        self.assertFalse(psutil.pid_exists(wrapper) and psutil.Process(wrapper).status() != psutil.STATUS_ZOMBIE)

    async def test_standalone_guard_exits_when_parent_dies(self):
        # helper の guard_parent は Hermes / stdio bridge が直接使う経路。
        launcher = "import subprocess,sys,time; subprocess.Popen(sys.argv[1:]); time.sleep(60)"
        owner = self._spawn([sys.executable, "-c", launcher, *self._command("guard"), str(SUPERVISOR.parent.parent)])
        await self._ready(("guard", "child", "leaf"))
        owner.kill()
        await asyncio.to_thread(owner.communicate, timeout=10)
        await self._assert_children_gone()

    async def test_cancellation_during_spawn_still_cleans_tree(self):
        module = _load_code_ai_module()
        ai = module.CodeAI(AI_NAME="aidiy_hermes")
        create_process = asyncio.create_subprocess_exec
        release = asyncio.Event()

        async def delayed_spawn(*args, **kwargs):
            process = await create_process(*args, **kwargs)
            await release.wait()  # OS 起動済み、呼び出し側への PID 返却前を再現
            return process

        with patch.object(module.asyncio, "create_subprocess_exec", delayed_spawn):
            task = asyncio.create_task(ai._subprocess実行(self._command(), str(ROOT), 30))
            await self._ready(("root", "child", "leaf"))
            task.cancel()
            release.set()
            with self.assertRaises(asyncio.CancelledError):
                await asyncio.wait_for(task, timeout=8)
        await self._assert_children_gone()
        self.assertIsNone(ai.current_process)

    async def test_timeout_and_cancellation_clean_tree_without_affecting_other_session(self):
        unrelated = self._spawn([sys.executable, "-c", "import time; time.sleep(60)"])
        module = _load_code_ai_module()
        for reason, method in (("timeout", "_subprocess実行"), ("cancel", "_subprocess実行"), ("stop", "_subprocess実行"), ("cancel", "_antigravity実行")):
            with self.subTest(reason=reason, method=method):
                for name in ("root", "child", "leaf"):
                    (self.directory / (name + ".pid")).unlink(missing_ok=True)
                ai = module.CodeAI(AI_NAME="antigravity_cli" if "antigravity" in method else "aidiy_hermes")
                task = asyncio.create_task(getattr(ai, method)(self._command(), str(ROOT), 1 if reason == "timeout" else 30))
                await self._ready(("root", "child", "leaf"))
                if reason == "cancel":
                    task.cancel()
                    with self.assertRaises(asyncio.CancelledError):
                        await asyncio.wait_for(task, timeout=8)
                elif reason == "stop":
                    await ai.強制終了()
                    await asyncio.wait_for(task, timeout=8)
                else:
                    result = await asyncio.wait_for(task, timeout=8)
                    self.assertIn("タイムアウト", result)
                await self._assert_children_gone()
                self.assertIsNone(ai.current_process)
                self.assertIsNone(unrelated.poll())


if __name__ == "__main__":
    unittest.main()

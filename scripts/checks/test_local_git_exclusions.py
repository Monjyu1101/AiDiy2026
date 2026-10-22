"""ローカル Git 管理情報を走査・クリーンアップから保護する回帰試験。"""
import ast
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class LocalGitExclusionTests(unittest.TestCase):
    def test_cleanup_does_not_descend_into_git_metadata(self):
        spec = importlib.util.spec_from_file_location('cleanup_local_git_test', ROOT / '_cleanup.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ('.git', '.git_local', '.GIT_LOCAL', 'source'):
                (root / name / 'temp').mkdir(parents=True)
            self.assertEqual(module.find_temp_directories(root), [root / 'source' / 'temp'])
            self.assertTrue((root / '.git_local' / 'temp').is_dir())

    def test_python_scan_exclusions(self):
        # Importing these application modules would load services or execute a BOM scan.
        for path, variable in (
            ('scripts/remove_bom.py', 'IGNORE_DIRS'),
            ('scripts/bom_anomaly_list.py', 'IGNORE_DIRS'),
            ('backend_server/AIコア/AIバックアップ.py', '_バックアップ除外フォルダ'),
            ('backend_tools/aidiy_automations/ビデオページ生成/utils/steps.py', '除外フォルダ'),
        ):
            with self.subTest(path=path):
                tree = ast.parse((ROOT / path).read_text(encoding='utf-8-sig'))
                values = [ast.literal_eval(node.value) for node in ast.walk(tree)
                          if isinstance(node, ast.Assign) and any(
                              isinstance(target, ast.Name) and target.id == variable for target in node.targets)]
                self.assertEqual(len(values), 1)
                self.assertIn('.git', values[0])
                self.assertIn('.git_local', values[0])


if __name__ == '__main__':
    unittest.main()

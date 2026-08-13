# -*- coding: utf-8 -*-

import importlib.util
import logging
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
CONF_MAIN_PATH = BACKEND_DIR / "conf" / "__main__.py"


def _load_conf_module():
    log_config_stub = types.ModuleType("log_config")
    log_config_stub.get_logger = logging.getLogger

    package_name = "conf_init_test_package"
    package_stub = types.ModuleType(package_name)
    package_stub.__path__ = [str(BACKEND_DIR / "conf")]

    spec = importlib.util.spec_from_file_location(
        f"{package_name}.__main__",
        CONF_MAIN_PATH,
        submodule_search_locations=[str(BACKEND_DIR / "conf")],
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"設定モジュールを読み込めません: {CONF_MAIN_PATH}")
    module = importlib.util.module_from_spec(spec)
    with patch.dict(
        sys.modules,
        {
            "log_config": log_config_stub,
            package_name: package_stub,
            spec.name: module,
        },
    ):
        spec.loader.exec_module(module)
    return module


class ConfInitTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = _load_conf_module()
        cls.Conf = cls.module.Conf

    def test_invalid_run_mode_returns_false_after_json_is_loaded(self):
        class FakeConfJson:
            pass

        conf = self.Conf()
        with patch.object(self.module, "conf_json", FakeConfJson):
            self.assertFalse(
                conf.init(
                    runMode="invalid",
                    conf_path_enabled=False,
                    conf_models_enabled=False,
                )
            )

        self.assertIsInstance(conf.json, FakeConfJson)

    def test_malformed_config_failure_is_reported_without_partial_json(self):
        conf = self.Conf()

        class BrokenConfJson:
            def __init__(self):
                raise ValueError("broken config")

        with (
            patch.object(self.module, "conf_json", BrokenConfJson),
            self.assertLogs(self.module.logger.name, level="ERROR") as captured,
        ):
            self.assertFalse(
                conf.init(conf_path_enabled=False, conf_models_enabled=False)
            )

        self.assertIsNone(conf.json)
        self.assertTrue(
            any("設定初期化エラー: broken config" in line for line in captured.output)
        )
        self.assertFalse(any("無効な実行モード" in line for line in captured.output))


if __name__ == "__main__":
    unittest.main()

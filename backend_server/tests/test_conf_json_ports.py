# -*- coding: utf-8 -*-

import importlib.util
import json
import logging
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
CONF_JSON_PATH = BACKEND_DIR / "conf" / "conf_json.py"


def _load_conf_json_module():
    log_config_stub = types.ModuleType("log_config")
    log_config_stub.get_logger = logging.getLogger

    spec = importlib.util.spec_from_file_location("conf_json_port_test", CONF_JSON_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"設定モジュールを読み込めません: {CONF_JSON_PATH}")
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"log_config": log_config_stub}):
        spec.loader.exec_module(module)
    return module


class ConfJsonPortKeyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = _load_conf_json_module()
        cls.conf_json = cls.module.conf_json

    def test_default_port_keys_and_values(self):
        expected = {
            "PORT_WEB": "8090",
            "PORT_CORE": "8091",
            "PORT_AVATAR": "8092",
            "PORT_TASKTEAM": "8093",
            "PORT_TOOLS": "8095",
            "PORT_LOCAL": "8096",
            "PORT_APPS": "8098",
        }

        actual = {
            key: self.conf_json.DEFAULT_CONFIG[key]
            for key in expected
        }
        self.assertEqual(expected, actual)
        for old_keys in self.conf_json.LEGACY_PORT_KEYS.values():
            for old_key in old_keys:
                self.assertNotIn(old_key, self.conf_json.DEFAULT_CONFIG)

    def test_legacy_port_keys_are_migrated_and_removed(self):
        legacy = {
            "WEB_BASE": "18090",
            "CORE_BASE": "18091",
            "AVATAR_BASE": "18092",
            "TASK_BASE": "18093",
            "TEAM_BASE": "28093",
            "TOOLS_BASE": "18095",
            "LOCAL_BASE": "18096",
            "APPS_BASE": "18098",
            "CUSTOM_VALUE": "keep",
        }
        expected = {
            "PORT_WEB": "18090",
            "PORT_CORE": "18091",
            "PORT_AVATAR": "18092",
            "PORT_TASKTEAM": "18093",
            "PORT_TOOLS": "18095",
            "PORT_LOCAL": "18096",
            "PORT_APPS": "18098",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "AiDiy_key.json"
            config_path.write_text(
                json.dumps(legacy, ensure_ascii=False),
                encoding="utf-8",
            )

            config = self.conf_json(json=str(config_path))
            saved = json.loads(config_path.read_text(encoding="utf-8"))
            saved_text = config_path.read_text(encoding="utf-8")
            reloaded = self.conf_json(json=str(config_path))
            reloaded_text = config_path.read_text(encoding="utf-8")

        self.assertEqual(expected, {key: config.get(key) for key in expected})
        self.assertEqual(expected, {key: saved[key] for key in expected})
        self.assertEqual(expected, {key: reloaded.get(key) for key in expected})
        self.assertEqual(saved_text, reloaded_text)
        self.assertEqual(saved_text, json.dumps(saved, indent=4, ensure_ascii=False) + "\n")
        self.assertEqual("keep", saved["CUSTOM_VALUE"])
        self.assertEqual(list(expected), list(saved)[:len(expected)])
        for old_keys in self.conf_json.LEGACY_PORT_KEYS.values():
            for old_key in old_keys:
                self.assertNotIn(old_key, saved)

    def test_current_port_value_takes_precedence(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "AiDiy_key.json"
            config_path.write_text(
                json.dumps(
                    {"PORT_WEB": "28090", "WEB_BASE": "18090"},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            config = self.conf_json(json=str(config_path))
            saved = json.loads(config_path.read_text(encoding="utf-8"))

        self.assertEqual("28090", config.get("PORT_WEB"))
        self.assertNotIn("WEB_BASE", saved)

    def test_team_only_key_is_migrated_to_taskteam(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "AiDiy_key.json"
            config_path.write_text(
                json.dumps({"TEAM_BASE": "18093"}),
                encoding="utf-8",
            )

            config = self.conf_json(json=str(config_path))
            saved = json.loads(config_path.read_text(encoding="utf-8"))

        self.assertEqual("18093", config.get("PORT_TASKTEAM"))
        self.assertNotIn("TEAM_BASE", saved)

    def test_semantically_equal_taskteam_values_do_not_warn(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "AiDiy_key.json"
            config_path.write_text(
                json.dumps({"TASK_BASE": "08093", "TEAM_BASE": " 8093 "}),
                encoding="utf-8",
            )

            with self.assertNoLogs(level="WARNING"):
                config = self.conf_json(json=str(config_path))

        self.assertEqual("8093", config.get("PORT_TASKTEAM"))

    def test_all_write_paths_canonicalize_legacy_keys(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "AiDiy_key.json"
            config = self.conf_json(json=str(config_path))

            self.assertTrue(config.set("WEB_BASE", "18090"))
            self.assertTrue(config.update({
                "CORE_BASE": 18091,
                "TASK_BASE": "18093",
                "TEAM_BASE": "28093",
                "PORT_APPS": "18098",
                "APPS_BASE": "28098",
            }))
            config.AVATAR_BASE = "18092"
            saved = json.loads(config_path.read_text(encoding="utf-8"))

        self.assertEqual("18090", saved["PORT_WEB"])
        self.assertEqual("18091", saved["PORT_CORE"])
        self.assertEqual("18092", saved["PORT_AVATAR"])
        self.assertEqual("18093", saved["PORT_TASKTEAM"])
        self.assertEqual("18098", saved["PORT_APPS"])
        for old_keys in self.conf_json.LEGACY_PORT_KEYS.values():
            for old_key in old_keys:
                self.assertNotIn(old_key, saved)

    def test_invalid_port_update_does_not_change_file_or_memory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "AiDiy_key.json"
            config = self.conf_json(json=str(config_path))
            before_file = config_path.read_bytes()
            before_value = config.get("PORT_WEB")

            with self.assertRaises(ValueError):
                config.set("WEB_BASE", "0")

            self.assertEqual(before_file, config_path.read_bytes())
            self.assertEqual(before_value, config.get("PORT_WEB"))

    def test_malformed_or_non_object_json_is_not_overwritten(self):
        invalid_values = ("{broken", "[]")
        for invalid_text in invalid_values:
            with self.subTest(invalid_text=invalid_text):
                with tempfile.TemporaryDirectory() as temp_dir:
                    config_path = Path(temp_dir) / "AiDiy_key.json"
                    config_path.write_text(invalid_text, encoding="utf-8")
                    before = config_path.read_bytes()

                    with self.assertRaises(ValueError):
                        self.conf_json(json=str(config_path))

                    self.assertEqual(before, config_path.read_bytes())

    def test_invalid_current_port_does_not_delete_legacy_value(self):
        original = {"PORT_WEB": "", "WEB_BASE": "18090", "CUSTOM_VALUE": "keep"}
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "AiDiy_key.json"
            config_path.write_text(
                json.dumps(original, ensure_ascii=False),
                encoding="utf-8",
            )
            before = config_path.read_bytes()

            with self.assertRaises(ValueError):
                self.conf_json(json=str(config_path))

            self.assertEqual(before, config_path.read_bytes())

    def test_invalid_secondary_taskteam_value_preserves_original_file(self):
        original = {"TASK_BASE": "18093", "TEAM_BASE": "invalid"}
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "AiDiy_key.json"
            config_path.write_text(json.dumps(original), encoding="utf-8")
            before = config_path.read_bytes()

            with self.assertRaises(ValueError):
                self.conf_json(json=str(config_path))

            self.assertEqual(before, config_path.read_bytes())

    def test_atomic_replace_failure_preserves_file_and_memory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "AiDiy_key.json"
            config = self.conf_json(json=str(config_path))
            before_file = config_path.read_bytes()
            before_value = config.get("PORT_WEB")

            with patch.object(self.module.os, "replace", side_effect=PermissionError("locked")):
                self.assertFalse(config.set("PORT_WEB", "18090"))

            self.assertEqual(before_file, config_path.read_bytes())
            self.assertEqual(before_value, config.get("PORT_WEB"))
            self.assertEqual([], list(Path(temp_dir).glob("*.tmp")))


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101
# -------------------------------------------------------------------------

from log_config import get_logger
logger = get_logger(__name__)

import os
import json
from typing import Any, Dict

class conf_json:
    """設定JSON管理クラス（シンプル実装・プロパティアクセス対応）"""

    # デフォルト設定値
    DEFAULT_CONFIG = {
        # WebUI設定
        'WEB_BASE': '8090',
        'CORE_BASE': '8091',
        'WEBUI_FIRST_PAGE': 'Sスケジュール',

        # APIキー
        'gemini_key_id': '< your gemini api key >',
        'freeai_key_id': '< your freeai api key >',
        'claude_key_id': '< your claude api key >',

        # OpenAI/Azureの基本設定
        'openai_api_type': 'openai',
        'openai_organization': '< your openai organization id >',
        'openai_key_id': '< your openai api key >',
        'azure_endpoint': '< your azure openai endpoint >',
        'azure_version': 'yyyy-mm-dd-preview',
        'azure_key_id': '< your azure openai api key >',
        'copilot_key_id': '< your copilot api key >',
        'openrt_key_id': '< your openrouter api key >',

        # ChatAI設定
        'CHAT_AI_NAME': 'freeai',
        'CHAT_GEMINI_MODEL': 'gemini-3-pro-image-preview',
        'CHAT_FREEAI_MODEL': 'gemini-2.5-flash-preview-09-2025',
        'CHAT_OPENRT_MODEL': 'google/gemini-3-pro-image-preview',

        # LiveAI設定
        'LIVE_AI_NAME': 'freeai_live',
        'LIVE_GEMINI_MODEL': 'gemini-2.5-flash-native-audio-preview-12-2025',
        'LIVE_GEMINI_VOICE': 'Zephyr',
        'LIVE_FREEAI_MODEL': 'gemini-2.5-flash-native-audio-preview-09-2025',
        'LIVE_FREEAI_VOICE': 'Zephyr',
        'LIVE_OPENAI_MODEL': 'gpt-realtime-mini',
        'LIVE_OPENAI_VOICE': 'marin',

        # CodeAI設定
        'CODE_BASE_PATH': '../',
        'CODE_AI1_NAME': 'claude_sdk',
        'CODE_AI1_MODEL': 'auto',
        'CODE_AI2_NAME': 'copilot_cli',
        'CODE_AI2_MODEL': 'auto',
        'CODE_AI3_NAME': 'codex_cli',
        'CODE_AI3_MODEL': 'auto',
        'CODE_AI4_NAME': 'gemini_cli',
        'CODE_AI4_MODEL': 'auto',
        'CODE_CLAUDE_SDK_MODEL': 'auto',
        'CODE_CLAUDE_CLI_MODEL': 'auto',
        'CODE_COPILOT_CLI_MODEL': 'auto',
        'CODE_GEMINI_CLI_MODEL': 'auto',
        'CODE_CODEX_CLI_MODEL': 'auto',
        'CODE_MAX_TURNS': 999,
        'CODE_PLAN': 'auto',
        'CODE_VERIFY': 'auto',
    }

    def __init__(self, json: str = None):
        """
        初期化

        Args:
            json: 設定ファイルパス（省略時はデフォルト）
        """
        if json is None:
            json = '_config/AiDiy_key.json'

        object.__setattr__(self, '_config_file', json)
        object.__setattr__(self, '_config_data', {})

        # 設定ファイルを読み込み（無い場合は作成）
        self._load_or_create()

    def _load_or_create(self) -> None:
        """設定ファイルの読み込み、または初期値で作成"""
        config_file = object.__getattribute__(self, '_config_file')
        保存要否 = False

        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8-sig') as f:
                    config_data = json.load(f)
                if not isinstance(config_data, dict):
                    raise ValueError("設定JSONのルートはオブジェクト(dict)である必要があります")
                object.__setattr__(self, '_config_data', config_data)
                logger.info(f'設定ファイル読み込み完了: {config_file}')
            except Exception as e:
                logger.error(f'設定ファイル読み込みエラー: {e}')
                object.__setattr__(self, '_config_data', self.DEFAULT_CONFIG.copy())
                保存要否 = True
        else:
            logger.warning(f'設定ファイルが存在しません: {config_file}')
            object.__setattr__(self, '_config_data', self.DEFAULT_CONFIG.copy())
            保存要否 = True

        # 既存設定に不足しているデフォルト項目を補完
        if self._apply_default_keys():
            保存要否 = True

        # CODE_AI2_NAME～4_NAMEが"auto"の場合、CODE_AI1_NAMEの値をコピー
        if self._apply_code_ai_auto():
            保存要否 = True

        if 保存要否:
            self._save()

    def _apply_default_keys(self) -> bool:
        """不足しているデフォルト設定キーを補完"""
        config_data = object.__getattribute__(self, '_config_data')
        変更あり = False
        for key, value in self.DEFAULT_CONFIG.items():
            if key not in config_data:
                config_data[key] = value
                変更あり = True
        # 並び順をDEFAULT_CONFIG準拠に統一（未知キーは末尾維持）
        ordered = {}
        for key in self.DEFAULT_CONFIG.keys():
            if key in config_data:
                ordered[key] = config_data[key]
        for key, value in config_data.items():
            if key not in ordered:
                ordered[key] = value
        if list(ordered.keys()) != list(config_data.keys()):
            変更あり = True
        object.__setattr__(self, '_config_data', ordered)
        return 変更あり

    def _apply_code_ai_auto(self) -> bool:
        """CODE_AI2_NAME～4_NAMEが'auto'の場合、CODE_AI1_NAMEの値をコピー"""
        config_data = object.__getattribute__(self, '_config_data')
        変更あり = False
        
        code_ai1 = config_data.get('CODE_AI1_NAME', 'auto')
        code_ai1_model = config_data.get('CODE_AI1_MODEL', 'auto')
        
        # CODE_AI2_NAME～4_NAMEをチェック
        for i in range(2, 5):
            code_ai_key = f'CODE_AI{i}_NAME'
            code_model_key = f'CODE_AI{i}_MODEL'
            
            # CODE_AIn_NAMEが"auto"の場合、CODE_AI1_NAMEの値をコピー
            if config_data.get(code_ai_key, 'auto') == 'auto':
                config_data[code_ai_key] = code_ai1
                config_data[code_model_key] = code_ai1_model
                変更あり = True
                logger.debug(f'{code_ai_key}が"auto"のため、CODE_AI1_NAMEの値({code_ai1})をコピーしました')
        return 変更あり

    def _save(self) -> bool:
        """設定ファイルを保存"""
        try:
            config_file = object.__getattribute__(self, '_config_file')
            config_data = object.__getattribute__(self, '_config_data')

            os.makedirs(os.path.dirname(config_file), exist_ok=True)

            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            logger.info(f'設定ファイル保存完了: {config_file}')
            return True
        except Exception as e:
            logger.error(f'設定ファイル保存エラー: {e}')
            return False

    def __getattr__(self, key: str) -> Any:
        """プロパティアクセスで設定値を取得"""
        config_data = object.__getattribute__(self, '_config_data')
        if key in config_data:
            return config_data[key]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{key}'")

    def __setattr__(self, key: str, value: Any) -> None:
        """プロパティアクセスで設定値を設定し、ファイルに保存"""
        if key.startswith('_'):
            object.__setattr__(self, key, value)
        else:
            config_data = object.__getattribute__(self, '_config_data')
            config_data[key] = value
            self._save()

    def get(self, key: str, default: Any = None) -> Any:
        """設定値を取得（辞書形式）"""
        config_data = object.__getattribute__(self, '_config_data')
        return config_data.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        """設定値を設定し、ファイルに保存（辞書形式）"""
        config_data = object.__getattribute__(self, '_config_data')
        config_data[key] = value
        return self._save()

    def update(self, data: Dict[str, Any]) -> bool:
        """複数の設定値を一括更新し、ファイルに保存"""
        config_data = object.__getattribute__(self, '_config_data')
        config_data.update(data)
        return self._save()


ConfigJsonManager = conf_json

__all__ = [
    "conf_json",
    "ConfigJsonManager",
]

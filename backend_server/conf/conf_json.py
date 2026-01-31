# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

# モジュール名
MODULE_NAME = 'json'

# ロガーの設定
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)-10s - %(levelname)-8s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(MODULE_NAME)

import os
import json
from typing import Any, Dict

class conf_json:
    """設定JSON管理クラス（シンプル実装・プロパティアクセス対応）"""

    # デフォルト設定値
    DEFAULT_CONFIG = {
        # WebUI設定
        'WEB_BASE': '8080',
        'CORE_BASE': '8080',
        'WEBUI_FIRST_PAGE': '_テスト',

        # APIキー
        'gemini_key_id': '< your gemini api key >',
        'freeai_key_id': '< your freeai api key >',  # GeminiのAPI別キー（実態はGemini API）
        'claude_key_id': '< your claude api key >',
        'openai_api_type': 'openai',
        'openai_organization': '< your openai organization id >',
        'openai_key_id': '< your openai api key >',
        'azure_endpoint': '< your azure openai endpoint >',
        'azure_version': 'yyyy-mm-dd-preview',
        'azure_key_id': '< your azure openai api key >',
        'copilot_key_id': '< your copilot api key >',
        'openrt_key_id': '< your openrouter api key >',

        # ChatAI設定
        'CHAT_AI': 'freeai',
        'CHAT_GEMINI_MODEL': 'gemini-3-pro-image-preview',
        'CHAT_FREEAI_MODEL': 'gemini-2.5-flash',
        'CHAT_OPENRT_MODEL': 'google/gemini-3-pro-image-preview',

        # LiveAI設定
        'LIVE_AI': 'freeai_live',
        'LIVE_GEMINI_MODEL': 'gemini-2.5-flash-native-audio-preview-09-2025',
        'LIVE_GEMINI_VOICE': 'Zephyr',
        'LIVE_FREEAI_MODEL': 'gemini-2.5-flash-native-audio-preview-09-2025',
        'LIVE_FREEAI_VOICE': 'Zephyr',
        'LIVE_OPENAI_MODEL': 'gpt-realtime-mini',
        'LIVE_OPENAI_VOICE': 'marin',

        # CodeAI設定
        'CODE_BASE_PATH': '../',
        'CODE_AI1': 'copilot',
        'CODE_AI1_MODEL': 'auto',
        'CODE_AI2': 'auto',
        'CODE_AI2_MODEL': 'auto',
        'CODE_AI3': 'auto',
        'CODE_AI3_MODEL': 'auto',
        'CODE_AI4': 'auto',
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
            json = '_config/RiKi_AiDiy_key.json'

        object.__setattr__(self, '_config_file', json)
        object.__setattr__(self, '_config_data', {})

        # 設定ファイルを読み込み（無い場合は作成）
        self._load_or_create()

    def _load_or_create(self) -> None:
        """設定ファイルの読み込み、または初期値で作成"""
        config_file = object.__getattribute__(self, '_config_file')

        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                object.__setattr__(self, '_config_data', config_data)
                logger.info(f'設定ファイル読み込み完了: {config_file}')
            except Exception as e:
                logger.error(f'設定ファイル読み込みエラー: {e}')
                object.__setattr__(self, '_config_data', self.DEFAULT_CONFIG.copy())
        else:
            logger.warning(f'設定ファイルが存在しません: {config_file}')
            object.__setattr__(self, '_config_data', self.DEFAULT_CONFIG.copy())
            self._save()

        # CODE_AI2～4が"auto"の場合、CODE_AI1の値をコピー
        self._apply_code_ai_auto()

    def _apply_code_ai_auto(self) -> None:
        """CODE_AI2～4が'auto'の場合、CODE_AI1の値をコピー"""
        config_data = object.__getattribute__(self, '_config_data')
        
        code_ai1 = config_data.get('CODE_AI1', 'auto')
        code_ai1_model = config_data.get('CODE_AI1_MODEL', 'auto')
        
        # CODE_AI2～4をチェック
        for i in range(2, 5):
            code_ai_key = f'CODE_AI{i}'
            code_model_key = f'CODE_AI{i}_MODEL'
            
            # CODE_AInが"auto"の場合、CODE_AI1の値をコピー
            if config_data.get(code_ai_key, 'auto') == 'auto':
                config_data[code_ai_key] = code_ai1
                config_data[code_model_key] = code_ai1_model
                logger.debug(f'{code_ai_key}が"auto"のため、CODE_AI1の値({code_ai1})をコピーしました')

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

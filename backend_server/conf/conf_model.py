# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

# モジュール名
MODULE_NAME = 'models'

# ロガーの設定
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)-10s - %(levelname)-8s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(MODULE_NAME)

import datetime
import json
import os
import requests
from typing import Dict, Optional

class conf_models:
    """AIコアモデル管理クラス"""

    def __init__(self, conf=None):
        self.conf = conf
        self.openrt_models: Dict[str, Dict[str, str]] = {}
        self.google_models: Dict[str, Dict[str, str]] = {}
        self.openai_models: Dict[str, Dict[str, str]] = {}
        self.claude_models: Dict[str, Dict[str, str]] = {}

        # ライブAIモデル一覧
        self.LIVE_GEMINI_MODELS = {
            "gemini-2.5-flash-native-audio-preview-12-2025": "yyyy/mm/dd - gemini-2.5-flash-native-audio-preview-12-2025",
            "gemini-2.5-flash-native-audio-preview-09-2025": "yyyy/mm/dd - gemini-2.5-flash-native-audio-preview-09-2025",
            "gemini-live-2.5-flash-preview": "yyyy/mm/dd - gemini-live-2.5-flash-preview",
        }
        self.LIVE_OPENAI_MODELS = {
            "gpt-realtime-mini": "yyyy/mm/dd - gpt-realtime-mini",
            "gpt-realtime": "yyyy/mm/dd - gpt-realtime"
        }

        # ライブAIボイス一覧
        self.LIVE_GEMINI_VOICES = {
            "Zephyr": "(2.5) Zephyr Female",

            "Puck": "(2.0) Puck",
            "Charon": "(2.0) Charon",
            "Kore": "(2.0) Kore Female",
            "Fenrir": "(2.0) Fenrir",
            "Leda": "(2.5) Leda Female",
            "Orus": "(2.5) Orus",
            "Aoede": "(2.0) Aoede Female",

            "Callirrhoe": "Callirrhoe Female",
            "Autonoe": "Autonoe Female",
            "Enceladus": "Enceladus",
            "Lapetus": "Lapetus",
            "Umbriel": "Umbriel",
            "Algieba": "Algieba",
            "Despina": "Despina Female",
            "Erinome": "Erinome Female",
            "Algenib": "Algenib",
            "Rasalgethi": "Rasalgethi",
            "Laomedeia": "Laomedeia Female",
            "Achernar": "Achernar Female",
            "Alnilam": "Alnilam",
            "Schedar": "Schedar",
            "Gacrux": "Gacrux Female",
            "Pulcherrima": "Pulcherrima",
            "Achird": "Achird",
            "Zubenelgenubi": "Zubenelgenubi",
            "Vindemiatrix": "Vindemiatrix Female",
            "Sadachbia": "Sadachbia",
            "Sadaltager": "Sadaltager",
            "Sulafat": "Sulafat Female",
        }
        self.LIVE_OPENAI_VOICES = {
            "marin": "Marin Female",

            "alloy": "Alloy Female",
            "ash": "Ash",
            "ballad": "Ballad Female",
            "ceder": "Cedar",
            "coral": "Coral Female",
            "echo": "Echo",
            "fable": "Fable",
            "nova": "Nova Female",
            "onyx": "Onyx",
            "sage": "Sage Female",
            "shimmer": "Shimmer Female",
            "verse": "Verse Female",
        }

        # コードAIモデル一覧
        self.CODE_CLAUDE_SDK_MODELS = {
            "auto": "yyyy/mm/dd - auto (default)",
            "sonnet": "yyyy/mm/dd - sonnet",
            "opus": "yyyy/mm/dd - opus",
            "haiku": "yyyy/mm/dd - haiku",
        }
        self.CODE_CLAUDE_CLI_MODELS = {
            "auto": "yyyy/mm/dd - auto (default)",
            "sonnet": "yyyy/mm/dd - sonnet",
            "opus": "yyyy/mm/dd - opus",
            "haiku": "yyyy/mm/dd - haiku",
        }
        self.CODE_COPILOT_CLI_MODELS = {
            "auto": "yyyy/mm/dd - auto (default)",
            "claude-sonnet-4.5": "yyyy/mm/dd - claude-sonnet-4.5",
            "claude-haiku-4.5": "yyyy/mm/dd - claude-haiku-4.5",
        }
        self.CODE_GEMINI_CLI_MODELS = {
            "auto": "yyyy/mm/dd - auto (default)",
            "gemini-2.5-flash": "yyyy/mm/dd - gemini-2.5-flash",
            "gemini-3-pro-preview": "yyyy/mm/dd - gemini-3-pro-preview",
        }
        self.CODE_CODEX_CLI_MODELS = {
            "auto": "yyyy/mm/dd - auto (default)",
            "gpt-5.2": "yyyy/mm/dd - gpt-5.2",
            "gpt-5.1-codex": "yyyy/mm/dd - gpt-5.1-codex",
            "gpt-5.1-codex-max": "yyyy/mm/dd - gpt-5.1-codex-max",
            "gpt-5.1-codex-mini": "yyyy/mm/dd - gpt-5.1-codex-mini",
            "gpt-5.1": "yyyy/mm/dd - gpt-5.1",
        }

        # _config 下の設定JSONと同期（無ければ作成、あれば読込）
        self._sync_local_model_configs()

    def _config_dir_path(self) -> str:
        """backend_server/_config ディレクトリを返す"""
        return os.path.normpath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_config")
        )

    def _config_file_path(self, filename: str) -> str:
        """設定ファイルの絶対パスを返す（ディレクトリは自動作成）"""
        config_dir = self._config_dir_path()
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, filename)

    def _write_json_file(self, file_path: str, payload: dict) -> None:
        """JSONファイルを書き込む"""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4, ensure_ascii=False)

    def _load_or_create_live_config(
        self,
        filename: str,
        default_models: Dict[str, str],
        default_voices: Dict[str, str],
    ) -> tuple[Dict[str, str], Dict[str, str]]:
        """
        ライブ設定JSONを読込。無ければデフォルトで作成。
        返却値は（models, voices）。
        """
        file_path = self._config_file_path(filename)
        default_payload = {
            "models": default_models,
            "voices": default_voices,
        }

        if not os.path.exists(file_path):
            self._write_json_file(file_path, default_payload)
            logger.info(f"ライブ設定JSONを作成: {file_path}")
            return default_models.copy(), default_voices.copy()

        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                payload = json.load(f)
            if not isinstance(payload, dict):
                raise ValueError("JSONのルートはobject(dict)である必要があります")
            models = payload.get("models", {})
            voices = payload.get("voices", {})
            if not isinstance(models, dict) or not isinstance(voices, dict):
                raise ValueError("models/voices は object(dict)である必要があります")
            logger.info(f"ライブ設定JSONを読込: {file_path}")
            return dict(models), dict(voices)
        except Exception as e:
            logger.error(f"ライブ設定JSON読込エラー: {file_path}, {e}")
            return default_models.copy(), default_voices.copy()

    def _load_or_create_code_config(
        self,
        filename: str,
        default_models: Dict[str, str],
    ) -> Dict[str, str]:
        """
        コード設定JSONを読込。無ければデフォルトで作成。
        返却値は models。
        """
        file_path = self._config_file_path(filename)
        default_payload = {
            "models": default_models,
        }

        if not os.path.exists(file_path):
            self._write_json_file(file_path, default_payload)
            logger.info(f"コード設定JSONを作成: {file_path}")
            return default_models.copy()

        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                payload = json.load(f)
            if not isinstance(payload, dict):
                raise ValueError("JSONのルートはobject(dict)である必要があります")
            models = payload.get("models", {})
            if not isinstance(models, dict):
                raise ValueError("models は object(dict)である必要があります")
            logger.info(f"コード設定JSONを読込: {file_path}")
            return dict(models)
        except Exception as e:
            logger.error(f"コード設定JSON読込エラー: {file_path}, {e}")
            return default_models.copy()

    def _sync_local_model_configs(self) -> None:
        """ローカル設定JSONとモデル定義を同期"""
        self.LIVE_GEMINI_MODELS, self.LIVE_GEMINI_VOICES = self._load_or_create_live_config(
            "AiDiy_live_gemini.json",
            self.LIVE_GEMINI_MODELS,
            self.LIVE_GEMINI_VOICES,
        )
        self.LIVE_OPENAI_MODELS, self.LIVE_OPENAI_VOICES = self._load_or_create_live_config(
            "AiDiy_live_openai.json",
            self.LIVE_OPENAI_MODELS,
            self.LIVE_OPENAI_VOICES,
        )
        self.CODE_CLAUDE_SDK_MODELS = self._load_or_create_code_config(
            "AiDiy_code_claude_sdk.json",
            self.CODE_CLAUDE_SDK_MODELS,
        )
        self.CODE_CLAUDE_CLI_MODELS = self._load_or_create_code_config(
            "AiDiy_code_claude_cli.json",
            self.CODE_CLAUDE_CLI_MODELS,
        )
        self.CODE_COPILOT_CLI_MODELS = self._load_or_create_code_config(
            "AiDiy_code_copilot_cli.json",
            self.CODE_COPILOT_CLI_MODELS,
        )
        self.CODE_GEMINI_CLI_MODELS = self._load_or_create_code_config(
            "AiDiy_code_gemini_cli.json",
            self.CODE_GEMINI_CLI_MODELS,
        )
        self.CODE_CODEX_CLI_MODELS = self._load_or_create_code_config(
            "AiDiy_code_codex_cli.json",
            self.CODE_CODEX_CLI_MODELS,
        )

    def fetch_all_models(self):
        """起動時に全モデルを一括取得"""
        if self.conf:
            self.get_openrt_models(self.conf.json.openrt_key_id)

            gemini_key = self.conf.json.gemini_key_id
            freeai_key = self.conf.json.freeai_key_id

            if gemini_key and not gemini_key.startswith('<'):
                api_key = gemini_key
                key_source = "gemini_key"
            elif freeai_key and not freeai_key.startswith('<'):
                api_key = freeai_key
                key_source = "freeai_key"
            else:
                api_key = None
                key_source = None

            self.get_google_models(api_key, key_source=key_source)

            org = self.conf.json.openai_organization
            self.get_openai_models(self.conf.json.openai_key_id, org)

            self.get_claude_models(self.conf.json.claude_key_id)

    def get_openrt_models(self, api_key: str) -> Dict[str, Dict[str, str]]:
        """OpenRouter apiからモデル一覧を取得（プロバイダー別フィルタリング）"""
        try:
            if not api_key or api_key.startswith('<'):
                logger.warning("OpenRouter apiキーが未設定です")
                return {}

            headers = {
                "Authorization": f"Bearer {api_key}"
            }
            response = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers=headers,
                timeout=30
            )

            if response.status_code != 200:
                logger.error(f"OpenRouterモデル取得エラー: HTTP {response.status_code}")
                return {}

            models_data = response.json()
            result_models = {}

            current_time = datetime.datetime.now()
            filter_1year = (current_time - datetime.timedelta(days=365)).timestamp()
            filter_6months = (current_time - datetime.timedelta(days=180)).timestamp()
            filter_3months = (current_time - datetime.timedelta(days=90)).timestamp()

            very_long_filter_providers = ["perplexity"]
            long_filter_providers = ["google", "openai", "anthropic", "x-ai"]

            filtered_count = 0
            for model in models_data.get('data', []):
                model_id = model.get("id", "")
                context_length = model.get("context_length", 0)
                modality = model.get("architecture", {}).get("modality", "unknown")
                created_timestamp = model.get("created", 0)

                provider = model_id.split('/')[0].lower() if '/' in model_id else ""

                if provider in very_long_filter_providers:
                    if created_timestamp < filter_1year:
                        continue
                elif provider in long_filter_providers:
                    if created_timestamp < filter_6months:
                        continue
                else:
                    if created_timestamp < filter_3months:
                        continue

                created_date = datetime.datetime.fromtimestamp(created_timestamp).strftime("%Y/%m/%d")

                result_models[model_id] = {
                    "model_id": model_id,
                    "トークン数": str(context_length),
                    "モダリティ": modality,
                    "作成日": created_date
                }
                filtered_count += 1

            self.openrt_models = result_models

            logger.info(f"OpenRouterモデル取得完了: {filtered_count}個のモデル（プロバイダー別フィルタリング適用）")

            return result_models

        except requests.exceptions.Timeout:
            logger.error("OpenRouterモデル取得タイムアウト")
            return {}
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouterモデル取得リクエストエラー: {e}")
            return {}
        except Exception as e:
            logger.error(f"OpenRouterモデル取得エラー: {e}")
            return {}

    def get_google_models(self, api_key: str, key_source: str = None) -> Dict[str, Dict[str, str]]:
        """Google Gemini apiからモデル一覧を取得（全件取得後、日付のあるものだけ残す）"""
        try:
            if not api_key or api_key.startswith('<'):
                logger.warning("Google apiキー・FreeAI apiキーともに未設定です")
                return {}

            import google.genai as genai
            client = genai.Client(api_key=api_key)

            models = client.models.list()
            result_models = {}

            for model in models:
                if "generateContent" in model.supported_actions:
                    model_id = model.name.replace('models/', '')

                    token_limit = model.input_token_limit if hasattr(model, 'input_token_limit') else 0

                    if hasattr(model, 'supported_actions'):
                        modality = ','.join(model.supported_actions)
                    else:
                        modality = "unknown"

                    result_models[model_id] = {
                        "model_id": model_id,
                        "トークン数": str(token_limit),
                        "モダリティ": modality,
                        "作成日": None
                    }

            has_openrouter = len(self.openrt_models) > 0
            if has_openrouter:
                for model_id in list(result_models.keys()):
                    openrt_key = f"google/{model_id}"
                    if openrt_key in self.openrt_models:
                        result_models[model_id]["作成日"] = self.openrt_models[openrt_key]["作成日"]
                    else:
                        if "live" not in model_id.lower():
                            del result_models[model_id]

            self.google_models = result_models

            if not has_openrouter:
                filter_info = "全てのモデル"
            else:
                filter_info = f"使用キー: {key_source}" if key_source else "不明なキー"
            logger.info(f"Googleモデル取得完了: {len(result_models)}個のモデル（{filter_info}）")

            return result_models

        except ImportError:
            logger.error("google-genai パッケージがインストールされていません")
            return {}
        except Exception as e:
            logger.error(f"Googleモデル取得エラー: {e}")
            return {}

    def get_openai_models(self, api_key: str, organization: str = None) -> Dict[str, Dict[str, str]]:
        """OpenAI apiからモデル一覧を取得（6ヶ月以内のモデル）"""
        try:
            if not api_key or api_key.startswith('<'):
                logger.warning("OpenAI apiキーが未設定です")
                return {}

            import openai
            client = openai.OpenAI(
                api_key=api_key,
                organization=organization
            )

            models = client.models.list()
            result_models = {}

            current_time = datetime.datetime.now()
            filter_6months = (current_time - datetime.timedelta(days=180)).timestamp()

            for model in models:
                model_id = model.id
                created_timestamp = model.created

                if created_timestamp < filter_6months:
                    continue

                created_date = datetime.datetime.fromtimestamp(created_timestamp).strftime("%Y/%m/%d")

                result_models[model_id] = {
                    "model_id": model_id,
                    "トークン数": "0",
                    "モダリティ": None,
                    "作成日": created_date
                }

            has_openrouter = len(self.openrt_models) > 0
            if has_openrouter:
                for model_id in result_models.keys():
                    openrt_key = f"openai/{model_id}"
                    if openrt_key in self.openrt_models:
                        result_models[model_id]["トークン数"] = self.openrt_models[openrt_key]["トークン数"]
                        result_models[model_id]["モダリティ"] = self.openrt_models[openrt_key]["モダリティ"]

                for model_id in list(result_models.keys()):
                    if "realtime" not in model_id.lower():
                        if result_models[model_id]["トークン数"] == "0":
                            del result_models[model_id]

            self.openai_models = result_models

            filter_info = "全てのモデル" if not has_openrouter else "6ヶ月以内"
            logger.info(f"OpenAIモデル取得完了: {len(result_models)}個のモデル（{filter_info}）")

            return result_models

        except ImportError:
            logger.error("openai パッケージがインストールされていません")
            return {}
        except Exception as e:
            logger.error(f"OpenAIモデル取得エラー: {e}")
            return {}

    def get_claude_models(self, api_key: str) -> Dict[str, Dict[str, str]]:
        """Anthropic Claude apiからモデル一覧を取得（6ヶ月以内のモデル）"""
        try:
            if not api_key or api_key.startswith('<'):
                logger.warning("Claude apiキーが未設定です")
                return {}

            import anthropic
            client = anthropic.Anthropic(api_key=api_key)

            models = client.models.list()
            result_models = {}

            current_time = datetime.datetime.now()
            filter_6months = (current_time - datetime.timedelta(days=180)).timestamp()

            for model in models.data:
                model_id = model.id

                created_date = None
                created_timestamp = None
                try:
                    if hasattr(model, 'created_at') and model.created_at:
                        if isinstance(model.created_at, str):
                            from dateutil import parser
                            created_dt = parser.parse(model.created_at)
                        else:
                            created_dt = model.created_at
                        created_timestamp = created_dt.timestamp()
                        created_date = created_dt.strftime("%Y/%m/%d")
                except Exception as e:
                    logger.debug(f"日付変換エラー ({model_id}): {e}")

                if created_timestamp is not None and created_timestamp < filter_6months:
                    continue

                result_models[model_id] = {
                    "model_id": model_id,
                    "トークン数": "0",
                    "モダリティ": None,
                    "作成日": created_date
                }

            has_openrouter = len(self.openrt_models) > 0
            if has_openrouter:
                for model_id in result_models.keys():
                    normalized_id = model_id

                    if len(normalized_id) >= 9 and normalized_id[-9:-8] == '-' and normalized_id[-8:-6] == '20':
                        normalized_id = normalized_id[:-9]

                    if len(normalized_id) >= 3 and normalized_id[-2] == '-':
                        last_char = normalized_id[-1]
                        third_last = normalized_id[-3]
                        if third_last in ['3', '4', '5'] and last_char.isdigit():
                            normalized_id = normalized_id[:-3] + third_last + '.' + last_char

                    openrt_key = f"anthropic/{normalized_id}"
                    if openrt_key in self.openrt_models:
                        result_models[model_id]["トークン数"] = self.openrt_models[openrt_key]["トークン数"]
                        result_models[model_id]["モダリティ"] = self.openrt_models[openrt_key]["モダリティ"]

            self.claude_models = result_models

            filter_info = "全てのモデル" if not has_openrouter else "6ヶ月以内"
            logger.info(f"Claudeモデル取得完了: {len(result_models)}個のモデル（{filter_info}）")

            return result_models

        except ImportError:
            logger.error("anthropic パッケージがインストールされていません")
            return {}
        except Exception as e:
            logger.error(f"Claudeモデル取得エラー: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def get_chat_models(self) -> Dict[str, Dict[str, str]]:
        """チャットAIモデル一覧を取得（日付情報付き）"""
        models: Dict[str, Dict[str, str]] = {
            "gemini": {
                k: f"{v.get('作成日') or 'yyyy/mm/dd'} - {k}"
                for k, v in self.google_models.items()
            },
            "freeai": {
                k: f"{v.get('作成日') or 'yyyy/mm/dd'} - {k}"
                for k, v in self.google_models.items()
            },
            "openrt": {
                k: f"{v.get('作成日') or 'yyyy/mm/dd'} - {k}"
                for k, v in self.openrt_models.items()
            }
        }

        return models

    def get_live_models(self) -> Dict[str, Dict[str, str]]:
        """ライブAIモデル一覧を取得（手動保守）"""
        return {
            "gemini_live": self.LIVE_GEMINI_MODELS,
            "freeai_live": self.LIVE_GEMINI_MODELS,
            "openai_live": self.LIVE_OPENAI_MODELS,
        }

    def get_live_voices(self) -> Dict[str, Dict[str, str]]:
        """ライブAIボイス一覧を取得（手動保守）"""
        return {
            "gemini_live": self.LIVE_GEMINI_VOICES,
            "freeai_live": self.LIVE_GEMINI_VOICES,
            "openai_live": self.LIVE_OPENAI_VOICES,
        }

    def get_code_models(self) -> Dict[str, Dict[str, str]]:
        """コードAIモデル一覧を取得（手動保守）"""
        return {
            "claude_sdk": self.CODE_CLAUDE_SDK_MODELS,
            "claude_cli": self.CODE_CLAUDE_CLI_MODELS,
            "copilot_cli": self.CODE_COPILOT_CLI_MODELS,
            "gemini_cli": self.CODE_GEMINI_CLI_MODELS,
            "codex_cli": self.CODE_CODEX_CLI_MODELS,
        }


__all__ = [
    "conf_models",
]

# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

# -*- coding: utf-8 -*-
# 診断単独動作用にコピーしたモデル絞り込み・補完処理。
# I/O、設定保存、OAuth、静的候補へのフォールバックは行わない。
# コピー元: backend_server/conf/conf_model.py
# 元コミット: 0f48c862251e4bffe656930b827c965ed56426d2
# 元blob: 7b70e037c3c9e5624509a6a7678f6d104c188f9a
# 元 Git blob: 7b70e037c3c9e5624509a6a7678f6d104c188f9a（8adbdb4 基準と同一）
# 元の日付窓・応答加工を維持。今後の元実装変更は自動反映されない。
import datetime
import logging
logger = logging.getLogger(__name__)

def openrouter_catalog(models_data, now=None):
    result_models = {}

    current_time = (now or datetime.datetime.now())
    filter_1year = (current_time - datetime.timedelta(days=365)).timestamp()
    filter_8months = (current_time - datetime.timedelta(days=240)).timestamp()
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
            if created_timestamp < filter_8months:
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

    return result_models

def google_catalog(models, openrouter=None):
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

    has_openrouter = len((openrouter or {})) > 0
    if has_openrouter:
        for model_id in list(result_models.keys()):
            openrt_key = f"google/{model_id}"
            if openrt_key in (openrouter or {}):
                result_models[model_id]["作成日"] = (openrouter or {})[openrt_key]["作成日"]
            else:
                if "live" not in model_id.lower():
                    del result_models[model_id]

    return result_models

def openai_catalog(models, openrouter=None, now=None):
    result_models = {}

    current_time = (now or datetime.datetime.now())
    filter_8months = (current_time - datetime.timedelta(days=240)).timestamp()

    for model in models:
        model_id = model.id
        created_timestamp = model.created

        if created_timestamp < filter_8months:
            continue

        created_date = datetime.datetime.fromtimestamp(created_timestamp).strftime("%Y/%m/%d")

        result_models[model_id] = {
            "model_id": model_id,
            "トークン数": "0",
            "モダリティ": None,
            "作成日": created_date
        }

    has_openrouter = len((openrouter or {})) > 0
    if has_openrouter:
        for model_id in result_models.keys():
            openrt_key = f"openai/{model_id}"
            if openrt_key in (openrouter or {}):
                result_models[model_id]["トークン数"] = (openrouter or {})[openrt_key]["トークン数"]
                result_models[model_id]["モダリティ"] = (openrouter or {})[openrt_key]["モダリティ"]

        for model_id in list(result_models.keys()):
            if "realtime" not in model_id.lower():
                if result_models[model_id]["トークン数"] == "0":
                    del result_models[model_id]

    return result_models

def claude_catalog(models, openrouter=None, now=None):
    result_models = {}

    current_time = (now or datetime.datetime.now())
    filter_8months = (current_time - datetime.timedelta(days=240)).timestamp()

    for model in models.data:
        model_id = model.id

        created_date = None
        created_timestamp = None
        try:
            if hasattr(model, 'created_at') and model.created_at:
                if isinstance(model.created_at, str):
                    # APIのISO 8601日時をstdlibで読む（Z/UTCオフセット対応）。
                    created_dt = datetime.datetime.fromisoformat(model.created_at.replace("Z", "+00:00"))
                else:
                    created_dt = model.created_at
                created_timestamp = created_dt.timestamp()
                created_date = created_dt.strftime("%Y/%m/%d")
        except Exception as e:
            logger.debug(f"日付変換エラー ({model_id}): {e}")

        if created_timestamp is not None and created_timestamp < filter_8months:
            continue

        result_models[model_id] = {
            "model_id": model_id,
            "トークン数": "0",
            "モダリティ": None,
            "作成日": created_date
        }

    has_openrouter = len((openrouter or {})) > 0
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
            if openrt_key in (openrouter or {}):
                result_models[model_id]["トークン数"] = (openrouter or {})[openrt_key]["トークン数"]
                result_models[model_id]["モダリティ"] = (openrouter or {})[openrt_key]["モダリティ"]

    return result_models

def ollama_catalog(models_data, now=None):
    result = {}
    current_time = (now or datetime.datetime.now())
    filter_8months = (current_time - datetime.timedelta(days=240)).timestamp()
    source_models = [
        model for model in models_data.get("data", [])
        if isinstance(model, dict)
    ]
    source_models.sort(key=lambda model: model.get("created") or 0, reverse=True)

    for model in source_models:
        if not isinstance(model, dict):
            continue
        model_id = model.get("id", "")
        if not model_id:
            continue
        created_timestamp = model.get("created")
        if not created_timestamp or created_timestamp < filter_8months:
            continue
        result[model_id] = _format_ollama_model_label(model_id, created_timestamp)

    return {ident: {"model_id":ident,"トークン数":"0","モダリティ":None,"作成日":label.split(" - ",1)[0]} for ident,label in result.items()}

def _format_ollama_model_label(model_id: str, created_timestamp=None) -> str:
    """他のチャットモデルと同じ「日付 - モデル名」形式に整える。"""
    created_date = "yyyy/mm/dd"
    try:
        if created_timestamp:
            created_date = datetime.datetime.fromtimestamp(int(created_timestamp)).strftime("%Y/%m/%d")
    except Exception:
        created_date = "yyyy/mm/dd"
    return f"{created_date} - {model_id}"



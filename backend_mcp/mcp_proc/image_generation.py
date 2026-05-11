# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""
画像生成モジュール

OpenAI API（DALL-E 3 / GPT Image 2）、Gemini / FreeAI（Google Gemini API）を使って画像を生成する。
"""

import base64
import io
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from PIL import Image


class ImageGenerationError(Exception):
    """画像生成エラー"""
    pass


class ImageGeneration:
    """
    画像生成クラス

    provider パラメータ:
        "auto"   — FreeAI を自動選択（デフォルト）
        "gemini" — Google Gemini API（gemini_key_id が必要）
        "freeai" — FreeAI API（freeai_key_id が必要、実装は Gemini 共通）
        "openai" — OpenAI DALL-E / GPT Image API
    """

    DEFAULT_OUTPUT_DIR = "backend_server/temp/output"

    # ================================================================== #
    # OpenAI モデルカタログ
    # ================================================================== #

    _MODELS = {
        "gpt-image-2": {
            "display": "GPT Image 2",
            "api_model": "gpt-image-2",
            "qualities": ["low", "medium", "high"],
            "default_quality": "medium",
            "valid_sizes": {"1024x1024", "1536x1024", "1024x1536"},
        },
        "gpt-image-1": {
            "display": "GPT Image 1",
            "api_model": "gpt-image-1",
            "qualities": ["low", "medium", "high"],
            "default_quality": "medium",
            "valid_sizes": {"1024x1024", "1536x1024", "1024x1536"},
        },
        "dall-e-3": {
            "display": "DALL-E 3",
            "api_model": "dall-e-3",
            "qualities": ["standard", "hd"],
            "default_quality": "standard",
            "valid_sizes": {"1024x1024", "1792x1024", "1024x1792"},
        },
    }

    OPENAI_DEFAULT_MODEL = "gpt-image-2"
    OPENAI_DEFAULT_SIZE = "1024x1024"

    # ================================================================== #
    # Gemini モデルカタログ
    # ================================================================== #

    _GEMINI_MODELS = {
        "gemini-3.1-flash-image-preview": {
            "display": "Gemini 3.1 Flash Image (Nano Banana 2)",
        },
        "gemini-3-pro-image-preview": {
            "display": "Gemini 3 Pro Image (Nano Banana Pro)",
        },
        "gemini-2.5-flash-image": {
            "display": "Gemini 2.5 Flash Image (Nano Banana)",
        },
    }

    GEMINI_DEFAULT_MODEL = "gemini-3.1-flash-image-preview"
    GEMINI_DEFAULT_SIZE = "1024x1024"
    FREEAI_DEFAULT_SIZE = "512x512"

    # Gemini サイズ → aspect_ratio / image_size マッピング
    _GEMINI_SIZE_MAP = {
        "512x512":   {"aspect_ratio": "1:1",  "image_size": "512"},
        "1024x1024": {"aspect_ratio": "1:1",  "image_size": "1K"},
        "1920x1080": {"aspect_ratio": "16:9", "image_size": "2K"},
        "1080x1920": {"aspect_ratio": "9:16", "image_size": "2K"},
    }

    # ================================================================== #
    # AiDiy_key.json へのパス（backend_mcp 起点）
    # ================================================================== #

    _KEY_CONFIG_REL = "../backend_server/_config/AiDiy_key.json"

    # ------------------------------------------------------------------ #
    # API キー解決（共通）
    # ------------------------------------------------------------------ #

    @staticmethod
    def _is_valid_key(key: str) -> bool:
        return bool(key) and not key.startswith("<")

    def _read_key_from_config(self, key_name: str) -> str:
        config_path = Path(__file__).resolve().parent.parent / self._KEY_CONFIG_REL
        try:
            if not config_path.exists():
                return ""
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            value = data.get(key_name, "")
            return value.strip() if isinstance(value, str) else ""
        except (json.JSONDecodeError, OSError):
            return ""

    def _get_openai_api_key(self) -> str:
        key = self._read_key_from_config("openai_key_id")
        return key if self._is_valid_key(key) else ""

    def _get_gemini_api_key(self) -> str:
        key = self._read_key_from_config("gemini_key_id")
        return key if self._is_valid_key(key) else ""

    def _get_freeai_api_key(self) -> str:
        key = self._read_key_from_config("freeai_key_id")
        return key if self._is_valid_key(key) else ""

    # ------------------------------------------------------------------ #
    # モデル解決
    # ------------------------------------------------------------------ #

    def _resolve_openai_model(self, model_id: Optional[str] = None):
        mid = (model_id or self.OPENAI_DEFAULT_MODEL).strip()
        if mid in self._MODELS:
            return mid, self._MODELS[mid]
        return self.OPENAI_DEFAULT_MODEL, self._MODELS[self.OPENAI_DEFAULT_MODEL]

    def _resolve_gemini_model(self, model_id: Optional[str] = None):
        mid = (model_id or self.GEMINI_DEFAULT_MODEL).strip()
        if mid in self._GEMINI_MODELS:
            return mid, self._GEMINI_MODELS[mid]
        return self.GEMINI_DEFAULT_MODEL, self._GEMINI_MODELS[self.GEMINI_DEFAULT_MODEL]

    def _resolve_gemini_size(self, size: str):
        size = size.strip()
        if size in self._GEMINI_SIZE_MAP:
            return self._GEMINI_SIZE_MAP[size]
        return self._GEMINI_SIZE_MAP[self.GEMINI_DEFAULT_SIZE]

    # ------------------------------------------------------------------ #
    # 画像生成（OpenAI）
    # ------------------------------------------------------------------ #

    def _generate_openai(
        self,
        prompt: str,
        original_path: Optional[str],
        model: str,
        size: str,
        quality: str,
    ) -> tuple[Image.Image, dict]:
        api_key = self._get_openai_api_key()
        if not api_key:
            raise ImageGenerationError(
                "OpenAI API キーが設定されていません。"
                "AiDiy_key.json の openai_key_id を設定してください。"
            )

        try:
            from openai import OpenAI
        except ImportError:
            raise ImageGenerationError(
                "openai パッケージがインストールされていません。"
                "pip install openai で導入してください。"
            )

        model_id, model_meta = self._resolve_openai_model(
            model if model != "auto" else None
        )

        if size == "auto":
            size = self.OPENAI_DEFAULT_SIZE
        elif size not in model_meta["valid_sizes"]:
            size = self.OPENAI_DEFAULT_SIZE

        if quality == "auto":
            quality = model_meta["default_quality"]

        client = OpenAI(api_key=api_key)
        try:
            payload = {
                "model": model_meta["api_model"],
                "prompt": prompt.strip(),
                "size": size,
                "quality": quality,
                "n": 1,
            }
            if original_path:
                with open(original_path, "rb") as f:
                    response = client.images.edit(image=f, **payload)
            else:
                if model_id == "dall-e-3":
                    payload["response_format"] = "b64_json"
                response = client.images.generate(**payload)
        finally:
            close = getattr(client, "close", None)
            if callable(close):
                close()

        data = getattr(response, "data", None) or []
        if not data:
            raise ImageGenerationError("OpenAI が画像データを返しませんでした")

        first = data[0]
        b64 = getattr(first, "b64_json", None)
        url = getattr(first, "url", None)

        if b64:
            raw = base64.b64decode(b64)
        elif url:
            import requests as _r
            raw = _r.get(url, timeout=60).content
        else:
            raise ImageGenerationError("OpenAI が画像データを返しませんでした")

        img = Image.open(io.BytesIO(raw))

        info = {
            "provider": "openai",
            "model": model_id,
            "prompt": prompt.strip(),
            "original_path": original_path,
            "width": img.width,
            "height": img.height,
            "size": size,
            "quality": quality,
            "engine_note": f"OpenAI {model_meta['display']}",
        }
        return img, info

    # ------------------------------------------------------------------ #
    # 画像生成（Gemini / FreeAI）
    # ------------------------------------------------------------------ #

    def _generate_gemini(
        self,
        prompt: str,
        original_path: Optional[str],
        model: str,
        size: str,
        provider: str,
    ) -> tuple[Image.Image, dict]:
        if provider == "freeai":
            api_key = self._get_freeai_api_key()
            provider_label = "freeai"
            default_size = self.FREEAI_DEFAULT_SIZE
        else:
            api_key = self._get_gemini_api_key()
            provider_label = "gemini"
            default_size = self.GEMINI_DEFAULT_SIZE

        if not api_key:
            raise ImageGenerationError(
                f"{provider_label.upper()} API キーが設定されていません。"
                f"AiDiy_key.json の {provider_label}_key_id を設定してください。"
            )

        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise ImageGenerationError(
                "google-genai パッケージがインストールされていません。"
                "pip install google-genai で導入してください。"
            )

        model_id, model_meta = self._resolve_gemini_model(
            model if model != "auto" else None
        )
        size_conf = self._resolve_gemini_size(size if size != "auto" else default_size)

        client = genai.Client(api_key=api_key)

        contents = [prompt.strip()]
        if original_path:
            contents.append(Image.open(original_path))

        image_config = types.ImageConfig(
            aspect_ratio=size_conf["aspect_ratio"],
            image_size=size_conf["image_size"],
        )

        config = types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            image_config=image_config,
        )

        response = client.models.generate_content(
            model=model_id,
            contents=contents,
            config=config,
        )

        img = None
        for part in response.parts:
            if part.inline_data is not None:
                img = part.as_image()._pil_image
                break

        if img is None:
            raise ImageGenerationError("Gemini が画像データを返しませんでした")

        info = {
            "provider": provider_label,
            "model": model_id,
            "prompt": prompt.strip(),
            "original_path": original_path,
            "width": img.width,
            "height": img.height,
            "size": size,
            "aspect_ratio": size_conf["aspect_ratio"],
            "image_size": size_conf["image_size"],
            "engine_note": f"Gemini {model_meta['display']} ({provider_label})",
        }
        return img, info

    # ------------------------------------------------------------------ #
    # 画像生成（統合入口）
    # ------------------------------------------------------------------ #

    def generate(
        self,
        prompt: str,
        provider: str = "auto",
        original_path: Optional[str] = None,
        model: str = "auto",
        size: str = "auto",
        quality: str = "auto",
    ) -> tuple[Image.Image, dict]:
        """
        プロンプトから画像を生成する。

        Args:
            prompt: 生成プロンプト
            provider: "auto" / "openai" / "gemini" / "freeai"
            original_path: 参照画像のパス（省略可）
            model:
              OpenAI: "auto"=gpt-image-2 / "gpt-image-2" / "gpt-image-1" / "dall-e-3"
              Gemini/FreeAI: "auto"=gemini-3.1-flash-image-preview
            size:
              OpenAI: "auto"=1024x1024 / "1024x1024" / "1536x1024" / "1024x1536" / ...
              Gemini/FreeAI: "auto"=1024x1024 / "512x512" / "1024x1024" / "1920x1080" / "1080x1920"
            quality:
              OpenAI only: "auto"（モデル既定値） / gpt-image-2: "low","medium","high" / dall-e-3: "standard","hd"

        Returns:
            (image, info_dict)
            info_dict: provider, model, prompt, width, height, engine_note
        """
        if not prompt or not prompt.strip():
            raise ImageGenerationError("prompt は必須です")

        provider = provider.strip().lower()
        if provider not in ("auto", "openai", "gemini", "freeai"):
            raise ImageGenerationError(
                f"未対応の provider です: '{provider}'（auto / openai / gemini / freeai のみ）"
            )

        if original_path and not os.path.isfile(original_path):
            raise ImageGenerationError(f"参照画像が見つかりません: '{original_path}'")

        # auto → freeai にフォールバック
        if provider == "auto":
            provider = "freeai"

        if provider == "openai":
            return self._generate_openai(prompt, original_path, model, size, quality)
        else:
            return self._generate_gemini(prompt, original_path, model, size, provider)

    # ------------------------------------------------------------------ #
    # 出力
    # ------------------------------------------------------------------ #

    def _resolve_default_output_dir(self) -> str:
        """プロジェクトルート起点で DEFAULT_OUTPUT_DIR を絶対パス化する"""
        project_root = Path(__file__).resolve().parent.parent.parent
        return str(project_root / self.DEFAULT_OUTPUT_DIR)

    @staticmethod
    def _is_directory_path(path: str) -> bool:
        """save_path をフォルダ扱いとするか判定する。
           - 既存ディレクトリ
           - 末尾が / または \\
           - 拡張子なし
        """
        if os.path.isdir(path):
            return True
        if path.endswith(("/", "\\")):
            return True
        if not os.path.splitext(path)[1]:
            return True
        return False

    def to_base64(
        self,
        img: Image.Image,
        fmt: str = "png",
        quality: int = 85,
        save_path: Optional[str] = None,
    ) -> str:
        """PIL Image を Base64 文字列で返す（desktop_capture と同形式）。

        Args:
            fmt: "png" または "jpeg"
            quality: JPEG 品質 (1-100)
            save_path: 保存先。
                       フォルダ指定（既存ディレクトリ / 末尾 / または \\ / 拡張子なし）なら
                       そのフォルダに yyyymmdd.hhmmss.png で保存。
                       ファイル指定（拡張子あり）なら指定ファイルに上書き保存（拡張子に合わせて変換）。
                       None なら DEFAULT_OUTPUT_DIR にデフォルト保存。
        """
        buf = io.BytesIO()
        fmt_upper = fmt.upper()
        if fmt_upper in ("JPEG", "JPG"):
            img = img.convert("RGB")
            img.save(buf, format="JPEG", quality=quality, optimize=True)
        else:
            img.save(buf, format="PNG", optimize=True)
        data = buf.getvalue()

        if save_path is None:
            save_path = self._resolve_default_output_dir()

        if self._is_directory_path(save_path):
            os.makedirs(save_path, exist_ok=True)
            fname = datetime.now().strftime("%Y%m%d.%H%M%S") + ".png"
            dest = os.path.join(save_path, fname)
            file_buf = io.BytesIO()
            img.save(file_buf, format="PNG", optimize=True)
            file_data = file_buf.getvalue()
        else:
            dest = save_path
            parent = os.path.dirname(os.path.abspath(dest))
            if parent:
                os.makedirs(parent, exist_ok=True)
            ext = os.path.splitext(save_path)[1].lower()
            if ext in (".jpg", ".jpeg"):
                file_buf = io.BytesIO()
                img.convert("RGB").save(file_buf, format="JPEG", quality=quality, optimize=True)
                file_data = file_buf.getvalue()
            else:
                file_buf = io.BytesIO()
                img.save(file_buf, format="PNG", optimize=True)
                file_data = file_buf.getvalue()
        with open(dest, "wb") as f:
            f.write(file_data)

        return base64.b64encode(data).decode("ascii")

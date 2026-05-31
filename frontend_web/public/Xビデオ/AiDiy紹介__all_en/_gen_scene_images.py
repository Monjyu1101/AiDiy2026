# -*- coding: utf-8 -*-
"""
シーン画像生成スクリプト

scenario.js の各 scene から images/scene_*.png を生成します。
- scenario.js の image_prompt フィールドを優先使用（なければ title/kicker 等から構築）
- テンプレート元画像（日本語版）を original_path として渡し、スタイル・構図を参照
- 既存の画像ファイル（1000 bytes 超）は自動スキップします。
"""

import json
import os
import time
import urllib.error
import urllib.request

OUTPUT_DIR = 'D:/OneDrive/_sandbox/AiDiy2026/frontend_web/public/Xビデオ\\AiDiy紹介__all_en\\images'
TEMPLATE_IMAGE_DIR = 'D:/OneDrive/_sandbox/AiDiy2026/frontend_web/public/Xビデオ/AiDiy紹介__all_ja\\images'
IMAGE_GEN_API_URL = 'http://localhost:8095/aidiy_image_generation/generate'
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _clean_text(value):
    return " ".join(str(value or "").replace("\\n", " ").replace("\n", " ").split()).strip()


def load_scenes():
    scenario_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scenario.js")
    with open(scenario_file, encoding="utf-8-sig") as f:
        content = f.read()

    json_str = content.strip()
    if json_str.startswith("window.SCENARIO ="):
        json_str = json_str[len("window.SCENARIO ="):].strip()
    json_str = json_str.rstrip(";").strip()

    data = json.loads(json_str)
    scenes = data.get("scenes", [])
    return scenes if isinstance(scenes, list) else []


LANGUAGE = 'en'

# 言語コード → 言語名・地域スタイル・禁止文字のマッピング
_LANG_MAP = {
    "en": ("English",    "globally appealing, internationally neutral",  "NO Japanese text, NO hiragana, NO katakana, NO kanji"),
    "fr": ("French",     "European, French cultural aesthetic",           "NO Japanese text, NO hiragana, NO katakana, NO kanji"),
    "de": ("German",     "European, German/Central European aesthetic",   "NO Japanese text, NO hiragana, NO katakana, NO kanji"),
    "es": ("Spanish",    "Latin/Spanish cultural aesthetic",              "NO Japanese text, NO hiragana, NO katakana, NO kanji"),
    "pt": ("Portuguese", "Latin/Portuguese cultural aesthetic",           "NO Japanese text, NO hiragana, NO katakana, NO kanji"),
    "it": ("Italian",    "European, Italian cultural aesthetic",          "NO Japanese text, NO hiragana, NO katakana, NO kanji"),
    "ru": ("Russian",    "Eastern European/Russian aesthetic",            "NO Japanese text, NO hiragana, NO katakana, NO kanji"),
    "nl": ("Dutch",      "European, Dutch/Nordic aesthetic",              "NO Japanese text, NO hiragana, NO katakana, NO kanji"),
    "zh": ("Chinese",    "East Asian, Chinese cultural aesthetic",        "NO hiragana, NO katakana. Chinese hanzi characters are acceptable if needed"),
    "ko": ("Korean",     "East Asian, Korean cultural aesthetic",         "NO hiragana, NO katakana. Korean hangul characters are acceptable if needed"),
    "ar": ("Arabic",     "Middle Eastern/Arabic cultural aesthetic",      "NO Japanese text, NO hiragana, NO katakana, NO kanji"),
    "ja": ("Japanese",   "Japanese cultural aesthetic",                   ""),
}

def _get_lang_info(lang_code):
    base = lang_code.split("-")[0].lower()
    return _LANG_MAP.get(base, (lang_code, "internationally neutral", "NO Japanese text, NO hiragana, NO katakana, NO kanji"))

def _build_image_directive():
    lang_name, style_hint, char_ban = _get_lang_info(LANGUAGE)
    lines = [
        "CRITICAL REQUIREMENTS — strictly follow all of the following:",
        "1. This image is for a %s-language presentation. Use visuals that feel natural and appealing to %s-speaking audiences (%s)." % (lang_name, lang_name, style_hint),
        "2. NO embedded text, NO readable labels, NO text overlay of any kind baked into the image.",
    ]
    if char_ban:
        lines.append("3. %s anywhere in the image." % char_ban)
    lines.append("4. If a reference image is provided, use it ONLY for layout/composition/style inspiration. Do NOT copy any text or language-specific elements from it.")
    return "\n".join(lines)

IMAGE_DIRECTIVE = _build_image_directive()


def build_prompt(scene):
    # scenario.js の image_prompt を最優先で使用し、言語別指示を必ず追記する
    image_prompt = _clean_text(scene.get("image_prompt", ""))
    if image_prompt:
        return f"{image_prompt}\n\n{IMAGE_DIRECTIVE}"

    # image_prompt がない場合は他フィールドから構築
    title = _clean_text(scene.get("title", ""))
    headline = _clean_text(scene.get("headline", ""))
    kicker = _clean_text(scene.get("kicker", ""))
    lead = _clean_text(scene.get("lead", ""))
    subtitle = _clean_text(scene.get("subtitle", ""))

    lines = [
        "Create a high-quality, professional widescreen illustration/concept-art for a technology introduction presentation.",
    ]
    if kicker:
        lines.append(f"Topic: {kicker}.")
    if title:
        lines.append(f"Title: {title}.")
    if headline:
        lines.append(f"Headline: {headline}.")
    if lead:
        lines.append(f"Details: {lead}.")
    if subtitle:
        lines.append(f"Concept: {subtitle}.")
    lines.append("Style: modern technical slide illustration, clean design, gradient background, futuristic, beautiful.")
    lines.append(IMAGE_DIRECTIVE)
    return "\n".join(lines).strip()


def get_template_image(num_str):
    """テンプレート元画像のパスを返す。存在しない場合は None。"""
    if not TEMPLATE_IMAGE_DIR:
        return None
    path = os.path.join(TEMPLATE_IMAGE_DIR, f"scene_{num_str}.png")
    if os.path.isfile(path) and os.path.getsize(path) > 1000:
        return path
    return None


def post_json(url, payload, timeout_sec=600):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as res:
            raw = res.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as e:
        raise RuntimeError(f"HTTP API に接続できません: {url} ({e})") from e
    result = json.loads(raw)
    if isinstance(result, dict) and result.get("error"):
        raise RuntimeError(result["error"])
    return result


def generate_one(prompt, out_path, original_path=None):
    attempts = [
        ("openai", "gpt-image-2", "1536x1024", "medium"),
        ("freeai", "auto", "1920x1080", "auto"),
        ("auto", "auto", "1024x1024", "auto"),
    ]
    last_error = None
    for provider, model, size, quality in attempts:
        try:
            payload = {
                "prompt": prompt,
                "provider": provider,
                "model": model,
                "size": size,
                "quality": quality,
                "save_path": out_path,
            }
            if original_path:
                payload["original_path"] = original_path
            result = post_json(IMAGE_GEN_API_URL, payload)
            return {
                "provider": provider,
                "model": model,
                "save_path": result.get("save_path", out_path),
            }
        except Exception as e:
            last_error = f"{provider}/{model}/{size}: {e}"
    raise RuntimeError(last_error or "image generation failed")


def main():
    scenes = load_scenes()
    total = len(scenes)
    done = 0
    skip = 0
    fail = 0

    for i, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            continue
        scene_id = str(scene.get("id", f"scene_{i:03d}") or f"scene_{i:03d}")
        num_str = scene_id.replace("scene_", "")
        out_path = os.path.join(OUTPUT_DIR, f"scene_{num_str}.png")

        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            print(f"  [SKIP] {os.path.basename(out_path)}")
            skip += 1
            continue

        prompt = build_prompt(scene)
        original_path = get_template_image(num_str)
        title = _clean_text(scene.get("title", scene_id))
        ref_label = f" (ref: {os.path.basename(original_path)})" if original_path else ""
        print(f"  [GEN ] {os.path.basename(out_path)} : {title}{ref_label}")
        try:
            info = generate_one(prompt, out_path, original_path=original_path)
            size = os.path.getsize(out_path) if os.path.exists(out_path) else 0
            if size > 1000:
                print(
                    f"         -> OK ({size:,} bytes) "
                    f"[{info.get('provider', '?')}/{info.get('model', '?')}]"
                )
                done += 1
            else:
                print("         -> FAIL (empty or too small)")
                fail += 1
        except Exception as e:
            print(f"         -> ERROR: {e}")
            fail += 1

        time.sleep(1)

    print(f"\n完了: {done} 生成, {skip} スキップ, {fail} 失敗 (合計 {total} 件)")
    if fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# See LICENSE for full terms.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""
code_agents テスト

テスト構成:
  Test 1: バージョン確認・設定表示
  Test 2: auto AI で簡単なプロンプト実行
  Test 3: 利用可能な AI を個別指定して実行（version_info に基づく）
"""

import asyncio
import os
import sys

# UTF-8 出力強制（Windows cp932 文字化け対策）
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_proc.code_agents import CodeAgents, CodeAgentsError


TEST_PROMPT = "1+1の計算結果だけを数字で答えてください。余計な説明は不要です。"


# ------------------------------------------------------------------ #
# Test 1: バージョン確認・設定表示
# ------------------------------------------------------------------ #

def test_version_and_config(ca: CodeAgents) -> None:
    print("=" * 60)
    print("Test 1: バージョン確認・設定表示")
    print("=" * 60)

    version_info = ca._check_ai_versions()
    ca.version_info = version_info

    for ai_name, info in version_info.items():
        status = "OK" if info.get("ok") else "NG"
        ver = info.get("version", "")
        print(f"  [{status}] {ai_name:20s} {ver}")

    config = ca.get_config()
    print(f"\n  project_root           = {config['project_root']}")
    print(f"  resolved_project_path  = {config['resolved_project_path']}")
    print(f"  path_exists            = {config['project_path_exists']}")

    available = [k for k, v in version_info.items() if v.get("ok")]
    print(f"\n  利用可能 AI: {available if available else '（なし）'}")
    return available


# ------------------------------------------------------------------ #
# Test 2: auto AI で簡単なプロンプト実行
# ------------------------------------------------------------------ #

async def test_run_auto(ca: CodeAgents, available: list) -> None:
    print()
    print("=" * 60)
    print("Test 2: auto AI でプロンプト実行")
    print("=" * 60)

    if not available:
        print("  SKIP: 利用可能な AI がありません")
        return

    ai_name, ai_model = ca._resolve_ai_params("auto", "auto")
    print(f"  ai_name   = {ai_name}")
    print(f"  ai_model  = {ai_model}")
    print(f"  prompt    = {TEST_PROMPT}")
    print()

    result = await ca.run_async(
        prompt=TEST_PROMPT,
        ai_name="auto",
        ai_model="auto",
        max_turns=3,
        code_plan="off",
        code_verify="off",
        timeout_sec=120,
    )

    print(f"  status    = {result['status']}")
    print(f"  ai_name   = {result['ai_name']}")
    print(f"  ai_model  = {result['ai_model']}")
    print(f"  result    =\n{result['result']}")


# ------------------------------------------------------------------ #
# Test 3: 利用可能 AI を個別に指定して実行
# ------------------------------------------------------------------ #

async def test_run_each(ca: CodeAgents, available: list) -> None:
    print()
    print("=" * 60)
    print("Test 3: 利用可能 AI を個別指定して実行")
    print("=" * 60)

    if not available:
        print("  SKIP: 利用可能な AI がありません")
        return

    for ai_name in available:
        print()
        print(f"  --- {ai_name} ---")
        result = await ca.run_async(
            prompt=TEST_PROMPT,
            ai_name=ai_name,
            ai_model="auto",
            max_turns=3,
            code_plan="off",
            code_verify="off",
            timeout_sec=120,
        )
        print(f"  status  = {result['status']}")
        print(f"  result  = {result['result'][:200]}")


# ------------------------------------------------------------------ #
# main
# ------------------------------------------------------------------ #

async def main() -> None:
    ca = CodeAgents()

    available = test_version_and_config(ca)

    await test_run_auto(ca, available)

    await test_run_each(ca, available)

    print()
    print("=" * 60)
    print("OK")


if __name__ == "__main__":
    asyncio.run(main())
